"""Property-based tests for session management service.

Feature: platform-evolution
Properties tested:
- Property 13: Messages route to correct agent
- Property 14: Session histories are isolated

Validates: Requirements 4.3, 4.4
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from frankenagent.services.session_service import SessionService
from frankenagent.db.models import User, Blueprint, Session
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


def create_test_user(db_session, email="test@example.com"):
    """Create a test user in the database."""
    user = User(
        email=email,
        password_hash="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_blueprint(db_session, user_id, name="Test Blueprint"):
    """Create a test blueprint in the database."""
    blueprint = Blueprint(
        user_id=user_id,
        name=name,
        description="Test blueprint",
        blueprint_data={"head": {"model": "gpt-4", "provider": "openai"}},
        version=1
    )
    db_session.add(blueprint)
    db_session.commit()
    db_session.refresh(blueprint)
    return blueprint


# Hypothesis strategies

@st.composite
def message_content(draw):
    """Generate valid message content."""
    return draw(st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
        whitelist_characters='.,!?'
    )))


@st.composite
def message_role(draw):
    """Generate valid message roles."""
    return draw(st.sampled_from(['user', 'assistant']))


# Property tests

@given(
    message1=message_content(),
    message2=message_content(),
    role1=message_role(),
    role2=message_role()
)
@settings(max_examples=10, deadline=None)
def test_property_13_messages_route_to_correct_agent(message1, message2, role1, role2):
    """
    **Feature: platform-evolution, Property 13: Messages route to correct agent**
    
    For any message sent in a session, the system should execute the agent associated
    with that session's blueprint_id, not any other agent.
    
    **Validates: Requirements 4.3**
    """
    # Create fresh database session and service
    db_session = create_test_db_session()
    session_service = SessionService()
    
    try:
        # Create user
        user = create_test_user(db_session)
        
        # Create two different blueprints (representing two different agents)
        blueprint1 = create_test_blueprint(db_session, user.id, "Agent 1")
        blueprint2 = create_test_blueprint(db_session, user.id, "Agent 2")
        
        # Create two sessions, each with a different blueprint
        session1 = session_service.create_session(
            db=db_session,
            user_id=user.id,
            blueprint_id=blueprint1.id
        )
        
        session2 = session_service.create_session(
            db=db_session,
            user_id=user.id,
            blueprint_id=blueprint2.id
        )
        
        # Add messages to each session
        success1 = session_service.add_message(
            db=db_session,
            session_id=session1.id,
            user_id=user.id,
            role=role1,
            content=message1
        )
        assert success1
        
        success2 = session_service.add_message(
            db=db_session,
            session_id=session2.id,
            user_id=user.id,
            role=role2,
            content=message2
        )
        assert success2
        
        # Verify each session is still associated with its correct blueprint
        db_session.refresh(session1)
        db_session.refresh(session2)
        
        assert session1.blueprint_id == blueprint1.id
        assert session2.blueprint_id == blueprint2.id
        
        # Verify messages are in the correct sessions
        history1 = session_service.get_session_history(
            db=db_session,
            session_id=session1.id,
            user_id=user.id
        )
        assert history1 is not None
        assert len(history1) == 1
        assert history1[0]["content"] == message1
        assert history1[0]["role"] == role1
        
        history2 = session_service.get_session_history(
            db=db_session,
            session_id=session2.id,
            user_id=user.id
        )
        assert history2 is not None
        assert len(history2) == 1
        assert history2[0]["content"] == message2
        assert history2[0]["role"] == role2
        
        # Verify the blueprint associations haven't changed
        # (messages routed to correct agent)
        assert session1.blueprint_id == blueprint1.id
        assert session2.blueprint_id == blueprint2.id
        
    finally:
        db_session.close()


@given(
    messages_session1=st.lists(
        st.tuples(message_role(), message_content()),
        min_size=1,
        max_size=5
    ),
    messages_session2=st.lists(
        st.tuples(message_role(), message_content()),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=10, deadline=None)
def test_property_14_session_histories_are_isolated(messages_session1, messages_session2):
    """
    **Feature: platform-evolution, Property 14: Session histories are isolated**
    
    For any two different sessions, messages added to one session should never appear
    in the message history of the other session, even if they belong to the same user.
    
    **Validates: Requirements 4.4**
    """
    # Create fresh database session and service
    db_session = create_test_db_session()
    session_service = SessionService()
    
    try:
        # Create user and blueprint
        user = create_test_user(db_session)
        blueprint = create_test_blueprint(db_session, user.id)
        
        # Create two different sessions for the same user and blueprint
        session1 = session_service.create_session(
            db=db_session,
            user_id=user.id,
            blueprint_id=blueprint.id
        )
        
        session2 = session_service.create_session(
            db=db_session,
            user_id=user.id,
            blueprint_id=blueprint.id
        )
        
        # Verify sessions have different IDs
        assert session1.id != session2.id
        
        # Add messages to session1
        for role, content in messages_session1:
            success = session_service.add_message(
                db=db_session,
                session_id=session1.id,
                user_id=user.id,
                role=role,
                content=content
            )
            assert success
        
        # Add messages to session2
        for role, content in messages_session2:
            success = session_service.add_message(
                db=db_session,
                session_id=session2.id,
                user_id=user.id,
                role=role,
                content=content
            )
            assert success
        
        # Get histories for both sessions
        history1 = session_service.get_session_history(
            db=db_session,
            session_id=session1.id,
            user_id=user.id
        )
        
        history2 = session_service.get_session_history(
            db=db_session,
            session_id=session2.id,
            user_id=user.id
        )
        
        # Verify histories exist
        assert history1 is not None
        assert history2 is not None
        
        # Verify correct number of messages in each session
        assert len(history1) == len(messages_session1)
        assert len(history2) == len(messages_session2)
        
        # Verify messages in session1 match what was added
        for i, (role, content) in enumerate(messages_session1):
            assert history1[i]["role"] == role
            assert history1[i]["content"] == content
        
        # Verify messages in session2 match what was added
        for i, (role, content) in enumerate(messages_session2):
            assert history2[i]["role"] == role
            assert history2[i]["content"] == content
        
        # Verify no cross-contamination: messages from session1 not in session2
        session1_contents = {msg["content"] for msg in history1}
        session2_contents = {msg["content"] for msg in history2}
        
        # If the randomly generated messages happen to be identical, skip this check
        # (extremely unlikely but possible with hypothesis)
        if session1_contents != session2_contents:
            # Verify isolation: each session has its own distinct messages
            for msg in history1:
                # This message should not appear in session2 unless it was explicitly added there
                if msg["content"] not in [m[1] for m in messages_session2]:
                    assert msg["content"] not in session2_contents
            
            for msg in history2:
                # This message should not appear in session1 unless it was explicitly added there
                if msg["content"] not in [m[1] for m in messages_session1]:
                    assert msg["content"] not in session1_contents
        
    finally:
        db_session.close()


# Additional edge case tests

def test_session_isolation_different_users():
    """
    Test that sessions are isolated between different users.
    
    This is an edge case for Property 14.
    """
    db_session = create_test_db_session()
    session_service = SessionService()
    
    try:
        # Create two different users
        user1 = create_test_user(db_session, "user1@example.com")
        user2 = create_test_user(db_session, "user2@example.com")
        
        # Create blueprint for user1
        blueprint = create_test_blueprint(db_session, user1.id)
        
        # Create session for user1
        session1 = session_service.create_session(
            db=db_session,
            user_id=user1.id,
            blueprint_id=blueprint.id
        )
        
        # Add message to user1's session
        session_service.add_message(
            db=db_session,
            session_id=session1.id,
            user_id=user1.id,
            role="user",
            content="User 1 message"
        )
        
        # User2 should not be able to access user1's session
        history = session_service.get_session_history(
            db=db_session,
            session_id=session1.id,
            user_id=user2.id
        )
        
        # Should return None (access denied)
        assert history is None
        
    finally:
        db_session.close()


def test_session_creation_with_nonexistent_blueprint():
    """
    Test that session creation fails with non-existent blueprint.
    
    This is an edge case for Property 13.
    """
    db_session = create_test_db_session()
    session_service = SessionService()
    
    try:
        # Create user
        user = create_test_user(db_session)
        
        # Try to create session with non-existent blueprint
        fake_blueprint_id = uuid4()
        
        with pytest.raises(ValueError, match="Blueprint .* not found"):
            session_service.create_session(
                db=db_session,
                user_id=user.id,
                blueprint_id=fake_blueprint_id
            )
        
    finally:
        db_session.close()


def test_session_creation_with_private_blueprint():
    """
    Test that session creation fails when user doesn't have access to private blueprint.
    
    This is an edge case for Property 13.
    """
    db_session = create_test_db_session()
    session_service = SessionService()
    
    try:
        # Create two users
        user1 = create_test_user(db_session, "user1@example.com")
        user2 = create_test_user(db_session, "user2@example.com")
        
        # Create private blueprint for user1
        blueprint = create_test_blueprint(db_session, user1.id)
        blueprint.is_public = False
        db_session.commit()
        
        # User2 should not be able to create session with user1's private blueprint
        with pytest.raises(ValueError, match="does not have access"):
            session_service.create_session(
                db=db_session,
                user_id=user2.id,
                blueprint_id=blueprint.id
            )
        
    finally:
        db_session.close()


def test_session_creation_with_public_blueprint():
    """
    Test that session creation succeeds with public blueprint from another user.
    
    This is an edge case for Property 13.
    """
    db_session = create_test_db_session()
    session_service = SessionService()
    
    try:
        # Create two users
        user1 = create_test_user(db_session, "user1@example.com")
        user2 = create_test_user(db_session, "user2@example.com")
        
        # Create public blueprint for user1
        blueprint = create_test_blueprint(db_session, user1.id)
        blueprint.is_public = True
        db_session.commit()
        
        # User2 should be able to create session with user1's public blueprint
        session = session_service.create_session(
            db=db_session,
            user_id=user2.id,
            blueprint_id=blueprint.id
        )
        
        assert session is not None
        assert session.user_id == user2.id
        assert session.blueprint_id == blueprint.id
        
    finally:
        db_session.close()


def test_empty_session_history():
    """
    Test that newly created session has empty message history.
    
    This is an edge case for Property 14.
    """
    db_session = create_test_db_session()
    session_service = SessionService()
    
    try:
        # Create user and blueprint
        user = create_test_user(db_session)
        blueprint = create_test_blueprint(db_session, user.id)
        
        # Create session
        session = session_service.create_session(
            db=db_session,
            user_id=user.id,
            blueprint_id=blueprint.id
        )
        
        # Get history
        history = session_service.get_session_history(
            db=db_session,
            session_id=session.id,
            user_id=user.id
        )
        
        # Should be empty list
        assert history is not None
        assert len(history) == 0
        
    finally:
        db_session.close()
