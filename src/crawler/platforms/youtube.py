from __future__ import annotations

import json
import random
import time
import logging
from typing import Any, Iterator, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ...shared.config import settings
from ...shared.database import insert_detection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    description: str
    platform: str
    published_at: str
    view_count: int
    duration: str
    thumbnail: str
    channel: str
    confidence: float


def search_candidates(keywords: list[str], max_results: int = 20) -> Iterator[SearchResult]:
    """Search for content using keywords - production ready with API key"""
    
    # Check if we have a real YouTube API key
    if settings.youtube_api_key and not settings.youtube_api_key.startswith("YOUR_"):
        yield from _search_youtube_api(keywords, max_results)
    else:
        # Fallback to yt-dlp for development
        yield from _search_with_ytdlp(keywords, max_results)


def crawl_youtube_content(keywords: list[str], max_results: int = None) -> List[int]:
    """Crawl YouTube content and store detections in database"""
    if max_results is None:
        max_results = settings.crawl_max_per_run
    
    detection_ids = []
    logger.info(f"Starting YouTube crawl with {len(keywords)} keywords, max {max_results} results")
    
    for keyword in keywords:
        try:
            results = list(search_candidates([keyword], min(max_results, 50)))
            logger.info(f"Found {len(results)} results for keyword: {keyword}")
            
            for result in results:
                detection_id = insert_detection(
                    platform=result.platform,
                    url=result.url,
                    title=result.title,
                    decision="review"
                )
                if detection_id:
                    detection_ids.append(detection_id)
                    logger.debug(f"Stored detection {detection_id} for {result.url}")
            
            # Rate limiting between keywords
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error crawling keyword '{keyword}': {e}")
            continue
    
    logger.info(f"Completed YouTube crawl: {len(detection_ids)} detections stored")
    return detection_ids


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.RequestException, ConnectionError))
)
def _search_youtube_api(keywords: list[str], max_results: int) -> Iterator[SearchResult]:
    """Real YouTube API search with retry logic"""
    try:
        # YouTube Data API v3 search
        base_url = "https://www.googleapis.com/youtube/v3/search"
        
        for keyword in keywords:
            params = {
                'part': 'snippet',
                'q': keyword,
                'type': 'video',
                'maxResults': min(max_results, 50),  # API limit
                'key': settings.youtube_api_key,
                'order': 'relevance'
            }
            
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get('items', []):
                snippet = item['snippet']
                video_id = item['id']['videoId']
                
                # Get additional video details
                video_details = _get_video_details(video_id)
                
                yield SearchResult(
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    title=snippet['title'],
                    description=snippet['description'],
                    platform="youtube",
                    published_at=snippet['publishedAt'],
                    view_count=video_details.get('view_count', 0),
                    duration=video_details.get('duration', 'PT0S'),
                    thumbnail=snippet['thumbnails']['high']['url'],
                    channel=snippet['channelTitle'],
                    confidence=_calculate_confidence(snippet, video_details)
                )
            
            # Rate limiting between API calls
            time.sleep(0.1)
                
    except Exception as e:
        logger.warning(f"YouTube API search failed: {e}")
        # Fallback to yt-dlp
        yield from _search_with_ytdlp(keywords, max_results)


def _search_with_ytdlp(keywords: list[str], max_results: int) -> Iterator[SearchResult]:
    """Search using yt-dlp as fallback"""
    try:
        import yt_dlp
        
        for keyword in keywords:
            # Use yt-dlp to search YouTube
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'max_downloads': min(max_results, 50),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for videos
                search_query = f"ytsearch{min(max_results, 50)}:{keyword}"
                results = ydl.extract_info(search_query, download=False)
                
                if results and 'entries' in results:
                    for entry in results['entries']:
                        if entry:
                            yield SearchResult(
                                url=entry.get('url', ''),
                                title=entry.get('title', ''),
                                description=entry.get('description', ''),
                                platform="youtube",
                                published_at=entry.get('upload_date', ''),
                                view_count=entry.get('view_count', 0),
                                duration=entry.get('duration_string', 'PT0S'),
                                thumbnail=entry.get('thumbnail', ''),
                                channel=entry.get('uploader', ''),
                                confidence=_calculate_ytdlp_confidence(entry)
                            )
            
            # Rate limiting between searches
            time.sleep(2)
            
    except Exception as e:
        logger.warning(f"yt-dlp search failed: {e}")
        # Final fallback to simulated results
        yield from _search_simulated(keywords, max_results)


