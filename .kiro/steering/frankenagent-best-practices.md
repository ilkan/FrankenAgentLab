---
inclusion: always
---

# FrankenAgent Lab Implementation Best Practices

## Code Organization Principles

### 1. Separation of Concerns

Each module has a single, clear responsibility:
- `config/` - Blueprint schema and loading only
- `compiler/` - Blueprint → Agno transformation only
- `tools/` - Tool registry and instantiation only
- `runtime/` - Execution orchestration and tracing only
- `cli/` - Command-line interface only
- `api/` - HTTP API endpoints only

Never mix concerns across modules.

### 2. Dependency Direction

Dependencies should flow in one direction:

```
CLI/API → Runtime → Compiler → Config
                  ↓
                Tools
```

Lower layers should never import from higher layers.

### 3. Error Handling Strategy

Use specific exception types:

```python
# Define custom exceptions
class FrankenAgentError(Exception):
    """Base exception for FrankenAgent Lab"""
    pass

class BlueprintNotFoundError(FrankenAgentError):
    """Blueprint file not found"""
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
    pass
```

Always catch specific exceptions and provide context:

```python
try:
    blueprint = loader.load_from_file(path)
except FileNotFoundError:
    raise BlueprintNotFoundError(f"Blueprint not found: {path}")
except yaml.YAMLError as e:
    raise ValidationError(f"Invalid YAML in {path}: {e}")
```

## Coding Standards

### Type Hints

Always use type hints:

```python
from typing import List, Dict, Any, Optional

def compile(self, blueprint: AgentBlueprint) -> Agent | Workflow | Team:
    """Compile blueprint into runnable agent"""
    pass

def execute(self, blueprint_id: str, message: str) -> ExecutionResult:
    """Execute agent from blueprint"""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def load_from_file(path: str) -> AgentBlueprint:
    """Load and validate blueprint from file.
    
    Args:
        path: Path to YAML or JSON blueprint file
        
    Returns:
        Validated AgentBlueprint object
        
    Raises:
        FileNotFoundError: If blueprint file doesn't exist
        ValidationError: If blueprint is invalid
    """
    pass
```

### Naming Conventions

- Classes: `PascalCase` (e.g., `BlueprintCompiler`)
- Functions/methods: `snake_case` (e.g., `load_from_file`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `TOOL_MAP`)
- Private methods: `_leading_underscore` (e.g., `_build_tools`)

### Code Formatting

Use Black with 100 character line length:

```bash
poetry run black --line-length 100 frankenagent tests
```

## Testing Best Practices

### Test Organization

```
tests/
├── test_config.py       # Config loading and validation
├── test_compiler.py     # Blueprint compilation
├── test_runtime.py      # Execution and tracing
├── test_api.py          # API endpoints
├── test_cli.py          # CLI commands
└── fixtures/
    ├── valid_blueprint.yaml
    ├── invalid_blueprint.yaml
    └── mock_tools.py
```

### Test Naming

```python
def test_load_valid_blueprint_succeeds():
    """Test that valid blueprint loads successfully"""
    pass

def test_load_invalid_blueprint_raises_validation_error():
    """Test that invalid blueprint raises ValidationError"""
    pass

def test_compile_single_agent_returns_agent_instance():
    """Test that single_agent mode returns Agent"""
    pass
```

### Use Fixtures

```python
import pytest
from frankenagent.config.loader import AgentBlueprint, HeadConfig, LegsConfig

@pytest.fixture
def simple_blueprint():
    """Fixture for simple test blueprint"""
    return AgentBlueprint(
        name="Test Agent",
        head=HeadConfig(
            model="gpt-4",
            provider="openai",
            system_prompt="Test prompt"
        ),
        legs=LegsConfig(execution_mode="single_agent")
    )

def test_compile_simple_blueprint(simple_blueprint):
    compiler = BlueprintCompiler()
    agent = compiler.compile(simple_blueprint)
    assert agent is not None
```

