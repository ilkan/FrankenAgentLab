"""Blueprint loader for reading and validating Agent Blueprints from files.

This module provides functionality to load Agent Blueprints from YAML or JSON files
and validate them against the Pydantic schema.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any
from pydantic import ValidationError as PydanticValidationError

from frankenagent.config.schema import AgentBlueprint


class BlueprintError(Exception):
    """Base exception for blueprint-related errors."""
    pass


class BlueprintNotFoundError(BlueprintError):
    """Raised when a blueprint file is not found."""
    pass


class ValidationError(BlueprintError):
    """Raised when blueprint validation fails."""
    pass


class BlueprintLoader:
    """Loader for Agent Blueprint files.
    
    Supports loading blueprints from YAML and JSON files with automatic
    format detection based on file extension.
    """
    
    @staticmethod
    def load_from_file(path: str) -> AgentBlueprint:
        """Load and validate blueprint from YAML or JSON file.
        
        Automatically detects file format based on extension (.yaml, .yml, .json).
        
        Args:
            path: Path to blueprint file
            
        Returns:
            Validated AgentBlueprint object
            
        Raises:
            BlueprintNotFoundError: If the file doesn't exist
            ValidationError: If the blueprint is invalid or cannot be parsed
        """
        file_path = Path(path)
        
        # Check if file exists
        if not file_path.exists():
            raise BlueprintNotFoundError(f"Blueprint file not found: {path}")
        
        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ValidationError(f"Failed to read blueprint file {path}: {e}")
        
        # Parse based on file extension
        try:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                data = yaml.safe_load(content)
            elif file_path.suffix.lower() == ".json":
                data = json.loads(content)
            else:
                raise ValidationError(
                    f"Unsupported file format: {file_path.suffix}. "
                    "Use .yaml, .yml, or .json"
                )
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in {path}: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in {path}: {e}")
        
        # Validate using Pydantic
        return BlueprintLoader.load_from_dict(data, source_path=path)
    
    @staticmethod
    def load_from_dict(data: Dict[str, Any], source_path: str = None) -> AgentBlueprint:
        """Load and validate blueprint from dictionary.
        
        Args:
            data: Dictionary containing blueprint data
            source_path: Optional source file path for error messages
            
        Returns:
            Validated AgentBlueprint object
            
        Raises:
            ValidationError: If the blueprint data is invalid
        """
        if not isinstance(data, dict):
            raise ValidationError(
                f"Blueprint data must be a dictionary, got {type(data).__name__}"
            )
        
        try:
            blueprint = AgentBlueprint(**data)
            return blueprint
        except PydanticValidationError as e:
            # Format validation errors for better readability
            error_messages = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_messages.append(f"  - {field_path}: {error['msg']}")
            
            source_info = f" in {source_path}" if source_path else ""
            error_summary = "\n".join(error_messages)
            
            raise ValidationError(
                f"Blueprint validation failed{source_info}:\n{error_summary}"
            )
        except Exception as e:
            source_info = f" in {source_path}" if source_path else ""
            raise ValidationError(f"Failed to validate blueprint{source_info}: {e}")
