"""Authentication API endpoints."""

import logging
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from frankenagent.api.models import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    UserRegisterResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
)
from frankenagent.auth.service import AuthService
from frankenagent.db.database import get_db
from frankenagent.db.models import User
from frankenagent.api.logging_middleware import auth_logger
from frankenagent.services.activity_service import ActivityService
from frankenagent.services.email_service import EmailService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Initialize services
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
auth_service = AuthService(secret_key=JWT_SECRET_KEY)
activity_service = ActivityService()
email_service = EmailService()


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        authorization: Authorization header with Bearer token
        db: Database session
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify token and extract user_id
    user_id = auth_service.verify_token(token)
    if not user_id:
        auth_logger.log_token_validation(
            user_id="unknown",
            valid=False,
            reason="Invalid or expired token"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        auth_logger.log_token_validation(
            user_id=str(user_id),
            valid=False,
            reason="User not found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful token validation
    auth_logger.log_token_validation(
        user_id=str(user.id),
        valid=True
    )
    
    return user


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, req: Request, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user with hashed password and returns JWT token.
    
    Args:
        request: User registration data (email, password, full_name)
        req: FastAPI request object (for client IP)
        db: Database session
        
    Returns:
        UserRegisterResponse with user info and access token
        
    Raises:
        HTTPException: 400 if email already exists
    """
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"Registration attempt for email: {request.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        logger.warning(f"Registration failed: email already exists: {request.email}")
        auth_logger.log_registration(
            email=request.email,
            user_id=None,
            client_ip=client_ip,
            success=False,
            error="Email already registered"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = auth_service.hash_password(request.password)
    
    # Create user
    user = User(
        email=request.email,
        password_hash=password_hash,
        full_name=request.full_name,
        avatar_url=None,
        bio=None,
        token_quota=100000,
        token_used=0,
        last_login_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate JWT token
    access_token = auth_service.create_access_token(user.id)
    
    # Update last_login_at for activity tracking
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    activity_service.log_activity(
        db=db,
        user_id=user.id,
        activity_type="user.login",
        summary="Signed in",
        metadata={"client_ip": client_ip},
    )
    
    logger.info(f"User registered successfully: {user.id}")
    auth_logger.log_registration(
        email=request.email,
        user_id=str(user.id),
        client_ip=client_ip,
        success=True
    )
    activity_service.log_activity(
        db=db,
        user_id=user.id,
        activity_type="user.registered",
        summary="Created a new FrankenAgent account",
        metadata={"email": user.email, "client_ip": client_ip},
    )
    
    return UserRegisterResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer",
        expires_in=86400
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest, req: Request, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    Verifies credentials and returns JWT token.
    
    Args:
        request: Login credentials (email, password)
        req: FastAPI request object (for client IP)
        db: Database session
        
    Returns:
        TokenResponse with access token
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"Login attempt for email: {request.email}")
    
    # Get user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        logger.warning(f"Login failed: user not found: {request.email}")
        auth_logger.log_login_attempt(
            email=request.email,
            client_ip=client_ip,
            success=False,
            error="User not found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not auth_service.verify_password(request.password, user.password_hash):
        logger.warning(f"Login failed: invalid password for: {request.email}")
        auth_logger.log_login_attempt(
            email=request.email,
            client_ip=client_ip,
            success=False,
            user_id=str(user.id),
            error="Invalid password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT token
    access_token = auth_service.create_access_token(user.id)
    
    logger.info(f"User logged in successfully: {user.id}")
    auth_logger.log_login_attempt(
        email=request.email,
        client_ip=client_ip,
        success=True,
        user_id=str(user.id)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        UserResponse with user information
    """
    logger.info(f"User info requested: {current_user.id}")
    
    return UserResponse.model_validate(current_user)


# OAuth endpoints
from frankenagent.auth.oauth_service import OAuthService
from frankenagent.api.models import OAuthLoginRequest
import secrets

oauth_service = OAuthService()


@router.post("/oauth/login", response_model=TokenResponse)
async def oauth_login(request: OAuthLoginRequest, req: Request, db: Session = Depends(get_db)):
    """
    Login or register with OAuth provider (Google or GitHub).
    
    Exchanges OAuth authorization code for user info and creates/logs in user.
    
    Args:
        request: OAuth login data (provider, code, redirect_uri)
        req: FastAPI request object (for client IP)
        db: Database session
        
    Returns:
        TokenResponse with access token
        
    Raises:
        HTTPException: 400 if OAuth exchange fails or 500 on error
    """
    client_ip = req.client.host if req.client else "unknown"
    logger.info(f"OAuth login attempt with provider: {request.provider}")
    
    # Exchange code for user info
    user_info = None
    
    # Use configured redirect URI from backend config to ensure it matches
    # the one used to generate the authorization URL.
    # We prefer the backend config over the frontend request param to prevent mismatches.
    
    if request.provider == "google":
        # Use backend configured URI if available, otherwise fallback to request
        redirect_uri = oauth_service.google_redirect_uri or request.redirect_uri
        user_info = await oauth_service.exchange_google_code(request.code, redirect_uri)
    elif request.provider == "github":
        # Use backend configured URI if available, otherwise fallback to request
        redirect_uri = oauth_service.github_redirect_uri or request.redirect_uri
        user_info = await oauth_service.exchange_github_code(request.code, redirect_uri)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {request.provider}"
        )
    
    if not user_info or not user_info.get("email"):
        logger.error(f"OAuth exchange failed for provider: {request.provider}")
        auth_logger.log_login_attempt(
            email="unknown",
            client_ip=client_ip,
            success=False,
            error=f"OAuth {request.provider} exchange failed"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to authenticate with OAuth provider"
        )
    
    email = user_info["email"]
    full_name = user_info.get("name")
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user with OAuth
        random_password = secrets.token_urlsafe(32)
        password_hash = auth_service.hash_password(random_password)
        
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            avatar_url=user_info.get("picture"),
            bio=None,
            token_quota=100000,
            token_used=0,
            last_login_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"New user created via OAuth: {user.id}")
        auth_logger.log_registration(
            email=email,
            user_id=str(user.id),
            client_ip=client_ip,
            success=True
        )
    else:
        logger.info(f"Existing user logged in via OAuth: {user.id}")
    
    auth_logger.log_login_attempt(
        email=email,
        client_ip=client_ip,
        success=True,
        user_id=str(user.id)
    )
    
    # Generate JWT token
    access_token = auth_service.create_access_token(user.id)
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    activity_service.log_activity(
        db=db,
        user_id=user.id,
        activity_type="user.login",
        summary=f"Signed in via {request.provider.capitalize()} OAuth",
        metadata={"provider": request.provider},
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400
    )


