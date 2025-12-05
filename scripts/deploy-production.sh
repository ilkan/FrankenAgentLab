#!/bin/bash
# Production Deployment Script for FrankenAgent Lab
# Deploys both backend and frontend to production environment

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-frankenagent-prod}"
REGION="${GCP_REGION:-us-central1}"
ENVIRONMENT="production"

echo "========================================="
echo "FrankenAgent Lab - Production Deployment"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo ""

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

info() {
    echo "ℹ $1"
}

# Confirmation prompt
echo -e "${YELLOW}⚠ WARNING: You are about to deploy to PRODUCTION${NC}"
echo ""
echo "This will:"
echo "  - Deploy backend to Cloud Run (production)"
echo "  - Deploy frontend to Cloud Storage (production)"
echo "  - Update production services with latest code"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Validate prerequisites
info "Validating prerequisites..."

if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI not found. Run: ./scripts/install-gcp-cli.sh"
fi

if ! command -v gsutil &> /dev/null; then
    error "gsutil not found. Install Google Cloud SDK."
fi

if [ ! -d "frontend" ]; then
    error "frontend directory not found"
fi

success "Prerequisites validated"

# Set project
info "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Run tests before deployment
info "Running tests..."
if command -v poetry &> /dev/null; then
    poetry run pytest tests/ -v || error "Tests failed. Fix tests before deploying to production."
    success "All tests passed"
else
    warning "Poetry not found. Skipping tests."
fi

# Deploy backend
echo ""
echo "========================================="
echo "Step 1: Deploying Backend"
echo "========================================="
echo ""

SERVICE_NAME="frankenagent-backend"
DB_INSTANCE="${DB_INSTANCE_NAME:-frankenagent-db}"

info "Building and deploying backend to Cloud Run..."

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=20 \
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
BREVO_API_KEY=BREVO_API_KEY:latest \
    --set-env-vars=ENVIRONMENT=production,\
LOG_LEVEL=INFO,\
GCP_PROJECT_ID=$PROJECT_ID \
    --tag=production

# Get service URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

success "Backend deployed successfully"
info "Backend URL: $BACKEND_URL"

# Health check
echo ""
info "Running health check..."
sleep 5  # Wait for service to be ready

HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" || echo "000")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    success "Health check passed (HTTP 200)"
else
    error "Health check failed (HTTP $HEALTH_RESPONSE)"
fi

# Deploy frontend
echo ""
echo "========================================="
echo "Step 2: Deploying Frontend"
echo "========================================="
echo ""

BUCKET_NAME="${BUCKET_NAME:-$PROJECT_ID-frontend}"
BUCKET="gs://$BUCKET_NAME"

info "Building frontend..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    info "Installing dependencies..."
    npm install
fi

# Update API endpoint to production backend
info "Configuring production API endpoint..."
export REACT_APP_API_URL="$BACKEND_URL"

# Build production bundle
info "Creating production build..."
npm run build

cd ..

# Deploy to Cloud Storage
info "Deploying to Cloud Storage..."
gsutil -m rsync -r -d frontend/build/ $BUCKET

# Set cache control headers
info "Setting cache control headers..."
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" "$BUCKET/**/*.html" 2>/dev/null || true
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" "$BUCKET/**/*.js" 2>/dev/null || true
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" "$BUCKET/**/*.css" 2>/dev/null || true
gsutil -m setmeta -h "Cache-Control:public, max-age=604800" "$BUCKET/**/*.{png,jpg,jpeg,gif,svg,ico}" 2>/dev/null || true

FRONTEND_URL="https://storage.googleapis.com/$BUCKET_NAME/index.html"

success "Frontend deployed successfully"
info "Frontend URL: $FRONTEND_URL"

# Run smoke tests
echo ""
echo "========================================="
echo "Step 3: Running Smoke Tests"
echo "========================================="
echo ""

info "Testing backend endpoints..."

# Test health endpoint
info "  - Testing /health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")
if [ "$HEALTH_STATUS" = "200" ]; then
    success "    Health endpoint OK"
else
    warning "    Health endpoint returned $HEALTH_STATUS"
fi

# Test API docs
info "  - Testing /docs..."
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/docs")
if [ "$DOCS_STATUS" = "200" ]; then
    success "    API docs OK"
else
    warning "    API docs returned $DOCS_STATUS"
fi

# Test auth endpoints
info "  - Testing /api/auth/register..."
REGISTER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"testpass123"}')
if [ "$REGISTER_STATUS" = "201" ] || [ "$REGISTER_STATUS" = "400" ]; then
    success "    Register endpoint OK"
else
    warning "    Register endpoint returned $REGISTER_STATUS"
fi

success "Smoke tests completed"

# Deployment summary
echo ""
echo "========================================="
echo "✓ Production Deployment Complete!"
echo "========================================="
echo ""
echo "Backend:"
echo "  URL: $BACKEND_URL"
echo "  Health: $BACKEND_URL/health"
echo "  API Docs: $BACKEND_URL/docs"
echo ""
echo "Frontend:"
echo "  URL: $FRONTEND_URL"
echo ""
echo "Monitoring:"
echo "  Logs: gcloud run services logs read $SERVICE_NAME --region=$REGION --follow"
echo "  Metrics: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics"
echo ""
echo "Next steps:"
echo "  1. Configure custom domain (./scripts/setup-custom-domain.sh)"
echo "  2. Setup monitoring alerts (./scripts/setup-monitoring.sh)"
echo "  3. Test all features in production"
echo "  4. Monitor logs and metrics"
echo ""
echo "Rollback (if needed):"
echo "  gcloud run services update-traffic $SERVICE_NAME --region=$REGION --to-revisions=PREVIOUS_REVISION=100"
echo ""

