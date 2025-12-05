"""Tests for blueprint validator."""

import pytest
from frankenagent.compiler.validator import BlueprintValidator, ValidationResult


def test_valid_simple_blueprint():
    """Test that a valid simple blueprint passes validation."""
    validator = BlueprintValidator()
    
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
    
    result = validator.validate(blueprint)
    
    assert result.valid is True
    assert len(result.errors) == 0
    assert result.blueprint_id is not None
    assert result.blueprint_id.startswith("bp_")
    assert result.normalized_blueprint is not None


def test_valid_blueprint_with_tools():
    """Test that a valid blueprint with tools passes validation."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Search Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a research assistant",
            "temperature": 0.7
        },
        "arms": [
            {
                "type": "tavily_search",
                "config": {"max_results": 5}
            }
        ],
        "legs": {
            "execution_mode": "single_agent"
        },
        "spine": {
            "max_tool_calls": 3,
            "timeout_seconds": 30
        }
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is True
    assert len(result.errors) == 0


def test_missing_required_head():
    """Test that missing head field returns validation error."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Invalid",
        "legs": {"execution_mode": "single_agent"}
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is False
    assert len(result.errors) > 0
    assert any(error.field == "head" for error in result.errors)


def test_missing_required_legs():
    """Test that missing legs field returns validation error."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Invalid",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        }
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is False
    assert len(result.errors) > 0
    assert any(error.field == "legs" for error in result.errors)


def test_unsupported_provider():
    """Test that unsupported provider returns validation error."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Invalid",
        "head": {
            "provider": "unsupported",
            "model": "some-model"
        },
        "legs": {"execution_mode": "single_agent"}
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is False
    assert any("provider" in error.field for error in result.errors)


def test_unsupported_model():
    """Test that unsupported model returns validation error."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Invalid",
        "head": {
            "provider": "openai",
            "model": "unsupported-model"
        },
        "legs": {"execution_mode": "single_agent"}
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is False
    assert any("model" in error.field for error in result.errors)


def test_unsupported_tool_type():
    """Test that unsupported tool type returns validation error."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Invalid",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "arms": [
            {"type": "unsupported_tool"}
        ],
        "legs": {"execution_mode": "single_agent"}
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is False
    assert any("arms" in error.field and "type" in error.field for error in result.errors)


def test_invalid_guardrail_max_tool_calls():
    """Test that invalid max_tool_calls returns validation error."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Invalid",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "legs": {"execution_mode": "single_agent"},
        "spine": {
            "max_tool_calls": -1
        }
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is False
    assert any("max_tool_calls" in error.field for error in result.errors)


def test_invalid_guardrail_timeout():
    """Test that invalid timeout_seconds returns validation error."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Invalid",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "legs": {"execution_mode": "single_agent"},
        "spine": {
            "timeout_seconds": 0
        }
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is False
    assert any("timeout_seconds" in error.field for error in result.errors)


def test_blueprint_normalization():
    """Test that blueprint normalization adds defaults."""
    validator = BlueprintValidator()
    
    blueprint = {
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "legs": {}
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is True
    normalized = result.normalized_blueprint
    
    # Check defaults were added
    assert normalized["name"] == "Unnamed Agent"
    assert normalized["head"]["system_prompt"] == "You are a helpful assistant"
    assert normalized["head"]["temperature"] == 0.7
    assert normalized["legs"]["execution_mode"] == "single_agent"
    assert normalized["heart"]["memory_enabled"] is False
    assert normalized["spine"]["max_tool_calls"] == 10
    assert normalized["spine"]["timeout_seconds"] == 60


def test_blueprint_id_generation():
    """Test that blueprint ID is generated consistently."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Test Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "legs": {"execution_mode": "single_agent"}
    }
    
    result1 = validator.validate(blueprint)
    result2 = validator.validate(blueprint)
    
    # Same blueprint should generate same ID
    assert result1.blueprint_id == result2.blueprint_id


def test_anthropic_provider():
    """Test that Anthropic provider is supported."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Claude Agent",
        "head": {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022"
        },
        "legs": {"execution_mode": "single_agent"}
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is True
    assert len(result.errors) == 0


def test_invalid_temperature_range():
    """Test that temperature outside valid range returns error."""
    validator = BlueprintValidator()
    
    blueprint = {
        "name": "Invalid",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 3.0
        },
        "legs": {"execution_mode": "single_agent"}
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid is False
    assert any("temperature" in error.field for error in result.errors)
