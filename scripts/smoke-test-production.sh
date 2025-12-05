#!/bin/bash
# Smoke Tests for Production Deployment
# Validates that all critical endpoints are working

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-frankenagent-prod}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="frankenagent-backend"

echo "========================================="
echo "Production Smoke Tests"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}✗ FAILED: $1${NC}"
    ((FAILURES++))
}

success() {
    echo -e "${GREEN}✓ PASSED: $1${NC}"
    ((PASSES++))
}

info() {
    echo "ℹ $1"
}

PASSES=0
FAILURES=0

# Get backend URL
info "Getting backend URL..."
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

if [ -z "$BACKEND_URL" ]; then
    error "Could not get backend URL"
    exit 1
fi

info "Backend URL: $BACKEND_URL"
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | grep -q "healthy"; then
        success "Health check endpoint returns 200 and healthy status"
    else
        error "Health check returns 200 but unexpected body: $BODY"
    fi
else
    error "Health check returned HTTP $HTTP_CODE"
fi
echo ""

# Test 2: API Documentation
echo "Test 2: API Documentation"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/docs")

if [ "$HTTP_CODE" = "200" ]; then
    success "API documentation accessible"
else
    error "API docs returned HTTP $HTTP_CODE"
fi
echo ""

# Test 3: User Registration
echo "Test 3: User Registration"
RANDOM_EMAIL="test-$(date +%s)@example.com"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$RANDOM_EMAIL\",\"password\":\"TestPass123!\",\"full_name\":\"Test User\"}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "201" ]; then
    if echo "$BODY" | grep -q "access_token"; then
        success "User registration works and returns JWT token"
        # Extract token for subsequent tests
        TOKEN=$(echo "$BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    else
        error "Registration returns 201 but no token in response"
    fi
elif [ "$HTTP_CODE" = "400" ]; then
    # Email might already exist, try login instead
    info "Registration returned 400 (email may exist), trying login..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$RANDOM_EMAIL\",\"password\":\"TestPass123!\"}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        success "Login works as fallback"
        TOKEN=$(echo "$BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    else
        error "Both registration and login failed"
    fi
else
    error "Registration returned HTTP $HTTP_CODE"
fi
echo ""

# Test 4: Protected Endpoint (requires auth)
if [ -n "$TOKEN" ]; then
    echo "Test 4: Protected Endpoint (/api/auth/me)"
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/auth/me" \
        -H "Authorization: Bearer $TOKEN")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q "email"; then
            success "Protected endpoint works with valid token"
        else
            error "Protected endpoint returns 200 but unexpected body"
        fi
    else
        error "Protected endpoint returned HTTP $HTTP_CODE"
    fi
    echo ""
    
    # Test 5: Blueprint Creation
    echo "Test 5: Blueprint Creation"
    BLUEPRINT_DATA='{"name":"Test Agent","description":"Smoke test agent","blueprint_data":{"head":{"model":"gpt-4","provider":"openai","system_prompt":"You are a test agent"},"legs":{"execution_mode":"single_agent"}}}'
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/blueprints" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$BLUEPRINT_DATA")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "201" ]; then
        if echo "$BODY" | grep -q "id"; then
            success "Blueprint creation works"
            BLUEPRINT_ID=$(echo "$BODY" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
        else
            error "Blueprint creation returns 201 but no ID in response"
        fi
    else
        error "Blueprint creation returned HTTP $HTTP_CODE: $BODY"
    fi
    echo ""
    
    # Test 6: Blueprint Retrieval
    if [ -n "$BLUEPRINT_ID" ]; then
        echo "Test 6: Blueprint Retrieval"
        RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/blueprints/$BLUEPRINT_ID" \
            -H "Authorization: Bearer $TOKEN")
        
        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
        
        if [ "$HTTP_CODE" = "200" ]; then
            success "Blueprint retrieval works"
        else
            error "Blueprint retrieval returned HTTP $HTTP_CODE"
        fi
        echo ""
    fi
    
    # Test 7: Marketplace Listing
    echo "Test 7: Marketplace Listing"
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/marketplace")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q "listings"; then
            success "Marketplace listing works"
        else
            error "Marketplace returns 200 but unexpected format"
        fi
    else
        error "Marketplace returned HTTP $HTTP_CODE"
    fi
    echo ""
    
    # Test 8: Session Creation
    if [ -n "$BLUEPRINT_ID" ]; then
        echo "Test 8: Session Creation"
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/sessions" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"blueprint_id\":\"$BLUEPRINT_ID\"}")
        
        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
        
        if [ "$HTTP_CODE" = "201" ]; then
            success "Session creation works"
        else
            error "Session creation returned HTTP $HTTP_CODE"
        fi
        echo ""
    fi
else
    warning "Skipping protected endpoint tests (no auth token)"
fi

# Test 9: Rate Limiting Headers
echo "Test 9: Rate Limiting Headers"
RESPONSE=$(curl -s -I "$BACKEND_URL/health")

if echo "$RESPONSE" | grep -qi "x-ratelimit"; then
    success "Rate limiting headers present"
else
    info "Rate limiting headers not found (may not be enabled on health endpoint)"
fi
echo ""

# Test 10: CORS Headers
echo "Test 10: CORS Headers"
RESPONSE=$(curl -s -I -X OPTIONS "$BACKEND_URL/api/auth/register" \
    -H "Origin: https://example.com" \
    -H "Access-Control-Request-Method: POST")

if echo "$RESPONSE" | grep -qi "access-control-allow"; then
    success "CORS headers configured"
else
    warning "CORS headers not found"
fi
echo ""

# Summary
echo "========================================="
echo "Smoke Test Summary"
echo "========================================="
echo ""
echo -e "${GREEN}Passed: $PASSES${NC}"
echo -e "${RED}Failed: $FAILURES${NC}"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    echo ""
    echo "Production deployment is healthy and ready to use."
    exit 0
else
    echo -e "${RED}✗ Some tests failed!${NC}"
    echo ""
    echo "Please investigate the failures before using production."
    echo ""
    echo "View logs:"
    echo "  gcloud run services logs read $SERVICE_NAME --region=$REGION --follow"
    exit 1
fi

