"""Health monitoring and metrics for the arbitrage system."""

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import asyncio

@dataclass
class HealthMetrics:
    """System health metrics."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    disk_percent: float = 0.0
    uptime_seconds: float = 0.0
    response_time_ms: float = 0.0
    status: str = "unknown"

@dataclass
class ServiceHealth:
    """Service-specific health information."""
    service_name: str
    status: str  # healthy, degraded, unhealthy
    last_check: datetime
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

class HealthMonitor:
    """Monitors system and service health."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.response_times = []
        self.error_count = 0
        self.request_count = 0
        
    def get_system_metrics(self) -> HealthMetrics:
        """Get current system metrics."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Uptime
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Average response time
            avg_response_time = sum(self.response_times[-100:]) / len(self.response_times[-100:]) if self.response_times else 0.0
            
            # Determine status
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 80:
                status = "degraded"
            if cpu_percent > 95 or memory.percent > 95:
                status = "unhealthy"
                
            return HealthMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_total_mb=memory.total / (1024 * 1024),
                disk_percent=disk.percent,
                uptime_seconds=uptime,
                response_time_ms=avg_response_time,
                status=status
            )
        except Exception as e:
            return HealthMetrics(
                status="error",
                details={"error": str(e)}
            )
    
    def record_request(self, response_time_ms: float, is_error: bool = False):
        """Record a request for metrics."""
        self.response_times.append(response_time_ms)
        self.request_count += 1
        
        if is_error:
            self.error_count += 1
            
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_error_rate(self) -> float:
        """Get current error rate."""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def get_service_health(self, service_name: str) -> ServiceHealth:
        """Get health status for a specific service."""
        metrics = self.get_system_metrics()
        
        # Determine service status based on system health
        status = "healthy"
        if metrics.status == "degraded":
            status = "degraded"
        elif metrics.status == "unhealthy" or metrics.status == "error":
            status = "unhealthy"
        
        error_rate = self.get_error_rate()
        if error_rate > 0.1:  # More than 10% error rate
            status = "degraded"
        if error_rate > 0.5:  # More than 50% error rate
            status = "unhealthy"
        
        return ServiceHealth(
            service_name=service_name,
            status=status,
            last_check=datetime.utcnow(),
            response_time_ms=metrics.response_time_ms,
            error_rate=error_rate,
            details={
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "uptime_seconds": metrics.uptime_seconds,
                "total_requests": self.request_count,
                "total_errors": self.error_count
            }
        )
    
    def get_detailed_health(self) -> Dict[str, Any]:
        """Get comprehensive health information."""
        metrics = self.get_system_metrics()
        service_health = self.get_service_health("quantshit-api")
        
        return {
            "overall_status": service_health.status,
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "memory_used_mb": round(metrics.memory_used_mb, 2),
                "memory_total_mb": round(metrics.memory_total_mb, 2),
                "disk_percent": metrics.disk_percent,
                "uptime_seconds": round(metrics.uptime_seconds, 2)
            },
            "service": {
                "status": service_health.status,
                "response_time_ms": round(service_health.response_time_ms, 2),
                "error_rate": round(service_health.error_rate, 4),
                "total_requests": self.request_count,
                "total_errors": self.error_count
            },
            "checks": {
                "api_responsive": service_health.status != "unhealthy",
                "cpu_healthy": metrics.cpu_percent < 80,
                "memory_healthy": metrics.memory_percent < 80,
                "disk_healthy": metrics.disk_percent < 90,
                "error_rate_healthy": service_health.error_rate < 0.1
            }
        }

# Global health monitor instance
health_monitor = HealthMonitor()