#!/bin/bash
set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${REGION:-us-central1}"

echo "🚀 Deploying Trading Intelligence System"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

# Deploy MCP Servers
for service in trade risk market news client; do
  ./deploy/deploy_mcp_$service.sh
done

# Get MCP URLs
TRADE_MCP_URL=$(gcloud run services describe trade-mcp --region $REGION --format 'value(status.url)')
RISK_MCP_URL=$(gcloud run services describe risk-mcp --region $REGION --format 'value(status.url)')
MARKET_MCP_URL=$(gcloud run services describe market-mcp --region $REGION --format 'value(status.url)')
NEWS_MCP_URL=$(gcloud run services describe news-mcp --region $REGION --format 'value(status.url)')
CLIENT_MCP_URL=$(gcloud run services describe client-mcp --region $REGION --format 'value(status.url)')

export MCP_TRADE_SERVER_URL=$TRADE_MCP_URL
export MCP_RISK_SERVER_URL=$RISK_MCP_URL
export MCP_MARKET_SERVER_URL=$MARKET_MCP_URL
export MCP_NEWS_SERVER_URL=$NEWS_MCP_URL
export MCP_CLIENT_SERVER_URL=$CLIENT_MCP_URL

./deploy/deploy_agents_service.sh

AGENTS_URL=$(gcloud run services describe agents-service --region $REGION --format 'value(status.url)')
export AGENTS_SERVICE_URL=$AGENTS_URL

./deploy/deploy_api_facade.sh

FACADE_URL=$(gcloud run services describe api-facade --region $REGION --format 'value(status.url)')

echo ""
echo "🎉 Deployment Complete!"
echo "   API: $FACADE_URL"
