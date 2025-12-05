# Platform Evolution Design Document

## Overview

This design transforms FrankenAgent Lab from a local MVP into a production-ready multi-tenant platform with authentication, persistent storage, agent marketplace, and cloud deployment on GCP. The design maintains the existing Agno-based runtime and drag-and-drop frontend while adding enterprise features.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Users (Web Browsers)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Cloud CDN + Cloud Storage                       │
│              (Frontend Static Assets)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cloud Endpoints / API Gateway               │
│              (Rate Limiting, Auth, Routing)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Run (Backend)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Application                                 │   │
│  │  - Auth Service (JWT)                                │   │
│  │  - Blueprint Service (CRUD)                          │   │
│  │  - Marketplace Service                               │   │
│  │  - Agent Execution Service (Agno)                    │   │
│  │  - Session Management                                │   │
│  └──────────────────────────────────────────────────────┘   │
└───────┬──────────────────┬──────────────────┬───────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Cloud SQL   │  │ Memorystore  │  │   Secret     │
│ (PostgreSQL) │  │   (Redis)    │  │   Manager    │
│              │  │              │  │              │
│ - Users      │  │ - Agent      │  │ - API Keys   │
│ - Blueprints │  │   Cache      │  │ - DB Creds   │
│ - Sessions   │  │ - Rate       │  │              │
│ - Marketplace│  │   Limits     │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Component Breakdown

1. **Frontend (React + TypeScript)**
   - Existing drag-and-drop builder
   - New: Auth UI (login/register)
   - New: Marketplace browser
   - New: Multi-agent selector dropdown
   - Deployed to Cloud Storage with CDN

2. **Backend (FastAPI + Python)**
   - Existing: Blueprint validation, compilation, execution
   - New: Auth endpoints with JWT
   - New: Blueprint CRUD with PostgreSQL
   - New: Marketplace API
   - New: Session management
   - Deployed to Cloud Run

3. **Database (Cloud SQL PostgreSQL)**
   - User accounts and credentials
   - Blueprint storage with ownership
   - Session history
   - Marketplace listings

4. **Cache (Memorystore Redis)**
   - Compiled agent cache
   - Rate limiting counters
   - Session tokens (optional)

5. **Secrets (Secret Manager)**
   - OpenAI API key
   - Tavily API key
   - Database credentials
   - JWT signing key



## Data Models

### Database Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    token_quota INTEGER DEFAULT 100000,
    token_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Blueprints table
CREATE TABLE blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    blueprint_data JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    is_public BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    clone_count INTEGER DEFAULT 0,
    rating_sum INTEGER DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_blueprints_user_id ON blueprints(user_id);
CREATE INDEX idx_blueprints_public ON blueprints(is_public) WHERE is_public = TRUE AND is_deleted = FALSE;
CREATE INDEX idx_blueprints_name_search ON blueprints USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blueprint_id UUID NOT NULL REFERENCES blueprints(id) ON DELETE CASCADE,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_blueprint_id ON sessions(blueprint_id);
CREATE INDEX idx_sessions_last_message ON sessions(user_id, last_message_at DESC);

-- Marketplace ratings table
CREATE TABLE marketplace_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blueprint_id UUID NOT NULL REFERENCES blueprints(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(blueprint_id, user_id)
);

CREATE INDEX idx_ratings_blueprint ON marketplace_ratings(blueprint_id);
```

### Pydantic Models (Python)

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# User models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    token_quota: int
    token_used: int
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours

# Blueprint models
class BlueprintCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    blueprint_data: Dict[str, Any]

class BlueprintUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    blueprint_data: Optional[Dict[str, Any]] = None

class BlueprintResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    blueprint_data: Dict[str, Any]
    version: int
    is_public: bool
    created_at: datetime
    updated_at: datetime

# Marketplace models
class MarketplaceListingResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    author_name: Optional[str]
    clone_count: int
    average_rating: float
    rating_count: int
    created_at: datetime

class MarketplaceSearchResponse(BaseModel):
    listings: List[MarketplaceListingResponse]
    total: int
    page: int
    page_size: int

# Session models
class SessionCreate(BaseModel):
    blueprint_id: UUID

class SessionResponse(BaseModel):
    id: UUID
    blueprint_id: UUID
    blueprint_name: str
    last_message_preview: Optional[str]
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
```



## Components and Interfaces

### Authentication Service

```python
# frankenagent/auth/service.py
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

class AuthService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with salt rounds=12"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    
    def create_access_token(self, user_id: UUID, expires_delta: timedelta = None) -> str:
        """Create JWT access token"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[UUID]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = UUID(payload.get("sub"))
            return user_id
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
            return None
```

### Blueprint Service

```python
# frankenagent/services/blueprint_service.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from frankenagent.models import Blueprint, User
from frankenagent.compiler.validator import BlueprintValidator

class BlueprintService:
    def __init__(self, validator: BlueprintValidator):
        self.validator = validator
    
    def create_blueprint(
        self,
        db: Session,
        user_id: UUID,
        name: str,
        description: Optional[str],
        blueprint_data: dict
    ) -> Blueprint:
        """Create new blueprint with validation"""
        # Validate blueprint
        validation = self.validator.validate(blueprint_data)
        if not validation.valid:
            raise ValueError(f"Invalid blueprint: {validation.errors}")
        
        # Create in database
        blueprint = Blueprint(
            user_id=user_id,
            name=name,
            description=description,
            blueprint_data=validation.normalized_blueprint,
            version=1
        )
        db.add(blueprint)
        db.commit()
        db.refresh(blueprint)
        return blueprint
    
    def get_user_blueprints(self, db: Session, user_id: UUID) -> List[Blueprint]:
        """Get all blueprints owned by user"""
        return db.query(Blueprint).filter(
            Blueprint.user_id == user_id,
            Blueprint.is_deleted == False
        ).order_by(Blueprint.updated_at.desc()).all()
    
    def get_blueprint(self, db: Session, blueprint_id: UUID, user_id: UUID) -> Optional[Blueprint]:
        """Get blueprint by ID (must be owned by user or public)"""
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.is_deleted == False
        ).first()
        
        if not blueprint:
            return None
        
        # Check access: owner or public
        if blueprint.user_id != user_id and not blueprint.is_public:
            return None
        
        return blueprint
    
    def update_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID,
        updates: dict
    ) -> Optional[Blueprint]:
        """Update blueprint (must be owner)"""
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.user_id == user_id,
            Blueprint.is_deleted == False
        ).first()
        
        if not blueprint:
            return None
        
        # Validate if blueprint_data is being updated
        if "blueprint_data" in updates:
            validation = self.validator.validate(updates["blueprint_data"])
            if not validation.valid:
                raise ValueError(f"Invalid blueprint: {validation.errors}")
            updates["blueprint_data"] = validation.normalized_blueprint
        
        # Update fields
        for key, value in updates.items():
            setattr(blueprint, key, value)
        
        blueprint.version += 1
        blueprint.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(blueprint)
        return blueprint
    
    def delete_blueprint(self, db: Session, blueprint_id: UUID, user_id: UUID) -> bool:
        """Soft delete blueprint (must be owner)"""
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.user_id == user_id
        ).first()
        
        if not blueprint:
            return False
        
        blueprint.is_deleted = True
        blueprint.deleted_at = datetime.utcnow()
        db.commit()
        return True
```

