"""Blueprint management API endpoints."""

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
)
from frankenagent.api.auth import get_current_user
from frankenagent.db.database import get_db
from frankenagent.db.models import User
from frankenagent.services.activity_service import ActivityService
from frankenagent.services.blueprint_service import BlueprintService
from frankenagent.compiler.validator import BlueprintValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/blueprints", tags=["Blueprints"])

# Initialize services
validator = BlueprintValidator()
blueprint_service = BlueprintService(validator)
activity_service = ActivityService()


@router.post("", response_model=BlueprintResponse, status_code=status.HTTP_201_CREATED)
async def create_blueprint(
    request: BlueprintCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new blueprint (requires authentication).
    
    Args:
        request: Blueprint creation request with name, description, and blueprint_data
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Created blueprint with all fields
        
    Raises:
        HTTPException: 400 if validation fails, 500 for server errors
    """
    logger.info(f"Creating blueprint '{request.name}' for user {current_user.id}")
    
    try:
        blueprint = blueprint_service.create_blueprint(
            db=db,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            blueprint_data=request.blueprint_data
        )
        
        logger.info(f"Blueprint created: {blueprint.id}")
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="blueprint.created",
            summary=f"Created blueprint {blueprint.name}",
            metadata={"blueprint_id": str(blueprint.id)},
        )
        
        return BlueprintResponse.from_orm(blueprint)
        
    except ValueError as e:
        logger.warning(f"Blueprint validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating blueprint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create blueprint: {str(e)}"
        )


@router.get("", response_model=BlueprintListResponse)
async def list_blueprints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's blueprints (requires authentication).
    
    Args:
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        List of blueprints owned by the user (without full blueprint_data)
    """
    logger.info(f"Listing blueprints for user {current_user.id}")
    
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
        
        logger.info(f"Found {len(items)} blueprints for user {current_user.id}")
        
        return BlueprintListResponse(blueprints=items)
        
    except Exception as e:
        logger.error(f"Error listing blueprints: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list blueprints: {str(e)}"
        )


@router.get("/{blueprint_id}", response_model=BlueprintResponse)
async def get_blueprint(
    blueprint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific blueprint (requires auth, must be owner or public).
    
    Args:
        blueprint_id: UUID of the blueprint
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Blueprint with all fields including blueprint_data
        
    Raises:
        HTTPException: 404 if not found or not accessible
    """
    logger.info(f"Fetching blueprint {blueprint_id} for user {current_user.id}")
    
    try:
        blueprint = blueprint_service.get_blueprint(
            db=db,
            blueprint_id=blueprint_id,
            user_id=current_user.id
        )
        
        if not blueprint:
            logger.warning(f"Blueprint {blueprint_id} not found or not accessible")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not found or not accessible"
            )
        
        logger.info(f"Blueprint {blueprint_id} retrieved successfully")
        
        return BlueprintResponse.from_orm(blueprint)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blueprint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch blueprint: {str(e)}"
        )


@router.put("/{blueprint_id}", response_model=BlueprintResponse)
async def update_blueprint(
    blueprint_id: UUID,
    request: BlueprintUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a blueprint (requires auth, must be owner).
    
    Args:
        blueprint_id: UUID of the blueprint
        request: Update request with optional name, description, blueprint_data
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        Updated blueprint with incremented version
        
    Raises:
        HTTPException: 400 if validation fails, 404 if not found or not owner
    """
    logger.info(f"Updating blueprint {blueprint_id} for user {current_user.id}")
    
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
            blueprint_id=blueprint_id,
            user_id=current_user.id,
            updates=updates
        )
        
        if not blueprint:
            logger.warning(
                f"Blueprint {blueprint_id} not found or user {current_user.id} is not owner"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not found or you are not the owner"
            )
        
        logger.info(f"Blueprint {blueprint_id} updated to version {blueprint.version}")
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="blueprint.updated",
            summary=f"Updated blueprint {blueprint.name}",
            metadata={"blueprint_id": str(blueprint.id), "version": blueprint.version},
        )
        
        return BlueprintResponse.from_orm(blueprint)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Blueprint validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating blueprint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update blueprint: {str(e)}"
        )


@router.delete("/{blueprint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blueprint(
    blueprint_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a blueprint (requires auth, must be owner).
    
    Args:
        blueprint_id: UUID of the blueprint
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: 404 if not found or not owner
    """
    logger.info(f"Deleting blueprint {blueprint_id} for user {current_user.id}")
    
    try:
        success = blueprint_service.delete_blueprint(
            db=db,
            blueprint_id=blueprint_id,
            user_id=current_user.id
        )
        
        if not success:
            logger.warning(
                f"Blueprint {blueprint_id} not found or user {current_user.id} is not owner"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not found or you are not the owner"
            )
        
        logger.info(f"Blueprint {blueprint_id} deleted successfully")
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="blueprint.deleted",
            summary=f"Deleted blueprint {blueprint_id}",
            metadata={"blueprint_id": str(blueprint_id)},
        )
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting blueprint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete blueprint: {str(e)}"
        )
