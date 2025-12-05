---
inclusion: manual
---

# FrankenAgent Lab Steering Documents

This directory contains comprehensive guidance for implementing FrankenAgent Lab. These steering documents provide context, patterns, and best practices that complement the spec files.

## Document Overview

### Always Included (Core Guidance)

These documents are always included in context when working on FrankenAgent Lab:

1. **frankenagent-architecture.md**
   - Core metaphor preservation (head/arms/legs/heart/spine)
   - Blueprint-first design principles
   - Agno integration patterns
   - Error handling standards
   - MVP constraints and future extensibility

2. **frankenagent-best-practices.md**
   - Code organization principles
   - Coding standards and conventions
   - Testing best practices
   - Performance considerations
   - Security guidelines
   - Logging standards
   - Common pitfalls to avoid

3. **frankenagent-development-setup.md**
   - Prerequisites and installation
   - Project structure setup
   - Development workflow
   - Configuration files
   - Common development tasks
   - Troubleshooting guide

### Context-Specific (Included by File Match)

These documents are automatically included when working on specific modules:

4. **frankenagent-blueprint-schema.md** (fileMatch: `**/config/**/*.py`)
   - Complete schema structure
   - Pydantic model implementation
   - Validation rules
   - File format support
   - Supported tool types
   - Execution mode details

5. **frankenagent-compiler-patterns.md** (fileMatch: `**/compiler/**/*.py`)
   - Compiler architecture
   - Tool building patterns
   - Single agent, workflow, and team patterns
   - Memory configuration
   - Guardrails application
   - Error handling

6. **frankenagent-runtime-implementation.md** (fileMatch: `**/runtime/**/*.py`)
   - Runtime execution patterns
   - Agno integration best practices
   - Guardrail enforcement
   - Session management
   - Tool call logging
   - Error handling patterns
   - Performance considerations

7. **frankenagent-execution-tracing.md** (fileMatch: `**/runtime/**/*.py`)
   - Tracing requirements
   - Data structures
   - Tracing wrapper pattern
   - RuntimeService integration
   - Trace formatting (CLI, API, UI)
   - Guardrail tracing
   - Performance considerations

8. **frankenagent-api-standards.md** (fileMatch: `**/api/**/*.py`)
   - FastAPI application structure
   - Request/response models
   - Endpoint implementations
   - Error response format
   - CORS configuration
   - Logging
   - Testing the API

9. **frankenagent-visual-builder.md** (fileMatch: `**/frontend/**/*`)
   - Visual builder architecture
   - React + TypeScript patterns
   - Zustand state management
   - Drag and drop implementation
   - Real-time validation
   - Blueprint export (YAML/JSON)
   - Backend integration
   - Component configuration UIs
   - Styling and theming
   - Performance optimization

## How to Use These Documents

### During Implementation

When implementing a task from `tasks.md`:

1. Read the relevant spec document (requirements.md, design.md, tasks.md)
2. Check the always-included steering docs for general guidance
3. Review the context-specific steering doc for your module
4. Follow the patterns and standards documented
5. Reference example code snippets

### When Adding Features

1. Ensure new features align with the Frankenstein metaphor
2. Follow the blueprint-first design principle
3. Update relevant steering docs if patterns change
4. Add examples to demonstrate new capabilities

### When Debugging

1. Check error handling standards in architecture.md
2. Review logging best practices
3. Consult troubleshooting sections in development-setup.md
4. Verify you're following the documented patterns

## Quick Reference

### Key Concepts

- **Agent Blueprint**: YAML/JSON config defining agent anatomy
- **Compiler**: Transforms blueprints into Agno agents
- **Runtime Service**: Orchestrates execution with tracing
- **Execution Trace**: Log of tool activations during execution

### File Locations

```
.kiro/specs/
├── frankenagent-lab/          # Original full system spec
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
└── agent-runtime/             # Core agent runtime spec
    ├── requirements.md        # Runtime requirements (validation, compilation, execution)
    ├── design.md              # Runtime architecture and Agno integration
    └── tasks.md               # Runtime implementation tasks

.kiro/steering/
├── frankenagent-architecture.md              # Always included
├── frankenagent-best-practices.md            # Always included
├── frankenagent-development-setup.md         # Always included
├── frankenagent-blueprint-schema.md          # fileMatch: **/config/**/*.py
├── frankenagent-compiler-patterns.md         # fileMatch: **/compiler/**/*.py
├── frankenagent-runtime-implementation.md    # fileMatch: **/runtime/**/*.py
├── frankenagent-execution-tracing.md         # fileMatch: **/runtime/**/*.py
├── frankenagent-api-standards.md             # fileMatch: **/api/**/*.py
└── frankenagent-visual-builder.md            # fileMatch: **/frontend/**/*
```

### Core Patterns

1. **Blueprint → Compile → Execute → Trace**
   - Never bypass this flow
   - Always validate before compiling
   - Always trace during execution

2. **Error Handling**
   - Use specific exception types
   - Provide descriptive error messages
   - Log with context

3. **Testing**
   - Use fixtures for common test data
   - Mock external dependencies
   - Test each execution mode separately

4. **Code Organization**
   - One responsibility per module
   - Dependencies flow downward
   - Private methods start with underscore

## Getting Started

If you're new to FrankenAgent Lab:

1. Read **frankenagent-architecture.md** for the big picture
2. Follow **frankenagent-development-setup.md** to set up your environment
3. Review **frankenagent-best-practices.md** for coding standards
4. Choose your implementation path:
   - **Core Runtime**: Start with `.kiro/specs/agent-runtime/tasks.md` for the backend agent execution system
   - **Full System**: Start with `.kiro/specs/frankenagent-lab/tasks.md` for the complete application
5. Reference module-specific steering docs as needed

## Updating Steering Documents

When patterns evolve or new best practices emerge:

1. Update the relevant steering document
2. Ensure consistency across all steering docs
3. Update examples to reflect new patterns
4. Consider if spec documents need updates too

## Questions?

If you're unsure about:
- **Architecture decisions** → Check frankenagent-architecture.md
- **How to implement a feature** → Check the module-specific steering doc
- **Coding standards** → Check frankenagent-best-practices.md
- **Setup issues** → Check frankenagent-development-setup.md

## Current Project Status

FrankenAgent Lab has evolved beyond MVP with comprehensive features:

### ✅ Completed Features
- Core functionality (blueprint → compile → execute → trace)
- Visual drag-and-drop builder (React + TypeScript)
- HTTP Tool for external API integration
- Production deployment to Google Cloud Platform
- Multi-tenant authentication with JWT
- OAuth authentication (Google & GitHub)
- Agent marketplace for sharing
- PostgreSQL + Redis for persistence
- Comprehensive monitoring and alerting
- Custom domain support with SSL
- Rate limiting and security hardening

### 🎯 Focus Areas
- Maintain code quality and documentation
- Ensure frontend-backend integration stability
- Optimize performance and scalability
- Enhance security and guardrails
- Improve developer experience

### 📚 Key Documentation
- **Visual Builder**: [frontend/ARCHITECTURE.md](../frontend/ARCHITECTURE.md)
- **Integration**: [README_INTEGRATION.md](../README_INTEGRATION.md)
- **Production**: [PRODUCTION_DEPLOYMENT_GUIDE.md](../PRODUCTION_DEPLOYMENT_GUIDE.md)
- **OAuth Setup**: [docs/OAUTH_SETUP.md](../docs/OAUTH_SETUP.md)
