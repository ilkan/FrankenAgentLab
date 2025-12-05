"""Execution orchestrator for running agents with guardrails and logging."""

import copy
import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from frankenagent.compiler.compiler import AgentCompiler, CompiledAgent
from frankenagent.runtime.session_manager import SessionManager
from frankenagent.api.models import ExecutionResult, ToolCallLog
from frankenagent.exceptions import GuardrailViolation, ExecutionError
from frankenagent.logging_config import StructuredLogger
from frankenagent.services.cache_service import AgentCacheService
from frankenagent.services.user_api_key_service import UserAPIKeyService
from frankenagent.services.activity_service import ActivityService
from frankenagent.services.credit_service import CreditService
from frankenagent.runtime.credit_tracker import CreditTracker, CreditAwareExecutor

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger("execution")


class ExecutionOrchestrator:
    """Orchestrates agent execution with guardrails and logging.
    
    The orchestrator is responsible for:
    - Compiling or retrieving agents from blueprints
    - Managing session lifecycle
    - Enforcing guardrails (timeout, tool call limits)
    - Logging tool calls and execution metrics
    - Handling errors gracefully
    - Recording user activity for monitoring
    
    Example:
        >>> compiler = AgentCompiler()
        >>> session_manager = SessionManager()
        >>> orchestrator = ExecutionOrchestrator(compiler, session_manager)
        >>> result = await orchestrator.execute(blueprint, "Hello!", session_id="sess_123")
    """
    
    def __init__(
        self,
        compiler: AgentCompiler,
        session_manager: SessionManager,
        cache_service: Optional[AgentCacheService] = None,
        api_key_service: Optional[UserAPIKeyService] = None,
        activity_service: Optional[ActivityService] = None,
        credit_service: Optional[CreditService] = None,
    ):
        """Initialize execution orchestrator.
        
        Args:
            compiler: AgentCompiler instance for compiling blueprints
            session_manager: SessionManager instance for session and log management
            cache_service: Optional AgentCacheService for caching compiled agents
            api_key_service: Optional UserAPIKeyService for user API key management
            activity_service: Optional ActivityService for auditing agent runs
            credit_service: Optional CreditService for credit tracking
        """
        self.compiler = compiler
        self.session_manager = session_manager
        self.cache_service = cache_service
        self.api_key_service = api_key_service
        self.activity_service = activity_service
        self.credit_service = credit_service or CreditService()
        self.credit_executor = CreditAwareExecutor(self.credit_service)
        logger.debug(
            f"ExecutionOrchestrator initialized "
            f"(cache_enabled={cache_service is not None and cache_service.enabled}, "
            f"credit_tracking_enabled={credit_service is not None})"
        )
    
    async def execute(
        self,
        blueprint: Dict[str, Any],
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        db: Optional[Session] = None,
        agent_id: Optional[UUID] = None
    ) -> ExecutionResult:
        """Execute an agent with guardrails and logging.
        
        This is the main entry point for agent execution. It performs the following steps:
        1. Decrypt the user's API key for the selected provider (if requested)
        2. Inject the key into the ephemeral blueprint configuration
        3. Compile or fetch the cached agent
        4. Load or create the interactive session state
        5. Execute the plan with guardrails and timeout protections
        6. Securely wipe any transient secrets from memory
        7. Log tool calls, latency, and record a user activity event
        8. Return the structured execution result
        
        Args:
            blueprint: Validated blueprint dictionary
            message: User message to process
            session_id: Optional session ID for conversation history
            user_id: Optional user ID for API key retrieval and logging
            db: Optional database session for API key retrieval
            agent_id: Optional agent ID for execution logging
            
        Returns:
            ExecutionResult with response, tool calls, guardrails triggered, and metrics
            
        Raises:
            ExecutionError: If quota exceeded (429 status code)
            
        Example:
            >>> blueprint = {"head": {...}, "arms": [...], ...}
            >>> result = await orchestrator.execute(
            ...     blueprint, "What's the weather?", 
            ...     user_id=user_uuid, db=db_session
            ... )
            >>> print(result.response)
            >>> print(result.tool_calls)
        """
        start_time = time.time()
        blueprint_id = blueprint.get("id", "unknown")
        
        # Extract provider and model for logging
        head_config = blueprint.get("head", {})
        provider = head_config.get("provider", "unknown")
        model = head_config.get("model", "unknown")
        execution_mode = blueprint.get("legs", {}).get("execution_mode", "single_agent")
        
        logger.info(f"🚀 STEP 1: Starting execution")
        logger.info(f"   Blueprint ID: {blueprint_id}")
        logger.info(f"   Execution Mode: {execution_mode}")
        logger.info(f"   Provider: {provider}")
        logger.info(f"   Model: {model}")
        logger.info(f"   Message: {message[:100]}...")
        logger.info(f"   Session ID: {session_id or 'new'}")
        
        # Log to session if we have a session_id
        if session_id:
            self.session_manager.log_event(
                session_id=session_id,
                event_type="execution_start",
                message=f"🚀 Starting execution: {execution_mode} mode",
                details={
                    "blueprint_id": blueprint_id,
                    "execution_mode": execution_mode,
                    "provider": provider,
                    "model": model
                }
            )
        
        structured_logger.log_execution_start(
            blueprint_id=blueprint_id,
            message=message,
            session_id=session_id
        )
        
        # Variable to track if we need to wipe API key from memory
        api_key_injected = False
        blueprint_with_key = None
        
        # Variables for execution logging
        input_tokens = 0
        output_tokens = 0
        
        # Initialize credit tracker
        credit_tracker = None
        if user_id and db:
            # Check if user has sufficient credits
            if not self.credit_executor.check_sufficient_credits(db, user_id, estimated_credits=10):
                raise ExecutionError(
                    "Insufficient credits. Please check your credit balance in Settings."
                )
            credit_tracker = self.credit_executor.create_tracker()
            
            # Track execution mode cost
            # For team mode, count the number of agents
            num_agents = 1
            if execution_mode == "team":
                team_members = blueprint.get("legs", {}).get("team_members", [])
                num_agents = len(team_members) if team_members else 2  # Default to 2 if not specified
            
            credit_tracker.track_execution_mode(execution_mode, num_agents=num_agents)
            logger.info(f"💳 Credit tracking enabled for user {user_id} (mode: {execution_mode}, agents: {num_agents})")
        
        try:
            # 1. Decrypt and inject user's API key if provided
            logger.info(f"🔑 STEP 2: Retrieving API keys")
            if user_id and self.api_key_service:
                provider = blueprint.get("head", {}).get("provider")

                if not provider:
                    raise ExecutionError("Blueprint missing provider in head configuration")
                if db is None:
                    raise ExecutionError(
                        "Authenticated executions require a database session for API key retrieval."
                    )

                logger.info(f"   Fetching {provider} API key for user {user_id}")
                logger.debug("Retrieving API key for user %s and provider %s", user_id, provider)
                api_key = self.api_key_service.get_decrypted_key(
                    db=db,
                    user_id=user_id,
                    provider=provider,
                )

                if not api_key:
                    env_key_name = f"{provider.upper()}_API_KEY"
                    env_api_key = os.getenv(env_key_name)
                    if env_api_key:
                        logger.info(
                            "Using fallback %s from environment for user %s",
                            env_key_name,
                            user_id,
                        )
                        api_key = env_api_key
                    else:
                        raise ExecutionError(
                            f"No API key configured for provider '{provider}'. "
                            f"Add your {provider.upper()} API key in settings."
                        )

                blueprint_with_key = copy.deepcopy(blueprint)
                head_section = blueprint_with_key.setdefault("head", {})
                head_section["api_key"] = api_key.strip()
                blueprint = blueprint_with_key
                api_key_injected = True
                logger.info(f"   ✓ API key injected successfully")
                logger.debug("API key injected for provider %s", provider)
            else:
                logger.info(f"   Using system API keys")
            
            # 2. Get blueprint metadata for caching
            logger.info(f"⚙️  STEP 3: Compiling agent")
            blueprint_id_str = blueprint.get("id")
            blueprint_version = blueprint.get("version", 1)
            
            # Try to get from cache if we have blueprint ID and version
            compiled_agent = None
            cache_hit = False
            
            if blueprint_id_str and self.cache_service:
                logger.info(f"   Checking cache for blueprint {blueprint_id_str} v{blueprint_version}")
                try:
                    blueprint_uuid = UUID(blueprint_id_str) if isinstance(blueprint_id_str, str) else blueprint_id_str
                    compiled_agent = self.cache_service.get_compiled_agent(
                        blueprint_uuid,
                        blueprint_version
                    )
                    if compiled_agent:
                        cache_hit = True
                        logger.info(f"   ✓ Cache HIT - using cached agent")
                except Exception as e:
                    logger.warning(f"Cache lookup failed: {e}")
            
            # Compile if not in cache
            if not compiled_agent:
                if blueprint_id_str:
                    logger.info(f"   Cache MISS - compiling agent...")
                else:
                    logger.info(f"   Compiling ephemeral agent...")
                
                compile_start = time.time()
                compiled_agent = self.compiler.compile(blueprint)
                compile_duration = int((time.time() - compile_start) * 1000)
                logger.info(f"   ✓ Agent compiled in {compile_duration}ms")
                
                # Store in cache if we have blueprint ID
                if blueprint_id_str and self.cache_service:
                    try:
                        blueprint_uuid = UUID(blueprint_id_str) if isinstance(blueprint_id_str, str) else blueprint_id_str
                        self.cache_service.set_compiled_agent(
                            blueprint_uuid,
                            blueprint_version,
                            compiled_agent
                        )
                        logger.debug(f"Cached compiled agent for {blueprint_id_str} v{blueprint_version}")
                    except Exception as e:
                        logger.warning(f"Failed to cache compiled agent: {e}")
            
            agent = compiled_agent.agent
            guardrails = compiled_agent.guardrails
            
            # Log agent configuration
            num_tools = len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0
            logger.info(f"   Agent configured with {num_tools} tools")
            logger.info(f"   Guardrails: timeout={guardrails.get('timeout_seconds', 60)}s, max_tool_calls={guardrails.get('max_tool_calls', 10)}")
            logger.debug(f"Agent ready with guardrails: {guardrails} (cache_hit={cache_hit})")
            
            # 2. Load or create session
            logger.info(f"💬 STEP 4: Managing session")
            if session_id:
                session = self.session_manager.get_or_create(session_id)
                logger.info(f"   Using existing session: {session_id}")
                logger.debug(f"Using existing session: {session_id}")
            else:
                session_id = self.session_manager.create_new_session()
                logger.info(f"   Created new session: {session_id}")
                logger.debug(f"Created new session: {session_id}")
            
            # Now that we have a session_id, log all previous steps
            self.session_manager.log_event(
                session_id=session_id,
                event_type="execution_start",
                message=f"🚀 STEP 1: Starting {execution_mode} execution",
                details={
                    "blueprint_id": blueprint_id,
                    "execution_mode": execution_mode,
                    "provider": provider,
                    "model": model
                }
            )
            
            if user_id and self.api_key_service:
                self.session_manager.log_event(
                    session_id=session_id,
                    event_type="api_key_retrieval",
                    message=f"🔑 STEP 2: Retrieved {provider} API key",
                    details={"provider": provider}
                )
            else:
                self.session_manager.log_event(
                    session_id=session_id,
                    event_type="api_key_retrieval",
                    message="🔑 STEP 2: Using system API keys",
                    details={}
                )
            
            if cache_hit:
                self.session_manager.log_event(
                    session_id=session_id,
                    event_type="compilation",
                    message=f"⚙️  STEP 3: Cache HIT - using cached agent ({num_tools} tools)",
                    details={"cache_hit": True, "num_tools": num_tools}
                )
            else:
                compile_time = int((time.time() - start_time) * 1000)
                self.session_manager.log_event(
                    session_id=session_id,
                    event_type="compilation",
                    message=f"⚙️  STEP 3: Agent compiled in {compile_time}ms ({num_tools} tools)",
                    details={"cache_hit": False, "compile_time_ms": compile_time, "num_tools": num_tools}
                )
            
            self.session_manager.log_event(
                session_id=session_id,
                event_type="session_ready",
                message=f"💬 STEP 4: Session ready",
                details={"session_id": session_id}
            )
            
            # Set both user_id and session_id for Agno's conversation history
            # user_id groups conversations by user, session_id identifies the specific conversation
            agent.user_id = str(user_id) if user_id else session_id
            agent.session_id = session_id
            
            # 3. Execute with guardrails
            logger.info(f"🤖 STEP 5: Executing agent")
            logger.info(f"   Running {execution_mode} agent with message...")
            
            self.session_manager.log_event(
                session_id=session_id,
                event_type="agent_execution",
                message=f"🤖 STEP 5: Executing {execution_mode} agent...",
                details={"execution_mode": execution_mode}
            )
            
            try:
                response, tool_calls = await self._execute_with_guardrails(
                    agent,
                    message,
                    guardrails,
                    session_id
                )
                
                # 4. Calculate metrics
                total_latency = int((time.time() - start_time) * 1000)
                
                logger.info(f"✅ STEP 6: Execution completed successfully")
                logger.info(f"   Total latency: {total_latency}ms")
                logger.info(f"   Tool calls: {len(tool_calls)}")
                logger.info(f"   Response length: {len(response)} characters")
                
                self.session_manager.log_event(
                    session_id=session_id,
                    event_type="execution_complete",
                    message=f"✅ STEP 6: Completed in {total_latency}ms with {len(tool_calls)} tool calls",
                    details={
                        "total_latency_ms": total_latency,
                        "tool_calls": len(tool_calls),
                        "response_length": len(response),
                        "success": True
                    }
                )
                
                logger.info(
                    f"Execution completed successfully in {total_latency}ms "
                    f"with {len(tool_calls)} tool calls"
                )
                
                structured_logger.log_execution_complete(
                    blueprint_id=blueprint_id,
                    latency_ms=total_latency,
                    tool_calls=len(tool_calls),
                    success=True,
                    session_id=session_id
                )
                
                # Extract token counts from response if available
                input_tokens, output_tokens = self._extract_token_counts(response)
                
                # Track credits if enabled
                if credit_tracker and db and user_id:
                    try:
                        # Collect tool types for LLM pricing
                        tool_types = [self._determine_component_type(tc.tool, blueprint) for tc in tool_calls]
                        has_tools = len(tool_calls) > 0
                        
                        # Track LLM call with token usage and tool information
                        total_tokens = input_tokens + output_tokens
                        if total_tokens > 0:
                            credit_tracker.track_llm_call(
                                token_count=total_tokens,
                                model_name=model,
                                prompt_tokens=input_tokens,
                                completion_tokens=output_tokens,
                                has_tools=has_tools,
                                tool_types=tool_types
                            )
                        
                        # Track individual tool calls (for detailed logging only)
                        for tool_call in tool_calls:
                            component_type = self._determine_component_type(tool_call.tool, blueprint)
                            credit_tracker.track_tool_call(
                                tool_name=tool_call.tool,
                                component_type=component_type,
                                duration_ms=tool_call.duration_ms
                            )
                        
                        # Commit credits and log usage
                        # Note: session_id is not passed because runtime sessions use a different format
                        # (sess_<hex>) than database sessions (UUID). Credit tracking uses blueprint_id
                        # for grouping instead.
                        credit_tracker.commit_usage(
                            db=db,
                            user_id=user_id,
                            blueprint_id=agent_id,
                            session_id=None  # Runtime session format incompatible with DB UUID
                        )
                        
                        logger.info(f"💳 Credits tracked: {credit_tracker.get_total_credits()} credits used")
                    except ValueError as e:
                        # Insufficient credits - this shouldn't happen as we checked earlier
                        logger.error(f"Credit tracking failed: {e}")
                        raise ExecutionError(str(e))
                    except Exception as e:
                        logger.error(f"Failed to track credits: {e}")
                        # Don't fail execution if credit tracking fails
                
                if self.activity_service and db and user_id:
                    metadata: Dict[str, Any] = {
                        "agent_id": str(agent_id) if agent_id else None,
                        "provider": provider,
                        "model": model,
                        "latency_ms": total_latency,
                        "tool_calls": len(tool_calls),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "session_id": session_id,
                        "success": True,
                    }
                    try:
                        self.activity_service.log_activity(
                            db=db,
                            user_id=user_id,
                            activity_type="agent.run",
                            summary=f"Ran agent {agent_id or 'ephemeral'}",
                            metadata=metadata,
                        )
                    except Exception as log_error:
                        logger.warning("Failed to record activity: %s", log_error)
                
                result = ExecutionResult(
                    success=True,
                    response=response,
                    tool_calls=tool_calls,
                    session_id=session_id,
                    total_latency_ms=total_latency,
                    guardrails_triggered=[]
                )
                
                return result
                
            except GuardrailViolation as e:
                total_latency = int((time.time() - start_time) * 1000)
                logger.warning(f"Guardrail violated: {e.guardrail_type} - {str(e)}")
                
                structured_logger.log_guardrail_violation(
                    guardrail_type=e.guardrail_type,
                    message=str(e),
                    session_id=session_id
                )
                
                structured_logger.log_execution_complete(
                    blueprint_id=blueprint_id,
                    latency_ms=total_latency,
                    tool_calls=0,
                    success=False,
                    session_id=session_id
                )
                
                if self.activity_service and db and user_id:
                    metadata = {
                        "agent_id": str(agent_id) if agent_id else None,
                        "provider": provider,
                        "model": model,
                        "latency_ms": total_latency,
                        "guardrail": e.guardrail_type,
                        "session_id": session_id,
                        "success": False,
                        "error": str(e),
                    }
                    try:
                        self.activity_service.log_activity(
                            db=db,
                            user_id=user_id,
                            activity_type="agent.run",
                            summary="Guardrail triggered during run",
                            metadata=metadata,
                        )
                    except Exception as log_error:
                        logger.warning("Failed to record guardrail activity: %s", log_error)
                
                result = ExecutionResult(
                    success=False,
                    error=str(e),
                    guardrails_triggered=[e.guardrail_type],
                    session_id=session_id,
                    total_latency_ms=total_latency,
                    tool_calls=[]
                )
                
                return result
                
        except Exception as e:
            total_latency = int((time.time() - start_time) * 1000)

            logger.error(f"Execution error: {e}", exc_info=True)

            # Ensure we have a session_id even if execution failed early
            if not session_id:
                session_id = self.session_manager.create_new_session()

            structured_logger.log_execution_complete(
                blueprint_id=blueprint_id,
                latency_ms=total_latency,
                tool_calls=0,
                success=False,
                session_id=session_id
            )

            if self.activity_service and db and user_id:
                metadata = {
                    "agent_id": str(agent_id) if agent_id else None,
                    "provider": provider,
                    "model": model,
                    "latency_ms": total_latency,
                    "session_id": session_id,
                    "success": False,
                    "error": str(e),
                }
                try:
                    self.activity_service.log_activity(
                        db=db,
                        user_id=user_id,
                        activity_type="agent.run",
                        summary="Agent execution failed",
                        metadata=metadata,
                    )
                except Exception as log_error:
                    logger.warning("Failed to record failure activity: %s", log_error)

            result = ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}",
                session_id=session_id,
                total_latency_ms=total_latency,
                tool_calls=[],
                guardrails_triggered=[]
            )

            return result
        
        finally:
            # SECURITY: Securely wipe API key from memory
            if api_key_injected and blueprint_with_key:
                if "head" in blueprint_with_key and "api_key" in blueprint_with_key["head"]:
                    # Overwrite with zeros before deletion
                    api_key_value = blueprint_with_key["head"]["api_key"]
                    if isinstance(api_key_value, str):
                        # Overwrite string memory (best effort in Python)
                        blueprint_with_key["head"]["api_key"] = "0" * len(api_key_value)
                    del blueprint_with_key["head"]["api_key"]
                    logger.debug("API key wiped from memory")
                
                # Delete the blueprint copy
                del blueprint_with_key

    async def _execute_with_guardrails(
        self,
        agent: Any,
        message: str,
        guardrails: Dict[str, Any],
        session_id: str
    ) -> tuple[str, List[ToolCallLog]]:
        """Execute agent with guardrail enforcement.
        
        Wraps agent execution with timeout and tool call limit enforcement.
        
        Args:
            agent: Compiled Agno Agent instance
            message: User message to process
            guardrails: Guardrail configuration (max_tool_calls, timeout_seconds)
            session_id: Session identifier for logging
            
        Returns:
            Tuple of (response_text, tool_call_logs)
            
        Raises:
            GuardrailViolation: If timeout or tool call limit is exceeded
        """
        timeout = guardrails.get("timeout_seconds", 60)
        max_tool_calls = guardrails.get("max_tool_calls", 10)
        
        logger.debug(
            f"Executing with guardrails: timeout={timeout}s, "
            f"max_tool_calls={max_tool_calls}"
        )
        
        # Wrap execution with timeout
        try:
            result = await asyncio.wait_for(
                self._run_agent_with_tool_limit(
                    agent,
                    message,
                    max_tool_calls,
                    session_id
                ),
                timeout=timeout
            )
            return result
            
        except asyncio.TimeoutError:
            raise GuardrailViolation(
                "timeout_seconds",
                f"Execution exceeded {timeout}s timeout"
            )
    
    async def _run_agent_with_tool_limit(
        self,
        agent: Any,
        message: str,
        max_tool_calls: int,
        session_id: str
    ) -> tuple[str, List[ToolCallLog]]:
        """Run agent and track tool calls against limit.
        
        This method executes the agent and monitors tool invocations,
        logging each call and enforcing the max_tool_calls limit.
        
        Args:
            agent: Agno Agent instance
            message: User message to process
            max_tool_calls: Maximum allowed tool calls
            session_id: Session identifier for logging
            
        Returns:
            Tuple of (response_text, tool_call_logs)
            
        Raises:
            GuardrailViolation: If max_tool_calls limit is exceeded
        """
        tool_call_logs: List[ToolCallLog] = []
        
        # Track tool calls by wrapping the agent's tools
        original_tools = agent.tools if hasattr(agent, 'tools') and agent.tools else []
        
        if original_tools:
            wrapped_tools = []
            
            for tool in original_tools:
                wrapped_tool = self._wrap_tool_with_logging(
                    tool,
                    session_id,
                    tool_call_logs,
                    max_tool_calls,
                    credit_tracker=None,  # Will be passed from execute method
                    blueprint=None  # Will be passed from execute method
                )
                wrapped_tools.append(wrapped_tool)
            
            # Replace tools with wrapped versions
            agent.tools = wrapped_tools
        
        # Run agent
        logger.debug(f"Running agent with message: {message[:50]}...")
        
        try:
            # Use async run if available, otherwise sync
            if hasattr(agent, 'arun'):
                response = await agent.arun(message)
            else:
                # Run sync method in executor to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, agent.run, message)
            
            # Extract response text
            response_text = self._extract_response_text(response)
            
            logger.debug(f"Agent completed with {len(tool_call_logs)} tool calls")
            
            # Check if we exceeded tool call limit
            if len(tool_call_logs) > max_tool_calls:
                raise GuardrailViolation(
                    "max_tool_calls",
                    f"Exceeded limit of {max_tool_calls} tool calls "
                    f"({len(tool_call_logs)} calls made)"
                )
            
            return response_text, tool_call_logs
            
        finally:
            # Restore original tools
            if original_tools:
                agent.tools = original_tools
    
    def _wrap_tool_with_logging(
        self,
        tool: Any,
        session_id: str,
        tool_call_logs: List[ToolCallLog],
        max_tool_calls: int,
        credit_tracker: Optional[CreditTracker] = None,
        blueprint: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Wrap a tool to log calls and enforce limits.
        
        Creates a wrapper around the tool that logs execution details
        and checks against the max_tool_calls limit.
        
        Args:
            tool: Original Agno tool instance
            session_id: Session identifier for logging
            tool_call_logs: List to append tool call logs to
            max_tool_calls: Maximum allowed tool calls
            credit_tracker: Optional credit tracker for usage tracking
            blueprint: Optional blueprint for determining component type
            
        Returns:
            Wrapped tool with logging
        """
        # Get tool name - Agno tools typically have a name attribute or __name__
        tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', 'unknown_tool')
        
        # For Agno tools, we need to wrap the actual callable methods
        # This is a simplified approach for MVP
        original_call = None
        
        if hasattr(tool, '__call__'):
            original_call = tool.__call__
        
        def logged_call(*args, **kwargs):
            """Wrapped call with logging."""
            # Check limit before executing
            if len(tool_call_logs) >= max_tool_calls:
                raise GuardrailViolation(
                    "max_tool_calls",
                    f"Exceeded limit of {max_tool_calls} tool calls"
                )
            
            start = time.time()
            
            try:
                # Execute the tool
                if original_call:
                    result = original_call(*args, **kwargs)
                else:
                    result = tool(*args, **kwargs)
                
                duration = int((time.time() - start) * 1000)
                
                # Create log entry
                tool_log = ToolCallLog(
                    tool=tool_name,
                    args=kwargs if kwargs else {},
                    duration_ms=duration,
                    success=True,
                    result=str(result)[:200] if result else None
                )
                
                tool_call_logs.append(tool_log)
                
                # Log to session manager
                self.session_manager.log_tool_call(
                    session_id=session_id,
                    tool_name=tool_name,
                    args=kwargs if kwargs else {},
                    duration_ms=duration,
                    success=True,
                    result=str(result)
                )
                
                # Structured logging
                structured_logger.log_tool_call(
                    tool_name=tool_name,
                    duration_ms=duration,
                    success=True
                )
                
                # Track credits if enabled
                if credit_tracker:
                    component_type = self._determine_component_type(tool_name, blueprint)
                    credit_tracker.track_tool_call(tool_name, component_type, duration)
                
                logger.debug(f"Tool call succeeded: {tool_name} in {duration}ms")
                
                return result
                
            except Exception as e:
                duration = int((time.time() - start) * 1000)
                
                # Create error log entry
                tool_log = ToolCallLog(
                    tool=tool_name,
                    args=kwargs if kwargs else {},
                    duration_ms=duration,
                    success=False,
                    error=str(e)
                )
                
                tool_call_logs.append(tool_log)
                
                # Log to session manager
                self.session_manager.log_tool_call(
                    session_id=session_id,
                    tool_name=tool_name,
                    args=kwargs if kwargs else {},
                    duration_ms=duration,
                    success=False,
                    error=str(e)
                )
                
                # Structured logging
                structured_logger.log_tool_call(
                    tool_name=tool_name,
                    duration_ms=duration,
                    success=False,
                    error=str(e)
                )
                
                logger.error(f"Tool call failed: {tool_name} - {e}")
                
                raise
        
        # Replace the call method if it exists
        if original_call:
            tool.__call__ = logged_call
        
        return tool
    
    def _extract_response_text(self, response: Any) -> str:
        """Extract text from agent response.
        
        Agno agents can return different response formats. This method
        normalizes them to a string.
        
        Args:
            response: Agent response object
            
        Returns:
            Response text as string
        """
        # Handle different response types
        if isinstance(response, str):
            return response
        
        # Agno RunResponse object
        if hasattr(response, 'content'):
            content = response.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Join multiple content parts
                return '\n'.join(str(part) for part in content)
            else:
                return str(content)
        
        # Fallback to string conversion
        return str(response)
    
    def _extract_token_counts(self, response: Any) -> tuple[int, int]:
        """Extract token counts from LLM response.
        
        Attempts to extract input and output token counts from the response
        object. Different LLM providers may structure this differently.
        
        Args:
            response: Agent response object
            
        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        input_tokens = 0
        output_tokens = 0
        
        try:
            # Agno RunResponse with metrics
            if hasattr(response, 'metrics'):
                metrics = response.metrics
                if metrics:
                    input_tokens = getattr(metrics, 'input_tokens', 0) or 0
                    output_tokens = getattr(metrics, 'output_tokens', 0) or 0
                    
                    # Also check for prompt_tokens/completion_tokens (OpenAI style)
                    if input_tokens == 0:
                        input_tokens = getattr(metrics, 'prompt_tokens', 0) or 0
                    if output_tokens == 0:
                        output_tokens = getattr(metrics, 'completion_tokens', 0) or 0
            
            # Check for usage attribute (common in many LLM responses)
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                if hasattr(usage, 'input_tokens'):
                    input_tokens = usage.input_tokens or 0
                if hasattr(usage, 'output_tokens'):
                    output_tokens = usage.output_tokens or 0
                if hasattr(usage, 'prompt_tokens'):
                    input_tokens = usage.prompt_tokens or 0
                if hasattr(usage, 'completion_tokens'):
                    output_tokens = usage.completion_tokens or 0
            
            # Check for dict-style response
            if isinstance(response, dict):
                if 'usage' in response:
                    usage = response['usage']
                    input_tokens = usage.get('input_tokens', 0) or usage.get('prompt_tokens', 0) or 0
                    output_tokens = usage.get('output_tokens', 0) or usage.get('completion_tokens', 0) or 0
                if 'metrics' in response:
                    metrics = response['metrics']
                    input_tokens = metrics.get('input_tokens', 0) or metrics.get('prompt_tokens', 0) or 0
                    output_tokens = metrics.get('output_tokens', 0) or metrics.get('completion_tokens', 0) or 0
            
        except Exception as e:
            logger.warning(f"Failed to extract token counts from response: {e}")
        
        return input_tokens, output_tokens
    
    def _format_tool_calls_for_logging(self, tool_calls: List[ToolCallLog]) -> List[Dict[str, Any]]:
        """Format tool call logs for database storage.
        
        Converts ToolCallLog objects to dictionaries suitable for JSONB storage.
        
        Args:
            tool_calls: List of ToolCallLog objects
            
        Returns:
            List of dictionaries with tool call information
        """
        formatted_calls = []
        
        for call in tool_calls:
            call_data = {
                "tool": call.tool,
                "args": call.args,
                "duration_ms": call.duration_ms,
                "success": call.success,
            }
            
            # Add optional fields if present
            if call.result:
                # Truncate result to avoid storing huge data
                call_data["result_summary"] = call.result[:500] if len(call.result) > 500 else call.result
            
            if call.error:
                call_data["error"] = call.error
            
            formatted_calls.append(call_data)
        
        return formatted_calls
    
    def _determine_component_type(self, tool_name: str, blueprint: Optional[Dict[str, Any]]) -> str:
        """Determine the component type for credit calculation.
        
        Args:
            tool_name: Name of the tool being called
            blueprint: Blueprint configuration
            
        Returns:
            Component type string for credit calculation
        """
        tool_name_lower = tool_name.lower()
        
        # Check for MCP tools
        if "mcp" in tool_name_lower:
            return "mcp_tool"
        
        # Check for HTTP tools
        if "http" in tool_name_lower or "api" in tool_name_lower:
            return "http_tool"
        
        # Check for Tavily search
        if "tavily" in tool_name_lower or "search" in tool_name_lower:
            return "tavily_search"
        
        # Check for Python eval
        if "python" in tool_name_lower or "eval" in tool_name_lower:
            return "python_eval"
        
        # Check blueprint for tool configuration
        if blueprint:
            arms = blueprint.get("arms", [])
            for arm in arms:
                if arm.get("type") in tool_name_lower:
                    return arm.get("type")
        
        # Default to generic tool
        return "http_tool"
