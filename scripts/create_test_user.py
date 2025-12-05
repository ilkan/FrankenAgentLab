#!/usr/bin/env python3
"""Create a test user for development."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frankenagent.db.database import SessionLocal
from frankenagent.db.models import User
from frankenagent.auth.service import AuthService

def create_test_user():
    """Create a test user account."""
    
    # Test user credentials
    email = "test@example.com"
    password = "testpassword123"
    full_name = "Test User"
    
    # Initialize auth service
    jwt_secret = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    auth_service = AuthService(secret_key=jwt_secret)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"✓ Test user already exists: {email}")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            return
        
        # Hash password
        password_hash = auth_service.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("✓ Test user created successfully!")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"  User ID: {user.id}")
        
    except Exception as e:
        print(f"✗ Error creating test user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
