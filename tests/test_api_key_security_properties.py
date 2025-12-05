"""Property-based tests for API key security.

Feature: platform-evolution
Properties tested:
- Property 19: API keys are encrypted before storage
- Property 20: Decrypted keys are never logged
- Property 21: Keys displayed with masking
- Property 22: Deleted keys are permanently removed
- Property 23: User deletion removes all keys

Validates: Requirements 9.1, 9.2, 9.4, 9.5, 9.7
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from uuid import uuid4
import logging
import io

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from frankenagent.services.api_key_encryption_service import APIKeyEncryptionService
from frankenagent.services.user_api_key_service import UserAPIKeyService
from frankenagent.db.models import User, UserAPIKey
from frankenagent.db.base import Base
from frankenagent.logging_config import APIKeySanitizingFilter


# Helper functions

def create_test_db_session():
    """Create a fresh in-memory SQLite database session for testing."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    return TestSessionLocal()


def create_mock_encryption_service():
    """
    Create a mock encryption service for testing.
    
    Note: This uses a simplified encryption for testing purposes.
    In production, this would use actual Cloud KMS.
    """
    from unittest.mock import Mock
    
    class MockKMSClient:
        def crypto_key_path(self, project, location, keyring, key):
            return f"projects/{project}/locations/{location}/keyRings/{keyring}/cryptoKeys/{key}"
        
        def encrypt(self, request):
            class Response:
                def __init__(self, plaintext):
                    # Simple XOR encryption for testing
                    self.ciphertext = bytes([b ^ 0x42 for b in plaintext])
            return Response(request["plaintext"])
        
        def decrypt(self, request):
            class Response:
                def __init__(self, ciphertext):
                    # Simple XOR decryption for testing
                    self.plaintext = bytes([b ^ 0x42 for b in ciphertext])
            return Response(request["ciphertext"])
    
    # Create service without initializing real KMS client
    service = object.__new__(APIKeyEncryptionService)
    service.kms_client = MockKMSClient()
    service.kms_key_name = service.kms_client.crypto_key_path(
        "test-project", "us-central1", "test-keyring", "test-key"
    )
    return service


def create_api_key_service():
    """Create API key service with mock encryption."""
    encryption_service = create_mock_encryption_service()
    return UserAPIKeyService(encryption_service)


# Hypothesis strategies

@st.composite
def api_key_data(draw):
    """Generate valid API key data."""
    provider = draw(st.sampled_from(['openai', 'anthropic', 'groq', 'gemini']))
    
    # Generate realistic API key formats using only ASCII alphanumeric characters
    # This matches the regex patterns in the sanitization filter
    if provider == 'openai':
        key = 'sk-' + draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=40,
            max_size=50
        ))
    elif provider == 'anthropic':
        key = 'sk-ant-' + draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
            min_size=40,
            max_size=50
        ))
    elif provider == 'groq':
        key = 'gsk_' + draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=40,
            max_size=50
        ))
    else:  # gemini
        key = 'AIza' + draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-',
            min_size=30,
            max_size=40
        ))
    
    key_name = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ')
    ))
    
    return {
        "provider": provider,
        "api_key": key,
        "key_name": key_name
    }


# Property tests

@given(key_data=api_key_data())
@settings(max_examples=10, deadline=None)
def test_property_19_api_keys_are_encrypted_before_storage(key_data):
    """
    **Feature: platform-evolution, Property 19: API keys are encrypted before storage**
    
    For any user API key being stored, the system should encrypt it using AES-256-GCM
    with a user-specific DEK before writing to the database, and the plaintext key
    should never be stored.
    
    **Validates: Requirements 9.1**
    """
    db_session = create_test_db_session()
    api_key_service = create_api_key_service()
    
    try:
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Add API key
        stored_key = api_key_service.add_api_key(
            db=db_session,
            user_id=user.id,
            provider=key_data["provider"],
            plaintext_key=key_data["api_key"],
            key_name=key_data["key_name"]
        )
        
        # Verify key was stored
        assert stored_key.id is not None
        assert stored_key.user_id == user.id
        assert stored_key.provider == key_data["provider"]
        
        # Verify plaintext key is NOT stored
        assert stored_key.encrypted_key != key_data["api_key"].encode()
        assert stored_key.encrypted_key != key_data["api_key"]
        
        # Verify encrypted_key is bytes
        assert isinstance(stored_key.encrypted_key, bytes)
        assert len(stored_key.encrypted_key) > 0
        
        # Verify encrypted_dek is bytes
        assert isinstance(stored_key.encrypted_dek, bytes)
        assert len(stored_key.encrypted_dek) > 0
        
        # Verify nonce is bytes
        assert isinstance(stored_key.nonce, bytes)
        assert len(stored_key.nonce) == 12  # GCM nonce is 96 bits = 12 bytes
        
        # Verify only last 4 characters are stored for display
        assert stored_key.key_last_four == key_data["api_key"][-4:]
        
        # Verify we can decrypt and get original key back
        decrypted_key = api_key_service.get_decrypted_key(
            db=db_session,
            user_id=user.id,
            provider=key_data["provider"]
        )
        assert decrypted_key == key_data["api_key"]
        
    finally:
        db_session.close()


