"""MCP testing and tool discovery API endpoints."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from frankenagent.tools.mcp_tool import MCPTools

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp", tags=["MCP"])


class MCPTestConnectionRequest(BaseModel):
    """Request to test MCP server connection."""
    server_url: str
    transport_type: str = "sse"
    api_token: Optional[str] = None
    auth_header: str = "Authorization"
    timeout: int = 10


class MCPToolInfo(BaseModel):
    """Information about an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any] = {}


class MCPTestConnectionResponse(BaseModel):
    """Response from MCP connection test."""
    success: bool
    message: str
    tools: List[MCPToolInfo] = []
    error: Optional[str] = None


@router.post("/test-connection", response_model=MCPTestConnectionResponse)
async def test_mcp_connection(request: MCPTestConnectionRequest):
    """Test connection to an MCP server and fetch available tools.
    
    This endpoint attempts to connect to an MCP server using the provided
    configuration and returns the list of available tools if successful.
    
    Args:
        request: MCPTestConnectionRequest with server URL and configuration
        
    Returns:
        MCPTestConnectionResponse with connection status and available tools
        
    Raises:
        HTTPException: 400 for invalid configuration, 500 for connection errors
    """
    logger.info(f"Testing MCP connection to {request.server_url}")
    
    try:
        # For SSE/HTTP transport, we'll use Agno's MCPTools
        if request.transport_type in ["sse", "http", "streamable-http"]:
            # Create MCPTools instance for testing
            mcp_tool = MCPTools(
                server_name="test_server",
                transport="http",  # Use http for SSE/streamable-http
                server_url=request.server_url,
                api_token=request.api_token,
                auth_header=request.auth_header,
                timeout=request.timeout,
            )
            
            try:
                # Try to connect and list tools using Agno's async methods
                # Since we're in FastAPI async context, we can use asyncio
                from agno.tools.mcp import MCPTools as AgnoMCPTools
                
                # Map transport types to Agno's expected values
                # According to Agno docs: "sse", "streamable-http", or "stdio"
                transport_map = {
                    "sse": "sse",
                    "http": "streamable-http",
                    "streamable-http": "streamable-http",
                }
                agno_transport = transport_map.get(request.transport_type, "streamable-http")
                
                logger.info(f"Using Agno transport: {agno_transport} for {request.transport_type}")
                
                # Create Agno MCP client
                agno_mcp = AgnoMCPTools(
                    url=request.server_url,
                    transport=agno_transport,
                    timeout_seconds=request.timeout,
                )
                
                # Connect to the server
                await agno_mcp.connect()
                
                # Get available tools
                tools_list = []
                if hasattr(agno_mcp, 'functions') and agno_mcp.functions:
                    for func in agno_mcp.functions:
                        tools_list.append(MCPToolInfo(
                            name=func.name if hasattr(func, 'name') else str(func),
                            description=func.description if hasattr(func, 'description') else "",
                            input_schema=func.parameters if hasattr(func, 'parameters') else {},
                        ))
                
                # Close connection
                await agno_mcp.close()
                
                logger.info(f"Successfully connected to MCP server. Found {len(tools_list)} tools.")
                
                return MCPTestConnectionResponse(
                    success=True,
                    message=f"Connected successfully. Found {len(tools_list)} tools.",
                    tools=tools_list,
                )
                
            except Exception as e:
                logger.error(f"Failed to connect to MCP server: {e}")
                return MCPTestConnectionResponse(
                    success=False,
                    message="Connection failed",
                    error=str(e),
                    tools=[],
                )
        else:
            # Stdio transport not supported for browser-based testing
            return MCPTestConnectionResponse(
                success=False,
                message="Stdio transport not supported for connection testing",
                error="Use SSE or HTTP transport for browser-based testing",
                tools=[],
            )
            
    except Exception as e:
        logger.error(f"MCP connection test error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}"
        )
