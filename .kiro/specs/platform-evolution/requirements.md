# Platform Evolution Requirements

## Introduction

Transform FrankenAgent Lab from a local MVP into a production-ready multi-tenant platform with authentication, agent marketplace, persistent storage, and cloud deployment on GCP.

## Current State Summary

**Working:**
- Frontend drag-and-drop builder produces valid blueprints
- Backend validates blueprints (schema + business rules)
- Backend compiles blueprints to Agno agents
- Backend executes agents with guardrails and tracing
- In-memory session management
- Real-time chat interface with deployed agents

**Missing:**
- User authentication and authorization
- Blueprint persistence (currently file-based only)
- Agent marketplace (discovery, sharing, versioning)
- Multi-agent selection/switching
- Production database
- API gateway and rate limiting
- Cloud deployment infrastructure
- Caching layer for compiled agents

## Glossary

- **Platform**: The complete FrankenAgent Lab system including auth, marketplace, and cloud infrastructure
- **Blueprint**: YAML/JSON agent configuration following the Frankenstein metaphor
- **Marketplace**: Public/private repository of shareable agent blueprints
- **Session**: User conversation context with an agent
- **Compiled Agent**: Agno agent instance created from a blueprint
- **API Gateway**: Cloud-based request routing and rate limiting layer

## Requirements

### Requirement 1: User Authentication and Authorization

**User Story:** As a platform user, I want to create an account and log in, so that I can save my agents and access them across devices.

#### Acceptance Criteria

1. WHEN a new user visits the platform THEN the system SHALL provide registration with email and password
2. WHEN a user registers THEN the system SHALL create a user account with unique identifier and store credentials securely
3. WHEN a registered user logs in with valid credentials THEN the system SHALL issue a JWT token with 24-hour expiration
4. WHEN a user makes an API request with a valid JWT token THEN the system SHALL authenticate the request and associate it with the user
5. WHEN a user makes an API request without a token or with an invalid token THEN the system SHALL reject the request with 401 status

### Requirement 2: Blueprint Persistence

**User Story:** As a platform user, I want to save my agent blueprints to the cloud, so that I can access them from any device and don't lose my work.

#### Acceptance Criteria

1. WHEN a user creates or modifies a blueprint THEN the system SHALL persist it to the database with user ownership
2. WHEN a user requests their blueprints THEN the system SHALL return only blueprints owned by that user
3. WHEN a user deletes a blueprint THEN the system SHALL remove it from the database and prevent further access
4. WHEN a blueprint is saved THEN the system SHALL store metadata including name, description, version, created_at, and updated_at timestamps
5. WHEN a blueprint is updated THEN the system SHALL increment the version number and update the updated_at timestamp

### Requirement 3: Agent Marketplace

**User Story:** As a platform user, I want to discover and use pre-built agents from a marketplace, so that I can quickly get started without building from scratch.

#### Acceptance Criteria

1. WHEN a user publishes a blueprint to the marketplace THEN the system SHALL mark it as public and make it discoverable to all users
2. WHEN a user browses the marketplace THEN the system SHALL display public blueprints with name, description, author, rating, and usage count
3. WHEN a user searches the marketplace by keyword THEN the system SHALL return relevant blueprints matching the search term
4. WHEN a user clones a marketplace blueprint THEN the system SHALL create a private copy owned by that user
5. WHEN a user rates a marketplace blueprint THEN the system SHALL update the blueprint's average rating

### Requirement 4: Multi-Agent Selection

**User Story:** As a platform user, I want to switch between multiple deployed agents in the chat interface, so that I can use different agents for different tasks.

#### Acceptance Criteria

1. WHEN a user has multiple deployed agents THEN the system SHALL display a dropdown selector in the chat interface
2. WHEN a user selects a different agent from the dropdown THEN the system SHALL switch the active agent and start a new session
3. WHEN a user sends a message THEN the system SHALL route it to the currently selected agent
4. WHEN switching agents THEN the system SHALL preserve the conversation history for each agent separately
5. WHEN displaying the agent selector THEN the system SHALL show agent name and last used timestamp

