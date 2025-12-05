#!/usr/bin/env python3
"""
Test the Research & Writing Team

This script demonstrates team mode by having a research specialist and content writer
collaborate to create an article about a given topic.

Usage:
    poetry run python examples/test_research_team.py

Requirements:
    - OPENAI_API_KEY environment variable set
    - TAVILY_API_KEY environment variable set (for web search)
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from frankenagent.config.loader import BlueprintLoader
from frankenagent.compiler.compiler import AgentCompiler, TEAM_AVAILABLE
from frankenagent.runtime.executor import ExecutionOrchestrator
from frankenagent.runtime.session_manager import SessionManager


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


async def test_research_team():
    """Test the research team with a real query."""
    
    print_section("🧪 Testing Research & Writing Team")
    
    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️  WARNING: TAVILY_API_KEY not set")
        print("   The researcher won't be able to search the web.")
        print("   Set it with: export TAVILY_API_KEY='your-key-here'")
        print()
    
    if not TEAM_AVAILABLE:
        print("❌ ERROR: Agno Team not available")
        print("   Install with: poetry add agno")
        return
    
    # Load the blueprint
    print("📋 Loading research team blueprint...")
    loader = BlueprintLoader()
    blueprint_path = Path("blueprints/research_team.yaml")
    
    if not blueprint_path.exists():
        print(f"❌ ERROR: Blueprint not found at {blueprint_path}")
        return
    
    blueprint = loader.load_from_file(str(blueprint_path))
    print(f"✅ Loaded: {blueprint.name}")
    print(f"   Team members: {len(blueprint.legs.team_members)}")
    for i, member in enumerate(blueprint.legs.team_members, 1):
        tools_count = len(member.arms)
        print(f"   {i}. {member.name} - {tools_count} tool(s)")
    
    # Compile the blueprint
    print("\n🔧 Compiling team...")
    compiler = AgentCompiler()
    
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
    print(f"✅ Team compiled successfully")
    print(f"   Type: {type(compiled.agent).__name__}")
    print(f"   Members: {len(compiled.agent.members)}")
    
    # Execute the team
    print_section("🚀 Executing Team Task")
    
    # Test query
    query = "Write a brief article about the latest developments in AI agents and autonomous systems in 2025"
    print(f"📝 Query: {query}\n")
    
    session_manager = SessionManager()
    orchestrator = ExecutionOrchestrator(compiler, session_manager)
    
    print("⏳ Team is working (this may take 30-60 seconds)...\n")
    
    try:
        result = await orchestrator.execute(
            blueprint=blueprint_dict,
            message=query
        )
        
        if result.success:
            print_section("✅ Team Response")
            print(result.response)
            
            print_section("📊 Execution Metrics")
            print(f"Session ID: {result.session_id}")
            print(f"Total latency: {result.total_latency_ms}ms")
            print(f"Tool calls: {len(result.tool_calls)}")
            
            if result.tool_calls:
                print("\n🔧 Tool Usage:")
                for i, tool_call in enumerate(result.tool_calls, 1):
                    status = "✅" if tool_call.success else "❌"
                    print(f"   {i}. {status} {tool_call.tool} ({tool_call.duration_ms}ms)")
                    if tool_call.error:
                        print(f"      Error: {tool_call.error}")
            
            if result.guardrails_triggered:
                print(f"\n⚠️  Guardrails triggered: {result.guardrails_triggered}")
        
        else:
            print_section("❌ Execution Failed")
            print(f"Error: {result.error}")
            if result.guardrails_triggered:
                print(f"Guardrails triggered: {result.guardrails_triggered}")
    
    except Exception as e:
        print_section("❌ Execution Error")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print_section("🏁 Test Complete")


if __name__ == "__main__":
    asyncio.run(test_research_team())
