# Design Document

## Overview

FrankenAgent Lab MVP is a developer-focused system for composing AI agents using a Frankenstein-inspired metaphor. The system consists of:

1. **Agent Blueprint Schema** - A declarative config format expressing agent anatomy
2. **Config Loader & Validator** - Parses and validates blueprint files
3. **Compiler** - Transforms blueprints into runnable Agno agents
4. **Runtime Service** - Executes agents via CLI and HTTP API
5. **Minimal Web UI** - Simple interface for testing agents

The design preserves the conceptual "body parts" metaphor (head/arms/legs/heart/spine) while mapping cleanly to Agno's agent framework primitives.

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   CLI Tool   │  │  HTTP API    │  │  Web UI      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────┐
│                    Runtime Service                            │
│  ┌────────────────────────▼──────────────────────────┐       │
│  │         Agent Execution Orchestrator              │       │
│  │  - Load blueprint                                 │       │
│  │  - Compile to Agno agent                          │       │
│  │  - Execute with message                           │       │
│  │  - Capture execution trace                        │       │
│  └────────────┬──────────────────────┬────────────────┘      │
│               │                      │                        │
│  ┌────────────▼──────────┐  ┌───────▼────────────┐          │
│  │   Blueprint Compiler   │  │  Execution Logger  │          │
│  │  - Parse config        │  │  - Tool traces     │          │
│  │  - Map to Agno         │  │  - Timestamps      │          │
│  │  - Build agent         │  │  - Errors          │          │
│  └────────────┬───────────┘  └────────────────────┘          │
└───────────────┼──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│                   Config Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ Blueprint Loader │  │ Schema Validator │                 │
│  │ - YAML/JSON      │  │ - Pydantic       │                 │
│  │ - File I/O       │  │ - Type checking  │                 │
│  └──────────────────┘  └──────────────────┘                 │
└───────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────┐
│                      Agno Framework                            │
│  - Agent execution                                             │
│  - Tool management                                             │
│  - Memory systems                                              │
│  - Workflow orchestration                                      │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Blueprint Definition**: Developer creates YAML/JSON blueprint file
2. **Loading**: Config loader reads and parses the file
3. **Validation**: Schema validator checks structure and types
4. **Compilation**: Compiler maps blueprint to Agno agent configuration
5. **Execution**: Runtime service runs agent with user message
6. **Tracing**: Logger captures tool activations and results
7. **Response**: System returns agent output + execution trace

## Components and Interfaces

### 1. Agent Blueprint Schema

The blueprint uses a body-parts metaphor that maps to Agno primitives:

```yaml
# Example: simple_assistant.yaml
name: "Simple Assistant"
description: "A basic assistant with web search"
version: "1.0"

# HEAD = LLM Brain
head:
  model: "gpt-4"
  provider: "openai"
  system_prompt: "You are a helpful assistant."
  temperature: 0.7
  max_tokens: 2000

# ARMS = Tools & Integrations
arms:
  - name: "web_search"
    type: "tavily_search"
    config:
      api_key_env: "TAVILY_API_KEY"
  - name: "calculator"
    type: "python_eval"
    config:
      safe_mode: true

# LEGS = Execution Mode
legs:
  execution_mode: "single_agent"  # single_agent | workflow | team

# HEART = Memory & Knowledge
heart:
  memory:
    type: "conversation"
    max_messages: 20
  knowledge:
    enabled: false

# SPINE = Guardrails & Constraints
spine:
  max_tool_calls: 10
  timeout_seconds: 60
  allowed_domains: []
```

#### Mapping to Agno

| Blueprint Part | Agno Concept | Implementation |
|----------------|--------------|----------------|
| `head.model` | Agent model | `Agent(model=...)` |
| `head.system_prompt` | Agent instructions | `Agent(instructions=...)` |
| `arms[]` | Tools | `Agent(tools=[...])` |
| `legs.execution_mode=single_agent` | Single agent | `Agent(...)` |
| `legs.execution_mode=workflow` | Workflow | `Workflow(...)` |
| `legs.execution_mode=team` | Team | `Team(...)` |
| `heart.memory` | Memory | `Agent(memory=...)` |
| `spine.max_tool_calls` | Guardrails | Custom wrapper |

### 2. Config Loader & Validator

