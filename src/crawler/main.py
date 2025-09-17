#!/usr/bin/env python3
"""
Main crawler module for the anti-piracy system.
Provides CLI interface and orchestration for content crawling.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Optional

from .platforms.youtube import crawl_youtube_content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def crawl_platform(platform: str, keywords: List[str], max_results: Optional[int] = None) -> List[int]:
    """Crawl content from a specific platform"""
    logger.info(f"Starting crawl for platform: {platform}")
    
    if platform == "youtube":
        return crawl_youtube_content(keywords, max_results)
    else:
        logger.warning(f"Platform {platform} not yet implemented")
        return []


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Anti-piracy content crawler")
    parser.add_argument(
        "--platform", 
        choices=["youtube", "telegram", "facebook", "twitter", "instagram"],
        default="youtube",
        help="Platform to crawl"
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        required=True,
        help="Keywords to search for"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="Maximum number of results to return"
    )
    parser.add_argument(
        "--since",
        help="Only crawl content since this time (e.g., '2h', '1d')"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Parse since parameter
        since_time = None
        if args.since:
            since_time = _parse_since_time(args.since)
            logger.info(f"Crawling content since: {since_time}")
        
        # Start crawling
        start_time = datetime.now()
        detection_ids = crawl_platform(args.platform, args.keywords, args.max_results)
        end_time = datetime.now()
        
        # Report results
        duration = end_time - start_time
        logger.info(f"Crawl completed in {duration.total_seconds():.2f} seconds")
        logger.info(f"Found {len(detection_ids)} detections")
        
        if detection_ids:
            print(f"✅ Successfully crawled {len(detection_ids)} items")
            print(f"Detection IDs: {detection_ids[:10]}{'...' if len(detection_ids) > 10 else ''}")
        else:
            print("⚠️  No detections found")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        sys.exit(1)


def _parse_since_time(since_str: str) -> Optional[datetime]:
    """Parse since time string (e.g., '2h', '1d', '30m')"""
    try:
        if since_str.endswith('h'):
            hours = int(since_str[:-1])
            return datetime.now() - timedelta(hours=hours)
        elif since_str.endswith('d'):
            days = int(since_str[:-1])
            return datetime.now() - timedelta(days=days)
        elif since_str.endswith('m'):
            minutes = int(since_str[:-1])
            return datetime.now() - timedelta(minutes=minutes)
        else:
            logger.warning(f"Invalid since format: {since_str}")
            return None
    except ValueError:
        logger.warning(f"Invalid since format: {since_str}")
        return None


if __name__ == "__main__":
    main()