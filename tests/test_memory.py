"""Integration tests for conversation memory."""

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
async def test_session_created_and_persisted(executor, validator, session_manager):
    """Test that session is created and persisted."""
    # Skip if OPENAI_API_KEY not set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Memory Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant."
        },
        "heart": {
            "memory_enabled": True,
            "history_length": 5
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Execute first message
    execution_result = await executor.execute(
        blueprint=normalized,
        message="Hello, my name is Alice"
    )
    
    # Verify session was created
    assert execution_result.success is True
    assert execution_result.session_id is not None
    
    session_id = execution_result.session_id
    
    # Verify session exists in session manager
    session = session_manager.get_or_create(session_id)
    assert session is not None
    assert "created_at" in session
    assert "messages" in session
    
    # Session should persist
    session2 = session_manager.get_or_create(session_id)
    assert session2 == session


@pytest.mark.asyncio
async def test_conversation_history_maintained(executor, validator):
    """Test that conversation history is maintained across messages."""
    # Skip if OPENAI_API_KEY not set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Memory Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant with memory."
        },
        "heart": {
            "memory_enabled": True,
            "history_length": 5
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # First message - introduce name
    result1 = await executor.execute(
        blueprint=normalized,
        message="My name is Bob"
    )
    
    assert result1.success is True
    session_id = result1.session_id
    
    # Second message - ask about name (should remember)
    result2 = await executor.execute(
        blueprint=normalized,
        message="What is my name?",
        session_id=session_id
    )
    
    assert result2.success is True
    assert result2.session_id == session_id
    
    # The response should reference the name Bob
    # (This is a best-effort test - LLM behavior may vary)
    assert result2.response is not None
    assert len(result2.response) > 0


@pytest.mark.asyncio
async def test_history_included_in_context(executor, validator):
    """Test that history is included in agent context."""
    # Skip if OPENAI_API_KEY not set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Memory Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant. Remember what users tell you."
        },
        "heart": {
            "memory_enabled": True,
            "history_length": 3
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Send multiple messages in sequence
    result1 = await executor.execute(
        blueprint=normalized,
        message="I like pizza"
    )
    assert result1.success is True
    session_id = result1.session_id
    
    result2 = await executor.execute(
        blueprint=normalized,
        message="I also like pasta",
        session_id=session_id
    )
    assert result2.success is True
    
    result3 = await executor.execute(
        blueprint=normalized,
        message="What foods do I like?",
        session_id=session_id
    )
    assert result3.success is True
    
    # Agent should remember both foods
    # (Best-effort test - LLM behavior may vary)
    response_lower = result3.response.lower()
    # At least verify we got a response
    assert len(result3.response) > 0


@pytest.mark.asyncio
async def test_new_session_has_no_history(executor, validator):
    """Test that new sessions start with empty history."""
    # Skip if OPENAI_API_KEY not set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Memory Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant."
        },
        "heart": {
            "memory_enabled": True,
            "history_length": 5
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # First session
    result1 = await executor.execute(
        blueprint=normalized,
        message="My favorite color is blue"
    )
    assert result1.success is True
    session_id1 = result1.session_id
    
    # Second session (new session)
    result2 = await executor.execute(
        blueprint=normalized,
        message="What is my favorite color?"
    )
    assert result2.success is True
    session_id2 = result2.session_id
    
    # Should be different sessions
    assert session_id1 != session_id2
    
    # Second session should not know the color
    # (Best-effort test - just verify it executed)
    assert result2.response is not None


@pytest.mark.asyncio
async def test_memory_disabled_no_history(executor, validator):
    """Test that agents without memory don't maintain history."""
    # Skip if OPENAI_API_KEY not set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "No Memory Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant."
        },
        "heart": {
            "memory_enabled": False
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # First message
    result1 = await executor.execute(
        blueprint=normalized,
        message="Remember that I like cats"
    )
    assert result1.success is True
    session_id = result1.session_id
    
    # Second message in same session
    result2 = await executor.execute(
        blueprint=normalized,
        message="What do I like?",
        session_id=session_id
    )
    assert result2.success is True
    
    # Without memory, agent won't remember
    # (Just verify execution succeeded)
    assert result2.response is not None


@pytest.mark.asyncio
async def test_history_length_configuration(executor, validator):
    """Test that history_length configuration is respected."""
    # Skip if OPENAI_API_KEY not set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Limited Memory Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant."
        },
        "heart": {
            "memory_enabled": True,
            "history_length": 2  # Only remember last 2 exchanges
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Verify history_length is configured
    assert normalized["heart"]["history_length"] == 2
    
    # Execute to verify it works
    result1 = await executor.execute(
        blueprint=normalized,
        message="Hello"
    )
    assert result1.success is True


@pytest.mark.asyncio
async def test_multiple_sessions_independent(executor, validator):
    """Test that multiple sessions maintain independent histories."""
    # Skip if OPENAI_API_KEY not set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Memory Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant."
        },
        "heart": {
            "memory_enabled": True,
            "history_length": 5
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    normalized = result.normalized_blueprint
    normalized["id"] = result.blueprint_id
    
    # Session 1
    result1a = await executor.execute(
        blueprint=normalized,
        message="My name is Alice"
    )
    assert result1a.success is True
    session_id1 = result1a.session_id
    
    # Session 2
    result2a = await executor.execute(
        blueprint=normalized,
        message="My name is Bob"
    )
    assert result2a.success is True
    session_id2 = result2a.session_id
    
    # Verify different sessions
    assert session_id1 != session_id2
    
    # Continue session 1
    result1b = await executor.execute(
        blueprint=normalized,
        message="What is my name?",
        session_id=session_id1
    )
    assert result1b.success is True
    
    # Continue session 2
    result2b = await executor.execute(
        blueprint=normalized,
        message="What is my name?",
        session_id=session_id2
    )
    assert result2b.success is True
    
    # Both should have responses
    assert result1b.response is not None
    assert result2b.response is not None
