"""
Metrics and observability module for the anti-piracy system.
Provides Prometheus-style metrics and structured logging.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client not available. Metrics will use fallback implementation.")

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Metrics collector for the anti-piracy system"""
    
    def __init__(self):
        self.metrics = {}
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize metrics"""
        if PROMETHEUS_AVAILABLE:
            # Prometheus metrics
            self.detections_found = Counter(
                'antipiracy_detections_found_total',
                'Total number of detections found',
                ['platform', 'status']
            )
            
            self.evidence_captured = Counter(
                'antipiracy_evidence_captured_total',
                'Total number of evidence items captured',
                ['platform', 'status']
            )
            
            self.matches_made = Counter(
                'antipiracy_matches_made_total',
                'Total number of matches made',
                ['decision', 'platform']
            )
            
            self.dmca_queued = Counter(
                'antipiracy_dmca_queued_total',
                'Total number of DMCA notices queued',
                ['platform', 'dry_run']
            )
            
            self.dmca_sent = Counter(
                'antipiracy_dmca_sent_total',
                'Total number of DMCA notices sent',
                ['platform', 'status']
            )
            
            self.pipeline_duration = Histogram(
                'antipiracy_pipeline_duration_seconds',
                'Time spent processing pipeline',
                ['stage']
            )
            
            self.active_detections = Gauge(
                'antipiracy_active_detections',
                'Number of active detections by status',
                ['status']
            )
            
            self.database_connections = Gauge(
                'antipiracy_database_connections',
                'Number of active database connections'
            )
            
        else:
            # Fallback metrics
            self.metrics = {
                'detections_found': {},
                'evidence_captured': {},
                'matches_made': {},
                'dmca_queued': {},
                'dmca_sent': {},
                'pipeline_duration': {},
                'active_detections': {},
                'database_connections': 0
            }
    
    def record_detection_found(self, platform: str, status: str = "found"):
        """Record a detection found"""
        if PROMETHEUS_AVAILABLE:
            self.detections_found.labels(platform=platform, status=status).inc()
        else:
            key = f"{platform}:{status}"
            self.metrics['detections_found'][key] = self.metrics['detections_found'].get(key, 0) + 1
    
    def record_evidence_captured(self, platform: str, status: str = "captured"):
        """Record evidence captured"""
        if PROMETHEUS_AVAILABLE:
            self.evidence_captured.labels(platform=platform, status=status).inc()
        else:
            key = f"{platform}:{status}"
            self.metrics['evidence_captured'][key] = self.metrics['evidence_captured'].get(key, 0) + 1
    
    def record_match_made(self, decision: str, platform: str):
        """Record a match made"""
        if PROMETHEUS_AVAILABLE:
            self.matches_made.labels(decision=decision, platform=platform).inc()
        else:
            key = f"{decision}:{platform}"
            self.metrics['matches_made'][key] = self.metrics['matches_made'].get(key, 0) + 1
    
    def record_dmca_queued(self, platform: str, dry_run: bool = True):
        """Record DMCA notice queued"""
        if PROMETHEUS_AVAILABLE:
            self.dmca_queued.labels(platform=platform, dry_run=str(dry_run)).inc()
        else:
            key = f"{platform}:{dry_run}"
            self.metrics['dmca_queued'][key] = self.metrics['dmca_queued'].get(key, 0) + 1
    
    def record_dmca_sent(self, platform: str, status: str = "sent"):
        """Record DMCA notice sent"""
        if PROMETHEUS_AVAILABLE:
            self.dmca_sent.labels(platform=platform, status=status).inc()
        else:
            key = f"{platform}:{status}"
            self.metrics['dmca_sent'][key] = self.metrics['dmca_sent'].get(key, 0) + 1
    
    def record_pipeline_duration(self, stage: str, duration: float):
        """Record pipeline stage duration"""
        if PROMETHEUS_AVAILABLE:
            self.pipeline_duration.labels(stage=stage).observe(duration)
        else:
            self.metrics['pipeline_duration'][stage] = duration
    
    def set_active_detections(self, status: str, count: int):
        """Set active detections count"""
        if PROMETHEUS_AVAILABLE:
            self.active_detections.labels(status=status).set(count)
        else:
            self.metrics['active_detections'][status] = count
    
    def set_database_connections(self, count: int):
        """Set database connections count"""
        if PROMETHEUS_AVAILABLE:
            self.database_connections.set(count)
        else:
            self.metrics['database_connections'] = count
    
    @contextmanager
    def time_pipeline_stage(self, stage: str):
        """Context manager to time pipeline stages"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_pipeline_duration(stage, duration)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        if PROMETHEUS_AVAILABLE:
            return {
                "prometheus_available": True,
                "metrics_endpoint": "/metrics"
            }
        else:
            return {
                "prometheus_available": False,
                "fallback_metrics": self.metrics
            }
    
    def get_prometheus_metrics(self) -> Optional[str]:
        """Get Prometheus metrics in text format"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest()
        return None


# Global metrics instance
metrics = MetricsCollector()


class StructuredLogger:
    """Structured logger for the anti-piracy system"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup structured logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_detection(self, detection_id: int, platform: str, url: str, 
                     status: str, **kwargs):
        """Log detection event"""
        self.logger.info(
            f"Detection {detection_id} - {platform} - {status}",
            extra={
                "event_type": "detection",
                "detection_id": detection_id,
                "platform": platform,
                "url": url,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_evidence(self, evidence_id: int, detection_id: int, 
                    status: str, **kwargs):
        """Log evidence event"""
        self.logger.info(
            f"Evidence {evidence_id} - Detection {detection_id} - {status}",
            extra={
                "event_type": "evidence",
                "evidence_id": evidence_id,
                "detection_id": detection_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_match(self, match_id: int, detection_id: int, reference_id: int,
                 decision: str, confidence: float, **kwargs):
        """Log match event"""
        self.logger.info(
            f"Match {match_id} - Detection {detection_id} -> Reference {reference_id} - {decision}",
            extra={
                "event_type": "match",
                "match_id": match_id,
                "detection_id": detection_id,
                "reference_id": reference_id,
                "decision": decision,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_enforcement(self, enforcement_id: int, detection_id: int,
                       decision: str, dry_run: bool, **kwargs):
        """Log enforcement event"""
        self.logger.info(
            f"Enforcement {enforcement_id} - Detection {detection_id} - {decision} - {'DRY_RUN' if dry_run else 'LIVE'}",
            extra={
                "event_type": "enforcement",
                "enforcement_id": enforcement_id,
                "detection_id": detection_id,
                "decision": decision,
                "dry_run": dry_run,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_pipeline_stage(self, stage: str, duration: float, **kwargs):
        """Log pipeline stage"""
        self.logger.info(
            f"Pipeline stage {stage} completed in {duration:.2f}s",
            extra={
                "event_type": "pipeline_stage",
                "stage": stage,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_error(self, error: str, context: Dict[str, Any] = None):
        """Log error event"""
        self.logger.error(
            f"Error: {error}",
            extra={
                "event_type": "error",
                "error": error,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)


def setup_logging(level: str = "INFO", format_type: str = "text"):
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger.info(f"Logging configured - Level: {level}, Format: {format_type}")


# Request ID middleware for tracing
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID for tracing"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


# Health check endpoint
def get_health_status() -> Dict[str, Any]:
    """Get system health status"""
    try:
        from .database import test_connection
        from .redis_client import get_redis
        
        # Test database connection
        db_healthy = test_connection()
        
        # Test Redis connection
        try:
            redis_client = get_redis()
            redis_healthy = redis_client.ping()
        except Exception:
            redis_healthy = False
        
        return {
            "status": "healthy" if db_healthy and redis_healthy else "unhealthy",
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics.get_metrics_summary()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
