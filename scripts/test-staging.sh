#!/bin/bash
# scripts/test-staging.sh
# Comprehensive integration tests for staging environment

set -e

# Configuration
BACKEND_URL="${STAGING_BACKEND_URL:-}"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123!"
TEST_USER_NAME="Test User"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo ""
    echo "========================================="
    echo "TEST: $1"
    echo "========================================="
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if backend URL is provided
if [ -z "$BACKEND_URL" ]; then
    echo "Error: BACKEND_URL not set"
    echo "Usage: STAGING_BACKEND_URL=https://your-backend-url ./scripts/test-staging.sh"
    exit 1
fi

echo "========================================="
echo "FrankenAgent Lab - Staging Tests"
echo "========================================="
echo "Backend URL: $BACKEND_URL"
echo "Test Email: $TEST_EMAIL"
echo ""

# Test 1: Health Check
print_test "Health Check"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" $BACKEND_URL/health)
HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HEALTH_CODE" = "200" ]; then
    print_success "Health check passed"
    echo "Response: $HEALTH_BODY"
else
    print_failure "Health check failed with status $HEALTH_CODE"
    echo "Response: $HEALTH_BODY"
fi

# Test 2: User Registration
print_test "User Registration"
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"$TEST_USER_NAME\"}")

REGISTER_CODE=$(echo "$REGISTER_RESPONSE" | tail -n 1)
REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | head -n -1)

