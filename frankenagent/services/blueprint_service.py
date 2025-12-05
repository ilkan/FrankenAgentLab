"""Blueprint service for managing agent blueprints with persistence."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from frankenagent.db.models import Blueprint, User
from frankenagent.compiler.validator import BlueprintValidator
from frankenagent.services.cache_service import AgentCacheService

logger = logging.getLogger(__name__)


class BlueprintService:
    """Service for managing blueprint CRUD operations with validation."""
    
    def __init__(
        self,
        validator: BlueprintValidator,
        cache_service: Optional['AgentCacheService'] = None
    ):
        """Initialize blueprint service.
        
        Args:
            validator: BlueprintValidator instance for validating blueprints
            cache_service: Optional AgentCacheService for cache invalidation
        """
        self.validator = validator
        self.cache_service = cache_service
    
    def create_blueprint(
        self,
        db: Session,
        user_id: UUID,
        name: str,
        description: Optional[str],
        blueprint_data: Dict[str, Any]
    ) -> Blueprint:
        """Create new blueprint with validation and database insert.
        
        Args:
            db: Database session
            user_id: ID of the user creating the blueprint
            name: Blueprint name
            description: Optional blueprint description
            blueprint_data: Blueprint configuration data
            
        Returns:
            Created Blueprint instance
            
        Raises:
            ValueError: If blueprint validation fails
        """
        logger.info(f"Creating blueprint '{name}' for user {user_id}")
        
        # Validate blueprint
        validation = self.validator.validate(blueprint_data)
        if not validation.valid:
            error_messages = [f"{e.field}: {e.message}" for e in validation.errors]
            raise ValueError(f"Invalid blueprint: {', '.join(error_messages)}")
        
        # Create in database
        blueprint = Blueprint(
            user_id=user_id,
            name=name,
            description=description,
            blueprint_data=validation.normalized_blueprint,
            version=1
        )
        
        db.add(blueprint)
        db.commit()
        db.refresh(blueprint)
        
        logger.info(f"Blueprint created: {blueprint.id} (version {blueprint.version})")
        
        return blueprint
    
    def get_user_blueprints(
        self,
        db: Session,
        user_id: UUID,
        include_deleted: bool = False
    ) -> List[Blueprint]:
        """Get all blueprints owned by user, filtered by user_id.
        
        Args:
            db: Database session
            user_id: ID of the user
            include_deleted: Whether to include soft-deleted blueprints
            
        Returns:
            List of Blueprint instances owned by the user
        """
        logger.debug(f"Fetching blueprints for user {user_id}")
        
        query = db.query(Blueprint).filter(Blueprint.user_id == user_id)
        
        if not include_deleted:
            query = query.filter(Blueprint.is_deleted == False)
        
        blueprints = query.order_by(Blueprint.updated_at.desc()).all()
        
        logger.debug(f"Found {len(blueprints)} blueprints for user {user_id}")
        
        return blueprints
    
    def get_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID
    ) -> Optional[Blueprint]:
        """Get blueprint by ID with ownership/public check.
        
        Args:
            db: Database session
            blueprint_id: ID of the blueprint
            user_id: ID of the requesting user
            
        Returns:
            Blueprint instance if found and accessible, None otherwise
        """
        logger.debug(f"Fetching blueprint {blueprint_id} for user {user_id}")
        
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.is_deleted == False
        ).first()
        
        if not blueprint:
            logger.debug(f"Blueprint {blueprint_id} not found")
            return None
        
        # Check access: owner or public
        if blueprint.user_id != user_id and not blueprint.is_public:
            logger.warning(
                f"Access denied: user {user_id} attempted to access "
                f"private blueprint {blueprint_id} owned by {blueprint.user_id}"
            )
            return None
        
        logger.debug(f"Blueprint {blueprint_id} retrieved successfully")
        
        return blueprint
    
    def update_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[Blueprint]:
        """Update blueprint with version increment (must be owner).
        
        Args:
            db: Database session
            blueprint_id: ID of the blueprint to update
            user_id: ID of the user making the update
            updates: Dictionary of fields to update (name, description, blueprint_data)
            
        Returns:
            Updated Blueprint instance if successful, None if not found or unauthorized
            
        Raises:
            ValueError: If blueprint_data validation fails
        """
        logger.info(f"Updating blueprint {blueprint_id} for user {user_id}")
        
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.user_id == user_id,
            Blueprint.is_deleted == False
        ).first()
        
        if not blueprint:
            logger.warning(
                f"Update failed: blueprint {blueprint_id} not found or "
                f"user {user_id} is not the owner"
            )
            return None
        
        # Validate if blueprint_data is being updated
        if "blueprint_data" in updates:
            validation = self.validator.validate(updates["blueprint_data"])
            if not validation.valid:
                error_messages = [f"{e.field}: {e.message}" for e in validation.errors]
                raise ValueError(f"Invalid blueprint: {', '.join(error_messages)}")
            updates["blueprint_data"] = validation.normalized_blueprint
        
        # Update fields
        for key, value in updates.items():
            if hasattr(blueprint, key):
                setattr(blueprint, key, value)
        
        # Increment version and update timestamp
        blueprint.version += 1
        blueprint.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(blueprint)
        
        # Invalidate cache for this blueprint
        if self.cache_service:
            try:
                deleted = self.cache_service.invalidate_agent(blueprint_id)
                logger.debug(f"Invalidated {deleted} cache entries for blueprint {blueprint_id}")
            except Exception as e:
                logger.warning(f"Failed to invalidate cache: {e}")
        
        logger.info(
            f"Blueprint {blueprint_id} updated to version {blueprint.version}"
        )
        
        return blueprint
    
    def delete_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID
    ) -> bool:
        """Soft delete blueprint (must be owner).
        
        Args:
            db: Database session
            blueprint_id: ID of the blueprint to delete
            user_id: ID of the user requesting deletion
            
        Returns:
            True if deletion successful, False if not found or unauthorized
        """
        logger.info(f"Deleting blueprint {blueprint_id} for user {user_id}")
        
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.user_id == user_id
        ).first()
        
        if not blueprint:
            logger.warning(
                f"Delete failed: blueprint {blueprint_id} not found or "
                f"user {user_id} is not the owner"
            )
            return False
        
        # Soft delete
        blueprint.is_deleted = True
        blueprint.deleted_at = datetime.utcnow()
        
        db.commit()
        
        # Invalidate cache for this blueprint
        if self.cache_service:
            try:
                deleted = self.cache_service.invalidate_agent(blueprint_id)
                logger.debug(f"Invalidated {deleted} cache entries for deleted blueprint {blueprint_id}")
            except Exception as e:
                logger.warning(f"Failed to invalidate cache: {e}")
        
        logger.info(f"Blueprint {blueprint_id} soft deleted")
        
        return True
