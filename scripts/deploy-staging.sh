#!/bin/bash
# scripts/deploy-staging.sh
# Deploy FrankenAgent Lab to staging environment

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-frankenagent-staging}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="frankenagent-backend-staging"
DB_INSTANCE="frankenagent-db-staging"
FRONTEND_BUCKET="${PROJECT_ID}-frontend"

echo "========================================="
echo "Deploying to Staging Environment"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is configured
if ! gcloud config get-value project &> /dev/null; then
    echo "❌ Error: gcloud not configured. Run 'gcloud init' first."
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Deploy backend to Cloud Run
echo ""
echo "========================================="
echo "Deploying Backend to Cloud Run"
echo "========================================="

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=5 \
    --concurrency=80 \
    --timeout=300 \
    --set-cloudsql-instances=$PROJECT_ID:$REGION:$DB_INSTANCE \
    --set-secrets=DATABASE_URL=DATABASE_URL:latest,\
OPENAI_API_KEY=OPENAI_API_KEY:latest,\
TAVILY_API_KEY=TAVILY_API_KEY:latest,\
JWT_SECRET_KEY=JWT_SECRET_KEY:latest,\
REDIS_HOST=REDIS_HOST:latest,\
KMS_PROJECT_ID=KMS_PROJECT_ID:latest,\
KMS_LOCATION=KMS_LOCATION:latest,\
KMS_KEYRING=KMS_KEYRING:latest,\
KMS_KEY=KMS_KEY:latest \
    --set-env-vars=ENVIRONMENT=staging,\
LOG_LEVEL=INFO,\
REDIS_PORT=6379

# Get service URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

echo ""
echo "✓ Backend deployed successfully!"
echo "Backend URL: $BACKEND_URL"

# Deploy frontend to Cloud Storage
echo ""
echo "========================================="
echo "Deploying Frontend to Cloud Storage"
echo "========================================="

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found"
    exit 1
fi

cd frontend

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Build frontend with staging backend URL
echo "Building frontend..."
VITE_API_URL=$BACKEND_URL npm run build

# Deploy to Cloud Storage
echo "Deploying to Cloud Storage..."
gsutil -m rsync -r -d build/ gs://$FRONTEND_BUCKET

# Set cache control headers
echo "Setting cache control headers..."
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" gs://$FRONTEND_BUCKET/**/*.html
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" gs://$FRONTEND_BUCKET/**/*.js
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" gs://$FRONTEND_BUCKET/**/*.css

cd ..

FRONTEND_URL="https://storage.googleapis.com/$FRONTEND_BUCKET/index.html"

echo ""
echo "✓ Frontend deployed successfully!"
echo "Frontend URL: $FRONTEND_URL"

# Health check
echo ""
echo "========================================="
echo "Running Health Check"
echo "========================================="

sleep 5  # Wait for service to be ready

HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/health || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✓ Health check passed"
else
    echo "⚠ Health check returned status: $HEALTH_STATUS"
fi

# Summary
echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Backend URL:  $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "Next steps:"
echo "1. Run integration tests: ./scripts/test-staging.sh"
echo "2. Monitor logs: gcloud run logs tail $SERVICE_NAME --region=$REGION"
echo "3. View metrics: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo ""
