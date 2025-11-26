# MCP Architecture for Trading Intelligence Agents

## 🎯 Executive Summary

**Question**: *"Will core table data come from MCP server(s) for legacy existing system(s)?"*

**Answer**: **YES! This is the recommended production architecture.**

MCP (Model Context Protocol) servers are **perfect** for:
- ✅ Wrapping legacy systems (Oracle, Sybase, Murex, etc.)
- ✅ Providing unified interface to agents
- ✅ Handling authentication, retries, caching
- ✅ Standardizing data formats
- ✅ Easy to add new data sources

---

## 🏗️ Architecture Evolution

### **Phase 1: Demo/POC (Current)**
```
Agents → PostgreSQL (demo data)
```
- Simple, self-contained
- Good for proof-of-concept
- **Not production-ready**

### **Phase 2: Direct Integration (Not Recommended)**
```
Agents → Oracle OMS
       → Sybase Risk Warehouse
       → Bloomberg API
       → Reuters News
       → Salesforce CRM
```
- ❌ Agents tightly coupled to data sources
- ❌ Each agent needs connection logic
- ❌ Hard to add new sources
- ❌ Difficult to test

### **Phase 3: MCP Architecture (Recommended)** ✅
```
Agents → MCP Data Service (unified interface)
            ↓
      ┌─────┴─────┬─────────┬──────────┬──────────┐
      ▼           ▼         ▼          ▼          ▼
  Trade MCP   Risk MCP  Market MCP  News MCP  Client MCP
  Server      Server    Server      Server    Server
      ↓           ↓         ▼          ▼          ▼
  Oracle      Sybase    Bloomberg  Reuters   Salesforce
  OMS         Risk      API        News      CRM
              Warehouse
```

**Benefits**:
- ✅ Agents don't know about legacy systems
- ✅ Easy to swap data sources (just change MCP server)
- ✅ MCP servers handle connection complexity
- ✅ Can test with mock MCP servers
- ✅ Standard protocol (MCP spec)

---

## 📦 Required MCP Servers

### **1. Trade Data MCP Server**

**Purpose**: Expose trade execution data from OMS

**Backend Systems**:
- Oracle Order Management System
- Murex trading platform
- FIX execution venues
- Internal trade capture systems

**Exposed Tools**:
```python
get_client_trades(client_id, start_date, end_date)
→ Returns: trade_id, instrument, side, quantity, price, timestamp, venue

get_trade_summary(client_id, days=90)
→ Returns: count, instruments, avg_quantity, market_order_ratio

get_position_flips(client_id, days=90)
→ Returns: daily flip counts (for HMM switch probability)

get_execution_quality(client_id, days=30)
→ Returns: slippage, fill rate, venue breakdown
```

**Implementation Considerations**:
- Read-only database user (security)
- Connection pooling (performance)
- Query timeout limits
- Data caching (frequently accessed clients)

---

### **2. Risk Data MCP Server**

**Purpose**: Expose risk metrics, positions, P&L

**Backend Systems**:
- Sybase risk warehouse
- Collateral management system
- Margin calculation engine
- VAR computation systems

**Exposed Tools**:
```python
get_client_positions(client_id)
→ Returns: instrument, net_position, gross_position, leverage

get_client_risk_metrics(client_id)
→ Returns: VAR, concentration_scores, leverage_ratio, margin_util

get_historical_pnl(client_id, days=90)
→ Returns: daily P&L time series

get_risk_alerts(client_id)
→ Returns: active breaches, limit exceedances
```

**Implementation Considerations**:
- May need to call multiple systems
- Risk calculations might be slow (cache results)
- Sensitive data (strict access control)

---

### **3. Market Data MCP Server**

**Purpose**: Provide market prices, historical bars

**Backend Systems**:
- Bloomberg API
- Reuters feeds
- ICE Data Services
- Internal market data cache

**Exposed Tools**:
```python
get_market_bars(instruments, start_date, end_date)
→ Returns: OHLCV data for momentum-beta calculation

get_current_prices(instruments)
→ Returns: real-time bid/ask/last

get_correlation_matrix(instruments, days=90)
→ Returns: instrument correlation matrix

get_volatility_surface(instrument)
→ Returns: implied vol grid (for options)
```

