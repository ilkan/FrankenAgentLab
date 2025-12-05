#!/bin/bash
set -e

echo "=== GCP Project Setup ==="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    echo "Please run: ./scripts/install-gcp-cli.sh"
    exit 1
fi

# Prompt for project ID
read -p "Enter your GCP Project ID (or press Enter to create a new one): " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    # Generate a project ID
    RANDOM_SUFFIX=$(date +%s | tail -c 5)
    PROJECT_ID="frankenagent-lab-${RANDOM_SUFFIX}"
    echo "Generated Project ID: ${PROJECT_ID}"
    
    # Create new project
    echo "Creating new GCP project..."
    gcloud projects create ${PROJECT_ID} --name="FrankenAgent Lab"
    
    echo ""
    echo "⚠️  IMPORTANT: You need to link a billing account to this project."
    echo "   Visit: https://console.cloud.google.com/billing/linkedaccount?project=${PROJECT_ID}"
    echo ""
    read -p "Press Enter after you've enabled billing..."
else
    echo "Using existing project: ${PROJECT_ID}"
fi

# Set the project
echo "Setting active project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo ""
echo "Enabling required GCP APIs..."
echo "This may take a few minutes..."

APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "sqladmin.googleapis.com"
    "redis.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudkms.googleapis.com"
    "storage-api.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
    "compute.googleapis.com"
)

for API in "${APIS[@]}"; do
    echo "  Enabling ${API}..."
    gcloud services enable ${API} --project=${PROJECT_ID}
done

echo ""
echo "✓ APIs enabled successfully!"

# Update .env file
echo ""
echo "Updating .env file with project configuration..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi

# Add or update GCP_PROJECT_ID in .env
if grep -q "^GCP_PROJECT_ID=" .env; then
    # Update existing line (macOS compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^GCP_PROJECT_ID=.*/GCP_PROJECT_ID=${PROJECT_ID}/" .env
    else
        sed -i "s/^GCP_PROJECT_ID=.*/GCP_PROJECT_ID=${PROJECT_ID}/" .env
    fi
else
    # Add new line
    echo "" >> .env
    echo "# GCP Configuration" >> .env
    echo "GCP_PROJECT_ID=${PROJECT_ID}" >> .env
fi

# Add GCP_REGION if not present
if ! grep -q "^GCP_REGION=" .env; then
    echo "GCP_REGION=us-central1" >> .env
fi

echo "✓ .env file updated"

# Display summary
echo ""
echo "=== Setup Complete ==="
echo "Project ID: ${PROJECT_ID}"
echo "Region: us-central1 (default)"
echo ""
echo "Next steps:"
echo "  1. Verify billing is enabled:"
echo "     gcloud beta billing projects describe ${PROJECT_ID}"
echo ""
echo "  2. Run infrastructure setup:"
echo "     ./scripts/setup-infrastructure.sh"
echo ""
echo "  3. Configure authentication:"
echo "     gcloud auth application-default login"