### Marketplace Service

```python
# frankenagent/services/marketplace_service.py
from typing import List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from frankenagent.models import Blueprint, User, MarketplaceRating

class MarketplaceService:
    def publish_blueprint(self, db: Session, blueprint_id: UUID, user_id: UUID) -> bool:
        """Publish blueprint to marketplace"""
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.user_id == user_id
        ).first()
        
        if not blueprint:
            return False
        
        blueprint.is_public = True
        db.commit()
        return True
    
    def search_marketplace(
        self,
        db: Session,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """Search marketplace with pagination"""
        base_query = db.query(
            Blueprint,
            User.full_name.label("author_name"),
            func.coalesce(Blueprint.rating_sum / func.nullif(Blueprint.rating_count, 0), 0).label("avg_rating")
        ).join(User, Blueprint.user_id == User.id).filter(
            Blueprint.is_public == True,
            Blueprint.is_deleted == False
        )
        
        # Apply search filter
        if query:
            search_filter = or_(
                Blueprint.name.ilike(f"%{query}%"),
                Blueprint.description.ilike(f"%{query}%")
            )
            base_query = base_query.filter(search_filter)
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination
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
        
        return listings, total
    
    def clone_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID
    ) -> Optional[Blueprint]:
        """Clone marketplace blueprint to user's collection"""
        source = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.is_public == True,
            Blueprint.is_deleted == False
        ).first()
        
        if not source:
            return None
        
        # Create copy
        cloned = Blueprint(
            user_id=user_id,
            name=f"{source.name} (Copy)",
            description=source.description,
            blueprint_data=source.blueprint_data,
            version=1,
            is_public=False
        )
        
        # Increment clone count
        source.clone_count += 1
        
        db.add(cloned)
        db.commit()
        db.refresh(cloned)
        return cloned
    
    def rate_blueprint(
        self,
        db: Session,
        blueprint_id: UUID,
        user_id: UUID,
        rating: int
    ) -> bool:
        """Rate a marketplace blueprint (1-5 stars)"""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        blueprint = db.query(Blueprint).filter(
            Blueprint.id == blueprint_id,
            Blueprint.is_public == True
        ).first()
        
        if not blueprint:
            return False
        
        # Check if user already rated
        existing = db.query(MarketplaceRating).filter(
            MarketplaceRating.blueprint_id == blueprint_id,
            MarketplaceRating.user_id == user_id
        ).first()
        
        if existing:
            # Update existing rating
            old_rating = existing.rating
            existing.rating = rating
            blueprint.rating_sum = blueprint.rating_sum - old_rating + rating
        else:
            # Create new rating
            new_rating = MarketplaceRating(
                blueprint_id=blueprint_id,
                user_id=user_id,
                rating=rating
            )
            db.add(new_rating)
            blueprint.rating_sum += rating
            blueprint.rating_count += 1
        
        db.commit()
        return True
```



### Agent Cache Service

```python
# frankenagent/services/cache_service.py
import redis
import pickle
from typing import Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

class AgentCacheService:
    def __init__(self, redis_host: str, redis_port: int = 6379):
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self.ttl = 3600  # 1 hour
    
    def get_compiled_agent(self, blueprint_id: UUID, version: int):
        """Get compiled agent from cache"""
        key = f"agent:{blueprint_id}:{version}"
        try:
            data = self.redis.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return pickle.loads(data)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set_compiled_agent(self, blueprint_id: UUID, version: int, agent):
        """Cache compiled agent"""
        key = f"agent:{blueprint_id}:{version}"
        try:
            data = pickle.dumps(agent)
            self.redis.setex(key, self.ttl, data)
            logger.debug(f"Cache SET: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def invalidate_agent(self, blueprint_id: UUID):
        """Invalidate all versions of an agent"""
        pattern = f"agent:{blueprint_id}:*"
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.debug(f"Cache INVALIDATE: {len(keys)} keys for {blueprint_id}")
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
```

### Rate Limiting Service

```python
# frankenagent/services/rate_limit_service.py
import redis
from typing import Tuple
from uuid import UUID
import time

class RateLimitService:
    def __init__(self, redis_host: str, redis_port: int = 6379):
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        self.requests_per_minute = 100
        self.requests_per_day = 1000
    
    def check_rate_limit(self, user_id: UUID) -> Tuple[bool, int]:
        """
        Check if user is within rate limits.
        Returns (allowed, retry_after_seconds)
        """
        minute_key = f"ratelimit:minute:{user_id}:{int(time.time() / 60)}"
        day_key = f"ratelimit:day:{user_id}:{int(time.time() / 86400)}"
        
        # Check minute limit
        minute_count = self.redis.incr(minute_key)
        if minute_count == 1:
            self.redis.expire(minute_key, 60)
        
        if minute_count > self.requests_per_minute:
            return False, 60
        
        # Check day limit
        day_count = self.redis.incr(day_key)
        if day_count == 1:
            self.redis.expire(day_key, 86400)
        
        if day_count > self.requests_per_day:
            return False, 86400
        
        return True, 0
    
    def get_usage(self, user_id: UUID) -> dict:
        """Get current usage stats"""
        minute_key = f"ratelimit:minute:{user_id}:{int(time.time() / 60)}"
        day_key = f"ratelimit:day:{user_id}:{int(time.time() / 86400)}"
        
        minute_count = int(self.redis.get(minute_key) or 0)
        day_count = int(self.redis.get(day_key) or 0)
        
        return {
            "requests_this_minute": minute_count,
            "requests_this_day": day_count,
            "minute_limit": self.requests_per_minute,
            "day_limit": self.requests_per_day
        }
```

### Session Service

```python
# frankenagent/services/session_service.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session as DBSession
from frankenagent.models import Session, Blueprint
from datetime import datetime

class SessionService:
    def create_session(
        self,
        db: DBSession,
        user_id: UUID,
        blueprint_id: UUID
    ) -> Session:
        """Create new session for user and blueprint"""
        session = Session(
            user_id=user_id,
            blueprint_id=blueprint_id,
            messages=[],
            last_message_at=None
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def get_user_sessions(
        self,
        db: DBSession,
        user_id: UUID,
        limit: int = 50
    ) -> List[dict]:
        """Get user's recent sessions with metadata"""
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
                "last_message_preview": last_message.get("content", "")[:100] if last_message else None,
                "last_message_at": session.last_message_at,
                "created_at": session.created_at
            })
        
        return result
    
    def add_message(
        self,
        db: DBSession,
        session_id: UUID,
        user_id: UUID,
        role: str,
        content: str
    ) -> bool:
        """Add message to session"""
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id
        ).first()
        
        if not session:
            return False
        
        messages = session.messages or []
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        session.messages = messages
        session.last_message_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    def get_session_history(
        self,
        db: DBSession,
        session_id: UUID,
        user_id: UUID
    ) -> Optional[List[dict]]:
        """Get message history for session"""
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id
        ).first()
        
        if not session:
            return None
        
        return session.messages or []
```



