---
inclusion: fileMatch
fileMatchPattern: '**/runtime/**/*.py'
---

# FrankenAgent Runtime Implementation Guide

## Overview

This guide provides specific patterns and best practices for implementing the FrankenAgent Lab agent runtime system. The runtime is responsible for validating blueprints, compiling them into Agno agents, executing them with guardrails, and providing comprehensive logging.

## Core Runtime Flow

```
Blueprint → Validate → Compile → Execute → Trace → Response
```

Never skip validation or bypass the compiler. Every execution must be traced.

## Key Components

### 1. Blueprint Validator (`frankenagent/compiler/validator.py`)

**Purpose**: Validate blueprint structure and values before compilation

**Key Patterns**:

```python
class BlueprintValidator:
    # Define supported options as class constants
    SUPPORTED_PROVIDERS = ["openai", "anthropic"]
    SUPPORTED_MODELS = {
        "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
    }
    SUPPORTED_TOOLS = ["tavily_search", "http_tool"]
    
    def validate(self, blueprint: dict) -> ValidationResult:
        """
        Validate blueprint and return normalized version or errors.
        
        Always return ValidationResult with:
        - valid: bool
        - errors: list of field-level errors
        - normalized_blueprint: cleaned/normalized version
        - blueprint_id: unique identifier
        """
        errors = []
        
        # Validate each section
        self._validate_head(blueprint, errors)
        self._validate_arms(blueprint, errors)
        self._validate_legs(blueprint, errors)
        self._validate_heart(blueprint, errors)
        self._validate_spine(blueprint, errors)
        
        if errors:
            return ValidationResult(valid=False, errors=errors)
        
        return ValidationResult(
            valid=True,
            normalized_blueprint=self._normalize(blueprint),
            blueprint_id=self._generate_id(blueprint)
        )
```

**Error Format**:
```python
{
    "field": "head.provider",
    "message": "Unsupported provider 'gpt'. Supported: ['openai', 'anthropic']"
}
```

### 2. Agent Compiler (`frankenagent/compiler/compiler.py`)

**Purpose**: Transform validated blueprints into Agno agents

**Key Patterns**:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

class AgentCompiler:
    def compile(self, blueprint: dict) -> CompiledAgent:
        """
        Compile validated blueprint into Agno Agent.
        
        CRITICAL: Never create agents in loops - reuse them!
        Create once, use many times.
        """
        # 1. Build model
        model = self._build_model(blueprint["head"])
        
        # 2. Build tools
        tools = self._build_tools(blueprint.get("arms", []))
        
        # 3. Build memory config
        memory_config = self._build_memory(blueprint.get("heart", {}))
        
        # 4. Create Agno Agent
        agent = Agent(
            model=model,
            instructions=blueprint["head"].get("system_prompt", "You are a helpful assistant"),
            tools=tools,
            markdown=True,  # Enable markdown formatting
            **memory_config
        )
        
        # 5. Wrap with guardrails
        return CompiledAgent(
            agent=agent,
            blueprint_id=blueprint.get("id"),
            guardrails=blueprint.get("spine", {})
        )
    
    def _build_model(self, head: dict):
        """Build Agno model from head config."""
        provider = head["provider"]
        model_id = head["model"]
        
        # Common parameters
        params = {
            "id": model_id,
            "temperature": head.get("temperature", 0.7)
        }
        
        if head.get("max_tokens"):
            params["max_tokens"] = head["max_tokens"]
        
        if provider == "openai":
            return OpenAIChat(**params)
        elif provider == "anthropic":
            return Claude(**params)
        else:
            raise CompilationError(f"Unsupported provider: {provider}")
