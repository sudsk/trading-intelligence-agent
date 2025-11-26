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

![Architecture Diagram](images/tia_arch.png)


## 📂 Project Structure

```
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
├── docs/
    ├── QUICKSTART.md               
    ├── INDEX.md        
    └── PROJECT_SUMMARY.md               
```

---

## 🤖 Agent Details

### **1. Segmentation Agent** 🎯
**Purpose**: Classify client trading behavior into one of 4 segments

**How It Works**:
- **Input**: Client ID → triggers data fetching via tools
- **Tools Called**:
  - `fetch_trades_summary()` - Gets 90-day trade statistics (count, instruments, flips, market order ratio)
  - `fetch_position_snapshot()` - Gets current position concentrations
  - `compute_switch_probability()` - HMM/change-point heuristic (5 signals)
- **Gemini Processing**: 
  - Sends comprehensive prompt (1500+ words) with trade patterns + positions
  - Gemini analyzes momentum alignment, holding periods, flip frequency
  - Returns JSON: segment, confidence, drivers, risk flags
- **Output**: 
  - Segment classification (Trend Follower / Mean Reverter / Hedger / Trend Setter)
  - Switch probability (0.15-0.85) from sophisticated HMM calculation
  - Confidence score (0.0-1.0)
  - 2-3 key drivers explaining the classification
  - Risk flags (concentration, leverage, instability)

**Key Innovation**: 
- Switch probability now uses **5 statistical signals** instead of Gemini's single estimate:
  1. Pattern Instability (rolling variance)
  2. Change-Point Detection (CUSUM test)
  3. Momentum Shifts (direction changes)
  4. Flip Acceleration (position reversal rate)
  5. Feature Drift (deviation from baseline)

**Temperature**: 0.3 (low for consistent classification)

**Example Flow**:
```
Client: ACME_FX_023
→ fetch_trades_summary() → 450 trades, 2.8d avg hold, 3 flips/30d, 85% market orders
→ fetch_position_snapshot() → EURUSD: 72% concentration
→ compute_switch_probability() → 0.51 (high pattern variance + recent change-point)
→ Gemini analyzes → "Trend Follower" (85% confidence)
→ Drivers: ["High momentum-beta", "Short holds", "Aggressive entries"]
→ Risk: ["EUR concentration 72%"]
```

---

### **2. Media Fusion Agent** 📰
**Purpose**: Analyze financial news sentiment impacting client exposures

**How It Works**:
- **Input**: Client ID + list of instruments (exposures)
- **Data Fetching**:
  - Queries headlines from last 72 hours
  - Filters by client's primary instruments (EURUSD, GBPUSD, etc.)
  - Batches up to 20 headlines for efficiency
- **Gemini Processing**:
  - Sends batch of headlines with classification instructions
  - Gemini scores each headline: sentiment (positive/neutral/negative) + score (-1.0 to +1.0)
  - Gemini assesses aggregate: average sentiment, velocity, media pressure
- **Pressure Logic**:
  - **HIGH**: >20 headlines AND |avg sentiment| > 0.5 AND |velocity| > 0.3
  - **MEDIUM**: >10 headlines OR |avg sentiment| > 0.3 OR |velocity| > 0.15
  - **LOW**: Otherwise
- **Output**:
  - Media pressure level (HIGH/MEDIUM/LOW)
  - Average sentiment (-1.0 to +1.0)
  - Sentiment velocity (rate of change)
  - Top 5 headlines with individual scores
  - Gemini's reasoning

**Key Features**:
- Batch processing (efficient token usage)
- Trader-focused sentiment (not general news)
- Velocity tracking (accelerating negative news = higher pressure)
- Fallback to keyword-based if Gemini unavailable

**Temperature**: 0.2 (very low for consistent scoring)

**Example Flow**:
```
Client: ACME_FX_023, Exposures: [EURUSD, GBPUSD]
→ Fetch headlines → 18 EUR-related headlines (last 72h)
→ Batch to Gemini → 
   "ECB Signals Rate Hold" → sentiment: negative, score: -0.6
   "EUR Falls on Weak PMI" → sentiment: negative, score: -0.7
   ...
→ Aggregate: avg_sentiment = -0.58, velocity = -0.18
→ Pressure: HIGH (18 headlines + strong negative + accelerating)
→ Reasoning: "High volume of negative EUR news with accelerating bearish sentiment"
```

