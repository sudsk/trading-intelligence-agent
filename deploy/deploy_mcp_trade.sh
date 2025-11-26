#!/bin/bash
set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${REGION:-us-central1}"

echo "📦 Deploying trade MCP Server..."

gcloud run deploy trade-mcp \
  --source ./mcp-servers/trade \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --port 3001 \
  --no-allow-unauthenticated \
  --ingress internal

echo "✅ trade MCP deployed"
