# Design Document

## Overview

The FrankenAgent Lab Agent Runtime is a Python-based backend service that transforms agent blueprints into executable AI agents using the Agno framework. The runtime provides a REST API for blueprint validation, agent compilation, execution, and logging. It integrates with LLM providers (OpenAI, Anthropic) and external tools (Tavily Search) while enforcing guardrails to ensure safe and controlled agent behavior.

The design follows a clear separation of concerns with four main layers:
1. **API Layer** - FastAPI endpoints for HTTP communication
2. **Compiler Layer** - Blueprint validation and Agno agent compilation
3. **Runtime Layer** - Agent execution orchestration and session management
4. **Tools Layer** - Tool registry and integration with external services

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend UI                              │
│                  (Visual Blueprint Builder)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ /validate-and-   │  │ /agents/run      │  │ /agents/logs  │ │
│  │  compile         │  │                  │  │               │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
└───────────┼────────────────────┼────────────────────┼──────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Compiler Layer                               │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Blueprint        │  │ Agent Compiler   │                     │
│  │ Validator        │  │ (Blueprint→Agno) │                     │
│  └──────────────────┘  └────────┬─────────┘                     │
└─────────────────────────────────┼──────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Runtime Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Execution        │  │ Session Manager  │  │ Guardrail     │ │
│  │ Orchestrator     │  │                  │  │ Enforcer      │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
└───────────┼────────────────────┼────────────────────┼──────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agno Framework                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Agent            │  │ Memory           │  │ Tools         │ │
│  │ (LLM + Tools)    │  │                  │  │               │ │
│  └────────┬─────────┘  └──────────────────┘  └───────┬───────┘ │
└───────────┼──────────────────────────────────────────┼──────────┘
            │                                           │
            ▼                                           ▼
┌─────────────────────┐                    ┌─────────────────────┐
│   LLM Providers     │                    │  External Tools     │
│  (OpenAI, Claude)   │                    │  (Tavily Search)    │
└─────────────────────┘                    └─────────────────────┘
```

### Data Flow

1. **Validation Flow**: Frontend → `/validate-and-compile` → Blueprint Validator → Response
2. **Execution Flow**: Frontend → `/agents/run` → Agent Compiler → Agno Agent → LLM + Tools → Response
3. **Logging Flow**: Frontend → `/agents/logs` → Session Manager → Log Entries

## Components and Interfaces

### 1. API Layer (`frankenagent/api/server.py`)

**Responsibilities:**
- Expose REST endpoints for blueprint operations
- Handle request/response serialization
- Manage HTTP error codes and responses

**Endpoints:**

```python
@app.post("/api/blueprints/validate-and-compile")
async def validate_and_compile(blueprint: dict) -> ValidateResponse:
    """
    Validate and optionally compile a blueprint.
    
    Request:
    {
        "blueprint": {...},  # Full blueprint JSON
        "compile": true      # Optional: compile immediately
    }
    
    Response:
    {
        "valid": true,
        "blueprint_id": "bp_abc123",
        "normalized_blueprint": {...},
        "errors": []
    }
    """
    pass

@app.post("/api/agents/run")
async def run_agent(request: RunRequest) -> RunResponse:
    """
    Execute an agent with a message.
    
    Request:
    {
        "blueprint": {...},           # Full blueprint OR
        "blueprint_id": "bp_abc123",  # Reference to saved blueprint
        "message": "What is the weather?",
        "session_id": "sess_xyz",     # Optional: for conversation history
        "stream": false               # Optional: streaming response
    }
    
    Response:
    {
        "response": "The weather is...",
        "session_id": "sess_xyz",
        "tool_calls": [
            {
                "tool": "tavily_search",
                "args": {"query": "current weather"},
                "duration_ms": 234,
                "success": true
            }
        ],
        "guardrails_triggered": [],
        "total_latency_ms": 1523
    }
    """
    pass

@app.get("/api/agents/logs")
async def get_logs(session_id: str) -> LogsResponse:
    """
    Retrieve execution logs for a session.
    
    Response:
    {
        "session_id": "sess_xyz",
        "logs": [
            {
                "timestamp": "2025-11-16T10:30:00Z",
                "event_type": "tool_call",
                "tool_name": "tavily_search",
                "details": {...}
            }
        ]
    }
    """
    pass

@app.get("/api/components/schemas")
async def get_component_schemas() -> ComponentSchemasResponse:
    """
    Get configuration schemas for all component types.
    
    Response:
    {
        "head": {
            "providers": ["openai", "anthropic"],
            "models": {
                "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
                "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
            },
            "parameters": {
                "system_prompt": {"type": "string", "max_length": 10000},
                "temperature": {"type": "float", "min": 0.0, "max": 2.0, "default": 0.7},
                "max_tokens": {"type": "integer", "min": 1, "max": 128000, "optional": true}
            }
        },
        "arms": {
            "tool_types": ["tavily_search", "http_tool"],
            "tool_configs": {
                "tavily_search": {
                    "max_results": {"type": "integer", "min": 1, "max": 10, "default": 5},
                    "search_depth": {"type": "string", "enum": ["basic", "advanced"], "default": "basic"}
                }
            }
        },
        "legs": {
            "execution_modes": ["single_agent", "workflow", "team"],
            "mode_requirements": {
                "single_agent": {},
                "workflow": {"steps": "required"},
                "team": {"members": "required"}
            }
        },
        "heart": {
            "memory_enabled": {"type": "boolean", "default": false},
            "history_length": {"type": "integer", "min": 1, "max": 100, "default": 5},
            "knowledge_enabled": {"type": "boolean", "default": false}
        },
        "spine": {
            "max_tool_calls": {"type": "integer", "min": 1, "max": 100, "default": 10},
            "timeout_seconds": {"type": "integer", "min": 1, "max": 300, "default": 60},
            "allowed_domains": {"type": "array", "items": "string", "optional": true}
        }
    }
    """
    pass

