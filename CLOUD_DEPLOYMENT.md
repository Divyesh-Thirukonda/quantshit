# 🚀 Cloud Deployment Guide

This guide will help you deploy the Quantshit Arbitrage API to the cloud.

## 🏗️ Architecture Overview

The system is designed for cloud deployment with:
- **FastAPI web service** with REST endpoints
- **Docker containerization** for consistent deployment
- **Health checks** and monitoring
- **Multi-cloud support** (AWS, GCP, Azure)
- **Auto-scaling** capabilities
- **Production security** best practices

## 📋 Prerequisites

### Required Tools
- **Docker** - For containerization
- **Cloud CLI** - AWS CLI, gcloud, or Azure CLI
- **Git** - For code management

### Required Accounts
- Cloud provider account (AWS, GCP, or Azure)
- API credentials for Kalshi and Polymarket (for Phase 2)

## 🔧 Quick Setup

### 1. Install Docker
```bash
# Windows
# Download from: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe

# macOS
# Download from: https://desktop.docker.com/mac/main/amd64/Docker.dmg

# Linux
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 2. Test Local Docker Build
```bash
# Build the image
docker build -t quantshit:latest .

# Test locally
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### 3. Choose Your Cloud Provider

## ☁️ AWS Deployment

### Setup
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

### Deploy
```bash
cd deploy/aws
chmod +x deploy.sh
./deploy.sh
```

### What It Creates
- **ECS Fargate Cluster** - Serverless container hosting
- **ECR Repository** - Private Docker registry
- **Application Load Balancer** - Traffic distribution
- **CloudWatch Logs** - Centralized logging
- **Secrets Manager** - Secure API key storage

### Cost Estimate
- ~$30-50/month for small production workload
- Scales automatically based on traffic

## 🌐 Google Cloud Deployment

### Setup
```bash
# Install gcloud CLI
# Download from: https://cloud.google.com/sdk/docs/install

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Deploy
```bash
cd deploy/gcp
chmod +x deploy.sh
./deploy.sh
```

### What It Creates
- **Cloud Run Service** - Serverless container platform
- **Container Registry** - Docker image storage
- **Secret Manager** - API credential storage
- **Cloud Logging** - Centralized logs

### Cost Estimate
- ~$10-20/month for small workload
- Pay only for actual usage

## 🔷 Azure Deployment

### Setup
```bash
# Install Azure CLI
# Download from: https://aka.ms/installazurecliwindows

# Login
az login
```

### Deploy
```bash
cd deploy/azure
chmod +x deploy.sh
./deploy.sh
```

### What It Creates
- **Container Instances** - Managed container hosting
- **Container Registry** - Private Docker registry
- **Key Vault** - Secure credential storage
- **Monitor** - Application insights

### Cost Estimate
- ~$25-40/month for small workload
- Simple pricing model

## 🛡️ Security Setup

### 1. Environment Variables
Create production environment file:
```bash
cp .env.production.example .env.production
# Edit with your actual credentials
```

### 2. API Credentials (Phase 2)
```bash
# Kalshi
KALSHI_API_KEY=your_production_key
KALSHI_API_SECRET=your_production_secret

# Polymarket  
POLYMARKET_API_KEY=your_production_key
POLYMARKET_API_SECRET=your_production_secret
```

### 3. Database (Phase 2)
```bash
# Use managed database services
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
```

## 📊 Monitoring & Health Checks

### Built-in Endpoints
- `GET /health` - Service health status
- `GET /status` - Detailed system status
- `GET /` - API information

### Monitoring Setup
```bash
# AWS CloudWatch
aws logs tail quantshit-logs --follow

# GCP Cloud Logging
gcloud logs tail cloud-run-hello --follow

# Azure Monitor
az container logs --resource-group quantshit-rg --name quantshit-api --follow
```

## 🔄 CI/CD Pipeline (Optional)

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to AWS
      run: ./deploy/aws/deploy.sh
```

## 🎯 Production Checklist

### Before Going Live
- [ ] API credentials configured
- [ ] Health checks passing
- [ ] Monitoring setup
- [ ] Backup strategy
- [ ] Security review
- [ ] Load testing
- [ ] Error handling
- [ ] Rate limiting

### Phase 1 Status
- ✅ **API Service** - Production ready
- ✅ **Health Checks** - Implemented
- ✅ **Cloud Deployment** - Multi-cloud support
- ✅ **Docker Containers** - Ready
- ✅ **Security** - Basic hardening
- 🔄 **Data Sources** - Coming in Phase 2
- 🔄 **Trading Logic** - Coming in Phase 3

## 🆘 Troubleshooting

### Common Issues

**Docker Build Fails**
```bash
# Check Docker is running
docker --version

# Clear cache and rebuild
docker system prune -a
docker build --no-cache -t quantshit:latest .
```

**API Not Responding**
```bash
# Check logs
docker logs quantshit-api

# Check health endpoint
curl http://localhost:8000/health
```

**Cloud Deployment Fails**
```bash
# Check credentials
aws sts get-caller-identity  # AWS
gcloud auth list            # GCP
az account show             # Azure

# Check permissions
# Ensure your account has container deployment permissions
```

## 📞 Support

- **Documentation**: See README.md
- **Issues**: Create GitHub issues
- **Monitoring**: Check `/status` endpoint

---

**🎉 Ready to Deploy!**

Your prediction market arbitrage system is ready for cloud deployment. Choose your preferred cloud provider and follow the deployment steps above.

The system is designed to be:
- **Scalable** - Handles increasing load automatically
- **Reliable** - Built-in health checks and monitoring
- **Secure** - Production security best practices
- **Cost-effective** - Pay only for what you use

**Next Steps**: Deploy to cloud → Set up monitoring → Prepare for Phase 2 data integration