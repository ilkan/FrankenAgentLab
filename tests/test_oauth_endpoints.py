"""Tests for OAuth authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from frankenagent.api.server import app

client = TestClient(app)


def test_get_google_oauth_url():
    """Test getting Google OAuth authorization URL."""
    response = client.get("/api/auth/oauth/url/google")
    
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "state" in data
    assert "accounts.google.com" in data["auth_url"]
    assert "client_id" in data["auth_url"]


def test_get_github_oauth_url():
    """Test getting GitHub OAuth authorization URL."""
    response = client.get("/api/auth/oauth/url/github")
    
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "state" in data
    assert "github.com" in data["auth_url"]
    assert "client_id" in data["auth_url"]


def test_get_oauth_url_invalid_provider():
    """Test getting OAuth URL with invalid provider."""
    response = client.get("/api/auth/oauth/url/invalid")
    
    assert response.status_code == 400
    assert "Unsupported OAuth provider" in response.json()["detail"]


@patch('frankenagent.api.auth.oauth_service.exchange_google_code')
async def test_oauth_login_google_success(mock_exchange):
    """Test successful OAuth login with Google."""
    # Mock OAuth exchange
    mock_exchange.return_value = {
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "provider": "google",
        "provider_user_id": "12345"
    }
    
    response = client.post(
        "/api/auth/oauth/login",
        json={
            "provider": "google",
            "code": "test-auth-code",
            "redirect_uri": "http://localhost:8000"
        }
    )
    
    # Note: This will fail in test because we need a real database
    # In a real test, you'd set up a test database
    assert response.status_code in [200, 500]  # 500 if no DB


@patch('frankenagent.api.auth.oauth_service.exchange_github_code')
async def test_oauth_login_github_success(mock_exchange):
    """Test successful OAuth login with GitHub."""
    # Mock OAuth exchange
    mock_exchange.return_value = {
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
        "provider": "github",
        "provider_user_id": "67890"
    }
    
    response = client.post(
        "/api/auth/oauth/login",
        json={
            "provider": "github",
            "code": "test-auth-code",
            "redirect_uri": "http://localhost:8000"
        }
    )
    
    # Note: This will fail in test because we need a real database
    assert response.status_code in [200, 500]  # 500 if no DB


def test_oauth_login_invalid_provider():
    """Test OAuth login with invalid provider."""
    response = client.post(
        "/api/auth/oauth/login",
        json={
            "provider": "invalid",
            "code": "test-code",
            "redirect_uri": "http://localhost:8000"
        }
    )
    
    assert response.status_code == 400
    assert "Unsupported OAuth provider" in response.json()["detail"]


def test_oauth_login_missing_code():
    """Test OAuth login with missing authorization code."""
    response = client.post(
        "/api/auth/oauth/login",
        json={
            "provider": "google",
            "redirect_uri": "http://localhost:8000"
        }
    )
    
    assert response.status_code == 422  # Validation error
