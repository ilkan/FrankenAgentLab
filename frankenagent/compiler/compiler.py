"""Blueprint compiler for transforming Agent Blueprints into runnable Agno agents.

This module implements the core compilation logic that maps the Frankenstein
metaphor (head/arms/legs/heart/spine) to Agno framework primitives.
"""

import logging
from typing import Any, Dict, List
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from frankenagent.tools.registry import ToolRegistry
from frankenagent.exceptions import CompilationError
from frankenagent.logging_config import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger("compilation")

# Try to import SqliteDb for conversation history, but make it optional
try:
    from agno.db.sqlite import SqliteDb
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    logger.warning("SqliteDb not available. Memory features will be disabled.")

# Try to import Team for team execution mode
try:
    from agno.team.team import Team
    TEAM_AVAILABLE = True
except ImportError:
    TEAM_AVAILABLE = False
    logger.warning("Agno Team not available. Team mode will be disabled.")


class CompiledAgent:
    """Wrapper for compiled agent with guardrails metadata.
    
    This class wraps an Agno Agent or Team along with its guardrail configuration,
    providing a unified interface for execution with safety constraints.
    """
    
    def __init__(self, agent: Any, blueprint_id: str, guardrails: Dict[str, Any], is_team: bool = False):
        """Initialize compiled agent wrapper.
        
        Args:
            agent: The compiled Agno Agent or Team instance
            blueprint_id: Unique identifier for the blueprint
            guardrails: Guardrail configuration from spine section
            is_team: Whether this is a Team (True) or single Agent (False)
        """
        self.agent = agent
        self.blueprint_id = blueprint_id
        self.guardrails = guardrails
        self.is_team = is_team
    
    def run(self, message: str, **kwargs) -> Any:
        """Run the agent/team with a message.
        
        Args:
            message: User message to process
            **kwargs: Additional arguments to pass to agent.run()
            
        Returns:
            Agent/Team response
        """
        return self.agent.run(message, **kwargs)
    
    async def arun(self, message: str, **kwargs) -> Any:
        """Run the agent/team asynchronously with a message.
        
        Args:
            message: User message to process
            **kwargs: Additional arguments to pass to agent.arun()
            
        Returns:
            Agent/Team response
        """
        return await self.agent.arun(message, **kwargs)


