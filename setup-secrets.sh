#!/bin/bash
# Create missing secrets in Google Cloud Secret Manager

PROJECT_ID="frankenagent-prod"

echo "Creating missing secrets..."

# Create ANTHROPIC_API_KEY secret
echo "Creating ANTHROPIC_API_KEY..."
echo -n "placeholder" | gcloud secrets create ANTHROPIC_API_KEY --data-file=- --project=$PROJECT_ID 2>/dev/null || echo "ANTHROPIC_API_KEY already exists"

# Create GROQ_API_KEY secret
echo "Creating GROQ_API_KEY..."
echo -n "placeholder" | gcloud secrets create GROQ_API_KEY --data-file=- --project=$PROJECT_ID 2>/dev/null || echo "GROQ_API_KEY already exists"

# Create GEMINI_API_KEY secret
echo "Creating GEMINI_API_KEY..."
echo -n "placeholder" | gcloud secrets create GEMINI_API_KEY --data-file=- --project=$PROJECT_ID 2>/dev/null || echo "GEMINI_API_KEY already exists"

# Create BREVO_API_KEY secret
echo "Creating BREVO_API_KEY..."
echo -n "placeholder" | gcloud secrets create BREVO_API_KEY --data-file=- --project=$PROJECT_ID 2>/dev/null || echo "BREVO_API_KEY already exists"

echo "Done! Now update the secrets with real values in Cloud Console:"
echo "https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
