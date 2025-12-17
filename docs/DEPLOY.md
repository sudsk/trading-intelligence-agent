# Deploying to Google Cloud Run + Cloud SQL

## Overview

✅ 8 services → Cloud Run (frontend, api-facade, agents-service, 5 MCP servers)

✅ PostgreSQL → Cloud SQL (managed database)

## Prerequisites
```
bash
# Set your project
export PROJECT_ID=your-project-id
export REGION=us-central1

gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com sqladmin.googleapis.com
```

## Step 1: Create Cloud SQL Database
```
bash# Create PostgreSQL instance
gcloud sql instances create trading-intelligence-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password=YOUR_SECURE_PASSWORD
```
### Create database
gcloud sql databases create trading_intelligence \
  --instance=trading-intelligence-db

### Get connection name (needed for Cloud Run)
gcloud sql instances describe trading-intelligence-db \
  --format='value(connectionName)'
# Output: PROJECT_ID:REGION:trading-intelligence-db
## Load Schema
```
bash# Connect and load schema
gcloud sql connect trading-intelligence-db --user=postgres
```
### Then paste your schema.sql contents
### Or upload via Cloud Console

## Step 2: Build & Push Container Images

Option A: Using Cloud Build (Recommended)
```
bash# Build all images
gcloud builds submit --config=cloudbuild.yaml
```
Create cloudbuild.yaml:

```
yaml steps:
  # Frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-frontend', './frontend']
  
  # API Façade
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-api-facade', '-f', 'api-facade/Dockerfile', '.']
  
  # Agents Service
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-agents-service', '-f', 'agents-service/Dockerfile', '.']
  
  # MCP Servers
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-mcp-trade', './mcp-servers/trade']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-mcp-risk', './mcp-servers/risk']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-mcp-market', './mcp-servers/market']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-mcp-news', './mcp-servers/news']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/trading-mcp-client', './mcp-servers/client']

images:
  - 'gcr.io/$PROJECT_ID/trading-frontend'
  - 'gcr.io/$PROJECT_ID/trading-api-facade'
  - 'gcr.io/$PROJECT_ID/trading-agents-service'
  - 'gcr.io/$PROJECT_ID/trading-mcp-trade'
  - 'gcr.io/$PROJECT_ID/trading-mcp-risk'
  - 'gcr.io/$PROJECT_ID/trading-mcp-market'
  - 'gcr.io/$PROJECT_ID/trading-mcp-news'
  - 'gcr.io/$PROJECT_ID/trading-mcp-client'
Option B: Local Build & Push
bash# Build and push each image
docker build -t gcr.io/$PROJECT_ID/trading-frontend ./frontend
docker push gcr.io/$PROJECT_ID/trading-frontend

docker build -t gcr.io/$PROJECT_ID/trading-api-facade -f api-facade/Dockerfile .
docker push gcr.io/$PROJECT_ID/trading-api-facade
```
### ... repeat for each service

## Step 3: Deploy MCP Servers (Internal Only)
These servers don't need public access - only agents-service calls them.
```
bash# Deploy Trade MCP
gcloud run deploy trading-mcp-trade \
  --image=gcr.io/$PROJECT_ID/trading-mcp-trade \
  --platform=managed \
  --region=$REGION \
  --port=3001 \
  --no-allow-unauthenticated \
  --memory=512Mi \
  --cpu=1
```
### Get the URL
```
export TRADE_MCP_URL=$(gcloud run services describe trading-mcp-trade --region=$REGION --format='value(status.url)')
```

### Repeat for other MCP servers (risk, market, news, client)
```
gcloud run deploy trading-mcp-risk --image=gcr.io/$PROJECT_ID/trading-mcp-risk --platform=managed --region=$REGION --port=3002 --no-allow-unauthenticated --memory=512Mi --cpu=1
gcloud run deploy trading-mcp-market --image=gcr.io/$PROJECT_ID/trading-mcp-market --platform=managed --region=$REGION --port=3003 --no-allow-unauthenticated --memory=512Mi --cpu=1
gcloud run deploy trading-mcp-news --image=gcr.io/$PROJECT_ID/trading-mcp-news --platform=managed --region=$REGION --port=3004 --no-allow-unauthenticated --memory=512Mi --cpu=1
gcloud run deploy trading-mcp-client --image=gcr.io/$PROJECT_ID/trading-mcp-client --platform=managed --region=$REGION --port=3005 --no-allow-unauthenticated --memory=512Mi --cpu=1
```
### Get all URLs
```
export RISK_MCP_URL=$(gcloud run services describe trading-mcp-risk --region=$REGION --format='value(status.url)')
export MARKET_MCP_URL=$(gcloud run services describe trading-mcp-market --region=$REGION --format='value(status.url)')
export NEWS_MCP_URL=$(gcloud run services describe trading-mcp-news --region=$REGION --format='value(status.url)')
export CLIENT_MCP_URL=$(gcloud run services describe trading-mcp-client --region=$REGION --format='value(status.url)')
```

