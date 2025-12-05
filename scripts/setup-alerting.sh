#!/bin/bash
# Setup alerting policies for FrankenAgent Lab

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"frankenagent-prod"}
REGION=${GCP_REGION:-"us-central1"}

echo "Setting up alerting for project: $PROJECT_ID"

# Set project
gcloud config set project $PROJECT_ID

# Enable Cloud Monitoring API (if not already enabled)
echo "Enabling Cloud Monitoring API..."
gcloud services enable monitoring.googleapis.com

# Note: Notification channels must be created first
echo ""
echo "⚠️  IMPORTANT: Create notification channels before running this script"
echo ""
echo "To create notification channels:"
echo "1. Go to: https://console.cloud.google.com/monitoring/alerting/notifications?project=$PROJECT_ID"
echo "2. Click 'Add New' and configure:"
echo "   - Email channel for non-critical alerts"
echo "   - Slack channel for team notifications"
echo "   - PagerDuty channel for critical alerts"
echo "3. Note the channel IDs and update this script"
echo ""

# Get notification channel IDs (user must create these first)
read -p "Enter Email notification channel ID (or press Enter to skip): " EMAIL_CHANNEL
read -p "Enter Slack notification channel ID (or press Enter to skip): " SLACK_CHANNEL
read -p "Enter PagerDuty notification channel ID (or press Enter to skip): " PAGERDUTY_CHANNEL

if [ -z "$EMAIL_CHANNEL" ] && [ -z "$SLACK_CHANNEL" ] && [ -z "$PAGERDUTY_CHANNEL" ]; then
    echo "No notification channels provided. Alerts will be created but won't send notifications."
    echo "You can add notification channels later in the Cloud Console."
fi

# Create uptime check first (required for service down alert)
echo "Creating uptime check..."
gcloud monitoring uptime create frankenagent-health-check \
    --resource-type=uptime-url \
    --display-name="FrankenAgent Health Check" \
    --http-check-path="/health" \
    --period=60 \
    --timeout=10s \
    --regions=us-central1,us-east1,us-west1 \
    2>/dev/null || echo "Uptime check already exists"

# Function to create alert policy
create_alert_policy() {
    local name=$1
    local display_name=$2
    local filter=$3
    local threshold=$4
    local duration=$5
    local comparison=$6
    local channels=$7
    
    echo "Creating alert policy: $display_name..."
    
    # Create policy JSON
    cat > /tmp/alert_policy.json <<EOF
{
  "displayName": "$display_name",
  "conditions": [
    {
      "displayName": "$display_name condition",
      "conditionThreshold": {
        "filter": "$filter",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ],
        "comparison": "$comparison",
        "thresholdValue": $threshold,
        "duration": "${duration}s"
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": $channels,
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF
    
    # Create the alert policy
    gcloud alpha monitoring policies create --policy-from-file=/tmp/alert_policy.json \
        2>/dev/null || echo "Alert policy '$display_name' may already exist"
    
    rm /tmp/alert_policy.json
}

# Build notification channels array
CHANNELS="[]"
if [ -n "$EMAIL_CHANNEL" ] || [ -n "$SLACK_CHANNEL" ]; then
    CHANNELS="["
    [ -n "$EMAIL_CHANNEL" ] && CHANNELS="${CHANNELS}\"projects/$PROJECT_ID/notificationChannels/$EMAIL_CHANNEL\","
    [ -n "$SLACK_CHANNEL" ] && CHANNELS="${CHANNELS}\"projects/$PROJECT_ID/notificationChannels/$SLACK_CHANNEL\","
    CHANNELS="${CHANNELS%,}]"
fi

CRITICAL_CHANNELS="[]"
if [ -n "$PAGERDUTY_CHANNEL" ]; then
    CRITICAL_CHANNELS="[\"projects/$PROJECT_ID/notificationChannels/$PAGERDUTY_CHANNEL\"]"
fi

# Alert 1: High Error Rate (>5%)
create_alert_policy \
    "high_error_rate" \
    "High Error Rate (>5%)" \
    "resource.type=\"cloud_run_revision\" AND metric.type=\"logging.googleapis.com/log_entry_count\" AND metric.label.severity=\"ERROR\"" \
    "0.05" \
    "300" \
    "COMPARISON_GT" \
    "$CHANNELS"

# Alert 2: High Latency (p95 > 2s)
echo "Creating alert policy: High Latency (p95 > 2s)..."
cat > /tmp/high_latency_policy.json <<EOF
{
  "displayName": "High Latency (p95 > 2s)",
  "conditions": [
    {
      "displayName": "p95 latency > 2000ms",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\"",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_DELTA",
            "crossSeriesReducer": "REDUCE_PERCENTILE_95"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 2000,
        "duration": "300s"
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": $CHANNELS,
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF
gcloud alpha monitoring policies create --policy-from-file=/tmp/high_latency_policy.json \
    2>/dev/null || echo "Alert policy 'High Latency' may already exist"
rm /tmp/high_latency_policy.json

# Alert 3: Database CPU High (>80%)
echo "Creating alert policy: Database CPU High (>80%)..."
cat > /tmp/db_cpu_policy.json <<EOF
{
  "displayName": "Database CPU High (>80%)",
  "conditions": [
    {
      "displayName": "Database CPU > 80%",
      "conditionThreshold": {
        "filter": "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\"",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_MEAN"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.80,
        "duration": "600s"
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": $CHANNELS,
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF
gcloud alpha monitoring policies create --policy-from-file=/tmp/db_cpu_policy.json \
    2>/dev/null || echo "Alert policy 'Database CPU High' may already exist"
rm /tmp/db_cpu_policy.json

# Alert 4: Service Down (Uptime Check)
if [ -n "$PAGERDUTY_CHANNEL" ]; then
    echo "Creating alert policy: Service Down (Uptime Check)..."
    cat > /tmp/service_down_policy.json <<EOF
{
  "displayName": "Service Down (Uptime Check Failed)",
  "conditions": [
    {
      "displayName": "Uptime check failed",
      "conditionThreshold": {
        "filter": "resource.type=\"uptime_url\" AND metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\"",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_FRACTION_TRUE"
          }
        ],
        "comparison": "COMPARISON_LT",
        "thresholdValue": 0.5,
        "duration": "60s"
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": $CRITICAL_CHANNELS,
  "alertStrategy": {
    "autoClose": "300s"
  }
}
EOF
    gcloud alpha monitoring policies create --policy-from-file=/tmp/service_down_policy.json \
        2>/dev/null || echo "Alert policy 'Service Down' may already exist"
    rm /tmp/service_down_policy.json
else
    echo "Skipping Service Down alert (no PagerDuty channel configured)"
fi

echo ""
echo "✓ Alerting setup complete!"
echo ""
echo "Created alert policies:"
echo "  - High Error Rate (>5%)"
echo "  - High Latency (p95 > 2s)"
echo "  - Database CPU High (>80%)"
if [ -n "$PAGERDUTY_CHANNEL" ]; then
    echo "  - Service Down (Uptime Check)"
fi
echo ""
echo "View alert policies at:"
echo "https://console.cloud.google.com/monitoring/alerting/policies?project=$PROJECT_ID"
echo ""
echo "Next steps:"
echo "1. Test alerts by triggering conditions"
echo "2. Adjust thresholds based on baseline metrics"
echo "3. Create runbooks for each alert type"
echo "4. Configure escalation policies in PagerDuty"
