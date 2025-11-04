# Trading Intelligence Agent 

## 🎯 Overview

**What it is:** A Trading Intelligence Agent delivered as a standalone React web app. It profiles each client (Trend Follower / Trend Setter / Mean-Reverter / Hedger), estimates Switch Probability (14d), and surfaces Next Best Actions for the desk. Advisory only—no execution.

**Who cares:** Sales & trading leads, RMs, sales-traders, desk heads—anyone prioritising outreach timing and product pitching.

**What they see (UI):**

**Strategy Profile card:** Segment, confidence, top drivers, risk flags, switch probability.

**Media ribbon:** last 3 headlines + sentiment and a Media Pressure chip.

**Timeline:** historical strategy regimes (6–12 months) with event windows.

**Insights feed:** Signals, Actions, Outcomes.

**List view:** “Clients with Rising Switch Risk,” sortable/filterable.

**Action bar:** one-click Create Task, Share Summary, Propose Product (logged in-app).

**Data (mocked but credible):** trades, positions, PnL/VAR, market bars, macro calendar & headlines (sentiment/velocity/topics).

**How it works (Vertex ADK):**
- React calls a thin Cloud Run façade (/api/v1/*).
- The façade invokes a Vertex AI ADK agent (deployed to Agent Engine) to: compute segments, estimate switch probability, fuse media signals, and propose NBAs.
- Mocked data services (CSV/JSON) provide trades/positions/markets/media to the agent tools.
- SSE streams from the façade simulate live alerts (or relay agent events).

**Optional:** Memory Bank to persist “Action → Outcome” per client for learning.

**Why it impresses:** Predictive feel, trading-native language, one-click action loop, longitudinal depth, clean agentic fit with a credible path to production.

**Success criteria:** sub-300ms UI loads (from mock), at least one live alert during the demo, actions logged to Insights, timeline & list view fully functional.

---

## 📐 Architecture

![Architecture Diagram](images/cia_arch.png)


## 📂 Project Structure

```
/outputs/
├── shared/
│   └── agent_contracts.py          # Type-safe contracts between services
│
├── agents-service/                  # ✅ 100% COMPLETE
│   ├── main.py                      # FastAPI app with 5 endpoints
│   ├── agents/
│   │   ├── segmentation_agent/      # Gemini-powered classification
│   │   │   ├── agent.py
│   │   │   ├── prompts.py           # 1500+ words of instructions
│   │   │   └── tools.py             # Data fetching functions
│   │   ├── media_fusion_agent/      # Gemini-powered sentiment
│   │   │   ├── agent.py
│   │   │   └── prompts.py
│   │   ├── nba_agent/               # Gemini-powered recommendations
│   │   │   ├── agent.py
│   │   │   └── prompts.py
│   │   └── orchestrator_agent/      # Coordination logic
│   │       └── agent.py
│   ├── services/
│   │   └── data_service.py          # PostgreSQL access
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── api-facade/                      
│   ├── main.py                      # FastAPI app
│   ├── routes/
│   │   ├── clients.py              
│   │   ├── actions.py              
│   │   ├── alerts.py               
│   │   └── demo.py                 
│   ├── services/
│   │   ├── agent_client.py         # HTTP client to agents-service
│   │   ├── alert_queue.py          
│   │   └── data_service.py         
│   ├── Dockerfile                   
│   ├── requirements.txt             
│   └── .env.example                 
│
├── BUILD_COMPLETE.md               # Comprehensive status
├── IMPLEMENTATION_STATUS.md        # Detailed progress
└── BUILD_PROGRESS.md               # Quick reference
```

---

## 🤖 Agent Details

### 1. Segmentation Agent (Pure Gemini)

**Purpose:** Classify clients into 4 trading segments

**Segments:**
- **Trend Follower**: Momentum-driven, short holds, directional
- **Mean Reverter**: Contrarian, frequent flips, range-bound
- **Hedger**: Long holds, defensive, risk mitigation
- **Trend Setter**: Anticipatory, leading indicators, alpha

**How It Works:**
1. Fetches 90-day trade summary (via tools)
2. Fetches position concentrations
3. Calls Gemini with comprehensive prompt (1500+ words)
4. Gemini analyzes patterns and outputs JSON
5. Returns segment, confidence, switch probability, drivers, risk flags

**Key Features:**
- Structured JSON output (`response_mime_type="application/json"`)
- Temperature: 0.3 (consistent classification)
- Fallback heuristics if Gemini unavailable
- Few-shot examples in prompts

---

### 2. Media Fusion Agent (Pure Gemini)

**Purpose:** Analyze financial news sentiment

**How It Works:**
1. Fetches last 72 hours of headlines for client's exposures
2. Batches up to 20 headlines
3. Calls Gemini for sentiment classification
4. Gemini scores each headline (-1 to +1)
5. Computes aggregates: avg sentiment, velocity, pressure
6. Returns pressure (HIGH/MEDIUM/LOW), top headlines, reasoning

**Pressure Logic:**
- **HIGH**: >20 headlines AND |avg| > 0.5 AND |velocity| > 0.3
- **MEDIUM**: >10 headlines OR |avg| > 0.3 OR |velocity| > 0.15
- **LOW**: Otherwise

**Key Features:**
- Batch processing (efficient)
- Trader-focused sentiment (not general news)
- Temperature: 0.2 (consistent scoring)
- Fallback keyword-based sentiment

---

### 3. NBA Agent (Pure Gemini)

**Purpose:** Generate relationship manager recommendations

**Action Types:**
1. **PROACTIVE_OUTREACH** (switch prob > 0.50)
2. **ENHANCED_MONITORING** (switch prob 0.35-0.50)
3. **PROPOSE_HEDGE** (risk flags present)
4. **SEND_MARKET_UPDATE** (high media pressure)
5. **SUGGEST_OPPORTUNITY** (stable client)

**How It Works:**
1. Receives client profile + context
2. Calls Gemini with segment-specific playbooks
3. Gemini selects actions, products, priorities
4. Returns 1-5 prioritized recommendations with reasoning

**Playbooks:**
- Separate playbooks for each segment
- Scenario-specific (high switch, hedge, opportunity)
- 20+ products per segment

**Key Features:**
- Temperature: 0.4 (creative but consistent)
- Priority determination (HIGH/MEDIUM/LOW)
- Product suggestions (specific, not generic)
- Action steps (3-5 concrete next steps)

---

### 4. Orchestrator Agent

**Purpose:** Coordinate all specialist agents

**Flow:**
1. Call Segmentation Agent → segment, switch prob
2. Extract exposures
3. Call Media Agent → sentiment, pressure
4. **Adjust switch prob** based on media:
   - HIGH negative media → +0.10
   - HIGH positive media → -0.05
   - MEDIUM → ±0.05
5. Call NBA Agent with complete context
6. Assemble full profile
7. Return to API

**Key Feature:** Media-driven switch probability adjustment

---

## 🚀 Quick Start

### 1. Set Up Environment

```bash
# Clone repository
git clone <repo-url>
cd trading-intelligence-agent

# Set up Python virtual environment
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Configure Environment Variables

```bash
# agents-service/.env
cp agents-service/.env.example agents-service/.env

# Edit .env:
DATABASE_URL=postgresql://user:pass@host:5432/dbname
GOOGLE_CLOUD_PROJECT=your-project-id
GEMINI_MODEL=gemini-2.0-flash-exp
```

### 3. Install Dependencies

```bash
# Agents service
cd agents-service
pip install -r requirements.txt
```

### 4. Run Locally

```bash
# Terminal 1: Agents Service
cd agents-service
uvicorn main:app --port 8001 --reload

# Terminal 2: API Façade (once complete)
cd api-facade
uvicorn main:app --port 8000 --reload

# Terminal 3: Frontend
cd frontend
npm start
```

### 5. Test Agents Service

```bash
# Health check
curl http://localhost:8001/health

# Get client profile
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}'

# Get segmentation only
curl -X POST http://localhost:8001/segment \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}'
```

---

## 🌩️ Deploy to Cloud Run

### Deploy Agents Service

```bash
cd agents-service

# Build and deploy
gcloud run deploy agents-service \
  --source . \
  --region us-central1 \
  --platform managed \
  --set-env-vars DATABASE_URL=postgresql://...,GOOGLE_CLOUD_PROJECT=... \
  --allow-unauthenticated  # For testing; remove for production

# Get URL
gcloud run services describe agents-service \
  --region us-central1 \
  --format 'value(status.url)'
```

### Deploy API Façade (once complete)

```bash
cd api-facade

# Deploy
gcloud run deploy api-facade \
  --source . \
  --region us-central1 \
  --set-env-vars AGENTS_SERVICE_URL=https://agents-service-xxx.run.app \
  --allow-unauthenticated

# Update frontend
echo "REACT_APP_API_URL=https://api-facade-xxx.run.app" > frontend/.env.production
```

---

## 🔧 Development

### Adding a New Agent

1. Create agent directory:
```bash
mkdir -p agents-service/agents/new_agent
touch agents-service/agents/new_agent/prompts.py
touch agents-service/agents/new_agent/agent.py
```

2. Define prompts (`prompts.py`):
```python
SYSTEM_INSTRUCTION = """
You are an expert [domain]...
"""
```

3. Implement agent (`agent.py`):
```python
from google import generativeai as genai

class NewAgent:
    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction=SYSTEM_INSTRUCTION
        )
```

4. Register in orchestrator

---

## 🧪 Testing

### Test Individual Agents

```python
# Test segmentation
from agents.segmentation_agent.agent import SegmentationAgent
from services.data_service import DataService

data_service = DataService()
agent = SegmentationAgent(data_service)
result = agent.analyze("ACME_FX_023")
print(result)
```

### Integration Tests

```bash
# Run all tests
cd agents-service
python -m pytest tests/

# Test specific agent
python -m pytest tests/test_segmentation_agent.py
```

---

## 📚 Documentation

- **BUILD_COMPLETE.md** - Comprehensive status and next steps
- **IMPLEMENTATION_STATUS.md** - Detailed progress breakdown
- **BUILD_PROGRESS.md** - Quick reference
- Code is extensively commented

---

## 🔄 Migration to Agent Engine

### Current (Cloud Run):
```python
response = await httpx.post(
    "https://agents-service.run.app/analyze",
    json={"client_id": client_id}
)
```

### Future (Agent Engine):
```python
response = await agent_engine_client.invoke(
    agent="orchestrator-agent",
    input={"client_id": client_id}
)
```

**Only 1 file changes:** `services/agent_client.py`

**No frontend changes needed!** ✅

---

## 📝 License

[Your License]


