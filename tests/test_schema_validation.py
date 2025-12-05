"""Tests for enhanced blueprint schema validation.

This module tests the validation rules for all component configurations:
- HeadConfig: system_prompt length, temperature range, max_tokens
- ArmConfig: tool-specific config parameters
- LegsConfig: execution mode requirements
- HeartConfig: history_length range
- SpineConfig: guardrail bounds and domain validation
"""

import pytest
from pydantic import ValidationError
from frankenagent.config.schema import (
    HeadConfig,
    ArmConfig,
    LegsConfig,
    HeartConfig,
    SpineConfig,
    AgentBlueprint
)


class TestHeadConfigValidation:
    """Tests for HeadConfig validation (Requirements 12.2, 12.3, 12.4)."""
    
    def test_valid_head_config(self):
        """Test that valid head configuration passes validation."""
        config = HeadConfig(
            provider="openai",
            model="gpt-4o",
            system_prompt="You are a helpful assistant",
            temperature=0.7,
            max_tokens=1000
        )
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
    
    def test_system_prompt_max_length(self):
        """Test that system_prompt exceeding 10000 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HeadConfig(
                provider="openai",
                model="gpt-4o",
                system_prompt="x" * 10001  # Exceeds limit
            )
        assert "system_prompt must not exceed 10000 characters" in str(exc_info.value)
    
    def test_system_prompt_at_max_length(self):
        """Test that system_prompt at exactly 10000 characters is accepted."""
        config = HeadConfig(
            provider="openai",
            model="gpt-4o",
            system_prompt="x" * 10000  # Exactly at limit
        )
        assert len(config.system_prompt) == 10000
    
    def test_temperature_below_range(self):
        """Test that temperature below 0.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HeadConfig(
                provider="openai",
                model="gpt-4o",
                temperature=-0.1
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()
    
    def test_temperature_above_range(self):
        """Test that temperature above 2.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HeadConfig(
                provider="openai",
                model="gpt-4o",
                temperature=2.1
            )
        assert "less than or equal to 2" in str(exc_info.value).lower()
    
    def test_temperature_at_boundaries(self):
        """Test that temperature at 0.0 and 2.0 is accepted."""
        config_min = HeadConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.0
        )
        assert config_min.temperature == 0.0
        
        config_max = HeadConfig(
            provider="openai",
            model="gpt-4o",
            temperature=2.0
        )
        assert config_max.temperature == 2.0
    
    def test_max_tokens_positive(self):
        """Test that max_tokens must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            HeadConfig(
                provider="openai",
                model="gpt-4o",
                max_tokens=0
            )
        assert "greater than 0" in str(exc_info.value).lower()
    
    def test_max_tokens_negative(self):
        """Test that negative max_tokens is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HeadConfig(
                provider="openai",
                model="gpt-4o",
                max_tokens=-100
            )
        assert "greater than 0" in str(exc_info.value).lower()


class TestArmConfigValidation:
    """Tests for ArmConfig validation (Requirements 14.1, 14.2, 14.3, 14.4)."""
    
    def test_valid_tavily_config(self):
        """Test that valid tavily_search configuration passes."""
        config = ArmConfig(
            type="tavily_search",
            config={
                "max_results": 5,
                "search_depth": "basic"
            }
        )
        assert config.type == "tavily_search"
        assert config.config["max_results"] == 5
        assert config.config["search_depth"] == "basic"
    
    def test_tavily_max_results_below_range(self):
        """Test that tavily max_results below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ArmConfig(
                type="tavily_search",
                config={"max_results": 0}
            )
        assert "max_results must be an integer between 1 and 10" in str(exc_info.value)
    
    def test_tavily_max_results_above_range(self):
        """Test that tavily max_results above 10 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ArmConfig(
                type="tavily_search",
                config={"max_results": 11}
            )
        assert "max_results must be an integer between 1 and 10" in str(exc_info.value)
    
    def test_tavily_max_results_at_boundaries(self):
        """Test that tavily max_results at 1 and 10 is accepted."""
        config_min = ArmConfig(
            type="tavily_search",
            config={"max_results": 1}
        )
        assert config_min.config["max_results"] == 1
        
        config_max = ArmConfig(
            type="tavily_search",
            config={"max_results": 10}
        )
        assert config_max.config["max_results"] == 10
    
    def test_tavily_invalid_search_depth(self):
        """Test that invalid search_depth is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ArmConfig(
                type="tavily_search",
                config={"search_depth": "invalid"}
            )
        assert 'search_depth must be "basic" or "advanced"' in str(exc_info.value)
    
    def test_tavily_valid_search_depths(self):
        """Test that both valid search_depth values are accepted."""
        config_basic = ArmConfig(
            type="tavily_search",
            config={"search_depth": "basic"}
        )
        assert config_basic.config["search_depth"] == "basic"
        
        config_advanced = ArmConfig(
            type="tavily_search",
            config={"search_depth": "advanced"}
        )
        assert config_advanced.config["search_depth"] == "advanced"
    
    def test_arm_config_preserves_order(self):
        """Test that multiple arm configs preserve order."""
        arms = [
            ArmConfig(type="tavily_search", config={}),
            ArmConfig(type="http_tool", config={}),
            ArmConfig(type="tavily_search", config={"max_results": 3})
        ]
        assert arms[0].type == "tavily_search"
        assert arms[1].type == "http_tool"
        assert arms[2].type == "tavily_search"
        assert arms[2].config["max_results"] == 3


class TestLegsConfigValidation:
    """Tests for LegsConfig validation (Requirements 15.1, 15.2, 15.3, 15.4)."""
    
    def test_single_agent_mode(self):
        """Test that single_agent mode works without additional fields."""
        config = LegsConfig(execution_mode="single_agent")
        assert config.execution_mode == "single_agent"
    
    def test_workflow_mode_requires_steps(self):
        """Test that workflow mode requires workflow_steps."""
        with pytest.raises(ValidationError) as exc_info:
            LegsConfig(execution_mode="workflow")
        assert "workflow execution_mode requires workflow_steps" in str(exc_info.value)
    
    def test_workflow_mode_with_steps(self):
        """Test that workflow mode works with workflow_steps."""
        config = LegsConfig(
            execution_mode="workflow",
            workflow_steps=["step1", "step2", "step3"]
        )
        assert config.execution_mode == "workflow"
        assert len(config.workflow_steps) == 3
    
    def test_workflow_mode_empty_steps(self):
        """Test that workflow mode rejects empty workflow_steps."""
        with pytest.raises(ValidationError) as exc_info:
            LegsConfig(
                execution_mode="workflow",
                workflow_steps=[]
            )
        assert "workflow" in str(exc_info.value).lower() and "workflow_steps" in str(exc_info.value).lower()
    
    def test_team_mode_requires_members(self):
        """Test that team mode requires team_members."""
        with pytest.raises(ValidationError) as exc_info:
            LegsConfig(execution_mode="team")
        assert "team execution_mode requires team_members" in str(exc_info.value)
    
    def test_team_mode_with_members(self):
        """Test that team mode works with team_members."""
        config = LegsConfig(
            execution_mode="team",
            team_members=[
                {"name": "researcher", "role": "research"},
                {"name": "writer", "role": "writing"}
            ]
        )
        assert config.execution_mode == "team"
        assert len(config.team_members) == 2
    
    def test_team_mode_empty_members(self):
        """Test that team mode rejects empty team_members."""
        with pytest.raises(ValidationError) as exc_info:
            LegsConfig(
                execution_mode="team",
                team_members=[]
            )
        assert "team" in str(exc_info.value).lower() and "team_members" in str(exc_info.value).lower()


class TestHeartConfigValidation:
    """Tests for HeartConfig validation (Requirements 16.1, 16.2)."""
    
    def test_valid_heart_config(self):
        """Test that valid heart configuration passes."""
        config = HeartConfig(
            memory_enabled=True,
            history_length=10,
            knowledge_enabled=False
        )
        assert config.memory_enabled is True
        assert config.history_length == 10
        assert config.knowledge_enabled is False
    
    def test_history_length_below_range(self):
        """Test that history_length below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HeartConfig(history_length=0)
        assert "greater than or equal to 1" in str(exc_info.value).lower()
    
    def test_history_length_above_range(self):
        """Test that history_length above 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HeartConfig(history_length=101)
        assert "less than or equal to 100" in str(exc_info.value).lower()
    
    def test_history_length_at_boundaries(self):
        """Test that history_length at 1 and 100 is accepted."""
        config_min = HeartConfig(history_length=1)
        assert config_min.history_length == 1
        
        config_max = HeartConfig(history_length=100)
        assert config_max.history_length == 100


class TestSpineConfigValidation:
    """Tests for SpineConfig validation (Requirements 17.1, 17.2, 17.3)."""
    
    def test_valid_spine_config(self):
        """Test that valid spine configuration passes."""
        config = SpineConfig(
            max_tool_calls=20,
            timeout_seconds=120,
            allowed_domains=["example.com", "api.example.com"]
        )
        assert config.max_tool_calls == 20
        assert config.timeout_seconds == 120
        assert len(config.allowed_domains) == 2
    
    def test_max_tool_calls_below_range(self):
        """Test that max_tool_calls below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SpineConfig(max_tool_calls=0)
        assert "greater than or equal to 1" in str(exc_info.value).lower()
    
    def test_max_tool_calls_above_range(self):
        """Test that max_tool_calls above 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SpineConfig(max_tool_calls=101)
        assert "less than or equal to 100" in str(exc_info.value).lower()
    
    def test_max_tool_calls_at_boundaries(self):
        """Test that max_tool_calls at 1 and 100 is accepted."""
        config_min = SpineConfig(max_tool_calls=1)
        assert config_min.max_tool_calls == 1
        
        config_max = SpineConfig(max_tool_calls=100)
        assert config_max.max_tool_calls == 100
    
    def test_timeout_seconds_below_range(self):
        """Test that timeout_seconds below 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SpineConfig(timeout_seconds=0)
        assert "greater than or equal to 1" in str(exc_info.value).lower()
    
    def test_timeout_seconds_above_range(self):
        """Test that timeout_seconds above 300 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SpineConfig(timeout_seconds=301)
        assert "less than or equal to 300" in str(exc_info.value).lower()
    
    def test_timeout_seconds_at_boundaries(self):
        """Test that timeout_seconds at 1 and 300 is accepted."""
        config_min = SpineConfig(timeout_seconds=1)
        assert config_min.timeout_seconds == 1
        
        config_max = SpineConfig(timeout_seconds=300)
        assert config_max.timeout_seconds == 300
    
    def test_valid_domain_formats(self):
        """Test that valid domain formats are accepted."""
        config = SpineConfig(
            allowed_domains=[
                "example.com",
                "api.example.com",
                "sub.domain.example.co.uk"
            ]
        )
        assert len(config.allowed_domains) == 3
    
    def test_invalid_domain_format(self):
        """Test that invalid domain formats are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SpineConfig(allowed_domains=["not a domain"])
        assert "invalid domain format" in str(exc_info.value)
    
    def test_invalid_domain_with_protocol(self):
        """Test that domains with protocols are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SpineConfig(allowed_domains=["https://example.com"])
        assert "invalid domain format" in str(exc_info.value)
    
    def test_invalid_domain_with_path(self):
        """Test that domains with paths are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SpineConfig(allowed_domains=["example.com/path"])
        assert "invalid domain format" in str(exc_info.value)


class TestAgentBlueprintIntegration:
    """Integration tests for complete blueprint validation."""
    
    def test_complete_valid_blueprint(self):
        """Test that a complete valid blueprint passes all validations."""
        blueprint = AgentBlueprint(
            name="Test Agent",
            head=HeadConfig(
                provider="openai",
                model="gpt-4o",
                system_prompt="You are a test assistant",
                temperature=0.8,
                max_tokens=2000
            ),
            arms=[
                ArmConfig(
                    type="tavily_search",
                    config={"max_results": 5, "search_depth": "basic"}
                )
            ],
            legs=LegsConfig(execution_mode="single_agent"),
            heart=HeartConfig(
                memory_enabled=True,
                history_length=10
            ),
            spine=SpineConfig(
                max_tool_calls=20,
                timeout_seconds=120,
                allowed_domains=["example.com"]
            )
        )
        assert blueprint.name == "Test Agent"
        assert blueprint.head.provider == "openai"
        assert len(blueprint.arms) == 1
        assert blueprint.legs.execution_mode == "single_agent"
        assert blueprint.heart.memory_enabled is True
        assert blueprint.spine.max_tool_calls == 20
    
    def test_blueprint_with_workflow_mode(self):
        """Test blueprint with workflow execution mode."""
        blueprint = AgentBlueprint(
            name="Workflow Agent",
            head=HeadConfig(provider="openai", model="gpt-4o"),
            legs=LegsConfig(
                execution_mode="workflow",
                workflow_steps=["research", "analyze", "report"]
            )
        )
        assert blueprint.legs.execution_mode == "workflow"
        assert len(blueprint.legs.workflow_steps) == 3
    
    def test_blueprint_with_team_mode(self):
        """Test blueprint with team execution mode."""
        blueprint = AgentBlueprint(
            name="Team Agent",
            head=HeadConfig(provider="openai", model="gpt-4o"),
            legs=LegsConfig(
                execution_mode="team",
                team_members=[
                    {"name": "researcher"},
                    {"name": "writer"}
                ]
            )
        )
        assert blueprint.legs.execution_mode == "team"
        assert len(blueprint.legs.team_members) == 2
    
    def test_blueprint_with_multiple_validation_errors(self):
        """Test that multiple validation errors are caught."""
        with pytest.raises(ValidationError) as exc_info:
            AgentBlueprint(
                name="Invalid Agent",
                head=HeadConfig(
                    provider="openai",
                    model="gpt-4o",
                    temperature=3.0,  # Invalid
                    max_tokens=-100  # Invalid
                ),
                heart=HeartConfig(history_length=200),  # Invalid
                spine=SpineConfig(
                    max_tool_calls=200,  # Invalid
                    timeout_seconds=500  # Invalid
                )
            )
        error_str = str(exc_info.value)
        # Should contain multiple validation errors
        assert "validation error" in error_str.lower()
