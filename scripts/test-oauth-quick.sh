#!/bin/bash

# Quick OAuth Test Script
# Tests Google OAuth endpoints without complex async code

echo "=========================================="
echo "Google OAuth Quick Test"
echo "=========================================="
echo ""

# Test 1: Server Health
echo "Test 1: Server Health Check"
echo "----------------------------"
HEALTH=$(curl -s http://localhost:8000/ 2>&1)
if echo "$HEALTH" | grep -q "FrankenAgent Lab API"; then
    echo "✅ Server is running"
    echo "$HEALTH" | python3 -m json.tool
else
    echo "❌ Server is not running"
    echo "Start with: poetry run uvicorn frankenagent.api.server:app --reload"
    exit 1
fi

echo ""
echo "Test 2: OAuth Configuration"
echo "----------------------------"
if [ -z "$GOOGLE_CLIENT_ID" ]; then
    source .env 2>/dev/null || true
fi

if [ ! -z "$GOOGLE_CLIENT_ID" ]; then
    echo "✅ GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:0:30}..."
else
    echo "❌ GOOGLE_CLIENT_ID not configured"
fi

if [ ! -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "✅ GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET:0:15}..."
else
    echo "❌ GOOGLE_CLIENT_SECRET not configured"
fi

echo ""
echo "Test 3: OAuth URL Endpoint"
echo "----------------------------"
OAUTH_URL=$(curl -s http://localhost:8000/api/auth/oauth/url/google 2>&1)

if echo "$OAUTH_URL" | grep -q "auth_url"; then
    echo "✅ OAuth URL endpoint working"
    echo ""
    echo "Response:"
    echo "$OAUTH_URL" | python3 -m json.tool
    
    # Extract the auth URL
    AUTH_URL=$(echo "$OAUTH_URL" | python3 -c "import sys, json; print(json.load(sys.stdin)['auth_url'])" 2>/dev/null)
    
    echo ""
    echo "=========================================="
    echo "✅ All Tests Passed!"
    echo "=========================================="
    echo ""
    echo "To test the complete OAuth flow:"
    echo ""
    echo "1. Open this URL in your browser:"
    echo ""
    echo "$AUTH_URL"
    echo ""
    echo "2. Log in with Google and authorize"
    echo "3. Copy the 'code' from the redirect URL"
    echo "4. Test the code exchange:"
    echo ""
    echo "curl -X POST http://localhost:8000/api/auth/oauth/login \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"provider\": \"google\", \"code\": \"YOUR_CODE\", \"redirect_uri\": \"http://localhost:8000\"}'"
    echo ""
else
    echo "❌ OAuth URL endpoint failed"
    echo "Response: $OAUTH_URL"
    exit 1
fi