### Requirement 5: Production Database

**User Story:** As a platform operator, I want to use a production-grade database, so that the system can scale and handle concurrent users reliably.

#### Acceptance Criteria

1. WHEN the system starts THEN the system SHALL connect to PostgreSQL database on Cloud SQL
2. WHEN storing user data THEN the system SHALL use PostgreSQL with proper indexing on user_id and blueprint_id
3. WHEN storing session data THEN the system SHALL use PostgreSQL with TTL-based cleanup of old sessions
4. WHEN multiple requests access the same data THEN the system SHALL handle concurrent access with proper transaction isolation
5. WHEN the database connection fails THEN the system SHALL retry with exponential backoff and log the error

### Requirement 6: API Gateway and Rate Limiting

**User Story:** As a platform operator, I want to protect the API from abuse, so that all users have fair access and costs remain controlled.

#### Acceptance Criteria

1. WHEN a request enters the system THEN the API Gateway SHALL route it to the appropriate backend service
2. WHEN a user exceeds 100 requests per minute THEN the system SHALL reject additional requests with 429 status
3. WHEN a user exceeds their daily token quota THEN the system SHALL reject execution requests with 429 status and quota exceeded message
4. WHEN rate limiting is triggered THEN the system SHALL include Retry-After header in the response
5. WHEN monitoring API usage THEN the system SHALL log request counts per user per endpoint

### Requirement 7: Agent Compilation Caching

**User Story:** As a platform user, I want my agents to respond quickly, so that I can have fluid conversations without waiting.

#### Acceptance Criteria

1. WHEN a blueprint is first executed THEN the system SHALL compile it to an Agno agent and cache the result
2. WHEN the same blueprint is executed again THEN the system SHALL retrieve the compiled agent from cache instead of recompiling
3. WHEN a blueprint is updated THEN the system SHALL invalidate the cached compiled agent
4. WHEN the cache reaches capacity THEN the system SHALL evict least recently used compiled agents
5. WHEN retrieving from cache THEN the system SHALL complete in under 50ms

### Requirement 8: Cloud Deployment on GCP

**User Story:** As a platform operator, I want to deploy the system to Google Cloud Platform, so that it's accessible to users worldwide with high availability.

#### Acceptance Criteria

1. WHEN deploying the backend THEN the system SHALL run on Cloud Run with auto-scaling from 0 to 10 instances
2. WHEN deploying the frontend THEN the system SHALL serve static assets from Cloud Storage with CDN
3. WHEN deploying the database THEN the system SHALL use Cloud SQL PostgreSQL with automated backups
4. WHEN deploying secrets THEN the system SHALL store API keys in Secret Manager
5. WHEN monitoring the system THEN the system SHALL send logs to Cloud Logging and metrics to Cloud Monitoring


### Requirement 9: Secure User API Key Storage

**User Story:** As a platform user, I want to securely store my own API keys (OpenAI, Claude, Groq, Gemini), so that I can use my own LLM accounts without exposing my keys to other users or platform administrators.

#### Acceptance Criteria

1. WHEN a user adds an API key THEN the system SHALL encrypt it using AES-256-GCM with a user-specific encryption key before storing
2. WHEN a user's API key is stored THEN the system SHALL never log the plaintext key or expose it in error messages
3. WHEN an agent executes using a user's API key THEN the system SHALL decrypt the key in memory only for the duration of the request
4. WHEN a user views their API keys THEN the system SHALL display only the last 4 characters (e.g., "sk-...xyz123")
5. WHEN a user deletes an API key THEN the system SHALL permanently remove both the encrypted key and encryption metadata from the database
6. WHEN the system detects an API key in logs or error messages THEN the system SHALL automatically redact it before storage
7. WHEN a user's account is deleted THEN the system SHALL securely delete all associated API keys and encryption keys
8. WHEN storing encryption keys THEN the system SHALL use Google Cloud KMS for key encryption keys (envelope encryption)
