#!/bin/bash

# Deploy API Façade to Cloud Run
# Usage: ./deploy_api_facade.sh [PROJECT_ID] [REGION]

set -e

# Configuration
PROJECT_ID=${1:-your-project-id}
REGION=${2:-us-central1}
SERVICE_NAME="api-facade"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Deploying API Façade${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}ERROR: gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Set project
echo -e "${BLUE}Setting project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Check required environment variables
if [ -z "$AGENTS_SERVICE_URL" ]; then
    echo -e "${YELLOW}ERROR: AGENTS_SERVICE_URL not set${NC}"
    echo "Please set it first:"
    echo "  export AGENTS_SERVICE_URL=https://agents-service-xxxxx.run.app"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}WARNING: DATABASE_URL not set${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Navigate to service directory (from deploy/ to api-facade/)
cd "$(dirname "$0")/../api-facade"

echo ""
echo -e "${BLUE}Building and deploying...${NC}"
echo "Agents Service URL: ${AGENTS_SERVICE_URL}"

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
    --source . \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "AGENTS_SERVICE_URL=${AGENTS_SERVICE_URL},DATABASE_URL=${DATABASE_URL},CORS_ORIGINS=*" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 20

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --format 'value(status.url)')

echo ""
echo -e "${GREEN}API Façade URL: ${SERVICE_URL}${NC}"

# Test health endpoint
echo ""
echo -e "${BLUE}Testing health endpoint...${NC}"
curl -s "${SERVICE_URL}/health" | jq '.' || echo "Health check failed"

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Update frontend .env: REACT_APP_API_URL=${SERVICE_URL}"
echo "2. Test client profile: curl ${SERVICE_URL}/api/v1/clients/ACME_FX_023/profile"
echo "3. Test SSE stream: curl -N ${SERVICE_URL}/alerts/stream"
echo "4. Test Force Event: curl -X POST ${SERVICE_URL}/api/v1/demo/trigger-alert"

echo ""
echo -e "${YELLOW}Frontend Environment Variable:${NC}"
echo "REACT_APP_API_URL=${SERVICE_URL}"
