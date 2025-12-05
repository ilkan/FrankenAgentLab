# FrankenAgent Lab Platform Evolution - Action Plan

## Executive Summary

Transform FrankenAgent Lab from local MVP to production multi-tenant platform on GCP. 5-8 shippable steps, 1-2 days each. Critical path marked with ⚡.

---

## Step 1: Database Schema + User Auth ⚡ (CRITICAL PATH)
**Duration:** 1-2 days  
**Dependencies:** None  
**Owner:** Backend team

**Deliverables:**
- PostgreSQL schema with tables: users, blueprints, sessions, marketplace_listings
- JWT-based auth endpoints: POST /auth/register, POST /auth/login, POST /auth/refresh
- Middleware for token validation on protected routes
- Migration from SQLite to PostgreSQL for Agno memory

**Implementation:**
```sql
-- Core tables
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE blueprints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  blueprint_data JSONB NOT NULL,
  version INTEGER DEFAULT 1,
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_blueprints_user_id ON blueprints(user_id);
CREATE INDEX idx_blueprints_public ON blueprints(is_public) WHERE is_public = TRUE;
```

**Decisions:**
- ✅ DB: PostgreSQL on Cloud SQL (managed, auto-backups)
- ✅ Auth: JWT with 24h expiration, refresh tokens
- ✅ Password: bcrypt hashing with salt rounds=12

**Unknowns:**
- OAuth providers (Google, GitHub)? → Defer to Step 6
- Email verification? → Defer to Step 6

**Testing:**
- Unit tests for auth endpoints
- Integration test: register → login → protected route

---

## Step 2: Blueprint CRUD API ⚡ (CRITICAL PATH)
**Duration:** 1 day  
**Dependencies:** Step 1  
**Owner:** Backend team

**Deliverables:**
- POST /api/blueprints - Create/update blueprint (requires auth)
- GET /api/blueprints - List user's blueprints (requires auth)
- GET /api/blueprints/{id} - Get single blueprint (requires auth or public)
- DELETE /api/blueprints/{id} - Delete blueprint (requires auth + ownership)
- Update /api/agents/run to accept blueprint_id from database

**Implementation:**
```python
@app.post("/api/blueprints")
async def create_blueprint(
    blueprint: BlueprintCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate blueprint
    validation = validator.validate(blueprint.data)
    if not validation.valid:
        raise HTTPException(400, detail=validation.errors)
    
    # Save to DB
    db_blueprint = Blueprint(
        user_id=user.id,
        name=blueprint.name,
        blueprint_data=blueprint.data,
        version=1
    )
    db.add(db_blueprint)
    db.commit()
    return db_blueprint
```

**Decisions:**
- ✅ Versioning: Auto-increment on update
- ✅ Soft delete: Keep deleted blueprints for 30 days

**Testing:**
- CRUD operations for authenticated user
- Verify ownership checks prevent unauthorized access

---

## Step 3: Agent Compilation Cache (Redis)
**Duration:** 1 day  
**Dependencies:** Step 2  
**Owner:** Backend team

**Deliverables:**
- Redis cache for compiled Agno agents
- Cache key: `agent:{blueprint_id}:{version}`
- TTL: 1 hour for compiled agents
- Cache invalidation on blueprint update

**Implementation:**
```python
import redis
import pickle

class AgentCache:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=6379,
            decode_responses=False
        )
    
    def get(self, blueprint_id: str, version: int):
        key = f"agent:{blueprint_id}:{version}"
        data = self.redis.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    def set(self, blueprint_id: str, version: int, agent):
        key = f"agent:{blueprint_id}:{version}"
        self.redis.setex(key, 3600, pickle.dumps(agent))
```

**Decisions:**
- ✅ Cache: Redis (Memorystore on GCP)
- ✅ Serialization: pickle for Agno agents
- ⚠️ Alternative: Don't cache agents, cache only validation results (lighter)

**Unknowns:**
- Can Agno agents be pickled safely? → Test in dev
- Cache warming strategy? → Defer to monitoring

**Testing:**
- Cache hit/miss scenarios
- Performance: cached vs uncached execution

---

## Step 4: Marketplace API + Frontend
**Duration:** 2 days  
**Dependencies:** Step 2  
**Owner:** Full-stack team

