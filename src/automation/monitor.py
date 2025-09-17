from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any, List
import logging

from ..llm.llm_client import LLMClient
from ..shared.config import settings
from ..shared.redis_client import get_redis
from ..shared.db import db_cursor
from ..crawler.platforms.youtube import search_candidates
from ..crawler.platforms.telegram import candidates_from_query
from ..crawler.platforms.facebook import candidates_from_query as fb_candidates_from_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AntiPiracyMonitor:
    def __init__(self):
        self.llm_client = LLMClient()
        self.redis = get_redis()
        self.platforms = ["youtube", "telegram", "facebook", "twitter", "instagram", "google"]
        self.scan_interval = 300  # 5 minutes
        self.max_candidates_per_scan = 10
        
    async def get_keywords(self) -> List[str]:
        """Get expanded keywords from LLM"""
        try:
            expanded = self.llm_client.expand_keywords({"seeds": [
                "tapmad live",
                "tapmad sports", 
                "live cricket tapmad",
                "free match stream",
                "live match hd",
                "ট্যাপম্যাড লাইভ",
                "ফ্রি খেলা লাইভ",
                "লাইভ ম্যাচ এইচডি",
                "খেলা ফ্রি স্ট্রিম"
            ], "date": "today"})
            return expanded[:20]  # Limit to 20 keywords
        except Exception as e:
            logger.error(f"Failed to get keywords: {e}")
            return ["tapmad live", "live cricket", "sports streaming"]
    
    async def scan_platform(self, platform: str, keyword: str) -> List[dict]:
        """Scan a specific platform for candidates"""
        try:
            if platform == "youtube":
                candidates = search_candidates(keyword, max_results=3)
            elif platform == "telegram":
                candidates = candidates_from_query(keyword)
            elif platform == "facebook":
                candidates = fb_candidates_from_query(keyword)
            elif platform == "twitter":
                from ..crawler.platforms.twitter import search_candidates
                candidates = search_candidates(keyword, max_results=3)
            elif platform == "instagram":
                from ..crawler.platforms.instagram import search_candidates
                candidates = search_candidates(keyword, max_results=3)
            elif platform == "google":
                from ..crawler.platforms.google import search_candidates
                candidates = search_candidates(keyword, max_results=3)
            else:
                return []
            
            logger.info(f"Found {len(candidates)} candidates on {platform} for '{keyword}'")
            return candidates
            
        except Exception as e:
            logger.error(f"Failed to scan {platform}: {e}")
            return []
    
    async def queue_candidates(self, candidates: List[dict]) -> int:
        """Queue candidates for processing"""
        queued_count = 0
        for candidate in candidates:
            try:
                cid = self.redis.incr("ap:candidates:id_seq")
                data = {
                    "id": cid,
                    "url": candidate["url"],
                    "title": candidate["title"],
                    "platform": candidate["platform"],
                    "status": "queued",
                    "queued_at": int(time.time())
                }
                self.redis.set(f"ap:candidate:{cid}", json.dumps(data))
                self.redis.rpush("ap:candidates", cid)
                queued_count += 1
                
            except Exception as e:
                logger.error(f"Failed to queue candidate: {e}")
        
        return queued_count
    
    async def process_pending_candidates(self) -> int:
        """Process candidates that are queued but not yet fingerprinted"""
        processed_count = 0
        
        # Get queued candidates
        candidate_ids = self.redis.lrange("ap:candidates", 0, 9)  # Process 10 at a time
        
        for cid in candidate_ids:
            try:
                cid = int(cid)
                raw = self.redis.get(f"ap:candidate:{cid}")
                if not raw:
                    continue
                    
                data = json.loads(raw)
                if data.get("status") != "queued":
                    continue
                
                # Mark as processing
                data["status"] = "processing"
                self.redis.set(f"ap:candidate:{cid}", json.dumps(data))
                
                # Here we would call the fingerprint and match tools
                # For now, just mark as processed
                data["status"] = "processed"
                data["processed_at"] = int(time.time())
                self.redis.set(f"ap:candidate:{cid}", json.dumps(data))
                
                processed_count += 1
                logger.info(f"Processed candidate {cid}: {data['title']}")
                
            except Exception as e:
                logger.error(f"Failed to process candidate {cid}: {e}")
        
        return processed_count
    
    async def check_system_health(self) -> dict:
        """Check system health and return status"""
        health = {
            "timestamp": int(time.time()),
            "status": "healthy",
            "components": {}
        }
        
        try:
            # Check Redis
            self.redis.ping()
            health["components"]["redis"] = "healthy"
        except Exception as e:
            health["components"]["redis"] = f"unhealthy: {e}"
            health["status"] = "degraded"
        
        try:
            # Check Database
            with db_cursor() as cur:
                cur.execute("SELECT 1")
            health["components"]["database"] = "healthy"
        except Exception as e:
            health["components"]["database"] = f"unhealthy: {e}"
            health["status"] = "degraded"
        
        try:
            # Check LLM
            self.llm_client.expand_keywords({"seeds": ["test"], "date": "today"})
            health["components"]["llm"] = "healthy"
        except Exception as e:
            health["components"]["llm"] = f"unhealthy: {e}"
            health["status"] = "degraded"
        
        return health
    
    async def run_scan_cycle(self):
        """Run one complete scan cycle"""
        logger.info("Starting scan cycle")
        
        try:
            # Get keywords
            keywords = await self.get_keywords()
            logger.info(f"Got {len(keywords)} keywords")
            
            total_queued = 0
            
            # Scan each platform
            for platform in self.platforms:
                for keyword in keywords[:5]:  # Limit keywords per platform
                    candidates = await self.scan_platform(platform, keyword)
                    if candidates:
                        queued = await self.queue_candidates(candidates)
                        total_queued += queued
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
            
            logger.info(f"Scan cycle complete: queued {total_queued} candidates")
            
        except Exception as e:
            logger.error(f"Scan cycle failed: {e}")
    
    async def run_processing_cycle(self):
        """Run one complete processing cycle"""
        logger.info("Starting processing cycle")
        
        try:
            processed = await self.process_pending_candidates()
            logger.info(f"Processing cycle complete: processed {processed} candidates")
            
        except Exception as e:
            logger.error(f"Processing cycle failed: {e}")
    
    async def run_health_check(self):
        """Run health check and log status"""
        try:
            health = await self.check_system_health()
            logger.info(f"Health check: {health['status']}")
            
            # Store health status in Redis
            self.redis.set("ap:health", json.dumps(health), ex=300)  # 5 min expiry
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def run_continuous_monitoring(self):
        """Main monitoring loop"""
        logger.info("Starting continuous monitoring")
        
        while True:
            try:
                # Run health check every 5 minutes
                await self.run_health_check()
                
                # Run scan cycle every 30 minutes
                await self.run_scan_cycle()
                
                # Run processing cycle every 2 minutes
                for _ in range(15):  # 15 * 2 = 30 minutes
                    await self.run_processing_cycle()
                    await asyncio.sleep(120)  # 2 minutes
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

async def main():
    monitor = AntiPiracyMonitor()
    await monitor.run_continuous_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
