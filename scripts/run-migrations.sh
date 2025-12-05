#!/bin/bash
# Run database migrations on Cloud SQL

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-frankenagent-prod}"
REGION="${GCP_REGION:-us-central1}"
DB_INSTANCE="${DB_INSTANCE:-frankenagent-db}"

echo "Running database migrations on Cloud SQL..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Instance: $DB_INSTANCE"

# Check if Cloud SQL Proxy is installed
if ! command -v cloud-sql-proxy &> /dev/null; then
    echo "Error: cloud-sql-proxy not found. Installing..."
    # macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
        chmod +x cloud-sql-proxy
        sudo mv cloud-sql-proxy /usr/local/bin/
    # Linux
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
        chmod +x cloud-sql-proxy
        sudo mv cloud-sql-proxy /usr/local/bin/
    fi
fi

# Get database URL from Secret Manager
echo "Fetching database credentials from Secret Manager..."
DATABASE_URL=$(gcloud secrets versions access latest --secret="DATABASE_URL" --project="$PROJECT_ID")

# Start Cloud SQL Proxy in background
echo "Starting Cloud SQL Proxy..."
cloud-sql-proxy "$PROJECT_ID:$REGION:$DB_INSTANCE" &
PROXY_PID=$!

# Wait for proxy to start
echo "Waiting for proxy to start..."
sleep 5

# Export database URL for Alembic
export DATABASE_URL

# Run Alembic migrations
echo "Running Alembic migrations..."
poetry run alembic upgrade head

# Check migration status
echo "Checking migration status..."
poetry run alembic current

# Kill proxy
echo "Stopping Cloud SQL Proxy..."
kill $PROXY_PID

echo "✓ Migrations completed successfully!"
echo ""
echo "To verify tables were created, run:"
echo "  gcloud sql connect $DB_INSTANCE --user=frankenagent --database=frankenagent"
echo "  \\dt"
