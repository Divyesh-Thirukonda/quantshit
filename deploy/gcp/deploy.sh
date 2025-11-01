#!/bin/bash

# Google Cloud Run Deployment Script
set -e

echo "🚀 Deploying Quantshit to Google Cloud Run..."

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="quantshit-api"
IMAGE_NAME="quantshit"

echo "📍 Project: ${PROJECT_ID}"
echo "📍 Region: ${REGION}"
echo "📍 Service: ${SERVICE_NAME}"

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com --project=${PROJECT_ID}
gcloud services enable run.googleapis.com --project=${PROJECT_ID}
gcloud services enable secretmanager.googleapis.com --project=${PROJECT_ID}

# Build and push to Google Container Registry
echo "🔨 Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest ../../ --project=${PROJECT_ID}

# Update the Cloud Run configuration with project ID
echo "📝 Updating Cloud Run configuration..."
sed "s/PROJECT_ID/${PROJECT_ID}/g" cloudrun.yaml > cloudrun-updated.yaml

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run services replace cloudrun-updated.yaml \
    --region=${REGION} \
    --project=${PROJECT_ID}

# Allow unauthenticated invocations (for public API)
echo "🌐 Setting up public access..."
gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --region=${REGION} \
    --project=${PROJECT_ID}

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(status.url)")

echo "✅ Deployment completed!"
echo "🌐 Your API is available at: ${SERVICE_URL}"
echo "📊 Test health: curl ${SERVICE_URL}/health"
echo "📋 View logs: gcloud logs tail cloud-run-hello --project=${PROJECT_ID}"