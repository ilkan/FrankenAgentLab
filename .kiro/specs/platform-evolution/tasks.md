# Implementation Plan

## Overview

Transform FrankenAgent Lab from local MVP to production multi-tenant platform on GCP with authentication, persistent storage, marketplace, and secure user API key management.

## Tasks

- [x] 1. Install deployment tools and setup GCP project
  - Install Google Cloud CLI using `scripts/install-gcp-cli.sh`
  - Install Firebase CLI using `scripts/install-firebase-cli.sh`
  - Create GCP project and enable billing
  - Set project ID in environment variables
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2. Setup GCP infrastructure
  - Run `scripts/setup-infrastructure.sh` to provision Cloud SQL, Memorystore, Storage bucket
  - Create KMS keyring and key for API key encryption
  - Add platform API keys to Secret Manager (OPENAI_API_KEY, TAVILY_API_KEY, JWT_SECRET_KEY)
  - Configure VPC and firewall rules
  - _Requirements: 5.1, 8.1, 8.2, 8.3, 8.4_

- [x] 3. Implement database models and migrations
- [x] 3.1 Create SQLAlchemy models for users, blueprints, sessions, user_api_keys, marketplace_ratings
  - Define User model with email, password_hash, token_quota, token_used
  - Define Blueprint model with user_id FK, blueprint_data JSONB, version, is_public
  - Define Session model with user_id FK, blueprint_id FK, messages JSONB
  - Define UserAPIKey model with encrypted_key, encrypted_dek, nonce, kms_key_version
  - Define MarketplaceRating model with blueprint_id FK, user_id FK, rating
  - _Requirements: 1.2, 2.1, 2.4, 4.3, 9.1_

- [x] 3.2 Create Alembic migration scripts
  - Initialize Alembic in project
  - Generate migration for all tables with indexes
  - Add full-text search index on blueprints (name, description)
  - Test migration up/down locally
  - _Requirements: 2.1, 3.3, 5.2_

- [x] 3.3 Run database migrations on Cloud SQL
  - Use `scripts/run-migrations.sh` to apply migrations
  - Verify all tables and indexes created
  - _Requirements: 5.1_

- [x] 4. Implement authentication service
- [x] 4.1 Create AuthService with JWT and bcrypt
  - Implement `hash_password()` using bcrypt with 12 rounds
  - Implement `verify_password()` for login
  - Implement `create_access_token()` with 24-hour expiration
  - Implement `verify_token()` to extract user_id from JWT
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 4.2 Create auth API endpoints
  - POST /api/auth/register - Create user with hashed password
  - POST /api/auth/login - Verify credentials and return JWT
  - GET /api/auth/me - Get current user info (requires auth)
  - Add JWT middleware to validate tokens on protected routes
  - _Requirements: 1.1, 1.3, 1.4, 1.5_

- [x] 4.3 Write property test for authentication
  - **Property 1: User registration creates unique accounts**
  - **Property 2: Valid login returns valid JWT**
  - **Property 3: Valid tokens authenticate requests**
  - **Property 4: Invalid tokens are rejected**
  - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**

- [-] 5. Implement API key encryption service
- [x] 5.1 Create APIKeyEncryptionService with Cloud KMS
  - Initialize KMS client with project/location/keyring/key
  - Implement `encrypt_api_key()` using AES-256-GCM + envelope encryption
  - Implement `decrypt_api_key()` with secure memory handling
  - Implement `rotate_encryption()` for key rotation
  - _Requirements: 9.1, 9.3, 9.8_

- [x] 5.2 Create UserAPIKeyService
  - Implement `add_api_key()` to encrypt and store user keys
  - Implement `get_user_api_keys()` to list keys (masked)
  - Implement `get_decrypted_key()` for agent execution
  - Implement `delete_api_key()` for secure deletion
  - Implement `rotate_all_keys()` for KMS key rotation
  - _Requirements: 9.1, 9.3, 9.4, 9.5, 9.7_

- [x] 5.3 Add log sanitization filter
  - Create `APIKeySanitizingFilter` with regex patterns for OpenAI, Anthropic, Groq, Gemini keys
  - Apply filter to root logger
  - Test that keys are redacted from logs
  - _Requirements: 9.2, 9.6_

- [x] 5.4 Create API key management endpoints
  - POST /api/keys - Add encrypted API key (requires auth)
  - GET /api/keys - List user's keys with masking (requires auth)
  - DELETE /api/keys/{id} - Delete key (requires auth + ownership)
  - _Requirements: 9.1, 9.4, 9.5_