@given(key_data=api_key_data())
@settings(max_examples=10, deadline=None)
def test_property_20_decrypted_keys_are_never_logged(key_data):
    """
    **Feature: platform-evolution, Property 20: Decrypted keys are never logged**
    
    For any operation that decrypts a user API key, the plaintext key should never
    appear in application logs, error messages, or debug output.
    
    **Validates: Requirements 9.2**
    """
    db_session = create_test_db_session()
    api_key_service = create_api_key_service()
    
    # Set up log capture
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    
    # Add sanitization filter
    handler.addFilter(APIKeySanitizingFilter())
    
    # Create logger and add handler
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    try:
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Add API key
        api_key_service.add_api_key(
            db=db_session,
            user_id=user.id,
            provider=key_data["provider"],
            plaintext_key=key_data["api_key"],
            key_name=key_data["key_name"]
        )
        
        # Decrypt key
        decrypted_key = api_key_service.get_decrypted_key(
            db=db_session,
            user_id=user.id,
            provider=key_data["provider"]
        )
        
        # Try to log the key (this should be sanitized)
        logger.info(f"API key: {decrypted_key}")
        logger.debug(f"Decrypted key value: {decrypted_key}")
        logger.error(f"Error with key {decrypted_key}")
        
        # Get log output
        log_output = log_stream.getvalue()
        
        # Verify plaintext key is NOT in logs
        assert key_data["api_key"] not in log_output
        
        # Verify redacted placeholder IS in logs
        assert "REDACTED" in log_output
        
    finally:
        logger.removeHandler(handler)
        db_session.close()


@given(key_data=api_key_data())
@settings(max_examples=10, deadline=None)
def test_property_21_keys_displayed_with_masking(key_data):
    """
    **Feature: platform-evolution, Property 21: Keys displayed with masking**
    
    For any API key display operation, the system should show only the last 4
    characters with the rest masked (e.g., "***...xyz123"), never the full
    plaintext key.
    
    **Validates: Requirements 9.4**
    """
    db_session = create_test_db_session()
    api_key_service = create_api_key_service()
    
    try:
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Add API key
        api_key_service.add_api_key(
            db=db_session,
            user_id=user.id,
            provider=key_data["provider"],
            plaintext_key=key_data["api_key"],
            key_name=key_data["key_name"]
        )
        
        # Get user's API keys (for display)
        keys = api_key_service.get_user_api_keys(db=db_session, user_id=user.id)
        
        # Verify we got the key
        assert len(keys) == 1
        key_info = keys[0]
        
        # Verify key_preview is masked
        assert "key_preview" in key_info
        preview = key_info["key_preview"]
        
        # Verify format is "***...XXXX"
        assert preview.startswith("***...")
        assert preview.endswith(key_data["api_key"][-4:])
        
        # Verify full plaintext key is NOT in preview
        assert key_data["api_key"] != preview
        
        # Verify only last 4 characters are visible
        visible_part = preview.split("...")[-1]
        assert visible_part == key_data["api_key"][-4:]
        
    finally:
        db_session.close()


