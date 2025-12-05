"""
Integration tests for Google OAuth service.

These tests verify the OAuth service logic without requiring actual Google authentication.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from frankenagent.auth.oauth_service import OAuthService
import os


@pytest.fixture
def oauth_service():
    """Create OAuth service with test credentials"""
    with patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
        "OAUTH_REDIRECT_URI": "http://localhost:8000"
    }):
        return OAuthService()


def test_oauth_service_initialization(oauth_service):
    """Test OAuth service initializes with environment variables"""
    assert oauth_service.google_client_id == "test-client-id.apps.googleusercontent.com"
    assert oauth_service.google_client_secret == "test-client-secret"
    assert oauth_service.redirect_uri == "http://localhost:8000"


def test_get_google_auth_url(oauth_service):
    """Test Google OAuth authorization URL generation"""
    state = "test-state-token"
    auth_url = oauth_service.get_google_auth_url(state)
    
    # Verify URL structure
    assert auth_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=test-client-id.apps.googleusercontent.com" in auth_url
    assert "redirect_uri=http://localhost:8000" in auth_url
    assert "response_type=code" in auth_url
    assert "scope=openid email profile" in auth_url.replace("%20", " ")
    assert f"state={state}" in auth_url
    assert "access_type=online" in auth_url


def test_get_google_auth_url_without_credentials():
    """Test Google OAuth URL generation fails without credentials"""
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": ""}, clear=True):
        service = OAuthService()
        
        with pytest.raises(ValueError, match="Google OAuth not configured"):
            service.get_google_auth_url("test-state")


@pytest.mark.asyncio
async def test_exchange_google_code_success(oauth_service):
    """Test successful Google OAuth code exchange"""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {
        "access_token": "test-access-token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    mock_user_response = Mock()
    mock_user_response.status_code = 200
    mock_user_response.json.return_value = {
        "id": "123456789",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.post.return_value = mock_token_response
        mock_instance.get.return_value = mock_user_response
        mock_client.return_value = mock_instance
        
        result = await oauth_service.exchange_google_code(
            code="test-auth-code",
            redirect_uri="http://localhost:8000"
        )
        
        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        assert result["picture"] == "https://example.com/photo.jpg"
        assert result["provider"] == "google"
        assert result["provider_user_id"] == "123456789"


@pytest.mark.asyncio
async def test_exchange_google_code_token_failure(oauth_service):
    """Test Google OAuth code exchange with token request failure"""
    mock_token_response = Mock()
    mock_token_response.status_code = 400
    mock_token_response.text = "Invalid authorization code"
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.post.return_value = mock_token_response
        mock_client.return_value = mock_instance
        
        result = await oauth_service.exchange_google_code(
            code="invalid-code",
            redirect_uri="http://localhost:8000"
        )
        
        assert result is None


@pytest.mark.asyncio
async def test_exchange_google_code_user_info_failure(oauth_service):
    """Test Google OAuth code exchange with user info request failure"""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {
        "access_token": "test-access-token"
    }
    
    mock_user_response = Mock()
    mock_user_response.status_code = 401
    mock_user_response.text = "Invalid access token"
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.post.return_value = mock_token_response
        mock_instance.get.return_value = mock_user_response
        mock_client.return_value = mock_instance
        
        result = await oauth_service.exchange_google_code(
            code="test-code",
            redirect_uri="http://localhost:8000"
        )
        
        assert result is None


@pytest.mark.asyncio
async def test_exchange_google_code_no_access_token(oauth_service):
    """Test Google OAuth code exchange with missing access token"""
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {
        "token_type": "Bearer"
        # Missing access_token
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.post.return_value = mock_token_response
        mock_client.return_value = mock_instance
        
        result = await oauth_service.exchange_google_code(
            code="test-code",
            redirect_uri="http://localhost:8000"
        )
        
        assert result is None


@pytest.mark.asyncio
async def test_exchange_google_code_without_credentials():
    """Test Google OAuth code exchange fails without credentials"""
    with patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "",
        "GOOGLE_CLIENT_SECRET": ""
    }, clear=True):
        service = OAuthService()
        
        result = await service.exchange_google_code(
            code="test-code",
            redirect_uri="http://localhost:8000"
        )
        
        assert result is None


@pytest.mark.asyncio
async def test_exchange_google_code_network_error(oauth_service):
    """Test Google OAuth code exchange with network error"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.post.side_effect = Exception("Network error")
        mock_client.return_value = mock_instance
        
        result = await oauth_service.exchange_google_code(
            code="test-code",
            redirect_uri="http://localhost:8000"
        )
        
        assert result is None


def test_oauth_service_with_missing_env_vars():
    """Test OAuth service handles missing environment variables"""
    with patch.dict(os.environ, {}, clear=True):
        service = OAuthService()
        
        assert service.google_client_id is None
        assert service.google_client_secret is None
        assert service.redirect_uri == "http://localhost:8000/api/auth/callback"


@pytest.mark.asyncio
async def test_exchange_google_code_with_custom_redirect_uri(oauth_service):
    """Test Google OAuth code exchange with custom redirect URI"""
    custom_redirect = "https://example.com/callback"
    
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {
        "access_token": "test-access-token"
    }
    
    mock_user_response = Mock()
    mock_user_response.status_code = 200
    mock_user_response.json.return_value = {
        "id": "123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.post.return_value = mock_token_response
        mock_instance.get.return_value = mock_user_response
        mock_client.return_value = mock_instance
        
        result = await oauth_service.exchange_google_code(
            code="test-code",
            redirect_uri=custom_redirect
        )
        
        assert result is not None
        # Verify the custom redirect URI was used in the token request
        mock_instance.post.assert_called_once()
        call_args = mock_instance.post.call_args
        assert call_args[1]["data"]["redirect_uri"] == custom_redirect
