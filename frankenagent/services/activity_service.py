"""User activity logging service leveraging the relational database."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from frankenagent.db.models import UserActivity

logger = logging.getLogger(__name__)


class ActivityService:
    """Service responsible for capturing and querying user activities."""

    def log_activity(
        self,
        db: Session,
        user_id: UUID,
        activity_type: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UserActivity:
        """Append an activity row for the supplied user.

        Args:
            db: Active SQLAlchemy session.
            user_id: User the activity belongs to.
            activity_type: Short machine readable identifier (e.g. 'blueprint.created').
            summary: Human readable summary describing the event.
            metadata: Optional JSON payload used by the UI for context.

        Returns:
            Persisted UserActivity instance.
        """
        payload = metadata or {}
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            summary=summary,
            details=payload,
            created_at=datetime.utcnow(),
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)

        logger.debug(
            "Logged activity %s for user %s",
            activity_type,
            user_id,
        )
        return activity

    def list_recent(
        self,
        db: Session,
        user_id: UUID,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return the newest activities for the user ordered by creation date."""
        query = (
            db.query(UserActivity)
            .filter(UserActivity.user_id == user_id)
            .order_by(UserActivity.created_at.desc())
            .limit(limit)
        )
        activities = query.all()
        return [
            {
                "id": activity.id,
                "activity_type": activity.activity_type,
                "summary": activity.summary,
                "metadata": activity.details or {},
                "created_at": activity.created_at,
            }
            for activity in activities
        ]