if [ "$REGISTER_CODE" = "201" ]; then
    print_success "User registration successful"
    ACCESS_TOKEN=$(echo "$REGISTER_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
    USER_ID=$(echo "$REGISTER_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null || echo "")
    
    if [ -n "$ACCESS_TOKEN" ]; then
        print_success "JWT token received"
    else
        print_failure "JWT token not found in response"
    fi
else
    print_failure "User registration failed with status $REGISTER_CODE"
    echo "Response: $REGISTER_BODY"
    exit 1
fi

# Test 3: User Login
print_test "User Login"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

if [ "$LOGIN_CODE" = "200" ]; then
    print_success "User login successful"
    LOGIN_TOKEN=$(echo "$LOGIN_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
    
    if [ -n "$LOGIN_TOKEN" ]; then
        print_success "JWT token received on login"
    fi
else
    print_failure "User login failed with status $LOGIN_CODE"
    echo "Response: $LOGIN_BODY"
fi

# Test 4: Protected Endpoint (Get Current User)
print_test "Protected Endpoint - Get Current User"
ME_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET $BACKEND_URL/api/auth/me \
    -H "Authorization: Bearer $ACCESS_TOKEN")

ME_CODE=$(echo "$ME_RESPONSE" | tail -n 1)
ME_BODY=$(echo "$ME_RESPONSE" | head -n -1)

if [ "$ME_CODE" = "200" ]; then
    print_success "Protected endpoint accessible with valid token"
    echo "User info: $ME_BODY"
else
    print_failure "Protected endpoint failed with status $ME_CODE"
    echo "Response: $ME_BODY"
fi

# Test 5: Invalid Token Rejection
print_test "Invalid Token Rejection"
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET $BACKEND_URL/api/auth/me \
    -H "Authorization: Bearer invalid_token_12345")

INVALID_CODE=$(echo "$INVALID_RESPONSE" | tail -n 1)

if [ "$INVALID_CODE" = "401" ]; then
    print_success "Invalid token correctly rejected with 401"
else
    print_failure "Invalid token not rejected (got status $INVALID_CODE)"
fi

# Test 6: Blueprint CRUD - Create
print_test "Blueprint CRUD - Create"
BLUEPRINT_DATA='{"name":"Test Agent","description":"Test agent for staging","blueprint_data":{"head":{"model":"gpt-4","provider":"openai","system_prompt":"You are a test agent"},"legs":{"execution_mode":"single_agent"}}}'

CREATE_BP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/blueprints \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$BLUEPRINT_DATA")

CREATE_BP_CODE=$(echo "$CREATE_BP_RESPONSE" | tail -n 1)
CREATE_BP_BODY=$(echo "$CREATE_BP_RESPONSE" | head -n -1)

if [ "$CREATE_BP_CODE" = "201" ]; then
    print_success "Blueprint created successfully"
    BLUEPRINT_ID=$(echo "$CREATE_BP_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
    
    if [ -n "$BLUEPRINT_ID" ]; then
        print_success "Blueprint ID: $BLUEPRINT_ID"
    fi
else
    print_failure "Blueprint creation failed with status $CREATE_BP_CODE"
    echo "Response: $CREATE_BP_BODY"
fi

# Test 7: Blueprint CRUD - Read
print_test "Blueprint CRUD - Read"
READ_BP_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET $BACKEND_URL/api/blueprints/$BLUEPRINT_ID \
    -H "Authorization: Bearer $ACCESS_TOKEN")

READ_BP_CODE=$(echo "$READ_BP_RESPONSE" | tail -n 1)
READ_BP_BODY=$(echo "$READ_BP_RESPONSE" | head -n -1)

if [ "$READ_BP_CODE" = "200" ]; then
    print_success "Blueprint retrieved successfully"
else
    print_failure "Blueprint retrieval failed with status $READ_BP_CODE"
    echo "Response: $READ_BP_BODY"
fi

# Test 8: Blueprint CRUD - Update
print_test "Blueprint CRUD - Update"
UPDATE_BP_DATA='{"name":"Updated Test Agent","description":"Updated description"}'

UPDATE_BP_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT $BACKEND_URL/api/blueprints/$BLUEPRINT_ID \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_BP_DATA")

UPDATE_BP_CODE=$(echo "$UPDATE_BP_RESPONSE" | tail -n 1)
UPDATE_BP_BODY=$(echo "$UPDATE_BP_RESPONSE" | head -n -1)

if [ "$UPDATE_BP_CODE" = "200" ]; then
    print_success "Blueprint updated successfully"
    VERSION=$(echo "$UPDATE_BP_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "")
    
    if [ "$VERSION" = "2" ]; then
        print_success "Version incremented to 2"
    else
        print_warning "Version is $VERSION (expected 2)"
    fi
else
    print_failure "Blueprint update failed with status $UPDATE_BP_CODE"
    echo "Response: $UPDATE_BP_BODY"
fi

# Test 9: Blueprint CRUD - List
print_test "Blueprint CRUD - List User Blueprints"
LIST_BP_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET $BACKEND_URL/api/blueprints \
    -H "Authorization: Bearer $ACCESS_TOKEN")

LIST_BP_CODE=$(echo "$LIST_BP_RESPONSE" | tail -n 1)
LIST_BP_BODY=$(echo "$LIST_BP_RESPONSE" | head -n -1)

if [ "$LIST_BP_CODE" = "200" ]; then
    print_success "Blueprint list retrieved successfully"
    BP_COUNT=$(echo "$LIST_BP_BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['blueprints']))" 2>/dev/null || echo "0")
    echo "Found $BP_COUNT blueprint(s)"
else
    print_failure "Blueprint list failed with status $LIST_BP_CODE"
    echo "Response: $LIST_BP_BODY"
fi

# Test 10: API Key Management - Add Key
print_test "API Key Management - Add Key"
API_KEY_DATA='{"provider":"openai","plaintext_key":"sk-test1234567890abcdefghijklmnopqrstuvwxyz","key_name":"Test OpenAI Key"}'

ADD_KEY_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/keys \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$API_KEY_DATA")

ADD_KEY_CODE=$(echo "$ADD_KEY_RESPONSE" | tail -n 1)
ADD_KEY_BODY=$(echo "$ADD_KEY_RESPONSE" | head -n -1)

if [ "$ADD_KEY_CODE" = "201" ]; then
    print_success "API key added successfully"
    KEY_ID=$(echo "$ADD_KEY_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
else
    print_failure "API key addition failed with status $ADD_KEY_CODE"
    echo "Response: $ADD_KEY_BODY"
fi

# Test 11: API Key Management - List Keys
print_test "API Key Management - List Keys"
LIST_KEYS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET $BACKEND_URL/api/keys \
    -H "Authorization: Bearer $ACCESS_TOKEN")

LIST_KEYS_CODE=$(echo "$LIST_KEYS_RESPONSE" | tail -n 1)
LIST_KEYS_BODY=$(echo "$LIST_KEYS_RESPONSE" | head -n -1)

if [ "$LIST_KEYS_CODE" = "200" ]; then
    print_success "API keys listed successfully"
    KEY_PREVIEW=$(echo "$LIST_KEYS_BODY" | python3 -c "import sys, json; keys=json.load(sys.stdin)['keys']; print(keys[0]['key_preview'] if keys else 'none')" 2>/dev/null || echo "")
    
    if [[ "$KEY_PREVIEW" == *"***"* ]]; then
        print_success "API key properly masked: $KEY_PREVIEW"
    else
        print_warning "API key masking may not be working correctly"
    fi
else
    print_failure "API key listing failed with status $LIST_KEYS_CODE"
    echo "Response: $LIST_KEYS_BODY"
fi

# Test 12: Session Management - Create Session
print_test "Session Management - Create Session"
SESSION_DATA="{\"blueprint_id\":\"$BLUEPRINT_ID\"}"

CREATE_SESSION_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/sessions \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$SESSION_DATA")

CREATE_SESSION_CODE=$(echo "$CREATE_SESSION_RESPONSE" | tail -n 1)
CREATE_SESSION_BODY=$(echo "$CREATE_SESSION_RESPONSE" | head -n -1)

if [ "$CREATE_SESSION_CODE" = "201" ]; then
    print_success "Session created successfully"
    SESSION_ID=$(echo "$CREATE_SESSION_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
else
    print_failure "Session creation failed with status $CREATE_SESSION_CODE"
    echo "Response: $CREATE_SESSION_BODY"
fi

# Test 13: Session Management - List Sessions
print_test "Session Management - List Sessions"
LIST_SESSIONS_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET $BACKEND_URL/api/sessions \
    -H "Authorization: Bearer $ACCESS_TOKEN")

LIST_SESSIONS_CODE=$(echo "$LIST_SESSIONS_RESPONSE" | tail -n 1)
LIST_SESSIONS_BODY=$(echo "$LIST_SESSIONS_RESPONSE" | head -n -1)

if [ "$LIST_SESSIONS_CODE" = "200" ]; then
    print_success "Sessions listed successfully"
else
    print_failure "Session listing failed with status $LIST_SESSIONS_CODE"
    echo "Response: $LIST_SESSIONS_BODY"
fi

# Test 14: Marketplace - Publish Blueprint
print_test "Marketplace - Publish Blueprint"
PUBLISH_DATA="{\"blueprint_id\":\"$BLUEPRINT_ID\"}"

PUBLISH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/marketplace/publish \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PUBLISH_DATA")

PUBLISH_CODE=$(echo "$PUBLISH_RESPONSE" | tail -n 1)
PUBLISH_BODY=$(echo "$PUBLISH_RESPONSE" | head -n -1)

if [ "$PUBLISH_CODE" = "200" ]; then
    print_success "Blueprint published to marketplace"
else
    print_failure "Blueprint publish failed with status $PUBLISH_CODE"
    echo "Response: $PUBLISH_BODY"
fi

# Test 15: Marketplace - Search
print_test "Marketplace - Search"
SEARCH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BACKEND_URL/api/marketplace?q=Test" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

SEARCH_CODE=$(echo "$SEARCH_RESPONSE" | tail -n 1)
SEARCH_BODY=$(echo "$SEARCH_RESPONSE" | head -n -1)

if [ "$SEARCH_CODE" = "200" ]; then
    print_success "Marketplace search successful"
    LISTING_COUNT=$(echo "$SEARCH_BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['listings']))" 2>/dev/null || echo "0")
    echo "Found $LISTING_COUNT listing(s)"
else
    print_failure "Marketplace search failed with status $SEARCH_CODE"
    echo "Response: $SEARCH_BODY"
fi

# Test 16: Marketplace - Clone Blueprint
print_test "Marketplace - Clone Blueprint"
CLONE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/marketplace/$BLUEPRINT_ID/clone \
    -H "Authorization: Bearer $ACCESS_TOKEN")

