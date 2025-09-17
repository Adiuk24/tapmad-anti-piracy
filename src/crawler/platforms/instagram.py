from __future__ import annotations

import re
from typing import List, Dict


def search_candidates(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for Instagram posts and stories related to the query.
    Returns actual post URLs and user URLs when possible.
    """
    # Common Instagram accounts that might have sports content
    accounts = [
        "tapmad.bd",
        "sports.bangladesh", 
        "cricket.live.bd",
        "football.streams",
        "live.sports.bd",
        "bpl.live",
        "cricket.world.cup.bd",
        "sports.news.bd"
    ]
    
    results = []
    
    # Add account URLs
    for account in accounts:
        if query.lower() in account.lower() or any(word in account.lower() for word in query.lower().split()):
            results.append({
                "platform": "instagram",
                "url": f"https://www.instagram.com/{account}/",
                "title": f"Instagram Account: @{account}"
            })
    
    # Add search results
    search_query = query.replace(' ', '+')
    search_url = f"https://www.instagram.com/explore/tags/{search_query}/"
    results.append({
        "platform": "instagram",
        "url": search_url,
        "title": f"Instagram Hashtag: #{query.replace(' ', '')}"
    })
    
    # Add location-based searches for sports venues
    sports_locations = [
        "sher-e-bangla-national-cricket-stadium",
        "bangabandhu-national-stadium",
        "mirpur-sher-e-bangla-cricket-stadium"
    ]
    
    for location in sports_locations:
        if any(word in location for word in query.lower().split()):
            results.append({
                "platform": "instagram",
                "url": f"https://www.instagram.com/explore/locations/{location}/",
                "title": f"Instagram Location: {location.replace('-', ' ').title()}"
            })
    
    return results[:max_results]


def extract_video_urls(post_text: str) -> List[str]:
    """
    Extract potential video URLs from Instagram post text.
    """
    # Look for common video hosting patterns
    video_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtu\.be/[\w-]+',
        r'https?://(?:www\.)?facebook\.com/.*?/videos/[\d]+',
        r'https?://(?:www\.)?t\.me/[\w]+/\d+',
        r'https?://(?:www\.)?instagram\.com/p/[\w-]+',
        r'https?://(?:www\.)?instagram\.com/reel/[\w-]+',
    ]
    
    urls = []
    for pattern in video_patterns:
        matches = re.findall(pattern, post_text, re.IGNORECASE)
        urls.extend(matches)
    
    return urls


def is_sports_related(post_text: str) -> bool:
    """
    Check if Instagram post text is sports-related.
    """
    sports_keywords = [
        'live', 'stream', 'match', 'game', 'cricket', 'football', 'soccer',
        'sports', 'highlight', 'score', 'commentary', 'broadcast',
        'stadium', 'ground', 'field', 'pitch', 'team', 'player',
        'খেলা', 'লাইভ', 'ম্যাচ', 'স্পোর্টস', 'হাইলাইট', 'স্টেডিয়াম'
    ]
    
    post_lower = post_text.lower()
    return any(keyword in post_lower for keyword in sports_keywords)


def extract_hashtags(post_text: str) -> List[str]:
    """
    Extract hashtags from Instagram post text.
    """
    hashtag_pattern = r'#(\w+)'
    hashtags = re.findall(hashtag_pattern, post_text)
    return hashtags


def is_live_content(post_text: str) -> bool:
    """
    Check if post indicates live content.
    """
    live_indicators = [
        'live', 'streaming', 'live now', 'watch live', 'live match',
        'লাইভ', 'স্ট্রিমিং', 'লাইভ এখন', 'লাইভ ম্যাচ'
    ]
    
    post_lower = post_text.lower()
    return any(indicator in post_lower for indicator in live_indicators)
