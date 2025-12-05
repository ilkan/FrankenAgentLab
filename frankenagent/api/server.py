"""FastAPI server for FrankenAgent Lab HTTP API.

This module provides HTTP endpoints for executing agents from blueprints,
listing available blueprints, and serving the web UI.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from uuid import UUID
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from frankenagent.api.auth import get_current_user, router as auth_router
from frankenagent.api.keys import router as keys_router
from frankenagent.api.marketplace import router as marketplace_router
from frankenagent.api.blueprints import router as blueprints_router
from frankenagent.api.agents import router as agents_router
from frankenagent.api.sessions import router as sessions_router
from frankenagent.api.users import router as users_router
from frankenagent.api.mcp import router as mcp_router
from frankenagent.api.routes.credits import router as credits_router
from frankenagent.api.rate_limit_middleware import RateLimitMiddleware
from frankenagent.api.logging_middleware import RequestLoggingMiddleware
from frankenagent.services.rate_limit_service import RateLimitService
from frankenagent.services.activity_service import ActivityService
from frankenagent.services.blueprint_service import BlueprintService
from frankenagent.api.models import (
    ValidateRequest,
    ValidateResponse,
    RunRequest,
    RunResponse,
    LogsResponse,
    LogEntry,
    ToolCallLog,
    ComponentSchemasResponse,
    ImproveInstructionsRequest,
    ImproveInstructionsResponse,
)
from frankenagent.compiler.validator import BlueprintValidator
from frankenagent.compiler.compiler import AgentCompiler
from frankenagent.runtime.executor import ExecutionOrchestrator
from frankenagent.runtime.session_manager import SessionManager
from frankenagent.db.database import get_db
from frankenagent.db.models import User
from frankenagent.config.schemas import ComponentSchemaProvider
from frankenagent.config.instruction_improver import InstructionImprover
from frankenagent.exceptions import (
    FrankenAgentError,
    ValidationError,
    CompilationError,
    ExecutionError,
    GuardrailViolation,
    ToolError,
    ConfigurationError,
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FrankenAgent Lab API",
    description="A Frankenstein-inspired visual agent builder API",
    version="0.1.0",
)

# Add CORS middleware for frontend integration
# Security: Configure allowed origins based on environment
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_str:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]
else:
    # Development fallback - restrict to localhost only
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    logger.warning(
        "ALLOWED_ORIGINS not set in environment. Using development defaults. "
        "Set ALLOWED_ORIGINS in production!"
    )

# Add production origins
allowed_origins.extend([
    "https://storage.googleapis.com",
    "https://frankenagent.com",
    "https://www.frankenagent.com",
])

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize rate limiting service
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
rate_limit_service = RateLimitService(
    redis_host=redis_host,
    redis_port=redis_port,
    requests_per_minute=100,
    requests_per_day=1000
)

# Add request logging middleware (first, so it logs everything)
app.add_middleware(RequestLoggingMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, rate_limit_service=rate_limit_service)

# Include authentication and profile routers
app.include_router(auth_router)
app.include_router(users_router)

# Include API key management router
app.include_router(keys_router)

# Include marketplace router
app.include_router(marketplace_router)

# Include blueprint and session routers
app.include_router(blueprints_router)
app.include_router(agents_router)
app.include_router(sessions_router)

# Include MCP testing router
app.include_router(mcp_router)

# Include credit management router
app.include_router(credits_router)

# Initialize core components
validator = BlueprintValidator()
compiler = AgentCompiler()
session_manager = SessionManager()
activity_service = ActivityService()
blueprint_service = BlueprintService(validator)

# Initialize credit service
from frankenagent.services.credit_service import CreditService
credit_service = CreditService()

# Initialize API key service for user API key management (lazy initialization)
# Import here to avoid circular dependencies
from frankenagent.api.keys import get_api_key_service

# Try to initialize API key service, but don't fail if GCP credentials are missing
# This allows tests to run without GCP setup
try:
    api_key_service = get_api_key_service()
except Exception as e:
    logger.warning(f"Failed to initialize API key service: {e}. User API keys will not be available.")
    api_key_service = None

# Initialize orchestrator with API key service and credit service
orchestrator = ExecutionOrchestrator(
    compiler,
    session_manager,
    api_key_service=api_key_service,
    activity_service=activity_service,
    credit_service=credit_service,
)
schema_provider = ComponentSchemaProvider()
instruction_improver = InstructionImprover()


# Error response formatting helpers

def format_error_response(error: Exception, status_code: int = 500) -> Dict[str, Any]:
    """Format an exception into a standardized error response.
    
    Args:
        error: The exception to format
        status_code: HTTP status code for the error
        
    Returns:
        Dictionary with error details in standard format
    """
    error_type = type(error).__name__
    
    # Build base error response
    error_response = {
        "error": {
            "type": error_type,
            "message": str(error),
            "status_code": status_code
        }
    }
    
    # Add additional context for specific error types
    if isinstance(error, GuardrailViolation):
        error_response["error"]["guardrail_type"] = error.guardrail_type
    
    return error_response


def handle_frankenagent_error(error: FrankenAgentError) -> HTTPException:
    """Convert a FrankenAgentError to an appropriate HTTPException.
    
    Args:
        error: The FrankenAgentError to convert
        
    Returns:
        HTTPException with appropriate status code and formatted error
    """
    # Map error types to HTTP status codes
    if isinstance(error, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(error, ConfigurationError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(error, CompilationError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(error, GuardrailViolation):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(error, ToolError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(error, ExecutionError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Log the error
    logger.error(
        f"{type(error).__name__}: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "status_code": status_code
        }
    )
    
    return HTTPException(
        status_code=status_code,
        detail=format_error_response(error, status_code)
    )


# API Endpoints

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check."""
    return {
        "name": "FrankenAgent Lab API",
        "version": "0.1.0",
        "status": "running"
    }


