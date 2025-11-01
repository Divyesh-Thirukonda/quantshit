#!/bin/bash

# AWS ECS Deployment Script
set -e

echo "🚀 Deploying Quantshit to AWS ECS..."

# Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
ECR_REPO="quantshit"
CLUSTER_NAME="quantshit-cluster"
SERVICE_NAME="quantshit-service"
TASK_DEFINITION="quantshit-api"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo "📍 AWS Account: ${ACCOUNT_ID}"
echo "📍 ECR URI: ${ECR_URI}"
echo "📍 Region: ${AWS_REGION}"

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr describe-repositories --repository-names ${ECR_REPO} --region ${AWS_REGION} || \
aws ecr create-repository --repository-name ${ECR_REPO} --region ${AWS_REGION}

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# Build and tag Docker image
echo "🔨 Building Docker image..."
docker build -t ${ECR_REPO}:latest ../../

# Tag for ECR
docker tag ${ECR_REPO}:latest ${ECR_URI}:latest

# Push to ECR
echo "📤 Pushing to ECR..."
docker push ${ECR_URI}:latest

# Update task definition with actual account ID and region
echo "📝 Updating task definition..."
sed "s/ACCOUNT_ID/${ACCOUNT_ID}/g; s/REGION/${AWS_REGION}/g" task-definition.json > task-definition-updated.json

# Register new task definition
echo "📋 Registering task definition..."
aws ecs register-task-definition \
    --cli-input-json file://task-definition-updated.json \
    --region ${AWS_REGION}

# Create ECS cluster if it doesn't exist
echo "🖥️ Creating ECS cluster..."
aws ecs describe-clusters --clusters ${CLUSTER_NAME} --region ${AWS_REGION} || \
aws ecs create-cluster --cluster-name ${CLUSTER_NAME} --capacity-providers FARGATE --region ${AWS_REGION}

# Update or create service
echo "⚙️ Updating ECS service..."
aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME} --region ${AWS_REGION} 2>/dev/null || {
    echo "Creating new service..."
    aws ecs create-service \
        --cluster ${CLUSTER_NAME} \
        --service-name ${SERVICE_NAME} \
        --task-definition ${TASK_DEFINITION} \
        --desired-count 2 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
        --region ${AWS_REGION}
}

# Update existing service
aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --task-definition ${TASK_DEFINITION} \
    --region ${AWS_REGION}

echo "✅ Deployment completed!"
echo "🌐 Your API will be available at the load balancer URL"
echo "📊 Monitor deployment: aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME} --region ${AWS_REGION}"