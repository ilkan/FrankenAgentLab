#!/bin/bash
set -e

# FrankenAgent Lab - Run Database Migration on Production
# This script creates a Cloud Run Job to run Alembic migrations

PROJECT_ID="frankenagent-prod"
REGION="us-central1"
DB_CONNECTION_NAME="frankenagent-prod:us-central1:frankenagent-db"
JOB_NAME="frankenagent-migration"

echo "🔄 Running database migration on production..."

# Use existing DATABASE_URL from Secret Manager
echo "✓ Using DATABASE_URL from Secret Manager"
DB_URL_SECRET="DATABASE_URL"

# Build and deploy the migration job
echo "📦 Building migration container..."
gcloud builds submit \
    --config=cloudbuild-migration.yaml \
    --project=$PROJECT_ID

echo "🚀 Creating Cloud Run Job..."
gcloud run jobs create $JOB_NAME \
    --image=gcr.io/$PROJECT_ID/frankenagent-migration:latest \
    --region=$REGION \
    --project=$PROJECT_ID \
    --set-cloudsql-instances=$DB_CONNECTION_NAME \
    --set-secrets=DATABASE_URL=$DB_URL_SECRET:latest \
    --max-retries=0 \
    --task-timeout=5m \
    2>/dev/null || \
gcloud run jobs update $JOB_NAME \
    --image=gcr.io/$PROJECT_ID/frankenagent-migration:latest \
    --region=$REGION \
    --project=$PROJECT_ID \
    --set-cloudsql-instances=$DB_CONNECTION_NAME \
    --set-secrets=DATABASE_URL=$DB_URL_SECRET:latest \
    --max-retries=0 \
    --task-timeout=5m

echo "▶️  Executing migration job..."
gcloud run jobs execute $JOB_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --wait

echo "✅ Migration completed!"
echo ""
echo "🔍 Check logs:"
echo "gcloud logging read 'resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME' --limit=50 --project=$PROJECT_ID"
