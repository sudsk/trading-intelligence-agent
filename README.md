# Trading Intelligence Agent

A demo application showcasing AI-powered trading intelligence using Google Vertex AI ADK, FastAPI, and React.

## Architecture
```
React Frontend ←→ FastAPI Backend ←→ Vertex AI Agents
                     (Facade)           (ADK)

Quick Start
Prerequisites

Python 3.11+
Node.js 18+
Docker & Docker Compose (optional)
GCP Account (for Vertex AI deployment)

Local Development

1. Generate Mock Data

```
cd data/scripts
python seed_data.py
```

2. Start Backend

```
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
uvicorn main:app --reload
```

3. Start Frontend

```
cd frontend
npm install
cp .env.example .env
# Edit .env with your settings
npm start
```

4. Access Application

Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs

## Using Docker Compose

```
# Start all services
docker-compose up --build

# Stop all services
docker-compose down
```

## Project Structure
```
trading-intelligence-agent/
├── frontend/          # React application
├── backend/           # FastAPI facade
├── agents/            # Vertex AI ADK agents
├── data/              # Mock data & generators
├── infrastructure/    # Deployment scripts
└── docs/              # Documentation
```

## Features

- ✅ Real-time client profiling
- ✅ Strategy segment classification
- ✅ Switch probability estimation
- ✅ Media sentiment analysis
- ✅ Next best action recommendations
- ✅ SSE-based live alerts
- ✅ EPAM Loveship Dark theme

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Cloud Run deployment instructions.

## API Documentation

See [docs/API.md](docs/API.md) for complete API reference.

## License

MIT