@given(key_data=api_key_data())
@settings(max_examples=10, deadline=None)
def test_property_22_deleted_keys_are_permanently_removed(key_data):
    """
    **Feature: platform-evolution, Property 22: Deleted keys are permanently removed**
    
    For any API key deletion operation, both the encrypted key and encrypted DEK
    should be permanently removed from the database with no recovery possible.
    
    **Validates: Requirements 9.5**
    """
    db_session = create_test_db_session()
    api_key_service = create_api_key_service()
    
    try:
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Add API key
        stored_key = api_key_service.add_api_key(
            db=db_session,
            user_id=user.id,
            provider=key_data["provider"],
            plaintext_key=key_data["api_key"],
            key_name=key_data["key_name"]
        )
        
        key_id = stored_key.id
        
        # Verify key exists
        key_before = db_session.query(UserAPIKey).filter(UserAPIKey.id == key_id).first()
        assert key_before is not None
        
        # Delete the key
        success = api_key_service.delete_api_key(
            db=db_session,
            key_id=key_id,
            user_id=user.id
        )
        assert success is True
        
        # Verify key is permanently removed (hard delete)
        key_after = db_session.query(UserAPIKey).filter(UserAPIKey.id == key_id).first()
        assert key_after is None
        
        # Verify we cannot retrieve the key
        decrypted_key = api_key_service.get_decrypted_key(
            db=db_session,
            user_id=user.id,
            provider=key_data["provider"]
        )
        assert decrypted_key is None
        
        # Verify key is not in user's key list
        keys = api_key_service.get_user_api_keys(db=db_session, user_id=user.id)
        assert len(keys) == 0
        
    finally:
        db_session.close()


@given(key_data1=api_key_data(), key_data2=api_key_data())
@settings(max_examples=10, deadline=None)
def test_property_23_user_deletion_removes_all_keys(key_data1, key_data2):
    """
    **Feature: platform-evolution, Property 23: User deletion removes all keys**
    
    For any user account deletion, all associated API keys and encryption keys
    should be permanently deleted from the database.
    
    **Validates: Requirements 9.7**
    """
    # Ensure different providers for the two keys
    assume(key_data1["provider"] != key_data2["provider"])
    
    db_session = create_test_db_session()
    api_key_service = create_api_key_service()
    
    try:
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Add multiple API keys
        key1 = api_key_service.add_api_key(
            db=db_session,
            user_id=user.id,
            provider=key_data1["provider"],
            plaintext_key=key_data1["api_key"],
            key_name=key_data1["key_name"]
        )
        
        key2 = api_key_service.add_api_key(
            db=db_session,
            user_id=user.id,
            provider=key_data2["provider"],
            plaintext_key=key_data2["api_key"],
            key_name=key_data2["key_name"]
        )
        
        # Verify both keys exist
        keys_before = db_session.query(UserAPIKey).filter(
            UserAPIKey.user_id == user.id
        ).all()
        assert len(keys_before) == 2
        
        # Delete user (cascade should delete all keys)
        db_session.delete(user)
        db_session.commit()
        
        # Verify all keys are deleted
        keys_after = db_session.query(UserAPIKey).filter(
            UserAPIKey.id.in_([key1.id, key2.id])
        ).all()
        assert len(keys_after) == 0
        
        # Verify user is deleted
        user_after = db_session.query(User).filter(User.id == user.id).first()
        assert user_after is None
        
    finally:
        db_session.close()


# Edge case tests

def test_property_19_edge_case_empty_key_rejected():
    """
    Test that empty or too-short API keys are rejected.
    
    This is an edge case for Property 19.
    """
    db_session = create_test_db_session()
    api_key_service = create_api_key_service()
    
    try:
        user = User(email="test@example.com", password_hash="hashed")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Try to add empty key
        with pytest.raises(ValueError):
            api_key_service.add_api_key(
                db=db_session,
                user_id=user.id,
                provider="openai",
                plaintext_key="",
                key_name="Test"
            )
        
        # Try to add too-short key
        with pytest.raises(ValueError):
            api_key_service.add_api_key(
                db=db_session,
                user_id=user.id,
                provider="openai",
                plaintext_key="short",
                key_name="Test"
            )
    finally:
        db_session.close()


def test_property_19_edge_case_invalid_provider_rejected():
    """
    Test that invalid providers are rejected.
    
    This is an edge case for Property 19.
    """
    db_session = create_test_db_session()
    api_key_service = create_api_key_service()
    
    try:
        user = User(email="test@example.com", password_hash="hashed")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Try to add key with invalid provider
        with pytest.raises(ValueError):
            api_key_service.add_api_key(
                db=db_session,
                user_id=user.id,
                provider="invalid_provider",
                plaintext_key="sk-1234567890abcdefghij",
                key_name="Test"
            )
    finally:
        db_session.close()


def test_property_22_edge_case_delete_nonexistent_key():
    """
    Test that deleting a non-existent key returns False.
    
    This is an edge case for Property 22.
    """
    db_session = create_test_db_session()
    api_key_service = create_api_key_service()
    
    try:
        user = User(email="test@example.com", password_hash="hashed")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Try to delete non-existent key
        success = api_key_service.delete_api_key(
            db=db_session,
            key_id=uuid4(),
            user_id=user.id
        )
        assert success is False
    finally:
        db_session.close()
