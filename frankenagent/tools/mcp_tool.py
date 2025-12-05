"""MCP (Model Context Protocol) tool for Agno agents.

This module provides an MCP client tool that connects to MCP servers
and exposes their tools to Agno agents. MCP servers can be any external
tool provider that implements the Model Context Protocol.

Supports two transport types:
- stdio: Command-based (e.g., uvx, npx)
- http/sse: HTTP Server-Sent Events (e.g., https://example.com/sse/)
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Literal
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from agno.tools import Toolkit
from agno.utils.log import logger


class MCPTools(Toolkit):
    """MCP client tool for connecting to MCP servers.
    
    This tool allows Agno agents to use tools provided by MCP servers.
    Supports both stdio (command-based) and HTTP/SSE transports.
    
    Attributes:
        server_name: Name identifier for this MCP server
        transport: Transport type ("stdio" or "http")
        command: Command to start the MCP server (stdio only)
        args: Arguments to pass to the command (stdio only)
        env: Environment variables for the server process (stdio only)
        server_url: HTTP/SSE server URL (http only)
        allowed_tools: List of allowed tool names (optional)
        require_approval: Approval requirement ("always", "never", "once")
    
    Examples:
        Stdio transport:
        >>> mcp_tool = MCPTools(
        ...     server_name="aws-docs",
        ...     transport="stdio",
        ...     command="uvx",
        ...     args=["awslabs.aws-documentation-mcp-server@latest"]
        ... )
        
        HTTP transport:
        >>> mcp_tool = MCPTools(
        ...     server_name="cats",
        ...     transport="http",
        ...     server_url="https://example.com/sse/",
        ...     allowed_tools=["search", "fetch"]
        ... )
    """
    
    def __init__(
        self,
        server_name: str,
        transport: Literal["stdio", "http"] = "stdio",
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        server_url: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        require_approval: Literal["always", "never", "once"] = "never",
        api_token: Optional[str] = None,
        api_token_env_var: str = "MCP_API_TOKEN",
        auth_header: str = "Authorization",
        timeout: int = 30,
    ):
        """Initialize MCP tool.
        
        Args:
            server_name: Name identifier for this MCP server
            transport: Transport type ("stdio" or "http")
            command: Command to start the MCP server (stdio only)
            args: Arguments to pass to the command (stdio only)
            env: Environment variables for the server process (stdio only)
            server_url: HTTP/SSE server URL (http only)
            allowed_tools: List of allowed tool names (optional filter)
            require_approval: Approval requirement ("always", "never", "once")
            api_token: API token for MCP servers that require authentication
            api_token_env_var: Environment variable name to pass the token as
            timeout: Timeout for MCP operations in seconds
        """
        super().__init__(name=f"MCP_{server_name}")
        
        self.server_name = server_name
        self.transport = transport
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.server_url = server_url
        self.allowed_tools = allowed_tools
        self.require_approval = require_approval
        self.api_token = api_token
        self.api_token_env_var = api_token_env_var
        self.auth_header = auth_header
        self.timeout = timeout
        
        # Validate configuration
        if self.transport == "stdio" and not self.command:
            raise ValueError("command is required for stdio transport")
        if self.transport == "http" and not self.server_url:
            raise ValueError("server_url is required for http transport")
        
        # For HTTP transport, we store the config for OpenAI to use directly
        # OpenAI handles the MCP connection natively
        self._http_mcp_config = None
        if self.transport == "http":
            self._http_mcp_config = {
                "type": "mcp",
                "server_label": self.server_name,
                "server_url": self.server_url,
                "allowed_tools": self.allowed_tools or [],
                "require_approval": self.require_approval,
            }
            
            # Add authentication if provided
            if self.api_token:
                # Format token with Bearer prefix if not already present
                token = self.api_token if self.api_token.startswith('Bearer ') else f'Bearer {self.api_token}'
                self._http_mcp_config["headers"] = {
                    self.auth_header: token
                }
        
        # If api_token is provided, add it to env
        if self.api_token:
            self.env[self.api_token_env_var] = self.api_token
        
        # Cache for available tools from the server
        self._available_tools: List[Dict[str, Any]] = []
        self._tools_loaded = False
        
        # Register the main call_tool method
        self.register(self.call_tool)
        self.register(self.list_tools)
    
    def get_mcp_config(self) -> Optional[Dict[str, Any]]:
        """Get MCP configuration for OpenAI native MCP support.
        
        Returns:
            MCP configuration dict for HTTP transport, None for stdio transport.
            This config can be passed directly to OpenAI's API.
        """
        return self._http_mcp_config
    
    def _get_server_params(self) -> StdioServerParameters:
        """Get stdio server parameters for MCP connection."""
        return StdioServerParameters(
            command=self.command,
            args=self.args,
            env=self.env if self.env else None,
        )
    
    @asynccontextmanager
    async def _get_session(self):
        """Create an MCP client session context manager."""
        server_params = self._get_server_params()
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    
    async def _fetch_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from the MCP server."""
        try:
            async with self._get_session() as session:
                result = await session.list_tools()
                tools = []
                for tool in result.tools:
                    tool_info = {
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                    }
                    # Filter by allowed_tools if specified
                    if not self.allowed_tools or tool.name in self.allowed_tools:
                        tools.append(tool_info)
                return tools
        except Exception as e:
            logger.error(f"Failed to fetch tools from MCP server {self.server_name}: {e}")
            return []
    
    async def _call_tool_async(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server asynchronously."""
        try:
            async with self._get_session() as session:
                result = await session.call_tool(tool_name, arguments)
                
                # Extract content from result
                if hasattr(result, 'content') and result.content:
                    contents = []
                    for content in result.content:
                        if hasattr(content, 'text'):
                            contents.append(content.text)
                        elif hasattr(content, 'data'):
                            contents.append(str(content.data))
                    return "\n".join(contents) if contents else "No content returned"
                
                return str(result)
                
        except Exception as e:
            error_msg = f"MCP tool call failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def list_tools(self) -> str:
        """List all available tools from the MCP server.
        
        Returns:
            JSON string containing list of available tools with their
            names, descriptions, and input schemas.
        
        Example:
            >>> tools = mcp_tool.list_tools()
            >>> print(tools)  # JSON list of tools
        """
        # For HTTP transport, return the allowed tools from config
        if self.transport == "http":
            tools = []
            if self.allowed_tools:
                for tool_name in self.allowed_tools:
                    tools.append({
                        "name": tool_name,
                        "description": f"MCP tool: {tool_name}",
                        "input_schema": {},
                    })
            
            return json.dumps({
                "server": self.server_name,
                "transport": "http",
                "server_url": self.server_url,
                "tools": tools,
            }, indent=2)
        
        # For stdio transport, fetch tools from the server
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._fetch_tools())
                    tools = future.result(timeout=self.timeout)
            else:
                tools = asyncio.run(self._fetch_tools())
            
            self._available_tools = tools
            self._tools_loaded = True
            
            return json.dumps({
                "server": self.server_name,
                "transport": "stdio",
                "tools": tools,
            }, indent=2)
            
        except Exception as e:
            error_msg = f"Failed to list MCP tools: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def call_tool(
        self,
        tool_name: str,
        arguments: Optional[str] = None,
    ) -> str:
        """Call a specific tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call on the MCP server
            arguments: JSON string of arguments to pass to the tool
        
        Returns:
            Result from the MCP tool as a string
        
        Example:
            >>> result = mcp_tool.call_tool(
            ...     "search_documentation",
            ...     '{"search_phrase": "S3 bucket"}'
            ... )
        """
        # For HTTP transport, OpenAI handles the tool calling natively
        # This method shouldn't be called directly for HTTP transport
        if self.transport == "http":
            return json.dumps({
                "note": "HTTP MCP tools are handled natively by OpenAI",
                "server": self.server_name,
                "tool": tool_name,
                "config": self._http_mcp_config
            })
        
        # For stdio transport, execute the tool call
        try:
            # Parse arguments if provided as JSON string
            args_dict = {}
            if arguments:
                if isinstance(arguments, str):
                    args_dict = json.loads(arguments)
                elif isinstance(arguments, dict):
                    args_dict = arguments
            
            logger.info(f"MCP call: {self.server_name}.{tool_name}")
            
            # Run async call
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self._call_tool_async(tool_name, args_dict)
                    )
                    result = future.result(timeout=self.timeout)
            else:
                result = asyncio.run(self._call_tool_async(tool_name, args_dict))
            
            return result
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON arguments: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"MCP tool call failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
