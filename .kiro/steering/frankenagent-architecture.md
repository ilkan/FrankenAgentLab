---
inclusion: always
---

# FrankenAgent Lab Architecture Guidelines

## Core Metaphor Preservation

The Frankenstein metaphor is central to FrankenAgent Lab's identity. All code and documentation must preserve this conceptual model:

- **Head** = LLM brain (model, provider, system prompt, temperature)
- **Arms** = Tools and external integrations
- **Legs** = Execution mode (single_agent, workflow, team)
- **Heart** = Memory and knowledge base
- **Spine** = Guardrails and safety constraints

## Blueprint-First Design

All agent functionality must be expressible through the Agent Blueprint schema. When implementing features:

1. Start with the blueprint schema definition
2. Implement the compiler mapping to Agno
3. Add runtime execution support
4. Ensure tracing captures the behavior

Never bypass the blueprint → compiler → agent flow.

## Agno Integration Patterns

### Single Agent Mapping

```python
# Blueprint head → Agno Agent
agent = Agent(
    model=blueprint.head.model,
    instructions=blueprint.head.system_prompt,
    temperature=blueprint.head.temperature,
    tools=compiled_tools,
    memory=compiled_memory
)
```

### Tool Registry Pattern

All tools must be registered in `ToolRegistry.TOOL_MAP`. When adding new tool types:

1. Add mapping to TOOL_MAP
2. Implement configuration parsing
3. Handle API key injection from environment
4. Add error handling for missing dependencies

### Execution Modes

- **single_agent**: Direct Agent instantiation
- **workflow**: Use Agno Workflow with steps
- **team**: Use Agno Team with member agents

## Error Handling Standards

All errors must be:
1. Descriptive with context
2. Logged with timestamps
3. Returned with appropriate status codes
4. Traceable to the blueprint that caused them

Error types:
- `BlueprintNotFoundError` → 404
- `ValidationError` → 400
- `CompilationError` → 500
- `ExecutionError` → 500
- `GuardrailViolation` → 429

## Tracing Requirements

Every tool invocation must be captured with:
- Tool name
- Timestamp (ISO 8601)
- Input parameters
- Output results
- Duration in milliseconds

Traces must be returned alongside agent responses in all interfaces (CLI, API, UI).

## File Organization

```
frankenagent/
├── config/      # Blueprint schema and loading
├── compiler/    # Blueprint → Agno transformation
├── tools/       # Tool registry and implementations
├── runtime/     # Execution orchestration and tracing
├── cli/         # Command-line interface
├── api/         # FastAPI HTTP server
└── ui/          # Minimal web interface
```

## Production Features

FrankenAgent Lab is a production-ready system with:

### ✅ Implemented Features

**Authentication & Authorization:**
- JWT authentication with secure token management
- OAuth integration (Google & GitHub)
- Password reset via email (Brevo integration)
- User profile management with avatar and bio
- API key management with Cloud KMS envelope encryption
- Token quota tracking per user

**Data Layer:**
- PostgreSQL database (Cloud SQL) with SQLAlchemy ORM
- Redis caching (Memorystore) for rate limiting
- Alembic migrations for schema management
- Session storage with conversation history
- User activity tracking and audit logs
- Blueprint versioning with soft deletes

**API & Execution:**
- Comprehensive REST API with FastAPI
- Blueprint validation and compilation
- Agent execution with tool call tracing
- Session-based conversation management
- Guardrails enforcement (max tool calls, timeouts)
- Rate limiting (per-user and global)
- Structured error handling with custom exceptions
- Request logging middleware

**Marketplace:**
- Public blueprint marketplace with categories
- Blueprint cloning and customization
- Rating system (1-5 stars)
- Tag-based organization
- Featured blueprints
- Download tracking

**Infrastructure:**
- Cloud Run deployment with auto-scaling (1-20 instances)
- Custom domain support with SSL/TLS
- Environment-based configuration (dev/test/production)
- Comprehensive logging (Cloud Logging)
- CORS configuration for frontend integration
- Health check endpoints
- Static file serving for web UI

**Visual Builder (Frontend):**
- Drag-and-drop canvas UI (React + TypeScript)
- Real-time blueprint preview (YAML/JSON)
- Live validation with instant feedback
- Auto-save functionality
- Export ready-to-use blueprints

### 🎯 Architecture Principles

Core principles maintained throughout:
- **Blueprint-first design**: All agent functionality expressed through YAML/JSON
- **Frankenstein metaphor**: Head, Arms, Legs, Heart, Spine components
- **Clear separation of concerns**: Config → Compiler → Runtime → API
- **Agno framework integration**: Direct mapping to Agno Agent/Workflow/Team
- **Comprehensive tracing**: Every tool call logged with inputs/outputs/duration
- **Security by design**: Envelope encryption, rate limiting, audit logs

## Future Extensibility

Design decisions must preserve compatibility with future features:

1. **Canvas UI**: Blueprint schema must remain stable
2. **Additional body parts**: Schema should be extensible (skin, eyes, voice)
3. **Multi-user**: Metadata fields should support user_id
4. **Database storage**: File-based storage should be abstracted

## Testing Philosophy

For MVP, focus on:
- Core functionality tests (required)
- Integration tests for end-to-end flows (required)
- Unit tests for critical paths (optional, marked with *)

Test using example blueprints as fixtures.
