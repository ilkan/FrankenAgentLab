"""Marketplace service for managing public blueprint sharing and discovery."""

import logging
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from frankenagent.db.models import Blueprint, User, MarketplaceRating

logger = logging.getLogger(__name__)


class MarketplaceService:
    """Service for managing marketplace operations including publish, search, clone, and rate."""
    
    def publish_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID
    ) -> bool:
        """Publish blueprint to marketplace by setting is_public=true.
        
        Args:
            db: Database session
            blueprint_id: ID of the blueprint to publish
            user_id: ID of the user publishing the blueprint (must be owner)
            
        Returns:
            True if published successfully, False if not found or unauthorized
        """
        logger.info(f"Publishing blueprint {blueprint_id} to marketplace for user {user_id}")
        
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.user_id == user_id,
            Blueprint.is_deleted == False
        ).first()
        
        if not blueprint:
            logger.warning(
                f"Publish failed: blueprint {blueprint_id} not found or "
                f"user {user_id} is not the owner"
            )
            return False
        
        blueprint.is_public = True
        db.commit()
        
        logger.info(f"Blueprint {blueprint_id} published to marketplace")
        
        return True
    
    def search_marketplace(
        self,
        db: Session,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search marketplace with full-text search and pagination.
        
        Args:
            db: Database session
            query: Optional search query to filter by name/description
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Tuple of (listings, total_count) where listings is a list of dicts
            containing marketplace listing information
        """
        logger.debug(f"Searching marketplace: query='{query}', page={page}, page_size={page_size}")
        
        # Build base query with join to get author name and calculate average rating
        base_query = db.query(
            Blueprint,
            User.full_name.label("author_name"),
            func.coalesce(
                Blueprint.rating_sum / func.nullif(Blueprint.rating_count, 0),
                0
            ).label("avg_rating")
        ).join(
            User, Blueprint.user_id == User.id
        ).filter(
            Blueprint.is_public == True,
            Blueprint.is_deleted == False
        )
        
        # Apply search filter if query provided
        if query:
            search_filter = or_(
                Blueprint.name.ilike(f"%{query}%"),
                Blueprint.description.ilike(f"%{query}%")
            )
            base_query = base_query.filter(search_filter)
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        results = base_query.order_by(
            Blueprint.clone_count.desc(),
            Blueprint.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        # Format results
        listings = []
        for blueprint, author_name, avg_rating in results:
            listings.append({
                "id": blueprint.id,
                "name": blueprint.name,
                "description": blueprint.description,
                "author_name": author_name,
                "clone_count": blueprint.clone_count,
                "average_rating": float(avg_rating),
                "rating_count": blueprint.rating_count,
                "created_at": blueprint.created_at
            })
        
        logger.debug(f"Found {total} total results, returning {len(listings)} for page {page}")
        
        return listings, total
    
    def clone_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID
    ) -> Optional[Blueprint]:
        """Clone marketplace blueprint to create user's private copy.
        
        Args:
            db: Database session
            blueprint_id: ID of the marketplace blueprint to clone
            user_id: ID of the user cloning the blueprint
            
        Returns:
            Cloned Blueprint instance if successful, None if source not found or not public
        """
        logger.info(f"Cloning blueprint {blueprint_id} for user {user_id}")
        
        # Find source blueprint (must be public and not deleted)
        source = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.is_public == True,
            Blueprint.is_deleted == False
        ).first()
        
        if not source:
            logger.warning(
                f"Clone failed: blueprint {blueprint_id} not found or not public"
            )
            return None
        
        # Create copy with user as owner
        cloned = Blueprint(
            user_id=user_id,
            name=f"{source.name} (Copy)",
            description=source.description,
            blueprint_data=source.blueprint_data,
            version=1,
            is_public=False
        )
        
        # Increment clone count on source
        source.clone_count += 1
        
        db.add(cloned)
        db.commit()
        db.refresh(cloned)
        
        logger.info(
            f"Blueprint {blueprint_id} cloned to {cloned.id} for user {user_id}. "
            f"Source clone count: {source.clone_count}"
        )
        
        return cloned
    
    def rate_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID,
        rating: int
    ) -> bool:
        """Rate a marketplace blueprint (1-5 stars), adding or updating rating.
        
        Args:
            db: Database session
            blueprint_id: ID of the blueprint to rate
            user_id: ID of the user rating the blueprint
            rating: Rating value (1-5)
            
        Returns:
            True if rating successful, False if blueprint not found or not public
            
        Raises:
            ValueError: If rating is not between 1 and 5
        """
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        logger.info(f"Rating blueprint {blueprint_id} with {rating} stars by user {user_id}")
        
        # Find blueprint (must be public)
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.is_public == True,
            Blueprint.is_deleted == False
        ).first()
        
        if not blueprint:
            logger.warning(
                f"Rating failed: blueprint {blueprint_id} not found or not public"
            )
            return False
        
        # Check if user already rated this blueprint
        existing = db.query(MarketplaceRating).filter(
            MarketplaceRating.blueprint_id == blueprint_id,
            MarketplaceRating.user_id == user_id
        ).first()
        
        if existing:
            # Update existing rating
            old_rating = existing.rating
            existing.rating = rating
            
            # Update blueprint rating aggregates
            blueprint.rating_sum = blueprint.rating_sum - old_rating + rating
            
            logger.info(
                f"Updated rating for blueprint {blueprint_id} from {old_rating} to {rating}"
            )
        else:
            # Create new rating
            new_rating = MarketplaceRating(
                blueprint_id=blueprint_id,
                user_id=user_id,
                rating=rating
            )
            db.add(new_rating)
            
            # Update blueprint rating aggregates
            blueprint.rating_sum += rating
            blueprint.rating_count += 1
            
            logger.info(
                f"Added new rating for blueprint {blueprint_id}: {rating} stars. "
                f"Total ratings: {blueprint.rating_count}"
            )
        
        db.commit()
        
        return True