@router.get("/oauth/url/{provider}")
async def get_oauth_url(provider: str):
    """
    Get OAuth authorization URL for a provider.
    
    Args:
        provider: OAuth provider (google or github)
        
    Returns:
        Dict with authorization URL
        
    Raises:
        HTTPException: 400 if provider is unsupported
    """
    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    
    try:
        if provider == "google":
            auth_url = oauth_service.get_google_auth_url(state)
        elif provider == "github":
            auth_url = oauth_service.get_github_auth_url(state)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/callback")
async def oauth_callback(code: str, state: str, error: Optional[str] = None):
    """
    OAuth callback endpoint that redirects to frontend with auth code.
    
    This endpoint receives the OAuth callback from Google/GitHub and
    redirects to the frontend with the code and state parameters.
    
    Args:
        code: Authorization code from OAuth provider
        state: CSRF state token
        error: Optional error from OAuth provider
        
    Returns:
        Redirect to frontend with code and state
    """
    # Get frontend URL from environment or use default for local development
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Build redirect URL with query parameters
    if error:
        redirect_url = f"{frontend_url}?error={error}"
    else:
        redirect_url = f"{frontend_url}?code={code}&state={state}"
    
    return RedirectResponse(url=redirect_url)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request password reset email.
    
    Sends a password reset email to the user if the email exists.
    For security, always returns success even if email doesn't exist.
    
    Args:
        request: Forgot password request with email
        db: Database session
        
    Returns:
        ForgotPasswordResponse with success message
    """
    logger.info(f"Password reset requested for email: {request.email}")
    
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    
    if user:
        # Generate password reset token (valid for 1 hour)
        reset_token = auth_service.create_password_reset_token(user.id)
        
        # Send email with reset link
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}?reset_token={reset_token}"
        
        # Send password reset email
        email_sent = await email_service.send_password_reset_email(
            to_email=user.email,
            reset_url=reset_url,
            user_name=user.full_name
        )
        
        if email_sent:
            logger.info(f"Password reset email sent to {request.email}")
        else:
            logger.warning(f"Failed to send password reset email to {request.email}")
        
        logger.info(f"Password reset token generated for user: {user.id}")
    else:
        # For security, don't reveal if email exists
        logger.info(f"Password reset requested for non-existent email: {request.email}")
    
    # Always return success to prevent email enumeration
    return ForgotPasswordResponse(
        message="If an account exists with this email, you will receive a password reset link shortly."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using reset token.
    
    Verifies the reset token and updates the user's password.
    
    Args:
        request: Reset password request with token and new password
        db: Database session
        
    Returns:
        ResetPasswordResponse with success message
        
    Raises:
        HTTPException: 400 if token is invalid or expired
    """
    logger.info("Password reset attempt with token")
    
    # Verify reset token
    user_id = auth_service.verify_password_reset_token(request.token)
    if not user_id:
        logger.warning("Invalid or expired password reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"User not found for password reset: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Hash new password
    password_hash = auth_service.hash_password(request.new_password)
    
    # Update password
    user.password_hash = password_hash
    db.commit()
    
    # Send confirmation email
    await email_service.send_password_changed_email(
        to_email=user.email,
        user_name=user.full_name
    )
    
    logger.info(f"Password reset successful for user: {user.id}")
    
    return ResetPasswordResponse(
        message="Password has been reset successfully. You can now log in with your new password."
    )


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.
    
    Requires valid JWT token and current password verification.
    
    Args:
        request: Change password request with current and new password
        current_user: Current authenticated user (from dependency)
        db: Database session
        
    Returns:
        ChangePasswordResponse with success message
        
    Raises:
        HTTPException: 401 if current password is incorrect
    """
    logger.info(f"Password change attempt for user: {current_user.id}")
    
    # Verify current password
    if not auth_service.verify_password(request.current_password, current_user.password_hash):
        logger.warning(f"Password change failed: incorrect current password for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    password_hash = auth_service.hash_password(request.new_password)
    
    # Update password
    current_user.password_hash = password_hash
    db.commit()
    
    # Send confirmation email
    await email_service.send_password_changed_email(
        to_email=current_user.email,
        user_name=current_user.full_name
    )
    
    # Log activity
    activity_service.log_activity(
        db=db,
        user_id=current_user.id,
        activity_type="security.password_changed",
        summary="Changed account password",
        metadata={}
    )
    
    logger.info(f"Password changed successfully for user: {current_user.id}")
    
    return ChangePasswordResponse(
        message="Password has been changed successfully."
    )