**Implementation Considerations**:
- Expensive API calls (Bloomberg charges per request)
- Aggressive caching (market bars don't change)
- Rate limiting (don't hammer Bloomberg)
- Fallback to alternative sources if primary fails

---

### **4. News/Media MCP Server**

**Purpose**: Financial news, headlines, sentiment

**Backend Systems**:
- Reuters News API
- Dow Jones Newswires
- Bloomberg News
- Internal research feeds

**Exposed Tools**:
```python
get_financial_headlines(instruments, hours=72)
→ Returns: headline_id, title, source, timestamp

get_sentiment_scores(headline_ids)
→ Returns: pre-computed sentiment (if available)

get_macro_events(days=7)
→ Returns: economic calendar (Fed meetings, NFP, GDP, etc.)

search_news(query, limit=50)
→ Returns: full-text search results
```

**Implementation Considerations**:
- News feeds are streaming (might need message queue)
- Deduplication (same story from multiple sources)
- Sentiment might be pre-computed by vendor
- Very time-sensitive (low latency required)

---

### **5. Client Master MCP Server**

**Purpose**: Client metadata, relationships, KYC

**Backend Systems**:
- Salesforce CRM
- Client master database (DB2/Oracle)
- KYC/Compliance systems
- Relationship management tools

**Exposed Tools**:
```python
get_client_metadata(client_id)
→ Returns: name, RM, sector, segment, onboarding_date

get_client_hierarchy(client_id)
→ Returns: parent entities, subsidiaries, beneficial owners

get_relationship_history(client_id)
→ Returns: past interactions, actions taken, outcomes

list_clients(search, segment, rm, limit)
→ Returns: filtered client list with switch probabilities

get_client_timeline(client_id, months=6)
→ Returns: historical segment changes, regime shifts
```

**Implementation Considerations**:
- May span multiple systems (CRM + master + compliance)
- PII handling (GDPR/privacy regulations)
- Audit logging (who accessed what when)

---

## 🔌 Integration Pattern

### **Step 1: Replace DataService**

```python
# OLD: agents-service/services/data_service.py
class DataService:
    def get_trades(self, client_id):
        conn = psycopg2.connect(...)  # Direct SQL
        cursor.execute("SELECT * FROM trades ...")

# NEW: agents-service/services/mcp_data_service.py
class MCPDataService:
    def get_trades(self, client_id):
        result = self.mcp_client.call_tool(
            server='trade-server',
            tool='get_client_trades',
            args={'client_id': client_id}
        )
        return result['trades']
```

### **Step 2: Update Agent Initialization**

```python
# agents-service/main.py

# OLD:
from services.data_service import DataService
data_service = DataService()

# NEW:
from services.mcp_data_service import MCPDataService
data_service = MCPDataService()  # Connects to MCP servers

# Or environment-based:
USE_MCP = os.getenv('USE_MCP', 'true') == 'true'
if USE_MCP:
    data_service = MCPDataService()  # Production
else:
    data_service = DataService()     # Local dev
```

### **Step 3: Configure MCP Server URLs**

```bash
# .env
MCP_TRADE_SERVER_URL=http://trade-mcp.bank.internal:3001
MCP_RISK_SERVER_URL=http://risk-mcp.bank.internal:3002
MCP_MARKET_SERVER_URL=http://market-mcp.bank.internal:3003
MCP_NEWS_SERVER_URL=http://news-mcp.bank.internal:3004
MCP_CLIENT_SERVER_URL=http://client-mcp.bank.internal:3005
```

### **Step 4: Deploy MCP Servers**

```bash
# Each MCP server runs as separate service

# Trade MCP Server (wraps Oracle OMS)
cd mcp-servers/trade
python server.py --config=config.json

# Risk MCP Server (wraps Sybase)
cd mcp-servers/risk
python server.py --config=config.json

# Market MCP Server (wraps Bloomberg)
cd mcp-servers/market
python server.py --config=config.json

# News MCP Server (wraps Reuters)
cd mcp-servers/news
python server.py --config=config.json

# Client MCP Server (wraps Salesforce)
cd mcp-servers/client
python server.py --config=config.json
```

---

## 📊 Data Flow Example

### **Scenario**: Analyze client ACME_FX_023

```
1. Frontend calls: GET /api/v1/clients/ACME_FX_023/profile

2. API Façade routes to: agents-service.analyze("ACME_FX_023")

3. Orchestrator starts:
   ├─ Call Segmentation Agent
   │  └─ fetch_trades_summary("ACME_FX_023")
   │     └─ MCPDataService.get_trades("ACME_FX_023")
   │        └─ Call Trade MCP Server
   │           └─ Query Oracle OMS
   │              SELECT * FROM oms_trades WHERE client_id = 'ACME_FX_023'
   │           └─ Return 450 trades
   │        └─ Convert to DataFrame
   │     └─ fetch_position_snapshot("ACME_FX_023")
   │        └─ Call Risk MCP Server
   │           └─ Query Sybase risk warehouse
   │              SELECT * FROM positions WHERE client_id = 'ACME_FX_023'
   │           └─ Return: EURUSD 72% concentration
   │     └─ compute_switch_probability (HMM)
   │        └─ Uses trades DataFrame
   │        └─ Computes 5 signals
   │        └─ Returns: 0.64
   │     └─ Call Gemini with data
   │        └─ Returns: "Trend Follower", 0.85 confidence
   │
   ├─ Call Media Fusion Agent
   │  └─ MCPDataService.get_headlines([EURUSD, GBPUSD])
   │     └─ Call News MCP Server
   │        └─ Query Reuters API
   │           headlines?symbols=EURUSD,GBPUSD&hours=72
   │        └─ Return 18 headlines
   │     └─ Batch to Gemini for sentiment
   │        └─ Returns: HIGH pressure, -0.58 avg sentiment
   │
   └─ Call NBA Agent
      └─ Gemini with context
         └─ Returns: PROACTIVE_OUTREACH + PROPOSE_HEDGE

4. Orchestrator assembles complete profile

5. Return to Frontend
```

**Key Point**: Agents never directly touch Oracle, Sybase, Bloomberg, etc. Everything goes through MCP servers.

---

## 🎨 Benefits of MCP Architecture

### **1. Decoupling**
```
Before: Agent → Oracle (tightly coupled)
After:  Agent → MCP Server → Oracle (loosely coupled)
```
- Can swap Oracle for Postgres without changing agent code
- Can add new data sources easily

### **2. Standardization**
All MCP servers return data in same format:
```python
{
  "trades": [
    {"trade_id": ..., "instrument": ..., "side": ..., "quantity": ...},
    ...
  ]
}
```
- Agent doesn't care if data came from Oracle, CSV, or API

### **3. Testing**
```python
# Mock MCP server for testing
class MockTradeMCPServer:
    def get_client_trades(self, client_id):
        return {'trades': [mock_trade_1, mock_trade_2]}

# Agents work with real or mock MCP servers
```

### **4. Security**
```
Agent → MCP Server (internal network)
       ↓
       Oracle (no direct access from agents)
```
- MCP server uses read-only DB user
- MCP server handles authentication
- MCP server logs all access

### **5. Performance**
```python
# MCP server can cache
@cache(ttl=300)  # Cache for 5 minutes
def get_client_trades(client_id):
    # Expensive Oracle query
    ...
```
- Agents get fast responses
- Database load reduced

### **6. Reliability**
```python
# MCP server can retry
def get_client_trades(client_id):
    for attempt in range(3):
        try:
            return oracle_query(...)
        except OracleError:
            sleep(1)
            continue
    return fallback_data()
```
- Agents don't need retry logic
- Graceful degradation

---

## 🚀 Migration Path

### **Phase 1: Hybrid (Now → 3 months)**
```python
class HybridDataService:
    def __init__(self):
        self.mcp = MCPDataService()
        self.sql = DataService()  # Fallback
    
    def get_trades(self, client_id):
        if self.mcp.servers.get('trade'):
            return self.mcp.get_trades(client_id)  # Try MCP first
        else:
            return self.sql.get_trades(client_id)  # Fallback to SQL
```

**Benefits**:
- Gradual migration
- Low risk (fallback to SQL)
- Can deploy MCP servers one at a time

### **Phase 2: MCP-First (3-6 months)**
```python
# All data goes through MCP
# SQL only for local dev
USE_MCP = os.getenv('USE_MCP', 'true')
```

### **Phase 3: MCP-Only (6+ months)**
```python
# Remove SQL data service entirely
# All environments use MCP
```

---

## 📋 MCP Server Checklist

For each MCP server, implement:

- [ ] **Connection Management**
  - [ ] Connection pooling
  - [ ] Timeout handling
  - [ ] Retry logic with exponential backoff
  - [ ] Health checks

- [ ] **Tools (MCP Interface)**
  - [ ] Tool declarations (names, params, descriptions)
  - [ ] Input validation
  - [ ] Output standardization
  - [ ] Error handling

- [ ] **Performance**
  - [ ] Caching (where appropriate)
  - [ ] Query optimization
  - [ ] Batch operations
  - [ ] Pagination for large results

- [ ] **Security**
  - [ ] Read-only database users
  - [ ] Authentication (API keys, OAuth)
  - [ ] Rate limiting
  - [ ] Audit logging (who called what when)

- [ ] **Monitoring**
  - [ ] Request/response logging
  - [ ] Latency metrics
  - [ ] Error rates
  - [ ] Cache hit rates

- [ ] **Testing**
  - [ ] Unit tests for each tool
  - [ ] Integration tests with real DB
  - [ ] Load testing
  - [ ] Failover testing

---

## 🔍 Example: Trade MCP Server Deployment

### **Directory Structure**
```
mcp-servers/trade/
├── server.py                 # MCP server implementation
├── config.json               # Configuration (DB connection, etc.)
├── requirements.txt          # Dependencies (mcp-sdk, cx_Oracle)
├── Dockerfile                # Container image
├── kubernetes/
│   ├── deployment.yaml       # K8s deployment
│   └── service.yaml          # K8s service
└── tests/
    ├── test_server.py        # Unit tests
    └── test_integration.py   # Integration tests
```

### **Deployment (Kubernetes)**
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trade-mcp-server
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: trade-mcp
        image: bank/trade-mcp-server:1.0
        env:
        - name: ORACLE_CONNECTION_STRING
          valueFrom:
            secretKeyRef:
              name: oracle-creds
              key: connection_string
        ports:
        - containerPort: 3001
        livenessProbe:
          httpGet:
            path: /health
            port: 3001
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### **Service Discovery**
```yaml
# kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: trade-mcp-server
spec:
  selector:
    app: trade-mcp-server
  ports:
  - port: 3001
    targetPort: 3001
  type: ClusterIP  # Internal only
```

### **Environment Variables** (agents-service)
```bash
MCP_TRADE_SERVER_URL=http://trade-mcp-server.default.svc.cluster.local:3001
```

---

## 📚 Resources

### **MCP Specification**
- [Model Context Protocol Spec](https://modelcontextprotocol.io)
- MCP Python SDK: `pip install mcp`
- MCP TypeScript SDK: `npm install @modelcontextprotocol/sdk`

### **Example MCP Servers** (from spec)
- Filesystem MCP Server
- Database MCP Server
- API Wrapper MCP Server

### **Best Practices**
1. **One MCP server per system** (Trade, Risk, Market, etc.)
2. **Read-only access** where possible (security)
3. **Caching aggressively** (performance)
4. **Health checks** on all tools
5. **Version your tools** (v1, v2 for backwards compatibility)

---

## ✅ Summary

**Yes, MCP servers are the right approach for production!**

**Current State** (Demo):
```
Agents → PostgreSQL (demo data)
```

**Production State** (MCP):
```
Agents → MCP Data Service
            ↓
      ┌─────┴─────┬─────────┬──────────┬──────────┐
      ▼           ▼         ▼          ▼          ▼
  Trade MCP   Risk MCP  Market MCP  News MCP  Client MCP
      ↓           ↓         ▼          ▼          ▼
  Oracle      Sybase    Bloomberg  Reuters   Salesforce
```

**Migration Strategy**:
1. Start with 1 MCP server (Trade)
2. Add hybrid fallback (MCP → SQL if MCP unavailable)
3. Gradually add more MCP servers (Risk, Market, News, Client)
4. Eventually remove SQL fallback

**Files Provided**:
- `mcp_data_service.py` - MCP client wrapper
- `example_trade_mcp_server.py` - Sample MCP server for Oracle OMS

Ready to proceed! 🚀