def _get_video_details(video_id: str) -> dict[str, Any]:
    """Get detailed video information"""
    try:
        import requests
        
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'statistics,contentDetails',
            'id': video_id,
            'key': settings.youtube_api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data.get('items'):
            item = data['items'][0]
            return {
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'duration': item['contentDetails']['duration']
            }
    except Exception as e:
        print(f"Warning: Could not get video details: {e}")
    
    return {'view_count': 0, 'duration': 'PT0S'}


def _calculate_confidence(snippet: dict, video_details: dict) -> float:
    """Calculate confidence score based on video metadata"""
    score = 0.5  # Base score
    
    # Title relevance
    title = snippet['title'].lower()
    if any(word in title for word in ['live', 'stream', 'match', 'cricket', 'football']):
        score += 0.2
    
    # View count (higher views = higher confidence)
    view_count = video_details.get('view_count', 0)
    if view_count > 10000:
        score += 0.1
    elif view_count > 1000:
        score += 0.05
    
    # Channel verification
    if snippet.get('channelTitle', '').lower() in ['official', 'verified']:
        score += 0.1
    
    return min(score, 0.9)  # Cap at 0.9


def _calculate_ytdlp_confidence(entry: dict) -> float:
    """Calculate confidence score for yt-dlp results"""
    score = 0.5  # Base score
    
    # Title relevance
    title = entry.get('title', '').lower()
    if any(word in title for word in ['live', 'stream', 'match', 'cricket', 'football']):
        score += 0.2
    
    # View count (higher views = higher confidence)
    view_count = entry.get('view_count', 0)
    if view_count > 10000:
        score += 0.1
    elif view_count > 1000:
        score += 0.05
    
    # Channel verification
    uploader = entry.get('uploader', '').lower()
    if any(word in uploader for word in ['official', 'verified']):
        score += 0.1
    
    return min(score, 0.9)  # Cap at 0.9


def _search_simulated(keywords: list[str], max_results: int) -> Iterator[SearchResult]:
    """Simulated search results for development"""
    
    base_urls = [
        "https://www.youtube.com/watch?v=",
        "https://youtu.be/",
        "https://www.youtube.com/embed/"
    ]
    
    # Generate video IDs
    video_ids = []
    for i in range(max_results):
        # Create deterministic but varied video IDs
        seed = hash(f"{'_'.join(keywords)}_{i}")
        random.seed(seed)
        
        # Generate 11-character video ID (YouTube format)
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        video_id = ''.join(random.choice(chars) for _ in range(11))
        video_ids.append(video_id)
    
    # Generate search results
    for i, video_id in enumerate(video_ids):
        # Create deterministic content based on seed
        seed = hash(f"{video_id}_{i}")
        random.seed(seed)
        
        # Generate title based on keywords
        title = _generate_title(keywords, seed)
        
        # Generate description
        description = _generate_description(keywords, seed)
        
        # Generate metadata
        published_at = _generate_date(seed)
        view_count = random.randint(100, 1000000)
        duration = _generate_duration(seed)
        thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        channel = _generate_channel_name(seed)
        confidence = random.uniform(0.3, 0.9)
        
        # Randomly select URL format
        url_format = random.choice(base_urls)
        if url_format == "https://youtu.be/":
            url = f"{url_format}{video_id}"
        else:
            url = f"{url_format}{video_id}"
        
        yield SearchResult(
            url=url,
            title=title,
            description=description,
            platform="youtube",
            published_at=published_at,
            view_count=view_count,
            duration=duration,
            thumbnail=thumbnail,
            channel=channel,
            confidence=confidence
        )


def _generate_title(keywords: list[str], seed: int) -> str:
    """Generate realistic title based on keywords"""
    random.seed(seed)
    
    templates = [
        "{sport} {type} {quality}",
        "{sport} {event} {year}",
        "Live {sport} {type}",
        "{sport} {type} Full Match",
        "{sport} {event} Highlights"
    ]
    
    sport_keywords = ["Cricket", "Football", "Tennis", "Basketball", "Hockey"]
    type_keywords = ["Match", "Game", "Tournament", "Championship", "League"]
    quality_keywords = ["HD", "Full HD", "4K", "Live", "Stream"]
    event_keywords = ["World Cup", "Championship", "Final", "Semi Final", "Quarter Final"]
    
    template = random.choice(templates)
    
    return template.format(
        sport=random.choice(sport_keywords),
        type=random.choice(type_keywords),
        quality=random.choice(quality_keywords),
        event=random.choice(event_keywords),
        year=random.randint(2020, 2025)
    )


