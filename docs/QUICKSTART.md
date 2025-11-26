
# Quick Start Guide - 10 Minutes to Running System

Get the Trading Intelligence Agent running locally in **10 minutes**.

---

## ⚡ Prerequisites (2 minutes)

### **Required**
- ✅ Docker Desktop installed and running
- ✅ Git installed
- ✅ Google Cloud SDK (`gcloud`) installed ([Install guide](https://cloud.google.com/sdk/docs/install))
- ✅ Google Cloud account with Vertex AI enabled

### **Authenticate with Google Cloud**

```bash
# Login to Google Cloud
gcloud auth login

# Set default project
gcloud config set project your-project-id

# Enable Vertex AI API (if not already enabled)
gcloud services enable aiplatform.googleapis.com

# Set application default credentials for local development
gcloud auth application-default login
```

**✅ This creates credentials at `~/.config/gcloud/application_default_credentials.json`**

---

## 🚀 Step 1: Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/sudsk/trading-intelligence-agent.git
cd trading-intelligence-agent

# Set environment variable (uses your current gcloud project)
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)

# Verify authentication works
gcloud auth application-default print-access-token

# Should output a long access token - this means authentication is working!

# Verify Docker is running
docker ps
```

---

## 🐳 Step 2: Start All Services (3 minutes)

```bash
# Start everything with Docker Compose
docker-compose up -d

# This starts 8 services:
# ✅ PostgreSQL (database)
# ✅ 5 MCP Servers (data layer)
# ✅ Agents Service (AI orchestration with Vertex AI)
# ✅ API Façade (routing)
```

**Note**: Docker containers need access to your credentials:

```yaml
# docker-compose.yml automatically mounts:
volumes:
  - ~/.config/gcloud:/root/.config/gcloud:ro  # Google Cloud credentials
```

**Wait for services to be ready (~1-2 minutes):**

```bash
# Watch logs
docker-compose logs -f

# Look for:
# ✅ "Database connection successful"
# ✅ "Loaded 2000 trades"
# ✅ "Vertex AI client initialized"
# ✅ "Application startup complete"
```

---

## ✅ Step 3: Test the System (2 minutes)

### **Test 1: Health Checks**

```bash
# Check all services are healthy
curl http://localhost:8001/health   # Agents Service
curl http://localhost:8000/health   # API Façade
curl http://localhost:3001/health   # Trade MCP
curl http://localhost:3002/health   # Risk MCP
curl http://localhost:3003/health   # Market MCP
curl http://localhost:3004/health   # News MCP
curl http://localhost:3005/health   # Client MCP

# All should return: {"status": "healthy"}
```

### **Test 2: Analyze a Client**

```bash
# Get complete client profile (calls Vertex AI Gemini)
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}' | jq

# Expected response:
# {
#   "client_id": "ACME_FX_023",
#   "segment": "Trend Follower",
#   "confidence": 0.85,
#   "switch_probability": 0.64,
#   "switch_method": "HMM/change-point",
#   "recommendations": [...]
# }
```

### **Test 3: Try Other Clients**

```bash
# Test different client profiles
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ZEUS_COMM_019"}' | jq

curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "TITAN_EQ_008"}' | jq

curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ATLAS_BOND_012"}' | jq
```

---

## 🎉 Success! You're Running

**All services are now running:**

| Service | URL | Purpose |
|---------|-----|---------|
| **API Façade** | http://localhost:8000 | Main API endpoint |
| **Agents Service** | http://localhost:8001 | AI orchestration (Vertex AI) |
| **Trade MCP** | http://localhost:3001 | Trade data |
| **Risk MCP** | http://localhost:3002 | Risk metrics |
| **Market MCP** | http://localhost:3003 | Market data |
| **News MCP** | http://localhost:3004 | Headlines |
| **Client MCP** | http://localhost:3005 | Client metadata |
| **PostgreSQL** | localhost:5432 | Agent state |

---

## 📊 What You Can Do Now

### **1. Get Client Segmentation**

```bash
curl -X POST http://localhost:8001/segment \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}' | jq
```

**Returns:**
- Segment classification (Trend Follower/Mean Reverter/Hedger/Trend Setter)
- Confidence score
- Key drivers
- Risk flags
- Switch probability (HMM-based)

### **2. Get Media Sentiment**

```bash
curl -X POST http://localhost:8001/media \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023", "instruments": ["EURUSD", "GBPUSD"]}' | jq
```

**Returns:**
- Media pressure level (HIGH/MEDIUM/LOW)
- Average sentiment (-1.0 to +1.0)
- Sentiment velocity
- Top headlines

### **3. Get Next Best Actions**

```bash
curl -X POST http://localhost:8001/recommend \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}' | jq
```

**Returns:**
- 1-5 prioritized recommendations
- Action types (PROACTIVE_OUTREACH, PROPOSE_HEDGE, etc.)
- Specific products
- Concrete action steps

### **4. Full Profile (All Agents)**

```bash
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"client_id": "ACME_FX_023"}' | jq
```

**Returns:**
- Complete profile with all agent outputs combined

---

## 🔍 Explore the Data

### **View Generated Mock Data**

```bash
# Trade data
docker exec -it trading-intelligence-agent-trade-mcp-1 cat /app/data/trades.csv | head -20

# Client metadata
docker exec -it trading-intelligence-agent-client-mcp-1 cat /app/data/clients.csv

# Headlines
docker exec -it trading-intelligence-agent-news-mcp-1 cat /app/data/headlines.csv | head -20
```

### **Check Database**

```bash
# Connect to PostgreSQL
docker exec -it trading-intelligence-agent-db-1 psql -U postgres -d trading_intelligence

