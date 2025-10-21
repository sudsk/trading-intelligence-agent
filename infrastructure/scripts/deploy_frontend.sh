#!/bin/bash

# Deploy React frontend to Cloud Run

PROJECT_ID="your-gcp-project"
REGION="us-central1"
SERVICE_NAME="trading-intelligence-ui"
BACKEND_URL="https://trading-intelligence-api-xxxxx.run.app"

echo "Building and deploying frontend..."

cd ../../frontend

# Set backend URL
echo "REACT_APP_API_URL=${BACKEND_URL}" > .env.production

# Build and push container
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated

echo "Frontend deployed!"
```

## **.gitignore**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
pip-log.txt
pip-delete-this-directory.txt

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
build/
.env.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Env files
.env
*.env

# Data
data/raw/*.csv
data/processed/*.json

# GCP
*.json
gcloud-key.json