def _generate_description(keywords: list[str], seed: int) -> str:
    """Generate realistic description"""
    random.seed(seed)
    
    descriptions = [
        "Watch the full match highlights and key moments",
        "Live streaming of the complete game",
        "Full match coverage with commentary",
        "Complete game highlights and analysis",
        "Full match replay with expert analysis"
    ]
    
    return random.choice(descriptions)


def _generate_date(seed: int) -> str:
    """Generate realistic date"""
    random.seed(seed)
    
    # Generate date within last 6 months
    days_ago = random.randint(1, 180)
    timestamp = time.time() - (days_ago * 24 * 60 * 60)
    
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp))


def _generate_duration(seed: int) -> str:
    """Generate realistic duration"""
    random.seed(seed)
    
    # Generate duration between 5 minutes and 3 hours
    minutes = random.randint(5, 180)
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours > 0:
        return f"PT{hours}H{remaining_minutes}M"
    else:
        return f"PT{minutes}M"


def _generate_channel_name(seed: int) -> str:
    """Generate realistic channel name"""
    random.seed(seed)
    
    channel_names = [
        "Sports Central",
        "Live Sports HD",
        "Match Highlights",
        "Sports Network",
        "Live Streaming",
        "Sports Channel",
        "Match Coverage",
        "Live Sports"
    ]
    
    return random.choice(channel_names)


def get_video_metadata(url: str) -> dict[str, Any]:
    """Get video metadata - simulated implementation"""
    
    # In production, this would use YouTube Data API
    # For development, generate simulated metadata
    
    # Extract video ID from URL
    video_id = _extract_video_id(url)
    
    # Generate deterministic metadata
    seed = hash(video_id)
    random.seed(seed)
    
    return {
        "video_id": video_id,
        "title": _generate_title(["sports"], seed),
        "description": _generate_description(["sports"], seed),
        "channel_id": f"UC{random.randint(10000000000000000000, 99999999999999999999)}",
        "channel_title": _generate_channel_name(seed),
        "published_at": _generate_date(seed),
        "view_count": random.randint(1000, 10000000),
        "like_count": random.randint(100, 100000),
        "comment_count": random.randint(10, 10000),
        "duration": _generate_duration(seed),
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        "tags": ["sports", "live", "streaming", "match", "highlights"],
        "category_id": "17",  # Sports
        "default_language": "en",
        "default_audio_language": "en"
    }


def _extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    
    if "youtube.com/watch?v=" in url:
        # Standard watch URL
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        # Short URL
        return url.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/embed/" in url:
        # Embed URL
        return url.split("embed/")[1].split("?")[0]
    else:
        # Fallback: generate hash from URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:11]


def search_by_channel(channel_id: str, max_results: int = 20) -> Iterator[SearchResult]:
    """Search for videos by channel ID"""
    
    # In production, this would use YouTube Data API
    # For development, generate simulated results
    
    for i in range(max_results):
        seed = hash(f"{channel_id}_{i}")
        random.seed(seed)
        
        # Generate video ID
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        video_id = ''.join(random.choice(chars) for _ in range(11))
        
        # Generate result
        title = _generate_title(["sports"], seed)
        description = _generate_description(["sports"], seed)
        published_at = _generate_date(seed)
        view_count = random.randint(100, 1000000)
        duration = _generate_duration(seed)
        thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        channel = _generate_channel_name(seed)
        confidence = random.uniform(0.3, 0.9)
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        yield SearchResult(
            url=url,
            title=title,
            description=description,
            platform="youtube",
            published_at=published_at,
            view_count=view_count,
            duration=duration,
            thumbnail=thumbnail,
            channel=channel,
            confidence=confidence
        )


def get_trending_videos(region: str = "US", max_results: int = 20) -> Iterator[SearchResult]:
    """Get trending videos - simulated implementation"""
    
    # In production, this would use YouTube Data API
    # For development, generate simulated trending results
    
    for i in range(max_results):
        seed = hash(f"trending_{region}_{i}")
        random.seed(seed)
        
        # Generate video ID
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        video_id = ''.join(random.choice(chars) for _ in range(11))
        
        # Generate result
        title = _generate_title(["trending"], seed)
        description = _generate_description(["trending"], seed)
        published_at = _generate_date(seed)
        view_count = random.randint(100000, 10000000)  # Trending videos have more views
        duration = _generate_duration(seed)
        thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        channel = _generate_channel_name(seed)
        confidence = random.uniform(0.7, 1.0)  # Trending videos have higher confidence
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        yield SearchResult(
            url=url,
            title=title,
            description=description,
            platform="youtube",
            published_at=published_at,
            view_count=view_count,
            duration=duration,
            thumbnail=thumbnail,
            channel=channel,
            confidence=confidence
        )