## API Endpoints

### Authentication Endpoints

```python
# POST /api/auth/register
Request:
{
  "email": "user@example.com",
  "password": "securepass123",
  "full_name": "John Doe"
}

Response: 201 Created
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "token_quota": 100000,
    "token_used": 0,
    "created_at": "2025-01-15T10:00:00Z"
  },
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}

# POST /api/auth/login
Request:
{
  "email": "user@example.com",
  "password": "securepass123"
}

Response: 200 OK
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}

# GET /api/auth/me (requires auth)
Response: 200 OK
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "token_quota": 100000,
  "token_used": 1250,
  "created_at": "2025-01-15T10:00:00Z"
}
```

### Blueprint Endpoints

```python
# POST /api/blueprints (requires auth)
Request:
{
  "name": "My Research Agent",
  "description": "Agent for web research",
  "blueprint_data": { ... }
}

Response: 201 Created
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "My Research Agent",
  "description": "Agent for web research",
  "blueprint_data": { ... },
  "version": 1,
  "is_public": false,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}

# GET /api/blueprints (requires auth)
Response: 200 OK
{
  "blueprints": [
    {
      "id": "uuid",
      "name": "My Research Agent",
      "description": "Agent for web research",
      "version": 1,
      "is_public": false,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ]
}

# GET /api/blueprints/{id} (requires auth)
Response: 200 OK
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "My Research Agent",
  "description": "Agent for web research",
  "blueprint_data": { ... },
  "version": 1,
  "is_public": false,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}

# PUT /api/blueprints/{id} (requires auth)
Request:
{
  "name": "Updated Name",
  "blueprint_data": { ... }
}

Response: 200 OK
{
  "id": "uuid",
  "version": 2,
  ...
}

# DELETE /api/blueprints/{id} (requires auth)
Response: 204 No Content
```

### Marketplace Endpoints

```python
# POST /api/marketplace/publish (requires auth)
Request:
{
  "blueprint_id": "uuid"
}

Response: 200 OK
{
  "status": "published"
}

# GET /api/marketplace?q=research&page=1&page_size=20
Response: 200 OK
{
  "listings": [
    {
      "id": "uuid",
      "name": "Research Agent",
      "description": "...",
      "author_name": "John Doe",
      "clone_count": 42,
      "average_rating": 4.5,
      "rating_count": 10,
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}

# POST /api/marketplace/{id}/clone (requires auth)
Response: 201 Created
{
  "id": "new-uuid",
  "name": "Research Agent (Copy)",
  ...
}

# POST /api/marketplace/{id}/rate (requires auth)
Request:
{
  "rating": 5
}

Response: 200 OK
{
  "status": "rated"
}
```

### Session Endpoints

```python
# POST /api/sessions (requires auth)
Request:
{
  "blueprint_id": "uuid"
}

Response: 201 Created
{
  "id": "session-uuid",
  "blueprint_id": "uuid",
  "created_at": "2025-01-15T10:00:00Z"
}

# GET /api/sessions (requires auth)
Response: 200 OK
{
  "sessions": [
    {
      "id": "session-uuid",
      "blueprint_id": "uuid",
      "blueprint_name": "My Agent",
      "message_count": 5,
      "last_message_preview": "What is...",
      "last_message_at": "2025-01-15T10:05:00Z",
      "created_at": "2025-01-15T10:00:00Z"
    }
  ]
}

# GET /api/sessions/{id}/history (requires auth)
Response: 200 OK
{
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-01-15T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Hi there!",
      "timestamp": "2025-01-15T10:00:01Z"
    }
  ]
}
```

### Agent Execution Endpoint (Updated)

```python
# POST /api/agents/run (requires auth)
Request:
{
  "blueprint_id": "uuid",  # Now from database
  "message": "What is the weather?",
  "session_id": "session-uuid"  # Optional
}

Response: 200 OK
{
  "response": "The weather is...",
  "session_id": "session-uuid",
  "tool_calls": [...],
  "guardrails_triggered": [],
  "total_latency_ms": 1250,
  "error": null
}
```



## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Blueprint validation failed",
    "details": {
      "field": "head.provider",
      "message": "Unsupported provider"
    }
  }
}
```

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid input or validation error
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - User doesn't have permission
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Rate Limiting Headers

When rate limited, responses include:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705320000

{
  "error": {
    "type": "RateLimitExceeded",
    "message": "Rate limit exceeded: 100 requests per minute",
    "retry_after": 60
  }
}
```

## Testing Strategy

### Unit Tests

Test individual services in isolation:

```python
# tests/test_auth_service.py
def test_hash_password():
    auth = AuthService(secret_key="test")
    hashed = auth.hash_password("password123")
    assert auth.verify_password("password123", hashed)
    assert not auth.verify_password("wrong", hashed)

def test_create_access_token():
    auth = AuthService(secret_key="test")
    user_id = uuid4()
    token = auth.create_access_token(user_id)
    verified_id = auth.verify_token(token)
    assert verified_id == user_id

# tests/test_blueprint_service.py
def test_create_blueprint(db_session, mock_validator):
    service = BlueprintService(mock_validator)
    blueprint = service.create_blueprint(
        db=db_session,
        user_id=uuid4(),
        name="Test Agent",
        description="Test",
        blueprint_data={"head": {...}}
    )
    assert blueprint.id is not None
    assert blueprint.version == 1
```

### Integration Tests

Test API endpoints end-to-end:

```python
# tests/test_api_integration.py
def test_register_login_flow(client):
    # Register
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    token = response.json()["access_token"]
    
    # Login
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    
    # Access protected endpoint
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_blueprint_crud(client, auth_token):
    # Create
    response = client.post(
        "/api/blueprints",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "Test Agent",
            "blueprint_data": {...}
        }
    )
    assert response.status_code == 201
    blueprint_id = response.json()["id"]
    
    # Read
    response = client.get(
        f"/api/blueprints/{blueprint_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    
    # Update
    response = client.put(
        f"/api/blueprints/{blueprint_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["version"] == 2
    
    # Delete
    response = client.delete(
        f"/api/blueprints/{blueprint_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204
```

### Load Tests

Test performance and scalability:

