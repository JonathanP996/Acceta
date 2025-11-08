# Google Cloud Setup Guide

## Quick Setup

### Option 1: Use in Current Session
```bash
export PATH="$PWD/google-cloud-sdk/bin:$PATH"
```

### Option 2: Add to Your Shell Profile (Permanent)
Add this line to your `~/.zshrc`:
```bash
export PATH="$HOME/gaTech/AI@GT/google-cloud-sdk/bin:$PATH"
```

Then reload:
```bash
source ~/.zshrc
```

## Select a Project

You need to select a Google Cloud project. Run:
```bash
export PATH="$PWD/google-cloud-sdk/bin:$PATH"
gcloud config set project YOUR_PROJECT_ID
```

Or list available projects:
```bash
gcloud projects list
```

## Common Agent Setup Tasks

### 1. Deploy to Cloud Run (for web apps)
```bash
# Build and deploy
gcloud run deploy dna-circuit-composer \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 2. Set up Vertex AI Agent
```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Create a Vertex AI agent
gcloud ai agents create --help
```

### 3. Deploy to App Engine
```bash
# Create app.yaml first, then:
gcloud app deploy
```

### 4. Set up Cloud Functions
```bash
gcloud functions deploy FUNCTION_NAME \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated
```

## Verify Setup
```bash
gcloud config list
gcloud auth list
gcloud projects list
```

