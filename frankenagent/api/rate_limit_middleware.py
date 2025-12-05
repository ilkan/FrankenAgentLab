"""Rate limiting middleware for FastAPI."""

import logging
from typing import Callable
from uuid import UUID

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from frankenagent.services.rate_limit_service import RateLimitService

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits on API requests.
    
    Applies rate limiting to all protected endpoints (those requiring authentication).
    Returns 429 Too Many Requests with Retry-After header when limits are exceeded.
    """
    
    def __init__(self, app, rate_limit_service: RateLimitService):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application instance
            rate_limit_service: RateLimitService instance for checking limits
        """
        super().__init__(app)
        self.rate_limit_service = rate_limit_service
        
        # Paths that should be exempt from rate limiting
        self.exempt_paths = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/register",
            "/api/auth/login",
            "/api/agents/logs",  # Logs endpoint (has its own auth check)
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and apply rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from next handler or 429 if rate limited
        """
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip rate limiting for static files
        if request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Extract user_id from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        # If no user_id, this is an unauthenticated request
        # Let it through - auth middleware will handle rejection
        if not user_id:
            return await call_next(request)
        
        # Check rate limit
        try:
            allowed, retry_after = self.rate_limit_service.check_rate_limit(user_id)
            
            if not allowed:
                # Get current usage for response headers
                usage = self.rate_limit_service.get_usage(user_id)
                
                # Log rate limit violation
                logger.warning(
                    f"Rate limit exceeded for user {user_id} on {request.method} {request.url.path}",
                    extra={
                        "user_id": str(user_id),
                        "path": request.url.path,
                        "method": request.method,
                        "requests_this_minute": usage["requests_this_minute"],
                        "requests_this_day": usage["requests_this_day"]
                    }
                )
                
                # Return 429 with rate limit headers
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "type": "RateLimitExceeded",
                            "message": f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                            "retry_after": retry_after
                        }
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit-Minute": str(usage["minute_limit"]),
                        "X-RateLimit-Remaining-Minute": str(usage["minute_remaining"]),
                        "X-RateLimit-Limit-Day": str(usage["day_limit"]),
                        "X-RateLimit-Remaining-Day": str(usage["day_remaining"])
                    }
                )
            
            # Rate limit passed, proceed with request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            usage = self.rate_limit_service.get_usage(user_id)
            response.headers["X-RateLimit-Limit-Minute"] = str(usage["minute_limit"])
            response.headers["X-RateLimit-Remaining-Minute"] = str(usage["minute_remaining"])
            response.headers["X-RateLimit-Limit-Day"] = str(usage["day_limit"])
            response.headers["X-RateLimit-Remaining-Day"] = str(usage["day_remaining"])
            
            return response
            
        except Exception as e:
            # If rate limiting fails, log error and allow request through
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            return await call_next(request)
