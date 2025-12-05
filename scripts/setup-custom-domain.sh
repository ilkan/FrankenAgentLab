#!/bin/bash
# Custom Domain Setup Script for FrankenAgent Lab
# Configures Cloud Load Balancer with SSL certificate and custom domain

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-frankenagent-prod}"
REGION="${GCP_REGION:-us-central1}"
DOMAIN="${CUSTOM_DOMAIN}"
BACKEND_SERVICE_NAME="frankenagent-backend"
FRONTEND_BUCKET="${PROJECT_ID}-frontend"

echo "========================================="
echo "Custom Domain Setup for FrankenAgent Lab"
echo "========================================="
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

# Check if domain is provided
if [ -z "$DOMAIN" ]; then
    echo "Please provide your custom domain:"
    echo ""
    echo "Examples:"
    echo "  - app.example.com"
    echo "  - frankenagent.example.com"
    echo ""
    read -p "Enter domain: " DOMAIN
    echo ""
fi

if [ -z "$DOMAIN" ]; then
    error "Domain is required"
fi

# Validate domain format
if ! echo "$DOMAIN" | grep -qE '^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$'; then
    error "Invalid domain format: $DOMAIN"
fi

info "Domain: $DOMAIN"
info "Project: $PROJECT_ID"
echo ""

# Confirmation
echo -e "${YELLOW}⚠ WARNING: This will configure a custom domain with SSL${NC}"
echo ""
echo "This will:"
echo "  1. Create a global external IP address"
echo "  2. Create a managed SSL certificate for $DOMAIN"
echo "  3. Setup Cloud Load Balancer"
echo "  4. Configure backend service (Cloud Run)"
echo "  5. Configure frontend service (Cloud Storage)"
echo "  6. Update CORS settings"
echo ""
echo "Prerequisites:"
echo "  - You must own the domain $DOMAIN"
echo "  - You must be able to add DNS records"
echo ""
read -p "Continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Set project
info "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
info "Enabling required APIs..."
gcloud services enable compute.googleapis.com
gcloud services enable certificatemanager.googleapis.com
success "APIs enabled"
echo ""

# Step 1: Reserve global IP address
echo "========================================="
echo "Step 1: Reserve Global IP Address"
echo "========================================="
echo ""

IP_NAME="frankenagent-ip"

if gcloud compute addresses describe $IP_NAME --global &> /dev/null; then
    info "IP address already exists"
    IP_ADDRESS=$(gcloud compute addresses describe $IP_NAME --global --format="value(address)")
else
    info "Creating global IP address..."
    gcloud compute addresses create $IP_NAME \
        --ip-version=IPV4 \
        --global
    
    IP_ADDRESS=$(gcloud compute addresses describe $IP_NAME --global --format="value(address)")
    success "IP address created"
fi

info "IP Address: $IP_ADDRESS"
echo ""

# Step 2: Create managed SSL certificate
echo "========================================="
echo "Step 2: Create Managed SSL Certificate"
echo "========================================="
echo ""

CERT_NAME="frankenagent-cert"

if gcloud compute ssl-certificates describe $CERT_NAME --global &> /dev/null; then
    info "SSL certificate already exists"
else
    info "Creating managed SSL certificate for $DOMAIN..."
    gcloud compute ssl-certificates create $CERT_NAME \
        --domains=$DOMAIN \
        --global
    
    success "SSL certificate created"
fi

info "Certificate: $CERT_NAME"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: Add DNS record before certificate can be provisioned${NC}"
echo ""
echo "Add this A record to your DNS:"
echo "  Type: A"
echo "  Name: $(echo $DOMAIN | cut -d'.' -f1)"
echo "  Value: $IP_ADDRESS"
echo "  TTL: 300"
echo ""
echo "Certificate provisioning will take 15-60 minutes after DNS is configured."
echo ""

# Step 3: Create backend NEG for Cloud Run
echo "========================================="
echo "Step 3: Configure Backend (Cloud Run)"
echo "========================================="
echo ""

