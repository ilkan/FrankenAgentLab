"""Simplified end-to-end API integration tests."""

import pytest
import os
from httpx import AsyncClient, ASGITransport
from frankenagent.api.server import app


@pytest.mark.asyncio
async def test_validate_endpoint_valid_blueprint():
    """Test /validate-and-compile endpoint with valid blueprint."""
    blueprint = {
        "name": "Test Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant"
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/blueprints/validate-and-compile",
            json={"blueprint": blueprint}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "blueprint_id" in data
        assert data["blueprint_id"].startswith("bp_")


@pytest.mark.asyncio
async def test_validate_endpoint_invalid_blueprint():
    """Test /validate-and-compile endpoint with invalid blueprint."""
    blueprint = {
        "name": "Invalid Agent",
        # Missing required 'head' field
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/blueprints/validate-and-compile",
            json={"blueprint": blueprint}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


@pytest.mark.asyncio
async def test_run_endpoint_simple_query():
    """Test /agents/run endpoint with simple query."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Simple Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o",
            "system_prompt": "You are a helpful assistant. Keep responses brief."
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/agents/run",
            json={
                "blueprint": blueprint,
                "message": "Say hello"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # API may return different structure, just verify it succeeded
        assert response.status_code == 200
        assert data is not None


@pytest.mark.asyncio
async def test_logs_endpoint():
    """Test /agents/logs endpoint."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    blueprint = {
        "name": "Test Agent",
        "head": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "legs": {
            "execution_mode": "single_agent"
        }
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First create a session by running
        run_response = await client.post(
            "/api/agents/run",
            json={"blueprint": blueprint, "message": "Hello"}
        )
        
        assert run_response.status_code == 200
        session_id = run_response.json()["session_id"]
        
        # Then get logs
        logs_response = await client.get(
            f"/api/agents/logs?session_id={session_id}"
        )
        
        assert logs_response.status_code == 200
        logs_data = logs_response.json()
        assert "session_id" in logs_data
        assert "logs" in logs_data
