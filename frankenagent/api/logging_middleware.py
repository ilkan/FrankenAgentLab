"""Request/Response logging middleware for FastAPI.

Provides structured logging of all HTTP requests and responses with
timing information, status codes, and error tracking.
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses.
    
    Logs:
    - Request method, path, and query parameters
    - Response status code
    - Request duration in milliseconds
    - Client IP address
    - User agent
    - Authenticated user ID (if available)
    
    Example log output:
        INFO - Request: GET /api/blueprints - 200 OK - 45ms - user_id=abc123
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize middleware.
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Start timing
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        # Log request start
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "event": "request_start",
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": str(user_id) if user_id else None
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log successful response
            logger.info(
                f"Request completed: {method} {path} - {response.status_code} - {duration_ms}ms",
                extra={
                    "event": "request_complete",
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": str(user_id) if user_id else None
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log error
            logger.error(
                f"Request failed: {method} {path} - {duration_ms}ms - {str(e)}",
                extra={
                    "event": "request_error",
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": str(user_id) if user_id else None
                },
                exc_info=True
            )
            
            # Re-raise to let error handlers deal with it
            raise


class AuthEventLogger:
    """Logger for authentication-related events.
    
    Provides structured logging for:
    - User registration
    - Login attempts (success and failure)
    - Token validation
    - Logout events
    - Password changes
    
    Security:
    - Never logs passwords or tokens
    - Logs failed login attempts for security monitoring
    - Includes IP address for audit trail
    """
    
    def __init__(self):
        """Initialize auth event logger."""
        self.logger = logging.getLogger("auth")
    
    def log_registration(
        self,
        email: str,
        user_id: str,
        client_ip: str,
        success: bool = True,
        error: str = None
    ) -> None:
        """Log user registration event.
        
        Args:
            email: User email address
            user_id: Generated user ID (if successful)
            client_ip: Client IP address
            success: Whether registration succeeded
            error: Error message if failed
        """
        level = logging.INFO if success else logging.WARNING
        self.logger.log(
            level,
            f"User registration {'succeeded' if success else 'failed'}: {email}",
            extra={
                "event": "user_registration",
                "email": email,
                "user_id": user_id if success else None,
                "client_ip": client_ip,
                "success": success,
                "error": error
            }
        )
    
    def log_login_attempt(
        self,
        email: str,
        client_ip: str,
        success: bool,
        user_id: str = None,
        error: str = None
    ) -> None:
        """Log login attempt.
        
        Args:
            email: User email address
            client_ip: Client IP address
            success: Whether login succeeded
            user_id: User ID (if successful)
            error: Error message if failed
        """
        level = logging.INFO if success else logging.WARNING
        self.logger.log(
            level,
            f"Login {'succeeded' if success else 'failed'}: {email}",
            extra={
                "event": "login_attempt",
                "email": email,
                "client_ip": client_ip,
                "success": success,
                "user_id": user_id,
                "error": error
            }
        )
    
    def log_token_validation(
        self,
        user_id: str,
        valid: bool,
        reason: str = None
    ) -> None:
        """Log token validation event.
        
        Args:
            user_id: User ID from token
            valid: Whether token is valid
            reason: Reason for invalidity (if applicable)
        """
        level = logging.DEBUG if valid else logging.WARNING
        self.logger.log(
            level,
            f"Token validation {'succeeded' if valid else 'failed'}: {user_id}",
            extra={
                "event": "token_validation",
                "user_id": user_id,
                "valid": valid,
                "reason": reason
            }
        )
    
    def log_logout(
        self,
        user_id: str,
        client_ip: str
    ) -> None:
        """Log user logout.
        
        Args:
            user_id: User ID
            client_ip: Client IP address
        """
        self.logger.info(
            f"User logged out: {user_id}",
            extra={
                "event": "logout",
                "user_id": user_id,
                "client_ip": client_ip
            }
        )
    
    def log_api_key_access(
        self,
        user_id: str,
        provider: str,
        action: str,
        success: bool = True,
        error: str = None
    ) -> None:
        """Log API key access event (with sanitization).
        
        SECURITY: Never logs actual API keys, only metadata.
        
        Args:
            user_id: User ID
            provider: API key provider (openai, anthropic, etc.)
            action: Action performed (add, retrieve, delete, rotate)
            success: Whether action succeeded
            error: Error message if failed
        """
        level = logging.INFO if success else logging.WARNING
        self.logger.log(
            level,
            f"API key {action} {'succeeded' if success else 'failed'}: {provider}",
            extra={
                "event": "api_key_access",
                "user_id": user_id,
                "provider": provider,
                "action": action,
                "success": success,
                "error": error
            }
        )


# Global auth event logger instance
auth_logger = AuthEventLogger()
