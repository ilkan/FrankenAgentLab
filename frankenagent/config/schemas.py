"""Component configuration schema provider for FrankenAgent Lab.

This module provides schemas for all agent component types (head, arms, legs, heart, spine)
that can be used by the frontend to build dynamic configuration forms with proper validation.
"""

from typing import Dict, Any


class ComponentSchemaProvider:
    """Provides configuration schemas for all agent components."""
    
    def get_all_schemas(self) -> Dict[str, Any]:
        """Get schemas for all component types.
        
        Returns:
            Dictionary with schemas for head, arms, legs, heart, and spine components
        """
        return {
            "head": self.get_head_schema(),
            "arms": self.get_arms_schema(),
            "legs": self.get_legs_schema(),
            "heart": self.get_heart_schema(),
            "spine": self.get_spine_schema()
        }
    
    def get_head_schema(self) -> Dict[str, Any]:
        """Get head (LLM) configuration schema.
        
        Returns:
            Schema with providers, models, and parameter validation rules
        """
        return {
            "providers": ["openai", "anthropic"],
            "models": {
                "openai": [
                    "gpt-4o",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo"
                ],
                "anthropic": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-haiku-20240307"
                ]
            },
            "parameters": {
                "system_prompt": {
                    "type": "string",
                    "max_length": 10000,
                    "description": "Instructions that define the agent's behavior and personality",
                    "default": "You are a helpful assistant"
                },
                "temperature": {
                    "type": "float",
                    "min": 0.0,
                    "max": 2.0,
                    "default": 0.7,
                    "description": "Controls randomness in responses (0=deterministic, 2=very random)"
                },
                "max_tokens": {
                    "type": "integer",
                    "min": 1,
                    "max": 128000,
                    "optional": True,
                    "description": "Maximum tokens in the response"
                }
            }
        }
    
    def get_arms_schema(self) -> Dict[str, Any]:
        """Get arms (tools) configuration schema.
        
        Returns:
            Schema with tool types and tool-specific configurations
        """
        return {
            "tool_types": ["tavily_search", "http_tool"],
            "tool_configs": {
                "tavily_search": {
                    "max_results": {
                        "type": "integer",
                        "min": 1,
                        "max": 10,
                        "default": 5,
                        "description": "Maximum number of search results to return"
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "default": "basic",
                        "description": "Search depth (basic=faster, advanced=more thorough)"
                    }
                },
                "http_tool": {
                    "name": {
                        "type": "string",
                        "default": "HTTP Request",
                        "description": "Name for this HTTP tool instance"
                    },
                    "description": {
                        "type": "string",
                        "default": "Make HTTP requests to external APIs",
                        "description": "Description of what this tool does"
                    },
                    "base_url": {
                        "type": "string",
                        "optional": True,
                        "description": "Base URL for HTTP requests (optional, can specify full URLs in requests)"
                    },
                    "default_headers": {
                        "type": "object",
                        "optional": True,
                        "description": "Default headers to include in all requests (e.g., Authorization, Content-Type)"
                    },
                    "timeout": {
                        "type": "integer",
                        "min": 1,
                        "max": 300,
                        "default": 30,
                        "description": "Request timeout in seconds"
                    }
                }
            }
        }
    
    def get_legs_schema(self) -> Dict[str, Any]:
        """Get legs (execution mode) configuration schema.
        
        Returns:
            Schema with execution modes and their requirements
        """
        return {
            "execution_modes": ["single_agent", "workflow", "team"],
            "mode_requirements": {
                "single_agent": {
                    "description": "Single agent handles all tasks"
                },
                "workflow": {
                    "description": "Sequential steps with programmatic control",
                    "required_fields": ["steps"]
                },
                "team": {
                    "description": "Multiple specialized agents with autonomous coordination",
                    "required_fields": ["members"]
                }
            }
        }
    
    def get_heart_schema(self) -> Dict[str, Any]:
        """Get heart (memory) configuration schema.
        
        Returns:
            Schema with memory and knowledge configuration options
        """
        return {
            "memory_enabled": {
                "type": "boolean",
                "default": False,
                "description": "Enable conversation history"
            },
            "history_length": {
                "type": "integer",
                "min": 1,
                "max": 100,
                "default": 5,
                "description": "Number of previous conversation turns to include"
            },
            "knowledge_enabled": {
                "type": "boolean",
                "default": False,
                "description": "Enable knowledge base / RAG"
            }
        }
    
    def get_spine_schema(self) -> Dict[str, Any]:
        """Get spine (guardrails) configuration schema.
        
        Returns:
            Schema with guardrail parameter ranges and validation rules
        """
        return {
            "max_tool_calls": {
                "type": "integer",
                "min": 1,
                "max": 100,
                "default": 10,
                "description": "Maximum number of tool calls per execution"
            },
            "timeout_seconds": {
                "type": "integer",
                "min": 1,
                "max": 300,
                "default": 60,
                "description": "Maximum execution time in seconds"
            },
            "allowed_domains": {
                "type": "array",
                "items": "string",
                "optional": True,
                "description": "Whitelist of allowed domains for web-based tools"
            }
        }