@app.post("/api/instructions/improve")
async def improve_instructions(request: ImproveInstructionsRequest) -> ImproveInstructionsResponse:
    """
    Use LLM to improve agent instructions.
    
    Request:
    {
        "current_instructions": "You are a helpful assistant",
        "improvement_goal": "Make it more specific for customer support",
        "context": {
            "agent_purpose": "Handle customer inquiries",
            "tools_available": ["tavily_search"]
        }
    }
    
    Response:
    {
        "improved_instructions": "You are a customer support specialist...",
        "explanation": "Enhanced the instructions to...",
        "suggestions": [
            "Consider adding tone guidelines",
            "Specify response format preferences"
        ]
    }
    """
    pass
```

### 2. Component Configuration Service (`frankenagent/config/`)

#### Component Schema Provider (`config/schemas.py`)

**Responsibilities:**
- Provide configuration schemas for all component types
- Define validation rules and available options
- Support dynamic schema generation based on installed tools

```python
from typing import Dict, Any
from pydantic import BaseModel

class ComponentSchemaProvider:
    """Provides configuration schemas for all agent components."""
    
    def get_all_schemas(self) -> Dict[str, Any]:
        """Get schemas for all component types."""
        return {
            "head": self.get_head_schema(),
            "arms": self.get_arms_schema(),
            "legs": self.get_legs_schema(),
            "heart": self.get_heart_schema(),
            "spine": self.get_spine_schema()
        }
    
    def get_head_schema(self) -> Dict[str, Any]:
        """Get head (LLM) configuration schema."""
        return {
            "providers": ["openai", "anthropic"],
            "models": {
                "openai": [
                    "gpt-4o",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo"
                ],
                "anthropic": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-haiku-20240307"
                ]
            },
            "parameters": {
                "system_prompt": {
                    "type": "string",
                    "max_length": 10000,
                    "description": "Instructions that define the agent's behavior and personality",
                    "default": "You are a helpful assistant"
                },
                "temperature": {
                    "type": "float",
                    "min": 0.0,
                    "max": 2.0,
                    "default": 0.7,
                    "description": "Controls randomness in responses (0=deterministic, 2=very random)"
                },
                "max_tokens": {
                    "type": "integer",
                    "min": 1,
                    "max": 128000,
                    "optional": True,
                    "description": "Maximum tokens in the response"
                }
            }
        }
    
    def get_arms_schema(self) -> Dict[str, Any]:
        """Get arms (tools) configuration schema."""
        return {
            "tool_types": ["tavily_search", "http_tool"],
            "tool_configs": {
                "tavily_search": {
                    "max_results": {
                        "type": "integer",
                        "min": 1,
                        "max": 10,
                        "default": 5,
                        "description": "Maximum number of search results to return"
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "default": "basic",
                        "description": "Search depth (basic=faster, advanced=more thorough)"
                    }
                },
                "http_tool": {
                    "base_url": {
                        "type": "string",
                        "description": "Base URL for HTTP requests"
                    },
                    "headers": {
                        "type": "object",
                        "optional": True,
                        "description": "Default headers for requests"
                    }
                }
            }
        }
    
    def get_legs_schema(self) -> Dict[str, Any]:
        """Get legs (execution mode) configuration schema."""
        return {
            "execution_modes": ["single_agent", "workflow", "team"],
            "mode_requirements": {
                "single_agent": {
                    "description": "Single agent handles all tasks"
                },
                "workflow": {
                    "description": "Sequential steps with programmatic control",
                    "required_fields": ["steps"]
                },
                "team": {
                    "description": "Multiple specialized agents with autonomous coordination",
                    "required_fields": ["members"]
                }
            }
        }
    
    def get_heart_schema(self) -> Dict[str, Any]:
        """Get heart (memory) configuration schema."""
        return {
            "memory_enabled": {
                "type": "boolean",
                "default": False,
                "description": "Enable conversation history"
            },
            "history_length": {
                "type": "integer",
                "min": 1,
                "max": 100,
                "default": 5,
                "description": "Number of previous conversation turns to include"
            },
            "knowledge_enabled": {
                "type": "boolean",
                "default": False,
                "description": "Enable knowledge base / RAG"
            }
        }
    
    def get_spine_schema(self) -> Dict[str, Any]:
        """Get spine (guardrails) configuration schema."""
        return {
            "max_tool_calls": {
                "type": "integer",
                "min": 1,
                "max": 100,
                "default": 10,
                "description": "Maximum number of tool calls per execution"
            },
            "timeout_seconds": {
                "type": "integer",
                "min": 1,
                "max": 300,
                "default": 60,
                "description": "Maximum execution time in seconds"
            },
            "allowed_domains": {
                "type": "array",
                "items": "string",
                "optional": True,
                "description": "Whitelist of allowed domains for web-based tools"
            }
        }
