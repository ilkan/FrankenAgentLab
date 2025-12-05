"""Runtime service for executing agents from blueprints.

This module provides the RuntimeService class that orchestrates the complete
execution flow: loading blueprints, compiling to agents, executing with tracing,
and returning results.
"""

import logging
from pathlib import Path
from typing import Optional

from frankenagent.config.loader import (
    BlueprintLoader,
    BlueprintNotFoundError,
    ValidationError,
)
from frankenagent.compiler.compiler import AgentCompiler, CompilationError
from frankenagent.runtime.tracing import ExecutionResult, TracingWrapper

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Raised when agent execution fails."""
    pass


class RuntimeService:
    """Service for executing agents from Agent Blueprints.
    
    The RuntimeService orchestrates the complete execution flow:
    1. Load blueprint from file
    2. Compile blueprint to Agno agent
    3. Wrap agent with tracing
    4. Execute agent with message
    5. Capture and return execution trace
    
    Example:
        >>> runtime = RuntimeService(blueprints_dir="./blueprints")
        >>> result = runtime.execute("simple_assistant", "Hello!")
        >>> print(result.response)
        >>> print(f"Used {len(result.execution_trace)} tools")
    """
    
    def __init__(self, blueprints_dir: str = "./blueprints"):
        """Initialize the runtime service.
        
        Args:
            blueprints_dir: Directory containing blueprint files
        """
        self.blueprints_dir = Path(blueprints_dir)
        self.loader = BlueprintLoader()
        self.compiler = AgentCompiler()
        
        logger.info(f"RuntimeService initialized with blueprints_dir: {blueprints_dir}")
        
        # Verify blueprints directory exists
        if not self.blueprints_dir.exists():
            logger.warning(
                f"Blueprints directory does not exist: {blueprints_dir}"
            )

    def list_blueprints(self) -> list[str]:
        """List all available blueprint IDs in the blueprints directory.
        
        Returns:
            List of blueprint IDs (filenames without extensions)
        """
        if not self.blueprints_dir.exists():
            logger.warning(f"Blueprints directory does not exist: {self.blueprints_dir}")
            return []
        
        blueprints = []
        for ext in [".yaml", ".yml", ".json"]:
            for blueprint_path in self.blueprints_dir.glob(f"*{ext}"):
                blueprint_id = blueprint_path.stem
                if blueprint_id not in blueprints:
                    blueprints.append(blueprint_id)
        
        logger.debug(f"Found {len(blueprints)} blueprints: {blueprints}")
        return sorted(blueprints)
    
    def _resolve_blueprint_path(self, blueprint_id: str) -> Path:
        """Resolve blueprint ID to file path.
        
        Tries common extensions (.yaml, .yml, .json) to find the blueprint file.
        
        Args:
            blueprint_id: Blueprint identifier (filename without extension)
            
        Returns:
            Path to the blueprint file
            
        Raises:
            BlueprintNotFoundError: If no blueprint file is found
        """
        # Try common extensions
        for ext in [".yaml", ".yml", ".json"]:
            blueprint_path = self.blueprints_dir / f"{blueprint_id}{ext}"
            if blueprint_path.exists():
                logger.debug(f"Found blueprint at: {blueprint_path}")
                return blueprint_path
        
        # Blueprint not found - provide helpful error with available blueprints
        available = self.list_blueprints()
        error_msg = (
            f"Blueprint '{blueprint_id}' not found in {self.blueprints_dir}. "
            f"Tried extensions: .yaml, .yml, .json"
        )
        
        if available:
            error_msg += f"\n\nAvailable blueprints: {', '.join(available)}"
        else:
            error_msg += f"\n\nNo blueprints found in {self.blueprints_dir}"
        
        raise BlueprintNotFoundError(error_msg)
    
    def execute(self, blueprint_id: str, message: str) -> ExecutionResult:
        """Execute agent from blueprint with message.
        
        This is the main entry point for agent execution. It orchestrates
        the complete flow from blueprint loading to traced execution.
        
        Steps:
        1. Resolve blueprint ID to file path
        2. Load and validate blueprint
        3. Compile blueprint to Agno agent
        4. Wrap agent with tracing
        5. Execute agent with message
        6. Return result with execution trace
        
        Args:
            blueprint_id: Identifier of the blueprint to execute
            message: User message to send to the agent
            
        Returns:
            ExecutionResult containing response and execution trace
            
        Raises:
            BlueprintNotFoundError: If blueprint file is not found
            ValidationError: If blueprint validation fails
            CompilationError: If blueprint compilation fails
            ExecutionError: If agent execution fails
        """
        from datetime import datetime
        
        start_timestamp = datetime.utcnow().isoformat() + "Z"
        logger.info(
            f"[{start_timestamp}] Executing blueprint '{blueprint_id}' "
            f"with message: {message[:100]}..."
        )
        
        try:
            # Step 1: Resolve blueprint path
            try:
                blueprint_path = self._resolve_blueprint_path(blueprint_id)
            except BlueprintNotFoundError as e:
                logger.error(
                    f"[{datetime.utcnow().isoformat()}Z] "
                    f"Blueprint not found: {blueprint_id}"
                )
                raise
            
            # Step 2: Load blueprint
            try:
                logger.debug(f"Loading blueprint from: {blueprint_path}")
                blueprint = self.loader.load_from_file(str(blueprint_path))
                logger.info(
                    f"[{datetime.utcnow().isoformat()}Z] "
                    f"Loaded blueprint: {blueprint.name} v{blueprint.version}"
                )
            except ValidationError as e:
                logger.error(
                    f"[{datetime.utcnow().isoformat()}Z] "
                    f"Validation failed for {blueprint_id}: {e}"
                )
                raise
            
            # Step 3: Compile blueprint to agent
            try:
                logger.debug("Compiling blueprint to agent")
                agent = self.compiler.compile(blueprint)
                logger.info(
                    f"[{datetime.utcnow().isoformat()}Z] "
                    f"Compiled agent with mode: {blueprint.legs.execution_mode}, "
                    f"tools: {len(blueprint.arms)}"
                )
            except CompilationError as e:
                logger.error(
                    f"[{datetime.utcnow().isoformat()}Z] "
                    f"Compilation failed for {blueprint.name}: {e}"
                )
                raise
            
            # Step 4: Wrap agent with tracing
            logger.debug("Wrapping agent with tracing")
            tracing_wrapper = TracingWrapper(agent)
            
            # Step 5: Execute agent with message
            try:
                logger.debug("Executing agent")
                result = tracing_wrapper.execute(message)
            except Exception as e:
                logger.error(
                    f"[{datetime.utcnow().isoformat()}Z] "
                    f"Agent execution failed: {e}",
                    exc_info=True
                )
                raise ExecutionError(
                    f"Agent execution failed for '{blueprint_id}': {e}"
                ) from e
            
            # Log execution summary
            end_timestamp = datetime.utcnow().isoformat() + "Z"
            logger.info(
                f"[{end_timestamp}] Execution completed: "
                f"{len(result.execution_trace)} tool calls, "
                f"{result.total_duration_ms:.2f}ms total"
            )
            
            if result.error:
                logger.error(
                    f"[{end_timestamp}] "
                    f"Execution completed with error: {result.error}"
                )
            
            return result
            
        except (BlueprintNotFoundError, ValidationError, CompilationError, ExecutionError) as e:
            # Re-raise known errors with timestamp
            logger.error(
                f"[{datetime.utcnow().isoformat()}Z] "
                f"Execution failed for '{blueprint_id}': {type(e).__name__}: {e}"
            )
            raise
            
        except Exception as e:
            # Wrap unexpected errors
            timestamp = datetime.utcnow().isoformat() + "Z"
            logger.error(
                f"[{timestamp}] Unexpected execution error for '{blueprint_id}': {e}",
                exc_info=True
            )
            raise ExecutionError(
                f"Failed to execute blueprint '{blueprint_id}': {e}"
            ) from e
