"""Integration tests for agent compilation."""

import pytest
import os
from frankenagent.compiler.compiler import AgentCompiler
from frankenagent.compiler.validator import BlueprintValidator
from frankenagent.tools.registry import ToolRegistry
from frankenagent.exceptions import CompilationError
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude


@pytest.fixture
def compiler():
    """Create compiler instance."""
    return AgentCompiler()


@pytest.fixture
def validator():
    """Create validator instance."""
    return BlueprintValidator()


def test_compile_simple_blueprint_to_agent(compiler, validator):
    """Test that a simple blueprint compiles to an Agno Agent."""
    blueprint = {
        "name": "Simple Assistant",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant"
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    # Validate and normalize first
    result = validator.validate(blueprint)
    assert result.valid is True
    
    # Compile
    compiled_agent = compiler.compile(result.normalized_blueprint)
    
    # Verify compiled agent structure
    assert compiled_agent is not None
    assert compiled_agent.agent is not None
    assert isinstance(compiled_agent.agent, Agent)
    assert compiled_agent.blueprint_id is not None
    assert compiled_agent.guardrails is not None


def test_compile_openai_model_configured_correctly(compiler, validator):
    """Test that OpenAI model is configured with correct parameters."""
    blueprint = {
        "name": "OpenAI Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a test assistant",
            "temperature": 0.5,
            "max_tokens": 1000
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    compiled_agent = compiler.compile(result.normalized_blueprint)
    
    # Verify agent has correct model
    agent = compiled_agent.agent
    assert agent is not None
    assert isinstance(agent.model, OpenAIChat)
    assert agent.model.id == "gpt-4o"
    assert agent.model.temperature == 0.5
    assert agent.model.max_tokens == 1000
    
    # Verify instructions
    assert agent.instructions == "You are a test assistant"


def test_compile_anthropic_model_configured_correctly(compiler, validator):
    """Test that Anthropic model is configured with correct parameters."""
    blueprint = {
        "name": "Claude Agent",
        "head": {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "system_prompt": "You are Claude",
            "temperature": 0.7
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    compiled_agent = compiler.compile(result.normalized_blueprint)
    
    # Verify agent has correct model
    agent = compiled_agent.agent
    assert agent is not None
    assert isinstance(agent.model, Claude)
    assert agent.model.id == "claude-3-5-sonnet-20241022"
    assert agent.model.temperature == 0.7


def test_compile_with_tools_attached(compiler, validator):
    """Test that tools are correctly attached to the agent."""
    # Skip if TAVILY_API_KEY not set
    if not os.getenv("TAVILY_API_KEY"):
        pytest.skip("TAVILY_API_KEY not set")
    
    blueprint = {
        "name": "Search Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a research assistant"
        },
        "arms": [
            {
                "type": "tavily_search",
                "config": {"max_results": 5}
            }
        ],
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    compiled_agent = compiler.compile(result.normalized_blueprint)
    
    # Verify tools are attached
    agent = compiled_agent.agent
    assert agent.tools is not None
    assert len(agent.tools) > 0


def test_compile_with_memory_enabled(compiler, validator):
    """Test that memory is configured when enabled in blueprint."""
    blueprint = {
        "name": "Memory Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You remember conversations"
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
    compiled_agent = compiler.compile(result.normalized_blueprint)
    
    # Verify memory is configured
    agent = compiled_agent.agent
    assert agent.storage is not None
    assert agent.add_history_to_messages is True
    assert agent.num_history_responses == 5


def test_compile_with_guardrails(compiler, validator):
    """Test that guardrails are included in compiled agent."""
    blueprint = {
        "name": "Guarded Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "legs": {
            "execution_mode": "single_agent"
        },
        "spine": {
            "max_tool_calls": 3,
            "timeout_seconds": 30
        }
    }
    
    result = validator.validate(blueprint)
    compiled_agent = compiler.compile(result.normalized_blueprint)
    
    # Verify guardrails are stored
    assert compiled_agent.guardrails is not None
    assert compiled_agent.guardrails["max_tool_calls"] == 3
    assert compiled_agent.guardrails["timeout_seconds"] == 30


def test_compile_with_default_values(compiler, validator):
    """Test that default values are applied during compilation."""
    blueprint = {
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "legs": {}
    }
    
    result = validator.validate(blueprint)
    compiled_agent = compiler.compile(result.normalized_blueprint)
    
    # Verify defaults were applied
    agent = compiled_agent.agent
    assert agent.instructions == "You are a helpful assistant"
    assert agent.model.temperature == 0.7
    
    # Verify default guardrails
    assert compiled_agent.guardrails["max_tool_calls"] == 10
    assert compiled_agent.guardrails["timeout_seconds"] == 60


def test_compile_unsupported_provider_raises_error(compiler):
    """Test that unsupported provider raises CompilationError."""
    blueprint = {
        "name": "Invalid",
        "head": {
            "provider": "unsupported",
            "model": "some-model"
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    with pytest.raises(CompilationError):
        compiler.compile(blueprint)


def test_compile_multiple_tools(compiler, validator):
    """Test that multiple tools can be attached."""
    # Skip if TAVILY_API_KEY not set
    if not os.getenv("TAVILY_API_KEY"):
        pytest.skip("TAVILY_API_KEY not set")
    
    blueprint = {
        "name": "Multi-Tool Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "arms": [
            {"type": "tavily_search", "config": {}},
            {"type": "tavily_search", "config": {"max_results": 3}}
        ],
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    compiled_agent = compiler.compile(result.normalized_blueprint)
    
    # Verify multiple tools attached
    agent = compiled_agent.agent
    assert len(agent.tools) >= 2


def test_compile_preserves_blueprint_id(compiler, validator):
    """Test that blueprint ID is preserved in compiled agent."""
    blueprint = {
        "name": "Test Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    result = validator.validate(blueprint)
    blueprint_id = result.blueprint_id
    
    # Add the blueprint_id to the normalized blueprint
    normalized = result.normalized_blueprint
    normalized["id"] = blueprint_id
    
    compiled_agent = compiler.compile(normalized)
    
    assert compiled_agent.blueprint_id == blueprint_id
