"""Session management API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from frankenagent.api.auth import get_current_user
from frankenagent.api.models import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    SessionListItem,
    SessionHistoryResponse,
    MessageItem,
)
from frankenagent.db.database import get_db
from frankenagent.db.models import User
from frankenagent.services.activity_service import ActivityService
from frankenagent.services.session_service import SessionService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

# Initialize session service
session_service = SessionService()
activity_service = ActivityService()


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Create a new chat session for a blueprint.
    
    Requires authentication. Creates a session linking the user to a specific
    blueprint/agent for conversation tracking.
    
    Args:
        request: Session creation data (blueprint_id)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SessionResponse with session ID and metadata
        
    Raises:
        HTTPException: 400 if blueprint doesn't exist or user doesn't have access
    """
    logger.info(
        f"Creating session for user {current_user.id} "
        f"with blueprint {request.blueprint_id}"
    )
    
    try:
        session = session_service.create_session(
            db=db,
            user_id=current_user.id,
            blueprint_id=request.blueprint_id
        )
        
        logger.info(f"Session created: {session.id}")
        activity_service.log_activity(
            db=db,
            user_id=current_user.id,
            activity_type="session.created",
            summary=f"Started session for blueprint {request.blueprint_id}",
            metadata={"session_id": str(session.id), "blueprint_id": str(request.blueprint_id)},
        )
        
        return SessionResponse.model_validate(session)
        
    except ValueError as e:
        logger.warning(f"Session creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    List user's chat sessions with metadata.
    
    Requires authentication. Returns recent sessions ordered by last message time.
    
    Args:
        limit: Maximum number of sessions to return (default: 50)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SessionListResponse with list of sessions and metadata
    """
    logger.info(f"Listing sessions for user {current_user.id} (limit: {limit})")
    
    sessions = session_service.get_user_sessions(
        db=db,
        user_id=current_user.id,
        limit=limit
    )
    
    # Convert to Pydantic models
    session_items = [SessionListItem(**session) for session in sessions]
    
    logger.info(f"Found {len(session_items)} sessions for user {current_user.id}")
    
    return SessionListResponse(sessions=session_items)


@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Get message history for a session.
    
    Requires authentication. Returns all messages in the session.
    
    Args:
        session_id: ID of the session
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SessionHistoryResponse with list of messages
        
    Raises:
        HTTPException: 404 if session not found or user doesn't have access
    """
    logger.info(f"Fetching history for session {session_id}")
    
    messages = session_service.get_session_history(
        db=db,
        session_id=session_id,
        user_id=current_user.id
    )
    
    if messages is None:
        logger.warning(
            f"Session {session_id} not found or user {current_user.id} "
            "doesn't have access"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    # Convert to Pydantic models
    message_items = [MessageItem(**msg) for msg in messages]
    
    logger.info(f"Retrieved {len(message_items)} messages from session {session_id}")
    
    return SessionHistoryResponse(messages=message_items)