## Step 4: Deploy Agents Service
```
bash
gcloud run deploy trading-agents-service \
  --image=gcr.io/$PROJECT_ID/trading-agents-service \
  --platform=managed \
  --region=$REGION \
  --port=8001 \
  --no-allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --set-env-vars="DATABASE_URL=postgresql://postgres:PASSWORD@/trading_intelligence?host=/cloudsql/PROJECT_ID:REGION:trading-intelligence-db" \
  --set-env-vars="MCP_TRADE_SERVER_URL=$TRADE_MCP_URL" \
  --set-env-vars="MCP_RISK_SERVER_URL=$RISK_MCP_URL" \
  --set-env-vars="MCP_MARKET_SERVER_URL=$MARKET_MCP_URL" \
  --set-env-vars="MCP_NEWS_SERVER_URL=$NEWS_MCP_URL" \
  --set-env-vars="MCP_CLIENT_SERVER_URL=$CLIENT_MCP_URL" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --add-cloudsql-instances=PROJECT_ID:REGION:trading-intelligence-db
```

### Get URL
export AGENTS_SERVICE_URL=$(gcloud run services describe trading-agents-service --region=$REGION --format='value(status.url)')

## Step 5: Deploy API Façade
```
bash
gcloud run deploy trading-api-facade \
  --image=gcr.io/$PROJECT_ID/trading-api-facade \
  --platform=managed \
  --region=$REGION \
  --port=8000 \
  --no-allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars="DATABASE_URL=postgresql://postgres:PASSWORD@/trading_intelligence?host=/cloudsql/PROJECT_ID:REGION:trading-intelligence-db" \
  --set-env-vars="AGENTS_SERVICE_URL=$AGENTS_SERVICE_URL" \
  --set-env-vars="MCP_CLIENT_SERVER_URL=$CLIENT_MCP_URL" \
  --add-cloudsql-instances=PROJECT_ID:REGION:trading-intelligence-db
```

### Get URL
```
export API_FACADE_URL=$(gcloud run services describe trading-api-facade --region=$REGION --format='value(status.url)')
```

## Step 6: Deploy Frontend
```
bash
gcloud run deploy trading-frontend \
  --image=gcr.io/$PROJECT_ID/trading-frontend \
  --platform=managed \
  --region=$REGION \
  --port=3000 \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --set-env-vars="REACT_APP_API_URL=$API_FACADE_URL"
```

# Get URL
```
export FRONTEND_URL=$(gcloud run services describe trading-frontend --region=$REGION --format='value(status.url)')

echo "🎉 Frontend available at: $FRONTEND_URL"
```

## Step 7: Set Up Service-to-Service Authentication
MCP servers and agents-service are internal - need IAM permissions:
```
bash# Get service accounts
export AGENTS_SA=$(gcloud run services describe trading-agents-service --region=$REGION --format='value(spec.template.spec.serviceAccountName)')
export API_SA=$(gcloud run services describe trading-api-facade --region=$REGION --format='value(spec.template.spec.serviceAccountName)')
```

### Grant agents-service permission to call MCP servers
```
for service in trading-mcp-trade trading-mcp-risk trading-mcp-market trading-mcp-news trading-mcp-client; do
  gcloud run services add-iam-policy-binding $service \
    --member="serviceAccount:$AGENTS_SA" \
    --role="roles/run.invoker" \
    --region=$REGION
done
```

### Grant api-facade permission to call agents-service
```
gcloud run services add-iam-policy-binding trading-agents-service \
  --member="serviceAccount:$API_SA" \
  --role="roles/run.invoker" \
  --region=$REGION
```

### Grant api-facade permission to call client MCP
```
gcloud run services add-iam-policy-binding trading-mcp-client \
  --member="serviceAccount:$API_SA" \
  --role="roles/run.invoker" \
  --region=$REGION
```

## Notes

✅ Cloud SQL: Use managed Cloud SQL.

✅ Database Connection: Uses Unix socket (/cloudsql/...) - no public IP needed

✅ Authentication: Service-to-service uses IAM, not API keys

✅ Secrets: Store GOOGLE_CLOUD_PROJECT API key in Secret Manager if needed

✅ Networking: All internal services are --no-allow-unauthenticated
