# Example Blueprints

This directory contains example agent blueprints for testing and demonstration purposes.

## Available Blueprints

### 1. simple_assistant.yaml
**Purpose:** Basic OpenAI agent with web search capabilities

- **Model:** OpenAI GPT-4o
- **Tools:** Tavily Search
- **Memory:** Disabled
- **Guardrails:** 5 tool calls max, 30s timeout
- **Use Case:** General-purpose assistant for answering questions with web search

### 2. search_agent.yaml
**Purpose:** Research assistant optimized for web search

- **Model:** OpenAI GPT-4o
- **Tools:** Tavily Search (5 results, basic depth)
- **Memory:** Disabled
- **Guardrails:** 10 tool calls max, 60s timeout
- **Use Case:** In-depth research queries requiring multiple searches

### 3. memory_agent.yaml
**Purpose:** Conversational agent with conversation history

- **Model:** OpenAI GPT-4o
- **Tools:** Tavily Search
- **Memory:** Enabled (10 messages history)
- **Guardrails:** 8 tool calls max, 45s timeout
- **Use Case:** Multi-turn conversations where context matters

### 4. guardrails_test.yaml
**Purpose:** Agent with strict limits for testing guardrail enforcement

- **Model:** OpenAI GPT-3.5-turbo
- **Tools:** Tavily Search (3 results)
- **Memory:** Disabled
- **Guardrails:** 2 tool calls max, 15s timeout (STRICT)
- **Use Case:** Testing timeout and tool call limit violations

## Testing Blueprints

### Validate a Blueprint

```bash
poetry run python3 -c "
import yaml
from frankenagent.compiler.validator import BlueprintValidator

with open('blueprints/simple_assistant.yaml') as f:
    blueprint = yaml.safe_load(f)

validator = BlueprintValidator()
result = validator.validate(blueprint)

if result.valid:
    print(f'✓ Valid - ID: {result.blueprint_id}')
else:
    for error in result.errors:
        print(f'✗ {error.field}: {error.message}')
"
```

### Run an Agent via API

```bash
# Start the API server
poetry run uvicorn frankenagent.api.server:app --reload

# In another terminal, test the agent
curl -X POST http://localhost:8000/api/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint": <blueprint_json>,
    "message": "What is the weather today?"
  }'
```

## Blueprint Requirements

All blueprints must satisfy these requirements (from requirements.md):

- **Requirement 1.5:** Valid provider, model, and tool configurations
- **Requirement 2.5:** Proper execution mode (single_agent for MVP)
- **Requirement 3.1:** Tavily search tool with valid configuration
- **Requirement 6.1:** Memory configuration when enabled

## Supported Configurations

### Providers & Models
- **OpenAI:** gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- **Anthropic:** claude-3-5-sonnet-20241022, claude-3-opus-20240229, claude-3-sonnet-20240229

### Tools
- **tavily_search:** Web search via Tavily API
- **http_tool:** (Future) HTTP requests

### Execution Modes
- **single_agent:** Single agent execution (MVP)
- **workflow:** Sequential workflow (Future)
- **team:** Multi-agent team (Future)

## Adding New Blueprints

1. Create a new YAML file in this directory
2. Follow the blueprint schema (see design.md)
3. Validate using the validator
4. Test via API or CLI
5. Document in this README
