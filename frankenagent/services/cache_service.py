"""Agent cache service using Redis for compiled agent caching.

This module implements caching for compiled agents to avoid recompilation
on every execution, significantly improving performance.
"""

import redis
import pickle
from typing import Optional, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class AgentCacheService:
    """
    Cache service for compiled agents using Redis.
    
    Uses pickle serialization to store compiled agent objects in Redis
    with a TTL of 1 hour. Provides cache invalidation on blueprint updates.
    
    Architecture:
    - Key format: agent:{blueprint_id}:{version}
    - TTL: 3600 seconds (1 hour)
    - Serialization: pickle (for Python object storage)
    - Error handling: Graceful degradation on Redis failures
    
    Example:
        >>> cache = AgentCacheService(redis_host="localhost")
        >>> cache.set_compiled_agent(blueprint_id, version, compiled_agent)
        >>> agent = cache.get_compiled_agent(blueprint_id, version)
    """
    
    def __init__(
        self,
        redis_host: str,
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        ttl: int = 3600
    ):
        """Initialize cache service with Redis connection.
        
        Args:
            redis_host: Redis server hostname or IP
            redis_port: Redis server port (default: 6379)
            redis_password: Optional Redis password for authentication
            ttl: Time-to-live for cached agents in seconds (default: 3600 = 1 hour)
        """
        try:
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                decode_responses=False,  # Keep binary for pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            self.redis.ping()
            self.ttl = ttl
            self.enabled = True
            logger.info(f"AgentCacheService initialized with Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Cache will be disabled.")
            self.redis = None
            self.enabled = False
    
    def get_compiled_agent(self, blueprint_id: UUID, version: int) -> Optional[Any]:
        """Get compiled agent from cache.
        
        Args:
            blueprint_id: UUID of the blueprint
            version: Version number of the blueprint
            
        Returns:
            Compiled agent object if found in cache, None otherwise
            
        Example:
            >>> agent = cache.get_compiled_agent(uuid4(), 1)
            >>> if agent:
            ...     print("Cache hit!")
        """
        if not self.enabled:
            return None
        
        key = f"agent:{blueprint_id}:{version}"
        
        try:
            data = self.redis.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return pickle.loads(data)
            
            logger.debug(f"Cache MISS: {key}")
            return None
            
        except redis.RedisError as e:
            logger.error(f"Redis error on get: {e}")
            return None
        except pickle.UnpicklingError as e:
            logger.error(f"Failed to unpickle cached agent: {e}")
            # Invalidate corrupted cache entry
            try:
                self.redis.delete(key)
            except:
                pass
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting from cache: {e}")
            return None
    
    def set_compiled_agent(
        self,
        blueprint_id: UUID,
        version: int,
        agent: Any
    ) -> bool:
        """Cache compiled agent with TTL.
        
        Args:
            blueprint_id: UUID of the blueprint
            version: Version number of the blueprint
            agent: Compiled agent object to cache
            
        Returns:
            True if successfully cached, False otherwise
            
        Example:
            >>> success = cache.set_compiled_agent(uuid4(), 1, compiled_agent)
        """
        if not self.enabled:
            return False
        
        key = f"agent:{blueprint_id}:{version}"
        
        try:
            data = pickle.dumps(agent)
            self.redis.setex(key, self.ttl, data)
            logger.debug(f"Cache SET: {key} (TTL: {self.ttl}s)")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error on set: {e}")
            return False
        except pickle.PicklingError as e:
            logger.error(f"Failed to pickle agent: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting cache: {e}")
            return False
    
    def invalidate_agent(self, blueprint_id: UUID) -> int:
        """Invalidate all cached versions of an agent.
        
        This is called when a blueprint is updated to ensure
        the next execution uses the new version.
        
        Args:
            blueprint_id: UUID of the blueprint to invalidate
            
        Returns:
            Number of cache entries deleted
            
        Example:
            >>> deleted = cache.invalidate_agent(blueprint_id)
            >>> print(f"Invalidated {deleted} cache entries")
        """
        if not self.enabled:
            return 0
        
        pattern = f"agent:{blueprint_id}:*"
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                logger.debug(f"Cache INVALIDATE: {deleted} keys for {blueprint_id}")
                return deleted
            return 0
            
        except redis.RedisError as e:
            logger.error(f"Redis error on invalidate: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error invalidating cache: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cached agents (use with caution).
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            pattern = "agent:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached agents")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error on clear_all: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error clearing cache: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {
                "enabled": False,
                "total_keys": 0,
                "memory_used": "0B"
            }
        
        try:
            pattern = "agent:*"
            keys = self.redis.keys(pattern)
            info = self.redis.info("memory")
            
            return {
                "enabled": True,
                "total_keys": len(keys),
                "memory_used": info.get("used_memory_human", "unknown"),
                "ttl": self.ttl
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }
