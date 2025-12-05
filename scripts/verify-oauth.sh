#!/bin/bash

# OAuth Setup Verification Script
# This script verifies that Google OAuth is properly configured

set -e

echo "=========================================="
echo "Google OAuth Setup Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi

echo -e "${GREEN}✓ .env file found${NC}"

# Load environment variables
source .env

# Check Google OAuth credentials
echo ""
echo "Checking OAuth credentials..."
echo ""

if [ -z "$GOOGLE_CLIENT_ID" ]; then
    echo -e "${RED}✗ GOOGLE_CLIENT_ID not set${NC}"
    MISSING_VARS=1
else
    echo -e "${GREEN}✓ GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:0:30}...${NC}"
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo -e "${RED}✗ GOOGLE_CLIENT_SECRET not set${NC}"
    MISSING_VARS=1
else
    echo -e "${GREEN}✓ GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET:0:15}...${NC}"
fi

if [ -z "$OAUTH_REDIRECT_URI" ]; then
    echo -e "${RED}✗ OAUTH_REDIRECT_URI not set${NC}"
    MISSING_VARS=1
else
    echo -e "${GREEN}✓ OAUTH_REDIRECT_URI: $OAUTH_REDIRECT_URI${NC}"
fi

if [ ! -z "$MISSING_VARS" ]; then
    echo ""
    echo -e "${RED}Missing OAuth credentials!${NC}"
    echo "Please configure them in your .env file"
    echo ""
    echo "See docs/OAUTH_SETUP.md for instructions"
    exit 1
fi

# Check if server is running
echo ""
echo "Checking if server is running..."
echo ""

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running at http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠ Server is not running${NC}"
    echo "Start the server with:"
    echo "  poetry run uvicorn frankenagent.api.server:app --reload"
    echo ""
    echo "Then run this script again"
    exit 0
fi

# Test OAuth URL endpoint
echo ""
echo "Testing OAuth URL endpoint..."
echo ""

OAUTH_RESPONSE=$(curl -s http://localhost:8000/api/auth/oauth/url/google)

if echo "$OAUTH_RESPONSE" | grep -q "auth_url"; then
    echo -e "${GREEN}✓ OAuth URL endpoint is working${NC}"
    
    # Extract and display the auth URL
    AUTH_URL=$(echo "$OAUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['auth_url'])" 2>/dev/null || echo "")
    
    if [ ! -z "$AUTH_URL" ]; then
        echo ""
        echo "=========================================="
        echo "Manual Test Instructions"
        echo "=========================================="
        echo ""
        echo "1. Open this URL in your browser:"
        echo ""
        echo "$AUTH_URL"
        echo ""
        echo "2. Log in with your Google account"
        echo "3. After authorization, check the redirect URL"
        echo "4. If you see a 'code' parameter, OAuth is working!"
        echo ""
    fi
else
    echo -e "${RED}✗ OAuth URL endpoint failed${NC}"
    echo "Response: $OAUTH_RESPONSE"
    exit 1
fi

# Run integration tests
echo ""
echo "Running integration tests..."
echo ""

if poetry run pytest tests/test_google_oauth_integration.py -v; then
    echo ""
    echo -e "${GREEN}✓ All integration tests passed${NC}"
else
    echo ""
    echo -e "${RED}✗ Some integration tests failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ Google OAuth is properly configured!${NC}"
echo ""
echo "To test the full OAuth flow:"
echo "  python tests/test_google_oauth_manual.py"
echo ""
