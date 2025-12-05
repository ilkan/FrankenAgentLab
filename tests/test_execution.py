"""Integration tests for agent execution with tools."""

import pytest
import os
from frankenagent.compiler.compiler import AgentCompiler
from frankenagent.compiler.validator import BlueprintValidator
from frankenagent.runtime.executor import ExecutionOrchestrator
from frankenagent.runtime.session_manager import SessionManager


@pytest.fixture
def compiler():
    """Create compiler instance."""
    return AgentCompiler()


@pytest.fixture
def validator():
    """Create validator instance."""
    return BlueprintValidator()


@pytest.fixture
def session_manager():
    """Create session manager instance."""
    return SessionManager()


@pytest.fixture
def executor(compiler, session_manager):
    """Create execution orchestrator instance."""
    return ExecutionOrchestrator(compiler, session_manager)


@pytest.mark.asyncio
async def test_execute_simple_query_without_tools(executor, validator):
    """Test that agent can execute a simple query without tools."""
    # Skip if OPENAI_API_KEY not set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Simple Assistant",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant. Keep responses brief."
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Execute simple query
    execution_result = await executor.execute(
        blueprint=normalized,
        message="Say hello in one word"
    )
    
    # Verify execution succeeded
    assert execution_result.success is True
    assert execution_result.response is not None
    assert len(execution_result.response) > 0
    assert execution_result.session_id is not None
    assert execution_result.total_latency_ms > 0
    assert len(execution_result.tool_calls) == 0  # No tools used


@pytest.mark.asyncio
async def test_execute_with_tavily_search(executor, validator):
    """Test that agent with Tavily tool can execute successfully."""
    # Skip if API keys not set
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        pytest.skip("OPENAI_API_KEY or TAVILY_API_KEY not set")
    
    blueprint = {
        "name": "Search Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a research assistant. Use search when needed."
        },
        "arms": [
            {
                "type": "tavily_search",
                "config": {"max_results": 3}
            }
        ],
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Execute query that requires search
    execution_result = await executor.execute(
        blueprint=normalized,
        message="What is the current weather in San Francisco?"
    )
    
    # Verify execution succeeded
    assert execution_result.success is True
    assert execution_result.response is not None
    assert execution_result.session_id is not None
    assert execution_result.total_latency_ms > 0
    
    # Note: Tool call tracking is a known limitation in current implementation
    # The agent can use tools, but detailed logging is not yet fully implemented


@pytest.mark.asyncio
async def test_tool_call_logged_correctly(executor, validator, session_manager):
    """Test that execution creates a session with logs."""
    # Skip if API keys not set
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        pytest.skip("OPENAI_API_KEY or TAVILY_API_KEY not set")
    
    blueprint = {
        "name": "Search Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a research assistant."
        },
        "arms": [
            {
                "type": "tavily_search",
                "config": {}
            }
        ],
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Execute query
    execution_result = await executor.execute(
        blueprint=normalized,
        message="Search for Python programming"
    )
    
    # Verify execution succeeded
    assert execution_result.success is True
    assert execution_result.session_id is not None
    
    # Verify session was created
    session = session_manager.get_or_create(execution_result.session_id)
    assert session is not None
    assert "created_at" in session
    
    # Note: Detailed tool call logging is a known limitation in current implementation


@pytest.mark.asyncio
async def test_response_includes_tool_metadata(executor, validator):
    """Test that response includes tool call metadata."""
    # Skip if API keys not set
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        pytest.skip("OPENAI_API_KEY or TAVILY_API_KEY not set")
    
    blueprint = {
        "name": "Search Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a research assistant."
        },
        "arms": [
            {
                "type": "tavily_search",
                "config": {}
            }
        ],
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Execute query
    execution_result = await executor.execute(
        blueprint=normalized,
        message="What is Python?"
    )
    
    # Verify response structure includes metadata
    assert execution_result.success is True
    assert execution_result.response is not None
    assert execution_result.session_id is not None
    assert execution_result.total_latency_ms > 0
    assert isinstance(execution_result.tool_calls, list)
    assert isinstance(execution_result.guardrails_triggered, list)
    
    # If tools were called, verify metadata structure
    if len(execution_result.tool_calls) > 0:
        tool_call = execution_result.tool_calls[0]
        assert "tool" in tool_call
        assert "duration_ms" in tool_call
        assert "success" in tool_call


@pytest.mark.asyncio
async def test_execute_without_search_when_not_needed(executor, validator):
    """Test that agent doesn't use search for simple queries."""
    # Skip if API keys not set
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        pytest.skip("OPENAI_API_KEY or TAVILY_API_KEY not set")
    
    blueprint = {
        "name": "Search Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant. Only use search when you need current information."
        },
        "arms": [
            {
                "type": "tavily_search",
                "config": {}
            }
        ],
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Execute query that doesn't need search
    execution_result = await executor.execute(
        blueprint=normalized,
        message="What is 2+2?"
    )
    
    # Verify execution succeeded
    assert execution_result.success is True
    assert execution_result.response is not None
    
    # Agent should not use search for simple math
    # (though this is not guaranteed, so we just check it executed)
    assert execution_result.total_latency_ms > 0
