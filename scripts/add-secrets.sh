#!/bin/bash
set -e

echo "=== Add Platform Secrets to Secret Manager ==="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    echo "Please run: ./scripts/install-gcp-cli.sh"
    exit 1
fi

# Load project ID from .env or prompt
if [ -f .env ] && grep -q "^GCP_PROJECT_ID=" .env; then
    PROJECT_ID=$(grep "^GCP_PROJECT_ID=" .env | cut -d '=' -f2)
    echo "Using project from .env: ${PROJECT_ID}"
else
    read -p "Enter your GCP Project ID: " PROJECT_ID
fi

gcloud config set project ${PROJECT_ID}

echo ""
echo "This script will help you add the following secrets to Secret Manager:"
echo "  1. OPENAI_API_KEY"
echo "  2. TAVILY_API_KEY"
echo "  3. JWT_SECRET_KEY"
echo ""
echo "You can skip any secret by pressing Enter without providing a value."
echo ""

# Function to add or update secret
add_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        echo "Skipping ${secret_name} (no value provided)"
        return
    fi
    
    if gcloud secrets describe ${secret_name} --project=${PROJECT_ID} &>/dev/null; then
        echo "Secret '${secret_name}' already exists. Creating new version..."
        echo -n "${secret_value}" | gcloud secrets versions add ${secret_name} --data-file=- --project=${PROJECT_ID}
    else
        echo "Creating secret '${secret_name}'..."
        echo -n "${secret_value}" | gcloud secrets create ${secret_name} --data-file=- --project=${PROJECT_ID}
    fi
    
    echo "✓ ${secret_name} stored"
}

# Prompt for OpenAI API Key
echo "1. OpenAI API Key"
echo "   Get your key from: https://platform.openai.com/api-keys"
read -sp "   Enter OpenAI API Key (or press Enter to skip): " OPENAI_KEY
echo ""
if [ -n "$OPENAI_KEY" ]; then
    add_secret "OPENAI_API_KEY" "$OPENAI_KEY"
fi

echo ""

# Prompt for Tavily API Key
echo "2. Tavily API Key"
echo "   Get your key from: https://tavily.com/"
read -sp "   Enter Tavily API Key (or press Enter to skip): " TAVILY_KEY
echo ""
if [ -n "$TAVILY_KEY" ]; then
    add_secret "TAVILY_API_KEY" "$TAVILY_KEY"
fi

echo ""

# Generate or prompt for JWT Secret
echo "3. JWT Secret Key"
echo "   This will be used to sign authentication tokens."
read -p "   Generate random JWT secret? (Y/n): " GENERATE_JWT

if [ "$GENERATE_JWT" != "n" ] && [ "$GENERATE_JWT" != "N" ]; then
    JWT_SECRET=$(openssl rand -base64 32)
    echo "   Generated JWT secret"
    add_secret "JWT_SECRET_KEY" "$JWT_SECRET"
else
    read -sp "   Enter JWT Secret Key (or press Enter to skip): " JWT_SECRET
    echo ""
    if [ -n "$JWT_SECRET" ]; then
        add_secret "JWT_SECRET_KEY" "$JWT_SECRET"
    fi
fi

echo ""
echo "=== Secrets Configuration Complete ==="
echo ""
echo "Secrets stored in Secret Manager:"
gcloud secrets list --project=${PROJECT_ID} --format="table(name)"

echo ""
echo "⚠️  IMPORTANT: Update your local .env file"
echo ""
echo "For local development, add these to your .env file:"
echo "  OPENAI_API_KEY=your-openai-key"
echo "  TAVILY_API_KEY=your-tavily-key"
echo "  JWT_SECRET_KEY=your-jwt-secret"
echo ""
echo "Note: The production deployment will use Secret Manager automatically."