```python
# tests/load_test.py
from locust import HttpUser, task, between

class FrankenAgentUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def list_blueprints(self):
        self.client.get(
            "/api/blueprints",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def execute_agent(self):
        self.client.post(
            "/api/agents/run",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "blueprint_id": "test-uuid",
                "message": "Hello"
            }
        )
```



## Deployment Architecture

### GCP Infrastructure

```
Project: frankenagent-prod
Region: us-central1

Resources:
├── Cloud Run (Backend)
│   ├── Service: frankenagent-backend
│   ├── Min instances: 0
│   ├── Max instances: 10
│   ├── Memory: 2GB
│   ├── CPU: 2
│   └── Concurrency: 80
│
├── Cloud SQL (Database)
│   ├── Instance: frankenagent-db
│   ├── Type: db-f1-micro (MVP) → db-n1-standard-1 (prod)
│   ├── Storage: 10GB SSD
│   ├── Backups: Daily automated
│   └── High Availability: Enabled (prod)
│
├── Memorystore (Redis)
│   ├── Instance: frankenagent-cache
│   ├── Tier: Basic (MVP) → Standard (prod)
│   ├── Memory: 1GB
│   └── Version: Redis 7.0
│
├── Cloud Storage (Frontend)
│   ├── Bucket: frankenagent-frontend
│   ├── CDN: Enabled
│   └── CORS: Configured
│
├── Secret Manager
│   ├── OPENAI_API_KEY
│   ├── TAVILY_API_KEY
│   ├── DATABASE_URL
│   ├── REDIS_HOST
│   └── JWT_SECRET_KEY
│
└── Cloud Build (CI/CD)
    ├── Trigger: Push to main branch
    ├── Build: Docker image
    └── Deploy: Cloud Run
```

### Deployment Scripts

#### 1. GCP CLI Installation Script

```bash
#!/bin/bash
# scripts/install-gcp-cli.sh

echo "Installing Google Cloud CLI..."

# macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install --cask google-cloud-sdk
    
# Linux
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
fi

# Initialize gcloud
echo "Initializing gcloud..."
gcloud init

# Install components
gcloud components install beta
gcloud components update

echo "✓ Google Cloud CLI installed successfully"
```

#### 2. Firebase CLI Installation Script

```bash
#!/bin/bash
# scripts/install-firebase-cli.sh

echo "Installing Firebase CLI..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Please install Node.js first."
    exit 1
fi

# Install Firebase CLI globally
npm install -g firebase-tools

# Login to Firebase
echo "Logging in to Firebase..."
firebase login

echo "✓ Firebase CLI installed successfully"
```

#### 3. Infrastructure Setup Script

```bash
#!/bin/bash
# scripts/setup-infrastructure.sh

set -e

PROJECT_ID="frankenagent-prod"
REGION="us-central1"
DB_INSTANCE="frankenagent-db"
REDIS_INSTANCE="frankenagent-cache"

echo "Setting up GCP infrastructure for $PROJECT_ID..."

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling APIs..."
gcloud services enable \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    storage-api.googleapis.com

# Create Cloud SQL instance
echo "Creating Cloud SQL instance..."
gcloud sql instances create $DB_INSTANCE \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04

# Create database
echo "Creating database..."
gcloud sql databases create frankenagent \
    --instance=$DB_INSTANCE

# Create database user
echo "Creating database user..."
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create frankenagent \
    --instance=$DB_INSTANCE \
    --password=$DB_PASSWORD

# Store database password in Secret Manager
echo "Storing database credentials..."
echo -n "postgresql://frankenagent:$DB_PASSWORD@/frankenagent?host=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE" | \
    gcloud secrets create DATABASE_URL --data-file=-

# Create Redis instance
echo "Creating Redis instance..."
gcloud redis instances create $REDIS_INSTANCE \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_7_0 \
    --tier=basic

# Get Redis host
REDIS_HOST=$(gcloud redis instances describe $REDIS_INSTANCE \
    --region=$REGION \
    --format="value(host)")

# Store Redis host in Secret Manager
echo -n "$REDIS_HOST" | gcloud secrets create REDIS_HOST --data-file=-

# Create storage bucket for frontend
echo "Creating storage bucket..."
gsutil mb -l $REGION gs://$PROJECT_ID-frontend
gsutil web set -m index.html gs://$PROJECT_ID-frontend
gsutil iam ch allUsers:objectViewer gs://$PROJECT_ID-frontend

# Enable CORS for bucket
cat > cors.json <<EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set cors.json gs://$PROJECT_ID-frontend
rm cors.json

echo "✓ Infrastructure setup complete!"
echo ""
echo "Next steps:"
echo "1. Add API keys to Secret Manager:"
echo "   echo -n 'your-key' | gcloud secrets create OPENAI_API_KEY --data-file=-"
echo "   echo -n 'your-key' | gcloud secrets create TAVILY_API_KEY --data-file=-"
echo "   echo -n 'your-secret' | gcloud secrets create JWT_SECRET_KEY --data-file=-"
echo ""
echo "2. Run database migrations:"
echo "   ./scripts/run-migrations.sh"
echo ""
echo "3. Deploy backend:"
echo "   ./scripts/deploy-backend.sh"
echo ""
echo "4. Deploy frontend:"
echo "   ./scripts/deploy-frontend.sh"
```

#### 4. Database Migration Script

```bash
#!/bin/bash
# scripts/run-migrations.sh

set -e

PROJECT_ID="frankenagent-prod"
REGION="us-central1"
DB_INSTANCE="frankenagent-db"

echo "Running database migrations..."

# Get database URL from Secret Manager
DATABASE_URL=$(gcloud secrets versions access latest --secret="DATABASE_URL")

# Run migrations using Cloud SQL Proxy
cloud_sql_proxy -instances=$PROJECT_ID:$REGION:$DB_INSTANCE=tcp:5432 &
PROXY_PID=$!

# Wait for proxy to start
sleep 3

# Run Alembic migrations
export DATABASE_URL="postgresql://frankenagent:password@localhost:5432/frankenagent"
poetry run alembic upgrade head

# Kill proxy
kill $PROXY_PID

echo "✓ Migrations complete!"
```

#### 5. Backend Deployment Script

```bash
#!/bin/bash
# scripts/deploy-backend.sh

set -e

PROJECT_ID="frankenagent-prod"
REGION="us-central1"
SERVICE_NAME="frankenagent-backend"
DB_INSTANCE="frankenagent-db"

echo "Deploying backend to Cloud Run..."

# Build and deploy
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=10 \
    --concurrency=80 \
    --timeout=300 \
    --set-cloudsql-instances=$PROJECT_ID:$REGION:$DB_INSTANCE \
    --set-secrets=DATABASE_URL=DATABASE_URL:latest,\
OPENAI_API_KEY=OPENAI_API_KEY:latest,\
TAVILY_API_KEY=TAVILY_API_KEY:latest,\
JWT_SECRET_KEY=JWT_SECRET_KEY:latest,\
REDIS_HOST=REDIS_HOST:latest \
    --set-env-vars=ENVIRONMENT=production,\
LOG_LEVEL=INFO

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

echo "✓ Backend deployed successfully!"
echo "Service URL: $SERVICE_URL"
```

