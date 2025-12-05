# FrankenAgent Lab Monitoring

This directory contains monitoring configuration for FrankenAgent Lab deployed on Google Cloud Platform.

## Overview

The monitoring setup includes:

1. **Custom Metrics** - Business and application metrics from structured logs
2. **Dashboards** - Pre-configured dashboards for request, infrastructure, and business metrics
3. **Alerting** - Alert policies for critical conditions
4. **Log-based Metrics** - Metrics derived from application logs

## Dashboards

### 1. Request Metrics Dashboard

Monitors HTTP request performance:

- **Request Rate**: Requests per second over time
- **Response Latency**: p50, p95, p99 latency percentiles
- **Error Rate**: Percentage of failed requests
- **Status Code Distribution**: Breakdown of 2xx, 4xx, 5xx responses

### 2. Infrastructure Dashboard

Monitors GCP infrastructure health:

- **Database Connection Pool**: Active PostgreSQL connections
- **Database CPU Usage**: Cloud SQL CPU utilization (threshold: 80%)
- **Redis Cache Hit Rate**: Percentage of cache hits
- **Cloud Run Instances**: Number of active container instances
- **Database Memory**: Cloud SQL memory utilization
- **Redis Memory**: Memorystore memory usage

### 3. Business Metrics Dashboard

Tracks application usage and business KPIs:

- **Active Users**: Unique users in the last hour
- **Agent Executions**: Total agent runs
- **Blueprints Created**: New blueprints in last 24h
- **Marketplace Clones**: Blueprint clones from marketplace
- **Average Execution Latency**: Mean agent execution time

## Custom Metrics

The following custom metrics are created from structured logs:

| Metric Name | Description | Type | Source Event |
|-------------|-------------|------|--------------|
| `agent_execution_count` | Count of agent executions | DELTA | `execution_complete` |
| `agent_execution_latency` | Agent execution latency (ms) | GAUGE | `execution_complete` |
| `tool_call_count` | Count of tool invocations | DELTA | `tool_call` |
| `auth_event_count` | Authentication events | DELTA | `login_attempt`, `user_registration` |
| `api_key_access_count` | API key operations | DELTA | `api_key_access` |
| `blueprint_operation_count` | Blueprint CRUD operations | DELTA | `blueprint_created`, etc. |
| `marketplace_operation_count` | Marketplace operations | DELTA | `blueprint_published`, etc. |
| `guardrail_violation_count` | Guardrail violations | DELTA | `guardrail_violation` |
| `error_count_by_type` | Errors by type | DELTA | ERROR severity logs |

## Setup Instructions

### 1. Create Custom Metrics

Run the monitoring setup script:

```bash
./scripts/setup-monitoring.sh
```

This will:
- Enable Cloud Monitoring API
- Create custom log-based metrics
- Configure metric descriptors

### 2. Create Dashboards

Dashboards can be created in two ways:

#### Option A: Cloud Console (Recommended)