```

**Memory Configuration**:
```python
def _build_memory(self, heart: dict) -> dict:
    """Build memory config from heart section."""
    memory_config = {}
    
    if heart.get("memory_enabled"):
        from agno.db.sqlite import SqliteDb
        
        # For MVP: SQLite
        # For production: PostgreSQL
        memory_config["db"] = SqliteDb(db_file="tmp/agents.db")
        memory_config["add_history_to_context"] = True
        memory_config["num_history_runs"] = heart.get("history_length", 5)
    
    return memory_config
```

### 3. Tool Registry (`frankenagent/tools/registry.py`)

**Purpose**: Map blueprint tool configs to Agno tool instances

**Key Patterns**:

```python
import os
from agno.tools.tavily import TavilyTools

class ToolRegistry:
    """Registry for creating Agno tools from blueprint configs."""
    
    def create_tool(self, arm_config: dict):
        """
        Create Agno tool from arm configuration.
        
        Args:
            arm_config: {"type": "tavily_search", "config": {...}}
        
        Returns:
            Agno tool instance
        """
        tool_type = arm_config["type"]
        config = arm_config.get("config", {})
        
        if tool_type == "tavily_search":
            return self._create_tavily_tool(config)
        elif tool_type == "http_tool":
            return self._create_http_tool(config)
        else:
            raise ValueError(f"Unsupported tool type: {tool_type}")
    
    def _create_tavily_tool(self, config: dict):
        """Create Tavily search tool."""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment")
        
        return TavilyTools(
            api_key=api_key,
            max_results=config.get("max_results", 5),
            search_depth=config.get("search_depth", "basic")
        )
```

**Adding New Tools**:
1. Add tool type to `SUPPORTED_TOOLS` in validator
2. Implement `_create_<tool>_tool` method
3. Handle API keys from environment
4. Add configuration validation

### 4. Execution Orchestrator (`frankenagent/runtime/executor.py`)

**Purpose**: Execute agents with guardrails and logging

**Key Patterns**:

```python
import asyncio
import time
from typing import Optional

