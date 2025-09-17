from __future__ import annotations

import json
import time
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from ..shared.redis_client import get_redis
from ..shared.db import db_cursor
from ..shared.config import settings

logger = logging.getLogger(__name__)

class AlertNotifier:
    def __init__(self):
        self.redis = get_redis()
        self.alert_channels = {
            "high_confidence": 0.9,
            "medium_confidence": 0.7,
            "system_health": "degraded",
            "new_platform": True
        }
    
    def send_alert(self, alert_type: str, message: str, data: Dict[str, Any] = None):
        """Send an alert to all configured channels"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": int(time.time()),
            "data": data or {}
        }
        
        # Store alert in Redis
        alert_id = self.redis.incr("ap:alerts:id_seq")
        self.redis.set(f"ap:alert:{alert_id}", json.dumps(alert), ex=86400)  # 24 hours
        self.redis.lpush("ap:alerts", alert_id)
        self.redis.ltrim("ap:alerts", 0, 999)  # Keep last 1000 alerts
        
        # Log alert
        logger.warning(f"ALERT [{alert_type}]: {message}")
        
        # TODO: Send to external notification services (Slack, Email, etc.)
        self._send_external_notification(alert)
    
    def _send_external_notification(self, alert: Dict[str, Any]):
        """Send alert to external notification services"""
        # This would integrate with Slack, Email, SMS, etc.
        # For now, just log the alert
        logger.info(f"External notification: {alert['type']} - {alert['message']}")
    
    def check_high_confidence_detections(self):
        """Check for high-confidence piracy detections"""
        try:
            with db_cursor() as cur:
                # Check for recent high-confidence detections
                cur.execute("""
                    SELECT id, platform, url, title, confidence, decision 
                    FROM detections 
                    WHERE confidence >= %s 
                    AND detected_at > %s
                    ORDER BY detected_at DESC
                """, (self.alert_channels["high_confidence"], 
                      datetime.now() - timedelta(hours=1)))
                
                high_conf_detections = cur.fetchall()
                
                for detection in high_conf_detections:
                    det_id, platform, url, title, confidence, decision = detection
                    
                    if decision == "approve":
                        self.send_alert(
                            "high_confidence_piracy",
                            f"High-confidence piracy detected on {platform}",
                            {
                                "detection_id": det_id,
                                "platform": platform,
                                "url": url,
                                "title": title,
                                "confidence": confidence,
                                "decision": decision
                            }
                        )
        
        except Exception as e:
            logger.error(f"Failed to check high-confidence detections: {e}")
    
    def check_system_health_alerts(self):
        """Check system health and send alerts if needed"""
        try:
            health_data = self.redis.get("ap:health")
            if health_data:
                health = json.loads(health_data)
                
                if health.get("status") == "degraded":
                    self.send_alert(
                        "system_health",
                        "System health is degraded",
                        health
                    )
                
                # Check individual components
                components = health.get("components", {})
                for component, status in components.items():
                    if "unhealthy" in str(status):
                        self.send_alert(
                            "component_failure",
                            f"Component {component} is unhealthy",
                            {"component": component, "status": status}
                        )
        
        except Exception as e:
            logger.error(f"Failed to check system health: {e}")
    
    def check_processing_backlog(self):
        """Check if there's a backlog in candidate processing"""
        try:
            queued_count = self.redis.llen("ap:candidates")
            
            if queued_count > 100:
                self.send_alert(
                    "processing_backlog",
                    f"Large processing backlog: {queued_count} candidates queued",
                    {"queued_count": queued_count}
                )
        
        except Exception as e:
            logger.error(f"Failed to check processing backlog: {e}")
    
    def check_new_platform_activity(self):
        """Check for activity on new platforms"""
        try:
            with db_cursor() as cur:
                # Check for detections from new platforms in the last hour
                cur.execute("""
                    SELECT platform, COUNT(*) as count
                    FROM detections 
                    WHERE detected_at > %s
                    GROUP BY platform
                    ORDER BY count DESC
                """, (datetime.now() - timedelta(hours=1),))
                
                platform_activity = cur.fetchall()
                
                for platform, count in platform_activity:
                    if count > 10:  # High activity threshold
                        self.send_alert(
                            "high_platform_activity",
                            f"High activity detected on {platform}: {count} detections",
                            {"platform": platform, "count": count}
                        )
        
        except Exception as e:
            logger.error(f"Failed to check platform activity: {e}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            alert_ids = self.redis.lrange("ap:alerts", 0, limit - 1)
            alerts = []
            
            for alert_id in alert_ids:
                alert_data = self.redis.get(f"ap:alert:{alert_id}")
                if alert_data:
                    alerts.append(json.loads(alert_data))
            
            return alerts
        
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def run_alert_checks(self):
        """Run all alert checks"""
        logger.info("Running alert checks")
        
        self.check_high_confidence_detections()
        self.check_system_health_alerts()
        self.check_processing_backlog()
        self.check_new_platform_activity()
        
        logger.info("Alert checks complete")


class AlertManager:
    """Manages the alert system"""
    
    def __init__(self):
        self.notifier = AlertNotifier()
        self.check_interval = 300  # 5 minutes
    
    def start_monitoring(self):
        """Start the alert monitoring loop"""
        import asyncio
        
        async def monitor_loop():
            while True:
                try:
                    self.notifier.run_alert_checks()
                    await asyncio.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"Alert monitoring error: {e}")
                    await asyncio.sleep(60)
        
        asyncio.run(monitor_loop())


# Global alert notifier instance
alert_notifier = AlertNotifier()
