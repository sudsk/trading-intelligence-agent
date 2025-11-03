# 🚀 Quick Reference Card

## Project Structure
```
trading-intelligence-agent/
├── docs/              ← Documentation (START HERE: INDEX.md)
├── deploy/            ← Deployment scripts
├── shared/            ← Type contracts
├── agents-service/    ← Gemini agents (Port 8001)
├── api-facade/        ← API layer (Port 8000)
├── frontend/          ← React UI (Port 3000)
└── database/          ← PostgreSQL schema
```

---

## 📖 Essential Docs

| Doc | Purpose |
|-----|---------|
| `docs/INDEX.md` | Navigation hub (START HERE) |
| `docs/PROJECT_SUMMARY.md` | What you built |
| `docs/QUICKSTART.md` | Run locally in 5 min |
| `docs/DEPLOYMENT_COMPLETE.md` | Deploy to Cloud Run |

---

## 🏃 Quick Start

### Run Locally
```bash
# Terminal 1: Agents Service
cd agents-service/
cp .env.example .env  # Edit DATABASE_URL
pip install -r requirements.txt
uvicorn main:app --port 8001 --reload

# Terminal 2: API Façade
cd api-facade/
cp .env.example .env  # Edit AGENTS_SERVICE_URL=http://localhost:8001
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload

# Terminal 3: Frontend
cd frontend/
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
npm start
```

### Deploy to Cloud Run
```bash
cd deploy/

export DATABASE_URL="postgresql://user:pass@host/db"
export PROJECT_ID="your-gcp-project"

./deploy_agents_service.sh $PROJECT_ID
# Note the URL from output

export AGENTS_SERVICE_URL="https://agents-service-xxx.run.app"
./deploy_api_facade.sh $PROJECT_ID
```

---

## 🧪 Test Commands

### Test Agents Service
```bash
# Health
curl http://localhost:8001/health

# Complete profile (orchestrator)
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}' | jq .

# Segmentation only
curl -X POST http://localhost:8001/segment \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}' | jq .

# Media analysis
curl -X POST http://localhost:8001/media \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023", "exposures": ["EURUSD"]}' | jq .

# Recommendations
curl -X POST http://localhost:8001/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "ACME_FX_023",
    "segment": "Trend Follower",
    "switch_prob": 0.6,
    "risk_flags": ["EUR concentration"],
    "media_pressure": "HIGH",
    "primary_exposure": "EURUSD"
  }' | jq .
```

### Test API Façade
```bash
# Health
curl http://localhost:8000/health

# List clients
curl "http://localhost:8000/api/v1/clients?limit=10" | jq .

# Client profile
curl "http://localhost:8000/api/v1/clients/ACME_FX_023/profile" | jq .

# Timeline
curl "http://localhost:8000/api/v1/clients/ACME_FX_023/timeline" | jq .

# SSE stream (keep running)
curl -N "http://localhost:8000/alerts/stream"

# Force event (in another terminal)
curl -X POST http://localhost:8000/api/v1/demo/trigger-alert \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}' | jq .

# Log action
curl -X POST http://localhost:8000/api/v1/actions \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "ACME_FX_023",
    "action_type": "PROACTIVE_OUTREACH",
    "title": "Scheduled strategy call",
    "rm": "John Smith"
  }' | jq .
```

---

## 🎯 Key Files

### Configuration
- `agents-service/.env.example` → Agents config template
- `api-facade/.env.example` → API config template

### Deployment
- `deploy/deploy_agents_service.sh` → Deploy agents
- `deploy/deploy_api_facade.sh` → Deploy API

### Prompts (Customize Here)
- `agents-service/agents/segmentation_agent/prompts.py` → 4 segments
- `agents-service/agents/media_fusion_agent/prompts.py` → Sentiment logic
- `agents-service/agents/nba_agent/prompts.py` → 5 action types + playbooks

### API Endpoints
- `agents-service/main.py` → 5 agent endpoints
- `api-facade/routes/*.py` → 12 API endpoints

### Type Contracts
- `shared/agent_contracts.py` → Pydantic models

---

## 🤖 The 3 Agents

