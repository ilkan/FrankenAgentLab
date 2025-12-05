"""Tests for HTTP tool implementation."""

import pytest
from frankenagent.tools.http_tool import HTTPTools


def test_http_tool_initialization():
    """Test HTTP tool can be initialized with config."""
    tool = HTTPTools(
        name="Test API",
        description="Test HTTP tool",
        base_url="https://jsonplaceholder.typicode.com",
        default_headers={"Content-Type": "application/json"},
        timeout=30,
    )
    
    assert tool.name == "Test API"
    assert tool.description == "Test HTTP tool"
    assert tool.base_url == "https://jsonplaceholder.typicode.com"
    assert tool.default_headers == {"Content-Type": "application/json"}
    assert tool.timeout == 30


def test_http_tool_get_request():
    """Test HTTP GET request to public API."""
    tool = HTTPTools(
        name="JSONPlaceholder",
        base_url="https://jsonplaceholder.typicode.com",
        timeout=10,
    )
    
    # Make GET request to fetch a post
    result = tool.get("/posts/1")
    
    # Should return JSON response
    assert "userId" in result
    assert "id" in result
    assert "title" in result


def test_http_tool_post_request():
    """Test HTTP POST request to public API."""
    tool = HTTPTools(
        name="JSONPlaceholder",
        base_url="https://jsonplaceholder.typicode.com",
        timeout=10,
    )
    
    # Make POST request to create a post
    result = tool.post(
        "/posts",
        json={
            "title": "Test Post",
            "body": "This is a test",
            "userId": 1,
        },
    )
    
    # Should return created resource
    assert "id" in result


def test_http_tool_url_building():
    """Test URL building with base_url."""
    tool = HTTPTools(base_url="https://api.example.com")
    
    # Test path with leading slash
    assert tool._build_url("/users") == "https://api.example.com/users"
    
    # Test path without leading slash
    assert tool._build_url("users") == "https://api.example.com/users"
    
    # Test full URL (should not prepend base_url)
    assert tool._build_url("https://other.com/api") == "https://other.com/api"


def test_http_tool_header_merging():
    """Test default headers are merged with request headers."""
    tool = HTTPTools(
        default_headers={
            "Authorization": "Bearer token",
            "User-Agent": "FrankenAgent",
        }
    )
    
    # Merge with request-specific headers
    merged = tool._merge_headers({"Content-Type": "application/json"})
    
    assert merged["Authorization"] == "Bearer token"
    assert merged["User-Agent"] == "FrankenAgent"
    assert merged["Content-Type"] == "application/json"
    
    # Request headers should override defaults
    merged = tool._merge_headers({"User-Agent": "Custom"})
    assert merged["User-Agent"] == "Custom"


def test_http_tool_without_base_url():
    """Test HTTP tool works without base_url."""
    tool = HTTPTools(name="Generic HTTP")
    
    # Should work with full URLs
    result = tool.get("https://jsonplaceholder.typicode.com/posts/1")
    assert "userId" in result
