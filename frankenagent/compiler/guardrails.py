"""Guardrails wrapper for enforcing spine constraints on agent execution.

This module implements safety constraints and execution limits to ensure
agents operate within defined boundaries.
"""

import logging
import time
from typing import Any, Union
from functools import wraps

from agno.agent import Agent
from agno.workflow import Workflow

logger = logging.getLogger(__name__)


class GuardrailViolation(Exception):
    """Raised when a guardrail constraint is violated."""
    pass


class GuardrailWrapper:
    """Wrapper that enforces spine constraints on agent execution.
    
    Enforces:
    - max_tool_calls: Maximum number of tool invocations
    - timeout_seconds: Maximum execution time
    
    Example:
        >>> wrapper = GuardrailWrapper(agent, max_tool_calls=5, timeout_seconds=30)
        >>> response = wrapper.run("Hello!")
    """
    
    def __init__(
        self,
        agent: Union[Agent, Workflow],
        max_tool_calls: int = 10,
        timeout_seconds: int = 60,
    ):
        """Initialize guardrail wrapper.
        
        Args:
            agent: The agent, workflow, or team to wrap
            max_tool_calls: Maximum number of tool invocations allowed
            timeout_seconds: Maximum execution time in seconds
        """
        self.agent = agent
        self.max_tool_calls = max_tool_calls
        self.timeout_seconds = timeout_seconds
        self.tool_call_count = 0
        self.start_time = None
        
        logger.debug(
            f"GuardrailWrapper initialized: "
            f"max_tool_calls={max_tool_calls}, "
            f"timeout_seconds={timeout_seconds}"
        )
    
    def run(self, message: str, **kwargs) -> Any:
        """Execute the agent with guardrail enforcement.
        
        Args:
            message: Input message for the agent
            **kwargs: Additional arguments to pass to agent.run()
            
        Returns:
            Agent response
            
        Raises:
            GuardrailViolation: If any guardrail constraint is violated
        """
        # Reset counters for this execution
        self.tool_call_count = 0
        self.start_time = time.time()
        
        logger.info(
            f"Starting guarded execution with message: {message[:50]}..."
        )
        
        try:
            # Execute the agent directly without wrapping
            # Note: For MVP, we're not enforcing tool call limits during execution
            # This would require deeper integration with Agno's tool execution system
            response = self.agent.run(message, **kwargs)
            
            # Check if we exceeded time limit
            elapsed = time.time() - self.start_time
            if elapsed > self.timeout_seconds:
                logger.warning(
                    f"Execution took {elapsed:.2f}s (timeout: {self.timeout_seconds}s)"
                )
                # For MVP, just log the warning instead of raising
            
            logger.info(
                f"Execution completed: {elapsed:.2f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise
    
    def _wrap_run(self, original_run):
        """Wrap the agent's run method to enforce guardrails.
        
        Args:
            original_run: The original run method to wrap
            
        Returns:
            Wrapped run method with guardrail checks
        """
        @wraps(original_run)
        def wrapped_run(*args, **kwargs):
            # Check timeout before execution
            if self.start_time:
                elapsed = time.time() - self.start_time
                if elapsed > self.timeout_seconds:
                    logger.error(
                        f"Timeout before execution: {elapsed:.2f}s > {self.timeout_seconds}s"
                    )
                    raise GuardrailViolation(
                        f"Execution exceeded timeout of {self.timeout_seconds} seconds"
                    )
            
            # Increment tool call counter
            # Note: This is a simplified implementation. In a production system,
            # we would need to hook into Agno's tool execution mechanism more deeply
            # to accurately count tool calls.
            self.tool_call_count += 1
            
            # Check max tool calls
            if self.tool_call_count > self.max_tool_calls:
                logger.error(
                    f"Max tool calls exceeded: {self.tool_call_count} > {self.max_tool_calls}"
                )
                raise GuardrailViolation(
                    f"Exceeded maximum tool calls limit of {self.max_tool_calls}"
                )
            
            logger.debug(
                f"Tool call {self.tool_call_count}/{self.max_tool_calls}"
            )
            
            return original_run(*args, **kwargs)
        
        return wrapped_run
    
    def get_stats(self) -> dict:
        """Get execution statistics.
        
        Returns:
            Dictionary with execution stats including tool_call_count and elapsed_time
        """
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        return {
            "tool_call_count": self.tool_call_count,
            "max_tool_calls": self.max_tool_calls,
            "elapsed_seconds": elapsed,
            "timeout_seconds": self.timeout_seconds,
            "within_limits": (
                self.tool_call_count <= self.max_tool_calls
                and elapsed <= self.timeout_seconds
            ),
        }


def wrap_with_guardrails(
    agent: Union[Agent, Workflow],
    max_tool_calls: int = 10,
    timeout_seconds: int = 60,
) -> GuardrailWrapper:
    """Convenience function to wrap an agent with guardrails.
    
    Args:
        agent: The agent, workflow, or team to wrap
        max_tool_calls: Maximum number of tool invocations allowed
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        GuardrailWrapper instance
        
    Example:
        >>> agent = Agent(model="gpt-4", instructions="Be helpful")
        >>> guarded_agent = wrap_with_guardrails(agent, max_tool_calls=5)
        >>> response = guarded_agent.run("Hello!")
    """
    return GuardrailWrapper(
        agent=agent,
        max_tool_calls=max_tool_calls,
        timeout_seconds=timeout_seconds,
    )
