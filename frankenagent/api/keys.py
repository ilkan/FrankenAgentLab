"""API key management endpoints.

This module provides secure API key management endpoints for users to:
- Add encrypted API keys for LLM providers
- List their API keys (with masking)
- Delete API keys

Security features:
- All endpoints require authentication
- Keys are encrypted before storage
- Only masked keys returned in responses
- Ownership verified before operations
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from frankenagent.api.models import (
    AddAPIKeyRequest,
    APIKeyResponse,
    ListAPIKeysResponse,
    DeleteAPIKeyResponse,
)
from frankenagent.api.auth import get_current_user
from frankenagent.db.database import get_db
from frankenagent.db.models import User
from frankenagent.services.user_api_key_service import UserAPIKeyService
from frankenagent.services.api_key_encryption_service import APIKeyEncryptionService
from frankenagent.api.logging_middleware import auth_logger
import os

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/keys", tags=["API Keys"])

# Initialize services
# Note: In production, these should be initialized with proper GCP credentials
# For now, we'll use environment variables for configuration
def get_encryption_service() -> APIKeyEncryptionService:
    """Get or create encryption service instance."""
    environment = os.getenv("ENVIRONMENT", "development")
    
    # In development, use local encryption (no GCP required)
    if environment == "development":
        logger.info("Using local encryption for development (no GCP KMS)")
        # Use dummy values - the service will be wrapped with local encryption
        return APIKeyEncryptionService(
            project_id="local-dev",
            location="local",
            keyring="local-keyring",
            key="local-key",
            use_local_encryption=True
        )
    
    # In production, use real GCP KMS
    project_id = os.getenv("GCP_PROJECT_ID", "frankenagent-dev")
    location = os.getenv("GCP_LOCATION", "us-central1")
    keyring = os.getenv("KMS_KEYRING", "frankenagent-keyring")
    key = os.getenv("KMS_KEY", "api-key-encryption")
    
    return APIKeyEncryptionService(
        project_id=project_id,
        location=location,
        keyring=keyring,
        key=key,
        use_local_encryption=False
    )


def get_api_key_service() -> UserAPIKeyService:
    """Get or create API key service instance."""
    encryption_service = get_encryption_service()
    return UserAPIKeyService(encryption_service)


@router.post(
    "",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add API key",
    description="Add and encrypt an API key for an LLM provider"
)
async def add_api_key(
    request: AddAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    api_key_service: UserAPIKeyService = Depends(get_api_key_service)
) -> APIKeyResponse:
    """
    Add and encrypt user API key.
    
    The API key is encrypted using envelope encryption with Cloud KMS before storage.
    Only the last 4 characters are stored for display purposes.
    
    Args:
        request: API key details (provider, key, optional name)
        current_user: Authenticated user
        db: Database session
        api_key_service: API key service
        
    Returns:
        APIKeyResponse with masked key information
        
    Raises:
        HTTPException: If provider invalid or key format invalid
        
    Security:
    - Requires authentication
    - Key encrypted before storage
    - Plaintext key never logged or stored
    """
    try:
        # Add and encrypt the key
        api_key = api_key_service.add_api_key(
            db=db,
            user_id=current_user.id,
            provider=request.provider,
            plaintext_key=request.api_key,
            key_name=request.key_name
        )
        
        # Log API key access event
        auth_logger.log_api_key_access(
            user_id=str(current_user.id),
            provider=request.provider,
            action="add",
            success=True
        )
        
        # Return masked response
        return APIKeyResponse(
            id=str(api_key.id),
            provider=api_key.provider,
            key_name=api_key.key_name,
            key_preview=f"***...{api_key.key_last_four}",
            created_at=api_key.created_at.isoformat(),
            last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None
        )
        
    except ValueError as e:
        logger.warning(f"Invalid API key request: {e}")
        auth_logger.log_api_key_access(
            user_id=str(current_user.id),
            provider=request.provider,
            action="add",
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to add API key: {e}")
        auth_logger.log_api_key_access(
            user_id=str(current_user.id),
            provider=request.provider,
            action="add",
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add API key"
        )


@router.get(
    "",
    response_model=ListAPIKeysResponse,
    summary="List API keys",
    description="List user's API keys with masking (only last 4 characters shown)"
)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    api_key_service: UserAPIKeyService = Depends(get_api_key_service)
) -> ListAPIKeysResponse:
    """
    List user's API keys (masked).
    
    Returns list of API keys with:
    - ID, provider, key_name
    - Masked key preview: "***...xyz123"
    - Created and last used timestamps
    
    Args:
        current_user: Authenticated user
        db: Database session
        api_key_service: API key service
        
    Returns:
        ListAPIKeysResponse with masked keys
        
    Security:
    - Requires authentication
    - Only returns user's own keys
    - Keys are masked (only last 4 chars shown)
    """
    try:
        keys = api_key_service.get_user_api_keys(db=db, user_id=current_user.id)
        
        return ListAPIKeysResponse(
            keys=[APIKeyResponse(**key) for key in keys]
        )
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete(
    "/{key_id}",
    response_model=DeleteAPIKeyResponse,
    summary="Delete API key",
    description="Permanently delete an API key (requires ownership)"
)
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    api_key_service: UserAPIKeyService = Depends(get_api_key_service)
) -> DeleteAPIKeyResponse:
    """
    Securely delete API key.
    
    Performs hard delete (not soft delete) to ensure:
    - Encrypted key permanently removed
    - Encrypted DEK permanently removed
    - No recovery possible
    
    Args:
        key_id: API key ID to delete
        current_user: Authenticated user
        db: Database session
        api_key_service: API key service
        
    Returns:
        DeleteAPIKeyResponse with success status
        
    Raises:
        HTTPException: If key not found or not owned by user
        
    Security:
    - Requires authentication
    - Ownership verified before deletion
    - Hard delete (no recovery)
    """
    try:
        # Parse UUID
        try:
            key_uuid = UUID(key_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid key ID format"
            )
        
        # Delete the key
        success = api_key_service.delete_api_key(
            db=db,
            key_id=key_uuid,
            user_id=current_user.id
        )
        
        if not success:
            auth_logger.log_api_key_access(
                user_id=str(current_user.id),
                provider="unknown",
                action="delete",
                success=False,
                error="API key not found or not owned by user"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or not owned by user"
            )
        
        # Log successful deletion
        auth_logger.log_api_key_access(
            user_id=str(current_user.id),
            provider="unknown",
            action="delete",
            success=True
        )
        
        return DeleteAPIKeyResponse(
            success=True,
            message="API key deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )
