from __future__ import annotations

import re
from typing import List, Dict


def search_candidates(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for Twitter/X posts related to the query.
    Returns actual post URLs and user URLs when possible.
    """
    # Common Twitter accounts that might have sports content
    accounts = [
        "tapmad_bd",
        "sports_bangla", 
        "cricket_live_bd",
        "football_streams",
        "live_sports_bd",
        "bpl_live",
        "cricket_world_cup_bd",
        "sports_news_bd"
    ]
    
    results = []
    
    # Add account URLs
    for account in accounts:
        if query.lower() in account.lower() or any(word in account.lower() for word in query.lower().split()):
            results.append({
                "platform": "twitter",
                "url": f"https://x.com/{account}",
                "title": f"Twitter Account: @{account}"
            })
    
    # Add search results
    search_query = query.replace(' ', '+')
    search_url = f"https://x.com/search?q={search_query}&src=typed_query&f=live"
    results.append({
        "platform": "twitter",
        "url": search_url,
        "title": f"Twitter Search: {query}"
    })
    
    # Add hashtag searches
    hashtag_query = f"%23{query.replace(' ', '')}"
    hashtag_url = f"https://x.com/search?q={hashtag_query}&src=hashtag_click&f=live"
    results.append({
        "platform": "twitter",
        "url": hashtag_url,
        "title": f"Twitter Hashtag: #{query.replace(' ', '')}"
    })
    
    return results[:max_results]


def extract_video_urls(tweet_text: str) -> List[str]:
    """
    Extract potential video URLs from tweet text.
    This is a simplified version - in production you'd use Twitter API.
    """
    # Look for common video hosting patterns
    video_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtu\.be/[\w-]+',
        r'https?://(?:www\.)?facebook\.com/.*?/videos/[\d]+',
        r'https?://(?:www\.)?t\.me/[\w]+/\d+',
        r'https?://(?:www\.)?instagram\.com/p/[\w-]+',
    ]
    
    urls = []
    for pattern in video_patterns:
        matches = re.findall(pattern, tweet_text, re.IGNORECASE)
        urls.extend(matches)
    
    return urls


def is_sports_related(tweet_text: str) -> bool:
    """
    Check if tweet text is sports-related.
    """
    sports_keywords = [
        'live', 'stream', 'match', 'game', 'cricket', 'football', 'soccer',
        'sports', 'highlight', 'score', 'commentary', 'broadcast',
        'খেলা', 'লাইভ', 'ম্যাচ', 'স্পোর্টস', 'হাইলাইট'
    ]
    
    tweet_lower = tweet_text.lower()
    return any(keyword in tweet_lower for keyword in sports_keywords)