class AgentCompiler:
    """Compiler that transforms validated blueprints into runnable Agno agents.
    
    The compiler handles the single_agent execution mode for MVP, with support
    for workflow and team modes planned for future releases.
    
    Example:
        >>> compiler = AgentCompiler()
        >>> blueprint = {"head": {...}, "arms": [...], ...}
        >>> compiled = compiler.compile(blueprint)
        >>> response = compiled.run("Hello!")
    """
    
    def __init__(self):
        """Initialize the compiler with a tool registry."""
        self.tool_registry = ToolRegistry()
        logger.debug("AgentCompiler initialized")
    
    def compile(self, blueprint: Dict[str, Any]) -> CompiledAgent:
        """Compile a validated blueprint into a runnable Agno Agent.
        
        This method transforms a blueprint dictionary (validated by BlueprintValidator)
        into a CompiledAgent wrapper containing an Agno Agent and guardrail metadata.
        
        Steps:
        1. Build LLM model from head section
        2. Build tools from arms section
        3. Build memory from heart section
        4. Create Agno Agent with all components
        5. Wrap with CompiledAgent including guardrails
        
        Args:
            blueprint: Validated and normalized blueprint dictionary
            
        Returns:
            CompiledAgent wrapper with agent and guardrails
            
        Raises:
            CompilationError: If compilation fails for any reason
            
        Example:
            >>> blueprint = {
            ...     "name": "Assistant",
            ...     "head": {"provider": "openai", "model": "gpt-4o"},
            ...     "arms": [],
            ...     "legs": {"execution_mode": "single_agent"},
            ...     "heart": {"memory_enabled": False},
            ...     "spine": {"max_tool_calls": 10, "timeout_seconds": 60}
            ... }
            >>> compiled = compiler.compile(blueprint)
        """
        blueprint_name = blueprint.get("name", "Unnamed Agent")
        execution_mode = blueprint.get("legs", {}).get("execution_mode", "single_agent")
        num_tools = len(blueprint.get("arms", []))
        has_memory = blueprint.get("heart", {}).get("memory_enabled", False)
        
        logger.info(f"   📋 Compiling: {blueprint_name}")
        logger.info(f"   Mode: {execution_mode}")
        logger.info(f"   Tools: {num_tools}")
        logger.info(f"   Memory: {'enabled' if has_memory else 'disabled'}")
        
        logger.info(
            f"Compiling blueprint: {blueprint_name} (mode: {execution_mode})"
        )
        
        try:
            # Route to appropriate builder based on execution mode
            if execution_mode == "single_agent":
                compiled_agent = self._build_single_agent(blueprint, blueprint_name)
            elif execution_mode == "team":
                compiled_agent = self._build_team(blueprint, blueprint_name)
            elif execution_mode == "workflow":
                raise CompilationError(
                    f"Execution mode 'workflow' not yet supported. "
                    f"Supported modes: 'single_agent', 'team'."
                )
            else:
                raise CompilationError(
                    f"Unknown execution mode '{execution_mode}'. "
                    f"Supported modes: 'single_agent', 'team'."
                )
            
            logger.info(f"Successfully compiled blueprint: {blueprint_name}")
            return compiled_agent
                
        except Exception as e:
            logger.error(f"Compilation failed for {blueprint_name}: {e}")
            structured_logger.log_compilation_error(
                blueprint_name=blueprint_name,
                error=str(e)
            )
            raise CompilationError(
                f"Failed to compile blueprint {blueprint_name}: {e}"
            ) from e
    
    def _build_single_agent(self, blueprint: Dict[str, Any], blueprint_name: str) -> CompiledAgent:
        """Build a single agent from blueprint.
        
        Args:
            blueprint: Validated blueprint dictionary
            blueprint_name: Name of the blueprint for logging
            
        Returns:
            CompiledAgent wrapper with single agent
        """
        # 1. Build LLM model from head
        logger.info(f"      Building LLM model...")
        model = self._build_model(blueprint["head"])
        logger.info(f"      ✓ Model configured")
        
        # 2. Build tools from arms
        arms = blueprint.get("arms", [])
        if arms:
            logger.info(f"      Building {len(arms)} tools...")
        tools = self._build_tools(arms)
        if tools:
            logger.info(f"      ✓ {len(tools)} tools ready")
        
        # 3. Build memory configuration from heart
        heart = blueprint.get("heart", {})
        if heart.get("memory_enabled"):
            logger.info(f"      Configuring memory...")
        memory_config = self._build_memory(heart)
        if memory_config:
            logger.info(f"      ✓ Memory configured")
        
        # 4. Create Agno Agent with enhanced head configuration
        system_prompt = blueprint["head"].get("system_prompt", "You are a helpful assistant")
        agent_params = {
            "model": model,
            "instructions": system_prompt,
            "name": blueprint_name,
            "markdown": True,
        }
        
        logger.info(f"      Creating Agno Agent...")
        logger.debug(f"Applying system_prompt (length={len(system_prompt)})")
        
        # Add tools if any are configured
        if tools:
            agent_params["tools"] = tools
        
        # Add memory configuration
        agent_params.update(memory_config)
        
        # Create the agent
        agent = Agent(**agent_params)
        
        # 5. Wrap with CompiledAgent including guardrails
        spine = blueprint.get("spine", {})
        guardrails = self._apply_default_guardrails(spine)
        blueprint_id = blueprint.get("id", "unknown")
        
        compiled_agent = CompiledAgent(
            agent=agent,
            blueprint_id=blueprint_id,
            guardrails=guardrails,
            is_team=False
        )
        
        logger.debug(
            f"Applied guardrails: max_tool_calls={guardrails.get('max_tool_calls')}, "
            f"timeout_seconds={guardrails.get('timeout_seconds')}"
        )
        
        return compiled_agent
    
    def _build_team(self, blueprint: Dict[str, Any], blueprint_name: str) -> CompiledAgent:
        """Build a team of agents from blueprint using Agno's Team class.
        
        The team consists of multiple specialized agents that coordinate
        to accomplish tasks. The first team member acts as the leader/coordinator.
        
        Args:
            blueprint: Validated blueprint dictionary with team_members in legs
            blueprint_name: Name of the blueprint for logging
            
        Returns:
            CompiledAgent wrapper with Team instance
            
        Raises:
            CompilationError: If Team is not available or team configuration is invalid
        """
        if not TEAM_AVAILABLE:
            raise CompilationError(
                "Team mode requires Agno Team support. "
                "Please install agno with team support: pip install agno[team]"
            )
        
        legs = blueprint.get("legs", {})
        team_members_config = legs.get("team_members", [])
        
        if not team_members_config:
            raise CompilationError(
                "Team mode requires at least one team member in legs.team_members"
            )
        
        logger.info(f"Building team with {len(team_members_config)} members")
        
        # Build member agents
        member_agents = []
        for i, member_config in enumerate(team_members_config):
            member_name = member_config.get("name", f"Agent {i + 1}")
            member_role = member_config.get("role", "Team member")
            
            logger.debug(f"Building team member {i + 1}: {member_name} ({member_role})")
            
            # Build member's model from their head config
            member_head = member_config.get("head")
            if not member_head:
                raise CompilationError(
                    f"Team member '{member_name}' is missing head (LLM) configuration"
                )
            
            member_model = self._build_model(member_head)
            
            # Build member's tools from their arms
            member_arms = member_config.get("arms", [])
            member_tools = self._build_tools(member_arms)
            
            # Build member's memory from their heart
            member_heart = member_config.get("heart", {})
            member_memory_config = self._build_memory(member_heart)
            
            # Get member's system prompt
            member_system_prompt = member_head.get(
                "system_prompt", 
                f"You are {member_name}. {member_role}"
            )
            
            # Create member agent
            member_params = {
                "name": member_name,
                "role": member_role,
                "model": member_model,
                "instructions": member_system_prompt,
                "markdown": True,
            }
            
            if member_tools:
                member_params["tools"] = member_tools
            
            member_params.update(member_memory_config)
            
            member_agent = Agent(**member_params)
            member_agents.append(member_agent)
            
            logger.debug(
                f"Created team member: {member_name} with {len(member_tools)} tools"
            )
        
        # Build the coordinator model from the main head config
        # Use the first member's head as the team coordinator model
        coordinator_head = blueprint.get("head") or team_members_config[0].get("head")
        coordinator_model = self._build_model(coordinator_head)
        
        # Get team-level instructions
        team_instructions = blueprint.get("head", {}).get(
            "system_prompt",
            "You are a team coordinator. Delegate tasks to team members based on their roles and expertise."
        )
        
        # Build team-level memory if configured
        team_memory_config = self._build_memory(blueprint.get("heart", {}))
        
        # Create the Team
        team_params = {
            "name": blueprint_name,
            "model": coordinator_model,
            "members": member_agents,
            "instructions": team_instructions,
            "markdown": True,
            "show_members_responses": True,  # Show individual member responses
        }
        
        team_params.update(team_memory_config)
        
        team = Team(**team_params)
        
        logger.info(
            f"Created team '{blueprint_name}' with {len(member_agents)} members: "
            f"{', '.join(m.name for m in member_agents)}"
        )
        
        # Apply guardrails
        spine = blueprint.get("spine", {})
        guardrails = self._apply_default_guardrails(spine)
        blueprint_id = blueprint.get("id", "unknown")
        
        compiled_agent = CompiledAgent(
            agent=team,
            blueprint_id=blueprint_id,
            guardrails=guardrails,
            is_team=True
        )
        
        logger.debug(
            f"Team guardrails: max_tool_calls={guardrails.get('max_tool_calls')}, "
            f"timeout_seconds={guardrails.get('timeout_seconds')}"
        )
        
        return compiled_agent
    
    def _build_model(self, head: Dict[str, Any]) -> Any:
        """Build Agno model from head configuration.
        
        Maps the head section to the appropriate Agno model class based on
        the provider (openai or anthropic). Passes all enhanced HeadConfig
        parameters including temperature, max_tokens, and api_key.
        
        Args:
            head: Head configuration dictionary with provider, model, temperature, etc.
            
        Returns:
            Agno model instance (OpenAIChat or Claude)
            
        Raises:
            CompilationError: If provider is unsupported or model creation fails
            
        Example:
            >>> head = {
            ...     "provider": "openai",
            ...     "model": "gpt-4o",
            ...     "temperature": 0.7,
            ...     "max_tokens": 1000,
            ...     "api_key": "sk-..."
            ... }
            >>> model = compiler._build_model(head)
        """
        provider = head["provider"]
        model_id = head["model"]
        temperature = head.get("temperature", 0.7)
        max_tokens = head.get("max_tokens")
        api_key = head.get("api_key")
        
        logger.debug(
            f"Building model: {provider}/{model_id} "
            f"(temperature={temperature}, max_tokens={max_tokens}, "
            f"api_key={'provided' if api_key else 'from env'})"
        )
        
        try:
            if provider == "openai":
                model_params = {
                    "id": model_id,
                    "temperature": temperature,
                }
                if max_tokens:
                    model_params["max_tokens"] = max_tokens
                if api_key:
                    model_params["api_key"] = api_key
                
                return OpenAIChat(**model_params)
                
            elif provider == "anthropic":
                model_params = {
                    "id": model_id,
                    "temperature": temperature,
                }
                if max_tokens:
                    model_params["max_tokens"] = max_tokens
                if api_key:
                    model_params["api_key"] = api_key
                
                return Claude(**model_params)
                
            else:
                raise CompilationError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            raise CompilationError(
                f"Failed to build model {provider}/{model_id}: {e}"
            ) from e
    
    def _build_tools(self, arms: List[Dict[str, Any]]) -> List[Any]:
        """Build Agno tools from arms configuration.
        
        Converts each arm configuration into an Agno tool instance using
        the ToolRegistry. Tools are attached in the order they appear in
        the arms list to preserve execution sequence.
        
        For MCP tools, this method creates Agno MCPTools instances that will
        connect to MCP servers and expose their tools to the agent.
        
        Args:
            arms: List of arm configuration dictionaries (order preserved)
            
        Returns:
            List of instantiated Agno tool objects in the same order
            
        Raises:
            CompilationError: If tool instantiation fails
            
        Example:
            >>> arms = [
            ...     {"type": "tavily_search", "config": {"max_results": 5}},
            ...     {"type": "mcp_tool", "config": {"server_url": "...", "allowed_tools": [...]}}
            ... ]
            >>> tools = compiler._build_tools(arms)
        """
        tools = []
        tool_names = []
        
        for i, arm in enumerate(arms):
            try:
                tool_type = arm.get("type")
                tool_config = arm.get("config", {})
                
                # Log tool configuration (sanitize sensitive data)
                safe_config = {k: v for k, v in tool_config.items() if k not in ['api_token', 'api_key']}
                logger.debug(
                    f"Building tool {i}: {tool_type} with config {safe_config}"
                )
                
                tool = self.tool_registry.create_tool(arm)
                tools.append(tool)
                tool_names.append(tool_type)
                
            except Exception as e:
                logger.error(f"Failed to build tool {i} ({tool_type}): {e}")
                raise CompilationError(
                    f"Failed to build tool at index {i} (type={tool_type}): {e}"
                ) from e
        
        logger.info(
            f"Built {len(tools)} tools: {', '.join(tool_names)}"
        )
        return tools
    
    def _apply_default_guardrails(self, spine: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default guardrail values when not specified.
        
        Ensures that guardrails are always present for safety, even if the
        blueprint doesn't explicitly specify spine configuration.
        
        Default values:
        - max_tool_calls: 10
        - timeout_seconds: 60
        - allowed_domains: None (no restrictions)
        
        Args:
            spine: Spine configuration dictionary (may be empty)
            
        Returns:
            Dictionary with guardrails including defaults for missing values
            
        Example:
            >>> spine = {"max_tool_calls": 5}
            >>> guardrails = compiler._apply_default_guardrails(spine)
            >>> guardrails["max_tool_calls"]  # 5 (from spine)
            >>> guardrails["timeout_seconds"]  # 60 (default)
        """
        # Default guardrail values
        DEFAULT_MAX_TOOL_CALLS = 10
        DEFAULT_TIMEOUT_SECONDS = 60
        
        guardrails = {
            "max_tool_calls": spine.get("max_tool_calls", DEFAULT_MAX_TOOL_CALLS),
            "timeout_seconds": spine.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
            "allowed_domains": spine.get("allowed_domains", None)
        }
        
        logger.debug(
            f"Guardrails applied: max_tool_calls={guardrails['max_tool_calls']}, "
            f"timeout_seconds={guardrails['timeout_seconds']}, "
            f"allowed_domains={guardrails['allowed_domains']}"
        )
        
        return guardrails
    
    def _build_memory(self, heart: Dict[str, Any]) -> Dict[str, Any]:
        """Build memory configuration from heart section.
        
        Configures conversation history storage using SQLite for MVP.
        When memory is enabled, creates a SqliteAgentStorage instance and configures
        the agent to add history to context with the specified history_length.
        
        Args:
            heart: Heart configuration dictionary with memory settings
                - memory_enabled: bool (default False)
                - history_length: int (default 5, range 1-100)
                - knowledge_enabled: bool (default False, future feature)
            
        Returns:
            Dictionary of memory-related parameters for Agent initialization
            
        Example:
            >>> heart = {
            ...     "memory_enabled": True,
            ...     "history_length": 10
            ... }
            >>> config = compiler._build_memory(heart)
            >>> config["db"]  # SqliteDb instance for session storage
            >>> config["add_history_to_context"]  # True
            >>> config["num_history_runs"]  # 10
        """
        memory_config = {}
        
        memory_enabled = heart.get("memory_enabled", False)
        history_length = heart.get("history_length", 5)
        knowledge_enabled = heart.get("knowledge_enabled", False)
        
        if memory_enabled:
            if not SQLITE_AVAILABLE:
                logger.warning(
                    "Memory requested but SqliteAgentStorage not available. "
                    "Install sqlalchemy to enable memory: pip install sqlalchemy"
                )
                return memory_config
            
            logger.debug(
                f"Enabling conversation memory with SQLite "
                f"(history_length={history_length})"
            )
            
            # For MVP: use SQLite for conversation history
            # Create tmp directory if it doesn't exist
            import os
            os.makedirs("tmp", exist_ok=True)
            
            # Use Agno's SqliteDb for session storage (correct API)
            memory_config["db"] = SqliteDb(db_file="tmp/agents.db")
            
            # Enable adding history to context
            memory_config["add_history_to_context"] = True
            
            # Apply history_length parameter (validated to be 1-100)
            memory_config["num_history_runs"] = history_length
            
            logger.debug(
                f"Memory configured: history_length={history_length}, "
                f"knowledge_enabled={knowledge_enabled}"
            )
        else:
            logger.debug("Memory disabled")
        
        # Handle knowledge_enabled flag (future feature)
        if knowledge_enabled:
            logger.warning(
                "Knowledge base (RAG) requested but not yet implemented. "
                "This feature is planned for a future release."
            )
            # Future: Add knowledge base configuration here
            # memory_config["knowledge"] = Knowledge(...)
            # memory_config["search_knowledge"] = True
        
        return memory_config
    

