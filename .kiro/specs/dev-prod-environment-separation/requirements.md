# Requirements Document

## Introduction

FrankenAgent Lab currently has mixed development and production configurations, leading to confusion and potential security issues. The Google OAuth authentication is not working properly in the local development environment. This specification addresses the need for clear separation between development and production environments following the KISS (Keep It Simple, Stupid) principle, while fixing the OAuth authentication flow.

## Glossary

- **Environment**: A distinct deployment context (development or production) with its own configuration
- **Dev Environment**: Local development setup running on localhost with SQLite and local OAuth
- **Prod Environment**: Production deployment using Supabase for authentication and database
- **OAuth Flow**: Authentication process using third-party providers (Google, GitHub)
- **Environment Variable**: Configuration value loaded from .env files
- **KISS Principle**: Keep It Simple, Stupid - favor simplicity over complexity
- **Supabase**: Backend-as-a-Service platform used for authentication and database
- **JWT**: JSON Web Token used for stateless authentication

## Requirements

### Requirement 1: Clear Environment Separation

**User Story:** As a developer, I want clear separation between development and production environments, so that I can develop and test locally without affecting production systems.

#### Acceptance Criteria

1. WHEN the system starts THEN the system SHALL determine the environment from an ENVIRONMENT variable (development or production)
2. WHEN running in development mode THEN the system SHALL use local SQLite database and disable SSL verification for OAuth
3. WHEN running in production mode THEN the system SHALL use Supabase for authentication and PostgreSQL database
4. WHEN environment-specific configuration is needed THEN the system SHALL load from .env.development or .env.production files
5. WHEN switching environments THEN the system SHALL validate that all required environment variables are present

### Requirement 2: Development Environment Configuration

**User Story:** As a developer, I want a simple local development setup, so that I can quickly start developing and testing features.

#### Acceptance Criteria

1. WHEN setting up development environment THEN the system SHALL use SQLite for database storage
2. WHEN running locally THEN the system SHALL use localhost URLs for frontend and backend
3. WHEN OAuth is configured THEN the system SHALL use development OAuth credentials with localhost redirect URIs
4. WHEN API keys are missing THEN the system SHALL provide clear error messages indicating which keys are required
5. WHEN starting the development server THEN the system SHALL automatically create necessary database tables

### Requirement 3: Production Environment Configuration

**User Story:** As a DevOps engineer, I want production configuration to be separate and secure, so that production systems are properly configured and protected.

#### Acceptance Criteria

1. WHEN deploying to production THEN the system SHALL use Supabase PostgreSQL for database storage
2. WHEN running in production THEN the system SHALL use production domain URLs for frontend and backend
3. WHEN OAuth is configured THEN the system SHALL use production OAuth credentials with production redirect URIs
4. WHEN secrets are needed THEN the system SHALL load from Supabase environment variables or Google Cloud Secret Manager
5. WHEN production starts THEN the system SHALL validate SSL certificates for all external connections

### Requirement 4: Google OAuth Fix for Development

**User Story:** As a developer, I want Google OAuth to work in my local development environment, so that I can test authentication flows without deploying to production.

#### Acceptance Criteria

1. WHEN Google OAuth is initiated in development THEN the system SHALL use localhost redirect URI (http://localhost:8000)
2. WHEN SSL certificate verification fails in development THEN the system SHALL disable SSL verification with a warning log
3. WHEN OAuth callback is received THEN the system SHALL properly exchange the authorization code for user information
4. WHEN OAuth user info is retrieved THEN the system SHALL create or update the user profile in the database
5. WHEN OAuth flow completes THEN the system SHALL return a valid JWT token to the frontend

### Requirement 5: Environment Variable Management

**User Story:** As a developer, I want clear documentation of required environment variables, so that I can properly configure each environment.

#### Acceptance Criteria

1. WHEN setting up an environment THEN the system SHALL provide .env.example files with all required variables
2. WHEN an environment variable is missing THEN the system SHALL fail fast with a clear error message
3. WHEN loading environment variables THEN the system SHALL prioritize environment-specific files (.env.development, .env.production)
4. WHEN sensitive values are needed THEN the system SHALL never commit actual secrets to version control
5. WHEN environment variables change THEN the system SHALL require a restart to pick up new values

### Requirement 6: Frontend Environment Configuration

**User Story:** As a frontend developer, I want the frontend to automatically use the correct backend URL, so that I don't have to manually configure it for each environment.

#### Acceptance Criteria

1. WHEN building for development THEN the frontend SHALL use http://localhost:8000 as the API base URL
2. WHEN building for production THEN the frontend SHALL use the production backend URL from environment variables
3. WHEN OAuth redirect occurs THEN the frontend SHALL handle the callback at the correct URL for the environment
4. WHEN API requests fail THEN the frontend SHALL display environment-appropriate error messages
5. WHEN switching environments THEN the frontend SHALL rebuild to pick up new configuration

### Requirement 7: Database Migration Strategy

**User Story:** As a developer, I want database migrations to work consistently across environments, so that schema changes are properly applied.

#### Acceptance Criteria

1. WHEN running migrations in development THEN the system SHALL apply migrations to local SQLite database
2. WHEN running migrations in production THEN the system SHALL apply migrations to Supabase PostgreSQL database
3. WHEN a migration fails THEN the system SHALL rollback and provide clear error messages
4. WHEN checking migration status THEN the system SHALL show which migrations have been applied
5. WHEN creating new migrations THEN the system SHALL generate migration files that work in both SQLite and PostgreSQL

### Requirement 8: Testing Environment Support

**User Story:** As a developer, I want to run tests without affecting development or production data, so that I can safely test features.

#### Acceptance Criteria

1. WHEN running tests THEN the system SHALL use a separate test database (SQLite in-memory or test-specific file)
2. WHEN tests complete THEN the system SHALL clean up test data automatically
3. WHEN testing OAuth THEN the system SHALL support mocking OAuth providers
4. WHEN testing API endpoints THEN the system SHALL use test-specific JWT tokens
5. WHEN tests fail THEN the system SHALL provide detailed error messages with environment context

### Requirement 9: Configuration Validation

**User Story:** As a system administrator, I want the system to validate configuration on startup, so that misconfigurations are caught early.

#### Acceptance Criteria

1. WHEN the system starts THEN the system SHALL validate all required environment variables are present
2. WHEN OAuth is enabled THEN the system SHALL validate OAuth credentials are configured
3. WHEN database connection is configured THEN the system SHALL test the connection on startup
4. WHEN configuration is invalid THEN the system SHALL fail fast with actionable error messages
5. WHEN running in production THEN the system SHALL enforce stricter validation rules (e.g., HTTPS required)

### Requirement 10: Documentation and Developer Experience

**User Story:** As a new developer, I want clear documentation on setting up each environment, so that I can quickly get started.

#### Acceptance Criteria

1. WHEN setting up development THEN the documentation SHALL provide step-by-step instructions
2. WHEN configuring OAuth THEN the documentation SHALL explain how to create OAuth applications for each provider
3. WHEN troubleshooting issues THEN the documentation SHALL provide common problems and solutions
4. WHEN deploying to production THEN the documentation SHALL provide a deployment checklist
5. WHEN environment variables change THEN the documentation SHALL be updated to reflect the changes
