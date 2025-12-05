#!/usr/bin/env python3
"""
Test Team Mode Validation and Compilation (No API Keys Required)

This script tests the team mode validation and compilation without making actual API calls.
Perfect for testing the implementation without needing API keys.

Usage:
    poetry run python examples/test_team_validation.py
"""

from pathlib import Path
from frankenagent.config.loader import BlueprintLoader
from frankenagent.compiler.validator import BlueprintValidator
from frankenagent.compiler.compiler import AgentCompiler, TEAM_AVAILABLE


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_team_validation():
    """Test team mode validation and compilation."""
    
    print_section("🧪 Team Mode Validation Test")
    
    if not TEAM_AVAILABLE:
        print("❌ ERROR: Agno Team not available")
        print("   Install with: poetry add agno")
        return False
    
    print("✅ Agno Team is available\n")
    
    # Test 1: Load and validate the research team blueprint
    print_section("Test 1: Load Research Team Blueprint")
    
    loader = BlueprintLoader()
    blueprint_path = Path("blueprints/research_team.yaml")
    
    if not blueprint_path.exists():
        print(f"❌ Blueprint not found at {blueprint_path}")
        return False
    
    try:
        blueprint = loader.load_from_file(str(blueprint_path))
        print(f"✅ Blueprint loaded: {blueprint.name}")
        print(f"   Execution mode: {blueprint.legs.execution_mode}")
        print(f"   Team members: {len(blueprint.legs.team_members)}")
        
        for i, member in enumerate(blueprint.legs.team_members, 1):
            print(f"\n   Member {i}: {member.name}")
            print(f"      Role: {member.role}")
            print(f"      Model: {member.head.provider}/{member.head.model}")
            print(f"      Tools: {len(member.arms)}")
            if member.arms:
                for arm in member.arms:
                    print(f"         - {arm.type}")
    
    except Exception as e:
        print(f"❌ Failed to load blueprint: {e}")
        return False
    
    # Test 2: Validate the blueprint
    print_section("Test 2: Validate Blueprint")
    
    validator = BlueprintValidator()
    
    # Convert to dict for validation
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
                        "temperature": member.head.temperature,
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
            "max_tool_calls": blueprint.spine.max_tool_calls,
            "timeout_seconds": blueprint.spine.timeout_seconds,
        },
    }
    
    result = validator.validate(blueprint_dict)
    
    if result.valid:
        print("✅ Blueprint is valid")
        print(f"   Blueprint ID: {result.blueprint_id}")
        print(f"   Normalized: {result.normalized_blueprint is not None}")
    else:
        print("❌ Blueprint validation failed:")
        for error in result.errors:
            print(f"   - {error.field}: {error.message}")
        return False
    
    # Test 3: Compile the blueprint
    print_section("Test 3: Compile Blueprint to Team")
    
    compiler = AgentCompiler()
    
    try:
        compiled = compiler.compile(result.normalized_blueprint)
        print("✅ Blueprint compiled successfully")
        print(f"   Type: {type(compiled.agent).__name__}")
        print(f"   Is team: {compiled.is_team}")
        print(f"   Blueprint ID: {compiled.blueprint_id}")
        print(f"   Guardrails:")
        print(f"      - Max tool calls: {compiled.guardrails['max_tool_calls']}")
        print(f"      - Timeout: {compiled.guardrails['timeout_seconds']}s")
        
        # Check team members
        if hasattr(compiled.agent, 'members'):
            print(f"\n   Team members: {len(compiled.agent.members)}")
            for i, member in enumerate(compiled.agent.members, 1):
                tools_count = len(member.tools) if member.tools else 0
                print(f"      {i}. {member.name}")
                print(f"         Role: {member.role}")
                print(f"         Tools: {tools_count}")
    
    except Exception as e:
        print(f"❌ Compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test invalid team configurations
    print_section("Test 4: Test Invalid Configurations")
    
    # Test 4a: Team without members
    print("Test 4a: Team without members (should fail)")
    invalid_blueprint = {
        "name": "Empty Team",
        "head": {"provider": "openai", "model": "gpt-4o-mini"},
        "legs": {"execution_mode": "team", "team_members": []},
    }
    result = validator.validate(invalid_blueprint)
    if not result.valid:
        print(f"   ✅ Correctly rejected: {result.errors[0].message}")
    else:
        print("   ❌ Should have failed validation")
        return False
    
    # Test 4b: Team member without head
    print("\nTest 4b: Team member without head (should fail)")
    invalid_blueprint2 = {
        "name": "Headless Team",
        "head": {"provider": "openai", "model": "gpt-4o-mini"},
        "legs": {
            "execution_mode": "team",
            "team_members": [
                {"name": "Agent1", "role": "Worker", "arms": []}
            ],
        },
    }
    result = validator.validate(invalid_blueprint2)
    if not result.valid:
        print(f"   ✅ Correctly rejected: {result.errors[0].message}")
    else:
        print("   ❌ Should have failed validation")
        return False
    
    # Test 4c: Team member with invalid tool
    print("\nTest 4c: Team member with invalid tool (should fail)")
    invalid_blueprint3 = {
        "name": "Invalid Tool Team",
        "head": {"provider": "openai", "model": "gpt-4o-mini"},
        "legs": {
            "execution_mode": "team",
            "team_members": [
                {
                    "name": "Agent1",
                    "role": "Worker",
                    "head": {"provider": "openai", "model": "gpt-4o-mini"},
                    "arms": [{"type": "invalid_tool", "config": {}}],
                }
            ],
        },
    }
    result = validator.validate(invalid_blueprint3)
    if not result.valid:
        print(f"   ✅ Correctly rejected: {result.errors[0].message}")
    else:
        print("   ❌ Should have failed validation")
        return False
    
    print_section("🎉 All Tests Passed!")
    print("Team mode is working correctly:")
    print("  ✅ Blueprint loading")
    print("  ✅ Validation")
    print("  ✅ Compilation to Agno Team")
    print("  ✅ Error handling")
    print("\nYou can now test with real API calls using:")
    print("  poetry run python examples/test_research_team.py")
    
    return True


if __name__ == "__main__":
    success = test_team_validation()
    exit(0 if success else 1)