```

#### Instruction Improvement Service (`config/instruction_improver.py`)

**Responsibilities:**
- Use LLM to improve user-provided instructions
- Provide context-aware suggestions
- Maintain user intent while enhancing clarity

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from typing import Dict, List

class InstructionImprover:
    """Service for improving agent instructions using LLM assistance."""
    
    def __init__(self):
        # Create a specialized agent for instruction improvement
        self.improver_agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            instructions="""You are an expert at writing effective AI agent instructions.
            
Your task is to improve system prompts for AI agents while:
1. Preserving the user's original intent
2. Making instructions clearer and more specific
3. Adding relevant context and guidelines
4. Ensuring the instructions work well with the agent's available tools
5. Following best practices for prompt engineering

Provide:
- Improved instructions
- Brief explanation of changes
- Optional suggestions for further improvement""",
            markdown=False
        )
    
    def improve(
        self,
        current_instructions: str,
        improvement_goal: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Improve instructions using LLM assistance.
        
        Args:
            current_instructions: The current system prompt
            improvement_goal: What the user wants to improve
            context: Additional context (agent purpose, tools, etc.)
        
        Returns:
            Dictionary with improved instructions, explanation, and suggestions
        """
        # Build prompt for the improver agent
        prompt = self._build_improvement_prompt(
            current_instructions,
            improvement_goal,
            context
        )
        
        try:
            # Run the improver agent
            result = self.improver_agent.run(prompt)
            
            # Parse the response
            improved = self._parse_improvement_response(result.content)
            
            return {
                "improved_instructions": improved["instructions"],
                "explanation": improved["explanation"],
                "suggestions": improved.get("suggestions", [])
            }
        except Exception as e:
            # If improvement fails, return original with error
            return {
                "improved_instructions": current_instructions,
                "explanation": f"Failed to improve instructions: {str(e)}",
                "suggestions": []
            }
    
    def _build_improvement_prompt(
        self,
        current: str,
        goal: str,
        context: Dict[str, Any]
    ) -> str:
        """Build the prompt for the improver agent."""
        tools_info = ""
        if context.get("tools_available"):
            tools_info = f"\nAvailable tools: {', '.join(context['tools_available'])}"
        
        purpose_info = ""
        if context.get("agent_purpose"):
            purpose_info = f"\nAgent purpose: {context['agent_purpose']}"
        
        return f"""Please improve these agent instructions:

Current instructions:
{current}

Improvement goal: {goal}{purpose_info}{tools_info}

Provide your response in this format:

IMPROVED INSTRUCTIONS:
[Your improved version here]

EXPLANATION:
[Brief explanation of what you changed and why]

SUGGESTIONS:
- [Optional suggestion 1]
- [Optional suggestion 2]
"""
    
    def _parse_improvement_response(self, response: str) -> Dict[str, Any]:
        """Parse the improver agent's response."""
        # Simple parsing - split by section headers
        sections = {}
        
        if "IMPROVED INSTRUCTIONS:" in response:
            parts = response.split("IMPROVED INSTRUCTIONS:")
            if len(parts) > 1:
                rest = parts[1]
                if "EXPLANATION:" in rest:
                    inst_parts = rest.split("EXPLANATION:")
                    sections["instructions"] = inst_parts[0].strip()
                    
                    if "SUGGESTIONS:" in inst_parts[1]:
                        exp_parts = inst_parts[1].split("SUGGESTIONS:")
                        sections["explanation"] = exp_parts[0].strip()
                        
                        # Parse suggestions
                        suggestions_text = exp_parts[1].strip()
                        suggestions = [
                            s.strip().lstrip("-").strip()
                            for s in suggestions_text.split("\n")
                            if s.strip() and s.strip().startswith("-")
                        ]
                        sections["suggestions"] = suggestions
                    else:
                        sections["explanation"] = inst_parts[1].strip()
        
        return sections
```

### 3. Compiler Layer (`frankenagent/compiler/`)

#### Blueprint Validator (`compiler/validator.py`)

**Responsibilities:**
- Validate blueprint schema and field values
- Check provider/model/tool support
- Normalize blueprint format

