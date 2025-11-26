# Gap Analysis: Current Repo vs MCP Architecture

## 📊 Summary

Based on your GitHub repo README, here's what exists and what's missing for the **MCP architecture with mock data**.

---

## ✅ What EXISTS in Repo (from README)

### **Agents Service** - ✅ COMPLETE
```
agents-service/
├── main.py                                    ✅ EXISTS
├── agents/
│   ├── segmentation_agent/
│   │   ├── agent.py                          ✅ EXISTS
│   │   ├── prompts.py                        ✅ EXISTS
│   │   └── tools.py                          ✅ EXISTS
│   ├── media_fusion_agent/
│   │   ├── agent.py                          ✅ EXISTS
│   │   └── prompts.py                        ✅ EXISTS
│   ├── nba_agent/
│   │   ├── agent.py                          ✅ EXISTS (but NEEDS UPDATE)
│   │   └── prompts.py                        ✅ EXISTS
│   └── orchestrator_agent/
│       └── agent.py                          ✅ EXISTS
├── services/
│   └── data_service.py                       ✅ EXISTS (but uses PostgreSQL)
├── Dockerfile                                 ✅ EXISTS
├── requirements.txt                           ✅ EXISTS
└── .env.example                              ✅ EXISTS
```

### **API Façade** - ✅ COMPLETE
```
api-facade/
├── main.py                                    ✅ EXISTS
├── routes/
│   ├── clients.py                            ✅ EXISTS
│   ├── actions.py                            ✅ EXISTS
│   ├── alerts.py                             ✅ EXISTS
│   └── demo.py                               ✅ EXISTS
├── services/
│   ├── agent_client.py                       ✅ EXISTS
│   ├── alert_queue.py                        ✅ EXISTS
│   └── data_service.py                       ✅ EXISTS
├── Dockerfile                                 ✅ EXISTS
├── requirements.txt                           ✅ EXISTS
└── .env.example                              ✅ EXISTS
```

### **Shared**
```
shared/
└── agent_contracts.py                        ✅ EXISTS
```

### **Documentation**
```
docs/
├── QUICKSTART.md                             ✅ EXISTS
├── INDEX.md                                  ✅ EXISTS
└── PROJECT_SUMMARY.md                        ✅ EXISTS
```

---

## ❌ What's MISSING for MCP Architecture

### **1. MCP Data Service** - ❌ MISSING (NEW FILE NEEDED)
```
agents-service/services/
└── mcp_data_service.py                       ❌ NEEDS TO BE CREATED
```
**Status**: I've already created this → `/mnt/user-data/outputs/mcp_data_service.py`

**Action**: Copy to `agents-service/services/mcp_data_service.py`

---

### **2. HMM Switch Probability Calculator** - ❌ MISSING (NEW FILE NEEDED)
```
agents-service/agents/segmentation_agent/
└── switch_probability.py                     ❌ NEEDS TO BE CREATED
```
**Status**: I've already created this → `/mnt/user-data/outputs/switch_probability.py`

**Action**: Copy to `agents-service/agents/segmentation_agent/switch_probability.py`

---

### **3. Updated NBA Agent** - ⚠️ NEEDS UPDATE
```
agents-service/agents/nba_agent/
└── agent.py                                  ⚠️ EXISTS BUT OUTDATED
```
**Issue**: Current version has:
- Character encoding issues (broken emojis)
- Wrong action format (suggestedActions vs suggested_actions)
- Only 4 fallback scenarios (spec requires 7)
- Missing segment-specific playbooks

**Status**: I've created fixed version → `/mnt/user-data/outputs/agent.py`

**Action**: Replace existing `agents-service/agents/nba_agent/agent.py`

---

