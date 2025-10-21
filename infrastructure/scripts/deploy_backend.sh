#!/bin/bash

# Deploy FastAPI backend to Cloud Run

PROJECT_ID="your-gcp-project"
REGION="us-central1"
SERVICE_NAME="trading-intelligence-api"

echo "Building and deploying backend..."

cd ../../backend

# Build and push container
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-env-vars "GCP_REGION=${REGION}" \
  --set-env-vars "DEMO_MODE=true"

echo "Backend deployed!"