```python
class BlueprintValidator:
    SUPPORTED_PROVIDERS = ["openai", "anthropic"]
    SUPPORTED_MODELS = {
        "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
    }
    SUPPORTED_TOOLS = ["tavily_search", "http_tool"]
    
    def validate(self, blueprint: dict) -> ValidationResult:
        """
        Validate blueprint and return normalized version or errors.
        
        Checks:
        - Required fields: head, legs
        - Valid provider and model combination
        - Valid tool types in arms
        - Valid guardrail values in spine
        - Valid memory config in heart
        """
        errors = []
        
        # Validate head
        if "head" not in blueprint:
            errors.append({"field": "head", "message": "Required field missing"})
        else:
            head = blueprint["head"]
            if head.get("provider") not in self.SUPPORTED_PROVIDERS:
                errors.append({
                    "field": "head.provider",
                    "message": f"Unsupported provider. Supported: {self.SUPPORTED_PROVIDERS}"
                })
            # ... more validation
        
        # Validate arms (tools)
        for i, arm in enumerate(blueprint.get("arms", [])):
            if arm.get("type") not in self.SUPPORTED_TOOLS:
                errors.append({
                    "field": f"arms[{i}].type",
                    "message": f"Unsupported tool. Supported: {self.SUPPORTED_TOOLS}"
                })
        
        # Validate spine (guardrails)
        spine = blueprint.get("spine", {})
        if "max_tool_calls" in spine:
            if not isinstance(spine["max_tool_calls"], int) or spine["max_tool_calls"] < 1:
                errors.append({
                    "field": "spine.max_tool_calls",
                    "message": "Must be a positive integer"
                })
        
        if errors:
            return ValidationResult(valid=False, errors=errors)
        
        return ValidationResult(
            valid=True,
            normalized_blueprint=self._normalize(blueprint),
            blueprint_id=self._generate_id(blueprint)
        )
```

#### Agent Compiler (`compiler/compiler.py`)

**Responsibilities:**
- Transform validated blueprint into Agno Agent
- Configure LLM provider and parameters
- Attach tools from registry
- Apply memory and guardrail settings

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from frankenagent.tools.registry import ToolRegistry

class AgentCompiler:
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
    
    def compile(self, blueprint: dict) -> CompiledAgent:
        """
        Compile a validated blueprint into an Agno Agent.
        
        Steps:
        1. Build LLM model from head
        2. Build tools from arms
        3. Build memory from heart
        4. Wrap with guardrails from spine
        5. Return CompiledAgent wrapper
        """
        # 1. Build LLM model
        model = self._build_model(blueprint["head"])
        
        # 2. Build tools
        tools = self._build_tools(blueprint.get("arms", []))
        
        # 3. Build memory
        memory_config = self._build_memory(blueprint.get("heart", {}))
        
        # 4. Create Agno Agent
        agent = Agent(
            model=model,
            instructions=blueprint["head"].get("system_prompt", "You are a helpful assistant"),
            tools=tools,
            **memory_config
        )
        
        # 5. Wrap with guardrails
        guardrails = blueprint.get("spine", {})
        compiled_agent = CompiledAgent(
            agent=agent,
            blueprint_id=blueprint.get("id"),
            guardrails=guardrails
        )
        
        return compiled_agent
    
    def _build_model(self, head: dict):
        """Build Agno model from head config."""
        provider = head["provider"]
        model_id = head["model"]
        
        if provider == "openai":
            return OpenAIChat(
                id=model_id,
                temperature=head.get("temperature", 0.7),
                max_tokens=head.get("max_tokens")
            )
        elif provider == "anthropic":
            return Claude(
                id=model_id,
                temperature=head.get("temperature", 0.7),
                max_tokens=head.get("max_tokens")
            )
        else:
            raise CompilationError(f"Unsupported provider: {provider}")
    
    def _build_tools(self, arms: list) -> list:
        """Build Agno tools from arms config."""
        tools = []
        for arm in arms:
            tool = self.tool_registry.create_tool(arm)
            tools.append(tool)
        return tools
    
    def _build_memory(self, heart: dict) -> dict:
        """Build memory config from heart."""
        memory_config = {}
        
        if heart.get("memory_enabled"):
            # For MVP: use SQLite for conversation history
            from agno.db.sqlite import SqliteDb
            memory_config["db"] = SqliteDb(db_file="tmp/agents.db")
            memory_config["add_history_to_context"] = True
            memory_config["num_history_runs"] = heart.get("history_length", 5)
        
        return memory_config
```

### 3. Tools Layer (`frankenagent/tools/`)

#### Tool Registry (`tools/registry.py`)

**Responsibilities:**
- Map tool types to Agno tool implementations
- Handle tool configuration and API keys
- Provide extensible tool registration

```python
import os
from agno.tools.tavily import TavilyTools

