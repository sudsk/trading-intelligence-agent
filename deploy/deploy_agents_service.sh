#!/bin/bash
set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${REGION:-us-central1}"

echo "📦 Deploying Agents Service..."

gcloud run deploy agents-service \
  --source ./agents-service \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 60 \
  --set-env-vars "MCP_TRADE_SERVER_URL=${MCP_TRADE_SERVER_URL},MCP_RISK_SERVER_URL=${MCP_RISK_SERVER_URL},MCP_MARKET_SERVER_URL=${MCP_MARKET_SERVER_URL},MCP_NEWS_SERVER_URL=${MCP_NEWS_SERVER_URL},MCP_CLIENT_SERVER_URL=${MCP_CLIENT_SERVER_URL},DATABASE_URL=${DATABASE_URL},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --no-allow-unauthenticated \
  --ingress internal

echo "✅ Agents Service deployed"
