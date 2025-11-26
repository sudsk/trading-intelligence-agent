# Trading Intelligence Agent

**AI-powered client segmentation and next best actions for sales & trading desks**

[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Run-4285F4?logo=google-cloud)](https://cloud.google.com/run)
[![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-fbbc04)](https://ai.google.dev/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-purple)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 What It Does

Profiles each trading client into behavioral segments (Trend Follower, Mean Reverter, Hedger, Trend Setter), estimates their **Switch Probability** using statistical signals, and surfaces **Next Best Actions** for relationship managers.

### **Key Features**

- 📊 **Client Segmentation** - Classifies trading behavior using Gemini 2.0 Flash
- 📈 **Switch Probability** - HMM/change-point detection (5 statistical signals)
- 📰 **Media Fusion** - Real-time sentiment analysis of market news
- 🎯 **Next Best Actions** - AI-generated recommendations with segment-specific playbooks
- ⚡ **Real-Time Alerts** - SSE streaming for immediate notifications
- 🏗️ **MCP Architecture** - Production-ready Model Context Protocol integration

---

## 🏛️ Architecture

![Architecture Diagram](images/tia_arch.png)

```
┌─────────────┐
│   React     │  Frontend (Port 3000)
│   Frontend  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API Façade  │  Thin routing layer (Port 8000)
│  (FastAPI)  │  • SSE streaming
└──────┬──────┘  • Action logging
       │
       ▼
┌─────────────┐
│   Agents    │  AI orchestration (Port 8001)
│  Service    │  • Segmentation Agent
│  (FastAPI)  │  • Media Fusion Agent
└──────┬──────┘  • NBA Agent
       │
       ├──────────┐
       ▼          ▼
┌──────────┐  ┌──────────────┐
│  Gemini  │  │ MCP Servers  │  Data abstraction (Ports 3001-3005)
│ 2.0 Flash│  │ • Trade      │  • Mock data (demo)
└──────────┘  │ • Risk       │  • Production ready
              │ • Market     │
              │ • News       │
              │ • Client     │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  PostgreSQL  │  Agent state only
              │  (Cloud SQL) │  • Alerts
              └──────────────┘  • Actions
                                • Switch probability history
```

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Google Cloud Project (for Gemini API)

### **1. Clone Repository**

```bash
git clone https://github.com/sudsk/trading-intelligence-agent.git
cd trading-intelligence-agent
```

### **2. Start Everything (Docker Compose)**

```bash
# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export GEMINI_API_KEY=your-api-key

# Start all services (8 containers)
docker-compose up

# Services will be available at:
# - Frontend: http://localhost:3000
# - API Façade: http://localhost:8000
# - Agents Service: http://localhost:8001
# - MCP Servers: http://localhost:3001-3005
# - PostgreSQL: localhost:5432
```

### **3. Test API**

```bash
# Health check
curl http://localhost:8001/health

# Analyze client
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}'
```

---

## 📊 Example Output

```json
{
  "client_id": "ACME_FX_023",
  "segment": "Trend Follower",
  "confidence": 0.85,
  "switch_probability": 0.64,
  "switch_method": "HMM/change-point",
  "switch_components": {
    "pattern_instability": 0.18,
    "changepoint_detection": 0.20,
    "momentum_shifts": 0.12,
    "flip_acceleration": 0.11,
    "feature_drift": 0.03
  },
  "drivers": [
    "High momentum-beta correlation",
    "Short holding periods (2.8 days avg)",
    "Aggressive market order execution (85%)"
  ],
  "risk_flags": [
    "EUR concentration 72%"
  ],
  "media_pressure": "HIGH",
  "media_sentiment": -0.58,
  "recommendations": [
    {
      "action": "PROACTIVE_OUTREACH",
      "priority": "HIGH",
      "urgency": "URGENT",
      "message": "Switch probability 64% + EUR concentration creates high churn risk",
      "products": [
        "EURUSD forward strips (3-month ladder)",
        "Options collars for EUR exposure"
      ],
      "suggested_actions": [
        "Call client today to discuss positioning",
        "Prepare EUR concentration analysis",
        "Present hedging scenarios with cost-benefit"
      ],
      "reasoning": "Elevated switch probability combined with 72% EUR concentration creates perfect storm for client defection"
    }
  ]
}
```

---

## 🧠 How It Works

### **1. Segmentation Agent**

Classifies trading behavior into 4 segments:

- **Trend Follower** - Momentum-driven, directional bias
- **Mean Reverter** - Counter-trend, range-bound strategies  
- **Hedger** - Risk mitigation, defensive positioning
- **Trend Setter** - Innovative, first-mover strategies

**Data Used**:
- 90-day trade history (count, instruments, flips, holding periods)
- Current positions (concentrations, leverage)
- Market order ratios

**Output**: Segment, confidence, drivers, risk flags

### **2. Switch Probability (HMM/Change-Point)**

Calculates probability client will switch trading desk using 5 statistical signals:

1. **Pattern Instability** (0.0-0.30) - Rolling variance in trade volume/diversity
2. **Change-Point Detection** (0.0-0.25) - CUSUM test for regime breaks
3. **Momentum Shifts** (0.0-0.20) - Position direction reversals
4. **Flip Acceleration** (0.0-0.15) - Increasing uncertainty indicators
5. **Feature Drift** (0.0-0.10) - Deviation from baseline behavior

**Formula**: `switch_prob = 0.30 (baseline) + Σ(5 signals)`, clamped to [0.15, 0.85]

### **3. Media Fusion Agent**

Analyzes financial news sentiment:

- Fetches last 72 hours of headlines for client exposures
- Gemini scores each headline: sentiment + score (-1.0 to +1.0)
- Calculates aggregate sentiment, velocity, media pressure
- Adjusts switch probability based on media environment

**Pressure Levels**:
- **HIGH**: >20 headlines AND |sentiment| > 0.5 AND |velocity| > 0.3
- **MEDIUM**: >10 headlines OR |sentiment| > 0.3
- **LOW**: Otherwise

### **4. NBA (Next Best Action) Agent**

Generates 1-5 prioritized recommendations using segment-specific playbooks:

**Action Types**:
- `PROACTIVE_OUTREACH` - Switch prob > 0.50 (prevent churn)
- `ENHANCED_MONITORING` - Switch prob 0.35-0.50 (watch closely)
- `PROPOSE_HEDGE` - Risk flags present (mitigate risk)
- `SEND_MARKET_UPDATE` - High media pressure (demonstrate expertise)
- `SUGGEST_OPPORTUNITY` - Stable client (cross-sell)

**16 Segment-Specific Playbooks** (4 segments × 4 scenarios)

Example products:
- **Trend Follower**: Forward strips, momentum algorithms
- **Hedger**: Dynamic hedging programs, tail risk protection

---

## 🏗️ MCP Architecture

**Model Context Protocol** provides clean abstraction for data sources.

### **Demo/PoC: Mock MCP Servers**

5 MCP servers auto-generate realistic CSV data:

- **Trade MCP** (Port 3001) - 2,000 trades across 4 clients
- **Risk MCP** (Port 3002) - Positions + risk metrics
- **Market MCP** (Port 3003) - 90 days OHLCV bars
- **News MCP** (Port 3004) - 200 headlines (72 hours)
- **Client MCP** (Port 3005) - Client metadata

### **Production: Real MCP Servers**

Replace CSV → Database queries:

```python
# Trade MCP: Oracle OMS instead of CSV
def get_client_trades(client_id):
    return oracle_connection.query("SELECT * FROM oms_trades WHERE...")

# Risk MCP: Sybase risk warehouse
# Market MCP: Bloomberg API
# News MCP: Reuters News API
# Client MCP: Salesforce CRM
```

**Agents don't change!** ✅ Just swap MCP server containers.

---

## 📁 Project Structure

```
trading-intelligence-agent/
├── frontend/                    # React SPA
│   ├── src/
│   │   ├── components/
│   │   └── services/
│   └── package.json
│
├── api-facade/                  # API routing layer
│   ├── routes/
│   │   ├── clients.py
│   │   ├── actions.py
│   │   └── alerts.py
│   ├── services/
│   │   ├── agent_client.py
│   │   ├── alert_queue.py
│   │   └── data_service.py
│   └── main.py
│
├── agents-service/              # AI agent orchestration
│   ├── agents/
│   │   ├── orchestrator/
│   │   ├── segmentation_agent/
│   │   │   ├── agent.py
│   │   │   ├── prompts.py
│   │   │   ├── tools.py
│   │   │   └── switch_probability.py   # HMM calculator
│   │   ├── media_fusion_agent/
│   │   └── nba_agent/
│   ├── services/
│   │   ├── mcp_data_service.py         # MCP client
│   │   └── data_service.py             # PostgreSQL (agent state)
│   └── main.py
│
├── mcp-servers/                 # Data abstraction layer
│   ├── trade/
│   ├── risk/
│   ├── market/
│   ├── news/
│   └── client/
│
├── database/
│   └── schema.sql               # PostgreSQL schema (agent state only)
│
├── deploy/                      # Cloud Run deployment
│   ├── deploy_all.sh
│   └── deploy_*.sh
│
├── docker-compose.yml           # Local development
└── README.md                    # This file
```

---

## ☁️ Cloud Deployment

### **Cloud Run Services (8 total)**

```bash
# Set environment
export GOOGLE_CLOUD_PROJECT=your-project-id
export REGION=us-central1

# Deploy all services
./deploy/deploy_all.sh

# Or deploy individually
./deploy/deploy_mcp_trade.sh      # Trade MCP
./deploy/deploy_mcp_risk.sh       # Risk MCP
./deploy/deploy_mcp_market.sh     # Market MCP
./deploy/deploy_mcp_news.sh       # News MCP
./deploy/deploy_mcp_client.sh     # Client MCP
./deploy/deploy_agents_service.sh # Agents
./deploy/deploy_api_facade.sh     # API
```

### **Cloud SQL Database**

```bash
# Create PostgreSQL instance
gcloud sql instances create trading-intelligence-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create trading_intelligence \
  --instance=trading-intelligence-db

# Load schema
gcloud sql connect trading-intelligence-db --user=postgres < database/schema.sql
```

### **Cost Estimate (Demo Traffic)**

| Service | Resources | Monthly Cost |
|---------|-----------|--------------|
| 5× MCP Servers | 512Mi, 0-5 instances | $15 |
| Agents Service | 2Gi, 1-10 instances | $15 |
| API Façade | 1Gi, 1-10 instances | $8 |
| Cloud SQL | db-f1-micro | $7 |
| **Total** | | **~$45/month** |

---

## 🔧 Configuration

### **Environment Variables**

```bash
# agents-service/.env
DATABASE_URL=postgresql://user:pass@host:5432/trading_intelligence
GOOGLE_CLOUD_PROJECT=your-project-id
GEMINI_MODEL=gemini-2.0-flash-exp
MCP_TRADE_SERVER_URL=http://trade-mcp:3001
MCP_RISK_SERVER_URL=http://risk-mcp:3002
MCP_MARKET_SERVER_URL=http://market-mcp:3003
MCP_NEWS_SERVER_URL=http://news-mcp:3004
MCP_CLIENT_SERVER_URL=http://client-mcp:3005

# api-facade/.env
DATABASE_URL=postgresql://user:pass@host:5432/trading_intelligence
AGENTS_SERVICE_URL=http://agents-service:8001
```

---

## 🧪 Testing

### **Run Tests**

```bash
# Agents service
cd agents-service
pytest tests/

# API façade
cd api-facade
pytest tests/
```

### **Manual Testing**

```bash
# Test MCP servers
curl http://localhost:3001/health   # Trade
curl http://localhost:3002/health   # Risk
curl http://localhost:3003/health   # Market
curl http://localhost:3004/health   # News
curl http://localhost:3005/health   # Client

# Test agents service
curl -X POST http://localhost:8001/segment \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}'

# Test full analysis
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}'
```

---

## 📖 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - 10-minute setup guide
- **[INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)** - MCP architecture integration
- **[AGENT_SUMMARY.md](docs/AGENT_SUMMARY.md)** - How each agent works
- **[MCP_ARCHITECTURE.md](docs/MCP_ARCHITECTURE.md)** - Production MCP setup

---

## 🎯 Use Cases

### **Sales & Trading Desks**
- Prioritize client outreach based on churn risk
- Proactive product recommendations
- Risk flag early warning system

### **Relationship Managers**
- Understand client trading behavior
- Time market updates for maximum impact
- Track action outcomes for learning

### **Desk Heads**
- Monitor portfolio of client relationships
- Identify high-value cross-sell opportunities
- Measure RM effectiveness

---

## 🔒 Security

- **Authentication**: Cloud Run IAM for service-to-service
- **Data Privacy**: Client data never leaves your environment
- **API Keys**: Store in Google Secret Manager
- **Network**: Internal-only for MCP servers
- **Database**: Cloud SQL with private IP

---

## 🚧 Roadmap

- [ ] **Agent Memory Bank** - Learn from action outcomes
- [ ] **Multi-asset Support** - FX, Equities, Fixed Income, Commodities
- [ ] **Real-time Streaming** - Live position updates
- [ ] **Mobile App** - iOS/Android for RMs
- [ ] **Voice Interface** - Conversational AI assistant
- [ ] **Advanced Analytics** - Client lifetime value, propensity models

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Cloud** - Gemini 2.0 Flash, Cloud Run, Cloud SQL
- **Model Context Protocol** - Data abstraction standard
- **FastAPI** - Modern Python web framework
- **React** - Frontend framework

---

## 📧 Contact

**Suds** - [@sudsk](https://github.com/sudsk)

**Project Link**: [https://github.com/sudsk/trading-intelligence-agent](https://github.com/sudsk/trading-intelligence-agent)

---

## 🎉 Demo

Try it now: [trading-intelligence-demo.run.app](https://trading-intelligence-demo.run.app)

---

Made with ❤️ for Sales & Trading teams
