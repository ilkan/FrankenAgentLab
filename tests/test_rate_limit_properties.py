"""Property-based tests for rate limiting service.

Feature: platform-evolution
Properties tested:
- Property 16: Rate limit enforced at threshold

Validates: Requirements 6.2, 6.4
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from uuid import uuid4, UUID
from unittest.mock import Mock, patch
import time

from frankenagent.services.rate_limit_service import RateLimitService


# Helper functions

def create_mock_redis():
    """Create a mock Redis client that simulates in-memory storage with TTL."""
    storage = {}
    expiry = {}
    
    mock_redis = Mock()
    
    def mock_incr(key):
        # Simulate INCR command
        if key not in storage:
            storage[key] = 0
        storage[key] += 1
        return storage[key]
    
    def mock_expire(key, ttl):
        # Simulate EXPIRE command
        expiry[key] = time.time() + ttl
        return True
    
    def mock_get(key):
        # Check if key has expired
        if key in expiry and time.time() > expiry[key]:
            if key in storage:
                del storage[key]
            del expiry[key]
            return None
        return str(storage.get(key, 0))
    
    def mock_delete(*keys):
        deleted = 0
        for key in keys:
            if key in storage:
                del storage[key]
                deleted += 1
            if key in expiry:
                del expiry[key]
        return deleted
    
    def mock_ping():
        return True
    
    mock_redis.incr = mock_incr
    mock_redis.expire = mock_expire
    mock_redis.get = mock_get
    mock_redis.delete = mock_delete
    mock_redis.ping = mock_ping
    
    return mock_redis, storage, expiry


# Hypothesis strategies

@st.composite
def user_ids(draw):
    """Generate random user UUIDs."""
    return uuid4()


# Property tests

@given(user_id=st.uuids())
@settings(max_examples=10, deadline=None)
def test_property_16_rate_limit_enforced_at_threshold(user_id):
    """
    **Feature: platform-evolution, Property 16: Rate limit enforced at threshold**
    
    For any user making requests, the 101st request within a 60-second window
    should be rejected with retry_after > 0.
    
    **Validates: Requirements 6.2, 6.4**
    """
    # Setup: Create rate limit service with mock Redis
    mock_redis, storage, expiry = create_mock_redis()
    
    with patch('frankenagent.services.rate_limit_service.redis.Redis', return_value=mock_redis):
        rate_limit_service = RateLimitService(
            redis_host="localhost",
            requests_per_minute=100,
            requests_per_day=1000
        )
    
    # Make exactly 100 requests (at the limit)
    for i in range(100):
        allowed, retry_after = rate_limit_service.check_rate_limit(user_id)
        assert allowed, f"Request {i+1} should be allowed (within limit)"
        assert retry_after == 0, f"Request {i+1} should have retry_after=0"
    
    # Property: The 101st request should be rejected
    allowed, retry_after = rate_limit_service.check_rate_limit(user_id)
    assert not allowed, "Request 101 should be rejected (exceeds limit)"
    assert retry_after > 0, "Rejected request should have retry_after > 0"
    assert retry_after <= 60, "Retry after should be within 60 seconds (minute window)"
    
    # Verify usage statistics reflect the limit
    usage = rate_limit_service.get_usage(user_id)
    assert usage["requests_this_minute"] == 101, "Should show 101 requests this minute"
    assert usage["minute_remaining"] == 0, "Should have 0 remaining requests"


@given(user_id=st.uuids(), num_requests=st.integers(min_value=1, max_value=99))
@settings(max_examples=10, deadline=None)
def test_requests_below_limit_are_allowed(user_id, num_requests):
    """
    Additional test: Verify requests below the limit are always allowed.
    
    For any number of requests below the limit, all should be allowed.
    """
    # Setup: Create rate limit service with mock Redis
    mock_redis, storage, expiry = create_mock_redis()
    
    with patch('frankenagent.services.rate_limit_service.redis.Redis', return_value=mock_redis):
        rate_limit_service = RateLimitService(
            redis_host="localhost",
            requests_per_minute=100,
            requests_per_day=1000
        )
    
    # Make requests below the limit
    for i in range(num_requests):
        allowed, retry_after = rate_limit_service.check_rate_limit(user_id)
        assert allowed, f"Request {i+1}/{num_requests} should be allowed"
        assert retry_after == 0, f"Request {i+1} should have retry_after=0"
    
    # Verify usage
    usage = rate_limit_service.get_usage(user_id)
    assert usage["requests_this_minute"] == num_requests
    assert usage["minute_remaining"] == 100 - num_requests


@given(user_id=st.uuids())
@settings(max_examples=10, deadline=None)
def test_daily_rate_limit_enforced(user_id):
    """
    Additional test: Verify daily rate limit is enforced.
    
    For any user, the 1001st request in a day should be rejected.
    """
    # Setup: Create rate limit service with mock Redis
    mock_redis, storage, expiry = create_mock_redis()
    
    with patch('frankenagent.services.rate_limit_service.redis.Redis', return_value=mock_redis):
        rate_limit_service = RateLimitService(
            redis_host="localhost",
            requests_per_minute=100,
            requests_per_day=1000
        )
    
    # Simulate 1000 requests spread across multiple minute windows
    # We'll manually set the day counter to 1000
    current_time = int(time.time())
    day_window = current_time // 86400
    day_key = f"ratelimit:day:{user_id}:{day_window}"
    
    # Set day counter to 1000 (at the limit)
    storage[day_key] = 1000
    
    # Next request should be rejected due to daily limit
    allowed, retry_after = rate_limit_service.check_rate_limit(user_id)
    assert not allowed, "Request should be rejected (exceeds daily limit)"
    assert retry_after > 0, "Rejected request should have retry_after > 0"
    # Daily limit retry should be longer than minute limit
    assert retry_after > 60, "Daily limit retry should be longer than minute limit"
    
    # Verify usage
    usage = rate_limit_service.get_usage(user_id)
    assert usage["requests_this_day"] == 1001, "Should show 1001 requests today"
    assert usage["day_remaining"] == 0, "Should have 0 remaining daily requests"


@given(user_ids=st.lists(st.uuids(), min_size=2, max_size=5, unique=True))
@settings(max_examples=10, deadline=None)
def test_rate_limits_isolated_per_user(user_ids):
    """
    Additional test: Verify rate limits are isolated per user.
    
    For any set of different users, one user hitting the limit should not
    affect other users.
    """
    # Setup: Create rate limit service with mock Redis
    mock_redis, storage, expiry = create_mock_redis()
    
    with patch('frankenagent.services.rate_limit_service.redis.Redis', return_value=mock_redis):
        rate_limit_service = RateLimitService(
            redis_host="localhost",
            requests_per_minute=100,
            requests_per_day=1000
        )
    
    # First user hits the limit
    target_user = user_ids[0]
    for _ in range(101):
        rate_limit_service.check_rate_limit(target_user)
    
    # Verify first user is rate limited
    allowed, _ = rate_limit_service.check_rate_limit(target_user)
    assert not allowed, "First user should be rate limited"
    
    # Verify other users are not affected
    for user_id in user_ids[1:]:
        allowed, retry_after = rate_limit_service.check_rate_limit(user_id)
        assert allowed, f"User {user_id} should not be affected by other user's limit"
        assert retry_after == 0, "Unaffected user should have retry_after=0"


@given(user_id=st.uuids())
@settings(max_examples=10, deadline=None)
def test_get_usage_returns_accurate_counts(user_id):
    """
    Additional test: Verify get_usage returns accurate request counts.
    
    For any user, get_usage should return accurate counts of requests made.
    """
    # Setup: Create rate limit service with mock Redis
    mock_redis, storage, expiry = create_mock_redis()
    
    with patch('frankenagent.services.rate_limit_service.redis.Redis', return_value=mock_redis):
        rate_limit_service = RateLimitService(
            redis_host="localhost",
            requests_per_minute=100,
            requests_per_day=1000
        )
    
    # Make some requests
    num_requests = 42
    for _ in range(num_requests):
        rate_limit_service.check_rate_limit(user_id)
    
    # Get usage
    usage = rate_limit_service.get_usage(user_id)
    
    # Verify accuracy
    assert usage["requests_this_minute"] == num_requests, \
        "Usage should show exact number of requests"
    assert usage["requests_this_day"] == num_requests, \
        "Daily usage should match minute usage (same window)"
    assert usage["minute_remaining"] == 100 - num_requests, \
        "Remaining should be limit minus used"
    assert usage["day_remaining"] == 1000 - num_requests, \
        "Daily remaining should be limit minus used"
    assert usage["minute_limit"] == 100, "Minute limit should be 100"
    assert usage["day_limit"] == 1000, "Day limit should be 1000"


@given(user_id=st.uuids())
@settings(max_examples=10, deadline=None)
def test_reset_user_limits_clears_counters(user_id):
    """
    Additional test: Verify reset_user_limits clears rate limit counters.
    
    For any user who has made requests, resetting their limits should
    allow them to make requests again.
    """
    # Setup: Create rate limit service with mock Redis
    mock_redis, storage, expiry = create_mock_redis()
    
    with patch('frankenagent.services.rate_limit_service.redis.Redis', return_value=mock_redis):
        rate_limit_service = RateLimitService(
            redis_host="localhost",
            requests_per_minute=100,
            requests_per_day=1000
        )
    
    # Hit the rate limit
    for _ in range(101):
        rate_limit_service.check_rate_limit(user_id)
    
    # Verify user is rate limited
    allowed, _ = rate_limit_service.check_rate_limit(user_id)
    assert not allowed, "User should be rate limited before reset"
    
    # Reset limits
    success = rate_limit_service.reset_user_limits(user_id)
    assert success, "Reset should succeed"
    
    # Verify user can make requests again
    allowed, retry_after = rate_limit_service.check_rate_limit(user_id)
    assert allowed, "User should be able to make requests after reset"
    assert retry_after == 0, "Reset user should have retry_after=0"
    
    # Verify usage is reset
    usage = rate_limit_service.get_usage(user_id)
    assert usage["requests_this_minute"] == 1, "Should show 1 request after reset"


@given(user_id=st.uuids())
@settings(max_examples=10, deadline=None)
def test_rate_limit_graceful_degradation_on_redis_failure(user_id):
    """
    Additional test: Verify rate limiting fails open on Redis errors.
    
    For any rate limit check, if Redis fails, the request should be allowed
    (fail open) to prevent service disruption.
    """
    # Setup: Create rate limit service with failing Redis
    mock_redis = Mock()
    mock_redis.incr.side_effect = Exception("Redis connection failed")
    mock_redis.get.side_effect = Exception("Redis connection failed")
    
    with patch('frankenagent.services.rate_limit_service.redis.Redis', return_value=mock_redis):
        rate_limit_service = RateLimitService(
            redis_host="localhost",
            requests_per_minute=100,
            requests_per_day=1000
        )
    
    # Verify requests are allowed despite Redis failure (fail open)
    allowed, retry_after = rate_limit_service.check_rate_limit(user_id)
    assert allowed, "Request should be allowed on Redis failure (fail open)"
    assert retry_after == 0, "Failed check should have retry_after=0"
    
    # Verify get_usage returns safe defaults
    usage = rate_limit_service.get_usage(user_id)
    assert usage["requests_this_minute"] == 0, "Should return 0 on failure"
    assert usage["minute_remaining"] == 100, "Should return full limit on failure"


@given(
    user_id=st.uuids(),
    requests_per_minute=st.integers(min_value=1, max_value=10),
    num_requests=st.integers(min_value=1, max_value=15)
)
@settings(max_examples=10, deadline=None)
def test_custom_rate_limits_enforced(user_id, requests_per_minute, num_requests):
    """
    Additional test: Verify custom rate limits are enforced correctly.
    
    For any custom rate limit configuration, the limit should be enforced
    at the specified threshold.
    """
    # Setup: Create rate limit service with custom limits
    mock_redis, storage, expiry = create_mock_redis()
    
    with patch('frankenagent.services.rate_limit_service.redis.Redis', return_value=mock_redis):
        rate_limit_service = RateLimitService(
            redis_host="localhost",
            requests_per_minute=requests_per_minute,
            requests_per_day=1000
        )
    
    # Make requests
    allowed_count = 0
    rejected_count = 0
    
    for i in range(num_requests):
        allowed, retry_after = rate_limit_service.check_rate_limit(user_id)
        if allowed:
            allowed_count += 1
        else:
            rejected_count += 1
    
    # Verify enforcement
    if num_requests <= requests_per_minute:
        # All requests should be allowed
        assert allowed_count == num_requests, \
            f"All {num_requests} requests should be allowed (limit={requests_per_minute})"
        assert rejected_count == 0, "No requests should be rejected"
    else:
        # Some requests should be rejected
        assert allowed_count == requests_per_minute, \
            f"Only {requests_per_minute} requests should be allowed"
        assert rejected_count == num_requests - requests_per_minute, \
            f"Excess requests should be rejected"
