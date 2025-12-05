#!/bin/bash

# Fix Production Connection Error
# This script adds missing KMS environment variables to Cloud Run

set -e

echo "🔧 FrankenAgent Lab - Production Connection Error Fix"
echo "=================================================="
echo ""

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No GCP project configured"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Project: $PROJECT_ID"
echo ""

# Configuration
REGION="us-central1"
SERVICE_NAME="frankenagent-backend"
KMS_KEYRING="frankenagent-keyring"
KMS_KEY="api-key-encryption"

# Check if service exists
echo "🔍 Checking if Cloud Run service exists..."
if ! gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "❌ Error: Cloud Run service '$SERVICE_NAME' not found in region '$REGION'"
    echo ""
    echo "Available services:"
    gcloud run services list --project=$PROJECT_ID
    exit 1
fi

echo "✅ Service found: $SERVICE_NAME"
echo ""

# Check if KMS keyring exists
echo "🔍 Checking if KMS keyring exists..."
if ! gcloud kms keyrings describe $KMS_KEYRING --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "⚠️  KMS keyring not found. Creating..."
    gcloud kms keyrings create $KMS_KEYRING \
        --location=$REGION \
        --project=$PROJECT_ID
    echo "✅ KMS keyring created: $KMS_KEYRING"
else
    echo "✅ KMS keyring exists: $KMS_KEYRING"
fi

echo ""

# Check if KMS key exists
echo "🔍 Checking if KMS key exists..."
if ! gcloud kms keys describe $KMS_KEY --keyring=$KMS_KEYRING --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "⚠️  KMS key not found. Creating..."
    gcloud kms keys create $KMS_KEY \
        --keyring=$KMS_KEYRING \
        --location=$REGION \
        --purpose=encryption \
        --project=$PROJECT_ID
    echo "✅ KMS key created: $KMS_KEY"
else
    echo "✅ KMS key exists: $KMS_KEY"
fi

echo ""

# Get service account
echo "🔍 Getting Cloud Run service account..."
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(spec.template.spec.serviceAccountName)")

if [ -z "$SERVICE_ACCOUNT" ]; then
    echo "⚠️  No custom service account found, using default compute service account"
    SERVICE_ACCOUNT="${PROJECT_ID}-compute@developer.gserviceaccount.com"
fi

echo "📧 Service Account: $SERVICE_ACCOUNT"
echo ""

# Grant KMS permissions
echo "🔐 Granting KMS permissions to service account..."
gcloud kms keys add-iam-policy-binding $KMS_KEY \
    --keyring=$KMS_KEYRING \
    --location=$REGION \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" \
    --project=$PROJECT_ID \
    --quiet

echo "✅ KMS permissions granted"
echo ""

# Update Cloud Run service with environment variables
echo "🚀 Updating Cloud Run service with KMS environment variables..."
gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --update-env-vars=GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},KMS_KEYRING=${KMS_KEYRING},KMS_KEY=${KMS_KEY} \
    --quiet

echo "✅ Cloud Run service updated"
echo ""

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
sleep 5

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo ""
echo "✅ Fix applied successfully!"
echo ""
echo "=================================================="
echo "📊 Summary"
echo "=================================================="
echo "Project ID:     $PROJECT_ID"
echo "Region:         $REGION"
echo "Service:        $SERVICE_NAME"
echo "Service URL:    $SERVICE_URL"
echo "KMS Keyring:    $KMS_KEYRING"
echo "KMS Key:        $KMS_KEY"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""
echo "=================================================="
echo "🧪 Testing"
echo "=================================================="
echo ""
echo "1. Test health endpoint:"
echo "   curl $SERVICE_URL/"
echo ""
echo "2. Test with authentication:"
echo "   curl -X POST $SERVICE_URL/api/agents/run \\"
echo "     -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{...}'"
echo ""
echo "3. View logs:"
echo "   gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo ""
echo "=================================================="
echo "📝 Next Steps"
echo "=================================================="
echo ""
echo "1. Users need to add their API keys via the settings page"
echo "2. Monitor logs for any remaining issues"
echo "3. Test agent execution with a real request"
echo ""
echo "For detailed troubleshooting, see: PRODUCTION_CONNECTION_ERROR_FIX.md"
echo ""