class ToolRegistry:
    """Registry for mapping blueprint tool configs to Agno tools."""
    
    def create_tool(self, arm_config: dict):
        """
        Create an Agno tool from arm configuration.
        
        Args:
            arm_config: Tool config from blueprint arms section
            Example: {"type": "tavily_search", "config": {...}}
        
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
    
    def _create_http_tool(self, config: dict):
        """Create HTTP request tool (future implementation)."""
        # Placeholder for future HTTP tool
        raise NotImplementedError("HTTP tool not yet implemented")
```

### 4. Runtime Layer (`frankenagent/runtime/`)

#### Execution Orchestrator (`runtime/executor.py`)

**Responsibilities:**
- Orchestrate agent execution
- Enforce guardrails during execution
- Capture tool calls and timing
- Handle errors and timeouts

```python
import time
import asyncio
from typing import Optional

class ExecutionOrchestrator:
    def __init__(self, compiler: AgentCompiler, session_manager: SessionManager):
        self.compiler = compiler
        self.session_manager = session_manager
    
    async def execute(
        self,
        blueprint: dict,
        message: str,
        session_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute an agent with guardrails and logging.
        
        Steps:
        1. Compile or retrieve agent
        2. Load session history if session_id provided
        3. Execute with timeout and tool call limits
        4. Log tool calls and results
        5. Return response with metadata
        """
        start_time = time.time()
        
        # 1. Compile agent
        compiled_agent = self.compiler.compile(blueprint)
        agent = compiled_agent.agent
        guardrails = compiled_agent.guardrails
        
        # 2. Load session
        if session_id:
            session = self.session_manager.get_or_create(session_id)
            # Agno handles history via db and user_id
            agent.user_id = session_id
        else:
            session_id = self.session_manager.create_new_session()
            agent.user_id = session_id
        
        # 3. Execute with guardrails
        try:
            result = await self._execute_with_guardrails(
                agent,
                message,
                guardrails,
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
            tool_calls=result.tool_calls,
            session_id=session_id,
            total_latency_ms=total_latency
        )
    
    async def _execute_with_guardrails(
        self,
        agent,
        message: str,
        guardrails: dict,
        session_id: str
    ):
        """Execute agent with guardrail enforcement."""
        timeout = guardrails.get("timeout_seconds", 60)
        max_tool_calls = guardrails.get("max_tool_calls", 10)
        
        # Wrap execution with timeout
        try:
            result = await asyncio.wait_for(
                self._run_agent_with_tool_limit(agent, message, max_tool_calls, session_id),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            raise GuardrailViolation("timeout_seconds", f"Execution exceeded {timeout}s")
    
    async def _run_agent_with_tool_limit(
        self,
        agent,
        message: str,
        max_tool_calls: int,
        session_id: str
    ):
        """Run agent and track tool calls."""
        # Agno agents handle tool calls internally
        # We need to wrap and monitor
        
        tool_call_count = 0
        
        # Create a custom tool wrapper to count calls
        original_tools = agent.tools
        wrapped_tools = []
        
        for tool in original_tools:
            wrapped_tool = self._wrap_tool_with_counter(
                tool,
                session_id,
                lambda: tool_call_count
            )
            wrapped_tools.append(wrapped_tool)
            tool_call_count += 1
        
        agent.tools = wrapped_tools
        
        # Run agent
        result = agent.run(message)
        
        # Check tool call limit
        if tool_call_count > max_tool_calls:
            raise GuardrailViolation(
                "max_tool_calls",
                f"Exceeded limit of {max_tool_calls} tool calls"
            )
        
        return result
    
    def _wrap_tool_with_counter(self, tool, session_id: str, get_count):
        """Wrap tool to log calls."""
        # This is a simplified version
        # In practice, we'd use Agno's built-in tracing or middleware
        
        def wrapped_function(*args, **kwargs):
            start = time.time()
            try:
                result = tool(*args, **kwargs)
                duration = int((time.time() - start) * 1000)
                
                # Log tool call
                self.session_manager.log_tool_call(
                    session_id=session_id,
                    tool_name=tool.__name__,
                    args=kwargs,
                    duration_ms=duration,
                    success=True,
                    result=result
                )
                
                return result
            except Exception as e:
                duration = int((time.time() - start) * 1000)
                self.session_manager.log_tool_call(
                    session_id=session_id,
                    tool_name=tool.__name__,
                    args=kwargs,
                    duration_ms=duration,
                    success=False,
                    error=str(e)
                )
                raise
        
        return wrapped_function
```

#### Session Manager (`runtime/session_manager.py`)

**Responsibilities:**
- Manage session lifecycle
- Store and retrieve conversation history
- Log execution events

```python
from datetime import datetime
from typing import List, Optional
import uuid

class SessionManager:
    def __init__(self):
        # For MVP: in-memory storage
        # Future: use database
        self.sessions = {}
        self.logs = {}
    
    def create_new_session(self) -> str:
        """Create a new session and return ID."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self.sessions[session_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "messages": []
        }
        self.logs[session_id] = []
        return session_id
    
    def get_or_create(self, session_id: str) -> dict:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "messages": []
            }
            self.logs[session_id] = []
        return self.sessions[session_id]
    
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
        """Log a tool call event."""
        if session_id not in self.logs:
            self.logs[session_id] = []
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "tool_call",
            "tool_name": tool_name,
            "args": args,
            "duration_ms": duration_ms,
            "success": success,
            "result": result[:200] if result else None,  # Truncate for storage
            "error": error
        }
        
        self.logs[session_id].append(log_entry)
    
    def get_logs(self, session_id: str) -> List[dict]:
        """Retrieve all logs for a session."""
        return self.logs.get(session_id, [])
```

## Data Models

### Blueprint Structure

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict, Any

class HeadConfig(BaseModel):
    provider: Literal["openai", "anthropic"]
    model: str
    system_prompt: Optional[str] = Field(
        default="You are a helpful assistant",
        max_length=10000,
        description="Instructions that define the agent's behavior"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness (0=deterministic, 2=very random)"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum tokens in response"
    )
    
    @validator('system_prompt')
    def validate_system_prompt(cls, v):
        if v and len(v) > 10000:
            raise ValueError("system_prompt must not exceed 10000 characters")
        return v

class ArmConfig(BaseModel):
    type: Literal["tavily_search", "http_tool"]
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific configuration"
    )
    
    @validator('config')
    def validate_config(cls, v, values):
        tool_type = values.get('type')
        if tool_type == 'tavily_search':
            if 'max_results' in v:
                if not isinstance(v['max_results'], int) or v['max_results'] < 1 or v['max_results'] > 10:
                    raise ValueError("max_results must be between 1 and 10")
            if 'search_depth' in v:
                if v['search_depth'] not in ['basic', 'advanced']:
                    raise ValueError("search_depth must be 'basic' or 'advanced'")
        return v

class LegsConfig(BaseModel):
    execution_mode: Literal["single_agent", "workflow", "team"] = "single_agent"
    workflow_steps: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Required when execution_mode is 'workflow'"
    )
    team_members: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Required when execution_mode is 'team'"
    )
    
    @validator('workflow_steps')
    def validate_workflow_steps(cls, v, values):
        if values.get('execution_mode') == 'workflow' and not v:
            raise ValueError("workflow_steps required when execution_mode is 'workflow'")
        return v
    
    @validator('team_members')
    def validate_team_members(cls, v, values):
        if values.get('execution_mode') == 'team' and not v:
            raise ValueError("team_members required when execution_mode is 'team'")
        return v

class HeartConfig(BaseModel):
    memory_enabled: bool = Field(
        default=False,
        description="Enable conversation history"
    )
    history_length: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of previous turns to include"
    )
    knowledge_enabled: bool = Field(
        default=False,
        description="Enable knowledge base / RAG"
    )

class SpineConfig(BaseModel):
    max_tool_calls: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum tool calls per execution"
    )
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Maximum execution time"
    )
    allowed_domains: Optional[List[str]] = Field(
        default=None,
        description="Whitelist of allowed domains"
    )

class AgentBlueprint(BaseModel):
    name: str = Field(description="Human-readable agent name")
    head: HeadConfig
    arms: List[ArmConfig] = Field(default_factory=list)
    legs: LegsConfig = Field(default_factory=LegsConfig)
    heart: HeartConfig = Field(default_factory=HeartConfig)
    spine: SpineConfig = Field(default_factory=SpineConfig)
```

### API Request/Response Models

```python
class ImproveInstructionsRequest(BaseModel):
    current_instructions: str = Field(description="Current system prompt")
    improvement_goal: str = Field(description="What to improve")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (purpose, tools, etc.)"
    )

class ImproveInstructionsResponse(BaseModel):
    improved_instructions: str
    explanation: str
    suggestions: List[str] = Field(default_factory=list)

class ComponentSchemasResponse(BaseModel):
    head: Dict[str, Any]
    arms: Dict[str, Any]
    legs: Dict[str, Any]
    heart: Dict[str, Any]
    spine: Dict[str, Any]
```

### Execution Result

```python
class ToolCallLog(BaseModel):
    tool: str
    args: dict
    duration_ms: int
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None

class ExecutionResult(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    session_id: str
    tool_calls: List[ToolCallLog] = []
    guardrails_triggered: List[str] = []
    total_latency_ms: int
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Component Schema Completeness
*For any* component type (head, arms, legs, heart, spine), the schema endpoint should return all required configuration fields and validation rules for that component.
**Validates: Requirements 11.2, 11.3, 11.4, 11.5, 11.6**

### Property 2: Head Configuration Validation
*For any* head configuration with system_prompt, temperature, and max_tokens, validation should succeed if and only if system_prompt length ≤ 10000, temperature is in [0.0, 2.0], and max_tokens is a positive integer.
**Validates: Requirements 12.2, 12.3, 12.4**

### Property 3: Instruction Improvement Preservation
*For any* valid system prompt, the instruction improvement service should return improved instructions that preserve the original intent while enhancing clarity.
**Validates: Requirements 13.3**

### Property 4: Arms Configuration Ordering
*For any* list of tool configurations in the arms section, the compiled agent should attach tools in the same order they appear in the configuration.
**Validates: Requirements 14.3**

### Property 5: Legs Mode Requirements
*For any* execution mode selection, validation should fail if and only if required fields for that mode are missing (workflow requires steps, team requires members).
**Validates: Requirements 15.2, 15.3, 15.4**

### Property 6: Heart Memory Configuration
*For any* heart configuration with memory enabled, the compiled agent should include conversation history with the specified history_length value between 1 and 100.
**Validates: Requirements 16.2, 16.4**

### Property 7: Spine Guardrail Bounds
*For any* spine configuration, validation should succeed if and only if max_tool_calls is in [1, 100], timeout_seconds is in [1, 300], and all allowed_domains are valid domain formats.
**Validates: Requirements 17.1, 17.2, 17.3**

### Property 8: Component Compilation Completeness
*For any* valid blueprint with all five components configured, the compiled agent should include all specified configurations (model, tools, memory, guardrails).
**Validates: Requirements 12.5, 14.5, 15.5, 16.4, 17.4**

### Property 9: Default Guardrail Application
*For any* blueprint without explicit spine configuration, the compiled agent should have default guardrail values applied (max_tool_calls=10, timeout_seconds=60).
**Validates: Requirements 17.5**

### Property 10: Instruction Improvement Fallback
*For any* instruction improvement request that fails, the service should return the original instructions unchanged with an error message.
**Validates: Requirements 13.5**

## Error Handling

### Exception Hierarchy

```python
class FrankenAgentError(Exception):
    """Base exception"""
    pass

class BlueprintNotFoundError(FrankenAgentError):
    """Blueprint not found"""
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

### Error Response Format

```python
{
    "error": {
        "type": "ValidationError",
        "message": "Blueprint validation failed",
        "details": [
            {
                "field": "head.provider",
                "message": "Unsupported provider 'gpt'. Supported: ['openai', 'anthropic']"
            }
        ]
    }
}
```

## Testing Strategy

### Unit Tests

- **Validator Tests**: Test each validation rule independently
- **Compiler Tests**: Test blueprint → Agno agent transformation
- **Tool Registry Tests**: Test tool creation and configuration
- **Guardrail Tests**: Test timeout and tool call limit enforcement
- **Component Schema Tests**: Test schema generation for all component types
- **Instruction Improver Tests**: Test instruction improvement with mock LLM responses
- **Configuration Validation Tests**: Test validation for each component configuration

### Integration Tests

- **End-to-End Flow**: Blueprint → Compile → Execute → Response
- **Tavily Integration**: Test actual Tavily API calls (with test key)
- **Memory Persistence**: Test conversation history across multiple messages
- **Error Scenarios**: Test invalid blueprints, API failures, guardrail violations
- **Instruction Improvement Flow**: Test full instruction improvement with real LLM
- **Component Configuration Flow**: Test retrieving schemas and validating configurations

### Test Fixtures

```python
# tests/fixtures/blueprints.py

VALID_SIMPLE_BLUEPRINT = {
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

VALID_SEARCH_BLUEPRINT = {
    "name": "Search Agent",
    "head": {
        "provider": "openai",
        "model": "gpt-4o",
        "system_prompt": "You are a research assistant"
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

INVALID_BLUEPRINT_MISSING_HEAD = {
    "name": "Invalid",
    "legs": {"execution_mode": "single_agent"}
}
```

## Future Extensibility

### Workflow Mode (Future)

```python
# When legs.execution_mode = "workflow"
from agno.workflow.workflow import Workflow

def compile_workflow(blueprint: dict) -> Workflow:
    """
    Compile blueprint into Agno Workflow.
    
    Blueprint would include:
    - steps: list of sequential agent tasks
    - transitions: conditional logic between steps
    """
    pass
```

### Team Mode (Future)

```python
# When legs.execution_mode = "team"
from agno.team.team import Team

def compile_team(blueprint: dict) -> Team:
    """
    Compile blueprint into Agno Team.
    
    Blueprint would include:
    - members: list of specialized agents
    - coordinator: agent that delegates tasks
    """
    pass
```

### Additional Tools (Future)

- HTTP Tool: Make arbitrary HTTP requests
- File Tool: Read/write files
- RAG Tool: Query knowledge base
- Code Execution Tool: Run Python code safely

### Streaming Support (Future)

```python
@app.post("/api/agents/run/stream")
async def run_agent_stream(request: RunRequest):
    """
    Stream agent responses via Server-Sent Events.
    
    Events:
    - tool_call: When a tool is invoked
    - tool_result: When a tool completes
    - response_chunk: Partial response text
    - complete: Final response
    """
    async def event_generator():
        # Stream events as they occur
        async for event in executor.execute_stream(request):
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Blueprint File Persistence

#### Blueprint File Manager (`config/blueprint_manager.py`)

**Responsibilities:**
- Save blueprints as YAML files to disk
- Load blueprints from YAML files
- List available blueprint files
- Validate blueprint files

```python
import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class BlueprintFileManager:
    """Manages blueprint configuration files on disk."""
    
    def __init__(self, blueprints_dir: str = "blueprints"):
        self.blueprints_dir = Path(blueprints_dir)
        self.blueprints_dir.mkdir(exist_ok=True)
    
    def save_blueprint(self, blueprint: Dict[str, Any], name: str = None) -> str:
        """
        Save blueprint to YAML file.
        
        Args:
            blueprint: Blueprint dictionary
            name: Optional custom name (defaults to blueprint['name'])
        
        Returns:
            Path to saved file
        """
        # Generate filename
        agent_name = name or blueprint.get('name', 'agent')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = self._sanitize_filename(agent_name)
        filename = f"{safe_name}_{timestamp}.yaml"
        filepath = self.blueprints_dir / filename
        
        # Save as YAML
        with open(filepath, 'w') as f:
            yaml.dump(blueprint, f, default_flow_style=False, sort_keys=False)
        
        return str(filepath)
    
    def load_blueprint(self, filename: str) -> Dict[str, Any]:
        """
        Load blueprint from YAML file.
        
        Args:
            filename: Name of blueprint file (with or without .yaml extension)
        
        Returns:
            Blueprint dictionary
        """
        if not filename.endswith('.yaml'):
            filename = f"{filename}.yaml"
        
        filepath = self.blueprints_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Blueprint file not found: {filename}")
        
        with open(filepath, 'r') as f:
            blueprint = yaml.safe_load(f)
        
        return blueprint
    
    def list_blueprints(self) -> List[Dict[str, Any]]:
        """
        List all available blueprint files.
        
        Returns:
            List of blueprint metadata (name, filename, created_at)
        """
        blueprints = []
        
        for filepath in self.blueprints_dir.glob("*.yaml"):
            try:
                with open(filepath, 'r') as f:
                    blueprint = yaml.safe_load(f)
                
                blueprints.append({
                    "name": blueprint.get('name', filepath.stem),
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "created_at": datetime.fromtimestamp(
                        filepath.stat().st_mtime
                    ).isoformat()
                })
            except Exception as e:
                # Skip invalid files
                continue
        
        return sorted(blueprints, key=lambda x: x['created_at'], reverse=True)
    
    def delete_blueprint(self, filename: str) -> bool:
        """
        Delete a blueprint file.
        
        Args:
            filename: Name of blueprint file
        
        Returns:
            True if deleted, False if not found
        """
        if not filename.endswith('.yaml'):
            filename = f"{filename}.yaml"
        
        filepath = self.blueprints_dir / filename
        
        if filepath.exists():
            filepath.unlink()
            return True
        
        return False
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize agent name for use as filename."""
        # Replace spaces and special chars with underscores
        safe = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name)
        return safe.lower()
