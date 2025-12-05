---
inclusion: fileMatch
fileMatchPattern: "**/runtime/**/*.py"
---

# Execution Tracing Implementation Guide

## Tracing Requirements

Every agent execution must capture:
1. Tool invocations (name, timestamp, inputs, outputs, duration)
2. Execution flow (order of operations)
3. Errors and exceptions
4. Total execution time

Traces must be returned alongside agent responses in all interfaces.

## Data Structures

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class ToolTrace:
    """Record of a single tool invocation"""
    tool_name: str
    timestamp: str  # ISO 8601 format
    inputs: Dict[str, Any]
    outputs: Any
    duration_ms: float
    error: Optional[str] = None

@dataclass
class ExecutionResult:
    """Complete execution result with trace"""
    response: str
    execution_trace: List[ToolTrace] = field(default_factory=list)
    total_duration_ms: float = 0.0
    error: Optional[str] = None
```

## Tracing Wrapper Pattern

Wrap Agno agents to intercept tool calls:

```python
import time
from datetime import datetime

class TracingWrapper:
    """Wraps an agent to capture tool invocations"""
    
    def __init__(self, agent):
        self.agent = agent
        self.traces: List[ToolTrace] = []
    
    def execute(self, message: str) -> ExecutionResult:
        """Execute agent with tracing"""
        start_time = time.time()
        
        try:
            # Wrap tool calls
            original_tools = self.agent.tools
            self.agent.tools = [self._wrap_tool(tool) for tool in original_tools]
            
            # Execute agent
            response = self.agent.run(message)
            
            # Calculate total duration
            total_duration = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                response=response,
                execution_trace=self.traces,
                total_duration_ms=total_duration
            )
        
        except Exception as e:
            total_duration = (time.time() - start_time) * 1000
            return ExecutionResult(
                response="",
                execution_trace=self.traces,
                total_duration_ms=total_duration,
                error=str(e)
            )
    
    def _wrap_tool(self, tool):
        """Wrap a single tool to capture invocations"""
        original_call = tool.__call__
        
        def traced_call(*args, **kwargs):
            tool_start = time.time()
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            try:
                result = original_call(*args, **kwargs)
                duration = (time.time() - tool_start) * 1000
                
                self.traces.append(ToolTrace(
                    tool_name=tool.__class__.__name__,
                    timestamp=timestamp,
                    inputs={"args": args, "kwargs": kwargs},
                    outputs=result,
                    duration_ms=duration
                ))
                
                return result
            
            except Exception as e:
                duration = (time.time() - tool_start) * 1000
                
                self.traces.append(ToolTrace(
                    tool_name=tool.__class__.__name__,
                    timestamp=timestamp,
                    inputs={"args": args, "kwargs": kwargs},
                    outputs=None,
                    duration_ms=duration,
                    error=str(e)
                ))
                
                raise
        
        tool.__call__ = traced_call
        return tool
```

## RuntimeService Integration

```python
class RuntimeService:
    def __init__(self, blueprints_dir: str = "./blueprints"):
        self.blueprints_dir = blueprints_dir
        self.compiler = BlueprintCompiler()
        self.loader = BlueprintLoader()
    
    def execute(self, blueprint_id: str, message: str) -> ExecutionResult:
        """Execute agent from blueprint with tracing"""
        try:
            # Load and compile blueprint
            blueprint_path = self._find_blueprint(blueprint_id)
            blueprint = self.loader.load_from_file(blueprint_path)
            agent = self.compiler.compile(blueprint)
            
            # Wrap with tracing
            wrapper = TracingWrapper(agent)
            
            # Execute with message
            result = wrapper.execute(message)
            
            return result
        
        except FileNotFoundError as e:
            return ExecutionResult(
                response="",
                error=f"Blueprint not found: {blueprint_id}"
            )
        except Exception as e:
            return ExecutionResult(
                response="",
                error=f"Execution failed: {str(e)}"
            )
```

## Trace Formatting

### CLI Output Format

```python
def format_trace_cli(trace: List[ToolTrace]) -> str:
    """Format trace for CLI output"""
    output = ["\n=== Execution Trace ==="]
    
    for i, t in enumerate(trace, 1):
        output.append(f"\n{i}. {t.tool_name}")
        output.append(f"   Time: {t.timestamp}")
        output.append(f"   Duration: {t.duration_ms:.2f}ms")
        output.append(f"   Inputs: {t.inputs}")
        output.append(f"   Outputs: {t.outputs}")
        if t.error:
            output.append(f"   Error: {t.error}")
    
    return "\n".join(output)
```

### API JSON Format

```python
def format_trace_json(trace: List[ToolTrace]) -> List[Dict]:
    """Format trace for JSON API response"""
    return [
        {
            "tool_name": t.tool_name,
            "timestamp": t.timestamp,
            "inputs": t.inputs,
            "outputs": t.outputs,
            "duration_ms": t.duration_ms,
            "error": t.error
        }
        for t in trace
    ]
```

### Web UI HTML Format

```javascript
function displayTrace(trace) {
    const traceDiv = document.getElementById('trace');
    traceDiv.innerHTML = '<h3>Execution Trace</h3>';
    
    trace.forEach((item, index) => {
        const traceItem = document.createElement('div');
        traceItem.className = 'trace-item';
        traceItem.innerHTML = `
            <strong>${index + 1}. ${item.tool_name}</strong><br>
            <small>${item.timestamp} (${item.duration_ms.toFixed(2)}ms)</small><br>
            Inputs: <code>${JSON.stringify(item.inputs)}</code><br>
            Outputs: <code>${JSON.stringify(item.outputs)}</code>
            ${item.error ? `<br><span class="error">Error: ${item.error}</span>` : ''}
        `;
        traceDiv.appendChild(traceItem);
    });
}
```

## Guardrail Tracing

Guardrail violations should also be captured in traces:

```python
class GuardrailWrapper:
    def __init__(self, agent, max_tool_calls, timeout_seconds):
        self.agent = agent
        self.max_tool_calls = max_tool_calls
        self.timeout_seconds = timeout_seconds
        self.tool_call_count = 0
    
    def run(self, message: str):
        # Check tool call limit
        if self.tool_call_count >= self.max_tool_calls:
            raise GuardrailViolation(
                f"Exceeded max_tool_calls limit: {self.max_tool_calls}"
            )
        
        # Execute with timeout
        # ... implementation
```

## Logging Integration

All traces should also be logged:

```python
import logging

logger = logging.getLogger(__name__)

def execute_with_logging(self, blueprint_id: str, message: str) -> ExecutionResult:
    logger.info(f"Executing blueprint: {blueprint_id}")
    logger.debug(f"Message: {message}")
    
    result = self.execute(blueprint_id, message)
    
    logger.info(f"Execution completed in {result.total_duration_ms:.2f}ms")
    logger.debug(f"Tool calls: {len(result.execution_trace)}")
    
    if result.error:
        logger.error(f"Execution error: {result.error}")
    
    return result
```

## Performance Considerations

- Tracing should add minimal overhead (<5% of execution time)
- Use efficient data structures (dataclasses, not dicts)
- Avoid deep copying of large outputs
- Truncate very large outputs in traces
- Consider async logging for high-throughput scenarios