**Module**: `frankenagent/config/loader.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
import yaml
import json

class HeadConfig(BaseModel):
    model: str
    provider: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2000

class ArmConfig(BaseModel):
    name: str
    type: str
    config: Dict[str, Any] = {}

class LegsConfig(BaseModel):
    execution_mode: Literal["single_agent", "workflow", "team"]
    workflow_steps: List[str] = []
    team_members: List[Dict[str, Any]] = []

class HeartConfig(BaseModel):
    memory: Dict[str, Any] = {"type": "conversation", "max_messages": 20}
    knowledge: Dict[str, Any] = {"enabled": False}

class SpineConfig(BaseModel):
    max_tool_calls: int = 10
    timeout_seconds: int = 60
    allowed_domains: List[str] = []

class AgentBlueprint(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0"
    head: HeadConfig
    arms: List[ArmConfig] = []
    legs: LegsConfig
    heart: HeartConfig = HeartConfig()
    spine: SpineConfig = SpineConfig()

class BlueprintLoader:
    @staticmethod
    def load_from_file(path: str) -> AgentBlueprint:
        """Load and validate blueprint from YAML or JSON file"""
        pass
    
    @staticmethod
    def load_from_dict(data: dict) -> AgentBlueprint:
        """Load and validate blueprint from dictionary"""
        pass
```

### 3. Blueprint Compiler

**Module**: `frankenagent/compiler/compiler.py`

The compiler transforms blueprints into Agno agents:

```python
from agno import Agent, Workflow, Team
from frankenagent.config.loader import AgentBlueprint
from frankenagent.tools.registry import ToolRegistry

class BlueprintCompiler:
    def __init__(self):
        self.tool_registry = ToolRegistry()
    
    def compile(self, blueprint: AgentBlueprint) -> Agent | Workflow | Team:
        """
        Compile blueprint into runnable Agno agent
        
        Steps:
        1. Build tool instances from arms
        2. Configure LLM from head
        3. Set up memory from heart
        4. Apply guardrails from spine
        5. Create agent/workflow/team based on legs
        """
        pass
    
    def _build_tools(self, arms: List[ArmConfig]) -> List[Any]:
        """Convert arm configs to Agno tool instances"""
        pass
    
    def _build_single_agent(self, blueprint: AgentBlueprint) -> Agent:
        """Build single agent from blueprint"""
        pass
    
    def _build_workflow(self, blueprint: AgentBlueprint) -> Workflow:
        """Build workflow from blueprint"""
        pass
    
    def _build_team(self, blueprint: AgentBlueprint) -> Team:
        """Build team from blueprint"""
        pass
```

### 4. Tool Registry

**Module**: `frankenagent/tools/registry.py`

Maps tool types to Agno tool implementations:

```python
class ToolRegistry:
    """Registry mapping tool types to Agno tool classes"""
    
    TOOL_MAP = {
        "tavily_search": "agno.tools.tavily.TavilyTools",
        "python_eval": "agno.tools.python.PythonTools",
        "file_tools": "agno.tools.file.FileTools",
        "duckduckgo_search": "agno.tools.duckduckgo.DuckDuckGoTools",
    }
    
    def get_tool(self, tool_type: str, config: dict) -> Any:
        """Instantiate tool from type and config"""
        pass
```

### 5. Runtime Service

**Module**: `frankenagent/runtime/service.py`

Orchestrates agent execution with tracing:

```python
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class ToolTrace:
    tool_name: str
    timestamp: str
    inputs: Dict[str, Any]
    outputs: Any
    duration_ms: float

@dataclass
class ExecutionResult:
    response: str
    execution_trace: List[ToolTrace]
    total_duration_ms: float
    error: str = None

class RuntimeService:
    def __init__(self, blueprints_dir: str = "./blueprints"):
        self.blueprints_dir = blueprints_dir
        self.compiler = BlueprintCompiler()
        self.loader = BlueprintLoader()
    
    def execute(self, blueprint_id: str, message: str) -> ExecutionResult:
        """
        Execute agent from blueprint with message
        
        Steps:
        1. Load blueprint by ID
        2. Compile to Agno agent
        3. Wrap agent with tracing
        4. Execute with message
        5. Capture tool activations
        6. Return result + trace
        """
        pass
    
    def _wrap_with_tracing(self, agent: Agent) -> Agent:
        """Wrap agent to capture tool calls"""
        pass
```

### 6. CLI Interface

**Module**: `frankenagent/cli/main.py`

```python
import click
from frankenagent.runtime.service import RuntimeService

@click.group()
def cli():
    """FrankenAgent Lab CLI"""
    pass

@cli.command()
@click.argument('blueprint_path')
@click.argument('message')
def run(blueprint_path: str, message: str):
    """Run agent from blueprint file"""
    pass

@cli.command()
def list_blueprints():
    """List available blueprints"""
    pass

if __name__ == '__main__':
    cli()
```

