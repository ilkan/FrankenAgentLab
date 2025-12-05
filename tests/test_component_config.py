"""Tests for component configuration endpoints.

This module tests the new component configuration endpoints:
- GET /api/components/schemas
- POST /api/instructions/improve
"""

import pytest
from fastapi.testclient import TestClient
from frankenagent.api.server import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


def test_get_component_schemas(client):
    """Test GET /api/components/schemas endpoint."""
    response = client.get("/api/components/schemas")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all components are present
    assert "head" in data
    assert "arms" in data
    assert "legs" in data
    assert "heart" in data
    assert "spine" in data
    
    # Validate head schema structure
    head = data["head"]
    assert "providers" in head
    assert "models" in head
    assert "parameters" in head
    assert "openai" in head["providers"]
    assert "anthropic" in head["providers"]
    
    # Validate arms schema structure
    arms = data["arms"]
    assert "tool_types" in arms
    assert "tool_configs" in arms
    assert "tavily_search" in arms["tool_types"]
    
    # Validate legs schema structure
    legs = data["legs"]
    assert "execution_modes" in legs
    assert "mode_requirements" in legs
    assert "single_agent" in legs["execution_modes"]
    
    # Validate heart schema structure
    heart = data["heart"]
    assert "memory_enabled" in heart
    assert "history_length" in heart
    
    # Validate spine schema structure
    spine = data["spine"]
    assert "max_tool_calls" in spine
    assert "timeout_seconds" in spine


def test_improve_instructions_success(client):
    """Test POST /api/instructions/improve with valid input."""
    request_data = {
        "current_instructions": "You are a helpful assistant",
        "improvement_goal": "Make it more specific for customer support",
        "context": {
            "agent_purpose": "Handle customer inquiries",
            "tools_available": ["tavily_search"]
        }
    }
    
    response = client.post("/api/instructions/improve", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "improved_instructions" in data
    assert "explanation" in data
    assert "suggestions" in data
    
    # Check that improved instructions are not empty
    assert len(data["improved_instructions"]) > 0
    assert isinstance(data["improved_instructions"], str)
    
    # Check that explanation is provided
    assert len(data["explanation"]) > 0
    assert isinstance(data["explanation"], str)
    
    # Check that suggestions is a list
    assert isinstance(data["suggestions"], list)


def test_improve_instructions_empty_instructions(client):
    """Test POST /api/instructions/improve with empty instructions."""
    request_data = {
        "current_instructions": "",
        "improvement_goal": "Make it better",
        "context": {}
    }
    
    response = client.post("/api/instructions/improve", json=request_data)
    
    assert response.status_code == 400
    assert "detail" in response.json()


def test_improve_instructions_empty_goal(client):
    """Test POST /api/instructions/improve with empty goal."""
    request_data = {
        "current_instructions": "You are a helpful assistant",
        "improvement_goal": "",
        "context": {}
    }
    
    response = client.post("/api/instructions/improve", json=request_data)
    
    assert response.status_code == 400
    assert "detail" in response.json()


def test_improve_instructions_minimal_context(client):
    """Test POST /api/instructions/improve with minimal context."""
    request_data = {
        "current_instructions": "You are a helpful assistant",
        "improvement_goal": "Make it better",
        "context": {}
    }
    
    response = client.post("/api/instructions/improve", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Should still work with minimal context
    assert "improved_instructions" in data
    assert len(data["improved_instructions"]) > 0


def test_improve_instructions_with_tools_context(client):
    """Test POST /api/instructions/improve with tools in context."""
    request_data = {
        "current_instructions": "You are a helpful assistant",
        "improvement_goal": "Optimize for search tasks",
        "context": {
            "tools_available": ["tavily_search", "http_tool"]
        }
    }
    
    response = client.post("/api/instructions/improve", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that improved instructions mention tools or search
    improved = data["improved_instructions"].lower()
    # The improved instructions should be contextually relevant
    assert len(improved) > len(request_data["current_instructions"])


def test_schemas_and_improve_integration(client):
    """Test integration between schemas and improve endpoints."""
    # First, get the schemas
    schemas_response = client.get("/api/components/schemas")
    assert schemas_response.status_code == 200
    schemas = schemas_response.json()
    
    # Use schema info to create an improvement request
    head_schema = schemas["head"]
    default_prompt = head_schema["parameters"]["system_prompt"]["default"]
    available_tools = schemas["arms"]["tool_types"]
    
    improve_request = {
        "current_instructions": default_prompt,
        "improvement_goal": "Make it more professional",
        "context": {
            "tools_available": available_tools
        }
    }
    
    improve_response = client.post("/api/instructions/improve", json=improve_request)
    assert improve_response.status_code == 200
    
    improved_data = improve_response.json()
    assert len(improved_data["improved_instructions"]) > 0
    
    # Verify the improved instructions respect schema constraints
    max_length = head_schema["parameters"]["system_prompt"]["max_length"]
    assert len(improved_data["improved_instructions"]) <= max_length