---

### **3. NBA Agent** 💡
**Purpose**: Generate relationship manager recommendations (Next Best Actions)

**How It Works**:
- **Input**: Complete client context from Segmentation + Media agents:
  - Segment, switch probability, confidence
  - Risk flags, primary exposure
  - Media pressure, sentiment
  - Key drivers
- **Gemini Processing**:
  - Builds rich prompt with segment-specific playbooks (4 segments × 4 scenarios)
  - Gemini selects 1-5 actions based on:
    - Switch prob > 0.50 → PROACTIVE_OUTREACH
    - Risk flags → PROPOSE_HEDGE
    - High media → SEND_MARKET_UPDATE
    - Stable → SUGGEST_OPPORTUNITY
  - Returns JSON array of recommendations
- **Validation**:
  - Ensures action types are valid (5 types)
  - Ensures priorities are valid (HIGH/MEDIUM/LOW)
  - Ensures products and action steps are present
- **Output**:
  - 1-5 prioritized recommendations
  - Each with: action, priority, message, 2-4 products, 3-5 action steps, reasoning

**Action Types** (per spec):
1. **PROACTIVE_OUTREACH** - Switch prob > 0.50 (prevent churn)
2. **ENHANCED_MONITORING** - Switch prob 0.35-0.50 (watch closely)
3. **PROPOSE_HEDGE** - Risk flags present (mitigate risk)
4. **SEND_MARKET_UPDATE** - High media pressure (demonstrate expertise)
5. **SUGGEST_OPPORTUNITY** - Stable client (cross-sell)

**Playbooks** (segment-specific products):
- **Trend Follower**: Forward strips, options collars, momentum algorithms
- **Mean Reverter**: Range products, volatility strategies, pairs trading
- **Hedger**: Dynamic hedging, basis swaps, tail risk protection
- **Trend Setter**: Alpha strategies, thematic products, smart beta

**Temperature**: 0.4 (higher for creative recommendations)

**Example Flow**:
```
Client: ACME_FX_023
Context:
  - Segment: Trend Follower (85% confidence)
  - Switch prob: 0.64 (HIGH)
  - Risk: EUR concentration 72%
  - Media: HIGH pressure, -0.58 sentiment
  - Drivers: Momentum-beta, short holds
  
→ Gemini analyzes playbooks →
   Recommendation 1: PROACTIVE_OUTREACH (HIGH priority, URGENT)
   - Message: "Switch prob 64% + EUR concentration = high churn risk"
   - Products: ["EURUSD forward strips (3-month)", "Options collars"]
   - Actions: ["Call today", "Prepare analysis", "Present hedging scenarios"]
   - Reasoning: "Elevated switch prob + concentration creates perfect storm"
   
   Recommendation 2: PROPOSE_HEDGE (HIGH priority)
   - Message: "EUR concentration 72% creates single-point failure"
   - Products: ["EURUSD put options", "Cross-hedge via EURGBP"]
   - Actions: ["Calculate hedge ratio", "Present cost-benefit", "Discuss outlook"]
   - Reasoning: "Concentration risk amplified by negative media"
```

---

## 🔄 Orchestrator Flow

**The orchestrator coordinates all three agents:**

```
1. Call Segmentation Agent
   → Get: segment, switch_prob (HMM-based), confidence, drivers, risk_flags
   
2. Extract exposures from segmentation
   → Primary exposure + top instruments
   
3. Call Media Fusion Agent
   → Get: pressure, sentiment, velocity, headlines
   
4. Adjust switch probability based on media
   → HIGH negative media → +0.10
   → HIGH positive media → -0.05
   → MEDIUM → ±0.05
   
5. Call NBA Agent with full context
   → Get: 1-5 prioritized recommendations
   
6. Assemble complete profile
   → Return to API façade
```

**Key Design**: 
- Segmentation provides base switch prob (HMM/change-point)
- Media provides adjustment factor (market sentiment)
- NBA uses final switch prob for action selection


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

- **QUICKSTART.md** - Quickstart
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


