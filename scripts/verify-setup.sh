#!/bin/bash

echo "=== FrankenAgent Lab Setup Verification ==="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ALL_GOOD=true

# Check gcloud CLI
echo -n "Checking Google Cloud CLI... "
if command -v gcloud &> /dev/null; then
    VERSION=$(gcloud version --format="value(core)" 2>/dev/null | head -n1)
    echo -e "${GREEN}✓ Installed${NC} (version: ${VERSION})"
else
    echo -e "${RED}✗ Not installed${NC}"
    echo "  Run: ./scripts/install-gcp-cli.sh"
    ALL_GOOD=false
fi

# Check Firebase CLI
echo -n "Checking Firebase CLI... "
if command -v firebase &> /dev/null; then
    VERSION=$(firebase --version 2>/dev/null)
    echo -e "${GREEN}✓ Installed${NC} (version: ${VERSION})"
else
    echo -e "${RED}✗ Not installed${NC}"
    echo "  Run: ./scripts/install-firebase-cli.sh"
    ALL_GOOD=false
fi

# Check gcloud authentication
echo -n "Checking gcloud authentication... "
if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -n1)
    echo -e "${GREEN}✓ Authenticated${NC} (${ACCOUNT})"
else
    echo -e "${YELLOW}⚠ Not authenticated${NC}"
    echo "  Run: gcloud auth login"
    ALL_GOOD=false
fi

# Check active GCP project
echo -n "Checking active GCP project... "
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -n "$PROJECT_ID" ]; then
    echo -e "${GREEN}✓ Set${NC} (${PROJECT_ID})"
else
    echo -e "${YELLOW}⚠ Not set${NC}"
    echo "  Run: ./scripts/setup-gcp-project.sh"
    ALL_GOOD=false
fi

# Check .env file
echo -n "Checking .env file... "
if [ -f .env ]; then
    echo -e "${GREEN}✓ Exists${NC}"
    
    # Check for GCP_PROJECT_ID
    if grep -q "^GCP_PROJECT_ID=" .env; then
        ENV_PROJECT=$(grep "^GCP_PROJECT_ID=" .env | cut -d'=' -f2)
        if [ "$ENV_PROJECT" != "your-gcp-project-id" ] && [ -n "$ENV_PROJECT" ]; then
            echo "  GCP_PROJECT_ID: ${ENV_PROJECT}"
        else
            echo -e "  ${YELLOW}⚠ GCP_PROJECT_ID not configured${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ GCP_PROJECT_ID missing${NC}"
    fi
else
    echo -e "${RED}✗ Not found${NC}"
    echo "  Run: cp .env.example .env"
    ALL_GOOD=false
fi

# Check Node.js (for Firebase)
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    VERSION=$(node --version)
    echo -e "${GREEN}✓ Installed${NC} (${VERSION})"
else
    echo -e "${YELLOW}⚠ Not installed${NC}"
    echo "  Required for Firebase CLI"
fi

# Check Python
echo -n "Checking Python... "
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Installed${NC} (${VERSION})"
else
    echo -e "${RED}✗ Not installed${NC}"
    ALL_GOOD=false
fi

# Check Poetry
echo -n "Checking Poetry... "
if command -v poetry &> /dev/null; then
    VERSION=$(poetry --version | cut -d' ' -f3)
    echo -e "${GREEN}✓ Installed${NC} (${VERSION})"
else
    echo -e "${YELLOW}⚠ Not installed${NC}"
    echo "  Install: curl -sSL https://install.python-poetry.org | python3 -"
fi

# Check GCP infrastructure (if project is set)
if [ -n "$PROJECT_ID" ]; then
    echo ""
    echo "=== Checking GCP Infrastructure ==="
    
    REGION="us-central1"
    if [ -f .env ] && grep -q "^GCP_REGION=" .env; then
        REGION=$(grep "^GCP_REGION=" .env | cut -d'=' -f2)
    fi
    
    # Check Cloud SQL
    echo -n "Checking Cloud SQL instance... "
    if gcloud sql instances describe frankenagent-db --project=${PROJECT_ID} &>/dev/null; then
        echo -e "${GREEN}✓ Exists${NC} (frankenagent-db)"
    else
        echo -e "${YELLOW}⚠ Not found${NC}"
        echo "  Run: ./scripts/setup-infrastructure.sh"
    fi
    
    # Check Redis
    echo -n "Checking Redis instance... "
    if gcloud redis instances describe frankenagent-cache --region=${REGION} --project=${PROJECT_ID} &>/dev/null; then
        echo -e "${GREEN}✓ Exists${NC} (frankenagent-cache)"
    else
        echo -e "${YELLOW}⚠ Not found${NC}"
        echo "  Run: ./scripts/setup-infrastructure.sh"
    fi
    
    # Check Storage bucket
    echo -n "Checking Storage bucket... "
    BUCKET_NAME="${PROJECT_ID}-frontend"
    if gsutil ls -b gs://${BUCKET_NAME} &>/dev/null 2>&1; then
        echo -e "${GREEN}✓ Exists${NC} (${BUCKET_NAME})"
    else
        echo -e "${YELLOW}⚠ Not found${NC}"
        echo "  Run: ./scripts/setup-infrastructure.sh"
    fi
    
    # Check KMS keyring
    echo -n "Checking KMS keyring... "
    if gcloud kms keyrings describe frankenagent-keyring --location=${REGION} --project=${PROJECT_ID} &>/dev/null; then
        echo -e "${GREEN}✓ Exists${NC} (frankenagent-keyring)"
    else
        echo -e "${YELLOW}⚠ Not found${NC}"
        echo "  Run: ./scripts/setup-infrastructure.sh"
    fi
    
    # Check secrets
    echo ""
    echo "Checking Secret Manager secrets:"
    
    SECRETS=("DATABASE_URL" "REDIS_HOST" "OPENAI_API_KEY" "TAVILY_API_KEY" "JWT_SECRET_KEY")
    for SECRET in "${SECRETS[@]}"; do
        echo -n "  ${SECRET}... "
        if gcloud secrets describe ${SECRET} --project=${PROJECT_ID} &>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠ Not found${NC}"
            if [ "$SECRET" = "DATABASE_URL" ] || [ "$SECRET" = "REDIS_HOST" ]; then
                echo "    Run: ./scripts/setup-infrastructure.sh"
            else
                echo "    Run: ./scripts/add-secrets.sh"
            fi
        fi
    done
fi

echo ""
echo "=== Summary ==="
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All required tools are installed and configured!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./scripts/setup-infrastructure.sh (if not done)"
    echo "  2. Run: ./scripts/add-secrets.sh (to add API keys)"
    echo "  3. Run database migrations (Task 3)"
    echo "  4. Deploy backend (Task 13)"
    echo "  5. Deploy frontend (Task 13)"
else
    echo -e "${YELLOW}⚠ Some setup steps are incomplete.${NC}"
    echo "Please follow the instructions above to complete setup."
fi