### **4. MCP Servers** - ❌ COMPLETELY MISSING (NEW DIRECTORY NEEDED)
```
mcp-servers/                                  ❌ ENTIRE DIRECTORY MISSING
├── trade/
│   ├── server.py                            ❌ NEEDS TO BE CREATED
│   ├── requirements.txt                     ❌ NEEDS TO BE CREATED
│   ├── Dockerfile                           ❌ NEEDS TO BE CREATED
│   └── data/
│       └── trades.csv                       ❌ NEEDS TO BE CREATED
├── risk/
│   ├── server.py                            ❌ NEEDS TO BE CREATED
│   ├── requirements.txt                     ❌ NEEDS TO BE CREATED
│   ├── Dockerfile                           ❌ NEEDS TO BE CREATED
│   └── data/
│       ├── positions.csv                    ❌ NEEDS TO BE CREATED
│       └── risk_metrics.csv                 ❌ NEEDS TO BE CREATED
├── market/
│   ├── server.py                            ❌ NEEDS TO BE CREATED
│   ├── requirements.txt                     ❌ NEEDS TO BE CREATED
│   ├── Dockerfile                           ❌ NEEDS TO BE CREATED
│   └── data/
│       └── market_bars.csv                  ❌ NEEDS TO BE CREATED
├── news/
│   ├── server.py                            ❌ NEEDS TO BE CREATED
│   ├── requirements.txt                     ❌ NEEDS TO BE CREATED
│   ├── Dockerfile                           ❌ NEEDS TO BE CREATED
│   └── data/
│       └── headlines.csv                    ❌ NEEDS TO BE CREATED
└── client/
    ├── server.py                            ❌ NEEDS TO BE CREATED
    ├── requirements.txt                     ❌ NEEDS TO BE CREATED
    ├── Dockerfile                           ❌ NEEDS TO BE CREATED
    └── data/
        ├── clients.csv                      ❌ NEEDS TO BE CREATED
        └── actions.csv                      ❌ NEEDS TO BE CREATED
```

**Status**: I've created template → `/mnt/user-data/outputs/simple_trade_mcp_server.py`

**Action**: 
1. Create `mcp-servers/` directory structure
2. Copy template to each MCP server
3. Modify for specific data types
4. Generate CSV files

---

### **5. Docker Compose** - ❌ MISSING (NEW FILE NEEDED)
```
docker-compose.yml                            ❌ NEEDS TO BE CREATED
```
**Purpose**: Run all 8 Cloud Run services locally

**Action**: Create `docker-compose.yml` with 8 services

---

### **6. Deploy Scripts** - ❌ MISSING (NEW DIRECTORY NEEDED)
```
deploy/                                       ❌ ENTIRE DIRECTORY MISSING
├── deploy_frontend.sh                       ❌ NEEDS TO BE CREATED
├── deploy_api_facade.sh                     ❌ NEEDS TO BE CREATED
├── deploy_agents_service.sh                 ❌ NEEDS TO BE CREATED
├── deploy_mcp_trade.sh                      ❌ NEEDS TO BE CREATED
├── deploy_mcp_risk.sh                       ❌ NEEDS TO BE CREATED
├── deploy_mcp_market.sh                     ❌ NEEDS TO BE CREATED
├── deploy_mcp_news.sh                       ❌ NEEDS TO BE CREATED
├── deploy_mcp_client.sh                     ❌ NEEDS TO BE CREATED
└── deploy_all.sh                            ❌ NEEDS TO BE CREATED
```

---

### **7. Frontend** - ❓ UNKNOWN STATUS
```
frontend/                                     ❓ NOT MENTIONED IN README
```
The README mentions "React web app" but doesn't show the folder structure.

**Question**: Does `frontend/` directory exist in your repo?

---

### **8. Database Schema** - ❓ UNKNOWN STATUS
```
database/                                     ❓ NOT MENTIONED IN README
├── schema.sql                               ❓ UNKNOWN
└── init.sql                                 ❓ UNKNOWN
```

**Question**: Do you have database schema files?

**Note**: With MCP architecture, database is only for **agent state** (alerts, actions, switch_probability_history), NOT for trades/positions/headlines.

---

## 🔄 Files That Need MODIFICATION (Not Replacement)

### **1. agents-service/main.py** - ⚠️ NEEDS UPDATE
```python
# Current (line ~5):
from services.data_service import DataService

# Change to:
from services.mcp_data_service import MCPDataService

# Current (line ~30):
app.state.data_service = DataService()

# Change to:
app.state.data_service = MCPDataService()
```

### **2. agents-service/requirements.txt** - ⚠️ NEEDS UPDATE
```
# Add this line:
scipy==1.11.0  # For HMM switch probability
```

### **3. agents-service/.env.example** - ⚠️ NEEDS UPDATE
```bash
# Add these lines:
MCP_TRADE_SERVER_URL=http://localhost:3001
MCP_RISK_SERVER_URL=http://localhost:3002
MCP_MARKET_SERVER_URL=http://localhost:3003
MCP_NEWS_SERVER_URL=http://localhost:3004
MCP_CLIENT_SERVER_URL=http://localhost:3005
```

### **4. agents-service/agents/segmentation_agent/tools.py** - ⚠️ NEEDS UPDATE
```python
# Add at top:
from .switch_probability import compute_switch_probability

# Modify fetch_trades_summary() to call:
switch_result = compute_switch_probability(
    client_id=client_id,
    trades_df=trades_df,
    days=90
)
```