### Mock External Dependencies

```python
from unittest.mock import Mock, patch

def test_execute_with_mock_agent():
    """Test execution with mocked Agno agent"""
    with patch('frankenagent.compiler.compiler.Agent') as MockAgent:
        mock_agent = Mock()
        mock_agent.run.return_value = "Test response"
        MockAgent.return_value = mock_agent
        
        # Test execution
        result = runtime.execute("test_blueprint", "test message")
        assert result.response == "Test response"
```

## Performance Considerations

### Lazy Loading

Load blueprints only when needed:

```python
class RuntimeService:
    def __init__(self, blueprints_dir: str):
        self.blueprints_dir = blueprints_dir
        self._blueprint_cache = {}  # Cache compiled blueprints
    
    def execute(self, blueprint_id: str, message: str):
        # Check cache first
        if blueprint_id in self._blueprint_cache:
            agent = self._blueprint_cache[blueprint_id]
        else:
            # Load and compile
            blueprint = self.loader.load_from_file(...)
            agent = self.compiler.compile(blueprint)
            self._blueprint_cache[blueprint_id] = agent
        
        # Execute
        return agent.run(message)
```

### Efficient Tracing

Avoid deep copying large objects:

```python
# Bad - copies entire output
trace.outputs = copy.deepcopy(result)

# Good - store reference or summary
trace.outputs = result if len(str(result)) < 1000 else str(result)[:1000] + "..."
```

### Async Where Appropriate

Use async for I/O-bound operations:

```python
@app.post("/execute")
async def execute_agent(request: ExecuteRequest):
    # If agent execution is I/O bound, make it async
    result = await runtime.execute_async(request.blueprint_id, request.message)
    return result
```

## Security Considerations (MVP)

### Environment Variables

Never hardcode API keys:

```python
# Bad
OPENAI_API_KEY = "sk-..."

# Good
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

### Input Validation

Validate all user inputs:

```python
def execute(self, blueprint_id: str, message: str):
    # Validate blueprint_id to prevent path traversal
    if ".." in blueprint_id or "/" in blueprint_id:
        raise ValueError("Invalid blueprint_id")
    
    # Validate message length
    if len(message) > 10000:
        raise ValueError("Message too long")
```

### Guardrails

Always enforce guardrails:

```python
class GuardrailWrapper:
    def __init__(self, agent, max_tool_calls=10, timeout_seconds=60):
        self.agent = agent
        self.max_tool_calls = max_tool_calls
        self.timeout_seconds = timeout_seconds
```

## Logging Best Practices

### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log with context
logger.info(
    "Executing blueprint",
    extra={
        "blueprint_id": blueprint_id,
        "message_length": len(message),
        "execution_mode": blueprint.legs.execution_mode
    }
)
```

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for recoverable issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical errors requiring immediate attention

```python
logger.debug(f"Loading blueprint from {path}")
logger.info(f"Compiled {blueprint.name} in {duration}ms")
logger.warning(f"Blueprint {id} not in cache, loading from disk")
logger.error(f"Failed to compile blueprint: {error}")
```

## Documentation Standards

### README Structure

```markdown
# FrankenAgent Lab

## Overview
Brief description with Frankenstein metaphor

## Installation
Step-by-step setup instructions

## Quick Start
Minimal example to get running

## Blueprint Schema
Complete schema documentation

## CLI Usage
All CLI commands with examples

## API Reference
All endpoints with request/response examples

## Examples
Links to example blueprints

## Troubleshooting
Common issues and solutions

## Contributing
Development setup and guidelines
```

### Inline Comments

Comment the "why", not the "what":

```python
# Bad
# Loop through arms
for arm in blueprint.arms:
    ...

# Good
# Build tools in order to preserve execution sequence
for arm in blueprint.arms:
    ...
```

## Git Workflow

### Commit Messages

Use conventional commits:

