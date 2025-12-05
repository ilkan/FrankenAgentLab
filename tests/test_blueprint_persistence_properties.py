"""Property-based tests for blueprint persistence.

These tests validate the correctness properties for blueprint CRUD operations
using Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from uuid import uuid4

from frankenagent.services.blueprint_service import BlueprintService
from frankenagent.compiler.validator import BlueprintValidator
from frankenagent.db.models import User, Blueprint
from frankenagent.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


# Helper functions for test setup

def create_db_session():
    """Create a fresh in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal(), engine


def create_test_user(db_session, email="test@example.com"):
    """Create a test user."""
    user = User(
        id=uuid4(),
        email=email,
        password_hash="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# Hypothesis strategies for generating test data

@st.composite
def valid_blueprint_data(draw):
    """Generate valid blueprint data."""
    provider = draw(st.sampled_from(["openai", "anthropic"]))
    
    if provider == "openai":
        model = draw(st.sampled_from(["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]))
    else:
        model = draw(st.sampled_from([
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229"
        ]))
    
    return {
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))),
        "head": {
            "provider": provider,
            "model": model,
            "system_prompt": draw(st.text(min_size=1, max_size=500)),
            "temperature": draw(st.floats(min_value=0.0, max_value=2.0))
        },
        "legs": {
            "execution_mode": draw(st.sampled_from(["single_agent", "workflow", "team"]))
        },
        "arms": []
    }


@st.composite
def blueprint_name(draw):
    """Generate valid blueprint name."""
    return draw(st.text(min_size=1, max_size=255, alphabet=st.characters(
        blacklist_categories=('Cs',),
        blacklist_characters='\x00'
    )))


@st.composite
def blueprint_description(draw):
    """Generate optional blueprint description."""
    return draw(st.one_of(
        st.none(),
        st.text(max_size=1000, alphabet=st.characters(blacklist_categories=('Cs',)))
    ))


# Property 5: Blueprint creation persists with ownership
# Feature: platform-evolution, Property 5: Blueprint creation persists with ownership
# Validates: Requirements 2.1, 2.4

@settings(max_examples=100)
@given(
    name=blueprint_name(),
    description=blueprint_description(),
    blueprint_data=valid_blueprint_data()
)
def test_property_5_blueprint_creation_persists_with_ownership(
    name,
    description,
    blueprint_data
):
    """Property 5: For any valid blueprint data and authenticated user, creating a 
    blueprint should result in a database record with the correct user_id, version 1, 
    and all required metadata fields.
    """
    # Setup
    db_session, engine = create_db_session()
    blueprint_service = BlueprintService(BlueprintValidator())
    test_user = create_test_user(db_session)
    
    try:
        # Create blueprint
        blueprint = blueprint_service.create_blueprint(
            db=db_session,
            user_id=test_user.id,
            name=name,
            description=description,
            blueprint_data=blueprint_data
        )
        
        # Verify persistence
        assert blueprint.id is not None, "Blueprint should have an ID"
        assert blueprint.user_id == test_user.id, "Blueprint should be owned by the user"
        assert blueprint.version == 1, "New blueprint should have version 1"
        assert blueprint.name == name, "Blueprint name should match"
        assert blueprint.description == description, "Blueprint description should match"
        assert blueprint.blueprint_data is not None, "Blueprint data should be stored"
        assert blueprint.created_at is not None, "Blueprint should have created_at timestamp"
        assert blueprint.updated_at is not None, "Blueprint should have updated_at timestamp"
        assert blueprint.is_deleted == False, "New blueprint should not be deleted"
        
        # Verify it can be retrieved from database
        retrieved = db_session.query(Blueprint).filter(Blueprint.id == blueprint.id).first()
        assert retrieved is not None, "Blueprint should be retrievable from database"
        assert retrieved.user_id == test_user.id, "Retrieved blueprint should have correct owner"
    finally:
        # Cleanup
        db_session.close()
        engine.dispose()


# Property 6: Users only see their own blueprints
# Feature: platform-evolution, Property 6: Users only see their own blueprints
# Validates: Requirements 2.2

@settings(max_examples=100)
@given(
    user1_blueprints=st.lists(
        st.tuples(blueprint_name(), blueprint_description(), valid_blueprint_data()),
        min_size=1,
        max_size=5
    ),
    user2_blueprints=st.lists(
        st.tuples(blueprint_name(), blueprint_description(), valid_blueprint_data()),
        min_size=1,
        max_size=5
    )
)
def test_property_6_users_only_see_own_blueprints(
    user1_blueprints,
    user2_blueprints
):
    """Property 6: For any user requesting their blueprints, the system should return 
    only blueprints where user_id matches the authenticated user, ensuring complete 
    isolation between users.
    """
    # Setup
    db_session, engine = create_db_session()
    blueprint_service = BlueprintService(BlueprintValidator())
    
    try:
        # Create two users
        user1 = create_test_user(db_session, "user1@example.com")
        user2 = create_test_user(db_session, "user2@example.com")
        
        # Create blueprints for user1
        user1_ids = []
        for name, desc, data in user1_blueprints:
            bp = blueprint_service.create_blueprint(
                db=db_session,
                user_id=user1.id,
                name=name,
                description=desc,
                blueprint_data=data
            )
            user1_ids.append(bp.id)
        
        # Create blueprints for user2
        user2_ids = []
        for name, desc, data in user2_blueprints:
            bp = blueprint_service.create_blueprint(
                db=db_session,
                user_id=user2.id,
                name=name,
                description=desc,
                blueprint_data=data
            )
            user2_ids.append(bp.id)
        
        # Get user1's blueprints
        user1_retrieved = blueprint_service.get_user_blueprints(db=db_session, user_id=user1.id)
        user1_retrieved_ids = [bp.id for bp in user1_retrieved]
        
        # Get user2's blueprints
        user2_retrieved = blueprint_service.get_user_blueprints(db=db_session, user_id=user2.id)
        user2_retrieved_ids = [bp.id for bp in user2_retrieved]
        
        # Verify isolation: user1 only sees their own blueprints
        assert len(user1_retrieved) == len(user1_blueprints), \
            "User1 should see exactly their blueprints"
        assert set(user1_retrieved_ids) == set(user1_ids), \
            "User1 should only see their own blueprint IDs"
        assert all(bp.user_id == user1.id for bp in user1_retrieved), \
            "All user1 blueprints should have user1's ID"
        
        # Verify isolation: user2 only sees their own blueprints
        assert len(user2_retrieved) == len(user2_blueprints), \
            "User2 should see exactly their blueprints"
        assert set(user2_retrieved_ids) == set(user2_ids), \
            "User2 should only see their own blueprint IDs"
        assert all(bp.user_id == user2.id for bp in user2_retrieved), \
            "All user2 blueprints should have user2's ID"
        
        # Verify no overlap
        assert set(user1_retrieved_ids).isdisjoint(set(user2_retrieved_ids)), \
            "Users should not see each other's blueprints"
    finally:
        # Cleanup
        db_session.close()
        engine.dispose()


# Property 7: Deletion prevents access
# Feature: platform-evolution, Property 7: Deletion prevents access
# Validates: Requirements 2.3

@settings(max_examples=100)
@given(
    name=blueprint_name(),
    description=blueprint_description(),
    blueprint_data=valid_blueprint_data()
)
def test_property_7_deletion_prevents_access(
    name,
    description,
    blueprint_data
):
    """Property 7: For any blueprint that has been deleted by its owner, subsequent 
    attempts to access that blueprint should fail, and it should not appear in the 
    owner's blueprint list.
    """
    # Setup
    db_session, engine = create_db_session()
    blueprint_service = BlueprintService(BlueprintValidator())
    test_user = create_test_user(db_session)
    
    try:
        # Create blueprint
        blueprint = blueprint_service.create_blueprint(
            db=db_session,
            user_id=test_user.id,
            name=name,
            description=description,
            blueprint_data=blueprint_data
        )
        blueprint_id = blueprint.id
        
        # Verify it's in the user's list
        blueprints_before = blueprint_service.get_user_blueprints(
            db=db_session,
            user_id=test_user.id
        )
        assert any(bp.id == blueprint_id for bp in blueprints_before), \
            "Blueprint should be in user's list before deletion"
        
        # Verify it can be accessed
        retrieved_before = blueprint_service.get_blueprint(
            db=db_session,
            blueprint_id=blueprint_id,
            user_id=test_user.id
        )
        assert retrieved_before is not None, "Blueprint should be accessible before deletion"
        
        # Delete the blueprint
        success = blueprint_service.delete_blueprint(
            db=db_session,
            blueprint_id=blueprint_id,
            user_id=test_user.id
        )
        assert success, "Deletion should succeed"
        
        # Verify it's NOT in the user's list anymore
        blueprints_after = blueprint_service.get_user_blueprints(
            db=db_session,
            user_id=test_user.id
        )
        assert not any(bp.id == blueprint_id for bp in blueprints_after), \
            "Deleted blueprint should not appear in user's list"
        
        # Verify it cannot be accessed
        retrieved_after = blueprint_service.get_blueprint(
            db=db_session,
            blueprint_id=blueprint_id,
            user_id=test_user.id
        )
        assert retrieved_after is None, "Deleted blueprint should not be accessible"
    finally:
        # Cleanup
        db_session.close()
        engine.dispose()


# Property 8: Updates increment version
# Feature: platform-evolution, Property 8: Updates increment version
# Validates: Requirements 2.5

@settings(max_examples=100)
@given(
    initial_name=blueprint_name(),
    initial_description=blueprint_description(),
    initial_data=valid_blueprint_data(),
    updates=st.lists(
        st.one_of(
            st.tuples(st.just("name"), blueprint_name()),
            st.tuples(st.just("description"), blueprint_description()),
            st.tuples(st.just("blueprint_data"), valid_blueprint_data())
        ),
        min_size=1,
        max_size=5
    )
)
def test_property_8_updates_increment_version(
    initial_name,
    initial_description,
    initial_data,
    updates
):
    """Property 8: For any blueprint update operation, the system should increment 
    the version number by exactly 1 and update the updated_at timestamp to the 
    current time.
    """
    # Setup
    db_session, engine = create_db_session()
    blueprint_service = BlueprintService(BlueprintValidator())
    test_user = create_test_user(db_session)
    
    try:
        # Create initial blueprint
        blueprint = blueprint_service.create_blueprint(
            db=db_session,
            user_id=test_user.id,
            name=initial_name,
            description=initial_description,
            blueprint_data=initial_data
        )
        
        assert blueprint.version == 1, "Initial version should be 1"
        initial_updated_at = blueprint.updated_at
        
        # Apply updates sequentially
        current_version = 1
        for field, value in updates:
            # Small delay to ensure timestamp changes
            import time
            time.sleep(0.01)
            
            # Update blueprint
            updated = blueprint_service.update_blueprint(
                db=db_session,
                blueprint_id=blueprint.id,
                user_id=test_user.id,
                updates={field: value}
            )
            
            # Verify version incremented by exactly 1
            assert updated.version == current_version + 1, \
                f"Version should increment by 1 (expected {current_version + 1}, got {updated.version})"
            
            # Verify updated_at changed
            assert updated.updated_at > initial_updated_at, \
                "updated_at should be more recent after update"
            
            # Update for next iteration
            current_version = updated.version
            initial_updated_at = updated.updated_at
        
        # Verify final version matches number of updates + 1
        final_blueprint = blueprint_service.get_blueprint(
            db=db_session,
            blueprint_id=blueprint.id,
            user_id=test_user.id
        )
        assert final_blueprint.version == len(updates) + 1, \
            f"Final version should be {len(updates) + 1} after {len(updates)} updates"
    finally:
        # Cleanup
        db_session.close()
        engine.dispose()