```

#### API Endpoints for Blueprint Files

```python
@app.post("/api/blueprints/save")
async def save_blueprint(request: SaveBlueprintRequest) -> SaveBlueprintResponse:
    """
    Save blueprint to YAML file.
    
    Request:
    {
        "blueprint": {...},
        "name": "my_agent"  # Optional custom name
    }
    
    Response:
    {
        "success": true,
        "filename": "my_agent_20251122_143022.yaml",
        "filepath": "blueprints/my_agent_20251122_143022.yaml"
    }
    """
    pass

@app.get("/api/blueprints/list")
async def list_blueprints() -> ListBlueprintsResponse:
    """
    List all saved blueprint files.
    
    Response:
    {
        "blueprints": [
            {
                "name": "Search Agent",
                "filename": "search_agent_20251122_143022.yaml",
                "filepath": "blueprints/search_agent_20251122_143022.yaml",
                "created_at": "2025-11-22T14:30:22Z"
            }
        ]
    }
    """
    pass

@app.get("/api/blueprints/load/{filename}")
async def load_blueprint(filename: str) -> LoadBlueprintResponse:
    """
    Load blueprint from file.
    
    Response:
    {
        "blueprint": {...},
        "filename": "search_agent_20251122_143022.yaml"
    }
    """
    pass

