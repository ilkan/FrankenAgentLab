#!/bin/bash
# Production Deployment Verification Script
# Tests all critical endpoints and configurations

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="https://frankenagent-backend-636617621192.us-central1.run.app"
FRONTEND_URL="https://storage.googleapis.com/frankenagent-prod-frontend/index.html"

echo "========================================="
echo "FrankenAgent Lab - Production Verification"
echo "========================================="
echo ""

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected_code)"
        ((FAILED++))
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local name=$1
    local url=$2
    local expected_field=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s "$url" 2>&1)
    
    if echo "$response" | grep -q "$expected_field"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Response: $response"
        ((FAILED++))
    fi
}

echo "=== Backend Tests ==="
echo ""

# Test health endpoint
test_json_endpoint "Health Check" "$BACKEND_URL/health" "healthy"

# Test API docs
test_endpoint "API Documentation" "$BACKEND_URL/docs" 200

# Test OAuth URL generation
test_json_endpoint "Google OAuth URL" "$BACKEND_URL/api/auth/oauth/url/google" "auth_url"
test_json_endpoint "GitHub OAuth URL" "$BACKEND_URL/api/auth/oauth/url/github" "auth_url"

echo ""
echo "=== Frontend Tests ==="
echo ""

# Test frontend
test_endpoint "Frontend HTML" "$FRONTEND_URL" 200

# Test frontend assets
test_endpoint "Frontend Assets" "https://storage.googleapis.com/frankenagent-prod-frontend/assets/" 200

echo ""
echo "=== Database Tests ==="
echo ""

# Test registration (creates a test user)
echo -n "Testing User Registration... "
response=$(curl -s -X POST "$BACKEND_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"test-$(date +%s)@example.com\",\"password\":\"testpass123\",\"full_name\":\"Test User\"}" 2>&1)

if echo "$response" | grep -q "access_token"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Response: $response"
    ((FAILED++))
fi

echo ""
echo "=== Configuration Tests ==="
echo ""

# Test CORS headers
echo -n "Testing CORS Configuration... "
cors_response=$(curl -s -I -X OPTIONS "$BACKEND_URL/api/auth/register" \
    -H "Origin: https://frankenagent.com" \
    -H "Access-Control-Request-Method: POST" 2>&1)

if echo "$cors_response" | grep -q "access-control-allow-origin"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} (CORS headers not found)"
    ((FAILED++))
fi

# Test SSL/TLS
echo -n "Testing SSL Certificate... "
ssl_response=$(curl -s -I "$BACKEND_URL" 2>&1)

if echo "$ssl_response" | grep -q "HTTP/2 200"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo ""
echo "========================================="
echo "Verification Summary"
echo "========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Production deployment is healthy.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    exit 1
fi
