"""Custom HTTP tool for Agno agents.

This module provides a custom HTTP request tool that can be used with Agno agents
to make HTTP requests to external APIs. Since Agno doesn't have a built-in HTTP tool,
this implements the tool interface that Agno expects.
"""

import httpx
from typing import Dict, Any, Optional, Literal
from agno.tools import Toolkit
from agno.utils.log import logger


class HTTPTools(Toolkit):
    """HTTP request tool for making API calls from Agno agents.
    
    This tool allows agents to make HTTP requests (GET, POST, PUT, DELETE, PATCH)
    to external APIs. It supports custom headers, timeouts, and base URLs.
    
    Attributes:
        name: Name of this tool instance
        description: Description of what this tool does
        base_url: Optional base URL to prepend to all requests
        default_headers: Default headers to include in all requests
        timeout: Request timeout in seconds
    
    Example:
        >>> http_tool = HTTPTools(
        ...     name="API Client",
        ...     description="Make requests to external API",
        ...     base_url="https://api.example.com",
        ...     default_headers={"Authorization": "Bearer token"},
        ...     timeout=30
        ... )
        >>> # Agent will use this tool to make HTTP requests
    """
    
    def __init__(
        self,
        name: str = "HTTP Request",
        description: str = "Make HTTP requests to external APIs",
        base_url: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        """Initialize HTTP tool.
        
        Args:
            name: Name for this tool instance
            description: Description of what this tool does
            base_url: Optional base URL to prepend to requests
            default_headers: Optional default headers for all requests
            timeout: Request timeout in seconds (default: 30)
        """
        super().__init__(name=name)
        
        self.description = description
        self.base_url = base_url.rstrip("/") if base_url else None
        self.default_headers = default_headers or {}
        self.timeout = timeout
        
        # Register the HTTP request methods
        self.register(self.get)
        self.register(self.post)
        self.register(self.put)
        self.register(self.delete)
        self.register(self.patch)
    
    def _build_url(self, path: str) -> str:
        """Build full URL from base_url and path.
        
        Args:
            path: URL path or full URL
            
        Returns:
            Full URL string
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path
        
        if self.base_url:
            return f"{self.base_url}/{path.lstrip('/')}"
        
        return path
    
    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Merge default headers with request-specific headers.
        
        Args:
            headers: Request-specific headers
            
        Returns:
            Merged headers dictionary
        """
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Make a GET request.
        
        Args:
            url: URL path or full URL to request
            headers: Optional headers to include (merged with default_headers)
            params: Optional query parameters
            
        Returns:
            Response body as string
            
        Example:
            >>> result = http_tool.get("/users", params={"limit": 10})
        """
        try:
            full_url = self._build_url(url)
            merged_headers = self._merge_headers(headers)
            
            logger.info(f"HTTP GET: {full_url}")
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    full_url,
                    headers=merged_headers,
                    params=params,
                )
                response.raise_for_status()
                return response.text
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """Make a POST request.
        
        Args:
            url: URL path or full URL to request
            data: Optional form data to send
            json: Optional JSON data to send
            headers: Optional headers to include (merged with default_headers)
            
        Returns:
            Response body as string
            
        Example:
            >>> result = http_tool.post("/users", json={"name": "John"})
        """
        try:
            full_url = self._build_url(url)
            merged_headers = self._merge_headers(headers)
            
            logger.info(f"HTTP POST: {full_url}")
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    full_url,
                    headers=merged_headers,
                    data=data,
                    json=json,
                )
                response.raise_for_status()
                return response.text
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """Make a PUT request.
        
        Args:
            url: URL path or full URL to request
            data: Optional form data to send
            json: Optional JSON data to send
            headers: Optional headers to include (merged with default_headers)
            
        Returns:
            Response body as string
        """
        try:
            full_url = self._build_url(url)
            merged_headers = self._merge_headers(headers)
            
            logger.info(f"HTTP PUT: {full_url}")
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.put(
                    full_url,
                    headers=merged_headers,
                    data=data,
                    json=json,
                )
                response.raise_for_status()
                return response.text
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """Make a DELETE request.
        
        Args:
            url: URL path or full URL to request
            headers: Optional headers to include (merged with default_headers)
            
        Returns:
            Response body as string
        """
        try:
            full_url = self._build_url(url)
            merged_headers = self._merge_headers(headers)
            
            logger.info(f"HTTP DELETE: {full_url}")
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.delete(
                    full_url,
                    headers=merged_headers,
                )
                response.raise_for_status()
                return response.text
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    
    def patch(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """Make a PATCH request.
        
        Args:
            url: URL path or full URL to request
            data: Optional form data to send
            json: Optional JSON data to send
            headers: Optional headers to include (merged with default_headers)
            
        Returns:
            Response body as string
        """
        try:
            full_url = self._build_url(url)
            merged_headers = self._merge_headers(headers)
            
            logger.info(f"HTTP PATCH: {full_url}")
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.patch(
                    full_url,
                    headers=merged_headers,
                    data=data,
                    json=json,
                )
                response.raise_for_status()
                return response.text
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