**Deliverables:**
- POST /api/marketplace/publish - Publish blueprint (requires auth)
- GET /api/marketplace - Browse public blueprints (no auth)
- GET /api/marketplace/search?q={query} - Search marketplace
- POST /api/marketplace/{id}/clone - Clone to user's blueprints (requires auth)
- Frontend: Marketplace tab with grid view, search, clone button

**Implementation:**
```python
@app.post("/api/marketplace/publish")
async def publish_to_marketplace(
    blueprint_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    blueprint = db.query(Blueprint).filter(
        Blueprint.id == blueprint_id,
        Blueprint.user_id == user.id
    ).first()
    
    if not blueprint:
        raise HTTPException(404)
    
    blueprint.is_public = True
    db.commit()
    return {"status": "published"}
```

**Decisions:**
- ✅ Search: PostgreSQL full-text search (pg_trgm extension)
- ✅ Ratings: Defer to Step 6 (add ratings table later)

**Testing:**
- Publish → browse → clone workflow
- Search relevance

---

## Step 5: Multi-Agent Selector + Session Management ⚡ (CRITICAL PATH)
**Duration:** 1-2 days  
**Dependencies:** Step 2  
**Owner:** Full-stack team

**Deliverables:**
- Frontend: Dropdown to select active agent from user's blueprints
- Backend: Session table with agent_id foreign key
- GET /api/sessions - List user's sessions with last message preview
- POST /api/sessions - Create new session for specific agent
- Update chat to maintain separate history per agent

**Implementation:**
```typescript
// Frontend
const [activeAgentId, setActiveAgentId] = useState<string>();
const [userBlueprints, setUserBlueprints] = useState<Blueprint[]>([]);

useEffect(() => {
  fetch('/api/blueprints', { headers: { Authorization: `Bearer ${token}` }})
    .then(r => r.json())
    .then(setUserBlueprints);
}, []);

const handleAgentSwitch = (agentId: string) => {
  setActiveAgentId(agentId);
  // Create new session for this agent
  fetch('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({ blueprint_id: agentId })
  });
};
```

**Decisions:**
- ✅ Session storage: PostgreSQL (not Redis) for persistence
- ✅ History: Store in sessions table as JSONB array

**Testing:**
- Switch between 3 agents, verify separate histories
- Session persistence across page refresh

---

## Step 6: API Gateway + Rate Limiting
**Duration:** 1 day  
**Dependencies:** Step 1  
**Owner:** DevOps + Backend

**Deliverables:**
- Cloud Endpoints or API Gateway config
- Rate limiting: 100 req/min per user, 1000 req/day
- Token quota tracking in users table
- Middleware to check quotas before execution

**Implementation:**
```yaml
# api-gateway-config.yaml
swagger: "2.0"
info:
  title: FrankenAgent Lab API
  version: "1.0"
host: api.frankenagent.dev
x-google-endpoints:
  - name: api.frankenagent.dev
    allowCors: true
paths:
  /api/agents/run:
    post:
      x-google-quota:
        metricCosts:
          agent_executions: 1
```

**Decisions:**
- ⚠️ Gateway: Cloud Endpoints vs Kong vs custom middleware
  - Recommendation: Start with FastAPI middleware (simpler), migrate to Cloud Endpoints later
- ✅ Rate limit storage: Redis (fast lookups)

**Unknowns:**
- Token quota calculation (per model)? → Use fixed cost per execution for MVP
- Quota reset period? → Daily at midnight UTC

**Testing:**
- Trigger rate limit, verify 429 response
- Verify Retry-After header

---

## Step 7: GCP Deployment ⚡ (CRITICAL PATH)
**Duration:** 2 days  
**Dependencies:** Steps 1-6  
**Owner:** DevOps

**Deliverables:**
- Cloud Run service for backend (auto-scale 0-10)
- Cloud Storage + CDN for frontend static files
- Cloud SQL PostgreSQL instance (db-f1-micro for MVP)
- Memorystore Redis (1GB for MVP)
- Secret Manager for API keys (OPENAI_API_KEY, TAVILY_API_KEY)
- Cloud Build CI/CD pipeline
- Custom domain with SSL