class ExecutionOrchestrator:
    async def execute(
        self,
        blueprint: dict,
        message: str,
        session_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute agent with guardrails and logging.
        
        CRITICAL: Always enforce guardrails
        CRITICAL: Always log tool calls
        """
        start_time = time.time()
        
        # 1. Compile agent (or retrieve from cache)
        compiled_agent = self.compiler.compile(blueprint)
        
        # 2. Setup session
        if not session_id:
            session_id = self.session_manager.create_new_session()
        
        # Set user_id for Agno's built-in history
        compiled_agent.agent.user_id = session_id
        
        # 3. Execute with guardrails
        try:
            result = await self._execute_with_guardrails(
                compiled_agent.agent,
                message,
                compiled_agent.guardrails,
                session_id
            )
        except GuardrailViolation as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                guardrails_triggered=[e.guardrail_type],
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}",
                session_id=session_id
            )
        
        # 4. Calculate metrics
        total_latency = int((time.time() - start_time) * 1000)
        
        return ExecutionResult(
            success=True,
            response=result.content,
            tool_calls=self._extract_tool_calls(result),
            session_id=session_id,
            total_latency_ms=total_latency
        )
```

**Guardrail Enforcement**:
```python
async def _execute_with_guardrails(
    self,
    agent,
    message: str,
    guardrails: dict,
    session_id: str
):
    """Execute with timeout and tool call limits."""
    timeout = guardrails.get("timeout_seconds", 60)
    max_tool_calls = guardrails.get("max_tool_calls", 10)
    
    # Wrap with timeout
    try:
        result = await asyncio.wait_for(
            self._run_with_monitoring(agent, message, max_tool_calls, session_id),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        raise GuardrailViolation("timeout_seconds", f"Execution exceeded {timeout}s")
```

### 5. Session Manager (`frankenagent/runtime/session_manager.py`)

**Purpose**: Manage sessions and execution logs

**Key Patterns**:

```python
import uuid
from datetime import datetime

class SessionManager:
    def __init__(self):
        # For MVP: in-memory storage
        self.sessions = {}
        self.logs = {}
    
    def create_new_session(self) -> str:
        """Create new session with unique ID."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self.sessions[session_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "messages": []
        }
        self.logs[session_id] = []
        return session_id
    
    def log_tool_call(
        self,
        session_id: str,
        tool_name: str,
        args: dict,
        duration_ms: int,
        success: bool,
        result: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log tool call with all metadata."""
        if session_id not in self.logs:
            self.logs[session_id] = []
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "tool_call",
            "tool_name": tool_name,
            "args": args,
            "duration_ms": duration_ms,
            "success": success,
            "result": result[:200] if result else None,  # Truncate
            "error": error
        }
        
        self.logs[session_id].append(log_entry)
```

## Agno Best Practices for Runtime

### 1. Agent Reuse (CRITICAL)

```python
# WRONG - Creates agent every time (slow!)
for message in messages:
    agent = Agent(...)  # DON'T DO THIS
    agent.run(message)

# CORRECT - Create once, reuse
agent = Agent(...)
for message in messages:
    agent.run(message)
```

### 2. Memory Configuration

```python
# Enable conversation history
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="tmp/agents.db"),
    user_id=session_id,  # CRITICAL: Set user_id for history
    add_history_to_context=True,
    num_history_runs=5
)
```

### 3. Tool Integration

```python
from agno.tools.tavily import TavilyTools

# Tools are automatically described to the LLM
# The agent decides when to use them
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[
        TavilyTools(api_key=os.getenv("TAVILY_API_KEY"))
    ],
    instructions="You are a research assistant. Use search when needed."
)
```

### 4. Structured Output (Future)

```python
from pydantic import BaseModel

class SearchResult(BaseModel):
    summary: str
    sources: list[str]

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    output_schema=SearchResult
)

result: SearchResult = agent.run("Search for AI news").content
```

## Error Handling

### Exception Hierarchy

```python
class FrankenAgentError(Exception):
    """Base exception for all FrankenAgent errors"""
    pass

class ValidationError(FrankenAgentError):
    """Blueprint validation failed"""
    pass

class CompilationError(FrankenAgentError):
    """Blueprint compilation failed"""
    pass

class ExecutionError(FrankenAgentError):
    """Agent execution failed"""
    pass

class GuardrailViolation(FrankenAgentError):
    """Guardrail constraint violated"""
    def __init__(self, guardrail_type: str, message: str):
        self.guardrail_type = guardrail_type
        super().__init__(message)
```

### Error Handling Pattern

```python
try:
    result = await executor.execute(blueprint, message, session_id)
except ValidationError as e:
    return {"error": {"type": "ValidationError", "message": str(e)}}
except CompilationError as e:
    return {"error": {"type": "CompilationError", "message": str(e)}}
except GuardrailViolation as e:
    return {
        "error": {
            "type": "GuardrailViolation",
            "guardrail": e.guardrail_type,
            "message": str(e)
        }
    }
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return {"error": {"type": "InternalError", "message": "An unexpected error occurred"}}
```

## Logging Best Practices

### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log with context
logger.info(
    "Executing agent",
    extra={
        "blueprint_id": blueprint_id,
        "session_id": session_id,
        "message_length": len(message)
    }
)

# Log tool calls
logger.debug(
    "Tool call completed",
    extra={
        "tool_name": tool_name,
        "duration_ms": duration,
        "success": success
    }
)
```

### Log Levels

- `DEBUG`: Tool calls, compilation steps, detailed execution flow
- `INFO`: Agent execution start/complete, session creation
- `WARNING`: Guardrail warnings, retries, fallbacks
- `ERROR`: Execution failures, API errors, validation errors

## Testing Patterns

### Unit Tests

```python
import pytest
from frankenagent.compiler.validator import BlueprintValidator

def test_validate_valid_blueprint():
    validator = BlueprintValidator()
    blueprint = {
        "name": "Test Agent",
        "head": {"provider": "openai", "model": "gpt-4o"},
        "legs": {"execution_mode": "single_agent"}
    }
    
    result = validator.validate(blueprint)
    
    assert result.valid
    assert result.blueprint_id is not None
    assert result.errors == []

def test_validate_missing_head():
    validator = BlueprintValidator()
    blueprint = {"legs": {"execution_mode": "single_agent"}}
    
    result = validator.validate(blueprint)
    
    assert not result.valid
    assert any(e["field"] == "head" for e in result.errors)
```

### Integration Tests

```python
import pytest
from frankenagent.runtime.executor import ExecutionOrchestrator

@pytest.mark.asyncio
async def test_execute_with_tavily(executor, search_blueprint):
    """Test agent execution with Tavily search."""
    result = await executor.execute(
        blueprint=search_blueprint,
        message="What is the weather in San Francisco?"
    )
    
    assert result.success
    assert result.response is not None
    assert len(result.tool_calls) > 0
    assert result.tool_calls[0]["tool"] == "tavily_search"
    assert result.tool_calls[0]["success"]
```

### Mock External Dependencies

```python
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_execute_with_mock_agent():
    """Test execution with mocked Agno agent."""
    with patch('frankenagent.compiler.compiler.Agent') as MockAgent:
        mock_agent = Mock()
        mock_agent.run.return_value = Mock(content="Test response")
        MockAgent.return_value = mock_agent
        
        result = await executor.execute(blueprint, "test message")
        
        assert result.success
        assert result.response == "Test response"
```

## Performance Considerations

### Agent Caching (Future)

```python
from functools import lru_cache

class ExecutionOrchestrator:
    def __init__(self):
        self._agent_cache = {}
    
    def _get_or_compile_agent(self, blueprint_id: str, blueprint: dict):
        """Cache compiled agents by blueprint ID."""
        if blueprint_id in self._agent_cache:
            return self._agent_cache[blueprint_id]
        
        compiled_agent = self.compiler.compile(blueprint)
        self._agent_cache[blueprint_id] = compiled_agent
        return compiled_agent
```

### Async Operations

```python
# All I/O-bound operations should be async
async def execute(self, blueprint, message, session_id):
    # Async agent execution
    result = await self._execute_async(agent, message)
    return result
```

## Common Pitfalls

1. **Creating agents in loops** - Always reuse agents
2. **Forgetting user_id** - Required for conversation history
3. **Not enforcing guardrails** - Always wrap execution with limits
4. **Skipping validation** - Always validate before compiling
5. **Not logging tool calls** - Every tool call must be logged
6. **Bypassing the compiler** - Never create agents directly
7. **Ignoring errors** - Always handle and log errors properly

## Production Features

FrankenAgent Lab runtime includes comprehensive production features:

### ✅ Implemented Features

**Core Runtime:**
- Blueprint validation with detailed error messages
- Single agent compilation with multiple tools (Tavily, HTTP, Python, File)
- Execution with timeout and tool call guardrails
- Conversation memory with PostgreSQL (production) and SQLite (dev)
- Comprehensive logging and tracing of all tool calls
- FastAPI endpoints for validation, execution, and logs

**Production Infrastructure:**
- Multi-tenant authentication with JWT
- OAuth authentication (Google & GitHub)
- PostgreSQL database (Cloud SQL)
- Redis caching (Memorystore)
- Rate limiting and security hardening
- Monitoring and alerting
- Auto-scaling with Cloud Run
- Custom domain support with SSL

**Tools & Integrations:**
- Tavily search for web research
- HTTP tool for external API integration
- Python evaluation for code execution
- File operations for document handling

### 🎯 Current Focus

- Optimize performance and reduce latency
- Enhance security and guardrails
- Improve error handling and recovery
- Add more tool types based on user feedback
- Implement workflow and team execution modes
- Add streaming response support