| Agent | Purpose | Model | Output |
|-------|---------|-------|--------|
| **Segmentation** | Classify clients into 4 segments | Gemini Flash 2.5 | Segment, confidence, switch prob |
| **Media Fusion** | Analyze headlines sentiment | Gemini Flash 2.5 | Pressure, sentiment, headlines |
| **NBA** | Generate RM recommendations | Gemini Flash 2.5 | Actions, products, priorities |

**Orchestrator** coordinates all 3 agents + adjusts switch probability based on media.

---

## 📊 API Endpoints

### Agents Service (Port 8001)
- `POST /analyze` → Complete profile (orchestrator)
- `POST /segment` → Segmentation only
- `POST /media` → Media analysis only
- `POST /recommend` → Recommendations only
- `POST /health` → Health check

### API Façade (Port 8000)
- `GET /api/v1/clients` → List clients
- `GET /api/v1/clients/{id}/profile` → Complete profile
- `GET /api/v1/clients/{id}/timeline` → Historical regimes
- `GET /api/v1/clients/{id}/insights` → Recent insights
- `GET /api/v1/clients/{id}/media` → Media analysis
- `POST /api/v1/actions` → Log action
- `GET /api/v1/actions/{client_id}` → Action history
- `GET /alerts/stream` → SSE alerts
- `GET /alerts/history` → Recent alerts
- `POST /api/v1/demo/trigger-alert` → Force Event
- `POST /api/v1/demo/reset-demo` → Reset demo
- `GET /health` → Health check

---

## 🔧 Environment Variables

### Agents Service
```bash
DATABASE_URL=postgresql://user:pass@host:5432/trading_intelligence
GOOGLE_CLOUD_PROJECT=your-project-id
GEMINI_MODEL=gemini-2.0-flash-exp
PORT=8001
```

### API Façade
```bash
AGENTS_SERVICE_URL=http://localhost:8001
DATABASE_URL=postgresql://user:pass@host:5432/trading_intelligence
CORS_ORIGINS=http://localhost:3000
PORT=8000
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Gemini API error" | Set GOOGLE_APPLICATION_CREDENTIALS or run `gcloud auth application-default login` |
| "Database connection failed" | Check DATABASE_URL format and database accessibility |
| "Module not found" | Run `pip install -r requirements.txt` |
| "Health check degraded" | Check Gemini API access and database connection |
| "SSE stream not working" | Check CORS_ORIGINS includes frontend URL |
| "Import error for shared/" | Ensure shared/ is in Python path or use correct imports |

---

## 📈 Status

| Component | Status | Lines |
|-----------|--------|-------|
| Agents Service | ✅ 100% | 3,230 |
| API Façade | ✅ 100% | 1,640 |
| Shared | ✅ 100% | 450 |
| Deploy Scripts | ✅ 100% | 200 |
| Documentation | ✅ 100% | - |
| **TOTAL** | **✅ 100%** | **5,320+** |

---

## 💡 Quick Tips

1. **Always start in repo root** (`trading-intelligence-agent/`)
2. **Read docs/INDEX.md first** for full navigation
3. **Deploy scripts are in deploy/** folder
4. **Test locally before deploying** (faster iteration)
5. **Customize prompts in agents/*/prompts.py** files
6. **Check logs**: `gcloud run logs read SERVICE_NAME`

---

## 🎯 Common Tasks

### Add a new segment
1. Edit `agents-service/agents/segmentation_agent/prompts.py`
2. Update SYSTEM_INSTRUCTION with new segment definition
3. Restart service

### Change Gemini temperature
1. Edit `agents-service/agents/*/agent.py`
2. Find `generation_config = {"temperature": 0.3, ...}`
3. Adjust temperature value

### Add a new product to playbook
1. Edit `agents-service/agents/nba_agent/prompts.py`
2. Find playbook for relevant segment
3. Add product to list

### View real-time logs
```bash
# Local
# Check terminal output

# Cloud Run
gcloud run logs read agents-service --region=us-central1
gcloud run logs read api-facade --region=us-central1
```

---

**For full documentation, see `docs/INDEX.md`** 📚
