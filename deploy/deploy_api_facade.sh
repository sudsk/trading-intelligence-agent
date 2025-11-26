#!/bin/bash
set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${REGION:-us-central1}"

echo "📦 Deploying API Façade..."

gcloud run deploy api-facade \
  --source ./api-facade \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars "AGENTS_SERVICE_URL=${AGENTS_SERVICE_URL},DATABASE_URL=${DATABASE_URL}" \
  --allow-unauthenticated

echo "✅ API Façade deployed"
