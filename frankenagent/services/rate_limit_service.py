"""Rate limiting service using Redis for request throttling."""

import redis
import time
import logging
from typing import Tuple
from uuid import UUID

logger = logging.getLogger(__name__)


class RateLimitService:
    """
    Rate limiting service using Redis for sliding window rate limiting.
    
    Implements per-user rate limits:
    - 100 requests per minute
    - 1000 requests per day
    """
    
    def __init__(
        self,
        redis_host: str,
        redis_port: int = 6379,
        requests_per_minute: int = 100,
        requests_per_day: int = 1000
    ):
        """
        Initialize rate limit service.
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            requests_per_minute: Maximum requests allowed per minute
            requests_per_day: Maximum requests allowed per day
        """
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
    
    def check_rate_limit(self, user_id: UUID) -> Tuple[bool, int]:
        """
        Check if user is within rate limits.
        
        Uses Redis INCR with TTL for efficient sliding window implementation.
        
        Args:
            user_id: User UUID to check rate limit for
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
            - allowed: True if request is allowed, False if rate limited
            - retry_after_seconds: Seconds to wait before retrying (0 if allowed)
        """
        current_time = int(time.time())
        minute_window = current_time // 60
        day_window = current_time // 86400
        
        minute_key = f"ratelimit:minute:{user_id}:{minute_window}"
        day_key = f"ratelimit:day:{user_id}:{day_window}"
        
        try:
            # Check minute limit
            minute_count = self.redis.incr(minute_key)
            if minute_count == 1:
                # First request in this window, set expiration
                self.redis.expire(minute_key, 60)
            
            if minute_count > self.requests_per_minute:
                # Calculate seconds until next minute window
                retry_after = 60 - (current_time % 60)
                logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{minute_count} requests in current minute"
                )
                return False, retry_after
            
            # Check day limit
            day_count = self.redis.incr(day_key)
            if day_count == 1:
                # First request in this window, set expiration
                self.redis.expire(day_key, 86400)
            
            if day_count > self.requests_per_day:
                # Calculate seconds until next day window
                retry_after = 86400 - (current_time % 86400)
                logger.warning(
                    f"Daily rate limit exceeded for user {user_id}: "
                    f"{day_count} requests today"
                )
                return False, retry_after
            
            # Both limits passed
            return True, 0
            
        except Exception as e:
            # If Redis is down, fail open (allow request) but log error
            logger.error(f"Redis error in rate limiting: {e}")
            return True, 0
    
    def get_usage(self, user_id: UUID) -> dict:
        """
        Get current usage statistics for a user.
        
        Args:
            user_id: User UUID to get usage for
            
        Returns:
            Dictionary with usage statistics:
            - requests_this_minute: Current minute request count
            - requests_this_day: Current day request count
            - minute_limit: Maximum requests per minute
            - day_limit: Maximum requests per day
            - minute_remaining: Remaining requests this minute
            - day_remaining: Remaining requests today
        """
        current_time = int(time.time())
        minute_window = current_time // 60
        day_window = current_time // 86400
        
        minute_key = f"ratelimit:minute:{user_id}:{minute_window}"
        day_key = f"ratelimit:day:{user_id}:{day_window}"
        
        try:
            minute_count = int(self.redis.get(minute_key) or 0)
            day_count = int(self.redis.get(day_key) or 0)
            
            return {
                "requests_this_minute": minute_count,
                "requests_this_day": day_count,
                "minute_limit": self.requests_per_minute,
                "day_limit": self.requests_per_day,
                "minute_remaining": max(0, self.requests_per_minute - minute_count),
                "day_remaining": max(0, self.requests_per_day - day_count)
            }
        except Exception as e:
            logger.error(f"Redis error getting usage: {e}")
            return {
                "requests_this_minute": 0,
                "requests_this_day": 0,
                "minute_limit": self.requests_per_minute,
                "day_limit": self.requests_per_day,
                "minute_remaining": self.requests_per_minute,
                "day_remaining": self.requests_per_day
            }
    
    def reset_user_limits(self, user_id: UUID) -> bool:
        """
        Reset rate limits for a user (admin function).
        
        Args:
            user_id: User UUID to reset limits for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            current_time = int(time.time())
            minute_window = current_time // 60
            day_window = current_time // 86400
            
            minute_key = f"ratelimit:minute:{user_id}:{minute_window}"
            day_key = f"ratelimit:day:{user_id}:{day_window}"
            
            self.redis.delete(minute_key, day_key)
            logger.info(f"Reset rate limits for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Redis error resetting limits: {e}")
            return False
