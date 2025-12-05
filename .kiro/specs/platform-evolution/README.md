# FrankenAgent Lab Platform Evolution Spec

## Overview

This spec transforms FrankenAgent Lab from a local MVP into a production-ready multi-tenant platform with authentication, persistent storage, agent marketplace, and secure user API key management deployed on Google Cloud Platform.

## Status

✅ Requirements Complete (9 requirements, 45 acceptance criteria)
✅ Design Complete (Architecture, Services, API, Deployment, Security)
✅ Tasks Complete (16 top-level tasks, 50+ sub-tasks)

## Quick Links

- [Requirements](./requirements.md) - User stories and acceptance criteria
- [Action Plan](./action-plan.md) - Executive summary and 8-step plan
- [Design](./design.md) - Technical architecture and implementation details
- [Tasks](./tasks.md) - Detailed implementation checklist

## Key Features

### 1. User Authentication (Requirement 1)
- JWT-based authentication with 24-hour expiration
- bcrypt password hashing (12 rounds)
- Protected API endpoints

### 2. Blueprint Persistence (Requirement 2)
- PostgreSQL storage with user ownership
- Version tracking and soft delete
- CRUD API endpoints

### 3. Agent Marketplace (Requirement 3)
- Publish blueprints publicly
- Search with full-text indexing
- Clone and rate blueprints

### 4. Multi-Agent Selection (Requirement 4)
- Switch between multiple agents
- Separate session history per agent
- Dropdown selector in UI

### 5. Production Database (Requirement 5)
- Cloud SQL PostgreSQL
- Automated backups
- Connection pooling

### 6. API Gateway & Rate Limiting (Requirement 6)
- 100 requests/minute per user
- 1000 requests/day per user
- Retry-After headers

### 7. Agent Compilation Caching (Requirement 7)
- Redis/Memorystore cache
- 1-hour TTL
- Cache invalidation on update

### 8. Cloud Deployment (Requirement 8)
- Cloud Run (backend)
- Cloud Storage + CDN (frontend)
- Secret Manager (API keys)
- Cloud Logging & Monitoring

### 9. Secure User API Key Storage (Requirement 9) ⭐
- **Envelope encryption** with Cloud KMS
- **AES-256-GCM** encryption at rest
- **Per-user encryption keys** (DEK)
- **Memory-only decryption**
- **Automatic log sanitization**
- **Masked display** (***...xyz123)
- **Secure deletion** (hard delete)
- Supports: OpenAI, Anthropic, Groq, Gemini

## Architecture

```
Users → Cloud CDN → API Gateway → Cloud Run (Backend)
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              Cloud SQL         Memorystore      Secret Manager
             (PostgreSQL)         (Redis)         (API Keys)
```

## Security Highlights

### User API Key Protection
- **Threat Model**: Database breach, log exposure, admin access, memory dumps
- **Encryption**: AES-256-GCM with envelope encryption
- **Key Management**: Google Cloud KMS (HSM-backed)
- **Compliance**: GDPR, PCI DSS, SOC 2

### Authentication Security
- JWT tokens with HS256
- bcrypt password hashing (12 rounds)
- HTTPS only in production
- Rate limiting per user

## Deployment

### Prerequisites
```bash
# Install tools
./scripts/install-gcp-cli.sh
./scripts/install-firebase-cli.sh
```

### Infrastructure Setup
```bash
# Provision GCP resources
./scripts/setup-infrastructure.sh

# Run database migrations
./scripts/run-migrations.sh
```

### Deploy
```bash
# Deploy backend to Cloud Run
./scripts/deploy-backend.sh

# Deploy frontend to Cloud Storage
./scripts/deploy-frontend.sh
```

## Cost Estimate

### Development
- Cloud Run: $0 (pay per request)
- Cloud SQL: $25/month (db-f1-micro)
- Memorystore: $30/month (1GB)
- **Total: ~$60/month**

### Production
- Cloud Run: $50/month (10K req/day)
- Cloud SQL: $100/month (db-n1-standard-1)
- Memorystore: $150/month (5GB)
- Cloud Storage + CDN: $10/month
- **Total: ~$310/month** (excluding LLM API costs)

## Testing

### Property-Based Tests (23 properties)
- Authentication (4 properties)
- Blueprint persistence (4 properties)
- Marketplace (4 properties)
- Sessions (2 properties)
- Rate limiting (1 property)
- Caching (2 properties)
- API key security (5 properties)
- Database concurrency (1 property)

### Integration Tests
- Auth flow: register → login → protected endpoint
- Blueprint CRUD: create → read → update → delete
- Marketplace: publish → search → clone → rate
- Multi-agent: create → switch → verify isolation
- API keys: add → use → delete

## Implementation Timeline

**Critical Path: 5-7 days**

1. Auth + Database (1-2 days) ⚡
2. Blueprint API (1 day) ⚡
3. API Key Encryption (1 day)
4. Caching (1 day)
5. Marketplace (2 days)
6. Multi-Agent (1-2 days) ⚡
7. Rate Limiting (1 day)
8. Deployment (2 days) ⚡

**Total with testing: 10-14 days**

## Success Metrics

- Auth: 95% registration success rate
- Blueprints: <100ms CRUD operations
- Cache: >80% hit rate
- Marketplace: >50% users clone ≥1 blueprint
- API: <500ms p95 latency
- Deployment: 99.5% uptime
- Security: 0 plaintext API keys in logs

## Next Steps

1. Review and approve this spec
2. Start with Task 1: Install deployment tools
3. Follow tasks sequentially through Task 16
4. Deploy to staging (Task 15)
5. Deploy to production (Task 16)

## Questions?

- Architecture questions → See [design.md](./design.md)
- Implementation questions → See [tasks.md](./tasks.md)
- Deployment questions → See [action-plan.md](./action-plan.md)