- [x] 5.5 Write property tests for API key security
  - **Property 19: API keys are encrypted before storage**
  - **Property 20: Decrypted keys are never logged**
  - **Property 21: Keys displayed with masking**
  - **Property 22: Deleted keys are permanently removed**
  - **Property 23: User deletion removes all keys**
  - **Validates: Requirements 9.1, 9.2, 9.4, 9.5, 9.7**

- [x] 6. Implement blueprint service with persistence
- [x] 6.1 Create BlueprintService
  - Implement `create_blueprint()` with validation and database insert
  - Implement `get_user_blueprints()` filtered by user_id
  - Implement `get_blueprint()` with ownership/public check
  - Implement `update_blueprint()` with version increment
  - Implement `delete_blueprint()` with soft delete
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6.2 Create blueprint API endpoints
  - POST /api/blueprints - Create blueprint (requires auth)
  - GET /api/blueprints - List user's blueprints (requires auth)
  - GET /api/blueprints/{id} - Get blueprint (requires auth or public)
  - PUT /api/blueprints/{id} - Update blueprint (requires auth + ownership)
  - DELETE /api/blueprints/{id} - Delete blueprint (requires auth + ownership)
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [x] 6.3 Write property tests for blueprint persistence
  - **Property 5: Blueprint creation persists with ownership**
  - **Property 6: Users only see their own blueprints**
  - **Property 7: Deletion prevents access**
  - **Property 8: Updates increment version**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

- [x] 7. Implement agent cache service
- [x] 7.1 Create AgentCacheService with Redis
  - Initialize Redis client with connection to Memorystore
  - Implement `get_compiled_agent()` with pickle deserialization
  - Implement `set_compiled_agent()` with 1-hour TTL
  - Implement `invalidate_agent()` to clear cache on update
  - Add error handling for Redis connection failures
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 7.2 Integrate cache into ExecutionOrchestrator
  - Check cache before compiling agent
  - Store compiled agent in cache after compilation
  - Invalidate cache when blueprint is updated
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 7.3 Write property tests for caching
  - **Property 17: Cache hit avoids recompilation**
  - **Property 18: Update invalidates cache**
  - **Validates: Requirements 7.2, 7.3**

- [x] 8. Implement rate limiting service
- [x] 8.1 Create RateLimitService with Redis
  - Implement `check_rate_limit()` with per-minute and per-day counters
  - Use Redis INCR with TTL for sliding window
  - Return (allowed, retry_after_seconds)
  - Implement `get_usage()` for monitoring
  - _Requirements: 6.2, 6.3_

- [x] 8.2 Add rate limiting middleware
  - Apply rate limit check before all protected endpoints
  - Return 429 with Retry-After header when exceeded
  - Log rate limit violations
  - _Requirements: 6.2, 6.4, 6.5_

- [x] 8.3 Write property test for rate limiting
  - **Property 16: Rate limit enforced at threshold**
  - **Validates: Requirements 6.2, 6.4**

- [-] 9. Implement marketplace service
- [x] 9.1 Create MarketplaceService
  - Implement `publish_blueprint()` to set is_public=true
  - Implement `search_marketplace()` with full-text search and pagination
  - Implement `clone_blueprint()` to create user copy
  - Implement `rate_blueprint()` to add/update rating
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 9.2 Create marketplace API endpoints
  - POST /api/marketplace/publish - Publish blueprint (requires auth)
  - GET /api/marketplace - Browse/search marketplace
  - POST /api/marketplace/{id}/clone - Clone blueprint (requires auth)
  - POST /api/marketplace/{id}/rate - Rate blueprint (requires auth)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 9.3 Write property tests for marketplace
  - **Property 9: Marketplace returns required fields**
  - **Property 10: Search returns matching results**
  - **Property 11: Clone creates independent copy**
  - **Property 12: Ratings update average correctly**
  - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**

- [x] 10. Implement session management service
- [x] 10.1 Create SessionService
  - Implement `create_session()` for user + blueprint
  - Implement `get_user_sessions()` with metadata
  - Implement `add_message()` to append to JSONB array
  - Implement `get_session_history()` to retrieve messages
  - _Requirements: 4.2, 4.3, 4.4_

- [x] 10.2 Create session API endpoints
  - POST /api/sessions - Create session (requires auth)
  - GET /api/sessions - List user's sessions (requires auth)
  - GET /api/sessions/{id}/history - Get message history (requires auth)
  - _Requirements: 4.2, 4.3_

- [x] 10.3 Write property tests for sessions
  - **Property 13: Messages route to correct agent**
  - **Property 14: Session histories are isolated**
  - **Validates: Requirements 4.3, 4.4**

