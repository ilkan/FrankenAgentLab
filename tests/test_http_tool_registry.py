"""Tests for HTTP tool integration with ToolRegistry."""

import pytest
from frankenagent.tools.registry import ToolRegistry
from frankenagent.tools.http_tool import HTTPTools


def test_registry_creates_http_tool():
    """Test that registry can create HTTP tool from config."""
    registry = ToolRegistry()
    
    arm_config = {
        "type": "http_tool",
        "config": {
            "name": "GitHub API",
            "description": "Access GitHub API",
            "base_url": "https://api.github.com",
            "default_headers": {
                "Accept": "application/vnd.github.v3+json",
            },
            "timeout": 30,
        },
    }
    
    tool = registry.create_tool(arm_config)
    
    assert isinstance(tool, HTTPTools)
    assert tool.name == "GitHub API"
    assert tool.description == "Access GitHub API"
    assert tool.base_url == "https://api.github.com"
    assert tool.timeout == 30


def test_registry_http_tool_with_defaults():
    """Test HTTP tool creation with minimal config."""
    registry = ToolRegistry()
    
    arm_config = {
        "type": "http_tool",
        "config": {},
    }
    
    tool = registry.create_tool(arm_config)
    
    assert isinstance(tool, HTTPTools)
    assert tool.name == "HTTP Request"
    assert tool.description == "Make HTTP requests to external APIs"
    assert tool.timeout == 30


def test_registry_http_tool_without_base_url():
    """Test HTTP tool can be created without base_url."""
    registry = ToolRegistry()
    
    arm_config = {
        "type": "http_tool",
        "config": {
            "name": "Generic HTTP Client",
            "timeout": 60,
        },
    }
    
    tool = registry.create_tool(arm_config)
    
    assert isinstance(tool, HTTPTools)
    assert tool.base_url is None
    assert tool.timeout == 60