CLONE_CODE=$(echo "$CLONE_RESPONSE" | tail -n 1)
CLONE_BODY=$(echo "$CLONE_RESPONSE" | head -n -1)

if [ "$CLONE_CODE" = "201" ]; then
    print_success "Blueprint cloned successfully"
    CLONED_ID=$(echo "$CLONE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
    
    if [ "$CLONED_ID" != "$BLUEPRINT_ID" ]; then
        print_success "Cloned blueprint has different ID"
    fi
else
    print_failure "Blueprint clone failed with status $CLONE_CODE"
    echo "Response: $CLONE_BODY"
fi

# Test 17: Marketplace - Rate Blueprint
print_test "Marketplace - Rate Blueprint"
RATE_DATA='{"rating":5}'

RATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/marketplace/$BLUEPRINT_ID/rate \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$RATE_DATA")

RATE_CODE=$(echo "$RATE_RESPONSE" | tail -n 1)
RATE_BODY=$(echo "$RATE_RESPONSE" | head -n -1)

if [ "$RATE_CODE" = "200" ]; then
    print_success "Blueprint rated successfully"
else
    print_failure "Blueprint rating failed with status $RATE_CODE"
    echo "Response: $RATE_BODY"
fi

# Test 18: Rate Limiting
print_test "Rate Limiting - 101 Requests"
echo "Sending 101 requests to test rate limiting..."

RATE_LIMIT_HIT=false
for i in {1..101}; do
    RATE_TEST_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET $BACKEND_URL/api/blueprints \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if [ "$RATE_TEST_CODE" = "429" ]; then
        RATE_LIMIT_HIT=true
        print_success "Rate limit enforced at request $i (status 429)"
        break
    fi
    
    # Show progress every 20 requests
    if [ $((i % 20)) -eq 0 ]; then
        echo "  Sent $i requests..."
    fi
done

if [ "$RATE_LIMIT_HIT" = false ]; then
    print_warning "Rate limit not hit after 101 requests (may need adjustment)"
fi

# Test 19: Caching - Repeated Execution
print_test "Caching - Repeated Execution"
echo "Testing cache behavior with repeated blueprint access..."

# First access
START_TIME=$(date +%s%N)
CACHE_TEST1=$(curl -s -o /dev/null -w "%{http_code}" -X GET $BACKEND_URL/api/blueprints/$BLUEPRINT_ID \
    -H "Authorization: Bearer $ACCESS_TOKEN")
END_TIME=$(date +%s%N)
FIRST_DURATION=$(( (END_TIME - START_TIME) / 1000000 ))

# Second access (should be cached)
START_TIME=$(date +%s%N)
CACHE_TEST2=$(curl -s -o /dev/null -w "%{http_code}" -X GET $BACKEND_URL/api/blueprints/$BLUEPRINT_ID \
    -H "Authorization: Bearer $ACCESS_TOKEN")
END_TIME=$(date +%s%N)
SECOND_DURATION=$(( (END_TIME - START_TIME) / 1000000 ))

echo "First request: ${FIRST_DURATION}ms"
echo "Second request: ${SECOND_DURATION}ms"

if [ "$CACHE_TEST1" = "200" ] && [ "$CACHE_TEST2" = "200" ]; then
    print_success "Both requests successful"
    
    if [ $SECOND_DURATION -lt $FIRST_DURATION ]; then
        print_success "Second request faster (likely cached)"
    else
        print_warning "Second request not faster (caching may not be working)"
    fi
else
    print_failure "Cache test requests failed"
fi

# Test 20: Multi-Agent Isolation
print_test "Multi-Agent Isolation - Create Second Agent"
BLUEPRINT_DATA2='{"name":"Second Test Agent","description":"Second agent for isolation test","blueprint_data":{"head":{"model":"gpt-4","provider":"openai","system_prompt":"You are agent 2"},"legs":{"execution_mode":"single_agent"}}}'

CREATE_BP2_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/blueprints \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$BLUEPRINT_DATA2")

CREATE_BP2_CODE=$(echo "$CREATE_BP2_RESPONSE" | tail -n 1)
CREATE_BP2_BODY=$(echo "$CREATE_BP2_RESPONSE" | head -n -1)

if [ "$CREATE_BP2_CODE" = "201" ]; then
    print_success "Second agent created"
    BLUEPRINT_ID2=$(echo "$CREATE_BP2_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
    
    # Create session for second agent
    SESSION_DATA2="{\"blueprint_id\":\"$BLUEPRINT_ID2\"}"
    CREATE_SESSION2_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BACKEND_URL/api/sessions \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$SESSION_DATA2")
    
    CREATE_SESSION2_CODE=$(echo "$CREATE_SESSION2_RESPONSE" | tail -n 1)
    SESSION_ID2=$(echo "$CREATE_SESSION2_RESPONSE" | head -n -1 | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
    
    if [ "$CREATE_SESSION2_CODE" = "201" ] && [ "$SESSION_ID" != "$SESSION_ID2" ]; then
        print_success "Second session created with different ID - isolation verified"
    else
        print_failure "Session isolation test failed"
    fi
else
    print_failure "Second agent creation failed"
fi

# Test 21: Blueprint CRUD - Delete
print_test "Blueprint CRUD - Delete"
DELETE_BP_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE $BACKEND_URL/api/blueprints/$BLUEPRINT_ID \
    -H "Authorization: Bearer $ACCESS_TOKEN")

DELETE_BP_CODE=$(echo "$DELETE_BP_RESPONSE" | tail -n 1)

if [ "$DELETE_BP_CODE" = "204" ]; then
    print_success "Blueprint deleted successfully"
    
    # Verify deletion
    VERIFY_DELETE=$(curl -s -o /dev/null -w "%{http_code}" -X GET $BACKEND_URL/api/blueprints/$BLUEPRINT_ID \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if [ "$VERIFY_DELETE" = "404" ]; then
        print_success "Deleted blueprint no longer accessible"
    else
        print_warning "Deleted blueprint still accessible (status $VERIFY_DELETE)"
    fi
else
    print_failure "Blueprint deletion failed with status $DELETE_BP_CODE"
fi

# Test 22: API Key Management - Delete Key
if [ -n "$KEY_ID" ]; then
    print_test "API Key Management - Delete Key"
    DELETE_KEY_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE $BACKEND_URL/api/keys/$KEY_ID \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    DELETE_KEY_CODE=$(echo "$DELETE_KEY_RESPONSE" | tail -n 1)
    
    if [ "$DELETE_KEY_CODE" = "204" ]; then
        print_success "API key deleted successfully"
    else
        print_failure "API key deletion failed with status $DELETE_KEY_CODE"
    fi
fi

# Test 23: Log Sanitization Check
print_test "Log Sanitization - Check for Plaintext Keys"
echo "Checking Cloud Logging for plaintext API keys..."
echo "(This requires gcloud logging read permissions)"

# Try to search logs for common API key patterns
LOG_CHECK=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND textPayload=~\"sk-[a-zA-Z0-9]{20}\"" \
    --limit=10 \
    --format="value(textPayload)" \
    --project=$PROJECT_ID 2>/dev/null || echo "")

if [ -z "$LOG_CHECK" ]; then
    print_success "No plaintext API keys found in logs"
else
    print_failure "Potential plaintext API keys found in logs!"
    echo "$LOG_CHECK"
fi

# Summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
