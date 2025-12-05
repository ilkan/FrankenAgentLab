---
inclusion: fileMatch
fileMatchPattern: "**/config/**/*.py"
---

# Agent Blueprint Schema Reference

## Schema Structure

Every Agent Blueprint must conform to this structure:

```yaml
name: string (required)
description: string (optional, default: "")
version: string (optional, default: "1.0")

head:
  model: string (required)
  provider: string (required)
  system_prompt: string (required)
  temperature: float (optional, default: 0.7)
  max_tokens: int (optional, default: 2000)

arms:
  - name: string (required)
    type: string (required)
    config: dict (optional, default: {})

legs:
  execution_mode: "single_agent" | "workflow" | "team" (required)
  workflow_steps: list[string] (optional, for workflow mode)
  team_members: list[dict] (optional, for team mode)

heart:
  memory:
    type: string (optional, default: "conversation")
    max_messages: int (optional, default: 20)
  knowledge:
    enabled: bool (optional, default: false)

spine:
  max_tool_calls: int (optional, default: 10)
  timeout_seconds: int (optional, default: 60)
  allowed_domains: list[string] (optional, default: [])
```

## Pydantic Model Implementation

Use Pydantic v2 with strict validation:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

class HeadConfig(BaseModel):
    model: str
    provider: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2000

class ArmConfig(BaseModel):
    name: str
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)

class LegsConfig(BaseModel):
    execution_mode: Literal["single_agent", "workflow", "team"]
    workflow_steps: List[str] = Field(default_factory=list)
    team_members: List[Dict[str, Any]] = Field(default_factory=list)

class HeartConfig(BaseModel):
    memory: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "conversation", "max_messages": 20}
    )
    knowledge: Dict[str, Any] = Field(
        default_factory=lambda: {"enabled": False}
    )

class SpineConfig(BaseModel):
    max_tool_calls: int = 10
    timeout_seconds: int = 60
    allowed_domains: List[str] = Field(default_factory=list)

class AgentBlueprint(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0"
    head: HeadConfig
    arms: List[ArmConfig] = Field(default_factory=list)
    legs: LegsConfig
    heart: HeartConfig = Field(default_factory=HeartConfig)
    spine: SpineConfig = Field(default_factory=SpineConfig)
```

## Validation Rules

1. **Required Fields**: name, head, legs.execution_mode
2. **Type Validation**: Pydantic handles type checking automatically
3. **Enum Validation**: execution_mode must be one of three values
4. **Default Values**: Apply sensible defaults for optional fields
5. **Error Messages**: Use Pydantic's built-in validation errors

## File Format Support

Support both YAML and JSON:

```python
def load_from_file(path: str) -> AgentBlueprint:
    with open(path, 'r') as f:
        if path.endswith('.yaml') or path.endswith('.yml'):
            data = yaml.safe_load(f)
        elif path.endswith('.json'):
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path}")
    
    return AgentBlueprint(**data)
```

## Supported Tool Types

Current tool registry mappings:

- `tavily_search` → Agno TavilyTools (web search)
- `http_tool` → Custom HTTP client (GET, POST, PUT, DELETE, PATCH requests)
- `python_eval` → Agno PythonTools (code execution)
- `file_tools` → Agno FileTools (file operations)
- `duckduckgo_search` → Agno DuckDuckGoTools (web search)

### HTTP Tool Configuration

The HTTP tool enables agents to make requests to external APIs:

```yaml
arms:
  - type: "http_tool"
    config:
      name: "API Client"
      description: "Make HTTP requests to external APIs"
      base_url: "https://api.example.com"  # Optional base URL
      default_headers:                      # Optional default headers
        Authorization: "Bearer token"
        Content-Type: "application/json"
      timeout: 30                           # Request timeout in seconds
```

When adding new tools, update `ToolRegistry.TOOL_MAP`.

## Execution Mode Details

### single_agent
- Creates a single Agno Agent
- All tools available to the agent
- Simple request-response flow

### workflow
- Creates Agno Workflow
- Requires `workflow_steps` list
- Sequential execution of steps
- Each step can use tools

### team
- Creates Agno Team
- Requires `team_members` list
- Each member is a specialized agent
- Tools can be assigned per member

## Example Blueprints

See `blueprints/` directory for complete examples:
- `simple_assistant.yaml` - Single agent example
- `research_workflow.yaml` - Workflow example
- `team_analyzer.yaml` - Team example
