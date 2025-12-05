"""Session service for managing chat sessions with message history."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session as DBSession
from sqlalchemy.orm.attributes import flag_modified

from frankenagent.db.models import Session, Blueprint

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing chat session CRUD operations."""
    
    def create_session(
        self,
        db: DBSession,
        user_id: UUID,
        blueprint_id: UUID
    ) -> Session:
        """Create new session for user and blueprint.
        
        Args:
            db: Database session
            user_id: ID of the user creating the session
            blueprint_id: ID of the blueprint/agent for this session
            
        Returns:
            Created Session instance
            
        Raises:
            ValueError: If blueprint doesn't exist or user doesn't have access
        """
        logger.info(f"Creating session for user {user_id} with blueprint {blueprint_id}")
        
        # Verify blueprint exists and user has access
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.is_deleted == False
        ).first()
        
        if not blueprint:
            raise ValueError(f"Blueprint {blueprint_id} not found")
        
        # Check access: owner or public
        if blueprint.user_id != user_id and not blueprint.is_public:
            raise ValueError(
                f"User {user_id} does not have access to blueprint {blueprint_id}"
            )
        
        # Create session
        session = Session(
            user_id=user_id,
            blueprint_id=blueprint_id,
            messages=[],
            last_message_at=None
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Session created: {session.id}")
        
        return session
    
    def get_user_sessions(
        self,
        db: DBSession,
        user_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's recent sessions with metadata.
        
        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of sessions to return (default: 50)
            
        Returns:
            List of session dictionaries with metadata including:
            - id: Session ID
            - blueprint_id: Blueprint ID
            - blueprint_name: Name of the blueprint
            - message_count: Number of messages in session
            - last_message_preview: Preview of last message (first 100 chars)
            - last_message_at: Timestamp of last message
            - created_at: Session creation timestamp
        """
        logger.debug(f"Fetching sessions for user {user_id} (limit: {limit})")
        
        # Query sessions with blueprint join
        sessions = db.query(Session, Blueprint).join(
            Blueprint, Session.blueprint_id == Blueprint.id
        ).filter(
            Session.user_id == user_id
        ).order_by(
            Session.last_message_at.desc().nullslast(),
            Session.created_at.desc()
        ).limit(limit).all()
        
        result = []
        for session, blueprint in sessions:
            messages = session.messages or []
            last_message = messages[-1] if messages else None
            
            result.append({
                "id": session.id,
                "blueprint_id": blueprint.id,
                "blueprint_name": blueprint.name,
                "message_count": len(messages),
                "last_message_preview": (
                    last_message.get("content", "")[:100] if last_message else None
                ),
                "last_message_at": session.last_message_at,
                "created_at": session.created_at
            })
        
        logger.debug(f"Found {len(result)} sessions for user {user_id}")
        
        return result
    
    def add_message(
        self,
        db: DBSession,
        session_id: UUID,
        user_id: UUID,
        role: str,
        content: str
    ) -> bool:
        """Add message to session by appending to JSONB array.
        
        Args:
            db: Database session
            session_id: ID of the session
            user_id: ID of the user (for ownership verification)
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            True if message added successfully, False if session not found or unauthorized
        """
        logger.debug(f"Adding {role} message to session {session_id}")
        
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id
        ).first()
        
        if not session:
            logger.warning(
                f"Add message failed: session {session_id} not found or "
                f"user {user_id} is not the owner"
            )
            return False
        
        # Append message to JSONB array
        # Note: We need to create a new list to trigger SQLAlchemy's change detection
        messages = list(session.messages or [])
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Assign the new list and flag as modified for SQLAlchemy
        session.messages = messages
        flag_modified(session, "messages")  # Explicitly mark JSONB field as modified
        session.last_message_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.debug(
            f"Message added to session {session_id} "
            f"(total messages: {len(messages)})"
        )
        
        return True
    
    def get_session_history(
        self,
        db: DBSession,
        session_id: UUID,
        user_id: UUID
    ) -> Optional[List[Dict[str, Any]]]:
        """Get message history for session.
        
        Args:
            db: Database session
            session_id: ID of the session
            user_id: ID of the user (for ownership verification)
            
        Returns:
            List of message dictionaries if session found and accessible,
            None if session not found or unauthorized.
            Each message contains:
            - role: 'user' or 'assistant'
            - content: Message content
            - timestamp: ISO 8601 timestamp
        """
        logger.debug(f"Fetching history for session {session_id}")
        
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id
        ).first()
        
        if not session:
            logger.warning(
                f"Get history failed: session {session_id} not found or "
                f"user {user_id} is not the owner"
            )
            return None
        
        messages = session.messages or []
        
        logger.debug(f"Retrieved {len(messages)} messages from session {session_id}")
        
        return messages
