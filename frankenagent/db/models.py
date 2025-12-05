"""SQLAlchemy database models for FrankenAgent Lab platform."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from frankenagent.db.base import Base


class User(Base):
    """User account model.
    
    Stores user authentication credentials and token quota information.
    """
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    bio = Column(Text, nullable=True)
    token_quota = Column(Integer, default=100000, nullable=False)
    token_used = Column(Integer, default=0, nullable=False)
    credit_balance = Column(Integer, default=1000, nullable=False)
    monthly_credit_limit = Column(Integer, default=1000, nullable=False)
    credit_reset_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    blueprints = relationship("Blueprint", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("UserAPIKey", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("MarketplaceRating", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Blueprint(Base):
    """Agent blueprint model.
    
    Stores agent configurations with ownership, versioning, and marketplace support.
    """
    
    __tablename__ = "blueprints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    blueprint_data = Column(JSON, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    clone_count = Column(Integer, default=0, nullable=False)
    rating_sum = Column(Integer, default=0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="blueprints")
    sessions = relationship("Session", back_populates="blueprint", cascade="all, delete-orphan")
    ratings = relationship("MarketplaceRating", back_populates="blueprint", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_blueprints_public", "is_public", postgresql_where=(is_public == True) & (is_deleted == False)),
    )
    
    def __repr__(self):
        return f"<Blueprint(id={self.id}, name={self.name}, version={self.version})>"


class Session(Base):
    """Chat session model.
    
    Stores conversation history between users and agents.
    """
    
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("blueprints.id", ondelete="CASCADE"), nullable=False, index=True)
    messages = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    blueprint = relationship("Blueprint", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index("idx_sessions_last_message", "user_id", "last_message_at"),
    )
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, blueprint_id={self.blueprint_id})>"


class UserAPIKey(Base):
    """User API key model with envelope encryption.
    
    Stores encrypted API keys for LLM providers using envelope encryption with Cloud KMS.
    Security features:
    - AES-256-GCM encryption with user-specific DEK
    - DEK encrypted by Cloud KMS KEK
    - Only last 4 characters stored for display
    - Nonce for GCM mode
    """
    
    __tablename__ = "user_api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # 'openai', 'anthropic', 'groq', 'gemini'
    key_name = Column(String(255), nullable=True)
    encrypted_key = Column(LargeBinary, nullable=False)  # AES-256-GCM encrypted key
    encrypted_dek = Column(LargeBinary, nullable=False)  # DEK encrypted by KMS
    key_last_four = Column(String(4), nullable=False)  # Last 4 chars for display
    nonce = Column(LargeBinary, nullable=False)  # GCM nonce
    kms_key_version = Column(String(255), nullable=False)  # KMS key version used
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_user_api_keys_provider", "user_id", "provider"),
    )
    
    def __repr__(self):
        return f"<UserAPIKey(id={self.id}, user_id={self.user_id}, provider={self.provider})>"


class MarketplaceRating(Base):
    """Marketplace blueprint rating model.
    
    Stores user ratings for public marketplace blueprints.
    """
    
    __tablename__ = "marketplace_ratings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("blueprints.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    blueprint = relationship("Blueprint", back_populates="ratings")
    user = relationship("User", back_populates="ratings")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        Index("idx_ratings_unique", "blueprint_id", "user_id", unique=True),
    )
    
    def __repr__(self):
        return f"<MarketplaceRating(id={self.id}, blueprint_id={self.blueprint_id}, rating={self.rating})>"


class UserActivity(Base):
    """Activity timeline for a user."""

    __tablename__ = "user_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(128), nullable=False, index=True)
    summary = Column(String(255), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="activities")

    __table_args__ = (
        Index("idx_user_activity_type", "user_id", "activity_type"),
    )

    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type={self.activity_type})>"
