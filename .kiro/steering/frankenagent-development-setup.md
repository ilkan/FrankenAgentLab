---
inclusion: always
---

# FrankenAgent Lab Development Setup

## Prerequisites

- Python 3.11 or higher
- Poetry (Python package manager)
- Git
- API keys for LLM providers and tools

## Initial Setup

### 1. Install Poetry

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or via pip
pip install poetry
```

### 2. Create Project Structure

```bash
mkdir frankenagent-lab
cd frankenagent-lab

# Initialize Poetry project
poetry init --name frankenagent --python "^3.11"
```

### 3. Add Dependencies

```bash
# Core dependencies
poetry add agno pydantic pyyaml click fastapi uvicorn python-dotenv

# Development dependencies
poetry add --group dev pytest pytest-asyncio httpx black ruff mypy
```

### 4. Create Folder Structure

```bash
mkdir -p frankenagent/{config,compiler,tools,runtime,cli,api,ui/static}
mkdir -p blueprints tests
touch frankenagent/__init__.py
touch frankenagent/{config,compiler,tools,runtime,cli,api}/__init__.py
```

### 5. Configure Environment Variables

Create `.env` file:

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

Create `.env.example` (without actual keys):

```bash
cp .env .env.example
# Edit .env.example to remove actual key values
```

### 6. Create .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
```

## Development Workflow

### Install Dependencies

```bash
poetry install
```

### Activate Virtual Environment

```bash
poetry shell
```

### Run Tests

```bash
poetry run pytest
poetry run pytest -v  # Verbose
poetry run pytest tests/test_compiler.py  # Specific file
```

### Code Formatting

```bash
# Format code with Black
poetry run black frankenagent tests

# Lint with Ruff
poetry run ruff check frankenagent tests

# Type checking with mypy
poetry run mypy frankenagent
```

### Run CLI

```bash
# List blueprints
poetry run frankenagent list

# Run agent
poetry run frankenagent run blueprints/simple_assistant.yaml "Hello"
```

### Run API Server

```bash
# Development mode with auto-reload
poetry run uvicorn frankenagent.api.server:app --reload

# Production mode
poetry run uvicorn frankenagent.api.server:app --host 0.0.0.0 --port 8000
```

### Access Web UI

```bash
open http://localhost:8000/static/index.html
```

## Project Configuration Files

### pyproject.toml

```toml
[tool.poetry]
name = "frankenagent"
version = "0.1.0"
description = "A Frankenstein-inspired visual agent builder"
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
agno = "^0.1.0"
pydantic = "^2.0"
pyyaml = "^6.0"
click = "^8.1"
fastapi = "^0.104"
uvicorn = "^0.24"
python-dotenv = "^1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
httpx = "^0.25"
black = "^23.0"
ruff = "^0.1"
mypy = "^1.7"

[tool.poetry.scripts]
frankenagent = "frankenagent.cli.main:cli"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Common Development Tasks

### Add a New Tool Type

1. Update `ToolRegistry.TOOL_MAP` in `frankenagent/tools/registry.py`
2. Add tool configuration handling
3. Update documentation
4. Add example blueprint using the tool

### Add a New Execution Mode

1. Add mode to `LegsConfig.execution_mode` enum
2. Implement `_build_<mode>()` in `BlueprintCompiler`
3. Add example blueprint
4. Update documentation

### Debug Agent Execution

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use breakpoints
import pdb; pdb.set_trace()
```

### Test API Endpoints

```bash
# Using curl
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"blueprint_id": "simple_assistant", "message": "test"}'

# Using httpx in Python
import httpx
response = httpx.post(
    "http://localhost:8000/execute",
    json={"blueprint_id": "simple_assistant", "message": "test"}
)
print(response.json())
```

## Troubleshooting

### Poetry Installation Issues

```bash
# Clear cache
poetry cache clear pypi --all

# Reinstall dependencies
rm poetry.lock
poetry install
```

### Import Errors

```bash
# Ensure you're in the virtual environment
poetry shell

# Or prefix commands with poetry run
poetry run python -c "import frankenagent"
```

### API Key Issues

```bash
# Verify .env file is loaded
poetry run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn frankenagent.api.server:app --port 8001
```

## Quick Start Commands

```bash
# Complete setup from scratch
git clone <repo>
cd frankenagent-lab
poetry install
cp .env.example .env
# Edit .env with your API keys
poetry run uvicorn frankenagent.api.server:app --reload
# Open http://localhost:8000/static/index.html
```

## Documentation

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- README.md: Project overview and usage
- Spec files: `.kiro/specs/frankenagent-lab/`
