"""Authentication service with JWT and bcrypt."""

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID


class AuthService:
    """
    Authentication service for user management.
    
    Provides secure password hashing with bcrypt and JWT token generation
    for stateless authentication.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize authentication service.
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with salt rounds=12.
        
        Args:
            password: Plaintext password
            
        Returns:
            Hashed password as string
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plaintext password to verify
            password_hash: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_access_token(self, user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token with 24-hour expiration.
        
        Args:
            user_id: User UUID
            expires_delta: Optional custom expiration delta (default: 24 hours)
            
        Returns:
            JWT token as string
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[UUID]:
        """
        Verify JWT token and extract user_id.
        
        Args:
            token: JWT token string
            
        Returns:
            User UUID if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id_str = payload.get("sub")
            if user_id_str is None:
                return None
            return UUID(user_id_str)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
            return None
    
    def create_password_reset_token(self, user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT token for password reset with 1-hour expiration.
        
        Args:
            user_id: User UUID
            expires_delta: Optional custom expiration delta (default: 1 hour)
            
        Returns:
            JWT token as string
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=1)
        
        expire = datetime.utcnow() + expires_delta
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "password_reset"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_password_reset_token(self, token: str) -> Optional[UUID]:
        """
        Verify password reset token and extract user_id.
        
        Args:
            token: JWT token string
            
        Returns:
            User UUID if token is valid and is a password reset token, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify it's a password reset token
            if payload.get("type") != "password_reset":
                return None
            
            user_id_str = payload.get("sub")
            if user_id_str is None:
                return None
            
            return UUID(user_id_str)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
            return None
