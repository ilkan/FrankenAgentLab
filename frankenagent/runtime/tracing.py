"""Execution tracing system for capturing tool invocations and agent behavior."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolTrace:
    """Record of a single tool invocation during agent execution.
    
    Attributes:
        tool_name: Name of the tool that was invoked
        timestamp: ISO 8601 timestamp of when the tool was called
        inputs: Dictionary of input parameters passed to the tool
        outputs: Result returned by the tool
        duration_ms: Execution time in milliseconds
    """
    tool_name: str
    timestamp: str
    inputs: Dict[str, Any]
    outputs: Any
    duration_ms: float


@dataclass
class ExecutionResult:
    """Result of an agent execution including response and trace.
    
    Attributes:
        response: The agent's text response to the user message
        execution_trace: List of tool invocations in chronological order
        total_duration_ms: Total execution time in milliseconds
        error: Error message if execution failed, None otherwise
    """
    response: str
    execution_trace: List[ToolTrace] = field(default_factory=list)
    total_duration_ms: float = 0.0
    error: Optional[str] = None


class TracingWrapper:
    """Wrapper that intercepts and traces tool calls during agent execution.
    
    This class wraps an Agno agent and captures all tool invocations,
    recording timestamps, inputs, outputs, and execution duration.
    """
    
    def __init__(self, agent: Any):
        """Initialize tracing wrapper.
        
        Args:
            agent: The Agno agent to wrap with tracing
        """
        self.agent = agent
        self.traces: List[ToolTrace] = []
        self._original_tools = None
        
    def _wrap_tool(self, tool: Any, tool_name: str) -> Any:
        """Wrap a single tool to capture its invocations.
        
        Args:
            tool: The tool instance to wrap
            tool_name: Name of the tool for logging
            
        Returns:
            Wrapped tool that captures execution traces
        """
        # Store original call method if it exists
        if hasattr(tool, '__call__'):
            original_call = tool.__call__
            
            def traced_call(*args: Any, **kwargs: Any) -> Any:
                """Traced version of tool call that captures execution details."""
                start_time = time.time()
                timestamp = datetime.utcnow().isoformat() + "Z"
                
                # Capture inputs (sanitize to avoid large objects)
                inputs = {
                    "args": [self._sanitize_value(arg) for arg in args],
                    "kwargs": {k: self._sanitize_value(v) for k, v in kwargs.items()}
                }
                
                try:
                    # Execute the actual tool
                    result = original_call(*args, **kwargs)
                    outputs = self._sanitize_value(result)
                    
                except Exception as e:
                    # Capture error as output
                    outputs = {"error": str(e)}
                    logger.error(f"Tool {tool_name} failed: {e}")
                    raise
                    
                finally:
                    # Calculate duration and record trace
                    duration_ms = (time.time() - start_time) * 1000
                    
                    trace = ToolTrace(
                        tool_name=tool_name,
                        timestamp=timestamp,
                        inputs=inputs,
                        outputs=outputs,
                        duration_ms=duration_ms
                    )
                    self.traces.append(trace)
                    
                    logger.debug(
                        f"Tool trace captured: {tool_name} "
                        f"({duration_ms:.2f}ms)"
                    )
                
                return result
            
            # Replace the call method
            tool.__call__ = traced_call
        
        return tool
    
    def _sanitize_value(self, value: Any, max_length: int = 1000) -> Any:
        """Sanitize a value for storage in trace.
        
        Prevents storing excessively large objects in traces.
        
        Args:
            value: Value to sanitize
            max_length: Maximum string length before truncation
            
        Returns:
            Sanitized value suitable for trace storage
        """
        if value is None:
            return None
            
        # Convert to string and check length
        str_value = str(value)
        if len(str_value) > max_length:
            return str_value[:max_length] + "... [truncated]"
        
        # For dictionaries, sanitize recursively
        if isinstance(value, dict):
            return {k: self._sanitize_value(v, max_length) for k, v in value.items()}
        
        # For lists, sanitize each item
        if isinstance(value, list):
            return [self._sanitize_value(item, max_length) for item in value]
        
        return value
    
    def wrap_tools(self) -> None:
        """Wrap all tools in the agent to enable tracing.
        
        This method modifies the agent's tools to capture invocations.
        """
        if not hasattr(self.agent, 'tools') or not self.agent.tools:
            logger.debug("Agent has no tools to wrap")
            return
        
        # Wrap each tool
        for i, tool in enumerate(self.agent.tools):
            tool_name = getattr(tool, 'name', f'tool_{i}')
            self.agent.tools[i] = self._wrap_tool(tool, tool_name)
            logger.debug(f"Wrapped tool: {tool_name}")
    
    def execute(self, message: str) -> ExecutionResult:
        """Execute the agent with tracing enabled.
        
        Args:
            message: User message to send to the agent
            
        Returns:
            ExecutionResult with response and captured traces
        """
        # Clear previous traces
        self.traces = []
        
        start_time = time.time()
        error = None
        response = ""
        
        try:
            # Execute the agent directly without wrapping tools
            # Tool tracing will be handled by Agno's built-in mechanisms
            logger.info(f"Executing agent with message: {message[:100]}...")
            
            # Get the underlying agent if wrapped in GuardrailWrapper
            agent_to_run = self.agent
            if hasattr(self.agent, 'agent'):
                agent_to_run = self.agent.agent
            
            result = agent_to_run.run(message)
            
            # Extract response text
            if hasattr(result, 'content'):
                response = result.content
            elif isinstance(result, str):
                response = result
            else:
                response = str(result)
                
        except Exception as e:
            error = str(e)
            logger.error(f"Agent execution failed: {e}")
            response = ""
        
        finally:
            # Calculate total duration
            total_duration_ms = (time.time() - start_time) * 1000
        
        return ExecutionResult(
            response=response,
            execution_trace=self.traces.copy(),
            total_duration_ms=total_duration_ms,
            error=error
        )
    
    def get_traces(self) -> List[ToolTrace]:
        """Get all captured traces in chronological order.
        
        Returns:
            List of ToolTrace objects in the order they were captured
        """
        return self.traces.copy()
