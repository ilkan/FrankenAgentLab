---
inclusion: fileMatch
fileMatchPattern: "**/api/**/*.py"
---

# API Implementation Standards

## FastAPI Application Structure

```python
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

app = FastAPI(
    title="FrankenAgent Lab API",
    description="API for executing AI agents from blueprints",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
app.mount("/static", StaticFiles(directory="frankenagent/ui/static"), name="static")
```

## Request/Response Models

```python
class ExecuteRequest(BaseModel):
    """Request to execute an agent"""
    blueprint_id: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "blueprint_id": "simple_assistant",
                "message": "What is the weather in San Francisco?"
            }
        }

class ToolTraceResponse(BaseModel):
    """Tool invocation trace"""
    tool_name: str
    timestamp: str
    inputs: Dict[str, Any]
    outputs: Any
    duration_ms: float
    error: Optional[str] = None

class ExecuteResponse(BaseModel):
    """Response from agent execution"""
    response: str
    execution_trace: List[ToolTraceResponse]
    total_duration_ms: float
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "The weather in San Francisco is...",
                "execution_trace": [
                    {
                        "tool_name": "TavilyTools",
                        "timestamp": "2025-11-15T10:30:45.123Z",
                        "inputs": {"query": "weather San Francisco"},
                        "outputs": {"results": [...]},
                        "duration_ms": 234.5,
                        "error": None
                    }
                ],
                "total_duration_ms": 1250.3,
                "error": None
            }
        }

class BlueprintInfo(BaseModel):
    """Blueprint metadata"""
    id: str
    name: str
    description: str
    version: str
    execution_mode: str

class BlueprintListResponse(BaseModel):
    """List of available blueprints"""
    blueprints: List[BlueprintInfo]
```

## Endpoint Implementations

### POST /execute

```python
from frankenagent.runtime.service import RuntimeService

runtime = RuntimeService()

@app.post("/execute", response_model=ExecuteResponse, status_code=status.HTTP_200_OK)
async def execute_agent(request: ExecuteRequest):
    """
    Execute an agent from a blueprint
    
    - **blueprint_id**: ID of the blueprint to execute (filename without extension)
    - **message**: Message to send to the agent
    
    Returns the agent's response and execution trace.
    """
    try:
        result = runtime.execute(request.blueprint_id, request.message)
        
        if result.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error
            )
        
        return ExecuteResponse(
            response=result.response,
            execution_trace=[
                ToolTraceResponse(**trace.__dict__)
                for trace in result.execution_trace
            ],
            total_duration_ms=result.total_duration_ms
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint not found: {request.blueprint_id}"
        )
    except Exception as e:
        logging.error(f"Execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )
```

### GET /blueprints

```python
import os
from pathlib import Path

@app.get("/blueprints", response_model=BlueprintListResponse)
async def list_blueprints():
    """
    List all available blueprints
    
    Returns metadata for all blueprint files in the blueprints directory.
    """
    try:
        blueprints_dir = Path(runtime.blueprints_dir)
        blueprints = []
        
        for file_path in blueprints_dir.glob("*.yaml"):
            try:
                blueprint = runtime.loader.load_from_file(str(file_path))
                blueprints.append(BlueprintInfo(
                    id=file_path.stem,
                    name=blueprint.name,
                    description=blueprint.description,
                    version=blueprint.version,
                    execution_mode=blueprint.legs.execution_mode
                ))
            except Exception as e:
                logging.warning(f"Failed to load blueprint {file_path}: {e}")
        
        for file_path in blueprints_dir.glob("*.json"):
            try:
                blueprint = runtime.loader.load_from_file(str(file_path))
                blueprints.append(BlueprintInfo(
                    id=file_path.stem,
                    name=blueprint.name,
                    description=blueprint.description,
                    version=blueprint.version,
                    execution_mode=blueprint.legs.execution_mode
                ))
            except Exception as e:
                logging.warning(f"Failed to load blueprint {file_path}: {e}")
        
        return BlueprintListResponse(blueprints=blueprints)
    
    except Exception as e:
        logging.error(f"Failed to list blueprints: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list blueprints: {str(e)}"
        )
```

### GET /blueprints/{blueprint_id}

```python
@app.get("/blueprints/{blueprint_id}", response_model=BlueprintInfo)
async def get_blueprint(blueprint_id: str):
    """
    Get details for a specific blueprint
    
    - **blueprint_id**: ID of the blueprint (filename without extension)
    
    Returns blueprint metadata.
    """
    try:
        blueprint_path = runtime._find_blueprint(blueprint_id)
        blueprint = runtime.loader.load_from_file(blueprint_path)
        
        return BlueprintInfo(
            id=blueprint_id,
            name=blueprint.name,
            description=blueprint.description,
            version=blueprint.version,
            execution_mode=blueprint.legs.execution_mode
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint not found: {blueprint_id}"
        )
    except Exception as e:
        logging.error(f"Failed to get blueprint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blueprint: {str(e)}"
        )
```

### GET /health

```python
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "frankenagent-lab"}
```

## Error Response Format

All errors should follow this format:

```json
{
    "detail": "Error message describing what went wrong"
}
```

HTTP status codes:
- 200: Success
- 400: Bad request (validation error)
- 404: Blueprint not found
- 429: Guardrail violation (rate limit)
- 500: Internal server error

## CORS Configuration

For MVP, allow all origins. For production, restrict to specific domains:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Logging

Configure structured logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

Log all requests and errors:

```python
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

## Running the Server

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "frankenagent.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

Or via command line:

```bash
uvicorn frankenagent.api.server:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

FastAPI automatically generates:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Testing the API

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secure123", "full_name": "Test User"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secure123"}'

# Get current user (requires token)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_token>"

# List user blueprints
curl http://localhost:8000/api/blueprints \
  -H "Authorization: Bearer <your_token>"

# Run agent
curl -X POST http://localhost:8000/api/agents/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"blueprint_id": "uuid", "message": "Hello"}'

# List marketplace blueprints (no auth required)
curl http://localhost:8000/api/marketplace/blueprints

# Clone marketplace blueprint
curl -X POST http://localhost:8000/api/marketplace/blueprints/simple_assistant/clone \
  -H "Authorization: Bearer <your_token>"

# Health check
curl http://localhost:8000/
```
