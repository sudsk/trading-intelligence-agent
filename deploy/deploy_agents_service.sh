#!/bin/bash

# Deploy Agents Service to Cloud Run
# Usage: ./deploy_agents_service.sh [PROJECT_ID] [REGION]

set -e

# Configuration
PROJECT_ID=${1:-your-project-id}
REGION=${2:-us-central1}
SERVICE_NAME="agents-service"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Deploying Agents Service${NC}"
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

# Check environment variables
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}WARNING: DATABASE_URL not set${NC}"
    echo "Set it with: export DATABASE_URL=postgresql://..."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Navigate to service directory (from deploy/ to agents-service/)
cd "$(dirname "$0")/../agents-service"

echo ""
echo -e "${BLUE}Building and deploying...${NC}"

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
    --source . \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "DATABASE_URL=${DATABASE_URL},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GEMINI_MODEL=gemini-2.0-flash-exp" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 60 \
    --max-instances 10

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --format 'value(status.url)')

echo ""
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"

# Test health endpoint
echo ""
echo -e "${BLUE}Testing health endpoint...${NC}"
curl -s "${SERVICE_URL}/health" | jq '.' || echo "Health check failed"

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Test the service: curl ${SERVICE_URL}/health"
echo "2. Analyze a client: curl -X POST ${SERVICE_URL}/analyze -H 'Content-Type: application/json' -d '{\"client_id\": \"ACME_FX_023\"}'"
echo "3. Deploy API façade with: AGENTS_SERVICE_URL=${SERVICE_URL} ./deploy_api_facade.sh"

echo ""
echo -e "${YELLOW}Remember to set AGENTS_SERVICE_URL for API façade:${NC}"
echo "export AGENTS_SERVICE_URL=${SERVICE_URL}"
