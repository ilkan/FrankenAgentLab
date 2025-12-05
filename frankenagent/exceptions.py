"""Custom exception classes for FrankenAgent Lab.

This module defines the exception hierarchy for the FrankenAgent Lab system,
providing specific error types for different failure scenarios.
"""


class FrankenAgentError(Exception):
    """Base exception for all FrankenAgent Lab errors.
    
    All custom exceptions in the system inherit from this base class,
    making it easy to catch any FrankenAgent-specific error.
    """
    pass


class BlueprintNotFoundError(FrankenAgentError):
    """Raised when a requested blueprint cannot be found.
    
    This typically occurs when trying to load a blueprint by ID or file path
    that doesn't exist in the system.
    """
    pass


class ValidationError(FrankenAgentError):
    """Raised when blueprint validation fails.
    
    This exception indicates that a blueprint does not conform to the
    required schema or business rules. The exception message should
    contain details about which validation rules were violated.
    """
    pass


class CompilationError(FrankenAgentError):
    """Raised when blueprint compilation fails.
    
    This exception occurs when a validated blueprint cannot be transformed
    into a runnable Agno agent. This could be due to unsupported features,
    missing dependencies, or internal compilation errors.
    """
    pass


class ExecutionError(FrankenAgentError):
    """Raised when agent execution fails.
    
    This exception covers runtime errors during agent execution, including
    LLM provider errors, tool failures, and unexpected runtime issues.
    """
    pass


class GuardrailViolation(FrankenAgentError):
    """Raised when a guardrail constraint is violated during execution.
    
    Guardrails are safety constraints that limit agent behavior. This exception
    is raised when an agent exceeds configured limits such as max_tool_calls
    or timeout_seconds.
    
    Attributes:
        guardrail_type: The type of guardrail that was violated (e.g., 'max_tool_calls', 'timeout_seconds')
        message: Detailed error message describing the violation
    """
    
    def __init__(self, guardrail_type: str, message: str):
        """Initialize guardrail violation exception.
        
        Args:
            guardrail_type: Type of guardrail violated (e.g., 'max_tool_calls', 'timeout_seconds')
            message: Error message describing the violation
        """
        self.guardrail_type = guardrail_type
        super().__init__(message)


class ToolError(FrankenAgentError):
    """Raised when a tool invocation fails.
    
    This exception is raised when an external tool (like Tavily search or HTTP tool)
    fails during execution. The exception message should contain details about
    which tool failed and why.
    """
    pass


class ConfigurationError(FrankenAgentError):
    """Raised when system configuration is invalid or missing.
    
    This exception occurs when required configuration (like API keys) is missing
    or invalid, preventing the system from functioning correctly.
    """
    pass
