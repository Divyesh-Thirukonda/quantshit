#!/bin/bash

# Azure Container Instances Deployment Script
set -e

echo "🚀 Deploying Quantshit to Azure Container Instances..."

# Configuration
RESOURCE_GROUP=${RESOURCE_GROUP:-"quantshit-rg"}
LOCATION=${LOCATION:-"eastus"}
CONTAINER_NAME="quantshit-api"
ACR_NAME="quantshitacr"
IMAGE_NAME="quantshit"

echo "📍 Resource Group: ${RESOURCE_GROUP}"
echo "📍 Location: ${LOCATION}"
echo "📍 Container: ${CONTAINER_NAME}"

# Login to Azure (if not already logged in)
echo "🔐 Checking Azure login..."
az account show || az login

# Create resource group
echo "📦 Creating resource group..."
az group create --name ${RESOURCE_GROUP} --location ${LOCATION}

# Create Azure Container Registry
echo "🏗️ Creating Azure Container Registry..."
az acr create --resource-group ${RESOURCE_GROUP} \
    --name ${ACR_NAME} \
    --sku Basic \
    --admin-enabled true

# Get ACR credentials
ACR_SERVER=$(az acr show --name ${ACR_NAME} --resource-group ${RESOURCE_GROUP} --query "loginServer" --output tsv)
ACR_USERNAME=$(az acr credential show --name ${ACR_NAME} --resource-group ${RESOURCE_GROUP} --query "username" --output tsv)
ACR_PASSWORD=$(az acr credential show --name ${ACR_NAME} --resource-group ${RESOURCE_GROUP} --query "passwords[0].value" --output tsv)

echo "📍 ACR Server: ${ACR_SERVER}"

# Build and push Docker image
echo "🔨 Building and pushing Docker image..."
az acr build --registry ${ACR_NAME} --image ${IMAGE_NAME}:latest ../../

# Deploy to Azure Container Instances
echo "🚀 Deploying to Azure Container Instances..."
az container create \
    --resource-group ${RESOURCE_GROUP} \
    --name ${CONTAINER_NAME} \
    --image ${ACR_SERVER}/${IMAGE_NAME}:latest \
    --registry-login-server ${ACR_SERVER} \
    --registry-username ${ACR_USERNAME} \
    --registry-password ${ACR_PASSWORD} \
    --dns-name-label quantshit-api-${RANDOM} \
    --ports 8000 \
    --environment-variables \
        ENVIRONMENT=production \
        DEBUG=false \
        PAPER_TRADING=true \
        API_HOST=0.0.0.0 \
        API_PORT=8000 \
    --cpu 1 \
    --memory 1

# Get the FQDN
FQDN=$(az container show --resource-group ${RESOURCE_GROUP} --name ${CONTAINER_NAME} --query "ipAddress.fqdn" --output tsv)

echo "✅ Deployment completed!"
echo "🌐 Your API is available at: http://${FQDN}:8000"
echo "📊 Test health: curl http://${FQDN}:8000/health"
echo "📋 View logs: az container logs --resource-group ${RESOURCE_GROUP} --name ${CONTAINER_NAME}"