"""Pydantic models for API requests and responses."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


class ValidateRequest(BaseModel):
    """Request model for blueprint validation endpoint."""
    
    blueprint: Dict[str, Any]
    compile: bool = False


class ValidationError(BaseModel):
    """Model for validation error details."""
    
    field: str
    message: str


class ValidateResponse(BaseModel):
    """Response model for blueprint validation endpoint."""
    
    valid: bool
    blueprint_id: Optional[str] = None
    normalized_blueprint: Optional[Dict[str, Any]] = None
    errors: List[ValidationError] = Field(default_factory=list)


class RunRequest(BaseModel):
    """Request model for agent execution endpoint."""
    
    blueprint: Optional[Dict[str, Any]] = None
    blueprint_id: Optional[str] = None
    message: str
    session_id: Optional[str] = None
    stream: bool = False


class ToolCallLog(BaseModel):
    """Model for tool call execution log."""
    
    tool: str
    args: Dict[str, Any]
    duration_ms: int
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password endpoint."""
    
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Response model for forgot password endpoint."""
    
    message: str


class ResetPasswordRequest(BaseModel):
    """Request model for reset password endpoint."""
    
    token: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    """Response model for reset password endpoint."""
    
    message: str


class ChangePasswordRequest(BaseModel):
    """Request model for change password endpoint (authenticated users)."""
    
    current_password: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordResponse(BaseModel):
    """Response model for change password endpoint."""
    
    message: str


class RunResponse(BaseModel):
    """Response model for agent execution endpoint."""
    
    response: Optional[str] = None
    session_id: str
    tool_calls: List[ToolCallLog] = Field(default_factory=list)
    guardrails_triggered: List[str] = Field(default_factory=list)
    total_latency_ms: int
    error: Optional[str] = None


class ExecutionResult(BaseModel):
    """Model for agent execution result."""
    
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    session_id: str
    tool_calls: List[ToolCallLog] = Field(default_factory=list)
    guardrails_triggered: List[str] = Field(default_factory=list)
    total_latency_ms: int = 0


class LogsRequest(BaseModel):
    """Request model for logs retrieval endpoint."""
    
    session_id: str


class LogEntry(BaseModel):
    """Model for a single log entry."""
    
    timestamp: str
    event_type: str
    tool_name: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    success: Optional[bool] = None
    result: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class LogsResponse(BaseModel):
    """Response model for logs retrieval endpoint."""
    
    session_id: str
    logs: List[LogEntry] = Field(default_factory=list)


class ComponentSchemasResponse(BaseModel):
    """Response model for component schemas endpoint."""
    
    head: Dict[str, Any]
    arms: Dict[str, Any]
    legs: Dict[str, Any]
    heart: Dict[str, Any]
    spine: Dict[str, Any]


class ImproveInstructionsRequest(BaseModel):
    """Request model for instruction improvement endpoint."""
    
    current_instructions: str = Field(description="Current system prompt")
    improvement_goal: str = Field(description="What to improve")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (purpose, tools, etc.)"
    )


class ImproveInstructionsResponse(BaseModel):
    """Response model for instruction improvement endpoint."""
    
    improved_instructions: str
    explanation: str
    suggestions: List[str] = Field(default_factory=list)



# Authentication models

class UserRegisterRequest(BaseModel):
    """Request model for user registration."""
    
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    
    email: EmailStr
    password: str


class OAuthLoginRequest(BaseModel):
    """Request model for OAuth login."""
    
    provider: str = Field(description="OAuth provider: google or github")
    code: str = Field(description="OAuth authorization code")
    redirect_uri: str = Field(description="OAuth redirect URI")


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds


class UserResponse(BaseModel):
    """Response model for user information."""
    
    id: UUID
    email: str
    full_name: Optional[str]
    token_quota: int
    token_used: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserRegisterResponse(BaseModel):
    """Response model for user registration."""
    
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class UserProfileUpdateRequest(BaseModel):
    """Request model for updating profile settings."""

    full_name: Optional[str] = None
    avatar_url: Optional[str] = Field(None, description="Public avatar URL")
    bio: Optional[str] = Field(None, description="Short user bio")


class UserProfileResponse(BaseModel):
    """Response model for profile settings."""

    id: UUID
    email: EmailStr
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    token_quota: int
    token_used: int
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserActivityResponse(BaseModel):
    """Response model for an individual activity entry."""

    id: UUID
    activity_type: str
    summary: str
    metadata: Dict[str, Any]
    created_at: datetime


class UserActivityListResponse(BaseModel):
    """Response model for activity feeds."""

    activities: List[UserActivityResponse] = Field(default_factory=list)


# API Key Management models

class AddAPIKeyRequest(BaseModel):
    """Request model for adding an API key."""
    
    provider: str = Field(description="LLM provider: openai, anthropic, groq, gemini")
    api_key: str = Field(min_length=10, description="API key to encrypt and store")
    key_name: Optional[str] = Field(None, description="Optional user-friendly name")


class APIKeyResponse(BaseModel):
    """Response model for API key information."""
    
    id: str
    provider: str
    key_name: str
    key_preview: str  # Masked: "***...xyz123"
    created_at: str
    last_used_at: Optional[str]


class ListAPIKeysResponse(BaseModel):
    """Response model for listing user's API keys."""
    
    keys: List[APIKeyResponse]


