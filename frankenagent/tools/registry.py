"""Tool registry for mapping tool types to Agno tool implementations."""

import os
import logging
from typing import Any, Dict
from dotenv import load_dotenv
from frankenagent.exceptions import ToolError, ConfigurationError

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry mapping tool types to Agno tool classes.
    
    The registry provides a centralized way to instantiate tools from
    blueprint configurations, handling API key injection and configuration
    validation.
    """
    
    # Supported tool types
    SUPPORTED_TOOLS = ["tavily_search", "http_tool", "mcp_tool"]
    
    # Map tool types to Agno tool class paths
    TOOL_MAP: Dict[str, str] = {
        "tavily_search": "agno.tools.tavily.TavilyTools",
        "python_eval": "agno.tools.python.PythonTools",
        "file_tools": "agno.tools.file.FileTools",
        "duckduckgo_search": "agno.tools.duckduckgo.DuckDuckGoTools",
    }
    
    def create_tool(self, arm_config: Dict[str, Any]) -> Any:
        """Create an Agno tool from arm configuration.
        
        This is the main entry point for creating tools from blueprint arm configs.
        Maps tool types to specific creation methods.
        
        Args:
            arm_config: Tool config from blueprint arms section
                Example: {"type": "tavily_search", "config": {...}}
        
        Returns:
            Agno tool instance ready for use with agents
            
        Raises:
            UnknownToolTypeError: If tool type is not supported
            ToolConfigurationError: If tool configuration is invalid
            
        Example:
            >>> registry = ToolRegistry()
            >>> arm = {"type": "tavily_search", "config": {"max_results": 5}}
            >>> tool = registry.create_tool(arm)
        """
        tool_type = arm_config.get("type")
        
        if not tool_type:
            raise ToolError("Tool configuration missing 'type' field")
        
        if tool_type not in self.SUPPORTED_TOOLS:
            raise ToolError(
                f"Unsupported tool type: {tool_type}. "
                f"Supported types: {', '.join(self.SUPPORTED_TOOLS)}"
            )
        
        config = arm_config.get("config", {})
        
        # Route to specific tool creation method
        if tool_type == "tavily_search":
            return self._create_tavily_tool(config)
        elif tool_type == "http_tool":
            return self._create_http_tool(config)
        elif tool_type == "mcp_tool":
            return self._create_mcp_tool(config)
        else:
            raise ToolError(f"Unsupported tool type: {tool_type}")
    
    def _create_tavily_tool(self, config: Dict[str, Any]) -> Any:
        """Create Tavily search tool with API key validation.
        
        Args:
            config: Tool configuration dictionary, may include:
                - api_key: API key for Tavily (optional, falls back to env var)
                - search_depth: Search depth "basic" or "advanced" (default: "advanced")
                - max_tokens: Maximum tokens in response (default: 6000)
                - include_answer: Include AI-generated answer (default: True)
                - format: Response format "json" or "markdown" (default: "markdown")
                - use_search_context: Use search context (default: False)
        
        Returns:
            TavilyTools instance configured with API key
            
        Raises:
            ToolConfigurationError: If API key not found in config or environment
            
        Example:
            >>> tool = registry._create_tavily_tool({"api_key": "tvly-...", "search_depth": "basic"})
        """
        from agno.tools.tavily import TavilyTools
        
        # Get API key from config first, then fall back to environment
        api_key = config.get("api_key") or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "Tavily API key not found. "
                "Please provide 'api_key' in config or set TAVILY_API_KEY environment variable."
            )
        
        # Build tool parameters with defaults
        tool_params = {
            "api_key": api_key,
        }
        
        # Add optional configuration parameters that TavilyTools supports
        if "search_depth" in config:
            tool_params["search_depth"] = config["search_depth"]
        
        if "max_tokens" in config:
            tool_params["max_tokens"] = config["max_tokens"]
        
        if "include_answer" in config:
            tool_params["include_answer"] = config["include_answer"]
        
        if "format" in config:
            tool_params["format"] = config["format"]
        
        if "use_search_context" in config:
            tool_params["use_search_context"] = config["use_search_context"]
        
        return TavilyTools(**tool_params)
    
    def _create_http_tool(self, config: Dict[str, Any]) -> Any:
        """Create HTTP request tool.
        
        Creates a custom HTTP tool that allows agents to make HTTP requests
        to external APIs. Supports GET, POST, PUT, DELETE, and PATCH methods.
        
        Args:
            config: Tool configuration dictionary, may include:
                - name: Name for this tool instance (default: "HTTP Request")
                - description: Description of what this tool does
                - base_url: Base URL for requests (optional)
                - default_headers: Default headers to include (optional)
                - timeout: Request timeout in seconds (default: 30)
        
        Returns:
            HTTPTools instance configured for making HTTP requests
            
        Example:
            >>> tool = registry._create_http_tool({
            ...     "name": "GitHub API",
            ...     "base_url": "https://api.github.com",
            ...     "default_headers": {"Accept": "application/vnd.github.v3+json"},
            ...     "timeout": 30
            ... })
        """
        from frankenagent.tools.http_tool import HTTPTools
        
        # Build tool parameters with defaults
        tool_params = {
            "name": config.get("name", "HTTP Request"),
            "description": config.get("description", "Make HTTP requests to external APIs"),
            "timeout": config.get("timeout", 30),
        }
        
        # Add optional parameters
        if "base_url" in config and config["base_url"]:
            tool_params["base_url"] = config["base_url"]
        
        if "default_headers" in config and config["default_headers"]:
            tool_params["default_headers"] = config["default_headers"]
        
        return HTTPTools(**tool_params)
    
    def _create_mcp_tool(self, config: Dict[str, Any]) -> Any:
        """Create MCP (Model Context Protocol) tool using Agno's MCPTools.
        
        Creates an MCP client tool that connects to an MCP server using Agno framework.
        Supports SSE, HTTP, and streamable-http transports.
        
        Args:
            config: Tool configuration dictionary, must include:
                - server_url: HTTP/SSE endpoint URL (required)
                - transport_type: Transport protocol ("sse", "http", "streamable-http")
                - server_label: Name identifier for the MCP server (optional)
                - allowed_tools: List of allowed tool names (optional, filters available tools)
                - require_approval: Approval requirement (optional)
                - api_token: Authentication token (optional)
                - auth_header: Header name for auth token (optional, default: "Authorization")
        
        Returns:
            Agno MCPTools instance configured to connect to the MCP server
            
        Example:
            >>> tool = registry._create_mcp_tool({
            ...     "server_url": "https://mevzuat.surucu.dev/mcp",
            ...     "transport_type": "sse",
            ...     "server_label": "mevzuat",
            ...     "allowed_tools": ["search_law", "get_regulation"],
            ...     "api_token": "Bearer token123"
            ... })
        """
        from agno.tools.mcp import MCPTools
        import re
        
        # Validate required fields
        if "server_url" not in config:
            raise ConfigurationError("MCP tool requires 'server_url' in config")
        
        server_url = config["server_url"]
        transport_type = config.get("transport_type", "sse")
        
        # Map transport types to Agno's expected values
        # According to Agno MCP docs: "sse", "streamable-http", or "stdio"
        # For HTTP/SSE servers, use "streamable-http" (recommended)
        transport_map = {
            "sse": "streamable-http",  # Map SSE to streamable-http
            "http": "streamable-http",
            "streamable-http": "streamable-http",
        }
        transport = transport_map.get(transport_type, "streamable-http")
        
        # Build tool parameters for Agno MCPTools
        tool_params = {
            "url": server_url,
            "transport": transport,
            "timeout_seconds": config.get("timeout", 30),
        }
        
        # Add tool name prefix if server label is provided
        # Sanitize server_label to only include valid characters (alphanumeric, underscore, hyphen)
        if "server_label" in config and config["server_label"]:
            server_label = config["server_label"]
            # Remove invalid characters and replace spaces with underscores
            sanitized_label = re.sub(r'[^a-zA-Z0-9_-]', '', server_label.replace(' ', '_'))
            if sanitized_label:
                tool_params["tool_name_prefix"] = sanitized_label
                logger.debug(f"Sanitized server_label '{server_label}' to '{sanitized_label}'")
            else:
                logger.warning(f"Server label '{server_label}' contains no valid characters, skipping prefix")
        
        # Note: allowed_tools filtering will be handled after connection
        # Store it in the config for later use
        allowed_tools = config.get("allowed_tools", [])
        
        logger.info(
            f"Creating Agno MCP tool: url={server_url}, transport={transport}, "
            f"allowed_tools={len(allowed_tools) if allowed_tools else 'all'}"
        )
        
        # Create the Agno MCPTools instance
        mcp_tool = MCPTools(**tool_params)
        
        # Store allowed_tools as metadata for filtering
        if allowed_tools:
            mcp_tool._allowed_tools_filter = allowed_tools
        
        return mcp_tool
    
    def get_tool(self, tool_type: str, config: Dict[str, Any]) -> Any:
        """Instantiate a tool from its type and configuration.
        
        Args:
            tool_type: The type of tool to instantiate (e.g., "tavily_search")
            config: Configuration dictionary for the tool, may include:
                - api_key_env: Environment variable name for API key
                - safe_mode: Boolean for safe execution mode
                - Other tool-specific options
        
        Returns:
            Instantiated tool object ready for use with Agno agents
            
        Raises:
            UnknownToolTypeError: If tool_type is not in TOOL_MAP
            ToolConfigurationError: If tool configuration is invalid
            
        Example:
            >>> registry = ToolRegistry()
            >>> tool = registry.get_tool("tavily_search", {"api_key_env": "TAVILY_API_KEY"})
        """
        if tool_type not in self.TOOL_MAP:
            available_types = ", ".join(self.TOOL_MAP.keys())
            raise ToolError(
                f"Unknown tool type: {tool_type}. "
                f"Available types: {available_types}"
            )
        
        tool_class_path = self.TOOL_MAP[tool_type]
        
        try:
            # Import the tool class dynamically
            tool_class = self._import_tool_class(tool_class_path)
            
            # Prepare tool initialization parameters
            init_params = self._prepare_tool_params(tool_type, config)
            
            # Instantiate the tool
            tool_instance = tool_class(**init_params)
            
            return tool_instance
            
        except ImportError as e:
            raise ToolError(
                f"Failed to import tool class {tool_class_path}: {e}"
            )
        except Exception as e:
            raise ToolError(
                f"Failed to instantiate tool {tool_type}: {e}"
            )
    
    def _import_tool_class(self, class_path: str) -> type:
        """Dynamically import a tool class from its module path.
        
        Args:
            class_path: Full path to the class (e.g., "agno.tools.tavily.TavilyTools")
            
        Returns:
            The imported class object
            
        Raises:
            ImportError: If the module or class cannot be imported
        """
        module_path, class_name = class_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    
    def _prepare_tool_params(self, tool_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare initialization parameters for a tool.
        
        Handles API key injection from environment variables and other
        tool-specific configuration transformations.
        
        Args:
            tool_type: The type of tool being configured
            config: Raw configuration from blueprint
            
        Returns:
            Dictionary of parameters ready for tool initialization
            
        Raises:
            ToolConfigurationError: If required configuration is missing
        """
        params = {}
        
        # Handle API key injection from environment
        if "api_key_env" in config:
            env_var = config["api_key_env"]
            api_key = os.getenv(env_var)
            
            if not api_key:
                raise ConfigurationError(
                    f"API key not found in environment variable: {env_var}"
                )
            
            params["api_key"] = api_key
        
        # Handle tool-specific configurations
        if tool_type == "python_eval":
            # Python eval tool supports safe_mode
            if "safe_mode" in config:
                params["safe_mode"] = config["safe_mode"]
        
        elif tool_type == "file_tools":
            # File tools may have base_dir or allowed_paths
            if "base_dir" in config:
                params["base_dir"] = config["base_dir"]
            if "allowed_paths" in config:
                params["allowed_paths"] = config["allowed_paths"]
        
        # Pass through any other configuration options
        for key, value in config.items():
            if key not in ["api_key_env"] and key not in params:
                params[key] = value
        
        return params