```
feat: add workflow execution mode support
fix: handle missing blueprint files gracefully
docs: update API endpoint documentation
test: add compiler integration tests
refactor: extract tool building logic
```

### Branch Strategy

For MVP, simple workflow:
- `main` - stable code
- `feature/*` - new features
- `fix/*` - bug fixes

## Production Deployment Status

FrankenAgent Lab is production-ready with comprehensive deployment:

### ✅ Implemented Features

**Authentication & Security:**
- [x] JWT authentication with secure token management
- [x] OAuth integration (Google & GitHub)
- [x] Password reset via email (Brevo integration)
- [x] User API key management with Cloud KMS envelope encryption
- [x] Rate limiting (per-user and global via Redis)
- [x] Request logging and audit trails
- [x] User activity tracking

**Database & Storage:**
- [x] PostgreSQL database (Cloud SQL)
- [x] Redis caching (Memorystore)
- [x] SQLAlchemy ORM with Alembic migrations
- [x] Session management with conversation history
- [x] Blueprint versioning and soft deletes

**API & Execution:**
- [x] FastAPI backend with comprehensive endpoints
- [x] Blueprint validation and compilation
- [x] Agent execution with tool tracing
- [x] Session-based conversation management
- [x] Guardrails enforcement
- [x] Structured error handling

**Marketplace:**
- [x] Public blueprint marketplace
- [x] Blueprint cloning and customization
- [x] Rating system
- [x] Category and tag-based organization

**Infrastructure:**
- [x] Environment variable validation
- [x] Health check endpoint
- [x] CORS configuration
- [x] Cloud Run deployment
- [x] Custom domain support
- [x] Comprehensive logging

### 📚 Deployment Documentation

- **Quick Start**: [PRODUCTION_QUICK_START.md](../PRODUCTION_QUICK_START.md)
- **Full Guide**: [PRODUCTION_DEPLOYMENT_GUIDE.md](../PRODUCTION_DEPLOYMENT_GUIDE.md)
- **Custom Domain**: [CUSTOM_DOMAIN_GUIDE.md](../CUSTOM_DOMAIN_GUIDE.md)
- **OAuth Setup**: [docs/OAUTH_SETUP.md](../docs/OAUTH_SETUP.md)
- **Password Reset**: [docs/PASSWORD_RESET_GUIDE.md](../docs/PASSWORD_RESET_GUIDE.md)

## Common Pitfalls to Avoid

1. **Don't bypass the compiler** - Always go through blueprint → compile → execute
2. **Don't hardcode tool types** - Use the registry pattern
3. **Don't ignore errors** - Always handle and log errors properly
4. **Don't skip tracing** - Every execution must be traced
5. **Don't mix execution modes** - Keep single_agent, workflow, and team separate
6. **Don't forget guardrails** - Always enforce constraints
7. **Don't skip validation** - Validate blueprints before compilation
8. **Don't cache incorrectly** - Be careful with stateful agents
9. **Don't expose secrets** - Use environment variables and Cloud KMS
10. **Don't skip authentication** - Always validate JWT tokens in production
11. **Don't ignore rate limits** - Enforce per-user and global limits
12. **Don't skip monitoring** - Track metrics, logs, and errors

## Production Best Practices

### Security
- Validate all user inputs
- Use parameterized queries for database
- Rotate secrets regularly
- Implement proper CORS policies
- Enable audit logging
- Use least privilege access

### Performance
- Cache compiled agents when possible
- Use connection pooling for database
- Implement request timeouts
- Monitor and optimize slow queries
- Use Redis for session management
- Enable CDN for static assets

### Reliability
- Implement health checks
- Use circuit breakers for external APIs
- Handle graceful degradation
- Implement retry logic with exponential backoff
- Monitor error rates and latency
- Set up alerting for critical issues

### Scalability
- Design for horizontal scaling
- Use async operations for I/O
- Implement proper database indexing
- Use message queues for background tasks
- Monitor resource utilization
- Plan for traffic spikes
