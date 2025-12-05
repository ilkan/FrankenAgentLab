"""Tests for MCP tool integration."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from frankenagent.tools.mcp_tool import MCPTools
from frankenagent.tools.registry import ToolRegistry
from frankenagent.config.schema import ArmConfig


class TestMCPToolSchema:
    """Test MCP tool schema validation."""
    
    def test_valid_mcp_tool_config(self):
        """Test valid MCP tool configuration."""
        arm = ArmConfig(
            type="mcp_tool",
            config={
                "server_name": "aws-docs",
                "command": "uvx",
                "args": ["awslabs.aws-documentation-mcp-server@latest"],
                "env": {"FASTMCP_LOG_LEVEL": "ERROR"},
            }
        )
        assert arm.type == "mcp_tool"
        assert arm.config["server_name"] == "aws-docs"
        assert arm.config["command"] == "uvx"
    
    def test_mcp_tool_missing_command_raises_error(self):
        """Test that missing command raises validation error."""
        with pytest.raises(ValueError, match="requires.*command"):
            ArmConfig(
                type="mcp_tool",
                config={"server_name": "test-server"}
            )
    
    def test_mcp_tool_missing_server_name_raises_error(self):
        """Test that missing server_name raises validation error."""
        with pytest.raises(ValueError, match="requires.*server_name"):
            ArmConfig(
                type="mcp_tool",
                config={"command": "uvx"}
            )
    
    def test_mcp_tool_invalid_args_type_raises_error(self):
        """Test that non-list args raises validation error."""
        with pytest.raises(ValueError, match="args.*must be a list"):
            ArmConfig(
                type="mcp_tool",
                config={
                    "server_name": "test",
                    "command": "uvx",
                    "args": "not-a-list"
                }
            )
    
    def test_mcp_tool_invalid_env_type_raises_error(self):
        """Test that non-dict env raises validation error."""
        with pytest.raises(ValueError, match="env.*must be a dictionary"):
            ArmConfig(
                type="mcp_tool",
                config={
                    "server_name": "test",
                    "command": "uvx",
                    "env": "not-a-dict"
                }
            )


class TestMCPToolRegistry:
    """Test MCP tool creation via registry."""
    
    def test_mcp_tool_in_supported_tools(self):
        """Test that mcp_tool is in supported tools list."""
        registry = ToolRegistry()
        assert "mcp_tool" in registry.SUPPORTED_TOOLS
    
    def test_create_mcp_tool_success(self):
        """Test successful MCP tool creation."""
        registry = ToolRegistry()
        arm_config = {
            "type": "mcp_tool",
            "config": {
                "server_name": "test-server",
                "command": "echo",
                "args": ["hello"],
                "timeout": 60,
            }
        }
        
        tool = registry.create_tool(arm_config)
        
        assert isinstance(tool, MCPTools)
        assert tool.server_name == "test-server"
        assert tool.command == "echo"
        assert tool.args == ["hello"]
        assert tool.timeout == 60
    
    def test_create_mcp_tool_with_env(self):
        """Test MCP tool creation with environment variables."""
        registry = ToolRegistry()
        arm_config = {
            "type": "mcp_tool",
            "config": {
                "server_name": "aws-docs",
                "command": "uvx",
                "args": ["awslabs.aws-documentation-mcp-server@latest"],
                "env": {"FASTMCP_LOG_LEVEL": "ERROR"},
            }
        }
        
        tool = registry.create_tool(arm_config)
        
        assert tool.env == {"FASTMCP_LOG_LEVEL": "ERROR"}


class TestMCPToolsClass:
    """Test MCPTools class functionality."""
    
    def test_mcp_tools_initialization(self):
        """Test MCPTools initialization."""
        tool = MCPTools(
            server_name="test",
            command="echo",
            args=["test"],
            env={"KEY": "value"},
            timeout=45,
        )
        
        assert tool.server_name == "test"
        assert tool.command == "echo"
        assert tool.args == ["test"]
        assert tool.env == {"KEY": "value"}
        assert tool.timeout == 45
        assert tool.name == "MCP_test"
    
    def test_mcp_tools_default_values(self):
        """Test MCPTools default values."""
        tool = MCPTools(
            server_name="test",
            command="echo",
        )
        
        assert tool.args == []
        assert tool.env == {}
        assert tool.timeout == 30
    
    def test_get_server_params(self):
        """Test server parameters generation."""
        tool = MCPTools(
            server_name="test",
            command="uvx",
            args=["package@latest"],
            env={"LOG_LEVEL": "DEBUG"},
        )
        
        params = tool._get_server_params()
        
        assert params.command == "uvx"
        assert params.args == ["package@latest"]
        assert params.env == {"LOG_LEVEL": "DEBUG"}
    
    def test_mcp_tools_with_api_token(self):
        """Test MCPTools with API token."""
        tool = MCPTools(
            server_name="test",
            command="echo",
            api_token="my-secret-token",
        )
        
        assert tool.api_token == "my-secret-token"
        assert "MCP_API_TOKEN" in tool.env
        assert tool.env["MCP_API_TOKEN"] == "my-secret-token"
    
    def test_mcp_tools_with_custom_token_env_var(self):
        """Test MCPTools with custom API token env var name."""
        tool = MCPTools(
            server_name="test",
            command="echo",
            api_token="my-token",
            api_token_env_var="CUSTOM_TOKEN",
        )
        
        assert tool.api_token_env_var == "CUSTOM_TOKEN"
        assert "CUSTOM_TOKEN" in tool.env
        assert tool.env["CUSTOM_TOKEN"] == "my-token"
    
    def test_mcp_tools_token_merged_with_env(self):
        """Test that API token is merged with existing env vars."""
        tool = MCPTools(
            server_name="test",
            command="echo",
            env={"EXISTING_VAR": "value"},
            api_token="token123",
        )
        
        assert tool.env["EXISTING_VAR"] == "value"
        assert tool.env["MCP_API_TOKEN"] == "token123"


class TestMCPToolRegistryWithToken:
    """Test MCP tool creation with API token via registry."""
    
    def test_create_mcp_tool_with_api_token(self):
        """Test MCP tool creation with API token."""
        registry = ToolRegistry()
        arm_config = {
            "type": "mcp_tool",
            "config": {
                "server_name": "test-server",
                "command": "echo",
                "api_token": "secret-token-123",
            }
        }
        
        tool = registry.create_tool(arm_config)
        
        assert isinstance(tool, MCPTools)
        assert tool.api_token == "secret-token-123"
        assert tool.env["MCP_API_TOKEN"] == "secret-token-123"
    
    def test_create_mcp_tool_with_custom_token_env_var(self):
        """Test MCP tool creation with custom token env var."""
        registry = ToolRegistry()
        arm_config = {
            "type": "mcp_tool",
            "config": {
                "server_name": "test-server",
                "command": "echo",
                "api_token": "my-token",
                "api_token_env_var": "MY_CUSTOM_TOKEN",
            }
        }
        
        tool = registry.create_tool(arm_config)
        
        assert tool.api_token_env_var == "MY_CUSTOM_TOKEN"
        assert tool.env["MY_CUSTOM_TOKEN"] == "my-token"
