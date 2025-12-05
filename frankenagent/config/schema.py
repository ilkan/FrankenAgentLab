"""Pydantic models for Agent Blueprint schema."""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class HeadConfig(BaseModel):
    """Configuration for the agent's head (LLM brain)."""
    
    provider: Literal["openai", "anthropic"]
    model: str
    system_prompt: Optional[str] = "You are a helpful assistant"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    api_key: Optional[str] = Field(default=None, description="API key for the LLM provider")
    
    @field_validator('system_prompt')
    @classmethod
    def validate_system_prompt_length(cls, v: Optional[str]) -> Optional[str]:
        """Validate system_prompt does not exceed 10000 characters."""
        if v is not None and len(v) > 10000:
            raise ValueError('system_prompt must not exceed 10000 characters')
        return v


class ArmConfig(BaseModel):
    """Configuration for the agent's arms (tools)."""
    
    type: Literal["tavily_search", "http_tool", "mcp_tool"]
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def validate_tool_config(self) -> 'ArmConfig':
        """Validate tool-specific configuration parameters."""
        if self.type == "tavily_search":
            config = self.config
            
            # Validate max_results if present
            if "max_results" in config:
                max_results = config["max_results"]
                if not isinstance(max_results, int) or max_results < 1 or max_results > 10:
                    raise ValueError('tavily_search max_results must be an integer between 1 and 10')
            
            # Validate search_depth if present
            if "search_depth" in config:
                search_depth = config["search_depth"]
                if search_depth not in ["basic", "advanced"]:
                    raise ValueError('tavily_search search_depth must be "basic" or "advanced"')
        
        elif self.type == "mcp_tool":
            config = self.config
            
            # MCP tools support two transport types:
            # 1. stdio: requires "command" and "server_name"
            # 2. HTTP/SSE: requires "server_url"
            
            has_server_url = "server_url" in config
            has_command = "command" in config
            
            if not has_server_url and not has_command:
                raise ValueError(
                    'mcp_tool requires either "server_url" (for HTTP/SSE transport) '
                    'or "command" (for stdio transport) in config'
                )
            
            # Validate stdio transport fields
            if has_command:
                if "server_name" not in config:
                    raise ValueError('mcp_tool with stdio transport requires "server_name" in config')
                
                # Validate args is a list if present
                if "args" in config and not isinstance(config["args"], list):
                    raise ValueError('mcp_tool "args" must be a list')
                
                # Validate env is a dict if present
                if "env" in config and not isinstance(config["env"], dict):
                    raise ValueError('mcp_tool "env" must be a dictionary')
            
            # Validate HTTP/SSE transport fields
            if has_server_url:
                # server_url is required, other fields are optional
                if not isinstance(config["server_url"], str):
                    raise ValueError('mcp_tool "server_url" must be a string')
                
                # Validate transport_type if present
                if "transport_type" in config:
                    valid_transports = ["sse", "http", "streamable-http"]
                    if config["transport_type"] not in valid_transports:
                        raise ValueError(
                            f'mcp_tool "transport_type" must be one of: {", ".join(valid_transports)}'
                        )
                
                # Validate allowed_tools is a list if present
                if "allowed_tools" in config and not isinstance(config["allowed_tools"], list):
                    raise ValueError('mcp_tool "allowed_tools" must be a list')
        
        return self


class TeamMemberHeadConfig(BaseModel):
    """Configuration for a team member's head (LLM brain)."""
    
    provider: Literal["openai", "anthropic"]
    model: str
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)


class TeamMemberConfig(BaseModel):
    """Configuration for a single team member agent."""
    
    name: str = Field(..., description="Name of the team member")
    role: str = Field(..., description="Role/responsibility of the team member")
    head: TeamMemberHeadConfig = Field(..., description="LLM configuration for this member")
    arms: List[ArmConfig] = Field(default_factory=list, description="Tools available to this member")
    heart: Optional[Dict[str, Any]] = Field(default=None, description="Memory configuration for this member")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate team member name is not empty."""
        if not v or not v.strip():
            raise ValueError('Team member name cannot be empty')
        return v.strip()
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate team member role is not empty."""
        if not v or not v.strip():
            raise ValueError('Team member role cannot be empty')
        return v.strip()


class LegsConfig(BaseModel):
    """Configuration for the agent's legs (execution mode)."""
    
    execution_mode: Literal["single_agent", "workflow", "team"] = "single_agent"
    workflow_steps: Optional[List[str]] = None
    team_members: Optional[List[TeamMemberConfig]] = None
    
    @model_validator(mode='after')
    def validate_execution_mode_requirements(self) -> 'LegsConfig':
        """Validate that required fields are present for each execution mode."""
        if self.execution_mode == "workflow":
            if not self.workflow_steps:
                raise ValueError('workflow execution_mode requires workflow_steps to be defined')
            if not isinstance(self.workflow_steps, list) or len(self.workflow_steps) == 0:
                raise ValueError('workflow_steps must be a non-empty list')
        
        if self.execution_mode == "team":
            if not self.team_members:
                raise ValueError('team execution_mode requires team_members to be defined')
            if not isinstance(self.team_members, list) or len(self.team_members) == 0:
                raise ValueError('team_members must be a non-empty list')
            
            # Validate at least one member has a head configured
            has_head = any(member.head for member in self.team_members)
            if not has_head:
                raise ValueError('At least one team member must have a head (LLM) configured')
        
        return self


class HeartConfig(BaseModel):
    """Configuration for the agent's heart (memory and knowledge)."""
    
    memory_enabled: bool = False
    history_length: int = Field(default=5, ge=1, le=100)
    knowledge_enabled: bool = False


class SpineConfig(BaseModel):
    """Configuration for the agent's spine (guardrails and safety)."""
    
    max_tool_calls: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    allowed_domains: Optional[List[str]] = None
    
    @field_validator('allowed_domains')
    @classmethod
    def validate_allowed_domains(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate that allowed_domains contains valid domain formats."""
        if v is not None:
            # Simple domain validation pattern
            domain_pattern = re.compile(
                r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
            )
            for domain in v:
                if not isinstance(domain, str):
                    raise ValueError(f'allowed_domains must contain strings, got {type(domain).__name__}')
                if not domain_pattern.match(domain):
                    raise ValueError(f'invalid domain format: {domain}')
        return v


class AgentBlueprint(BaseModel):
    """Complete agent blueprint configuration."""
    
    name: str
    head: HeadConfig
    arms: List[ArmConfig] = Field(default_factory=list)
    legs: LegsConfig = Field(default_factory=LegsConfig)
    heart: HeartConfig = Field(default_factory=HeartConfig)
    spine: SpineConfig = Field(default_factory=SpineConfig)
    id: Optional[str] = None  # Generated during validation