- [x] 11. Update agent execution to use user API keys
- [x] 11.1 Modify ExecutionOrchestrator
  - Accept user_id parameter
  - Decrypt user's API key for provider
  - Inject API key into blueprint (memory only)
  - Execute agent with user's key
  - Securely wipe key from memory after execution
  - _Requirements: 9.3_

- [x] 11.2 Update /api/agents/run endpoint
  - Extract user_id from JWT token
  - Pass user_id to ExecutionOrchestrator
  - Handle missing API key error gracefully
  - _Requirements: 9.3_

- [x] 12. Update frontend for authentication
- [x] 12.1 Create auth UI components
  - LoginForm component with email/password
  - RegisterForm component with email/password/name
  - AuthContext for managing JWT token
  - ProtectedRoute wrapper for authenticated pages
  - _Requirements: 1.1, 1.3_

- [x] 12.2 Add API key management UI
  - APIKeyList component showing masked keys
  - AddAPIKeyDialog for adding new keys
  - Delete confirmation for key removal
  - Provider selection (OpenAI, Anthropic, Groq, Gemini)
  - _Requirements: 9.1, 9.4, 9.5_

- [x] 12.3 Update blueprint management UI
  - Fetch blueprints from /api/blueprints instead of local
  - Save blueprints to database on deploy
  - Add blueprint list view with edit/delete
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 12.4 Add marketplace UI
  - MarketplaceBrowser component with search
  - MarketplaceCard showing blueprint details
  - Clone button to copy to user's collection
  - Rating stars for marketplace blueprints
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 12.5 Add multi-agent selector
  - AgentSelector dropdown in chat interface
  - Fetch user's blueprints for dropdown
  - Create new session on agent switch
  - Display agent name and last used time
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 13. Create deployment scripts
- [x] 13.1 Create Dockerfile for backend
  - Use python:3.11-slim base image
  - Install Poetry and dependencies
  - Copy application code
  - Expose port 8080
  - Set CMD to run uvicorn
  - _Requirements: 8.1_

- [x] 13.2 Create backend deployment script
  - Create `scripts/deploy-backend.sh`
  - Build Docker image and push to GCR
  - Deploy to Cloud Run with secrets and Cloud SQL connection
  - Set environment variables and scaling config
  - _Requirements: 8.1_

- [x] 13.3 Create frontend deployment script
  - Create `scripts/deploy-frontend.sh`
  - Build frontend with npm run build
  - Upload to Cloud Storage bucket
  - Set cache control headers
  - _Requirements: 8.2_

- [x] 13.4 Create CI/CD pipeline
  - Create `cloudbuild.yaml` for automated deployment
  - Configure trigger on push to main branch
  - Build, test, and deploy backend
  - Deploy frontend
  - _Requirements: 8.1, 8.2_

- [x] 14. Setup monitoring and logging
- [x] 14.1 Configure Cloud Logging
  - Setup structured logging with google-cloud-logging
  - Add request/response logging middleware
  - Log authentication events
  - Log API key access (with sanitization)
  - _Requirements: 8.5_

- [x] 14.2 Create monitoring dashboards
  - Request rate and latency metrics
  - Error rate by endpoint
  - Database connection pool usage
  - Redis cache hit rate
  - _Requirements: 8.5_

- [x] 14.3 Setup alerting
  - Alert on error rate > 5%
  - Alert on p95 latency > 2s
  - Alert on database CPU > 80%
  - Alert on service down (uptime check)
  - _Requirements: 8.5_

- [x] 15. Checkpoint - Deploy to staging and test
  - Deploy backend to Cloud Run staging environment
  - Deploy frontend to staging bucket
  - Run integration tests against staging
  - Test auth flow: register → login → protected endpoint
  - Test blueprint CRUD: create → read → update → delete
  - Test marketplace: publish → search → clone → rate
  - Test multi-agent: create 2 agents → switch → verify isolation
  - Test API key management: add → use → delete
  - Verify rate limiting with 101 requests
  - Verify caching with repeated executions
  - Check logs for sanitization (no plaintext keys)
  - Monitor metrics and alerts
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: All_

- [x] 16. Production deployment
- [x] 16.1 Deploy to production
  - Run `scripts/deploy-backend.sh` for production
  - Run `scripts/deploy-frontend.sh` for production
  - Verify health check endpoint
  - Run smoke tests
  - _Requirements: 8.1, 8.2_

- [x] 16.2 Configure custom domain
  - Setup Cloud Load Balancer
  - Configure SSL certificate
  - Point domain to load balancer
  - Update CORS settings
  - _Requirements: 8.1, 8.2_

- [x] 16.3 Final verification
  - Test all features in production
  - Verify monitoring and alerts
  - Check cost dashboard
  - Document any issues
  - _Requirements: All_
