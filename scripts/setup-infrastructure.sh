#!/bin/bash
set -e

echo "=== GCP Infrastructure Setup ==="
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

# Set default region
REGION="us-central1"
if [ -f .env ] && grep -q "^GCP_REGION=" .env; then
    REGION=$(grep "^GCP_REGION=" .env | cut -d '=' -f2)
fi

echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Set project
gcloud config set project ${PROJECT_ID}

# Verify billing is enabled
echo "Checking billing status..."
BILLING_ENABLED=$(gcloud beta billing projects describe ${PROJECT_ID} --format="value(billingEnabled)" 2>/dev/null || echo "false")

if [ "$BILLING_ENABLED" != "True" ]; then
    echo "⚠️  WARNING: Billing is not enabled for this project."
    echo "   Please enable billing at: https://console.cloud.google.com/billing/linkedaccount?project=${PROJECT_ID}"
    read -p "Press Enter after enabling billing to continue..."
fi

# Resource names
DB_INSTANCE="frankenagent-db"
REDIS_INSTANCE="frankenagent-cache"
BUCKET_NAME="${PROJECT_ID}-frontend"
KMS_KEYRING="frankenagent-keyring"
KMS_KEY="api-key-encryption"

echo ""
echo "=== Step 1: Creating Cloud SQL Instance ==="
echo "This will take 5-10 minutes..."

# Check if instance already exists
if gcloud sql instances describe ${DB_INSTANCE} --project=${PROJECT_ID} &>/dev/null; then
    echo "Cloud SQL instance '${DB_INSTANCE}' already exists. Skipping creation."
else
    gcloud sql instances create ${DB_INSTANCE} \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=${REGION} \
        --storage-type=SSD \
        --storage-size=10GB \
        --backup \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --project=${PROJECT_ID}
    
    echo "✓ Cloud SQL instance created"
fi

# Create database
echo ""
echo "Creating database 'frankenagent'..."
if gcloud sql databases describe frankenagent --instance=${DB_INSTANCE} --project=${PROJECT_ID} &>/dev/null; then
    echo "Database 'frankenagent' already exists. Skipping creation."
else
    gcloud sql databases create frankenagent \
        --instance=${DB_INSTANCE} \
        --project=${PROJECT_ID}
    
    echo "✓ Database created"
fi

# Create database user
echo ""
echo "Creating database user..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

if gcloud sql users list --instance=${DB_INSTANCE} --project=${PROJECT_ID} | grep -q "frankenagent"; then
    echo "User 'frankenagent' already exists. Updating password..."
    gcloud sql users set-password frankenagent \
        --instance=${DB_INSTANCE} \
        --password=${DB_PASSWORD} \
        --project=${PROJECT_ID}
else
    gcloud sql users create frankenagent \
        --instance=${DB_INSTANCE} \
        --password=${DB_PASSWORD} \
        --project=${PROJECT_ID}
fi

echo "✓ Database user configured"

# Store database URL in Secret Manager
echo ""
echo "Storing database credentials in Secret Manager..."
DB_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${DB_INSTANCE}"
DATABASE_URL="postgresql://frankenagent:${DB_PASSWORD}@/frankenagent?host=/cloudsql/${DB_CONNECTION_NAME}"

if gcloud secrets describe DATABASE_URL --project=${PROJECT_ID} &>/dev/null; then
    echo "Secret 'DATABASE_URL' already exists. Creating new version..."
    echo -n "${DATABASE_URL}" | gcloud secrets versions add DATABASE_URL --data-file=- --project=${PROJECT_ID}
else
    echo -n "${DATABASE_URL}" | gcloud secrets create DATABASE_URL --data-file=- --project=${PROJECT_ID}
fi

echo "✓ Database credentials stored"

# Create Redis instance
echo ""
echo "=== Step 2: Creating Redis Instance ==="
echo "This will take 3-5 minutes..."

if gcloud redis instances describe ${REDIS_INSTANCE} --region=${REGION} --project=${PROJECT_ID} &>/dev/null; then
    echo "Redis instance '${REDIS_INSTANCE}' already exists. Skipping creation."
else
    gcloud redis instances create ${REDIS_INSTANCE} \
        --size=1 \
        --region=${REGION} \
        --redis-version=redis_7_0 \
        --tier=basic \
        --project=${PROJECT_ID}
    
    echo "✓ Redis instance created"
fi

# Get Redis host
echo ""
echo "Retrieving Redis host..."
REDIS_HOST=$(gcloud redis instances describe ${REDIS_INSTANCE} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(host)")

echo "Redis host: ${REDIS_HOST}"

# Store Redis host in Secret Manager
if gcloud secrets describe REDIS_HOST --project=${PROJECT_ID} &>/dev/null; then
    echo "Secret 'REDIS_HOST' already exists. Creating new version..."
    echo -n "${REDIS_HOST}" | gcloud secrets versions add REDIS_HOST --data-file=- --project=${PROJECT_ID}
else
    echo -n "${REDIS_HOST}" | gcloud secrets create REDIS_HOST --data-file=- --project=${PROJECT_ID}
fi

echo "✓ Redis host stored"

# Create Cloud Storage bucket
echo ""
echo "=== Step 3: Creating Cloud Storage Bucket ==="

if gsutil ls -b gs://${BUCKET_NAME} &>/dev/null; then
    echo "Bucket 'gs://${BUCKET_NAME}' already exists. Skipping creation."
else
    gsutil mb -l ${REGION} -p ${PROJECT_ID} gs://${BUCKET_NAME}
    echo "✓ Bucket created"
fi

# Configure bucket for static website hosting
echo "Configuring bucket for static website hosting..."
gsutil web set -m index.html gs://${BUCKET_NAME}

# Make bucket publicly readable
echo "Making bucket publicly readable..."
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}

