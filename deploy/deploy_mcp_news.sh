#!/bin/bash
set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${REGION:-us-central1}"

echo "📦 Deploying news MCP Server..."

gcloud run deploy news-mcp \
  --source ./mcp-servers/news \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --port 3004 \
  --no-allow-unauthenticated \
  --ingress internal

echo "✅ news MCP deployed"