1. Go to [Cloud Monitoring Dashboards](https://console.cloud.google.com/monitoring/dashboards)
2. Click "Create Dashboard"
3. Use `monitoring/dashboards.yaml` as reference to add widgets
4. Configure each chart with the appropriate metrics and filters

#### Option B: Monitoring API

Use the Google Cloud Monitoring API to programmatically create dashboards from the YAML configuration.

### 3. Setup Alerting

Configure alert policies:

```bash
./scripts/setup-alerting.sh
```

See [Alerting Documentation](../docs/ALERTING.md) for details.

### 4. Configure Notification Channels

Set up notification channels for alerts:

1. Go to [Notification Channels](https://console.cloud.google.com/monitoring/alerting/notifications)
2. Add channels:
   - **Email**: For non-critical alerts
   - **Slack**: For team notifications
   - **PagerDuty**: For critical production alerts

## Viewing Metrics

### Metrics Explorer

View any metric in real-time:

```
https://console.cloud.google.com/monitoring/metrics-explorer?project=<PROJECT_ID>
```

Example queries:

```
# Agent execution rate
logging.googleapis.com/user/agent_execution_count

# Average execution latency
logging.googleapis.com/user/agent_execution_latency

# Error rate
logging.googleapis.com/log_entry_count{severity="ERROR"}
```

### Logs Explorer

Query structured logs:

```
https://console.cloud.google.com/logs/query?project=<PROJECT_ID>
```

Example queries:

```
# All agent executions
resource.type="cloud_run_revision"
jsonPayload.event="execution_complete"

# Failed login attempts
resource.type="cloud_run_revision"
jsonPayload.event="login_attempt"
jsonPayload.success=false

# API key access events
resource.type="cloud_run_revision"
jsonPayload.event="api_key_access"

# Errors in the last hour
resource.type="cloud_run_revision"
severity="ERROR"
timestamp>="2024-01-01T00:00:00Z"
```

## Structured Logging

All application logs follow a structured format with these fields:

### Common Fields

- `timestamp`: ISO 8601 timestamp
- `severity`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `event`: Event type identifier
- `user_id`: Authenticated user ID (when applicable)

### Event Types

#### Execution Events

```json
{
  "event": "execution_start",
  "blueprint_id": "uuid",
  "message_length": 123,
  "session_id": "uuid"
}

{
  "event": "execution_complete",
  "blueprint_id": "uuid",
  "latency_ms": 1234,
  "tool_calls": 3,
  "success": true,
  "session_id": "uuid"
}
```

#### Authentication Events

```json
{
  "event": "login_attempt",
  "email": "user@example.com",
  "client_ip": "1.2.3.4",
  "success": true,
  "user_id": "uuid"
}

{
  "event": "user_registration",
  "email": "user@example.com",
  "client_ip": "1.2.3.4",
  "success": true,
  "user_id": "uuid"
}
```

#### API Key Events

```json
{
  "event": "api_key_access",
  "user_id": "uuid",
  "provider": "openai",
  "action": "add",
  "success": true
}
```

#### Request Events

```json
{
  "event": "request_complete",
  "method": "POST",
  "path": "/api/agents/run",
  "status_code": 200,
  "duration_ms": 1234,
  "user_id": "uuid"
}
```

## Performance Targets

### Request Metrics

- **p50 Latency**: < 500ms
- **p95 Latency**: < 2000ms
- **p99 Latency**: < 5000ms
- **Error Rate**: < 1%
- **Availability**: > 99.9%

### Infrastructure Metrics

- **Database CPU**: < 80% sustained
- **Database Memory**: < 80% sustained
- **Redis Cache Hit Rate**: > 80%
- **Cloud Run Instances**: Auto-scale 0-10

## Troubleshooting

### High Latency

1. Check database connection pool usage
2. Review slow query logs in Cloud SQL
3. Check Redis cache hit rate
4. Review agent execution latency distribution

### High Error Rate

1. Check error logs by type:
   ```
   severity="ERROR"
   ```
2. Review recent deployments
3. Check external API availability (OpenAI, Anthropic, etc.)
4. Verify database connectivity

### Database Issues

1. Check CPU and memory utilization
2. Review active connections
3. Check for long-running queries
4. Review database logs

### Cache Issues

1. Check Redis memory usage
2. Review cache hit rate
3. Check for cache evictions
4. Verify cache TTL settings

## Cost Optimization

### Log Retention

- **Default**: 30 days
- **Long-term**: Export to Cloud Storage for archival
- **Cost**: ~$0.50/GB ingested

### Metrics Retention

- **Default**: 6 weeks (free)
- **Extended**: Up to 24 months (additional cost)

### Dashboard Queries

- Use appropriate aggregation periods (60s minimum)
- Limit time ranges for expensive queries
- Use filters to reduce data scanned

## References

- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Cloud Logging Documentation](https://cloud.google.com/logging/docs)
- [Log-based Metrics](https://cloud.google.com/logging/docs/logs-based-metrics)
- [Dashboard Configuration](https://cloud.google.com/monitoring/dashboards)
- [Alerting Policies](https://cloud.google.com/monitoring/alerts)
