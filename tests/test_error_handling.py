"""Tests for error handling and logging functionality."""

import pytest
from frankenagent.exceptions import (
    FrankenAgentError,
    ValidationError,
    CompilationError,
    ExecutionError,
    GuardrailViolation,
    ToolError,
    ConfigurationError,
    BlueprintNotFoundError,
)
from frankenagent.logging_config import setup_logging, StructuredLogger


def test_exception_hierarchy():
    """Test that all custom exceptions inherit from FrankenAgentError."""
    # Test ValidationError
    try:
        raise ValidationError("Test validation error")
    except FrankenAgentError as e:
        assert isinstance(e, ValidationError)
        assert str(e) == "Test validation error"
    
    # Test CompilationError
    try:
        raise CompilationError("Test compilation error")
    except FrankenAgentError as e:
        assert isinstance(e, CompilationError)
    
    # Test ExecutionError
    try:
        raise ExecutionError("Test execution error")
    except FrankenAgentError as e:
        assert isinstance(e, ExecutionError)
    
    # Test ToolError
    try:
        raise ToolError("Test tool error")
    except FrankenAgentError as e:
        assert isinstance(e, ToolError)
    
    # Test ConfigurationError
    try:
        raise ConfigurationError("Test config error")
    except FrankenAgentError as e:
        assert isinstance(e, ConfigurationError)
    
    # Test BlueprintNotFoundError
    try:
        raise BlueprintNotFoundError("Test not found error")
    except FrankenAgentError as e:
        assert isinstance(e, BlueprintNotFoundError)


def test_guardrail_violation_attributes():
    """Test that GuardrailViolation stores guardrail type."""
    try:
        raise GuardrailViolation("max_tool_calls", "Exceeded 10 calls")
    except GuardrailViolation as e:
        assert e.guardrail_type == "max_tool_calls"
        assert "Exceeded 10 calls" in str(e)
    
    try:
        raise GuardrailViolation("timeout_seconds", "Execution exceeded 60s")
    except GuardrailViolation as e:
        assert e.guardrail_type == "timeout_seconds"
        assert "60s" in str(e)


def test_logging_setup():
    """Test that logging can be configured."""
    # Test with INFO level
    setup_logging(level="INFO", format_style="simple")
    
    # Test with DEBUG level
    setup_logging(level="DEBUG", format_style="detailed")
    
    # Should not raise any exceptions
    assert True


def test_structured_logger_execution_events():
    """Test structured logger for execution events."""
    logger = StructuredLogger("test_execution")
    
    # Test execution start logging
    logger.log_execution_start(
        blueprint_id="bp_test123",
        message="Test message",
        session_id="sess_test456"
    )
    
    # Test execution complete logging
    logger.log_execution_complete(
        blueprint_id="bp_test123",
        latency_ms=1500,
        tool_calls=3,
        success=True,
        session_id="sess_test456"
    )
    
    # Test failed execution logging
    logger.log_execution_complete(
        blueprint_id="bp_test123",
        latency_ms=500,
        tool_calls=0,
        success=False,
        session_id="sess_test456"
    )
    
    # Should not raise any exceptions
    assert True


def test_structured_logger_tool_calls():
    """Test structured logger for tool call events."""
    logger = StructuredLogger("test_tools")
    
    # Test successful tool call
    logger.log_tool_call(
        tool_name="tavily_search",
        duration_ms=234,
        success=True
    )
    
    # Test failed tool call
    logger.log_tool_call(
        tool_name="http_tool",
        duration_ms=100,
        success=False,
        error="Connection timeout"
    )
    
    # Should not raise any exceptions
    assert True


def test_structured_logger_guardrail_violations():
    """Test structured logger for guardrail violations."""
    logger = StructuredLogger("test_guardrails")
    
    logger.log_guardrail_violation(
        guardrail_type="max_tool_calls",
        message="Exceeded limit of 10 calls",
        session_id="sess_test789"
    )
    
    logger.log_guardrail_violation(
        guardrail_type="timeout_seconds",
        message="Execution exceeded 60s timeout",
        session_id="sess_test789"
    )
    
    # Should not raise any exceptions
    assert True


def test_structured_logger_llm_errors():
    """Test structured logger for LLM provider errors."""
    logger = StructuredLogger("test_llm")
    
    logger.log_llm_error(
        provider="openai",
        model="gpt-4o",
        error="Rate limit exceeded",
        session_id="sess_test999"
    )
    
    logger.log_llm_error(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        error="Invalid API key",
        session_id="sess_test999"
    )
    
    # Should not raise any exceptions
    assert True


def test_structured_logger_validation_errors():
    """Test structured logger for validation errors."""
    logger = StructuredLogger("test_validation")
    
    errors = [
        {"field": "head.provider", "message": "Unsupported provider"},
        {"field": "arms[0].type", "message": "Unknown tool type"}
    ]
    
    logger.log_validation_error(
        blueprint_name="Test Blueprint",
        error_count=2,
        errors=errors
    )
    
    # Should not raise any exceptions
    assert True


def test_structured_logger_compilation_errors():
    """Test structured logger for compilation errors."""
    logger = StructuredLogger("test_compilation")
    
    logger.log_compilation_error(
        blueprint_name="Test Blueprint",
        error="Failed to build model: Invalid configuration"
    )
    
    # Should not raise any exceptions
    assert True


def test_catch_all_frankenagent_errors():
    """Test that all custom errors can be caught with FrankenAgentError."""
    errors_to_test = [
        ValidationError("validation"),
        CompilationError("compilation"),
        ExecutionError("execution"),
        GuardrailViolation("max_tool_calls", "guardrail"),
        ToolError("tool"),
        ConfigurationError("config"),
        BlueprintNotFoundError("not found"),
    ]
    
    for error in errors_to_test:
        try:
            raise error
        except FrankenAgentError:
            # Should catch all custom errors
            pass
        except Exception:
            # Should not reach here
            pytest.fail(f"Failed to catch {type(error).__name__} as FrankenAgentError")