class DeleteAPIKeyResponse(BaseModel):
    """Response model for API key deletion."""
    
    success: bool
    message: str


# Blueprint Management models

class BlueprintCreateRequest(BaseModel):
    """Request model for creating a blueprint."""
    
    name: str = Field(min_length=1, max_length=255, description="Blueprint name")
    description: Optional[str] = Field(None, description="Blueprint description")
    blueprint_data: Dict[str, Any] = Field(description="Blueprint configuration")


class BlueprintUpdateRequest(BaseModel):
    """Request model for updating a blueprint."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    blueprint_data: Optional[Dict[str, Any]] = None


class BlueprintResponse(BaseModel):
    """Response model for blueprint information."""
    
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    blueprint_data: Dict[str, Any]
    version: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BlueprintListItem(BaseModel):
    """Response model for blueprint list item (without full blueprint_data)."""
    
    id: UUID
    name: str
    description: Optional[str]
    version: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BlueprintListResponse(BaseModel):
    """Response model for listing blueprints."""
    
    blueprints: List[BlueprintListItem]


class AgentCreateResponse(BaseModel):
    """Response model for agent creation (wraps BlueprintResponse)."""
    
    agent: BlueprintResponse



# Marketplace models

class MarketplacePublishRequest(BaseModel):
    """Request model for publishing a blueprint to marketplace."""
    
    blueprint_id: UUID = Field(description="ID of blueprint to publish")


class MarketplacePublishResponse(BaseModel):
    """Response model for marketplace publish."""
    
    status: str = "published"
    blueprint_id: UUID


class MarketplaceListingResponse(BaseModel):
    """Response model for a single marketplace listing."""
    
    id: UUID
    name: str
    description: Optional[str]
    author_name: Optional[str]
    clone_count: int
    average_rating: float
    rating_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MarketplaceSearchResponse(BaseModel):
    """Response model for marketplace search results."""
    
    listings: List[MarketplaceListingResponse]
    total: int
    page: int
    page_size: int


class MarketplaceCloneResponse(BaseModel):
    """Response model for cloning a blueprint."""
    
    id: UUID
    name: str
    description: Optional[str]
    blueprint_data: Dict[str, Any]
    version: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MarketplaceRateRequest(BaseModel):
    """Request model for rating a blueprint."""
    
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5 stars")


class MarketplaceRateResponse(BaseModel):
    """Response model for rating a blueprint."""
    
    status: str = "rated"
    blueprint_id: UUID
    rating: int


# Session Management models

class SessionCreateRequest(BaseModel):
    """Request model for creating a session."""
    
    blueprint_id: UUID = Field(description="ID of blueprint/agent for this session")


class SessionResponse(BaseModel):
    """Response model for session information."""
    
    id: UUID
    blueprint_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionListItem(BaseModel):
    """Response model for session list item with metadata."""
    
    id: UUID
    blueprint_id: UUID
    blueprint_name: str
    message_count: int
    last_message_preview: Optional[str]
    last_message_at: Optional[datetime]
    created_at: datetime


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""
    
    sessions: List[SessionListItem]


class MessageItem(BaseModel):
    """Response model for a single message."""
    
    role: str
    content: str
    timestamp: str


class SessionHistoryResponse(BaseModel):
    """Response model for session message history."""
    
    messages: List[MessageItem]