@app.post("/api/blueprints/validate-and-compile", response_model=ValidateResponse, tags=["Blueprints"])
async def validate_and_compile(request: ValidateRequest):
    """Validate and optionally compile a blueprint.
    
    This endpoint validates a blueprint against the schema and business rules.
    If validation passes and compile=True, it also compiles the blueprint.
    
    Args:
        request: ValidateRequest containing blueprint and optional compile flag
        
    Returns:
        ValidateResponse with validation status, errors, and normalized blueprint
        
    Raises:
        HTTPException: 400 for malformed requests, 500 for compilation errors
    """
    logger.info(f"Validating blueprint (compile={request.compile})")
    
    try:
        # Validate the blueprint
        validation_result = validator.validate(request.blueprint)
        
        if not validation_result.valid:
            logger.warning(f"Blueprint validation failed with {len(validation_result.errors)} errors")
            return ValidateResponse(
                valid=False,
                errors=validation_result.errors
            )
        
        # If compile flag is set, attempt compilation
        if request.compile:
            try:
                compiled_agent = compiler.compile(validation_result.normalized_blueprint)
                logger.info(f"Blueprint compiled successfully: {validation_result.blueprint_id}")
            except CompilationError as e:
                logger.error(f"Compilation failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Compilation failed: {str(e)}"
                )
        
        logger.info(f"Blueprint validated successfully: {validation_result.blueprint_id}")
        
        return ValidateResponse(
            valid=True,
            blueprint_id=validation_result.blueprint_id,
            normalized_blueprint=validation_result.normalized_blueprint,
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@app.post("/api/agents/run", response_model=RunResponse, tags=["Execution"])
async def run_agent(
    request: RunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute an agent with a message using user's API keys.
    
    This endpoint accepts either a full blueprint or a blueprint_id reference,
    compiles it to an agent, executes it with the provided message using the
    authenticated user's API keys, and returns the response along with tool
    call logs and execution metadata.
    
    Args:
        request: RunRequest containing blueprint/blueprint_id, message, and optional session_id
        current_user: Authenticated user (from JWT token)
        db: Database session
        
    Returns:
        RunResponse with agent response, tool calls, and execution metrics
        
    Raises:
        HTTPException: 400 for validation errors or missing API key,
                      401 for authentication errors,
                      404 if blueprint_id not found,
                      500 for compilation or execution errors
    """
    user_id = current_user.id
    logger.info(
        f"Run request: user_id={user_id}, "
        f"message_length={len(request.message)}, "
        f"session_id={request.session_id}"
    )
    
    try:
        blueprint_payload: Dict[str, Any]
        agent_id: Optional[UUID] = None

        if request.blueprint_id:
            blueprint = blueprint_service.get_blueprint(
                db=db,
                blueprint_id=request.blueprint_id,
                user_id=current_user.id,
            )
            if not blueprint:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Blueprint not found or you do not have access.",
                )
            blueprint_payload = blueprint.blueprint_data
            agent_id = blueprint.id
        else:
            if not request.blueprint:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either 'blueprint' or 'blueprint_id' must be provided",
                )
            validation_result = validator.validate(request.blueprint)
            if not validation_result.valid:
                logger.warning(
                    "Blueprint validation failed with %d errors",
                    len(validation_result.errors),
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Blueprint validation failed",
                        "errors": [
                            {"field": e.field, "message": e.message}
                            for e in validation_result.errors
                        ],
                    },
                )
            blueprint_payload = validation_result.normalized_blueprint
        
        execution_result = await orchestrator.execute(
            blueprint=blueprint_payload,
            message=request.message,
            session_id=request.session_id,
            user_id=user_id,
            db=db,
            agent_id=agent_id,
        )
        
        # Build response
        response = RunResponse(
            response=execution_result.response,
            session_id=execution_result.session_id,
            tool_calls=execution_result.tool_calls,
            guardrails_triggered=execution_result.guardrails_triggered,
            total_latency_ms=execution_result.total_latency_ms,
            error=execution_result.error
        )
        
        if execution_result.success:
            logger.info(
                f"Run completed successfully: {len(execution_result.tool_calls)} tool calls, "
                f"{execution_result.total_latency_ms}ms total"
            )
        else:
            logger.warning(f"Run failed: {execution_result.error}")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except CompilationError as e:
        logger.error(f"Compilation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compilation failed: {str(e)}"
        )
    except ExecutionError as e:
        logger.error(f"Execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@app.get("/api/agents/logs", response_model=LogsResponse, tags=["Logs"])
async def get_logs(session_id: str = Query(..., description="Session identifier")):
    """Retrieve execution logs for a session.
    
    This endpoint returns all logged events for a given session, including
    tool calls, execution metadata, and any errors that occurred.
    
    Args:
        session_id: Session identifier (query parameter)
        
    Returns:
        LogsResponse with session logs in chronological order
        
    Raises:
        HTTPException: 404 if session not found, 500 for unexpected errors
    """
    logger.info(f"Retrieving logs for session: {session_id}")
    
    try:
        # Get logs from session manager
        logs = session_manager.get_logs(session_id)
        
        if not logs and session_id not in session_manager.sessions:
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Convert to LogEntry models
        log_entries = [
            LogEntry(
                timestamp=log["timestamp"],
                event_type=log["event_type"],
                tool_name=log.get("tool_name"),
                args=log.get("args"),
                duration_ms=log.get("duration_ms"),
                success=log.get("success"),
                result=log.get("result"),
                error=log.get("error"),
                details=log.get("details")
            )
            for log in logs
        ]
        
        logger.info(f"Retrieved {len(log_entries)} log entries for session {session_id}")
        
        return LogsResponse(
            session_id=session_id,
            logs=log_entries
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve logs: {str(e)}"
        )


@app.get("/api/components/schemas", response_model=ComponentSchemasResponse, tags=["Configuration"])
async def get_component_schemas():
    """Get configuration schemas for all component types.
    
    This endpoint returns schemas for all agent component types (head, arms, legs,
    heart, spine) that can be used by the frontend to build dynamic configuration
    forms with proper validation and available options.
    
    Returns:
        ComponentSchemasResponse with schemas for all component types
        
    Raises:
        HTTPException: 500 for schema generation failures
    """
    logger.info("Retrieving component schemas")
    
    try:
        # Get all schemas from the provider
        schemas = schema_provider.get_all_schemas()
        
        logger.info("Component schemas retrieved successfully")
        
        return ComponentSchemasResponse(
            head=schemas["head"],
            arms=schemas["arms"],
            legs=schemas["legs"],
            heart=schemas["heart"],
            spine=schemas["spine"]
        )
        
    except Exception as e:
        logger.error(f"Error generating component schemas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate component schemas: {str(e)}"
        )


@app.post("/api/instructions/improve", response_model=ImproveInstructionsResponse, tags=["Configuration"])
async def improve_instructions(request: ImproveInstructionsRequest):
    """Use LLM to improve agent instructions.
    
    This endpoint uses an LLM to help users refine their system prompts and
    instructions. It preserves the user's intent while enhancing clarity and
    effectiveness.
    
    Args:
        request: ImproveInstructionsRequest with current instructions, goal, and context
        
    Returns:
        ImproveInstructionsResponse with improved instructions, explanation, and suggestions
        
    Raises:
        HTTPException: 400 for invalid requests, 500 for improvement failures
    """
    logger.info(f"Improving instructions: goal='{request.improvement_goal}'")
    
    try:
        # Validate input
        if not request.current_instructions or not request.current_instructions.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="current_instructions cannot be empty"
            )
        
        if not request.improvement_goal or not request.improvement_goal.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="improvement_goal cannot be empty"
            )
        
        # Call the instruction improver service
        result = instruction_improver.improve(
            current_instructions=request.current_instructions,
            improvement_goal=request.improvement_goal,
            context=request.context
        )
        
        logger.info("Instructions improved successfully")
        
        return ImproveInstructionsResponse(
            improved_instructions=result["improved_instructions"],
            explanation=result["explanation"],
            suggestions=result["suggestions"]
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Error improving instructions: {e}", exc_info=True)
        # On error, return original instructions with error message
        return ImproveInstructionsResponse(
            improved_instructions=request.current_instructions,
            explanation=f"Failed to improve instructions: {str(e)}",
            suggestions=[]
        )



# Static file serving for web UI
# Mount static files at /static path
static_dir = Path(__file__).parent.parent / "ui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Mounted static files from: {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")


# Application startup event
@app.on_event("startup")
async def startup_event():
    """Configure logging, validate configuration, and log startup information."""
    from frankenagent.logging_config import setup_logging
    from frankenagent.config.environment import EnvironmentConfig
    import os
    
    # Step 1: Load and validate environment configuration
    # This must happen first to ensure we have valid configuration
    try:
        config = EnvironmentConfig.load()
        
        # Validate configuration and fail fast if invalid
        config.fail_fast_if_invalid()
        
        # Log successful configuration loading (without secrets)
        logger.info(
            f"Configuration loaded successfully",
            extra={
                "environment": config.environment.value,
                "database_type": "sqlite" if "sqlite" in config.database_url else "postgresql",
                "frontend_url": config.frontend_url,
                "backend_url": config.backend_url,
                "ssl_verify": config.ssl_verify,
                "log_level": config.log_level,
                "agno_debug": config.agno_debug,
            }
        )
        
        # Log OAuth configuration status (without secrets)
        oauth_providers = []
        if config.google_client_id:
            oauth_providers.append("Google")
        if config.github_client_id:
            oauth_providers.append("GitHub")
        
        if oauth_providers:
            logger.info(f"OAuth providers configured: {', '.join(oauth_providers)}")
        else:
            logger.warning("No OAuth providers configured")
        
        # Log LLM provider status (without keys)
        llm_providers = []
        if config.openai_api_key:
            llm_providers.append("OpenAI")
        if config.anthropic_api_key:
            llm_providers.append("Anthropic")
        
        if llm_providers:
            logger.info(f"LLM providers configured: {', '.join(llm_providers)}")
        else:
            logger.warning("No LLM API keys configured - agent execution will require user API keys")
        
    except ValueError as e:
        # Configuration validation failed - log error and exit
        logger.error(f"Configuration validation failed: {e}")
        # Re-raise to prevent application startup
        raise
    except Exception as e:
        # Unexpected error during configuration loading
        logger.error(f"Unexpected error loading configuration: {e}", exc_info=True)
        raise
    
    # Step 2: Configure logging based on validated configuration
    log_level = config.log_level
    log_format = os.getenv("LOG_FORMAT", "detailed")
    
    setup_logging(level=log_level, format_style=log_format)
    
    # Add environment context to all subsequent log messages
    logger.info(
        "FrankenAgent Lab API starting up",
        extra={"environment": config.environment.value}
    )
    
    # Step 3: Initialize database
    try:
        from frankenagent.db.database import engine
        from frankenagent.db.models import Base

        logger.info(
            "Creating database tables if they don't exist...",
            extra={"environment": config.environment.value}
        )
        Base.metadata.create_all(bind=engine)
        logger.info(
            "Database tables initialized successfully",
            extra={"environment": config.environment.value}
        )
    except Exception as e:
        logger.error(
            f"Failed to initialize database tables: {e}",
            extra={"environment": config.environment.value}
        )
    
    # Step 4: Log final startup status
    logger.info(
        "Core components initialized: validator, compiler, session_manager, orchestrator",
        extra={"environment": config.environment.value}
    )
    logger.info(
        f"Logging configured: level={log_level}, format={log_format}",
        extra={"environment": config.environment.value}
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    from frankenagent.config.environment import get_config
    
    try:
        config = get_config()
        logger.info(
            "FrankenAgent Lab API shutting down",
            extra={"environment": config.environment.value}
        )
    except Exception:
        # If config not available, log without environment context
        logger.info("FrankenAgent Lab API shutting down")