**Implementation:**
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/frankenagent-backend', '.']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/frankenagent-backend']
  
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'frankenagent-backend'
      - '--image=gcr.io/$PROJECT_ID/frankenagent-backend'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
```

**Decisions:**
- ✅ Region: us-central1 (lowest latency for US)
- ✅ Scaling: Min 0, Max 10 instances (cost control)
- ✅ Database: db-f1-micro (1 vCPU, 3.75GB RAM) - upgrade later

**Unknowns:**
- Cold start time for Cloud Run? → Monitor and optimize
- Database connection pooling? → Use SQLAlchemy pool (size=5)

**Testing:**
- Deploy to staging environment
- Load test: 100 concurrent users
- Verify auto-scaling behavior

---

## Step 8: Monitoring + Observability (Optional but Recommended)
**Duration:** 1 day  
**Dependencies:** Step 7  
**Owner:** DevOps

**Deliverables:**
- Cloud Logging for all services
- Cloud Monitoring dashboards (request rate, latency, errors)
- Alerts: Error rate >5%, latency >2s, database CPU >80%
- Uptime checks on /health endpoint

**Implementation:**
```python
# Structured logging
import logging
from google.cloud import logging as cloud_logging

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger(__name__)
logger.info("Agent executed", extra={
    "user_id": user.id,
    "blueprint_id": blueprint.id,
    "duration_ms": duration
})
```

**Decisions:**
- ✅ Logging: Cloud Logging (native GCP integration)
- ✅ Metrics: Cloud Monitoring (no additional cost)

**Testing:**
- Trigger alert conditions, verify notifications
- Review dashboard during load test

---

## Critical Path Summary

```
Step 1 (Auth + DB) → Step 2 (Blueprint API) → Step 5 (Multi-Agent) → Step 7 (Deploy)
        ⚡                    ⚡                      ⚡                    ⚡
```

**Total Critical Path Duration:** 5-7 days

**Parallel Work:**
- Step 3 (Cache) can run parallel to Step 4 (Marketplace)
- Step 6 (Rate Limiting) can run parallel to Step 5

---

## Key Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | PostgreSQL (Cloud SQL) | Managed, ACID, JSON support |
| Auth | JWT + bcrypt | Stateless, industry standard |
| Cache | Redis (Memorystore) | Fast, managed, pub/sub support |
| Gateway | FastAPI middleware → Cloud Endpoints | Start simple, migrate later |
| Deployment | Cloud Run | Serverless, auto-scale, cost-effective |
| Frontend Hosting | Cloud Storage + CDN | Static files, global distribution |

---

## Unknowns & Risks

1. **Agno agent serialization** - Can compiled agents be cached safely?
   - Mitigation: Test pickle/dill in dev, fallback to validation-only cache

2. **Cold start latency** - Cloud Run cold starts may impact UX
   - Mitigation: Keep 1 min instance warm, optimize container size

3. **Database connection limits** - Cloud SQL has connection limits
   - Mitigation: Use connection pooling (SQLAlchemy), monitor usage

4. **Token quota calculation** - How to fairly allocate LLM usage?
   - Mitigation: Start with fixed cost per execution, refine with usage data

5. **Search performance** - PostgreSQL full-text search may be slow at scale
   - Mitigation: Add indexes, consider Algolia/Elasticsearch later

---

## Cost Estimate (Monthly, MVP Scale)

- Cloud Run (backend): $20 (100K requests)
- Cloud SQL (db-f1-micro): $25
- Memorystore Redis (1GB): $30
- Cloud Storage + CDN: $5
- Secret Manager: $1
- **Total: ~$80/month** (excluding LLM API costs)

---

## Success Metrics

- Auth: 95% of registrations complete successfully
- Blueprints: <100ms CRUD operations
- Cache: >80% hit rate for compiled agents
- Marketplace: >50% of users clone at least 1 blueprint
- Multi-agent: Users switch agents avg 3x per session
- API: <500ms p95 latency for /api/agents/run
- Deployment: 99.5% uptime, <2s cold start

---

## Next Steps After MVP

1. OAuth providers (Google, GitHub)
2. Email verification + password reset
3. Blueprint versioning with rollback
4. Collaborative editing (share blueprints with team)
5. Usage analytics dashboard
6. Webhook integrations
7. Streaming responses (SSE)
8. Multi-region deployment