@app.delete("/api/blueprints/{filename}")
async def delete_blueprint(filename: str) -> DeleteBlueprintResponse:
    """
    Delete a blueprint file.
    
    Response:
    {
        "success": true,
        "message": "Blueprint deleted successfully"
    }
    """
    pass
```

### Blueprint Caching (Future)

```python
# Option 1: In-memory caching (MVP)
from functools import lru_cache

class BlueprintCache:
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
    
    def get(self, blueprint_id: str) -> Optional[CompiledAgent]:
        return self.cache.get(blueprint_id)
    
    def set(self, blueprint_id: str, compiled_agent: CompiledAgent):
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[blueprint_id] = compiled_agent

# Option 2: Database storage (Production)
class DatabaseBlueprintStore:
    def save(self, blueprint: dict, user_id: str) -> str:
        # Store in PostgreSQL with user association
        pass
```

## Performance Considerations

### Agent Caching

For MVP, compile agents on each request. Future optimization:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_compiled_agent(blueprint_id: str) -> CompiledAgent:
    """Cache compiled agents by blueprint ID."""
    blueprint = load_blueprint(blueprint_id)
    return compiler.compile(blueprint)
```

### Async Execution

All I/O-bound operations use async/await:
- API endpoints are async
- Agent execution is async
- Tool calls are async (where supported by Agno)

### Resource Limits

- Max concurrent executions: 10 (configurable)
- Max blueprint size: 1MB
- Max message length: 10,000 characters
- Max session history: 100 messages

## Security Considerations (MVP)

### API Key Management

- All API keys stored in environment variables
- Never expose keys in responses or logs
- Validate keys on startup

### Input Validation

- Validate all blueprint fields
- Sanitize user messages
- Limit message and blueprint sizes

### Guardrails

- Enforce timeout to prevent runaway execution
- Limit tool calls to prevent abuse
- Domain restrictions for web tools (future)

## Deployment Notes (Future)

For MVP: Local development only

Future production deployment:
- Containerize with Docker
- Use PostgreSQL for sessions and logs
- Add authentication and rate limiting
- Implement horizontal scaling
- Add monitoring and alerting
