---
inclusion: fileMatch
fileMatchPattern: "**/compiler/**/*.py"
---

# Blueprint Compiler Implementation Patterns

## Compiler Architecture

The compiler transforms Agent Blueprints into runnable Agno agents through a multi-step process:

1. **Parse Blueprint** → Validated AgentBlueprint object
2. **Build Tools** → List of Agno tool instances
3. **Configure LLM** → Model and provider settings
4. **Set Memory** → Memory configuration
5. **Apply Guardrails** → Wrap with constraints
6. **Create Agent** → Final Agno Agent/Workflow/Team

## Core Compiler Class

```python
from agno import Agent, Workflow, Team
from frankenagent.config.loader import AgentBlueprint
from frankenagent.tools.registry import ToolRegistry

class BlueprintCompiler:
    def __init__(self):
        self.tool_registry = ToolRegistry()
    
    def compile(self, blueprint: AgentBlueprint) -> Agent | Workflow | Team:
        """Main compilation entry point"""
        if blueprint.legs.execution_mode == "single_agent":
            return self._build_single_agent(blueprint)
        elif blueprint.legs.execution_mode == "workflow":
            return self._build_workflow(blueprint)
        elif blueprint.legs.execution_mode == "team":
            return self._build_team(blueprint)
        else:
            raise ValueError(f"Unknown execution mode: {blueprint.legs.execution_mode}")
```

## Tool Building Pattern

```python
def _build_tools(self, arms: List[ArmConfig]) -> List[Any]:
    """Convert arm configs to Agno tool instances"""
    tools = []
    for arm in arms:
        try:
            tool = self.tool_registry.get_tool(arm.type, arm.config)
            tools.append(tool)
        except Exception as e:
            raise CompilationError(
                f"Failed to build tool '{arm.name}' of type '{arm.type}': {e}"
            )
    return tools
```

## Single Agent Pattern

```python
def _build_single_agent(self, blueprint: AgentBlueprint) -> Agent:
    """Build single agent from blueprint"""
    tools = self._build_tools(blueprint.arms)
    
    agent = Agent(
        name=blueprint.name,
        model=blueprint.head.model,
        instructions=blueprint.head.system_prompt,
        temperature=blueprint.head.temperature,
        tools=tools,
        memory=self._build_memory(blueprint.heart),
        markdown=True
    )
    
    # Wrap with guardrails
    return self._apply_guardrails(agent, blueprint.spine)
```

## Workflow Pattern

```python
def _build_workflow(self, blueprint: AgentBlueprint) -> Workflow:
    """Build workflow from blueprint"""
    tools = self._build_tools(blueprint.arms)
    
    # Create workflow with steps
    workflow = Workflow(
        name=blueprint.name,
        model=blueprint.head.model,
        instructions=blueprint.head.system_prompt,
        tools=tools,
        steps=blueprint.legs.workflow_steps,
        memory=self._build_memory(blueprint.heart)
    )
    
    return self._apply_guardrails(workflow, blueprint.spine)
```

## Team Pattern

```python
def _build_team(self, blueprint: AgentBlueprint) -> Team:
    """Build team from blueprint"""
    members = []
    
    for member_config in blueprint.legs.team_members:
        # Build tools for this member
        member_tools = []
        for tool_name in member_config.get("tools", []):
            # Find tool config in arms
            arm = next((a for a in blueprint.arms if a.name == tool_name), None)
            if arm:
                tool = self.tool_registry.get_tool(arm.type, arm.config)
                member_tools.append(tool)
        
        # Create member agent
        member = Agent(
            name=member_config["name"],
            role=member_config["role"],
            model=blueprint.head.model,
            tools=member_tools
        )
        members.append(member)
    
    # Create team
    team = Team(
        name=blueprint.name,
        members=members,
        instructions=blueprint.head.system_prompt,
        memory=self._build_memory(blueprint.heart)
    )
    
    return self._apply_guardrails(team, blueprint.spine)
```

## Memory Configuration

```python
def _build_memory(self, heart: HeartConfig) -> Any:
    """Build memory configuration from heart"""
    memory_type = heart.memory.get("type", "conversation")
    
    if memory_type == "conversation":
        from agno.memory import ConversationMemory
        return ConversationMemory(
            max_messages=heart.memory.get("max_messages", 20)
        )
    elif memory_type == "shared":
        from agno.memory import SharedMemory
        return SharedMemory()
    else:
        return None
```

## Guardrails Application

```python
def _apply_guardrails(self, agent: Agent, spine: SpineConfig) -> Agent:
    """Wrap agent with guardrail constraints"""
    from frankenagent.runtime.guardrails import GuardrailWrapper
    
    return GuardrailWrapper(
        agent=agent,
        max_tool_calls=spine.max_tool_calls,
        timeout_seconds=spine.timeout_seconds,
        allowed_domains=spine.allowed_domains
    )
```

## Error Handling

Always wrap compilation steps with descriptive errors:

```python
class CompilationError(Exception):
    """Raised when blueprint compilation fails"""
    pass

try:
    agent = compiler.compile(blueprint)
except CompilationError as e:
    logger.error(f"Compilation failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected compilation error: {e}")
    raise CompilationError(f"Unexpected error during compilation: {e}")
```

## Testing Compilation

Test each execution mode separately:

```python
def test_compile_single_agent():
    blueprint = AgentBlueprint(
        name="Test Agent",
        head=HeadConfig(model="gpt-4", provider="openai", system_prompt="Test"),
        legs=LegsConfig(execution_mode="single_agent")
    )
    
    compiler = BlueprintCompiler()
    agent = compiler.compile(blueprint)
    
    assert isinstance(agent, Agent)
    assert agent.name == "Test Agent"
```

## Agno API Reference

Key Agno classes and their parameters:

- `Agent(name, model, instructions, tools, memory, temperature, markdown)`
- `Workflow(name, model, instructions, tools, steps, memory)`
- `Team(name, members, instructions, memory)`

Refer to Agno documentation for complete API details.
