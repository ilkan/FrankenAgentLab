# Deployment Scripts

This directory contains scripts for setting up and deploying FrankenAgent Lab to Google Cloud Platform (GCP).

## Prerequisites

- macOS or Linux operating system
- Homebrew (macOS) or curl (Linux)
- Node.js and npm (for Firebase CLI)
- Active Google Cloud account with billing enabled

## Setup Order

Follow these scripts in order:

### 1. Install Google Cloud CLI

```bash
./scripts/install-gcp-cli.sh
```

This script:
- Detects your operating system (macOS or Linux)
- Installs gcloud CLI via Homebrew (macOS) or direct download (Linux)
- Verifies the installation

After installation, authenticate:
```bash
gcloud auth login
gcloud auth application-default login
```

### 2. Install Firebase CLI

```bash
./scripts/install-firebase-cli.sh
```

This script:
- Checks for Node.js/npm installation
- Installs Firebase CLI globally via npm
- Verifies the installation

After installation, authenticate:
```bash
firebase login
```

### 3. Setup GCP Project

```bash
./scripts/setup-gcp-project.sh
```

This script:
- Creates a new GCP project or uses an existing one
- Enables required APIs (Cloud Run, Cloud SQL, Redis, Secret Manager, etc.)
- Updates your `.env` file with project configuration

**Important:** You must enable billing on your GCP project before proceeding. The script will prompt you to do this.

### 4. Setup Infrastructure

```bash
./scripts/setup-infrastructure.sh
```

This script provisions all required GCP infrastructure:
- **Cloud SQL PostgreSQL instance** - Database for users, blueprints, sessions
- **Memorystore Redis instance** - Cache for compiled agents and rate limiting
- **Cloud Storage bucket** - Static hosting for frontend assets
- **Cloud KMS keyring and key** - Encryption for user API keys
- **Secret Manager secrets** - Secure storage for DATABASE_URL and REDIS_HOST

The script will:
1. Create all infrastructure resources (takes 10-15 minutes)
2. Configure database and Redis instances
3. Set up storage bucket with CORS and public access
4. Create KMS encryption key for API key security
5. Store connection strings in Secret Manager
6. Update your `.env` file with resource details

**Note:** This script is idempotent - you can run it multiple times safely.

### 5. Add Platform Secrets

```bash
./scripts/add-secrets.sh
```

This script helps you securely add API keys to Secret Manager:
- **OPENAI_API_KEY** - For LLM provider access
- **TAVILY_API_KEY** - For web search tool
- **JWT_SECRET_KEY** - For authentication token signing

The script will prompt you for each key and store them securely in Secret Manager.

## Environment Variables

After running the setup scripts, your `.env` file will contain:

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GCP_ZONE=us-central1-a

# Database Configuration
DATABASE_URL=postgresql://...

# Redis Configuration
REDIS_HOST=10.0.0.3
REDIS_PORT=6379

# JWT Configuration
JWT_SECRET_KEY=your-secret-key
```

## Troubleshooting

### gcloud command not found

After installation, you may need to restart your terminal or source the path file:

**macOS (Homebrew):**
```bash
source "$(brew --prefix)/share/google-cloud-sdk/path.bash.inc"
```

**Linux:**
```bash
source ~/google-cloud-sdk/path.bash.inc
```

### Permission denied when running scripts

Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### Billing not enabled error

1. Visit the [GCP Console](https://console.cloud.google.com/billing)
2. Link a billing account to your project
3. Re-run the setup script

### API enablement fails

Some APIs may take a few minutes to enable. If you see errors:
1. Wait 2-3 minutes
2. Re-run the script
3. Or manually enable APIs in the [GCP Console](https://console.cloud.google.com/apis)

## Manual Setup (Alternative)

If the scripts don't work for your environment, you can set up manually:

1. **Install gcloud CLI:** https://cloud.google.com/sdk/docs/install
2. **Install Firebase CLI:** `npm install -g firebase-tools`
3. **Create GCP project:** https://console.cloud.google.com/projectcreate
4. **Enable APIs:** Visit the APIs & Services page in GCP Console
5. **Update .env:** Copy values from `.env.example` and fill in your project details

## Security Notes

- Never commit `.env` file to version control
- Rotate JWT_SECRET_KEY before production deployment
- Use Secret Manager for sensitive values in production
- Enable audit logging for production environments

## Next Steps

After completing these setup scripts:

1. ✅ Run `./scripts/setup-infrastructure.sh` - Provision GCP infrastructure
2. ✅ Run `./scripts/add-secrets.sh` - Add API keys to Secret Manager
3. Run database migrations (Task 3) - Create database schema
4. Deploy backend to Cloud Run (Task 13) - Deploy API server
5. Deploy frontend to Cloud Storage (Task 13) - Deploy web interface