# View tables
\dt

# View alerts
SELECT * FROM alerts LIMIT 5;

# View actions
SELECT * FROM actions LIMIT 5;

# Exit
\q
```

---

## 🎨 Optional: Start Frontend (3 minutes)

```bash
# Install dependencies
cd frontend
npm install

# Start React app
npm start

# Open browser
open http://localhost:3000
```

**Frontend features:**
- Strategy profile cards
- Switch probability gauge
- Media ribbon with headlines
- Next best actions list
- Action logging

---

## 🛠️ Useful Commands

### **View Logs**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f agents-service
docker-compose logs -f trade-mcp

# Last 100 lines
docker-compose logs --tail=100 agents-service
```

### **Restart Services**

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart agents-service

# Rebuild after code changes
docker-compose up -d --build agents-service
```

### **Stop Everything**

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### **Check Service Status**

```bash
# List running containers
docker-compose ps

# Check resource usage
docker stats
```

---

## 🐛 Troubleshooting

### **Problem: Services won't start**

```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs | grep -i error

# Restart Docker Desktop
```

### **Problem: "Database connection failed"**

```bash
# Wait for PostgreSQL to be ready (takes ~30 seconds)
docker-compose logs db | grep "ready to accept connections"

# Restart agents-service after DB is ready
docker-compose restart agents-service
```

### **Problem: "Vertex AI authentication error"**

```bash
# Check credentials exist
ls -la ~/.config/gcloud/application_default_credentials.json

# Re-authenticate if needed
gcloud auth application-default login

# Check project is set
gcloud config get-value project
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)

# Restart agents-service to pick up new credentials
docker-compose restart agents-service

# Check logs for auth issues
docker-compose logs agents-service | grep -i "auth\|credential\|permission"
```

### **Problem: "Credentials not found in container"**

```bash
# Verify docker-compose.yml has credentials mount
grep -A 2 "volumes:" docker-compose.yml | grep gcloud

# Should see:
#   - ~/.config/gcloud:/root/.config/gcloud:ro

# If missing, add to agents-service in docker-compose.yml:
#   volumes:
#     - ~/.config/gcloud:/root/.config/gcloud:ro
```

### **Problem: "Vertex AI API not enabled"**

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Verify it's enabled
gcloud services list --enabled | grep aiplatform

# Wait 1-2 minutes for API to be fully available
# Then restart agents-service
docker-compose restart agents-service
```

### **Problem: Port already in use**

```bash
# Check what's using the port
lsof -i :8001
lsof -i :3001

# Change ports in docker-compose.yml:
#   ports:
#     - "8002:8001"  # Use 8002 instead of 8001
```

### **Problem: MCP servers return empty data**

```bash
# MCP servers auto-generate data on first start
# If data is missing, restart the service:
docker-compose restart trade-mcp

# Or delete and regenerate
docker exec -it trading-intelligence-agent-trade-mcp-1 rm /app/data/trades.csv
docker-compose restart trade-mcp

# Check data was generated
docker-compose logs trade-mcp | grep "Generated"
```

---

## 🔐 Authentication Notes

### **How Authentication Works**

1. **Local Development** (this guide):
   ```
   You → gcloud auth → credentials file → Docker mounts → Agents use Vertex AI
   ```

2. **Cloud Run Deployment**:
   ```
   Cloud Run → Service Account → Automatic auth → Agents use Vertex AI
   ```

### **Credential File Location**

```bash
# macOS/Linux
~/.config/gcloud/application_default_credentials.json

# Windows
%APPDATA%\gcloud\application_default_credentials.json
```

### **Which Gemini Model?**

By default, uses **Gemini 2.0 Flash** via Vertex AI:
- Model: `gemini-2.0-flash-exp`
- Region: `us-central1`
- No API key needed - uses Google Cloud authentication

---

## 📚 Next Steps

### **1. Understand the Architecture**

Read the main [README.md](../README.md) to understand:
- How agents work together
- MCP protocol benefits
- Data flow patterns

### **2. Customize the Agents**

- **Modify prompts**: `agents-service/agents/*/prompts.py`
- **Adjust thresholds**: `agents-service/agents/segmentation_agent/switch_probability.py`
- **Add new actions**: `agents-service/agents/nba_agent/agent.py`

### **3. Add Real Data**

Replace mock MCP servers with real data sources:
- Implement production MCP servers connecting to:
  - Oracle OMS (trades)
  - Sybase (risk metrics)
  - Bloomberg API (market data)
  - Reuters (news)
  - Salesforce (client metadata)

### **4. Deploy to Cloud**

```bash
# Deploy to Cloud Run (uses service account authentication)
./deploy/deploy_all.sh
```

Cloud Run deployment automatically handles authentication via service accounts - no credentials file needed!

---

## 💡 Tips

1. **Keep credentials secure**: Never commit `application_default_credentials.json` to git
2. **Rotate regularly**: Run `gcloud auth application-default login` periodically
3. **Multiple projects**: Use `gcloud config configurations` to switch between projects
4. **Check quotas**: Vertex AI has rate limits - monitor usage in Cloud Console

---

## ✅ Success Checklist

- [ ] Google Cloud SDK installed
- [ ] Authenticated with `gcloud auth application-default login`
- [ ] Vertex AI API enabled
- [ ] Docker Compose running (8 services)
- [ ] All health checks return `{"status": "healthy"}`
- [ ] Test client analysis works
- [ ] Can see generated mock data
- [ ] Logs show "Vertex AI client initialized"

---

**You're all set! The system is running with Vertex AI Gemini.** 🎉

**Total time: ~10 minutes** ⏱️
