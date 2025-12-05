#!/bin/bash
# Validate Deployment Setup for FrankenAgent Lab
# Checks that all prerequisites are met before deployment

set -e

echo "========================================="
echo "FrankenAgent Lab Deployment Validation"
echo "========================================="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
    ((ERRORS++))
}

warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
    ((WARNINGS++))
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

info() {
    echo "ℹ $1"
}

# Check 1: gcloud CLI
echo "Checking gcloud CLI..."
if command -v gcloud &> /dev/null; then
    GCLOUD_VERSION=$(gcloud version --format="value(core)" 2>/dev/null)
    success "gcloud CLI installed (version: $GCLOUD_VERSION)"
else
    error "gcloud CLI not found. Run: ./scripts/install-gcp-cli.sh"
fi

# Check 2: gsutil
echo "Checking gsutil..."
if command -v gsutil &> /dev/null; then
    success "gsutil installed"
else
    error "gsutil not found. Install Google Cloud SDK."
fi

# Check 3: Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    success "Docker installed (version: $DOCKER_VERSION)"
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        success "Docker daemon is running"
    else
        warning "Docker daemon is not running. Start Docker Desktop."
    fi
else
    warning "Docker not found. Required for local testing only."
fi

# Check 4: Node.js and npm
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    success "Node.js installed (version: $NODE_VERSION)"
    
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        success "npm installed (version: $NPM_VERSION)"
    else
        error "npm not found"
    fi
else
    error "Node.js not found. Required for frontend build."
fi

# Check 5: Python and Poetry
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python installed (version: $PYTHON_VERSION)"
    
    if command -v poetry &> /dev/null; then
        POETRY_VERSION=$(poetry --version | cut -d' ' -f3)
        success "Poetry installed (version: $POETRY_VERSION)"
    else
        error "Poetry not found. Install with: pip install poetry"
    fi
else
    error "Python 3 not found"
fi

# Check 6: GCP Project Configuration
echo "Checking GCP project configuration..."
if command -v gcloud &> /dev/null; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -n "$PROJECT_ID" ]; then
        success "GCP project configured: $PROJECT_ID"
        
        # Check if project exists
        if gcloud projects describe "$PROJECT_ID" &> /dev/null; then
            success "Project exists and is accessible"
        else
            error "Cannot access project $PROJECT_ID. Check permissions."
        fi
    else
        warning "No GCP project configured. Set with: gcloud config set project PROJECT_ID"
    fi
fi

# Check 7: Required Files
echo "Checking required files..."
REQUIRED_FILES=(
    "Dockerfile"
    ".dockerignore"
    ".gcloudignore"
    "cloudbuild.yaml"
    "scripts/deploy-backend.sh"
    "scripts/deploy-frontend.sh"
    "scripts/setup-cicd.sh"
    "pyproject.toml"
    "poetry.lock"
    "frontend/package.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "Found: $file"
    else
        error "Missing: $file"
    fi
done

# Check 8: Environment Variables
echo "Checking environment variables..."
if [ -n "$GCP_PROJECT_ID" ]; then
    success "GCP_PROJECT_ID is set: $GCP_PROJECT_ID"
else
    warning "GCP_PROJECT_ID not set. Will use gcloud default."
fi

if [ -n "$GCP_REGION" ]; then
    success "GCP_REGION is set: $GCP_REGION"
else
    info "GCP_REGION not set. Will use default: us-central1"
fi

# Check 9: Secret Manager Secrets (if project is configured)
if [ -n "$PROJECT_ID" ] && command -v gcloud &> /dev/null; then
    echo "Checking Secret Manager secrets..."
    
    REQUIRED_SECRETS=(
        "DATABASE_URL"
        "OPENAI_API_KEY"
        "TAVILY_API_KEY"
        "JWT_SECRET_KEY"
        "REDIS_HOST"
        "KMS_PROJECT_ID"
        "KMS_LOCATION"
        "KMS_KEYRING"
        "KMS_KEY"
    )
    
    for secret in "${REQUIRED_SECRETS[@]}"; do
        if gcloud secrets describe "$secret" --project="$PROJECT_ID" &> /dev/null; then
            success "Secret exists: $secret"
        else
            warning "Secret not found: $secret. Run: ./scripts/add-secrets.sh"
        fi
    done
fi

# Check 10: Cloud SQL Instance (if project is configured)
if [ -n "$PROJECT_ID" ] && command -v gcloud &> /dev/null; then
    echo "Checking Cloud SQL instance..."
    
    DB_INSTANCE="${DB_INSTANCE_NAME:-frankenagent-db}"
    if gcloud sql instances describe "$DB_INSTANCE" --project="$PROJECT_ID" &> /dev/null 2>&1; then
        success "Cloud SQL instance exists: $DB_INSTANCE"
    else
        warning "Cloud SQL instance not found: $DB_INSTANCE. Run: ./scripts/setup-infrastructure.sh"
    fi
fi

# Check 11: Redis Instance (if project is configured)
if [ -n "$PROJECT_ID" ] && command -v gcloud &> /dev/null; then
    echo "Checking Redis instance..."
    
    REDIS_INSTANCE="${REDIS_INSTANCE_NAME:-frankenagent-cache}"
    REGION="${GCP_REGION:-us-central1}"
    if gcloud redis instances describe "$REDIS_INSTANCE" --region="$REGION" --project="$PROJECT_ID" &> /dev/null 2>&1; then
        success "Redis instance exists: $REDIS_INSTANCE"
    else
        warning "Redis instance not found: $REDIS_INSTANCE. Run: ./scripts/setup-infrastructure.sh"
    fi
fi

# Summary
echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Deploy backend: ./scripts/deploy-backend.sh"
    echo "  2. Deploy frontend: ./scripts/deploy-frontend.sh"
    echo "  3. Setup CI/CD: ./scripts/setup-cicd.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found. Review before deploying.${NC}"
    echo ""
    echo "You can proceed with deployment, but some features may not work."
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) and $WARNINGS warning(s) found.${NC}"
    echo ""
    echo "Please fix the errors before deploying."
    exit 1
fi
