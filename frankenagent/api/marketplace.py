"""API routes for marketplace blueprints.

This module provides PUBLIC endpoints for browsing marketplace blueprints.
No authentication required for listing and viewing.
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from frankenagent.api.auth import get_current_user
from frankenagent.api.models import BlueprintResponse, BlueprintListItem
from frankenagent.compiler.validator import BlueprintValidator
from frankenagent.db.database import get_db
from frankenagent.db.models import User, Blueprint
from frankenagent.services.activity_service import ActivityService
from frankenagent.services.blueprint_service import BlueprintService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

# Path to marketplace blueprints
MARKETPLACE_DIR = Path(__file__).parent.parent.parent / "blueprints" / "marketplace"
validator = BlueprintValidator()
blueprint_service = BlueprintService(validator)
activity_service = ActivityService()


def load_marketplace_blueprints() -> List[Dict[str, Any]]:
    """Load all marketplace blueprints from YAML files."""
    blueprints = []
    
    if not MARKETPLACE_DIR.exists():
        logger.warning(f"Marketplace directory not found: {MARKETPLACE_DIR}")
        return blueprints
    
    # Find all YAML files
    for yaml_file in MARKETPLACE_DIR.glob("*.yaml"):
        if yaml_file.name == "README.md":
            continue
            
        try:
            with open(yaml_file, 'r') as f:
                blueprint_data = yaml.safe_load(f)
            
            # Add metadata
            blueprint_id = yaml_file.stem
            blueprint_data['id'] = blueprint_id
            blueprint_data['marketplace_id'] = blueprint_id
            blueprint_data['is_marketplace'] = True
            
            # Categorize based on tools
            category = categorize_blueprint(blueprint_data)
            blueprint_data['category'] = category
            
            # Add tags based on content
            tags = generate_tags(blueprint_data)
            blueprint_data['tags'] = tags
            
            blueprints.append(blueprint_data)
            logger.debug(f"Loaded marketplace blueprint: {blueprint_id}")
            
        except Exception as e:
            logger.error(f"Failed to load blueprint {yaml_file}: {e}")
            continue
    
    return blueprints


def categorize_blueprint(blueprint: Dict[str, Any]) -> str:
    """Categorize blueprint based on its tools and purpose."""
    name = blueprint.get('name', '').lower()
    description = blueprint.get('description', '').lower()
    arms = blueprint.get('arms', [])
    
    # Check tools
    has_search = any(arm.get('type') == 'tavily_search' for arm in arms)
    has_http = any(arm.get('type') == 'http_tool' for arm in arms)
    has_mcp = any(arm.get('type') == 'mcp_tool' for arm in arms)
    
    # Categorize
    if 'news' in name or 'news' in description:
        return 'Content Creation'
    elif 'research' in name or 'research' in description:
        return 'Productivity'
    elif 'github' in name or 'api' in name:
        return 'Data & Analytics'
    elif 'weather' in name or 'crypto' in name:
        return 'Data & Analytics'
    elif 'aws' in name or 'documentation' in description:
        return 'Productivity'
    elif has_search and has_http:
        return 'Productivity'
    elif has_search:
        return 'Content Creation'
    elif has_http:
        return 'Data & Analytics'
    elif has_mcp:
        return 'Productivity'
    else:
        return 'Productivity'


def generate_tags(blueprint: Dict[str, Any]) -> List[str]:
    """Generate tags based on blueprint content."""
    tags = []
    name = blueprint.get('name', '').lower()
    description = blueprint.get('description', '').lower()
    arms = blueprint.get('arms', [])
    
    # Tool-based tags
    for arm in arms:
        tool_type = arm.get('type', '')
        if tool_type == 'tavily_search':
            tags.append('search')
        elif tool_type == 'http_tool':
            tags.append('api')
        elif tool_type == 'mcp_tool':
            tags.append('mcp')
    
    # Content-based tags
    if 'news' in name or 'news' in description:
        tags.append('news')
    if 'research' in name or 'research' in description:
        tags.append('research')
    if 'github' in name:
        tags.append('github')
    if 'weather' in name:
        tags.append('weather')
    if 'crypto' in name:
        tags.append('crypto')
    if 'aws' in name:
        tags.append('aws')
    if 'documentation' in description:
        tags.append('docs')
    
    # Add generic tags
    if len(arms) > 1:
        tags.append('multi-tool')
    
    return list(set(tags))  # Remove duplicates


@router.get("")
@router.get("/")
@router.get("/blueprints")
async def list_marketplace_blueprints(
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all available marketplace blueprints (PUBLIC - no auth required).
    
    This endpoint combines:
    1. Public blueprints from the database (is_public=True)
    2. YAML blueprints from the marketplace directory
    
    Supports multiple URL patterns:
    - GET /api/marketplace
    - GET /api/marketplace/
    - GET /api/marketplace/blueprints
    
    Args:
        category: Optional category filter
        page: Page number (default: 1)
        page_size: Items per page (default: 100)
        db: Database session
        
    Returns:
        List of marketplace blueprints with metadata
    """
    try:
        all_blueprints = []
        
        # 1. Load public blueprints from database
        try:
            db_blueprints = db.query(Blueprint).filter(
                and_(
                    Blueprint.is_public == True,
                    Blueprint.is_deleted == False
                )
            ).all()
            
            for bp in db_blueprints:
                blueprint_dict = {
                    'id': str(bp.id),
                    'name': bp.name,
                    'description': bp.description,
                    'version': bp.version,
                    'is_public': bp.is_public,
                    'clone_count': bp.clone_count,
                    'created_at': bp.created_at.isoformat() if bp.created_at else None,
                    'updated_at': bp.updated_at.isoformat() if bp.updated_at else None,
                    'source': 'database',
                    'category': categorize_blueprint(bp.blueprint_data),
                    'tags': generate_tags(bp.blueprint_data),
                    'rating': 4.5,  # Default rating
                    'downloads': bp.clone_count,
                    'featured': False
                }
                all_blueprints.append(blueprint_dict)
                
            logger.info(f"Loaded {len(db_blueprints)} public blueprints from database")
        except Exception as e:
            logger.warning(f"Failed to load database blueprints: {e}")
        
        # 2. Load YAML blueprints from marketplace directory
        yaml_blueprints = load_marketplace_blueprints()
        
        # Add mock ratings and mark as featured
        for i, blueprint in enumerate(yaml_blueprints):
            blueprint['rating'] = 4.5 + (i % 5) * 0.1  # 4.5-4.9
            blueprint['downloads'] = 100 + (i * 50)  # Varying downloads
            blueprint['featured'] = i < 3  # First 3 are featured
            blueprint['source'] = 'yaml'
        
        all_blueprints.extend(yaml_blueprints)
        
        # Filter by category if provided
        if category:
            all_blueprints = [
                bp for bp in all_blueprints 
                if bp.get('category', '').lower() == category.lower()
            ]
        
        # Apply pagination
        total = len(all_blueprints)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_blueprints = all_blueprints[start_idx:end_idx]
        
        logger.info(f"Retrieved {len(paginated_blueprints)} of {total} total marketplace blueprints (page {page})")
        
        return {
            "blueprints": paginated_blueprints,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Failed to list marketplace blueprints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blueprints/{blueprint_id}")
async def get_marketplace_blueprint(
    blueprint_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific marketplace blueprint by ID (PUBLIC - no auth required).
    
    Tries to find the blueprint in:
    1. Database (if UUID format and is_public=True)
    2. YAML files in marketplace directory
    
    Args:
        blueprint_id: Blueprint identifier (UUID or filename without extension)
        db: Database session
        
    Returns:
        Blueprint data with full details
    """
    try:
        # Try to parse as UUID and fetch from database
        try:
            from uuid import UUID
            blueprint_uuid = UUID(blueprint_id)
            
            db_blueprint = db.query(Blueprint).filter(
                and_(
                    Blueprint.id == blueprint_uuid,
                    Blueprint.is_public == True,
                    Blueprint.is_deleted == False
                )
            ).first()
            
            if db_blueprint:
                blueprint_data = db_blueprint.blueprint_data.copy()
                blueprint_data['id'] = str(db_blueprint.id)
                blueprint_data['name'] = db_blueprint.name
                blueprint_data['description'] = db_blueprint.description
                blueprint_data['version'] = db_blueprint.version
                blueprint_data['is_public'] = db_blueprint.is_public
                blueprint_data['clone_count'] = db_blueprint.clone_count
                blueprint_data['source'] = 'database'
                blueprint_data['category'] = categorize_blueprint(blueprint_data)
                blueprint_data['tags'] = generate_tags(blueprint_data)
                
                logger.info(f"Retrieved public blueprint from database: {blueprint_id}")
                return blueprint_data
        except (ValueError, AttributeError):
            # Not a valid UUID, continue to YAML lookup
            pass
        
        # Try to load from YAML file
        blueprint_file = MARKETPLACE_DIR / f"{blueprint_id}.yaml"
        
        if not blueprint_file.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Blueprint '{blueprint_id}' not found in marketplace"
            )
        
        with open(blueprint_file, 'r') as f:
            blueprint_data = yaml.safe_load(f)
        
        # Add metadata
        blueprint_data['id'] = blueprint_id
        blueprint_data['marketplace_id'] = blueprint_id
        blueprint_data['is_marketplace'] = True
        blueprint_data['source'] = 'yaml'
        blueprint_data['category'] = categorize_blueprint(blueprint_data)
        blueprint_data['tags'] = generate_tags(blueprint_data)
        
        logger.info(f"Retrieved marketplace blueprint from YAML: {blueprint_id}")
        return blueprint_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get marketplace blueprint {blueprint_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blueprints/{blueprint_id}/clone")
async def clone_marketplace_blueprint(
    blueprint_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clone a marketplace blueprint to user's account.
    
    This creates a copy of the marketplace blueprint in the user's account
    so they can customize and deploy it.
    
    Handles both:
    1. Database blueprints (UUID format, is_public=True)
    2. YAML blueprints (string names from marketplace directory)
    
    Args:
        blueprint_id: Marketplace blueprint ID (UUID or filename)
        current_user: Authenticated user
        
    Returns:
        Created agent/blueprint
    """
    try:
        blueprint_data = None
        
        # Try to parse as UUID and fetch from database first
        try:
            from uuid import UUID
            blueprint_uuid = UUID(blueprint_id)
            
            db_blueprint = db.query(Blueprint).filter(
                and_(
                    Blueprint.id == blueprint_uuid,
                    Blueprint.is_public == True,
                    Blueprint.is_deleted == False
                )
            ).first()
            
            if db_blueprint:
                # Clone from database blueprint
                blueprint_data = db_blueprint.blueprint_data
                name = db_blueprint.name
                description = db_blueprint.description
                logger.info(f"Cloning database blueprint {blueprint_id}")
        except (ValueError, AttributeError):
            # Not a valid UUID, will try YAML file
            pass
        
        # If not found in database, try YAML file
        if blueprint_data is None:
            blueprint_file = MARKETPLACE_DIR / f"{blueprint_id}.yaml"
            
            if not blueprint_file.exists():
                raise HTTPException(status_code=404, detail=f"Blueprint '{blueprint_id}' not found in marketplace")
            
            with open(blueprint_file, 'r') as f:
                blueprint_data = yaml.safe_load(f)
            
            name = blueprint_data.get("name", blueprint_id)
            description = blueprint_data.get("description", "")
            logger.info(f"Cloning YAML blueprint {blueprint_id}")
        
        # Validate the blueprint data
        validation_result = validator.validate(blueprint_data)
        
        if not validation_result.valid:
            error_messages = [f"{err.field}: {err.message}" for err in validation_result.errors]
            raise HTTPException(
                status_code=400,
                detail=f"Blueprint validation failed: {', '.join(error_messages)}"
            )
        
        # Create new blueprint in user's account
        new_blueprint = blueprint_service.create_blueprint(
            db=db,
            user_id=current_user.id,
            name=name,
            description=description,
            blueprint_data=validation_result.normalized_blueprint,
        )

        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="marketplace.clone",
            summary=f"Cloned marketplace blueprint {blueprint_id}",
            metadata={"blueprint_id": str(new_blueprint.id)},
        )

        logger.info("Cloned marketplace blueprint %s for user %s", blueprint_id, current_user.id)

        return BlueprintResponse.from_orm(new_blueprint)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to clone marketplace blueprint %s: %s", blueprint_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
