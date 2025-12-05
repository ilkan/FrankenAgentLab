"""Test team mode execution with a real use case."""

import pytest
import asyncio
from pathlib import Path
from frankenagent.config.loader import BlueprintLoader
from frankenagent.compiler.compiler import AgentCompiler, TEAM_AVAILABLE
from frankenagent.runtime.executor import ExecutionOrchestrator
from frankenagent.runtime.session_manager import SessionManager


@pytest.mark.skipif(not TEAM_AVAILABLE, reason="Agno Team not available")
def test_team_blueprint_loads():
    """Test that the research team blueprint loads correctly."""
    loader = BlueprintLoader()
    blueprint_path = Path("blueprints/research_team.yaml")
    
    assert blueprint_path.exists(), "Research team blueprint not found"
    
    blueprint = loader.load_from_file(str(blueprint_path))
    
    assert blueprint.name == "Research & Writing Team"
    assert blueprint.legs.execution_mode == "team"
    assert len(blueprint.legs.team_members) == 2
    
    # Check first member (Researcher)
    researcher = blueprint.legs.team_members[0]
    assert "Research Specialist" in researcher.name
    assert researcher.head.provider == "openai"
    assert len(researcher.arms) == 1
    assert researcher.arms[0].type == "tavily_search"
    
    # Check second member (Writer)
    writer = blueprint.legs.team_members[1]
    assert "Content Writer" in writer.name
    assert writer.head.provider == "openai"
    assert len(writer.arms) == 0


@pytest.mark.skipif(not TEAM_AVAILABLE, reason="Agno Team not available")
def test_team_blueprint_compiles():
    """Test that the research team blueprint compiles to a Team."""
    loader = BlueprintLoader()
    compiler = AgentCompiler()
    
    blueprint_path = Path("blueprints/research_team.yaml")
    blueprint = loader.load_from_file(str(blueprint_path))
    
    # Convert to dict for compilation
    blueprint_dict = {
        "name": blueprint.name,
        "head": {
            "provider": blueprint.head.provider,
            "model": blueprint.head.model,
            "system_prompt": blueprint.head.system_prompt,
            "temperature": blueprint.head.temperature,
            "max_tokens": blueprint.head.max_tokens,
        },
        "legs": {
            "execution_mode": blueprint.legs.execution_mode,
            "team_members": [
                {
                    "name": member.name,
                    "role": member.role,
                    "head": {
                        "provider": member.head.provider,
                        "model": member.head.model,
                        "system_prompt": member.head.system_prompt,
                        "temperature": member.head.temperature,
                        "max_tokens": member.head.max_tokens,
                    },
                    "arms": [
                        {"type": arm.type, "config": arm.config}
                        for arm in member.arms
                    ],
                }
                for member in blueprint.legs.team_members
            ],
        },
        "heart": {
            "memory_enabled": blueprint.heart.memory_enabled,
            "history_length": blueprint.heart.history_length,
        },
        "spine": {
            "max_tool_calls": blueprint.spine.max_tool_calls,
            "timeout_seconds": blueprint.spine.timeout_seconds,
        },
    }
    
    compiled = compiler.compile(blueprint_dict)
    
    assert compiled.is_team
    assert compiled.agent is not None
    assert hasattr(compiled.agent, 'members')
    assert len(compiled.agent.members) == 2
    
    # Check team members
    researcher = compiled.agent.members[0]
    assert "Research Specialist" in researcher.name
    assert researcher.tools is not None
    assert len(researcher.tools) > 0  # Should have Tavily search
    
    writer = compiled.agent.members[1]
    assert "Content Writer" in writer.name


@pytest.mark.skipif(not TEAM_AVAILABLE, reason="Agno Team not available")
@pytest.mark.asyncio
async def test_team_execution_mock():
    """Test team execution with a mock scenario (no actual API calls)."""
    from unittest.mock import Mock, AsyncMock, patch
    
    loader = BlueprintLoader()
    compiler = AgentCompiler()
    session_manager = SessionManager()
    orchestrator = ExecutionOrchestrator(compiler, session_manager)
    
    blueprint_path = Path("blueprints/research_team.yaml")
    blueprint = loader.load_from_file(str(blueprint_path))
    
    # Convert to dict
    blueprint_dict = {
        "name": blueprint.name,
        "head": {
            "provider": blueprint.head.provider,
            "model": blueprint.head.model,
            "system_prompt": blueprint.head.system_prompt,
            "temperature": blueprint.head.temperature,
        },
        "legs": {
            "execution_mode": blueprint.legs.execution_mode,
            "team_members": [
                {
                    "name": member.name,
                    "role": member.role,
                    "head": {
                        "provider": member.head.provider,
                        "model": member.head.model,
                        "system_prompt": member.head.system_prompt,
                    },
                    "arms": [
                        {"type": arm.type, "config": arm.config}
                        for arm in member.arms
                    ],
                }
                for member in blueprint.legs.team_members
            ],
        },
        "spine": {
            "max_tool_calls": 20,
            "timeout_seconds": 120,
        },
    }
    
    # Mock the team's run method
    with patch.object(compiler, 'compile') as mock_compile:
        mock_team = Mock()
        mock_team.tools = []
        mock_team.members = [Mock(tools=[]), Mock(tools=[])]
        
        # Create mock response
        mock_response = Mock()
        mock_response.content = "Based on research, AI is transforming industries..."
        mock_team.arun = AsyncMock(return_value=mock_response)
        
        mock_compiled = Mock()
        mock_compiled.agent = mock_team
        mock_compiled.guardrails = {"max_tool_calls": 20, "timeout_seconds": 120}
        mock_compiled.is_team = True
        
        mock_compile.return_value = mock_compiled
        
        # Execute
        result = await orchestrator.execute(
            blueprint=blueprint_dict,
            message="Write an article about AI trends in 2025"
        )
        
        assert result.success
        assert result.response is not None
        assert len(result.response) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