#### 6. Frontend Deployment Script

```bash
#!/bin/bash
# scripts/deploy-frontend.sh

set -e

PROJECT_ID="frankenagent-prod"
BUCKET="gs://$PROJECT_ID-frontend"

echo "Building frontend..."
cd frontend
npm install
npm run build

echo "Deploying to Cloud Storage..."
gsutil -m rsync -r -d build/ $BUCKET

echo "Setting cache control..."
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" $BUCKET/**/*.html
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" $BUCKET/**/*.js
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" $BUCKET/**/*.css

echo "✓ Frontend deployed successfully!"
echo "URL: https://storage.googleapis.com/$PROJECT_ID-frontend/index.html"
```

#### 7. CI/CD Configuration

```yaml
# cloudbuild.yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/frankenagent-backend:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/frankenagent-backend:latest'
      - '.'
  
  # Push Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/frankenagent-backend:$COMMIT_SHA'
  
  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'frankenagent-backend'
      - '--image=gcr.io/$PROJECT_ID/frankenagent-backend:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'

images:
  - 'gcr.io/$PROJECT_ID/frankenagent-backend:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/frankenagent-backend:latest'

options:
  machineType: 'N1_HIGHCPU_8'
```



### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY frankenagent ./frankenagent
COPY blueprints ./blueprints

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "frankenagent.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Environment Configuration

```python
# frankenagent/config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    
    # Database
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # Redis
    redis_host: str
    redis_port: int = 6379
    
    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API Keys
    openai_api_key: str
    tavily_api_key: str
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_day: int = 1000
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

## Security Considerations

### Authentication Security

1. **Password Hashing**: bcrypt with 12 salt rounds
2. **JWT Tokens**: 
   - HS256 algorithm
   - 24-hour expiration
   - Stored in httpOnly cookies (frontend)
3. **Token Refresh**: Implement refresh tokens for long-lived sessions

### API Security

1. **HTTPS Only**: Enforce TLS 1.2+ in production
2. **CORS**: Restrict origins to known domains
3. **Rate Limiting**: Per-user and per-IP limits
4. **Input Validation**: Pydantic models for all inputs
5. **SQL Injection**: Use parameterized queries (SQLAlchemy ORM)

### Secret Management

1. **Never commit secrets**: Use `.env` for local, Secret Manager for prod
2. **Rotate secrets**: Regular rotation schedule for API keys
3. **Least privilege**: Service accounts with minimal permissions
4. **Audit logging**: Track secret access in Cloud Logging

### Database Security

1. **Encrypted connections**: SSL/TLS for all database connections
2. **Private IP**: Database not exposed to public internet
3. **Automated backups**: Daily backups with 7-day retention
4. **Access control**: IAM-based database access

## Monitoring and Observability

### Logging Strategy

```python
# frankenagent/logging_config.py
import logging
from google.cloud import logging as cloud_logging