NEG_NAME="frankenagent-backend-neg"

# Get Cloud Run service URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)" | sed 's|https://||')

if gcloud compute network-endpoint-groups describe $NEG_NAME --region=$REGION --global-access &> /dev/null 2>&1; then
    info "Backend NEG already exists"
else
    info "Creating serverless NEG for Cloud Run..."
    gcloud compute network-endpoint-groups create $NEG_NAME \
        --region=$REGION \
        --network-endpoint-type=serverless \
        --cloud-run-service=$BACKEND_SERVICE_NAME \
        --global-access
    
    success "Backend NEG created"
fi

# Create backend service
BACKEND_SERVICE="frankenagent-backend-service"

if gcloud compute backend-services describe $BACKEND_SERVICE --global &> /dev/null; then
    info "Backend service already exists"
else
    info "Creating backend service..."
    gcloud compute backend-services create $BACKEND_SERVICE \
        --global \
        --load-balancing-scheme=EXTERNAL_MANAGED \
        --protocol=HTTPS
    
    gcloud compute backend-services add-backend $BACKEND_SERVICE \
        --global \
        --network-endpoint-group=$NEG_NAME \
        --network-endpoint-group-region=$REGION
    
    success "Backend service created"
fi

echo ""

# Step 4: Create backend bucket for frontend
echo "========================================="
echo "Step 4: Configure Frontend (Cloud Storage)"
echo "========================================="
echo ""

BACKEND_BUCKET="frankenagent-frontend-bucket"

if gcloud compute backend-buckets describe $BACKEND_BUCKET --global &> /dev/null; then
    info "Backend bucket already exists"
else
    info "Creating backend bucket..."
    gcloud compute backend-buckets create $BACKEND_BUCKET \
        --gcs-bucket-name=$FRONTEND_BUCKET \
        --enable-cdn \
        --global
    
    success "Backend bucket created"
fi

echo ""

# Step 5: Create URL map
echo "========================================="
echo "Step 5: Configure URL Routing"
echo "========================================="
echo ""

URL_MAP="frankenagent-url-map"

if gcloud compute url-maps describe $URL_MAP --global &> /dev/null; then
    info "URL map already exists"
else
    info "Creating URL map..."
    
    # Create URL map with frontend as default
    gcloud compute url-maps create $URL_MAP \
        --default-backend-bucket=$BACKEND_BUCKET \
        --global
    
    # Add path matcher for API routes
    gcloud compute url-maps add-path-matcher $URL_MAP \
        --path-matcher-name=api-matcher \
        --default-backend-bucket=$BACKEND_BUCKET \
        --backend-service-path-rules="/api/*=$BACKEND_SERVICE,/health=$BACKEND_SERVICE,/docs=$BACKEND_SERVICE,/redoc=$BACKEND_SERVICE,/openapi.json=$BACKEND_SERVICE" \
        --global
    
    success "URL map created"
fi

echo ""

# Step 6: Create HTTPS proxy
echo "========================================="
echo "Step 6: Configure HTTPS Proxy"
echo "========================================="
echo ""

HTTPS_PROXY="frankenagent-https-proxy"

if gcloud compute target-https-proxies describe $HTTPS_PROXY --global &> /dev/null; then
    info "HTTPS proxy already exists"
else
    info "Creating HTTPS proxy..."
    gcloud compute target-https-proxies create $HTTPS_PROXY \
        --ssl-certificates=$CERT_NAME \
        --url-map=$URL_MAP \
        --global
    
    success "HTTPS proxy created"
fi

echo ""

# Step 7: Create forwarding rule
echo "========================================="
echo "Step 7: Configure Load Balancer"
echo "========================================="
echo ""

FORWARDING_RULE="frankenagent-https-rule"

if gcloud compute forwarding-rules describe $FORWARDING_RULE --global &> /dev/null; then
    info "Forwarding rule already exists"
