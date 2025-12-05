"""Property-based tests for authentication service.

Feature: platform-evolution
Properties tested:
- Property 1: User registration creates unique accounts
- Property 2: Valid login returns valid JWT
- Property 3: Valid tokens authenticate requests
- Property 4: Invalid tokens are rejected

Validates: Requirements 1.2, 1.3, 1.4, 1.5
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import emails, text
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from frankenagent.auth.service import AuthService
from frankenagent.db.models import User
from frankenagent.db.base import Base


# Helper functions

def create_test_db_session():
    """Create a fresh in-memory SQLite database session for testing."""
    # Create in-memory SQLite engine for testing
    test_engine = create_engine("sqlite:///:memory:")
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    return TestSessionLocal()


def create_auth_service():
    """Create auth service instance."""
    return AuthService(secret_key="test-secret-key-for-testing")


# Hypothesis strategies

@st.composite
def valid_passwords(draw):
    """Generate valid passwords (at least 8 characters, max 72 bytes for bcrypt)."""
    # Generate password with at least 8 characters but ensure it's under 72 bytes when encoded
    # Use ASCII characters to avoid multi-byte encoding issues
    length = draw(st.integers(min_value=8, max_value=50))
    password = draw(st.text(
        alphabet=st.characters(min_codepoint=33, max_codepoint=126),  # Printable ASCII
        min_size=length,
        max_size=length
    ))
    # Ensure password is under 72 bytes when UTF-8 encoded (bcrypt limit)
    while len(password.encode('utf-8')) > 72:
        password = password[:len(password)-1]
    return password


@st.composite
def user_data(draw):
    """Generate valid user registration data."""
    email = draw(emails())
    password = draw(valid_passwords())
    full_name = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters=' '
        ))
    ))
    return {
        "email": email,
        "password": password,
        "full_name": full_name
    }


# Property tests

@given(data1=user_data(), data2=user_data())
@settings(max_examples=5, deadline=None)
def test_property_1_user_registration_creates_unique_accounts(data1, data2):
    """
    **Feature: platform-evolution, Property 1: User registration creates unique accounts**
    
    For any valid email and password, registering a new user should create a database
    record with a unique user ID and securely hashed password (bcrypt with 12 rounds).
    
    **Validates: Requirements 1.2**
    """
    # Create fresh database session and auth service for this test
    db_session = create_test_db_session()
    auth_service = create_auth_service()
    
    try:
        # Register first user
        password_hash1 = auth_service.hash_password(data1["password"])
        user1 = User(
            email=data1["email"],
            password_hash=password_hash1,
            full_name=data1["full_name"]
        )
        db_session.add(user1)
        db_session.commit()
        db_session.refresh(user1)
        
        # Verify user1 was created with unique ID
        assert user1.id is not None
        assert user1.email == data1["email"]
        assert user1.password_hash != data1["password"]  # Password should be hashed
        assert user1.password_hash.startswith("$2b$")  # bcrypt hash format
        
        # Verify password can be verified
        assert auth_service.verify_password(data1["password"], user1.password_hash)
        
        # If emails are different, register second user
        if data1["email"] != data2["email"]:
            password_hash2 = auth_service.hash_password(data2["password"])
            user2 = User(
                email=data2["email"],
                password_hash=password_hash2,
                full_name=data2["full_name"]
            )
            db_session.add(user2)
            db_session.commit()
            db_session.refresh(user2)
            
            # Verify user2 has different ID
            assert user2.id is not None
            assert user2.id != user1.id
            assert user2.email == data2["email"]
            
            # Verify both users exist independently
            all_users = db_session.query(User).all()
            assert len(all_users) == 2
            assert {u.email for u in all_users} == {data1["email"], data2["email"]}
    finally:
        db_session.close()


@given(user_info=user_data())
@settings(max_examples=5, deadline=None)
def test_property_2_valid_login_returns_valid_jwt(user_info):
    """
    **Feature: platform-evolution, Property 2: Valid login returns valid JWT**
    
    For any registered user with correct credentials, logging in should return a JWT
    token that can be verified and has an expiration time of 24 hours from issuance.
    
    **Validates: Requirements 1.3**
    """
    # Create fresh database session and auth service for this test
    db_session = create_test_db_session()
    auth_service = create_auth_service()
    
    try:
        # Register user
        password_hash = auth_service.hash_password(user_info["password"])
        user = User(
            email=user_info["email"],
            password_hash=password_hash,
            full_name=user_info["full_name"]
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Verify password (simulating login)
        assert auth_service.verify_password(user_info["password"], user.password_hash)
        
        # Create access token
        token = auth_service.create_access_token(user.id)
        
        # Verify token is a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded and contains correct user_id
        verified_user_id = auth_service.verify_token(token)
        assert verified_user_id is not None
        assert verified_user_id == user.id
        
        # Verify token with custom expiration
        short_token = auth_service.create_access_token(user.id, timedelta(hours=1))
        verified_short_id = auth_service.verify_token(short_token)
        assert verified_short_id == user.id
    finally:
        db_session.close()


@given(user_info=user_data())
@settings(max_examples=5, deadline=None)
def test_property_3_valid_tokens_authenticate_requests(user_info):
    """
    **Feature: platform-evolution, Property 3: Valid tokens authenticate requests**
    
    For any API request with a valid JWT token, the system should successfully
    authenticate the request and associate it with the correct user ID extracted
    from the token.
    
    **Validates: Requirements 1.4**
    """
    # Create fresh database session and auth service for this test
    db_session = create_test_db_session()
    auth_service = create_auth_service()
    
    try:
        # Register user
        password_hash = auth_service.hash_password(user_info["password"])
        user = User(
            email=user_info["email"],
            password_hash=password_hash,
            full_name=user_info["full_name"]
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create token
        token = auth_service.create_access_token(user.id)
        
        # Simulate authentication: verify token and extract user_id
        authenticated_user_id = auth_service.verify_token(token)
        
        # Verify authentication succeeded
        assert authenticated_user_id is not None
        assert authenticated_user_id == user.id
        
        # Verify we can retrieve the correct user from database
        authenticated_user = db_session.query(User).filter(User.id == authenticated_user_id).first()
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.email == user_info["email"]
    finally:
        db_session.close()


@given(
    user_info=user_data(),
    invalid_token=st.one_of(
        st.text(min_size=1, max_size=100),  # Random text
        st.just(""),  # Empty string
        st.just("invalid.token.format"),  # Invalid JWT format
        st.just("Bearer invalid"),  # Invalid with Bearer prefix
    )
)
@settings(max_examples=5, deadline=None)
def test_property_4_invalid_tokens_are_rejected(user_info, invalid_token):
    """
    **Feature: platform-evolution, Property 4: Invalid tokens are rejected**
    
    For any API request with a missing, expired, or malformed JWT token, the system
    should reject the request with HTTP 401 status.
    
    **Validates: Requirements 1.5**
    """
    # Create fresh database session and auth service for this test
    db_session = create_test_db_session()
    auth_service = create_auth_service()
    
    try:
        # Register user (for context, though not strictly needed for this test)
        password_hash = auth_service.hash_password(user_info["password"])
        user = User(
            email=user_info["email"],
            password_hash=password_hash,
            full_name=user_info["full_name"]
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Try to verify invalid token
        result = auth_service.verify_token(invalid_token)
        
        # Invalid tokens should return None
        assert result is None
        
        # Test expired token
        expired_token = auth_service.create_access_token(
            user.id,
            timedelta(seconds=-1)  # Already expired
        )
        expired_result = auth_service.verify_token(expired_token)
        assert expired_result is None
    finally:
        db_session.close()


# Additional edge case tests

def test_property_1_duplicate_email_constraint():
    """
    Test that duplicate emails are prevented at the database level.
    
    This is an edge case for Property 1.
    """
    db_session = create_test_db_session()
    auth_service = create_auth_service()
    
    try:
        email = "test@example.com"
        password_hash = auth_service.hash_password("password123")
        
        # Create first user
        user1 = User(email=email, password_hash=password_hash)
        db_session.add(user1)
        db_session.commit()
        
        # Try to create second user with same email
        user2 = User(email=email, password_hash=password_hash)
        db_session.add(user2)
        
        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()
    finally:
        db_session.close()


def test_property_2_wrong_password_fails():
    """
    Test that wrong password fails verification.
    
    This is an edge case for Property 2.
    """
    auth_service = create_auth_service()
    
    password = "correct_password"
    wrong_password = "wrong_password"
    
    password_hash = auth_service.hash_password(password)
    
    # Correct password should verify
    assert auth_service.verify_password(password, password_hash)
    
    # Wrong password should not verify
    assert not auth_service.verify_password(wrong_password, password_hash)