def setup_logging():
    if settings.environment == "production":
        # Use Cloud Logging in production
        client = cloud_logging.Client()
        client.setup_logging()
    else:
        # Use standard logging in development
        logging.basicConfig(
            level=settings.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

# Log structured data
logger = logging.getLogger(__name__)
logger.info("Agent executed", extra={
    "user_id": str(user_id),
    "blueprint_id": str(blueprint_id),
    "duration_ms": duration,
    "tool_calls": len(tool_calls)
})
```

### Metrics to Track

1. **Request Metrics**:
   - Request rate (req/s)
   - Response latency (p50, p95, p99)
   - Error rate (%)
   - Status code distribution

2. **Business Metrics**:
   - Active users (DAU, MAU)
   - Blueprints created
   - Agent executions
   - Marketplace clones
   - Token usage

3. **Infrastructure Metrics**:
   - Cloud Run instances
   - Database connections
   - Redis cache hit rate
   - Database CPU/memory
   - Storage usage

### Alerting Rules

```yaml
# monitoring/alerts.yaml
alerts:
  - name: high_error_rate
    condition: error_rate > 5%
    duration: 5m
    severity: critical
    notification: pagerduty
  
  - name: high_latency
    condition: p95_latency > 2000ms
    duration: 5m
    severity: warning
    notification: slack
  
  - name: database_cpu_high
    condition: db_cpu > 80%
    duration: 10m
    severity: warning
    notification: slack
  
  - name: service_down
    condition: uptime_check_failed
    duration: 1m
    severity: critical
    notification: pagerduty
```

### Health Check Endpoint

```python
# frankenagent/api/health.py
from fastapi import APIRouter, status
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for uptime monitoring"""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        # Check Redis connection
        redis_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "cache": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )
```

## Performance Optimization

### Database Optimization

1. **Indexing Strategy**:
   - Index on `user_id` for all user-owned resources
   - Index on `is_public` for marketplace queries
   - Full-text search index on blueprint names/descriptions
   - Composite index on `(user_id, last_message_at)` for sessions

2. **Connection Pooling**:
   ```python
   engine = create_engine(
       settings.database_url,
       pool_size=5,
       max_overflow=10,
       pool_pre_ping=True,
       pool_recycle=3600
   )
   ```

3. **Query Optimization**:
   - Use `select_related` for joins
   - Paginate large result sets
   - Avoid N+1 queries

### Caching Strategy

1. **Agent Compilation Cache**:
   - Key: `agent:{blueprint_id}:{version}`
   - TTL: 1 hour
   - Invalidate on blueprint update

2. **Marketplace Listings Cache**:
   - Key: `marketplace:page:{page}:query:{query}`
   - TTL: 5 minutes
   - Invalidate on new publish

3. **User Session Cache**:
   - Key: `session:{session_id}`
   - TTL: 24 hours
   - Store recent messages for quick access

### Frontend Optimization

1. **Code Splitting**: Lazy load routes and components
2. **Asset Optimization**: Minify JS/CSS, compress images
3. **CDN**: Serve static assets from Cloud CDN
4. **Caching Headers**: 
   - HTML: `Cache-Control: public, max-age=3600`
   - JS/CSS: `Cache-Control: public, max-age=31536000, immutable`

## Migration Strategy

### Phase 1: Parallel Run (Week 1)

1. Deploy new infrastructure alongside existing MVP
2. Migrate existing blueprints to database
3. Test with internal users
4. Monitor for issues

### Phase 2: Gradual Rollout (Week 2)

1. Enable auth for new users
2. Migrate existing users (if any)
3. Enable marketplace for beta users
4. Monitor metrics and performance

### Phase 3: Full Cutover (Week 3)

1. Switch all traffic to new platform
2. Deprecate file-based blueprints
3. Enable all features for all users
4. Decommission old infrastructure

### Rollback Plan

If critical issues arise:

1. Switch traffic back to old infrastructure
2. Disable new features
3. Investigate and fix issues
4. Re-deploy with fixes

## Cost Optimization

### Development Environment

- Cloud Run: Min instances = 0 (pay per request)
- Cloud SQL: db-f1-micro ($25/month)
- Redis: 1GB Basic tier ($30/month)
- **Total: ~$60/month**

### Production Environment (Estimated)

- Cloud Run: ~$50/month (10K requests/day)
- Cloud SQL: db-n1-standard-1 ($100/month)
- Redis: 5GB Standard tier ($150/month)
- Cloud Storage + CDN: $10/month
- Secret Manager: $1/month
- **Total: ~$310/month** (excluding LLM API costs)

### Cost Reduction Strategies

1. **Auto-scaling**: Scale to zero when idle
2. **Committed use discounts**: 1-year commitment for 30% savings
3. **Preemptible instances**: Use for non-critical workloads
4. **Storage lifecycle**: Archive old sessions after 90 days
5. **CDN optimization**: Aggressive caching for static assets



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Authentication Properties

**Property 1: User registration creates unique accounts**
*For any* valid email and password, registering a new user should create a database record with a unique user ID and securely hashed password (bcrypt with 12 rounds).
**Validates: Requirements 1.2**

**Property 2: Valid login returns valid JWT**
*For any* registered user with correct credentials, logging in should return a JWT token that can be verified and has an expiration time of 24 hours from issuance.
**Validates: Requirements 1.3**

**Property 3: Valid tokens authenticate requests**
*For any* API request with a valid JWT token, the system should successfully authenticate the request and associate it with the correct user ID extracted from the token.
**Validates: Requirements 1.4**

**Property 4: Invalid tokens are rejected**
*For any* API request with a missing, expired, or malformed JWT token, the system should reject the request with HTTP 401 status.
**Validates: Requirements 1.5**

### Blueprint Persistence Properties

**Property 5: Blueprint creation persists with ownership**
*For any* valid blueprint data and authenticated user, creating a blueprint should result in a database record with the correct user_id, version 1, and all required metadata fields.
**Validates: Requirements 2.1, 2.4**

**Property 6: Users only see their own blueprints**
*For any* user requesting their blueprints, the system should return only blueprints where user_id matches the authenticated user, ensuring complete isolation between users.
**Validates: Requirements 2.2**

**Property 7: Deletion prevents access**
*For any* blueprint that has been deleted by its owner, subsequent attempts to access that blueprint should fail, and it should not appear in the owner's blueprint list.
**Validates: Requirements 2.3**

**Property 8: Updates increment version**
*For any* blueprint update operation, the system should increment the version number by exactly 1 and update the updated_at timestamp to the current time.
**Validates: Requirements 2.5**

### Marketplace Properties

**Property 9: Marketplace returns required fields**
*For any* marketplace listing query, all returned blueprints should include name, description, author_name, clone_count, average_rating, and rating_count fields.
**Validates: Requirements 3.2**

**Property 10: Search returns matching results**
*For any* marketplace search query with a keyword, all returned blueprints should have the keyword present in either the name or description field (case-insensitive).
**Validates: Requirements 3.3**

**Property 11: Clone creates independent copy**
*For any* public marketplace blueprint, cloning should create a new blueprint record with a different ID, the same blueprint_data, is_public=false, and user_id set to the cloning user.
**Validates: Requirements 3.4**

**Property 12: Ratings update average correctly**
*For any* sequence of ratings on a blueprint, the average_rating should equal the sum of all ratings divided by the count of ratings.
**Validates: Requirements 3.5**

### Multi-Agent Session Properties

**Property 13: Messages route to correct agent**
*For any* message sent in a session, the system should execute the agent associated with that session's blueprint_id, not any other agent.
**Validates: Requirements 4.3**

**Property 14: Session histories are isolated**
*For any* two different sessions, messages added to one session should never appear in the message history of the other session, even if they belong to the same user.
**Validates: Requirements 4.4**

### Database Concurrency Properties

**Property 15: Concurrent updates maintain consistency**
*For any* two concurrent update operations on the same blueprint, the final state should reflect both updates without data loss, and the version number should be incremented by 2.
**Validates: Requirements 5.4**

### Rate Limiting Properties

**Property 16: Rate limit enforced at threshold**
*For any* user making requests, the 101st request within a 60-second window should be rejected with HTTP 429 status and Retry-After header.
**Validates: Requirements 6.2, 6.4**

### Caching Properties

**Property 17: Cache hit avoids recompilation**
*For any* blueprint that has been executed once, a second execution with the same blueprint_id and version should retrieve the compiled agent from cache without invoking the compiler.
**Validates: Requirements 7.2**

**Property 18: Update invalidates cache**
*For any* blueprint that is updated, any cached compiled agents for that blueprint_id should be removed from the cache, forcing recompilation on next execution.
**Validates: Requirements 7.3**

## Property Reflection

After reviewing all properties, the following observations ensure no redundancy:

- **Properties 1-4** cover distinct aspects of authentication (registration, login, valid auth, invalid auth)
- **Properties 5-8** cover distinct blueprint operations (create, read, delete, update)
- **Properties 9-12** cover distinct marketplace features (display, search, clone, rate)
- **Properties 13-14** cover distinct session behaviors (routing, isolation)
- **Property 15** is unique to concurrency
- **Property 16** combines rate limiting and response headers (both needed)
- **Properties 17-18** cover distinct cache behaviors (hit, invalidation)

No properties are redundant or can be combined without losing validation coverage.



## User API Key Security Architecture

### Threat Model

**Threats to Mitigate:**
1. **Database Breach**: Attacker gains read access to database
2. **Log Exposure**: API keys leaked in application logs
3. **Admin Access**: Platform administrators accessing user keys
4. **Memory Dumps**: Keys exposed in server memory dumps
5. **Backup Exposure**: Keys exposed in database backups
6. **Side-Channel Attacks**: Timing attacks to extract keys

### Encryption Strategy: Envelope Encryption

```
User API Key (plaintext)
    ↓
Encrypted with Data Encryption Key (DEK)
    ↓
Encrypted API Key stored in database
    
DEK (per-user)
    ↓
Encrypted with Key Encryption Key (KEK) from Cloud KMS
    ↓
Encrypted DEK stored in database

KEK
    ↓
Managed by Google Cloud KMS (never leaves KMS)
```

### Database Schema for API Keys

```sql
-- User API keys table
CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'groq', 'gemini'
    key_name VARCHAR(255),  -- User-friendly name
    encrypted_key BYTEA NOT NULL,  -- AES-256-GCM encrypted key
    encrypted_dek BYTEA NOT NULL,  -- DEK encrypted by KMS
    key_last_four CHAR(4) NOT NULL,  -- Last 4 chars for display
    nonce BYTEA NOT NULL,  -- GCM nonce
    kms_key_version VARCHAR(255) NOT NULL,  -- KMS key version used
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, provider, key_name)
);

CREATE INDEX idx_user_api_keys_user_id ON user_api_keys(user_id);
CREATE INDEX idx_user_api_keys_provider ON user_api_keys(user_id, provider);
```

### API Key Encryption Service

```python
# frankenagent/services/api_key_encryption_service.py
from google.cloud import kms
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
import os
import secrets
from typing import Tuple

class APIKeyEncryptionService:
    """
    Secure API key encryption using envelope encryption with Cloud KMS.
    
    Architecture:
    1. Generate unique DEK (Data Encryption Key) per user
    2. Encrypt user's API key with DEK using AES-256-GCM
    3. Encrypt DEK with KEK (Key Encryption Key) from Cloud KMS
    4. Store encrypted API key + encrypted DEK in database
    """
    
    def __init__(self, project_id: str, location: str, keyring: str, key: str):
        self.kms_client = kms.KeyManagementServiceClient()
        self.kms_key_name = self.kms_client.crypto_key_path(
            project_id, location, keyring, key
        )
    
    def encrypt_api_key(self, plaintext_key: str) -> Tuple[bytes, bytes, bytes, str]:
        """
        Encrypt API key using envelope encryption.
        
        Returns:
            (encrypted_key, encrypted_dek, nonce, key_last_four)
        """
        # Generate random DEK (32 bytes for AES-256)
        dek = secrets.token_bytes(32)
        
        # Encrypt API key with DEK using AES-256-GCM
        aesgcm = AESGCM(dek)
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        encrypted_key = aesgcm.encrypt(nonce, plaintext_key.encode(), None)
        
        # Encrypt DEK with KMS
        encrypt_response = self.kms_client.encrypt(
            request={
                "name": self.kms_key_name,
                "plaintext": dek
            }
        )
        encrypted_dek = encrypt_response.ciphertext
        
        # Extract last 4 characters for display
        key_last_four = plaintext_key[-4:] if len(plaintext_key) >= 4 else plaintext_key
        
        # Securely wipe DEK from memory
        del dek
        
        return encrypted_key, encrypted_dek, nonce, key_last_four
    
    def decrypt_api_key(self, encrypted_key: bytes, encrypted_dek: bytes, nonce: bytes) -> str:
        """
        Decrypt API key using envelope encryption.
        
        Returns:
            Plaintext API key (use immediately and discard)
        """
        # Decrypt DEK using KMS
        decrypt_response = self.kms_client.decrypt(
            request={
                "name": self.kms_key_name,
                "ciphertext": encrypted_dek
            }
        )
        dek = decrypt_response.plaintext
        
        # Decrypt API key with DEK
        aesgcm = AESGCM(dek)
        plaintext_key = aesgcm.decrypt(nonce, encrypted_key, None).decode()
        
        # Securely wipe DEK from memory
        del dek
        
        return plaintext_key
    
    def rotate_encryption(self, encrypted_key: bytes, encrypted_dek: bytes, nonce: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Re-encrypt API key with new KMS key version.
        Used for key rotation.
        """
        # Decrypt with old key
        plaintext_key = self.decrypt_api_key(encrypted_key, encrypted_dek, nonce)
        
        # Re-encrypt with current KMS key
        new_encrypted_key, new_encrypted_dek, new_nonce, _ = self.encrypt_api_key(plaintext_key)
        
        # Securely wipe plaintext from memory
        del plaintext_key
        
        return new_encrypted_key, new_encrypted_dek, new_nonce
```

### API Key Management Service

```python
# frankenagent/services/user_api_key_service.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from frankenagent.models import UserAPIKey
from frankenagent.services.api_key_encryption_service import APIKeyEncryptionService
import logging

logger = logging.getLogger(__name__)

class UserAPIKeyService:
    """Service for managing user API keys with secure encryption."""
    
    def __init__(self, encryption_service: APIKeyEncryptionService):
        self.encryption = encryption_service
    
    def add_api_key(
        self,
        db: Session,
        user_id: UUID,
        provider: str,
        plaintext_key: str,
        key_name: Optional[str] = None
    ) -> UserAPIKey:
        """
        Add and encrypt user API key.
        
        SECURITY: Plaintext key is never logged or stored.
        """
        # Validate provider
        valid_providers = ['openai', 'anthropic', 'groq', 'gemini']
        if provider not in valid_providers:
            raise ValueError(f"Invalid provider. Must be one of: {valid_providers}")
        
        # Validate key format (basic check)
        if not plaintext_key or len(plaintext_key) < 10:
            raise ValueError("Invalid API key format")
        
        # Encrypt the key
        encrypted_key, encrypted_dek, nonce, key_last_four = \
            self.encryption.encrypt_api_key(plaintext_key)
        
        # Store in database
        api_key = UserAPIKey(
            user_id=user_id,
            provider=provider,
            key_name=key_name or f"{provider.title()} Key",
            encrypted_key=encrypted_key,
            encrypted_dek=encrypted_dek,
            nonce=nonce,
            key_last_four=key_last_four,
            kms_key_version=self.encryption.kms_key_name
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        logger.info(f"API key added for user {user_id}, provider {provider}")
        
        return api_key
    
    def get_user_api_keys(self, db: Session, user_id: UUID) -> List[dict]:
        """
        Get user's API keys (encrypted, for display only).
        
        Returns masked keys: "sk-...xyz123"
        """
        keys = db.query(UserAPIKey).filter(
            UserAPIKey.user_id == user_id,
            UserAPIKey.is_active == True
        ).all()
        
        return [
            {
                "id": key.id,
                "provider": key.provider,
                "key_name": key.key_name,
                "key_preview": f"***...{key.key_last_four}",
                "created_at": key.created_at,
                "last_used_at": key.last_used_at
            }
            for key in keys
        ]
    
    def get_decrypted_key(
        self,
        db: Session,
        user_id: UUID,
        provider: str
    ) -> Optional[str]:
        """
        Decrypt and return API key for use.
        
        SECURITY: 
        - Key is decrypted in memory only
        - Caller must use immediately and discard
        - Never log or store the returned value
        """
        api_key = db.query(UserAPIKey).filter(
            UserAPIKey.user_id == user_id,
            UserAPIKey.provider == provider,
            UserAPIKey.is_active == True
        ).first()
        
        if not api_key:
            return None
        
        # Decrypt key
        plaintext_key = self.encryption.decrypt_api_key(
            api_key.encrypted_key,
            api_key.encrypted_dek,
            api_key.nonce
        )
        
        # Update last used timestamp
        api_key.last_used_at = datetime.utcnow()
        db.commit()
        
        return plaintext_key
    
    def delete_api_key(self, db: Session, key_id: UUID, user_id: UUID) -> bool:
        """
        Securely delete API key.
        
        SECURITY: Encrypted key and DEK are permanently removed.
        """
        api_key = db.query(UserAPIKey).filter(
            UserAPIKey.id == key_id,
            UserAPIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        # Hard delete (not soft delete) for security
        db.delete(api_key)
        db.commit()
        
        logger.info(f"API key deleted: {key_id} for user {user_id}")
        
        return True
    
    def rotate_all_keys(self, db: Session):
        """
        Rotate encryption for all API keys.
        
        Used when KMS key is rotated.
        """
        keys = db.query(UserAPIKey).filter(UserAPIKey.is_active == True).all()
        
        for key in keys:
            try:
                new_encrypted_key, new_encrypted_dek, new_nonce = \
                    self.encryption.rotate_encryption(
                        key.encrypted_key,
                        key.encrypted_dek,
                        key.nonce
                    )
                
                key.encrypted_key = new_encrypted_key
                key.encrypted_dek = new_encrypted_dek
                key.nonce = new_nonce
                key.kms_key_version = self.encryption.kms_key_name
                
                db.commit()
                logger.info(f"Rotated encryption for key {key.id}")
            except Exception as e:
                logger.error(f"Failed to rotate key {key.id}: {e}")
                db.rollback()
```

### Log Sanitization

```python
# frankenagent/logging_config.py
import re
import logging

class APIKeySanitizingFilter(logging.Filter):
    """
    Filter to automatically redact API keys from logs.
    
    Patterns matched:
    - sk-... (OpenAI)
    - sk-ant-... (Anthropic)
    - gsk_... (Groq)
    - AIza... (Google/Gemini)
    """
    
    API_KEY_PATTERNS = [
        (re.compile(r'sk-[a-zA-Z0-9]{20,}'), 'sk-***REDACTED***'),
        (re.compile(r'sk-ant-[a-zA-Z0-9-]{20,}'), 'sk-ant-***REDACTED***'),
        (re.compile(r'gsk_[a-zA-Z0-9]{20,}'), 'gsk_***REDACTED***'),
        (re.compile(r'AIza[a-zA-Z0-9_-]{20,}'), 'AIza***REDACTED***'),
    ]
    
    def filter(self, record):
        """Sanitize log message before writing."""
        if isinstance(record.msg, str):
            for pattern, replacement in self.API_KEY_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        
        # Also sanitize args
        if record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.API_KEY_PATTERNS:
                        arg = pattern.sub(replacement, arg)
                sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        
        return True

# Apply filter to all loggers
def setup_logging():
    root_logger = logging.getLogger()
    root_logger.addFilter(APIKeySanitizingFilter())
```

### Agent Execution with User Keys

```python
# frankenagent/runtime/executor.py (updated)
class ExecutionOrchestrator:
    def __init__(
        self,
        compiler: AgentCompiler,
        session_manager: SessionManager,
        api_key_service: UserAPIKeyService
    ):
        self.compiler = compiler
        self.session_manager = session_manager
        self.api_key_service = api_key_service
    
    async def execute(
        self,
        blueprint: dict,
        message: str,
        user_id: UUID,
        session_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute agent using user's own API keys.
        
        SECURITY: API keys are decrypted in memory only for the duration
        of the request and never logged.
        """
        # Get provider from blueprint
        provider = blueprint["head"]["provider"]
        
        # Decrypt user's API key
        api_key = self.api_key_service.get_decrypted_key(
            db=self.db,
            user_id=user_id,
            provider=provider
        )
        
        if not api_key:
            raise ValueError(f"No API key configured for provider: {provider}")
        
        try:
            # Inject API key into blueprint (in memory only)
            blueprint_with_key = blueprint.copy()
            blueprint_with_key["head"]["api_key"] = api_key
            
            # Compile and execute
            compiled_agent = self.compiler.compile(blueprint_with_key)
            result = await self._execute_with_guardrails(
                compiled_agent.agent,
                message,
                compiled_agent.guardrails,
                session_id
            )
            
            return result
        finally:
            # Securely wipe API key from memory
            del api_key
            if "api_key" in blueprint_with_key["head"]:
                del blueprint_with_key["head"]["api_key"]
```

### API Endpoints for Key Management

```python
# POST /api/keys (requires auth)
Request:
{
  "provider": "openai",
  "api_key": "sk-...",
  "key_name": "My OpenAI Key"
}

Response: 201 Created
{
  "id": "uuid",
  "provider": "openai",
  "key_name": "My OpenAI Key",
  "key_preview": "***...xyz123",
  "created_at": "2025-01-15T10:00:00Z"
}

# GET /api/keys (requires auth)
Response: 200 OK
{
  "keys": [
    {
      "id": "uuid",
      "provider": "openai",
      "key_name": "My OpenAI Key",
      "key_preview": "***...xyz123",
      "created_at": "2025-01-15T10:00:00Z",
      "last_used_at": "2025-01-15T11:30:00Z"
    }
  ]
}

# DELETE /api/keys/{id} (requires auth)
Response: 204 No Content
```

### Security Checklist

- [x] API keys encrypted at rest (AES-256-GCM)
- [x] Envelope encryption with Cloud KMS
- [x] Per-user encryption keys (DEK)
- [x] Keys decrypted in memory only
- [x] Automatic log sanitization
- [x] No plaintext keys in database
- [x] No plaintext keys in logs
- [x] No plaintext keys in error messages
- [x] Secure deletion (hard delete, not soft)
- [x] Key rotation support
- [x] Last 4 characters only for display
- [x] Audit logging of key access
- [x] KMS key versioning tracked

### Compliance Considerations

**GDPR (Right to be Forgotten):**
- User deletion permanently removes all API keys
- No key backups retained after deletion

**PCI DSS (if applicable):**
- Encryption at rest and in transit
- Key rotation procedures
- Access logging and monitoring

**SOC 2:**
- Encryption controls
- Access controls (user-specific keys)
- Audit trails



### User API Key Security Properties

**Property 19: API keys are encrypted before storage**
*For any* user API key being stored, the system should encrypt it using AES-256-GCM with a user-specific DEK before writing to the database, and the plaintext key should never be stored.
**Validates: Requirements 9.1**

**Property 20: Decrypted keys are never logged**
*For any* operation that decrypts a user API key, the plaintext key should never appear in application logs, error messages, or debug output.
**Validates: Requirements 9.2**

**Property 21: Keys displayed with masking**
*For any* API key display operation, the system should show only the last 4 characters with the rest masked (e.g., "***...xyz123"), never the full plaintext key.
**Validates: Requirements 9.4**

**Property 22: Deleted keys are permanently removed**
*For any* API key deletion operation, both the encrypted key and encrypted DEK should be permanently removed from the database with no recovery possible.
**Validates: Requirements 9.5**

**Property 23: User deletion removes all keys**
*For any* user account deletion, all associated API keys and encryption keys should be permanently deleted from the database.
**Validates: Requirements 9.7**

