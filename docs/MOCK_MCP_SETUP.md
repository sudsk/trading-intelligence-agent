# Mock MCP Setup Guide - Demo/PoC

## 🎯 Perfect! Demo/PoC with MCP from Day 1

**Your Requirement**: Use MCP architecture from the start, but with mock data sources (no Oracle, Bloomberg, etc.).

**Solution**: Mock MCP servers that read from CSV files.

---

## 🏗️ Architecture

```
Agents Service (production MCP interface)
     │
     │ HTTP/MCP Protocol
     │
┌────┴────┬────────┬────────┬────────┬────────┐
▼         ▼        ▼        ▼        ▼        ▼
Trade   Risk   Market   News   Client
Mock    Mock   Mock     Mock   Mock
MCP     MCP    MCP      MCP    MCP
:3001   :3002  :3003    :3004  :3005
│       │      │        │      │
▼       ▼      ▼        ▼      ▼
CSV     CSV    CSV      CSV    CSV
files   files  files    files  files
```

**Key**: Production MCP interface + Mock backends = Easy swap later!

---

## 📦 What You Get

1. **mcp_data_service.py** - Production MCP client
2. **simple_trade_mcp_server.py** - Mock MCP server template
3. **Docker Compose** - Run all 5 MCP servers
4. **CSV generators** - Realistic mock data

---

## 🚀 Quick Start

### **Step 1: Use MCP Data Service**

```python
# agents-service/main.py
from services.mcp_data_service import MCPDataService
app.state.data_service = MCPDataService()
```

### **Step 2: Start Mock MCP Servers**

```bash
# Clone simple_trade_mcp_server.py 5 times
cp simple_trade_mcp_server.py mcp-servers/trade/server.py
cp simple_trade_mcp_server.py mcp-servers/risk/server.py
# ... etc

# Run with Docker Compose
docker-compose up
```

### **Step 3: Test**

```bash
curl -X POST http://localhost:8001/analyze \
  -d '{"client_id": "ACME_FX_023"}'
```

---

## ✅ Benefits

- ✅ Production MCP architecture from day 1
- ✅ Easy to swap mock → real later
- ✅ No Oracle/Bloomberg setup needed
- ✅ Portable (runs anywhere)
- ✅ Fast iteration

---

**Files**:
- `mcp_data_service.py` - Client
- `simple_trade_mcp_server.py` - Server template
- `MOCK_MCP_SETUP.md` - This guide
