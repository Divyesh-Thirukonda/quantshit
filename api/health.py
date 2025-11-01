# Individual API endpoints for Vercel
# Each endpoint becomes a separate serverless function

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.monitoring.health import HealthMonitor
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json

# Initialize health monitor
health_monitor = HealthMonitor()

def handler(request):
    """Vercel handler for /api/health endpoint"""
    try:
        health_data = health_monitor.get_health_status()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(health_data)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }