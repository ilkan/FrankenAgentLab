#!/bin/bash
# Backend Deployment Script for FrankenAgent Lab
# Deploys backend to Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-frankenagent-prod}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="frankenagent-backend"
DB_INSTANCE="${DB_INSTANCE_NAME:-frankenagent-db}"

echo "========================================="
echo "Deploying FrankenAgent Backend to Cloud Run"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Verify gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install it first."
    echo "Run: ./scripts/install-gcp-cli.sh"
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Build and deploy using Cloud Build
echo ""
echo "Building and deploying to Cloud Run..."
echo "This may take several minutes..."
echo ""

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=10 \
    --concurrency=80 \
    --timeout=300 \
    --set-cloudsql-instances=$PROJECT_ID:$REGION:$DB_INSTANCE \
    --set-secrets=DATABASE_URL=DATABASE_URL:latest,\
OPENAI_API_KEY=OPENAI_API_KEY:latest,\
ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,\
GROQ_API_KEY=GROQ_API_KEY:latest,\
GEMINI_API_KEY=GEMINI_API_KEY:latest,\
TAVILY_API_KEY=TAVILY_API_KEY:latest,\
JWT_SECRET_KEY=JWT_SECRET_KEY:latest,\
REDIS_HOST=REDIS_HOST:latest,\
KMS_PROJECT_ID=KMS_PROJECT_ID:latest,\
KMS_LOCATION=KMS_LOCATION:latest,\
KMS_KEYRING=KMS_KEYRING:latest,\
KMS_KEY=KMS_KEY:latest,\
GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,\
GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,\
GITHUB_CLIENT_ID=GITHUB_CLIENT_ID:latest,\
GITHUB_CLIENT_SECRET=GITHUB_CLIENT_SECRET:latest,\
BREVO_API_KEY=BREVO_API_KEY:latest \
    --set-env-vars=ENVIRONMENT=production,\
LOG_LEVEL=INFO,\
GCP_PROJECT_ID=$PROJECT_ID,\
CLOUD_SQL_CONNECTION_NAME=$PROJECT_ID:$REGION:$DB_INSTANCE,\
'ALLOW_ORIGIN_REGEX=https://(storage\.googleapis\.com|frankenagent\.com).*',\
FRONTEND_URL=https://storage.googleapis.com/frankenagent-prod-frontend/index.html,\
OAUTH_REDIRECT_URI=https://frankenagent-backend-636617621192.us-central1.run.app/api/auth/callback,\
BACKEND_URL=https://frankenagent-backend-636617621192.us-central1.run.app

# Get service URL
echo ""
echo "Retrieving service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

echo ""
echo "========================================="
echo "✓ Backend deployed successfully!"
echo "========================================="
echo "Service URL: $SERVICE_URL"
echo ""
echo "Test the deployment:"
echo "  curl $SERVICE_URL/health"
echo ""
echo "View logs:"
echo "  gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo ""
