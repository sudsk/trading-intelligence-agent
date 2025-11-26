#!/bin/bash
# deploy_all.sh

PROJECT_ID="your-project-id"
REGION="us-central1"

echo "🚀 Deploying Trading Intelligence System to Cloud Run"

# 1. Frontend
echo "📦 Deploying Frontend..."
gcloud run deploy frontend \
  --source ./frontend \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated

FRONTEND_URL=$(gcloud run services describe frontend --region $REGION --format 'value(status.url)')
echo "✅ Frontend: $FRONTEND_URL"

# 2-8. MCP Servers
echo "📦 Deploying MCP Servers..."
for mcp in trade risk market news client; do
  gcloud run deploy ${mcp}-mcp \
    --source ./mcp-servers/${mcp} \
    --region $REGION \
    --project $PROJECT_ID \
    --no-allow-unauthenticated \
    --ingress internal
  
  MCP_URL=$(gcloud run services describe ${mcp}-mcp --region $REGION --format 'value(status.url)')
  echo "✅ ${mcp}-mcp: $MCP_URL"
  
  # Store in env vars
  export ${mcp^^}_MCP_URL=$MCP_URL
done

# 3. Agents Service
echo "📦 Deploying Agents Service..."
gcloud run deploy agents-service \
  --source ./agents-service \
  --region $REGION \
  --project $PROJECT_ID \
  --no-allow-unauthenticated \
  --ingress internal \
  --set-env-vars "MCP_TRADE_SERVER_URL=$TRADE_MCP_URL,MCP_RISK_SERVER_URL=$RISK_MCP_URL,MCP_MARKET_SERVER_URL=$MARKET_MCP_URL,MCP_NEWS_SERVER_URL=$NEWS_MCP_URL,MCP_CLIENT_SERVER_URL=$CLIENT_MCP_URL"

AGENTS_URL=$(gcloud run services describe agents-service --region $REGION --format 'value(status.url)')
echo "✅ Agents Service: $AGENTS_URL"

# 4. API Façade
echo "📦 Deploying API Façade..."
gcloud run deploy api-facade \
  --source ./api-facade \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --set-env-vars "AGENTS_SERVICE_URL=$AGENTS_URL"

FACADE_URL=$(gcloud run services describe api-facade --region $REGION --format 'value(status.url)')
echo "✅ API Façade: $FACADE_URL"

echo ""
echo "🎉 Deployment Complete!"
echo "Frontend: $FRONTEND_URL"
echo "API: $FACADE_URL"
