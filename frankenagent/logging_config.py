"""Logging configuration for FrankenAgent Lab.

This module provides centralized logging configuration with structured
logging support for execution events, tool calls, and errors.

Includes API key sanitization to prevent accidental logging of sensitive credentials.
Supports both local development logging and Google Cloud Logging for production.
"""

import logging
import sys
import re
import os
from typing import Optional


class APIKeySanitizingFilter(logging.Filter):
    """
    Filter to automatically redact API keys from logs.
    
    Prevents accidental logging of sensitive API keys by replacing them
    with redacted placeholders. Supports multiple LLM provider key formats:
    - OpenAI: sk-...
    - Anthropic: sk-ant-...
    - Groq: gsk_...
    - Gemini/Google: AIza...
    
    Security:
    - Applied to all loggers automatically
    - Sanitizes both message and args
    - Prevents keys in error messages and debug output
    """
    
    # Regex patterns for different API key formats
    API_KEY_PATTERNS = [
        # OpenAI keys: sk-... (20+ alphanumeric chars)
        (re.compile(r'sk-[a-zA-Z0-9]{20,}'), 'sk-***REDACTED***'),
        # Anthropic keys: sk-ant-... (20+ alphanumeric/hyphen chars)
        (re.compile(r'sk-ant-[a-zA-Z0-9-]{20,}'), 'sk-ant-***REDACTED***'),
        # Groq keys: gsk_... (20+ alphanumeric chars)
        (re.compile(r'gsk_[a-zA-Z0-9]{20,}'), 'gsk_***REDACTED***'),
        # Google/Gemini keys: AIza... (20+ alphanumeric/underscore/hyphen chars)
        (re.compile(r'AIza[a-zA-Z0-9_-]{20,}'), 'AIza***REDACTED***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Sanitize log record before writing.
        
        Replaces any API keys in the message or args with redacted placeholders.
        
        Args:
            record: Log record to sanitize
            
        Returns:
            True (always allow record through after sanitization)
        """
        # Sanitize message
        if isinstance(record.msg, str):
            for pattern, replacement in self.API_KEY_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        
        # Sanitize args
        if record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.API_KEY_PATTERNS:
                        arg = pattern.sub(replacement, arg)
                sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        
        return True


def setup_logging(
    level: str = "INFO",
    format_style: str = "detailed",
    use_cloud_logging: bool = None
) -> None:
    """Configure logging for the FrankenAgent Lab application.
    
    Sets up Python logging with appropriate levels, formatters, and handlers.
    In production (ENVIRONMENT=production), uses Google Cloud Logging for
    centralized log aggregation and analysis.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_style: Format style - 'detailed' for development, 'simple' for production
        use_cloud_logging: Whether to use Google Cloud Logging. If None, auto-detects
                          based on ENVIRONMENT variable.
        
    Example:
        >>> setup_logging(level="DEBUG", format_style="detailed")
        >>> setup_logging(level="INFO", use_cloud_logging=True)  # Force Cloud Logging
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Auto-detect cloud logging if not specified
    if use_cloud_logging is None:
        environment = os.getenv("ENVIRONMENT", "development")
        use_cloud_logging = environment == "production"
    
    # Configure Cloud Logging for production
    if use_cloud_logging:
        try:
            from google.cloud import logging as cloud_logging
            
            # Initialize Cloud Logging client
            client = cloud_logging.Client()
            
            # Setup Cloud Logging handler
            client.setup_logging(log_level=numeric_level)
            
            logger = logging.getLogger(__name__)
            logger.info("Google Cloud Logging configured successfully")
            
        except ImportError:
            # Fallback to standard logging if google-cloud-logging not installed
            logger = logging.getLogger(__name__)
            logger.warning(
                "google-cloud-logging not installed, falling back to standard logging. "
                "Install with: pip install google-cloud-logging"
            )
            use_cloud_logging = False
        except Exception as e:
            # Fallback to standard logging if Cloud Logging setup fails
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to setup Cloud Logging: {e}. Using standard logging.")
            use_cloud_logging = False
    
    # Configure standard logging (development or fallback)
    if not use_cloud_logging:
        # Define format based on style
        if format_style == "detailed":
            log_format = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
            )
        else:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Configure root logger
        logging.basicConfig(
            level=numeric_level,
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Standard logging configured: level={level}, format={format_style}")
    
    # Apply API key sanitization filter to root logger (always)
    root_logger = logging.getLogger()
    root_logger.addFilter(APIKeySanitizingFilter())
    
    # Set specific log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google.cloud").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("API key sanitization filter enabled")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return logging.getLogger(name)


class StructuredLogger:
    """Wrapper for structured logging with context.
    
    Provides methods for logging execution events with structured context
    that can be easily parsed and analyzed.
    
    Example:
        >>> logger = StructuredLogger("execution")
        >>> logger.log_execution_start(blueprint_id="bp_123", message="Hello")
        >>> logger.log_tool_call(tool="tavily_search", duration_ms=234, success=True)
        >>> logger.log_execution_complete(latency_ms=1523)
    """
    
    def __init__(self, name: str):
        """Initialize structured logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
    
    def log_execution_start(
        self,
        blueprint_id: str,
        message: str,
        session_id: Optional[str] = None
    ) -> None:
        """Log the start of an agent execution.
        
        Args:
            blueprint_id: Blueprint identifier
            message: User message being processed
            session_id: Optional session identifier
        """
        self.logger.info(
            "Execution started",
            extra={
                "event": "execution_start",
                "blueprint_id": blueprint_id,
                "message_length": len(message),
                "session_id": session_id
            }
        )
    
    def log_execution_complete(
        self,
        blueprint_id: str,
        latency_ms: int,
        tool_calls: int,
        success: bool,
        session_id: Optional[str] = None
    ) -> None:
        """Log the completion of an agent execution.
        
        Args:
            blueprint_id: Blueprint identifier
            latency_ms: Total execution latency in milliseconds
            tool_calls: Number of tool calls made
            success: Whether execution succeeded
            session_id: Optional session identifier
        """
        self.logger.info(
            f"Execution {'completed' if success else 'failed'}",
            extra={
                "event": "execution_complete",
                "blueprint_id": blueprint_id,
                "latency_ms": latency_ms,
                "tool_calls": tool_calls,
                "success": success,
                "session_id": session_id
            }
        )
    
    def log_tool_call(
        self,
        tool_name: str,
        duration_ms: int,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Log a tool invocation.
        
        Args:
            tool_name: Name of the tool invoked
            duration_ms: Tool execution duration in milliseconds
            success: Whether the tool call succeeded
            error: Optional error message if failed
        """
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"Tool call: {tool_name} ({'success' if success else 'failed'})",
            extra={
                "event": "tool_call",
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                "success": success,
                "error": error
            }
        )
    
    def log_guardrail_violation(
        self,
        guardrail_type: str,
        message: str,
        session_id: Optional[str] = None
    ) -> None:
        """Log a guardrail violation.
        
        Args:
            guardrail_type: Type of guardrail violated
            message: Violation message
            session_id: Optional session identifier
        """
        self.logger.warning(
            f"Guardrail violated: {guardrail_type}",
            extra={
                "event": "guardrail_violation",
                "guardrail_type": guardrail_type,
                "violation_message": message,
                "session_id": session_id
            }
        )
    
    def log_llm_error(
        self,
        provider: str,
        model: str,
        error: str,
        session_id: Optional[str] = None
    ) -> None:
        """Log an LLM provider error.
        
        Args:
            provider: LLM provider name (openai, anthropic)
            model: Model identifier
            error: Error message
            session_id: Optional session identifier
        """
        self.logger.error(
            f"LLM error: {provider}/{model}",
            extra={
                "event": "llm_error",
                "provider": provider,
                "model": model,
                "error": error,
                "session_id": session_id
            }
        )
    
    def log_validation_error(
        self,
        blueprint_name: str,
        error_count: int,
        errors: list
    ) -> None:
        """Log a blueprint validation error.
        
        Args:
            blueprint_name: Name of the blueprint
            error_count: Number of validation errors
            errors: List of validation error details
        """
        self.logger.warning(
            f"Blueprint validation failed: {blueprint_name}",
            extra={
                "event": "validation_error",
                "blueprint_name": blueprint_name,
                "error_count": error_count,
                "errors": errors
            }
        )
    
    def log_compilation_error(
        self,
        blueprint_name: str,
        error: str
    ) -> None:
        """Log a blueprint compilation error.
        
        Args:
            blueprint_name: Name of the blueprint
            error: Error message
        """
        self.logger.error(
            f"Blueprint compilation failed: {blueprint_name}",
            extra={
                "event": "compilation_error",
                "blueprint_name": blueprint_name,
                "error": error
            }
        )
