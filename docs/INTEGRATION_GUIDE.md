# Integration Guide - MCP Architecture

Complete guide for integrating MCP architecture into your existing repo.

## 🎯 Quick Start (30 minutes)

### **1. Copy New Files**

```bash
# Copy to your repo
cp mcp_data_service.py <repo>/agents-service/services/
cp switch_probability.py <repo>/agents-service/agents/segmentation_agent/
cp agent.py <repo>/agents-service/agents/nba_agent/
cp -r mcp-servers/ <repo>/
cp docker-compose.yml <repo>/
cp -r deploy/ <repo>/
```

### **2. Modify Existing Files**

**agents-service/main.py** (2 lines):
```python
from services.mcp_data_service import MCPDataService  # Changed
app.state.data_service = MCPDataService()  # Changed
```

**agents-service/requirements.txt** (add 1 line):
```
scipy==1.11.0
```

**agents-service/.env.example** (add 5 lines):
```bash
MCP_TRADE_SERVER_URL=http://localhost:3001
MCP_RISK_SERVER_URL=http://localhost:3002
MCP_MARKET_SERVER_URL=http://localhost:3003
MCP_NEWS_SERVER_URL=http://localhost:3004
MCP_CLIENT_SERVER_URL=http://localhost:3005
```

### **3. Test**

```bash
docker-compose up
curl http://localhost:8001/analyze -d '{"client_id":"ACME_FX_023"}'
```

---

## ✅ Files Created

**Core (3)**:
- mcp_data_service.py
- switch_probability.py
- agent.py (NBA fixed)

**MCP Servers (20)**:
- 5× server.py
- 5× Dockerfile
- 5× requirements.txt
- 5× .dockerignore

**Deploy (8)**:
- docker-compose.yml
- deploy_all.sh
- deploy_agents_service.sh
- deploy_api_facade.sh
- 5× deploy_mcp_*.sh

**Docs (3)**:
- INTEGRATION_GUIDE.md
- GAP_ANALYSIS.md
- MOCK_MCP_SETUP.md

**Total: 34 files** ✅

---

See GAP_ANALYSIS.md for detailed file-by-file comparison.