### **5. agents-service/agents/segmentation_agent/prompts.py** - ⚠️ NEEDS UPDATE
```python
# Add HMM breakdown to ANALYSIS_PROMPT_TEMPLATE:
Switch Probability (HMM/change-point): {switch_prob:.2f}
  - Pattern Instability: {pattern_score:.2f}
  - Change-Point Detection: {changepoint_score:.2f}
  - Momentum Shifts: {momentum_score:.2f}
  - Flip Acceleration: {flip_score:.2f}
  - Feature Drift: {drift_score:.2f}
```

### **6. agents-service/agents/segmentation_agent/agent.py** - ⚠️ NEEDS UPDATE
```python
# Override Gemini's switch_prob with HMM result:
if 'switch_prob' in tools_result:
    result['switch_prob'] = tools_result['switch_prob']
    result['switch_method'] = 'HMM/change-point'
    result['switch_components'] = tools_result['switch_components']
```

---

## 📋 Action Checklist

### **Phase 1: Core MCP Files** (30 minutes)
- [ ] Copy `mcp_data_service.py` to `agents-service/services/`
- [ ] Copy `switch_probability.py` to `agents-service/agents/segmentation_agent/`
- [ ] Replace `agents-service/agents/nba_agent/agent.py` with fixed version
- [ ] Update `agents-service/main.py` (2 line changes)
- [ ] Update `agents-service/requirements.txt` (add scipy)
- [ ] Update `agents-service/.env.example` (add MCP URLs)

### **Phase 2: HMM Integration** (15 minutes)
- [ ] Update `agents-service/agents/segmentation_agent/tools.py`
- [ ] Update `agents-service/agents/segmentation_agent/prompts.py`
- [ ] Update `agents-service/agents/segmentation_agent/agent.py`

### **Phase 3: MCP Servers** (2 hours)
- [ ] Create `mcp-servers/` directory structure
- [ ] Create Trade MCP Server (copy template + modify)
- [ ] Create Risk MCP Server (copy template + modify)
- [ ] Create Market MCP Server (copy template + modify)
- [ ] Create News MCP Server (copy template + modify)
- [ ] Create Client MCP Server (copy template + modify)
- [ ] Generate mock CSV data files
- [ ] Create Dockerfiles for each MCP server
- [ ] Create requirements.txt for each MCP server

### **Phase 4: Orchestration** (30 minutes)
- [ ] Create `docker-compose.yml`
- [ ] Create `deploy/` directory with 9 deployment scripts
- [ ] Test locally with docker-compose

### **Phase 5: Testing** (30 minutes)
- [ ] Start all MCP servers
- [ ] Start agents-service
- [ ] Test `/analyze` endpoint
- [ ] Verify HMM switch probability in response
- [ ] Verify NBA recommendations format

---

## 📊 Completion Status

| Component | Exists | Works | Needs Update | Missing |
|-----------|--------|-------|--------------|---------|
| **Agents Service** | ✅ | ✅ | ⚠️ (MCP) | - |
| **API Façade** | ✅ | ✅ | - | - |
| **Frontend** | ❓ | ❓ | ❓ | ❓ |
| **MCP Data Service** | ❌ | - | - | ✅ |
| **HMM Switch Calc** | ❌ | - | - | ✅ |
| **NBA Agent (fixed)** | ⚠️ | ⚠️ | ✅ | - |
| **Trade MCP Server** | ❌ | - | - | ✅ |
| **Risk MCP Server** | ❌ | - | - | ✅ |
| **Market MCP Server** | ❌ | - | - | ✅ |
| **News MCP Server** | ❌ | - | - | ✅ |
| **Client MCP Server** | ❌ | - | - | ✅ |
| **Docker Compose** | ❌ | - | - | ✅ |
| **Deploy Scripts** | ❌ | - | - | ✅ |
| **Database Schema** | ❓ | ❓ | ⚠️ (MCP) | ❓ |

---

## 🎯 Estimated Work

| Task | Time | Complexity |
|------|------|------------|
| Copy core MCP files | 30 min | Easy |
| HMM integration | 15 min | Easy |
| Create 5 MCP servers | 2 hours | Medium |
| Docker compose | 30 min | Easy |
| Deploy scripts | 30 min | Easy |
| Testing | 30 min | Easy |
| **TOTAL** | **~4.5 hours** | **Medium** |

---

## 🚀 Next Steps

**Option 1: I create all missing files** (recommended)
- I'll create all 5 MCP servers
- I'll create docker-compose.yml
- I'll create all deploy scripts
- I'll create mock CSV data
- Total: ~50 files

**Option 2: You tell me what else exists**
- Share more details about frontend/
- Share database schema
- I'll fill in only what's truly missing

**Which would you prefer?**
