#!/bin/bash
# Setup CI/CD Pipeline for FrankenAgent Lab
# Creates Cloud Build trigger for automated deployments

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-frankenagent-prod}"
REPO_NAME="${REPO_NAME:-frankenagent-lab}"
BRANCH_NAME="${BRANCH_NAME:-main}"
TRIGGER_NAME="frankenagent-deploy-main"

echo "========================================="
echo "Setting up CI/CD Pipeline"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Repository: $REPO_NAME"
echo "Branch: $BRANCH_NAME"
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

# Enable Cloud Build API
echo ""
echo "Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com

# Grant Cloud Build permissions
echo ""
echo "Granting Cloud Build service account permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin" \
    --quiet

# Grant Service Account User role (to deploy as service account)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser" \
    --quiet

# Grant Storage Admin role (for frontend deployment)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/storage.admin" \
    --quiet

# Grant Secret Manager Secret Accessor role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo ""
echo "========================================="
echo "Cloud Build Trigger Setup"
echo "========================================="
echo ""
echo "To create a trigger, you have two options:"
echo ""
echo "Option 1: Connect to GitHub repository (recommended)"
echo "  1. Go to: https://console.cloud.google.com/cloud-build/triggers"
echo "  2. Click 'Connect Repository'"
echo "  3. Select GitHub and authenticate"
echo "  4. Select your repository: $REPO_NAME"
echo "  5. Create trigger with these settings:"
echo "     - Name: $TRIGGER_NAME"
echo "     - Event: Push to branch"
echo "     - Branch: ^$BRANCH_NAME$"
echo "     - Configuration: Cloud Build configuration file (yaml or json)"
echo "     - Location: /cloudbuild.yaml"
echo ""
echo "Option 2: Manual trigger (for testing)"
echo "  Run this command to trigger a build manually:"
echo "  gcloud builds submit --config=cloudbuild.yaml ."
echo ""
echo "========================================="
echo "✓ CI/CD setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Connect your repository in Cloud Build console"
echo "  2. Push to $BRANCH_NAME branch to trigger deployment"
echo "  3. Monitor builds: gcloud builds list"
echo ""
