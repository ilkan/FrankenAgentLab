#!/bin/bash
# Frontend Deployment Script for FrankenAgent Lab
# Deploys frontend to Google Cloud Storage with CDN

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-frankenagent-prod}"
BUCKET_NAME="${BUCKET_NAME:-$PROJECT_ID-frontend}"
BUCKET="gs://$BUCKET_NAME"
REGION="${GCP_REGION:-us-central1}"

echo "========================================="
echo "Deploying FrankenAgent Frontend to Cloud Storage"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Bucket: $BUCKET_NAME"
echo ""

# Verify gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install it first."
    echo "Run: ./scripts/install-gcp-cli.sh"
    exit 1
fi

# Verify gsutil is available
if ! command -v gsutil &> /dev/null; then
    echo "Error: gsutil not found. Please install Google Cloud SDK."
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "Error: frontend directory not found"
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Build frontend
echo ""
echo "Building frontend..."
cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build production bundle
echo "Creating production build..."
npm run build

# Return to root directory
cd ..

# Check if bucket exists, create if not
echo ""
echo "Checking if bucket exists..."
if ! gsutil ls -b $BUCKET &> /dev/null; then
    echo "Creating bucket $BUCKET_NAME..."
    gsutil mb -l $REGION gs://$BUCKET_NAME
    
    # Configure bucket for website hosting
    echo "Configuring bucket for website hosting..."
    gsutil web set -m index.html -e index.html $BUCKET
    
    # Make bucket publicly readable
    echo "Making bucket publicly readable..."
    gsutil iam ch allUsers:objectViewer $BUCKET
    
    # Enable CORS
    echo "Enabling CORS..."
    cat > /tmp/cors.json <<EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD", "OPTIONS"],
    "responseHeader": ["Content-Type", "Authorization"],
    "maxAgeSeconds": 3600
  }
]
EOF
    gsutil cors set /tmp/cors.json $BUCKET
    rm /tmp/cors.json
fi

# Deploy to Cloud Storage
echo ""
echo "Deploying to Cloud Storage..."
gsutil -m rsync -r -d frontend/build/ $BUCKET

# Note: Cache headers can be set later via GCP Console if needed
# Skipping automatic cache header setting to avoid gsutil hanging issues on macOS
echo ""
echo "Files deployed successfully. Cache headers can be configured via GCP Console if needed."

# Get URLs
STORAGE_URL="https://storage.googleapis.com/$BUCKET_NAME/index.html"
CUSTOM_DOMAIN="https://frankenagent.com"

echo ""
echo "========================================="
echo "✓ Frontend deployed successfully!"
echo "========================================="
echo "Production URL: $CUSTOM_DOMAIN"
echo "Storage URL: $STORAGE_URL"
echo ""
echo "Your app is now live at: $CUSTOM_DOMAIN"
echo ""
echo "View bucket contents:"
echo "  gsutil ls -r $BUCKET"
echo ""