else
    info "Creating forwarding rule..."
    gcloud compute forwarding-rules create $FORWARDING_RULE \
        --address=$IP_NAME \
        --target-https-proxy=$HTTPS_PROXY \
        --global \
        --ports=443
    
    success "Forwarding rule created"
fi

echo ""

# Step 8: Create HTTP to HTTPS redirect
echo "========================================="
echo "Step 8: Configure HTTP to HTTPS Redirect"
echo "========================================="
echo ""

HTTP_PROXY="frankenagent-http-proxy"
HTTP_RULE="frankenagent-http-rule"

if gcloud compute target-http-proxies describe $HTTP_PROXY --global &> /dev/null; then
    info "HTTP redirect already configured"
else
    info "Creating HTTP to HTTPS redirect..."
    
    # Create URL map for redirect
    gcloud compute url-maps import frankenagent-http-redirect \
        --global \
        --source /dev/stdin <<EOF
name: frankenagent-http-redirect
defaultUrlRedirect:
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
  httpsRedirect: true
EOF
    
    # Create HTTP proxy
    gcloud compute target-http-proxies create $HTTP_PROXY \
        --url-map=frankenagent-http-redirect \
        --global
    
    # Create forwarding rule
    gcloud compute forwarding-rules create $HTTP_RULE \
        --address=$IP_NAME \
        --target-http-proxy=$HTTP_PROXY \
        --global \
        --ports=80
    
    success "HTTP redirect configured"
fi

echo ""

# Step 9: Update CORS settings
echo "========================================="
echo "Step 9: Update CORS Settings"
echo "========================================="
echo ""

info "Updating CORS configuration for custom domain..."

cat > /tmp/cors.json <<EOF
[
  {
    "origin": ["https://$DOMAIN", "http://localhost:3000"],
    "method": ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"],
    "responseHeader": ["Content-Type", "Authorization", "X-Requested-With"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set /tmp/cors.json gs://$FRONTEND_BUCKET
rm /tmp/cors.json

success "CORS settings updated"
echo ""

# Step 10: Update Cloud Run service to allow custom domain
echo "========================================="
echo "Step 10: Update Backend Service"
echo "========================================="
echo ""

info "Updating Cloud Run service configuration..."

# Update service to allow all traffic (including from load balancer)
gcloud run services update $BACKEND_SERVICE_NAME \
    --region=$REGION \
    --ingress=all \
    --quiet

success "Backend service updated"
echo ""

# Summary
echo "========================================="
echo "✓ Custom Domain Setup Complete!"
echo "========================================="
echo ""
echo "Configuration Summary:"
echo "  Domain: $DOMAIN"
echo "  IP Address: $IP_ADDRESS"
echo "  SSL Certificate: $CERT_NAME (provisioning...)"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT NEXT STEPS:${NC}"
echo ""
echo "1. Add DNS A record:"
echo "   Type: A"
echo "   Name: $(echo $DOMAIN | cut -d'.' -f1)"
echo "   Value: $IP_ADDRESS"
echo "   TTL: 300"
echo ""
echo "2. Wait for DNS propagation (5-30 minutes)"
echo "   Check with: dig $DOMAIN"
echo ""
echo "3. Wait for SSL certificate provisioning (15-60 minutes)"
echo "   Check status:"
echo "   gcloud compute ssl-certificates describe $CERT_NAME --global"
echo ""
echo "4. Test your domain:"
echo "   curl https://$DOMAIN/health"
echo "   open https://$DOMAIN"
echo ""
echo "5. Update frontend environment variables:"
echo "   REACT_APP_API_URL=https://$DOMAIN"
echo "   Then redeploy frontend"
echo ""
echo "Monitoring:"
echo "  Load Balancer: https://console.cloud.google.com/net-services/loadbalancing/list"
echo "  SSL Certificate: https://console.cloud.google.com/security/ccm/list/lbCertificates"
echo ""

