# Database Models and Migrations

This directory contains the SQLAlchemy database models and Alembic migration configuration for FrankenAgent Lab.

## Models

The following models are defined:

- **User**: User accounts with authentication credentials and token quotas
- **Blueprint**: Agent configurations with ownership, versioning, and marketplace support
- **Session**: Chat conversation history between users and agents
- **UserAPIKey**: Encrypted API keys for LLM providers (using envelope encryption with Cloud KMS)
- **MarketplaceRating**: User ratings for public marketplace blueprints

## Database Setup

### Local Development (SQLite)

For local development, the system uses SQLite by default:

```bash
# Set database URL in .env
DATABASE_URL=sqlite:///./tmp/frankenagent.db

# Run migrations
poetry run alembic upgrade head

# Check current migration version
poetry run alembic current

# Rollback one migration
poetry run alembic downgrade -1

# Rollback all migrations
poetry run alembic downgrade base
```

### Production (PostgreSQL on Cloud SQL)

For production deployment on Google Cloud Platform:

```bash
# Ensure GCP_PROJECT_ID is set
export GCP_PROJECT_ID=your-project-id

# Run migrations on Cloud SQL
./scripts/run-migrations.sh
```

## Creating New Migrations

When you modify the models, create a new migration:

```bash
# Auto-generate migration from model changes
poetry run alembic revision --autogenerate -m "Description of changes"

# Create empty migration for manual changes
poetry run alembic revision -m "Description of changes"

# Edit the generated migration file in alembic/versions/
# Then run the migration
poetry run alembic upgrade head
```

## Migration Best Practices

1. **Always review auto-generated migrations** - Alembic may not detect all changes correctly
2. **Test migrations locally first** - Run upgrade and downgrade to ensure they work
3. **Make migrations reversible** - Always implement the downgrade() function
4. **Use conditional logic for database-specific features** - Check dialect name for PostgreSQL-only features
5. **Never edit applied migrations** - Create a new migration to fix issues

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    token_quota INTEGER DEFAULT 100000,
    token_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Blueprints Table

```sql
CREATE TABLE blueprints (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    blueprint_data JSON NOT NULL,
    version INTEGER DEFAULT 1,
    is_public BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    clone_count INTEGER DEFAULT 0,
    rating_sum INTEGER DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);
```

### Sessions Table

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    blueprint_id UUID REFERENCES blueprints(id) ON DELETE CASCADE,
    messages JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP
);
```

### User API Keys Table

```sql
CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    key_name VARCHAR(255),
    encrypted_key BYTEA NOT NULL,
    encrypted_dek BYTEA NOT NULL,
    key_last_four CHAR(4) NOT NULL,
    nonce BYTEA NOT NULL,
    kms_key_version VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Marketplace Ratings Table

```sql
CREATE TABLE marketplace_ratings (
    id UUID PRIMARY KEY,
    blueprint_id UUID REFERENCES blueprints(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(blueprint_id, user_id)
);
```

## Indexes

The following indexes are created for performance:

- `ix_users_email` - Unique index on user email
- `ix_blueprints_user_id` - Index on blueprint ownership
- `ix_blueprints_is_public` - Index on public blueprints
- `idx_blueprints_public` - Partial index for public, non-deleted blueprints
- `idx_blueprints_name_search` - Full-text search index (PostgreSQL only)
- `ix_sessions_user_id` - Index on session ownership
- `ix_sessions_blueprint_id` - Index on session blueprint
- `idx_sessions_last_message` - Composite index for recent sessions
- `ix_user_api_keys_user_id` - Index on API key ownership
- `idx_user_api_keys_provider` - Composite index for user + provider
- `ix_marketplace_ratings_blueprint_id` - Index on blueprint ratings
- `idx_ratings_unique` - Unique composite index for one rating per user per blueprint

## Security Considerations

### API Key Encryption

User API keys are encrypted using envelope encryption:

1. Each API key is encrypted with a unique Data Encryption Key (DEK) using AES-256-GCM
2. The DEK is encrypted with a Key Encryption Key (KEK) from Google Cloud KMS
3. Only the encrypted key and encrypted DEK are stored in the database
4. The plaintext key is never logged or stored

### Password Hashing

User passwords are hashed using bcrypt with 12 salt rounds before storage.

### Cascade Deletes

All foreign keys use `ON DELETE CASCADE` to ensure:
- Deleting a user removes all their blueprints, sessions, API keys, and ratings
- Deleting a blueprint removes all associated sessions and ratings

## Troubleshooting

### Migration Conflicts

If you encounter migration conflicts:

```bash
# Check current migration version
poetry run alembic current

# View migration history
poetry run alembic history

# Stamp database to specific version (use with caution)
poetry run alembic stamp <revision>
```

### Database Connection Issues

If you can't connect to the database:

1. Check DATABASE_URL environment variable
2. Verify database server is running
3. Check firewall rules (for Cloud SQL)
4. Ensure Cloud SQL Proxy is running (for Cloud SQL)

### SQLite vs PostgreSQL Differences

Some features are PostgreSQL-specific:
- JSONB type (falls back to JSON in SQLite)
- Full-text search with GIN indexes
- UUID type (stored as string in SQLite)

The migrations handle these differences automatically.