# Set CORS configuration
echo "Setting CORS configuration..."
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
gsutil cors set /tmp/cors.json gs://${BUCKET_NAME}
rm /tmp/cors.json

echo "✓ Bucket configured"

# Create KMS keyring and key
echo ""
echo "=== Step 4: Creating Cloud KMS Key ==="

# Create keyring
if gcloud kms keyrings describe ${KMS_KEYRING} --location=${REGION} --project=${PROJECT_ID} &>/dev/null; then
    echo "KMS keyring '${KMS_KEYRING}' already exists. Skipping creation."
else
    gcloud kms keyrings create ${KMS_KEYRING} \
        --location=${REGION} \
        --project=${PROJECT_ID}
    
    echo "✓ KMS keyring created"
fi

# Create key
if gcloud kms keys describe ${KMS_KEY} --keyring=${KMS_KEYRING} --location=${REGION} --project=${PROJECT_ID} &>/dev/null; then
    echo "KMS key '${KMS_KEY}' already exists. Skipping creation."
else
    gcloud kms keys create ${KMS_KEY} \
        --keyring=${KMS_KEYRING} \
        --location=${REGION} \
        --purpose=encryption \
        --project=${PROJECT_ID}
    
    echo "✓ KMS key created"
fi

# Update .env file with infrastructure details
echo ""
echo "=== Step 5: Updating .env File ==="

# Function to update or add env variable
update_env() {
    local key=$1
    local value=$2
    local file=".env"
    
    if grep -q "^${key}=" ${file}; then
        # Update existing line (macOS compatible)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^${key}=.*|${key}=${value}|" ${file}
        else
            sed -i "s|^${key}=.*|${key}=${value}|" ${file}
        fi
    else
        # Add new line
        echo "${key}=${value}" >> ${file}
    fi
}

update_env "GCP_PROJECT_ID" "${PROJECT_ID}"
update_env "GCP_REGION" "${REGION}"
update_env "DB_INSTANCE_NAME" "${DB_INSTANCE}"
update_env "DB_CONNECTION_NAME" "${DB_CONNECTION_NAME}"
update_env "REDIS_INSTANCE_NAME" "${REDIS_INSTANCE}"
update_env "REDIS_HOST" "${REDIS_HOST}"
update_env "REDIS_PORT" "6379"
update_env "STORAGE_BUCKET" "${BUCKET_NAME}"
update_env "KMS_KEYRING" "${KMS_KEYRING}"
update_env "KMS_KEY" "${KMS_KEY}"

echo "✓ .env file updated"

# Display summary
echo ""
echo "=== Infrastructure Setup Complete! ==="
echo ""
echo "Resources created:"
echo "  ✓ Cloud SQL Instance: ${DB_INSTANCE}"
echo "  ✓ Database: frankenagent"
echo "  ✓ Redis Instance: ${REDIS_INSTANCE} (${REDIS_HOST})"
echo "  ✓ Storage Bucket: gs://${BUCKET_NAME}"
echo "  ✓ KMS Keyring: ${KMS_KEYRING}"
echo "  ✓ KMS Key: ${KMS_KEY}"
echo ""
echo "Secrets stored in Secret Manager:"
echo "  ✓ DATABASE_URL"
echo "  ✓ REDIS_HOST"
echo ""
echo "⚠️  IMPORTANT: Next Steps"
echo ""
echo "1. Add platform API keys to Secret Manager:"
echo "   echo -n 'your-openai-key' | gcloud secrets create OPENAI_API_KEY --data-file=- --project=${PROJECT_ID}"
echo "   echo -n 'your-tavily-key' | gcloud secrets create TAVILY_API_KEY --data-file=- --project=${PROJECT_ID}"
echo ""
echo "2. Generate and store JWT secret:"
echo "   JWT_SECRET=\$(openssl rand -base64 32)"
echo "   echo -n \"\$JWT_SECRET\" | gcloud secrets create JWT_SECRET_KEY --data-file=- --project=${PROJECT_ID}"
echo ""
echo "3. Update your local .env file with API keys for development"
echo ""
echo "4. Run database migrations (after implementing Task 3):"
echo "   ./scripts/run-migrations.sh"
echo ""
echo "5. Deploy backend (after implementing Task 13):"
echo "   ./scripts/deploy-backend.sh"
echo ""
echo "6. Deploy frontend (after implementing Task 13):"
echo "   ./scripts/deploy-frontend.sh"
echo ""
echo "For more information, see: scripts/README.md"
