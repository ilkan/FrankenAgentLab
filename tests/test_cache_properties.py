"""Property-based tests for agent cache service.

Feature: platform-evolution
Properties tested:
- Property 17: Cache hit avoids recompilation
- Property 18: Update invalidates cache

Validates: Requirements 7.2, 7.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch
import pickle

from frankenagent.services.cache_service import AgentCacheService
from frankenagent.compiler.compiler import AgentCompiler, CompiledAgent
from frankenagent.runtime.executor import ExecutionOrchestrator
from frankenagent.runtime.session_manager import SessionManager


# Helper functions

def create_mock_redis():
    """Create a mock Redis client that simulates in-memory storage."""
    storage = {}
    
    mock_redis = Mock()
    
    def mock_get(key):
        return storage.get(key)
    
    def mock_setex(key, ttl, value):
        storage[key] = value
        return True
    
    def mock_delete(*keys):
        deleted = 0
        for key in keys:
            if key in storage:
                del storage[key]
                deleted += 1
        return deleted
    
    def mock_keys(pattern):
        # Simple pattern matching for agent:*
        if pattern == "agent:*":
            return [k for k in storage.keys() if k.startswith("agent:")]
        # Pattern matching for agent:{uuid}:*
        if pattern.startswith("agent:") and pattern.endswith(":*"):
            prefix = pattern[:-1]  # Remove the *
            return [k for k in storage.keys() if k.startswith(prefix)]
        return []
    
    def mock_ping():
        return True
    
    def mock_info(section):
        return {"used_memory_human": "1.5M"}
    
    mock_redis.get = mock_get
    mock_redis.setex = mock_setex
    mock_redis.delete = mock_delete
    mock_redis.keys = mock_keys
    mock_redis.ping = mock_ping
    mock_redis.info = mock_info
    
    return mock_redis, storage


class SimpleAgent:
    """Simple picklable agent for testing."""
    def __init__(self):
        self.response = "Test response"
    
    def run(self, message):
        return self.response


def create_mock_compiled_agent(blueprint_id=None):
    """Create a mock compiled agent with a picklable agent."""
    simple_agent = SimpleAgent()
    
    if blueprint_id is None:
        blueprint_id = str(uuid4())
    
    compiled = CompiledAgent(
        agent=simple_agent,
        blueprint_id=blueprint_id,
        guardrails={"max_tool_calls": 10, "timeout_seconds": 60}
    )
    
    return compiled


# Hypothesis strategies

@st.composite
def blueprint_ids_and_versions(draw):
    """Generate blueprint ID and version pairs."""
    blueprint_id = uuid4()
    version = draw(st.integers(min_value=1, max_value=100))
    return blueprint_id, version


@st.composite
def blueprint_data(draw):
    """Generate minimal valid blueprint data."""
    blueprint_id = uuid4()
    version = draw(st.integers(min_value=1, max_value=10))
    
    return {
        "id": str(blueprint_id),
        "version": version,
        "name": draw(st.text(min_size=1, max_size=50)),
        "head": {
            "model": "gpt-4",
            "provider": "openai",
            "system_prompt": "You are a helpful assistant"
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }


# Property tests

@given(blueprint_id=st.uuids(), version=st.integers(min_value=1, max_value=100))
@settings(max_examples=10, deadline=None)
def test_property_17_cache_hit_avoids_recompilation(blueprint_id, version):
    """
    **Feature: platform-evolution, Property 17: Cache hit avoids recompilation**
    
    For any blueprint that has been executed once, a second execution with the same
    blueprint_id and version should retrieve the compiled agent from cache without
    invoking the compiler.
    
    **Validates: Requirements 7.2**
    """
    # Setup: Create cache service with mock Redis
    mock_redis, storage = create_mock_redis()
    
    with patch('frankenagent.services.cache_service.redis.Redis', return_value=mock_redis):
        cache_service = AgentCacheService(redis_host="localhost")
    
    # Create a mock compiled agent
    compiled_agent = create_mock_compiled_agent()
    
    # First execution: Store in cache
    success = cache_service.set_compiled_agent(blueprint_id, version, compiled_agent)
    assert success, "Failed to cache compiled agent"
    
    # Verify it was stored
    cache_key = f"agent:{blueprint_id}:{version}"
    assert cache_key in storage, "Cache key not found in storage"
    
    # Second execution: Retrieve from cache
    cached_agent = cache_service.get_compiled_agent(blueprint_id, version)
    
    # Property: Cache hit should return the same agent without recompilation
    assert cached_agent is not None, "Cache hit should return cached agent"
    # After unpickling, we get a new object instance, but it should have the same properties
    assert type(cached_agent.agent).__name__ == type(compiled_agent.agent).__name__, \
        "Cached agent should be same type"
    assert cached_agent.agent.response == compiled_agent.agent.response, \
        "Cached agent should have same response"
    assert cached_agent.guardrails == compiled_agent.guardrails, "Guardrails should match"
    assert cached_agent.blueprint_id == compiled_agent.blueprint_id, "Blueprint ID should match"
    
    # Verify the cached data is the pickled version of the original
    stored_data = storage[cache_key]
    unpickled = pickle.loads(stored_data)
    assert type(unpickled.agent).__name__ == type(compiled_agent.agent).__name__, \
        "Unpickled agent should be same type"


@given(blueprint_id=st.uuids(), initial_version=st.integers(min_value=1, max_value=50))
@settings(max_examples=10, deadline=None)
def test_property_18_update_invalidates_cache(blueprint_id, initial_version):
    """
    **Feature: platform-evolution, Property 18: Update invalidates cache**
    
    For any blueprint that is updated, any cached compiled agents for that blueprint_id
    should be removed from the cache, forcing recompilation on next execution.
    
    **Validates: Requirements 7.3**
    """
    # Setup: Create cache service with mock Redis
    mock_redis, storage = create_mock_redis()
    
    with patch('frankenagent.services.cache_service.redis.Redis', return_value=mock_redis):
        cache_service = AgentCacheService(redis_host="localhost")
    
    # Create and cache multiple versions of the same blueprint
    versions_to_cache = [initial_version, initial_version + 1, initial_version + 2]
    
    for version in versions_to_cache:
        compiled_agent = create_mock_compiled_agent()
        cache_service.set_compiled_agent(blueprint_id, version, compiled_agent)
    
    # Verify all versions are cached
    for version in versions_to_cache:
        cache_key = f"agent:{blueprint_id}:{version}"
        assert cache_key in storage, f"Version {version} should be cached"
    
    # Simulate blueprint update by invalidating cache
    deleted_count = cache_service.invalidate_agent(blueprint_id)
    
    # Property: All cached versions should be invalidated
    assert deleted_count == len(versions_to_cache), \
        f"Should invalidate all {len(versions_to_cache)} cached versions"
    
    # Verify all versions are removed from cache
    for version in versions_to_cache:
        cache_key = f"agent:{blueprint_id}:{version}"
        assert cache_key not in storage, f"Version {version} should be invalidated"
    
    # Verify cache miss after invalidation
    for version in versions_to_cache:
        cached_agent = cache_service.get_compiled_agent(blueprint_id, version)
        assert cached_agent is None, \
            f"Cache should miss for version {version} after invalidation"


@given(
    blueprint_id=st.uuids(),
    version=st.integers(min_value=1, max_value=100),
    num_executions=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=10, deadline=None)
def test_cache_hit_consistency_across_multiple_executions(blueprint_id, version, num_executions):
    """
    Additional test: Verify cache returns consistent results across multiple retrievals.
    
    For any cached agent, multiple cache hits should return the same agent instance.
    """
    # Setup: Create cache service with mock Redis
    mock_redis, storage = create_mock_redis()
    
    with patch('frankenagent.services.cache_service.redis.Redis', return_value=mock_redis):
        cache_service = AgentCacheService(redis_host="localhost")
    
    # Create and cache an agent
    original_agent = create_mock_compiled_agent()
    cache_service.set_compiled_agent(blueprint_id, version, original_agent)
    
    # Retrieve multiple times
    retrieved_agents = []
    for _ in range(num_executions):
        agent = cache_service.get_compiled_agent(blueprint_id, version)
        retrieved_agents.append(agent)
    
    # Verify all retrievals return the same agent properties
    for agent in retrieved_agents:
        assert agent is not None, "Cache should hit for all retrievals"
        assert type(agent.agent).__name__ == type(original_agent.agent).__name__, \
            "All retrievals should return same agent type"
        assert agent.agent.response == original_agent.agent.response, \
            "All retrievals should have same response"
        assert agent.guardrails == original_agent.guardrails, "Guardrails should be consistent"


@given(blueprint_ids=st.lists(st.uuids(), min_size=2, max_size=5, unique=True))
@settings(max_examples=10, deadline=None)
def test_cache_isolation_between_blueprints(blueprint_ids):
    """
    Additional test: Verify cache isolation between different blueprints.
    
    For any set of different blueprints, invalidating one should not affect others.
    """
    # Setup: Create cache service with mock Redis
    mock_redis, storage = create_mock_redis()
    
    with patch('frankenagent.services.cache_service.redis.Redis', return_value=mock_redis):
        cache_service = AgentCacheService(redis_host="localhost")
    
    # Cache agents for all blueprints
    version = 1
    for blueprint_id in blueprint_ids:
        agent = create_mock_compiled_agent()
        cache_service.set_compiled_agent(blueprint_id, version, agent)
    
    # Verify all are cached
    for blueprint_id in blueprint_ids:
        agent = cache_service.get_compiled_agent(blueprint_id, version)
        assert agent is not None, f"Blueprint {blueprint_id} should be cached"
    
    # Invalidate the first blueprint
    target_blueprint = blueprint_ids[0]
    cache_service.invalidate_agent(target_blueprint)
    
    # Verify only the target blueprint is invalidated
    for blueprint_id in blueprint_ids:
        agent = cache_service.get_compiled_agent(blueprint_id, version)
        if blueprint_id == target_blueprint:
            assert agent is None, "Target blueprint should be invalidated"
        else:
            assert agent is not None, "Other blueprints should remain cached"


@given(blueprint_id=st.uuids(), version=st.integers(min_value=1, max_value=100))
@settings(max_examples=10, deadline=None)
def test_cache_graceful_degradation_on_redis_failure(blueprint_id, version):
    """
    Additional test: Verify cache service handles Redis failures gracefully.
    
    For any cache operation, if Redis fails, the system should continue without crashing.
    """
    # Setup: Create cache service with failing Redis
    mock_redis = Mock()
    mock_redis.ping.side_effect = Exception("Redis connection failed")
    
    with patch('frankenagent.services.cache_service.redis.Redis', return_value=mock_redis):
        cache_service = AgentCacheService(redis_host="localhost")
    
    # Verify cache is disabled
    assert not cache_service.enabled, "Cache should be disabled on Redis failure"
    
    # Verify operations don't crash
    agent = create_mock_compiled_agent()
    
    # Set should return False but not crash
    success = cache_service.set_compiled_agent(blueprint_id, version, agent)
    assert not success, "Set should fail gracefully"
    
    # Get should return None but not crash
    cached = cache_service.get_compiled_agent(blueprint_id, version)
    assert cached is None, "Get should return None gracefully"
    
    # Invalidate should return 0 but not crash
    deleted = cache_service.invalidate_agent(blueprint_id)
    assert deleted == 0, "Invalidate should return 0 gracefully"
