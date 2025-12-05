# 🧟 FrankenAgent Lab

A production-ready AI agent platform that lets you compose intelligent agents from modular components using declarative YAML blueprints. Built on the powerful Agno framework with a complete visual builder, REST API, and marketplace.

![Version](https://img.shields.io/badge/version-1.0.0-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-blue)
![Status](https://img.shields.io/badge/status-production-brightgreen)

## 🎯 What is FrankenAgent Lab?

FrankenAgent Lab is a production-ready platform for building, deploying, and managing AI agents at scale. Using an intuitive body-parts metaphor, you can compose sophisticated agents from modular components:

- **Head** 🧠 = LLM brain (model, provider, system prompt, temperature)
- **Arms** 🦾 = Tools and external integrations (web search, APIs, MCP servers)
- **Legs** 🦿 = Execution mode (single agent, workflow, multi-agent team)
- **Heart** ❤️ = Memory and knowledge base (conversation history, RAG)
- **Spine** 🦴 = Guardrails and safety constraints (rate limits, timeouts)

**Three Ways to Build:**
1. **Visual Builder** - Drag-and-drop interface with real-time preview
2. **YAML/JSON** - Declarative configuration files
3. **REST API** - Programmatic agent creation and management

**Deploy Anywhere:**
- Local development with SQLite
- Production on Google Cloud Platform (Cloud Run + Cloud SQL + Redis)
- Custom domain with SSL/TLS
- Auto-scaling from 1-20 instances

## ✨ Features

### 🎨 Visual Builder
- **Drag-and-drop canvas** - Build agents visually with React + TypeScript
- **Real-time preview** - See YAML/JSON as you build
- **Live validation** - Instant feedback on configuration
- **Auto-save** - Never lose your work
- **Export ready-to-use blueprints** - Download and deploy immediately

### 🔐 Enterprise Security
- **Multi-tenant authentication** - JWT tokens with secure session management
- **OAuth integration** - Google and GitHub single sign-on
- **Password reset** - Email-based recovery via Brevo
- **API key vault** - Encrypted storage with Cloud KMS (AES-256-GCM)
- **Rate limiting** - Per-user and global request limits
- **Audit logging** - Complete activity tracking

### 🚀 Production Infrastructure
- **Auto-scaling** - Cloud Run with 1-20 instances
- **Database** - PostgreSQL (Cloud SQL) with connection pooling
- **Caching** - Redis (Memorystore) for sessions and rate limits
- **Custom domains** - SSL/TLS with automatic certificate management
- **Monitoring** - Cloud Logging with error tracking and alerts
- **CI/CD** - Automated deployment with Cloud Build

### 🏪 Marketplace
- **Public blueprint library** - Share and discover agents
- **One-click cloning** - Customize existing blueprints
- **Rating system** - Community-driven quality scores
- **Categories and tags** - Organized discovery
- **Featured blueprints** - Curated selections

### 🔧 Developer Tools
- **CLI interface** - Quick testing from terminal
- **REST API** - Complete programmatic access
- **Execution tracing** - Detailed tool call logs with timing
- **Multiple tools** - Web search, HTTP APIs, MCP servers, and more
- **Guardrails** - Built-in safety constraints
- **Session management** - Persistent conversation history

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry (Python package manager)
- Node.js 18+ (for frontend)
- OpenAI API key
- Tavily API key (for web search)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/frankenagent-lab.git
cd frankenagent-lab

# Install backend dependencies
poetry install

# Install frontend dependencies
cd frontend
npm install
cd ..

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Configuration

Create a `.env` file with your API keys:

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-your-openai-key-here
TAVILY_API_KEY=tvly-your-tavily-key-here

# Email Service (Optional - for password reset)
BREVO_API_KEY=xkeysib-your-brevo-api-key-here
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your App Name

# JWT Secret
JWT_SECRET_KEY=your-secret-key-here

# OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

#### Database configuration

The backend automatically selects the correct database connection based on `ENVIRONMENT`:

- **Development / Test**: set `LOCAL_DATABASE_URL` (defaults to `sqlite:///./frankenagent.db`).
- **Production**: set `PRODUCTION_DATABASE_URL` **or** the Cloud SQL variables:
  - `CLOUD_SQL_CONNECTION_NAME=project:region:instance`
  - `DB_USER`, `DB_PASSWORD`, `DB_NAME`

When running on Cloud Run, use the Unix socket connection string provided above to talk to Cloud SQL securely without exposing a public address.

### Run the Visual Builder (Recommended)

```bash
# Start the frontend visual builder
cd frontend
npm run dev
# Open http://localhost:3000

# Build your agent visually, export blueprint, then run:
poetry run frankenagent run blueprints/your_agent.yaml "Hello"
```

### Run the Web UI (Alternative)

```bash
# Start the API server
poetry run uvicorn frankenagent.api.server:app --reload

# Open in browser
open http://localhost:8000/static/index.html
```

### Use the CLI

```bash
# List available blueprints
poetry run frankenagent list

# Run an agent
poetry run frankenagent run blueprints/simple_assistant.yaml "What's the weather?"
```

## 🌐 Production Deployment

FrankenAgent Lab is production-ready and deployed on Google Cloud Platform with enterprise-grade infrastructure.

### Quick Deploy (5 Commands)

```bash
# 1. Set your GCP project
export GCP_PROJECT_ID="your-project-id"

# 2. Enable required APIs
gcloud services enable run.googleapis.com sql-component.googleapis.com \
  redis.googleapis.com cloudkms.googleapis.com secretmanager.googleapis.com

# 3. Create infrastructure
gcloud sql instances create frankenagent-db --tier=db-f1-micro --region=us-central1
gcloud redis instances create frankenagent-cache --size=1 --region=us-central1

# 4. Deploy backend
gcloud run deploy frankenagent-backend --source . --region=us-central1 \
  --allow-unauthenticated --min-instances=1 --max-instances=20

# 5. Setup custom domain (optional)
gcloud run domain-mappings create --service=frankenagent-backend \
  --domain=app.yourdomain.com --region=us-central1
```

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer (SSL)                  │
│                  app.yourdomain.com                     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Cloud Run (Auto-scaling)                   │
│         FastAPI + Agno Runtime (1-20 instances)         │
└─────┬──────────────────────────────────────────┬────────┘
      │                                          │
┌─────▼──────────────┐              ┌───────────▼─────────┐
│   Cloud SQL        │              │   Memorystore       │
│   (PostgreSQL)     │              │   (Redis)           │
│   - Users          │              │   - Sessions        │
│   - Blueprints     │              │   - Rate limits     │
│   - Sessions       │              │   - Cache           │
└────────────────────┘              └─────────────────────┘
         │
┌────────▼────────────┐
│   Cloud KMS         │
│   (API Keys)        │
│   AES-256-GCM       │
└─────────────────────┘
```

### Production Features

**✅ Fully Implemented:**
- Multi-tenant authentication (JWT + OAuth)
- Google & GitHub OAuth integration
- Password reset via email (Brevo)
- PostgreSQL database with connection pooling
- Redis caching for sessions and rate limits
- API key encryption with Cloud KMS
- Rate limiting (per-user and global)
- Auto-scaling (1-20 instances)
- Custom domain with SSL/TLS
- Comprehensive monitoring and logging
- Agent marketplace with ratings
- Session management with conversation history
- User activity tracking and audit logs

### Cost Estimate

**~$310-350/month** for 10,000 requests/day:
- **Cloud Run**: ~$50/month (1-20 instances)
- **Cloud SQL**: ~$100/month (db-f1-micro)
- **Redis**: ~$150/month (1GB)
- **Storage**: ~$10/month
- **Load Balancer**: ~$43/month (custom domain)
- **KMS**: ~$1/month

*Excludes LLM API costs (OpenAI, Anthropic, etc.)*

### Monitoring

```bash
# View logs
gcloud run services logs read frankenagent-backend --region=us-central1 --follow

# Check metrics
gcloud monitoring dashboards list

# View errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=50
```

## 🧱 Backend Architecture

**Core Components:**
- **FastAPI + Agno runtime** for orchestrating YAML blueprints
- **Blueprint Compiler** validates and transforms YAML → Agno Agent/Workflow/Team
- **Execution Orchestrator** manages agent runs with tool tracing and guardrails
- **Session Manager** handles conversation history and context

**Data Layer:**
- **SQLAlchemy ORM** with unified schema for local (SQLite) and production (PostgreSQL)
- **User activity ledger** for profile timelines and audit trails
- **Redis caching** for rate limiting and session management
- **Alembic migrations** for schema versioning

**Security:**
- **JWT authentication** with secure token management
- **OAuth integration** (Google & GitHub)
- **API key vault** with Cloud KMS envelope encryption (AES-256-GCM)
- **Rate limiting** per-user and global limits
- **Password reset** via email (Brevo integration)

**Services:**
- **Marketplace service** for blueprint sharing and cloning
- **Blueprint service** for CRUD operations with validation
- **User API key service** for encrypted key storage
- **Activity service** for audit logging
- **Email service** for transactional emails

See `frankenagent/db/models.py` for the complete database schema.

## 📋 Example Blueprint

Create a simple agent in `blueprints/my_agent.yaml`:

```yaml
name: "My Assistant"
description: "A helpful AI assistant"
version: "1.0"

# HEAD = LLM Configuration
head:
  model: "gpt-4o-mini"
  provider: "openai"
  system_prompt: "You are a helpful assistant."
  temperature: 0.7

# ARMS = Tools
arms:
  - type: "tavily_search"
    config:
      max_results: 5
      search_depth: "basic"
  
  - type: "http_tool"
    config:
      name: "API Client"
      description: "Make HTTP requests to external APIs"
      base_url: "https://api.example.com"
      default_headers:
        Authorization: "Bearer YOUR_TOKEN"
      timeout: 30

# LEGS = Execution Mode
legs:
  execution_mode: "single_agent"

# HEART = Memory
heart:
  memory:
    type: "conversation"
    max_messages: 20

# SPINE = Guardrails
spine:
  max_tool_calls: 10
  timeout_seconds: 60
```

## 🎨 Web UI

The web UI provides:

- 📋 Blueprint browser with all available agents
- 💬 Real-time chat interface
- 🔧 Detailed execution traces
- ⏱️ Performance metrics
- 🎨 Beautiful dark theme with Frankenstein aesthetic

![Web UI Screenshot](docs/screenshot.png)

## 🔌 API Endpoints

### Authentication

```bash
# Register
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}

# OAuth Login
POST /api/auth/oauth/login
{
  "provider": "google",
  "code": "auth_code",
  "redirect_uri": "http://localhost:3000"
}

# Get Current User
GET /api/auth/me
Authorization: Bearer <token>

# Password Reset
POST /api/auth/forgot-password
{
  "email": "user@example.com"
}

POST /api/auth/reset-password
{
  "token": "reset_token",
  "new_password": "new_secure_password"
}
```

### Blueprints

```bash
# List User Blueprints
GET /api/blueprints
Authorization: Bearer <token>

# Get Blueprint
GET /api/blueprints/{blueprint_id}
Authorization: Bearer <token>

# Create Blueprint
POST /api/blueprints
Authorization: Bearer <token>
{
  "name": "My Agent",
  "description": "Description",
  "blueprint_data": {...}
}

# Update Blueprint
PUT /api/blueprints/{blueprint_id}
Authorization: Bearer <token>
{
  "name": "Updated Name",
  "blueprint_data": {...}
}

# Delete Blueprint
DELETE /api/blueprints/{blueprint_id}
Authorization: Bearer <token>

# Validate Blueprint
POST /api/blueprints/validate-and-compile
{
  "blueprint": {...},
  "compile": true
}
```

### Agent Execution

```bash
# Run Agent
POST /api/agents/run
Authorization: Bearer <token>
{
  "blueprint_id": "uuid",
  "message": "Hello!",
  "session_id": "optional_session_id"
}

# Get Execution Logs
GET /api/agents/logs?session_id=<session_id>
```

### Sessions

```bash
# List Sessions
GET /api/sessions
Authorization: Bearer <token>

# Get Session
GET /api/sessions/{session_id}
Authorization: Bearer <token>

# Delete Session
DELETE /api/sessions/{session_id}
Authorization: Bearer <token>
```

### Marketplace

```bash
# List Marketplace Blueprints
GET /api/marketplace/blueprints

# Get Marketplace Blueprint
GET /api/marketplace/blueprints/{blueprint_id}

# Clone Marketplace Blueprint
POST /api/marketplace/blueprints/{blueprint_id}/clone
Authorization: Bearer <token>
```

### User Management

```bash
# Get User Profile
GET /api/users/me
Authorization: Bearer <token>

# Update Profile
PUT /api/users/me
Authorization: Bearer <token>
{
  "full_name": "John Doe",
  "bio": "AI enthusiast"
}

# Get Activity Timeline
GET /api/users/me/activity
Authorization: Bearer <token>
```

### API Keys

```bash
# List API Keys
GET /api/keys
Authorization: Bearer <token>

# Create API Key
POST /api/keys
Authorization: Bearer <token>
{
  "provider": "openai",
  "key_name": "My OpenAI Key",
  "api_key": "sk-..."
}

# Delete API Key
DELETE /api/keys/{key_id}
Authorization: Bearer <token>
```

## 🔧 Available Tools (Arms)

### Tavily Search
Web search powered by Tavily API.

```yaml
- type: "tavily_search"
  config:
    max_results: 5          # Number of results (1-10)
    search_depth: "basic"   # "basic" or "advanced"
```

### HTTP Tool
Make HTTP requests to external APIs (GET, POST, PUT, DELETE, PATCH).

```yaml
- type: "http_tool"
  config:
    name: "API Client"                    # Tool name
    description: "Make API requests"      # Tool description
    base_url: "https://api.example.com"   # Optional base URL
    default_headers:                      # Optional default headers
      Authorization: "Bearer token"
      Content-Type: "application/json"
    timeout: 30                           # Request timeout in seconds
```

### MCP (Model Context Protocol) Tool
Connect to MCP servers for extended functionality.

```yaml
- type: "mcp_tool"
  config:
    name: "AWS Docs"
    description: "Search AWS documentation"
    transport: "streamable-http"
    url: "https://mcp-server.example.com"
```

**Supported Transports:**
- `stdio` - Standard input/output (local servers)
- `sse` - Server-Sent Events
- `streamable-http` - HTTP with streaming support

**Example MCP Servers:**
- AWS Documentation
- GitHub API
- Google Calendar (via Pipedream)
- Filesystem access
- Custom MCP servers

See `blueprints/mcp_aws_docs_agent.yaml` and `blueprints/http_api_agent.yaml` for complete examples.

## 📚 Documentation

### API Documentation
- **Swagger UI**: http://localhost:8000/docs - Interactive API explorer
- **ReDoc**: http://localhost:8000/redoc - API reference documentation

### Code Documentation
- **Blueprint Schema**: `frankenagent/config/schema.py` - Complete YAML/JSON schema
- **Database Models**: `frankenagent/db/models.py` - SQLAlchemy models
- **API Routes**: `frankenagent/api/routes/` - All REST endpoints

### Architecture
- **Backend**: See `frankenagent/` directory structure
- **Frontend**: See `frontend/src/` directory structure
- **Database**: See `alembic/versions/` for migrations

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           User Interfaces               │
│  CLI  │  HTTP API  │  Web UI            │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│        Runtime Service                  │
│  - Load Blueprint                       │
│  - Compile to Agno Agent                │
│  - Execute with Tracing                 │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│      Blueprint Compiler                 │
│  - Validate Schema                      │
│  - Build Tools                          │
│  - Apply Guardrails                     │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Agno Framework                  │
│  - Agent Execution                      │
│  - Tool Management                      │
└─────────────────────────────────────────┘
```

## 🛠️ Built With

- [Agno](https://github.com/agno-agi/agno) - AI agent framework
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Pydantic](https://pydantic.dev/) - Data validation
- [Poetry](https://python-poetry.org/) - Dependency management
- [Click](https://click.palletsprojects.com/) - CLI framework

## 📦 Project Structure

```
frankenagent-lab/
├── frontend/              # Visual builder (React + TypeScript)
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── stores/       # State management (Zustand)
│   │   ├── utils/        # Blueprint converter
│   │   └── types/        # TypeScript types
│   └── ARCHITECTURE.md   # Frontend documentation
├── frankenagent/          # Backend (Python)
│   ├── config/           # Blueprint schema and loading
│   ├── compiler/         # Blueprint → Agno compilation
│   ├── tools/            # Tool registry
│   ├── runtime/          # Execution and tracing
│   ├── cli/              # CLI interface
│   ├── api/              # FastAPI server
│   └── ui/               # Web UI (alternative)
├── blueprints/           # Agent blueprints (YAML/JSON)
├── tests/                # Test suite
├── .kiro/                # Kiro IDE configuration
└── pyproject.toml        # Project dependencies
```

## 🎯 Example Blueprints

The project includes three example blueprints:

1. **simple_assistant.yaml** - Single agent with web search
2. **research_workflow.yaml** - Multi-tool research agent
3. **team_analyzer.yaml** - Agent with web search + Python calculator

## 🔒 Security Notes

- API keys are loaded from environment variables
- Never commit `.env` file to version control
- Guardrails enforce execution limits
- Input validation on all endpoints

## 🎨 Visual Builder

Build agents visually with our drag-and-drop interface:

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

**Features:**
- 🎨 Drag & drop components (Head, Arms, Legs, Heart, Spine)
- 👁️ Live YAML/JSON preview
- ✅ Real-time validation
- 💾 Auto-save to local storage
- 📥 Export ready-to-use blueprints
- 🎯 Template library with examples

## 🏗️ Technology Stack

### Backend
- **Framework**: FastAPI + Agno (AI agent orchestration)
- **Database**: PostgreSQL (Cloud SQL) with SQLAlchemy ORM
- **Cache**: Redis (Memorystore) for sessions and rate limiting
- **Authentication**: JWT tokens + OAuth 2.0 (Google, GitHub)
- **Email**: Brevo API for transactional emails
- **Encryption**: Cloud KMS with AES-256-GCM envelope encryption
- **Migrations**: Alembic for schema versioning

### Frontend
- **Framework**: React 18 + TypeScript
- **State Management**: Zustand
- **UI Components**: Custom component library
- **Build Tool**: Vite
- **Styling**: CSS Modules with dark theme

### Infrastructure
- **Compute**: Cloud Run (serverless containers)
- **Database**: Cloud SQL (PostgreSQL 14)
- **Cache**: Memorystore (Redis 7)
- **Storage**: Cloud Storage for static assets
- **Security**: Cloud KMS for encryption, Secret Manager for credentials
- **Monitoring**: Cloud Logging + Cloud Monitoring
- **CI/CD**: Cloud Build with automated deployments

### AI & Tools
- **LLM Providers**: OpenAI, Anthropic, Google, Groq
- **Web Search**: Tavily API
- **MCP Support**: Model Context Protocol for tool integration
- **Vector DB**: LanceDB for knowledge bases (optional)

## 🚦 Getting Started

### 1. Local Development

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/frankenagent-lab.git
cd frankenagent-lab
poetry install

# Configure environment
cp .env.example .env
# Add your API keys to .env

# Run migrations
poetry run alembic upgrade head

# Start backend
poetry run uvicorn frankenagent.api.server:app --reload

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### 2. Create Your First Agent

**Option A: Visual Builder**
1. Open http://localhost:3000
2. Drag components to canvas
3. Configure settings
4. Export blueprint

**Option B: YAML File**
```yaml
name: "My First Agent"
head:
  model: "gpt-4o-mini"
  provider: "openai"
  system_prompt: "You are a helpful assistant."
arms:
  - type: "tavily_search"
legs:
  execution_mode: "single_agent"
```

**Option C: REST API**
```bash
curl -X POST http://localhost:8000/api/blueprints \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Agent", "blueprint_data": {...}}'
```

### 3. Run Your Agent

```bash
# CLI
poetry run frankenagent run blueprints/my_agent.yaml "Hello!"

# API
curl -X POST http://localhost:8000/api/agents/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"blueprint_id": "uuid", "message": "Hello!"}'

# Web UI
# Open http://localhost:8000/static/index.html
```

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Development Guidelines:**
- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Add tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Agno Framework](https://github.com/agno-agi/agno)** - Powerful AI agent orchestration
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern web framework
- **[React](https://react.dev/)** - UI library
- **[Google Cloud Platform](https://cloud.google.com/)** - Infrastructure
- **[Kiro IDE](https://kiro.dev)** - Development environment

## 📞 Support & Community

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/frankenagent-lab/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/frankenagent-lab/discussions)
- **Documentation**: Check `/docs` and API docs at http://localhost:8000/docs
- **Examples**: Review blueprints in `blueprints/` directory

## 🗺️ Roadmap

- [ ] Multi-modal support (images, audio, video)
- [ ] Advanced workflow builder with conditional logic
- [ ] Team collaboration features
- [ ] Webhook integrations
- [ ] Custom tool marketplace
- [ ] Mobile app (iOS/Android)
- [ ] Enterprise SSO (SAML, LDAP)
- [ ] Advanced analytics dashboard

---

**Built with ⚡ by developers, for developers**

🧟 **Assemble your AI agents, one body part at a time!**

*FrankenAgent Lab - Where AI agents come to life*
