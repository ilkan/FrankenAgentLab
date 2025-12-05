"""Blueprint validation and normalization."""

import hashlib
import json
from typing import Dict, Any, List, Tuple
from frankenagent.api.models import ValidationError as ValidationErrorModel


class ValidationResult:
    """Result of blueprint validation."""
    
    def __init__(
        self,
        valid: bool,
        errors: List[ValidationErrorModel] = None,
        normalized_blueprint: Dict[str, Any] = None,
        blueprint_id: str = None
    ):
        self.valid = valid
        self.errors = errors or []
        self.normalized_blueprint = normalized_blueprint
        self.blueprint_id = blueprint_id


class BlueprintValidator:
    """Validates agent blueprints against schema and business rules."""
    
    SUPPORTED_PROVIDERS = ["openai", "anthropic"]
    SUPPORTED_MODELS = {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229"]
    }
    SUPPORTED_TOOLS = ["tavily_search", "http_tool", "mcp_tool"]
    
    def validate(self, blueprint: Dict[str, Any]) -> ValidationResult:
        """
        Validate blueprint and return normalized version or errors.
        
        Args:
            blueprint: Raw blueprint dictionary
            
        Returns:
            ValidationResult with validation status, errors, and normalized blueprint
        """
        errors = []
        
        # Validate required fields
        errors.extend(self._validate_required_fields(blueprint))
        
        # Validate head section
        if "head" in blueprint:
            errors.extend(self._validate_head(blueprint["head"]))
        
        # Validate arms section (tools)
        if "arms" in blueprint:
            errors.extend(self._validate_arms(blueprint["arms"]))
        
        # Validate legs section
        if "legs" in blueprint:
            errors.extend(self._validate_legs(blueprint["legs"]))
        
        # Validate spine section (guardrails)
        if "spine" in blueprint:
            errors.extend(self._validate_spine(blueprint["spine"]))
        
        # Validate heart section (memory)
        if "heart" in blueprint:
            errors.extend(self._validate_heart(blueprint["heart"]))
        
        # If there are errors, return invalid result
        if errors:
            return ValidationResult(valid=False, errors=errors)
        
        # Normalize and generate ID
        normalized = self._normalize(blueprint)
        blueprint_id = self._generate_id(normalized)
        
        return ValidationResult(
            valid=True,
            normalized_blueprint=normalized,
            blueprint_id=blueprint_id
        )
    
    def _validate_required_fields(self, blueprint: Dict[str, Any]) -> List[ValidationErrorModel]:
        """Validate that required fields are present."""
        errors = []
        
        if "head" not in blueprint:
            errors.append(ValidationErrorModel(
                field="head",
                message="Required field 'head' is missing"
            ))
        
        if "legs" not in blueprint:
            errors.append(ValidationErrorModel(
                field="legs",
                message="Required field 'legs' is missing"
            ))
        
        return errors
    
    def _validate_head(self, head: Dict[str, Any]) -> List[ValidationErrorModel]:
        """Validate head (LLM) configuration."""
        errors = []
        
        # Validate provider
        provider = head.get("provider")
        if not provider:
            errors.append(ValidationErrorModel(
                field="head.provider",
                message="Provider is required"
            ))
        elif provider not in self.SUPPORTED_PROVIDERS:
            errors.append(ValidationErrorModel(
                field="head.provider",
                message=f"Unsupported provider '{provider}'. Supported: {self.SUPPORTED_PROVIDERS}"
            ))
        
        # Validate model
        model = head.get("model")
        if not model:
            errors.append(ValidationErrorModel(
                field="head.model",
                message="Model is required"
            ))
        elif provider in self.SUPPORTED_MODELS:
            if model not in self.SUPPORTED_MODELS[provider]:
                errors.append(ValidationErrorModel(
                    field="head.model",
                    message=f"Unsupported model '{model}' for provider '{provider}'. Supported: {self.SUPPORTED_MODELS[provider]}"
                ))
        
        # Validate temperature if present
        temperature = head.get("temperature")
        if temperature is not None:
            if not isinstance(temperature, (int, float)):
                errors.append(ValidationErrorModel(
                    field="head.temperature",
                    message="Temperature must be a number"
                ))
            elif temperature < 0.0 or temperature > 2.0:
                errors.append(ValidationErrorModel(
                    field="head.temperature",
                    message="Temperature must be between 0.0 and 2.0"
                ))
        
        # Validate max_tokens if present
        max_tokens = head.get("max_tokens")
        if max_tokens is not None:
            if not isinstance(max_tokens, int):
                errors.append(ValidationErrorModel(
                    field="head.max_tokens",
                    message="max_tokens must be an integer"
                ))
            elif max_tokens < 1:
                errors.append(ValidationErrorModel(
                    field="head.max_tokens",
                    message="max_tokens must be positive"
                ))
        
        return errors
    
    def _validate_arms(self, arms: List[Dict[str, Any]]) -> List[ValidationErrorModel]:
        """Validate arms (tools) configuration."""
        errors = []
        
        if not isinstance(arms, list):
            errors.append(ValidationErrorModel(
                field="arms",
                message="Arms must be a list"
            ))
            return errors
        
        for i, arm in enumerate(arms):
            if not isinstance(arm, dict):
                errors.append(ValidationErrorModel(
                    field=f"arms[{i}]",
                    message="Each arm must be an object"
                ))
                continue
            
            tool_type = arm.get("type")
            if not tool_type:
                errors.append(ValidationErrorModel(
                    field=f"arms[{i}].type",
                    message="Tool type is required"
                ))
            elif tool_type not in self.SUPPORTED_TOOLS:
                errors.append(ValidationErrorModel(
                    field=f"arms[{i}].type",
                    message=f"Unsupported tool type '{tool_type}'. Supported: {self.SUPPORTED_TOOLS}"
                ))
        
        return errors
    
    def _validate_legs(self, legs: Dict[str, Any]) -> List[ValidationErrorModel]:
        """Validate legs (execution mode) configuration."""
        errors = []
        
        if not isinstance(legs, dict):
            errors.append(ValidationErrorModel(
                field="legs",
                message="Legs must be an object"
            ))
            return errors
        
        execution_mode = legs.get("execution_mode")
        if execution_mode and execution_mode not in ["single_agent", "workflow", "team"]:
            errors.append(ValidationErrorModel(
                field="legs.execution_mode",
                message=f"Unsupported execution mode '{execution_mode}'. Supported: ['single_agent', 'workflow', 'team']"
            ))
        
        # Validate team members if team mode
        if execution_mode == "team":
            errors.extend(self._validate_team_members(legs.get("team_members")))
        
        return errors
    
    def _validate_team_members(self, team_members: Any) -> List[ValidationErrorModel]:
        """Validate team members configuration for team execution mode."""
        errors = []
        
        if team_members is None:
            errors.append(ValidationErrorModel(
                field="legs.team_members",
                message="Team mode requires team_members to be defined"
            ))
            return errors
        
        if not isinstance(team_members, list):
            errors.append(ValidationErrorModel(
                field="legs.team_members",
                message="team_members must be a list"
            ))
            return errors
        
        if len(team_members) == 0:
            errors.append(ValidationErrorModel(
                field="legs.team_members",
                message="team_members must have at least one member"
            ))
            return errors
        
        has_head = False
        for i, member in enumerate(team_members):
            if not isinstance(member, dict):
                errors.append(ValidationErrorModel(
                    field=f"legs.team_members[{i}]",
                    message="Each team member must be an object"
                ))
                continue
            
            # Validate member name
            name = member.get("name")
            if not name or not isinstance(name, str) or not name.strip():
                errors.append(ValidationErrorModel(
                    field=f"legs.team_members[{i}].name",
                    message="Team member name is required"
                ))
            
            # Validate member role
            role = member.get("role")
            if not role or not isinstance(role, str) or not role.strip():
                errors.append(ValidationErrorModel(
                    field=f"legs.team_members[{i}].role",
                    message="Team member role is required"
                ))
            
            # Validate member head (LLM)
            head = member.get("head")
            if head:
                has_head = True
                head_errors = self._validate_head(head)
                for err in head_errors:
                    errors.append(ValidationErrorModel(
                        field=f"legs.team_members[{i}].{err.field}",
                        message=err.message
                    ))
            else:
                errors.append(ValidationErrorModel(
                    field=f"legs.team_members[{i}].head",
                    message="Team member must have a head (LLM) configuration"
                ))
            
            # Validate member arms (tools) if present
            arms = member.get("arms")
            if arms:
                arm_errors = self._validate_arms(arms)
                for err in arm_errors:
                    errors.append(ValidationErrorModel(
                        field=f"legs.team_members[{i}].{err.field}",
                        message=err.message
                    ))
        
        if not has_head:
            errors.append(ValidationErrorModel(
                field="legs.team_members",
                message="At least one team member must have a head (LLM) configured"
            ))
        
        return errors
    
    def _validate_spine(self, spine: Dict[str, Any]) -> List[ValidationErrorModel]:
        """Validate spine (guardrails) configuration."""
        errors = []
        
        if not isinstance(spine, dict):
            errors.append(ValidationErrorModel(
                field="spine",
                message="Spine must be an object"
            ))
            return errors
        
        # Validate max_tool_calls
        max_tool_calls = spine.get("max_tool_calls")
        if max_tool_calls is not None:
            if not isinstance(max_tool_calls, int):
                errors.append(ValidationErrorModel(
                    field="spine.max_tool_calls",
                    message="max_tool_calls must be an integer"
                ))
            elif max_tool_calls < 1:
                errors.append(ValidationErrorModel(
                    field="spine.max_tool_calls",
                    message="max_tool_calls must be a positive integer"
                ))
        
        # Validate timeout_seconds
        timeout_seconds = spine.get("timeout_seconds")
        if timeout_seconds is not None:
            if not isinstance(timeout_seconds, (int, float)):
                errors.append(ValidationErrorModel(
                    field="spine.timeout_seconds",
                    message="timeout_seconds must be a number"
                ))
            elif timeout_seconds <= 0:
                errors.append(ValidationErrorModel(
                    field="spine.timeout_seconds",
                    message="timeout_seconds must be positive"
                ))
        
        # Validate allowed_domains
        allowed_domains = spine.get("allowed_domains")
        if allowed_domains is not None:
            if not isinstance(allowed_domains, list):
                errors.append(ValidationErrorModel(
                    field="spine.allowed_domains",
                    message="allowed_domains must be a list"
                ))
            else:
                for i, domain in enumerate(allowed_domains):
                    if not isinstance(domain, str):
                        errors.append(ValidationErrorModel(
                            field=f"spine.allowed_domains[{i}]",
                            message="Each domain must be a string"
                        ))
        
        return errors
    
    def _validate_heart(self, heart: Dict[str, Any]) -> List[ValidationErrorModel]:
        """Validate heart (memory) configuration."""
        errors = []
        
        if not isinstance(heart, dict):
            errors.append(ValidationErrorModel(
                field="heart",
                message="Heart must be an object"
            ))
            return errors
        
        # Validate memory_enabled
        memory_enabled = heart.get("memory_enabled")
        if memory_enabled is not None and not isinstance(memory_enabled, bool):
            errors.append(ValidationErrorModel(
                field="heart.memory_enabled",
                message="memory_enabled must be a boolean"
            ))
        
        # Validate history_length
        history_length = heart.get("history_length")
        if history_length is not None:
            if not isinstance(history_length, int):
                errors.append(ValidationErrorModel(
                    field="heart.history_length",
                    message="history_length must be an integer"
                ))
            elif history_length < 1:
                errors.append(ValidationErrorModel(
                    field="heart.history_length",
                    message="history_length must be positive"
                ))
        
        # Validate knowledge_enabled
        knowledge_enabled = heart.get("knowledge_enabled")
        if knowledge_enabled is not None and not isinstance(knowledge_enabled, bool):
            errors.append(ValidationErrorModel(
                field="heart.knowledge_enabled",
                message="knowledge_enabled must be a boolean"
            ))
        
        return errors
    
    def _normalize(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize blueprint by adding defaults and standardizing format.
        
        Args:
            blueprint: Raw blueprint dictionary
            
        Returns:
            Normalized blueprint dictionary
        """
        normalized = blueprint.copy()
        
        # Add default name if missing
        if "name" not in normalized:
            normalized["name"] = "Unnamed Agent"
        
        # Normalize head
        if "head" in normalized:
            head = normalized["head"].copy()
            if "system_prompt" not in head:
                head["system_prompt"] = "You are a helpful assistant"
            if "temperature" not in head:
                head["temperature"] = 0.7
            normalized["head"] = head
        
        # Normalize arms (ensure it's a list)
        if "arms" not in normalized:
            normalized["arms"] = []
        
        # Normalize legs
        if "legs" in normalized:
            legs = normalized["legs"].copy()
            if "execution_mode" not in legs:
                legs["execution_mode"] = "single_agent"
            
            # Normalize team members if team mode
            if legs.get("execution_mode") == "team" and "team_members" in legs:
                normalized_members = []
                for member in legs["team_members"]:
                    normalized_member = member.copy()
                    
                    # Normalize member head
                    if "head" in normalized_member:
                        member_head = normalized_member["head"].copy()
                        if "system_prompt" not in member_head or not member_head["system_prompt"]:
                            member_name = normalized_member.get("name", "Agent")
                            member_role = normalized_member.get("role", "Team member")
                            member_head["system_prompt"] = f"You are {member_name}. {member_role}"
                        if "temperature" not in member_head:
                            member_head["temperature"] = 0.7
                        normalized_member["head"] = member_head
                    
                    # Ensure arms is a list
                    if "arms" not in normalized_member:
                        normalized_member["arms"] = []
                    
                    normalized_members.append(normalized_member)
                
                legs["team_members"] = normalized_members
            
            normalized["legs"] = legs
        else:
            normalized["legs"] = {"execution_mode": "single_agent"}
        
        # Normalize heart
        if "heart" not in normalized:
            normalized["heart"] = {
                "memory_enabled": False,
                "history_length": 5,
                "knowledge_enabled": False
            }
        else:
            heart = normalized["heart"].copy()
            if "memory_enabled" not in heart:
                heart["memory_enabled"] = False
            if "history_length" not in heart:
                heart["history_length"] = 5
            if "knowledge_enabled" not in heart:
                heart["knowledge_enabled"] = False
            normalized["heart"] = heart
        
        # Normalize spine
        if "spine" not in normalized:
            normalized["spine"] = {
                "max_tool_calls": 10,
                "timeout_seconds": 60
            }
        else:
            spine = normalized["spine"].copy()
            if "max_tool_calls" not in spine:
                spine["max_tool_calls"] = 10
            if "timeout_seconds" not in spine:
                spine["timeout_seconds"] = 60
            normalized["spine"] = spine
        
        return normalized
    
    def _generate_id(self, blueprint: Dict[str, Any]) -> str:
        """
        Generate a unique ID for the blueprint based on its content.
        
        Args:
            blueprint: Normalized blueprint dictionary
            
        Returns:
            Blueprint ID string (e.g., "bp_abc123")
        """
        # Create a stable JSON representation
        blueprint_json = json.dumps(blueprint, sort_keys=True)
        
        # Generate hash
        hash_obj = hashlib.sha256(blueprint_json.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Return first 12 characters with prefix
        return f"bp_{hash_hex[:12]}"
