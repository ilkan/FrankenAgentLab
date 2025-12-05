"""Agent management API endpoints (alias for blueprints).

This module provides /api/agents endpoints that map to the blueprint service.
The terminology 'agents' is used for frontend compatibility while internally
using the blueprint storage system.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from frankenagent.api.models import (
    BlueprintCreateRequest,
    BlueprintUpdateRequest,
    BlueprintResponse,
    BlueprintListItem,
    BlueprintListResponse,
    AgentCreateResponse,
)
from frankenagent.api.auth import get_current_user
from frankenagent.db.database import get_db
from frankenagent.db.models import User
from frankenagent.services.activity_service import ActivityService
from frankenagent.services.blueprint_service import BlueprintService
from frankenagent.compiler.validator import BlueprintValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["Agents"])

# Initialize services
validator = BlueprintValidator()
blueprint_service = BlueprintService(validator)
activity_service = ActivityService()


@router.post("", response_model=AgentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: BlueprintCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new agent (requires authentication).
    
    Args:
        request: Agent creation request with name, description, and blueprint_data
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Created agent with all fields
        
    Raises:
        HTTPException: 400 if validation fails, 500 for server errors
    """
    logger.info(f"Creating agent '{request.name}' for user {current_user.id}")
    
    try:
        blueprint = blueprint_service.create_blueprint(
            db=db,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            blueprint_data=request.blueprint_data
        )
        
        logger.info(f"Agent created: {blueprint.id}")
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="agent.created",
            summary=f"Created agent {blueprint.name}",
            metadata={"agent_id": str(blueprint.id)},
        )
        
        # Return in format expected by frontend
        return AgentCreateResponse(agent=BlueprintResponse.from_orm(blueprint))
        
    except ValueError as e:
        logger.warning(f"Agent validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.get("", response_model=BlueprintListResponse)
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's agents (requires authentication).
    
    Args:
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        List of agents owned by the user (without full blueprint_data)
    """
    logger.info(f"Listing agents for user {current_user.id}")
    
    try:
        blueprints = blueprint_service.get_user_blueprints(
            db=db,
            user_id=current_user.id
        )
        
        # Convert to list items (without blueprint_data for performance)
        items = [
            BlueprintListItem(
                id=bp.id,
                name=bp.name,
                description=bp.description,
                version=bp.version,
                is_public=bp.is_public,
                created_at=bp.created_at,
                updated_at=bp.updated_at
            )
            for bp in blueprints
        ]
        
        logger.info(f"Found {len(items)} agents for user {current_user.id}")
        
        return BlueprintListResponse(blueprints=items)
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get("/{agent_id}", response_model=BlueprintResponse)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific agent (requires auth, must be owner or public).
    
    Args:
        agent_id: UUID of the agent
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Agent with all fields including blueprint_data
        
    Raises:
        HTTPException: 404 if not found or not accessible
    """
    logger.info(f"Fetching agent {agent_id} for user {current_user.id}")
    
    try:
        blueprint = blueprint_service.get_blueprint(
            db=db,
            blueprint_id=agent_id,
            user_id=current_user.id
        )
        
        if not blueprint:
            logger.warning(f"Agent {agent_id} not found or not accessible")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or not accessible"
            )
        
        logger.info(f"Agent {agent_id} retrieved successfully")
        
        return BlueprintResponse.from_orm(blueprint)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch agent: {str(e)}"
        )


@router.put("/{agent_id}", response_model=BlueprintResponse)
async def update_agent(
    agent_id: UUID,
    request: BlueprintUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an agent (requires auth, must be owner).
    
    Args:
        agent_id: UUID of the agent
        request: Update request with optional name, description, blueprint_data
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Updated agent with incremented version
        
    Raises:
        HTTPException: 400 if validation fails, 404 if not found or not owner
    """
    logger.info(f"Updating agent {agent_id} for user {current_user.id}")
    
    try:
        # Build updates dict from request (only include provided fields)
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.blueprint_data is not None:
            updates["blueprint_data"] = request.blueprint_data
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        blueprint = blueprint_service.update_blueprint(
            db=db,
            blueprint_id=agent_id,
            user_id=current_user.id,
            updates=updates
        )
        
        if not blueprint:
            logger.warning(
                f"Agent {agent_id} not found or user {current_user.id} is not owner"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or you are not the owner"
            )
        
        logger.info(f"Agent {agent_id} updated to version {blueprint.version}")
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="agent.updated",
            summary=f"Updated agent {blueprint.name}",
            metadata={"agent_id": str(blueprint.id), "version": blueprint.version},
        )
        
        return BlueprintResponse.from_orm(blueprint)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Agent validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an agent (requires auth, must be owner).
    
    Args:
        agent_id: UUID of the agent
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: 404 if not found or not owner
    """
    logger.info(f"Deleting agent {agent_id} for user {current_user.id}")
    
    try:
        success = blueprint_service.delete_blueprint(
            db=db,
            blueprint_id=agent_id,
            user_id=current_user.id
        )
        
        if not success:
            logger.warning(
                f"Agent {agent_id} not found or user {current_user.id} is not owner"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or you are not the owner"
            )
        
        logger.info(f"Agent {agent_id} deleted successfully")
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="agent.deleted",
            summary=f"Deleted agent {agent_id}",
            metadata={"agent_id": str(agent_id)},
        )
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}"
        )


@router.post("/{agent_id}/clone", response_model=BlueprintResponse, status_code=status.HTTP_201_CREATED)
async def clone_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clone an agent (creates a copy for the current user).
    
    Args:
        agent_id: UUID of the agent to clone
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Cloned agent with new ID
        
    Raises:
        HTTPException: 404 if not found or not accessible
    """
    logger.info(f"Cloning agent {agent_id} for user {current_user.id}")
    
    try:
        # Get the original agent
        original = blueprint_service.get_blueprint(
            db=db,
            blueprint_id=agent_id,
            user_id=current_user.id
        )
        
        if not original:
            logger.warning(f"Agent {agent_id} not found or not accessible")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or not accessible"
            )
        
        # Create a copy with new name
        cloned_name = f"{original.name} (Copy)"
        cloned = blueprint_service.create_blueprint(
            db=db,
            user_id=current_user.id,
            name=cloned_name,
            description=original.description,
            blueprint_data=original.blueprint_data
        )
        
        logger.info(f"Agent cloned: {cloned.id}")
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="agent.cloned",
            summary=f"Cloned agent {original.name}",
            metadata={"original_id": str(agent_id), "cloned_id": str(cloned.id)},
        )
        
        return BlueprintResponse.from_orm(cloned)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone agent: {str(e)}"
        )
