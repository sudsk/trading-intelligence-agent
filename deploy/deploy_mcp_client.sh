#!/bin/bash
set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${REGION:-us-central1}"

echo "📦 Deploying client MCP Server..."

gcloud run deploy client-mcp \
  --source ./mcp-servers/client \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --port 3005 \
  --no-allow-unauthenticated \
  --ingress internal

echo "✅ client MCP deployed"
