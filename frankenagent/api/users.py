"""User profile and activity endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from frankenagent.api.auth import get_current_user
from frankenagent.api.models import (
    UserActivityListResponse,
    UserActivityResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from frankenagent.db.database import get_db
from frankenagent.db.models import User
from frankenagent.services.activity_service import ActivityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])
activity_service = ActivityService()


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    """Return the authenticated user's profile."""
    return UserProfileResponse.model_validate(current_user)


@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Update profile metadata such as name, avatar, or bio."""
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.avatar_url is not None:
        current_user.avatar_url = request.avatar_url
    if request.bio is not None:
        current_user.bio = request.bio

    db.commit()
    db.refresh(current_user)

    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        activity_type="profile.updated",
        summary="Updated profile settings",
        metadata={
            "full_name": current_user.full_name,
            "has_avatar": bool(current_user.avatar_url),
        },
    )

    logger.info("Profile updated for user %s", current_user.id)
    return UserProfileResponse.model_validate(current_user)


@router.get("/me/activities", response_model=UserActivityListResponse)
async def list_activities(
    limit: Optional[int] = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of activities to return",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserActivityListResponse:
    """Return the user's recent activities."""
    activities = activity_service.list_recent(db=db, user_id=current_user.id, limit=limit or 20)
    responses = [UserActivityResponse(**activity) for activity in activities]
    return UserActivityListResponse(activities=responses)
