"""
Manual test script for Google OAuth authentication.

This script helps you test the Google OAuth flow interactively.
Run this script and follow the instructions to verify OAuth is working.
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"


async def test_oauth_configuration():
    """Test 1: Verify OAuth credentials are configured"""
    print("\n" + "="*60)
    print("TEST 1: OAuth Configuration Check")
    print("="*60)
    
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    oauth_redirect_uri = os.getenv("OAUTH_REDIRECT_URI")
    
    print(f"✓ GOOGLE_CLIENT_ID: {google_client_id[:20]}..." if google_client_id else "✗ GOOGLE_CLIENT_ID: Not set")
    print(f"✓ GOOGLE_CLIENT_SECRET: {google_client_secret[:10]}..." if google_client_secret else "✗ GOOGLE_CLIENT_SECRET: Not set")
    print(f"✓ OAUTH_REDIRECT_URI: {oauth_redirect_uri}" if oauth_redirect_uri else "✗ OAUTH_REDIRECT_URI: Not set")
    
    if not all([google_client_id, google_client_secret, oauth_redirect_uri]):
        print("\n❌ OAuth credentials not properly configured!")
        print("Please check your .env file.")
        return False
    
    print("\n✅ OAuth credentials are configured")
    return True


async def test_oauth_url_endpoint():
    """Test 2: Get OAuth authorization URL"""
    print("\n" + "="*60)
    print("TEST 2: OAuth Authorization URL")
    print("="*60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/auth/oauth/url/google")
            
            if response.status_code == 200:
                data = response.json()
                auth_url = data.get("auth_url")
                state = data.get("state")
                
                print(f"✓ Status Code: {response.status_code}")
                print(f"✓ State Token: {state[:20]}...")
                print(f"✓ Auth URL: {auth_url[:80]}...")
                
                print("\n✅ OAuth URL endpoint is working")
                print("\n" + "-"*60)
                print("MANUAL TEST REQUIRED:")
                print("-"*60)
                print("1. Copy this URL and open it in your browser:")
                print(f"\n{auth_url}\n")
                print("2. Log in with your Google account")
                print("3. After authorization, you'll be redirected to:")
                print(f"   {os.getenv('OAUTH_REDIRECT_URI')}?code=...&state=...")
                print("4. Copy the 'code' parameter from the URL")
                print("5. Run the next test with that code")
                print("-"*60)
                
                return True, state
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None


async def test_oauth_code_exchange(code: str, state: str):
    """Test 3: Exchange OAuth code for access token"""
    print("\n" + "="*60)
    print("TEST 3: OAuth Code Exchange")
    print("="*60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/oauth/login",
                json={
                    "provider": "google",
                    "code": code,
                    "redirect_uri": os.getenv("OAUTH_REDIRECT_URI")
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                token_type = data.get("token_type")
                expires_in = data.get("expires_in")
                
                print(f"✓ Status Code: {response.status_code}")
                print(f"✓ Token Type: {token_type}")
                print(f"✓ Expires In: {expires_in} seconds")
                print(f"✓ Access Token: {access_token[:20]}...")
                
                print("\n✅ OAuth code exchange successful!")
                return True, access_token
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None


async def test_authenticated_request(access_token: str):
    """Test 4: Use access token to get user info"""
    print("\n" + "="*60)
    print("TEST 4: Authenticated Request")
    print("="*60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                print(f"✓ Status Code: {response.status_code}")
                print(f"✓ User ID: {user_data.get('id')}")
                print(f"✓ Email: {user_data.get('email')}")
                print(f"✓ Full Name: {user_data.get('full_name')}")
                print(f"✓ Token Quota: {user_data.get('token_quota')}")
                print(f"✓ Token Used: {user_data.get('token_used')}")
                
                print("\n✅ Authenticated request successful!")
                return True
            else:
                print(f"❌ Failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_server_health():
    """Test 0: Check if server is running"""
    print("\n" + "="*60)
    print("TEST 0: Server Health Check")
    print("="*60)
    
    try:
        with httpx.Client() as client:
            response = client.get(f"{BASE_URL}/", timeout=5.0)
            
            if response.status_code == 200:
                print(f"✓ Server is running at {BASE_URL}")
                print(f"✓ Status: {response.json()}")
                print("\n✅ Server is healthy")
                return True
            else:
                print(f"❌ Server returned status code: {response.status_code}")
                return False
                
    except httpx.ConnectError as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("\nPlease start the server first:")
        print("  poetry run uvicorn frankenagent.api.server:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


async def run_automated_tests():
    """Run automated tests that don't require user interaction"""
    print("\n" + "🧪 "*20)
    print("GOOGLE OAUTH AUTOMATED TESTS")
    print("🧪 "*20)
    
    # Test 0: Server health (synchronous)
    if not test_server_health():
        return
    
    # Test 1: Configuration
    if not await test_oauth_configuration():
        return
    
    # Test 2: OAuth URL
    success, state = await test_oauth_url_endpoint()
    if not success:
        return
    
    print("\n" + "="*60)
    print("AUTOMATED TESTS COMPLETE")
    print("="*60)
    print("\nTo complete the OAuth flow test:")
    print("1. Open the authorization URL shown above in your browser")
    print("2. Log in with Google and authorize the app")
    print("3. Copy the 'code' parameter from the redirect URL")
    print("4. Run: python tests/test_google_oauth_manual.py --code YOUR_CODE")


async def run_manual_test(code: str):
    """Run manual test with authorization code"""
    print("\n" + "🧪 "*20)
    print("GOOGLE OAUTH MANUAL TEST")
    print("🧪 "*20)
    
    # Get a fresh state token
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/auth/oauth/url/google")
        state = response.json().get("state")
    
    # Test 3: Code exchange
    success, access_token = await test_oauth_code_exchange(code, state)
    if not success:
        return
    
    # Test 4: Authenticated request
    await test_authenticated_request(access_token)
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\n✅ Google OAuth is working correctly!")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--code":
        if len(sys.argv) < 3:
            print("Usage: python tests/test_google_oauth_manual.py --code YOUR_CODE")
            sys.exit(1)
        
        code = sys.argv[2]
        asyncio.run(run_manual_test(code))
    else:
        asyncio.run(run_automated_tests())


if __name__ == "__main__":
    main()
