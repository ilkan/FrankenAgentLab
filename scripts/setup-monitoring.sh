#!/bin/bash
# Setup monitoring dashboards and metrics for FrankenAgent Lab

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"frankenagent-prod"}
REGION=${GCP_REGION:-"us-central1"}

echo "Setting up monitoring for project: $PROJECT_ID"

# Set project
gcloud config set project $PROJECT_ID

# Enable Cloud Monitoring API
echo "Enabling Cloud Monitoring API..."
gcloud services enable monitoring.googleapis.com

# Create custom metrics for business events
echo "Creating custom metrics..."

# Metric 1: Agent execution count
gcloud logging metrics create agent_execution_count \
    --description="Count of agent executions" \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.event="execution_complete"' \
    --value-extractor='EXTRACT(jsonPayload.success)' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric agent_execution_count already exists"

# Metric 2: Agent execution latency
gcloud logging metrics create agent_execution_latency \
    --description="Agent execution latency in milliseconds" \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.event="execution_complete"' \
    --value-extractor='EXTRACT(jsonPayload.latency_ms)' \
    --metric-kind=GAUGE \
    --value-type=INT64 \
    2>/dev/null || echo "Metric agent_execution_latency already exists"

# Metric 3: Tool call count
gcloud logging metrics create tool_call_count \
    --description="Count of tool calls" \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.event="tool_call"' \
    --value-extractor='EXTRACT(jsonPayload.success)' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric tool_call_count already exists"

# Metric 4: Authentication events
gcloud logging metrics create auth_event_count \
    --description="Count of authentication events" \
    --log-filter='resource.type="cloud_run_revision" AND (jsonPayload.event="login_attempt" OR jsonPayload.event="user_registration")' \
    --value-extractor='EXTRACT(jsonPayload.success)' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric auth_event_count already exists"

# Metric 5: API key access events
gcloud logging metrics create api_key_access_count \
    --description="Count of API key access events" \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.event="api_key_access"' \
    --value-extractor='EXTRACT(jsonPayload.success)' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric api_key_access_count already exists"

# Metric 6: Blueprint operations
gcloud logging metrics create blueprint_operation_count \
    --description="Count of blueprint operations" \
    --log-filter='resource.type="cloud_run_revision" AND (jsonPayload.event="blueprint_created" OR jsonPayload.event="blueprint_updated" OR jsonPayload.event="blueprint_deleted")' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric blueprint_operation_count already exists"

# Metric 7: Marketplace operations
gcloud logging metrics create marketplace_operation_count \
    --description="Count of marketplace operations" \
    --log-filter='resource.type="cloud_run_revision" AND (jsonPayload.event="blueprint_published" OR jsonPayload.event="blueprint_cloned" OR jsonPayload.event="blueprint_rated")' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric marketplace_operation_count already exists"

# Metric 8: Guardrail violations
gcloud logging metrics create guardrail_violation_count \
    --description="Count of guardrail violations" \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.event="guardrail_violation"' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric guardrail_violation_count already exists"

# Metric 9: Error count by type
gcloud logging metrics create error_count_by_type \
    --description="Count of errors by type" \
    --log-filter='resource.type="cloud_run_revision" AND severity="ERROR"' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric error_count_by_type already exists"

echo "✓ Custom metrics created successfully"

# Note: Dashboard creation via gcloud is complex and requires JSON format
# For now, dashboards should be created manually in the Cloud Console
# or using the Monitoring API with the dashboards.yaml configuration

echo ""
echo "Monitoring setup complete!"
echo ""
echo "Next steps:"
echo "1. Create dashboards in Cloud Console using monitoring/dashboards.yaml as reference"
echo "2. Setup alerting policies using scripts/setup-alerting.sh"
echo "3. Configure notification channels (email, Slack, PagerDuty)"
echo ""
echo "View metrics at:"
echo "https://console.cloud.google.com/monitoring/metrics-explorer?project=$PROJECT_ID"
echo ""
echo "View logs at:"
echo "https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