Usage:
```bash
# Run agent
frankenagent run blueprints/simple_assistant.yaml "What is the weather?"

# List blueprints
frankenagent list
```

### 7. HTTP API

**Module**: `frankenagent/api/server.py`

FastAPI server for HTTP access:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from frankenagent.runtime.service import RuntimeService

app = FastAPI(title="FrankenAgent Lab API")
runtime = RuntimeService()

class ExecuteRequest(BaseModel):
    blueprint_id: str
    message: str

class ExecuteResponse(BaseModel):
    response: str
    execution_trace: List[Dict]
    duration_ms: float

@app.post("/execute", response_model=ExecuteResponse)
async def execute_agent(request: ExecuteRequest):
    """Execute agent from blueprint"""
    pass

@app.get("/blueprints")
async def list_blueprints():
    """List available blueprints"""
    pass

@app.get("/blueprints/{blueprint_id}")
async def get_blueprint(blueprint_id: str):
    """Get blueprint details"""
    pass
```

API Endpoints:
- `POST /execute` - Execute agent with message
- `GET /blueprints` - List available blueprints
- `GET /blueprints/{id}` - Get blueprint details

### 8. Minimal Web UI

**Module**: `frankenagent/ui/static/index.html`

Simple single-page app:

```html
<!DOCTYPE html>
<html>
<head>
    <title>FrankenAgent Lab</title>
    <style>
        body { font-family: monospace; max-width: 800px; margin: 50px auto; }
        .blueprint-list { margin: 20px 0; }
        .blueprint-item { padding: 10px; border: 1px solid #ccc; margin: 5px 0; cursor: pointer; }
        .blueprint-item:hover { background: #f0f0f0; }
        .chat-container { margin-top: 20px; }
        .message-input { width: 100%; padding: 10px; margin: 10px 0; }
        .response { background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .trace { background: #fff3e0; padding: 10px; margin: 10px 0; font-size: 12px; }
        .trace-item { margin: 5px 0; padding: 5px; border-left: 3px solid #ff9800; }
    </style>
</head>
<body>
    <h1>🧟 FrankenAgent Lab</h1>
    
    <div class="blueprint-list">
        <h2>Available Blueprints</h2>
        <div id="blueprints"></div>
    </div>
    
    <div class="chat-container" id="chat" style="display:none;">
        <h2>Chat with: <span id="selected-blueprint"></span></h2>
        <input type="text" class="message-input" id="message" placeholder="Enter your message...">
        <button onclick="sendMessage()">Send</button>
        <div id="responses"></div>
    </div>
    
    <script>
        let selectedBlueprint = null;
        
        // Load blueprints on page load
        async function loadBlueprints() { /* ... */ }
        
        // Select blueprint
        function selectBlueprint(id) { /* ... */ }
        
        // Send message to agent
        async function sendMessage() { /* ... */ }
        
        // Display response and trace
        function displayResponse(data) { /* ... */ }
        
        loadBlueprints();
    </script>
</body>
</html>
```

UI Features:
- List of available blueprints
- Click to select blueprint
- Text input for messages
- Display agent responses
- Show execution trace with tool activations

## Data Models

### Blueprint Storage

Blueprints stored as files in `blueprints/` directory:

```
blueprints/
├── simple_assistant.yaml
├── research_workflow.yaml
└── team_analyzer.yaml
```

Blueprint ID = filename without extension

### Execution Trace Format

```json
{
  "response": "The weather in San Francisco is...",
  "execution_trace": [
    {
      "tool_name": "web_search",
      "timestamp": "2025-11-15T10:30:45.123Z",
      "inputs": {
        "query": "weather San Francisco"
      },
      "outputs": {
        "results": [...]
      },
      "duration_ms": 234.5
    }
  ],
  "total_duration_ms": 1250.3
}
```

## Error Handling

### Error Types

1. **Blueprint Not Found** - Return 404 with file path
2. **Validation Error** - Return 400 with field-level errors
3. **Compilation Error** - Return 500 with compilation details
4. **Execution Error** - Return 500 with agent error
5. **Guardrail Violation** - Return 429 with limit details

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Blueprint validation failed",
  "details": {
    "field": "head.model",
    "issue": "Field required"
  }
}
```

## Testing Strategy

### Unit Tests

- Blueprint schema validation
- Config loader (YAML/JSON parsing)
- Compiler mapping logic
- Tool registry lookups
- Guardrail enforcement

### Integration Tests

- End-to-end blueprint compilation
- Agent execution with mock tools
- CLI command execution
- API endpoint responses
- Trace capture accuracy

### Example Blueprints as Tests

Use example blueprints as integration test fixtures:
- `simple_assistant.yaml` - Single agent with 1 tool
- `research_workflow.yaml` - Workflow with multiple steps
- `team_analyzer.yaml` - Team with multiple agents

## Folder Structure

```
frankenagent-lab/
├── frankenagent/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py          # Blueprint loading & validation
│   │   └── schema.py           # Pydantic models
│   ├── compiler/
│   │   ├── __init__.py
│   │   └── compiler.py         # Blueprint → Agno compiler
│   ├── tools/
│   │   ├── __init__.py
│   │   └── registry.py         # Tool type registry
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── service.py          # Execution orchestrator
│   │   └── tracing.py          # Tool trace capture
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py             # CLI commands
│   ├── api/
│   │   ├── __init__.py
│   │   └── server.py           # FastAPI server
│   └── ui/
│       └── static/
│           └── index.html      # Minimal web UI
├── blueprints/
│   ├── simple_assistant.yaml
│   ├── research_workflow.yaml
│   └── team_analyzer.yaml
├── tests/
│   ├── test_loader.py
│   ├── test_compiler.py
│   ├── test_runtime.py
│   └── test_api.py
├── pyproject.toml
├── README.md
└── .env.example
```

## Example Blueprints

### 1. Simple Assistant (single_agent)

```yaml
name: "Simple Assistant"
description: "Basic assistant with web search"
version: "1.0"

head:
  model: "gpt-4o-mini"
  provider: "openai"
  system_prompt: "You are a helpful assistant."
  temperature: 0.7

arms:
  - name: "web_search"
    type: "tavily_search"
    config:
      api_key_env: "TAVILY_API_KEY"

legs:
  execution_mode: "single_agent"

heart:
  memory:
    type: "conversation"
    max_messages: 20

spine:
  max_tool_calls: 5
  timeout_seconds: 30
```

### 2. Research Workflow (workflow)

```yaml
name: "Research Workflow"
description: "Multi-step research agent"
version: "1.0"

head:
  model: "gpt-4"
  provider: "openai"
  system_prompt: "You are a research assistant."
  temperature: 0.5

arms:
  - name: "web_search"
    type: "tavily_search"
  - name: "file_writer"
    type: "file_tools"

legs:
  execution_mode: "workflow"
  workflow_steps:
    - "search_and_gather"
    - "analyze_results"
    - "write_summary"

heart:
  memory:
    type: "conversation"

spine:
  max_tool_calls: 15
  timeout_seconds: 120
```

### 3. Team Analyzer (team)

```yaml
name: "Analysis Team"
description: "Team of specialized agents"
version: "1.0"

head:
  model: "gpt-4"
  provider: "openai"
  system_prompt: "You coordinate a team of analysts."
  temperature: 0.7

arms:
  - name: "web_search"
    type: "tavily_search"
  - name: "calculator"
    type: "python_eval"

legs:
  execution_mode: "team"
  team_members:
    - name: "researcher"
      role: "Research and gather information"
      tools: ["web_search"]
    - name: "analyst"
      role: "Analyze data and calculate metrics"
      tools: ["calculator"]

heart:
  memory:
    type: "shared"

spine:
  max_tool_calls: 20
  timeout_seconds: 180
```

## Future Compatibility

The design preserves extensibility for future features:

### Drag-and-Drop Canvas (Future)

- Blueprint schema remains unchanged
- Canvas UI generates blueprint JSON
- Visual "body parts" map to config sections
- Compiler and runtime unchanged

### Additional Body Parts (Future)

- **Skin** (integrations): Add `skin` section to schema
- **Eyes** (sensors): Add `eyes` section for inputs
- **Voice** (output modes): Add `voice` section for responses

### Multi-User (Future)

- Add user_id to blueprint metadata
- Store blueprints in database instead of files
- Add authentication layer to API

## Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"
agno = "^0.1.0"
pydantic = "^2.0"
pyyaml = "^6.0"
click = "^8.1"
fastapi = "^0.104"
uvicorn = "^0.24"
python-dotenv = "^1.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
httpx = "^0.25"
```

## Configuration

Environment variables (`.env`):

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Tool API Keys
TAVILY_API_KEY=tvly-...

# Runtime Config
BLUEPRINTS_DIR=./blueprints
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

## Deployment (MVP)

For MVP, local development only:

```bash
# Install dependencies
poetry install

# Run CLI
poetry run frankenagent run blueprints/simple_assistant.yaml "Hello"

# Run API server
poetry run uvicorn frankenagent.api.server:app --reload

# Access UI
open http://localhost:8000/static/index.html
```

Production deployment is out of scope for MVP.
