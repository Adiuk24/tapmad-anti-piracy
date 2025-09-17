from __future__ import annotations

import re
from typing import List, Dict
from urllib.parse import quote_plus


def search_candidates(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for Google results related to the query.
    Returns search URLs and potential video hosting sites.
    """
    results = []
    
    # Create Google search URLs with different search strategies
    search_queries = [
        f'"{query}" live stream',
        f'"{query}" watch online',
        f'"{query}" free streaming',
        f'"{query}" live match',
        f'"{query}" highlights',
        f'"{query}" full match',
        f'"{query}" replay',
        f'"{query}" live score',
        f'"{query}" commentary',
        f'"{query}" broadcast'
    ]
    
    # Add Bengali language searches
    bengali_queries = [
        f'"{query}" লাইভ স্ট্রিম',
        f'"{query}" অনলাইন দেখুন',
        f'"{query}" ফ্রি স্ট্রিমিং',
        f'"{query}" লাইভ ম্যাচ',
        f'"{query}" হাইলাইটস',
        f'"{query}" সম্পূর্ণ ম্যাচ',
        f'"{query}" রিপ্লে',
        f'"{query}" লাইভ স্কোর',
        f'"{query}" কমেন্টারি',
        f'"{query}" সম্প্রচার'
    ]
    
    # Combine English and Bengali queries
    all_queries = search_queries + bengali_queries
    
    for search_query in all_queries[:max_results]:
        # Create Google search URL
        encoded_query = quote_plus(search_query)
        search_url = f"https://www.google.com/search?q={encoded_query}&tbm=vid"
        
        results.append({
            "platform": "google",
            "url": search_url,
            "title": f"Google Video Search: {search_query}"
        })
    
    # Add specific video hosting site searches
    video_sites = [
        "youtube.com",
        "dailymotion.com", 
        "vimeo.com",
        "facebook.com/videos",
        "twitter.com",
        "instagram.com",
        "tiktok.com",
        "reddit.com/r/soccerstreams",
        "reddit.com/r/footballhighlights",
        "streamable.com",
        "clippituser.tv",
        "v.redd.it"
    ]
    
    for site in video_sites[:3]:  # Limit to 3 site-specific searches
        site_query = f'"{query}" site:{site}'
        encoded_query = quote_plus(site_query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        results.append({
            "platform": "google",
            "url": search_url,
            "title": f"Google Search on {site}: {query}"
        })
    
    return results[:max_results]


def extract_video_urls(search_results: str) -> List[str]:
    """
    Extract potential video URLs from Google search results.
    This is a simplified version - in production you'd use Google Search API.
    """
    # Look for common video hosting patterns
    video_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtu\.be/[\w-]+',
        r'https?://(?:www\.)?dailymotion\.com/video/[\w-]+',
        r'https?://(?:www\.)?vimeo\.com/\d+',
        r'https?://(?:www\.)?facebook\.com/.*?/videos/[\d]+',
        r'https?://(?:www\.)?t\.me/[\w]+/\d+',
        r'https?://(?:www\.)?instagram\.com/p/[\w-]+',
        r'https?://(?:www\.)?instagram\.com/reel/[\w-]+',
        r'https?://(?:www\.)?tiktok\.com/@[\w]+/video/[\d]+',
        r'https?://(?:www\.)?reddit\.com/r/[\w]+/comments/[\w]+',
        r'https?://(?:www\.)?streamable\.com/[\w]+',
        r'https?://(?:www\.)?clippituser\.tv/c/[\w]+',
        r'https?://v\.redd\.it/[\w]+'
    ]
    
    urls = []
    for pattern in video_patterns:
        matches = re.findall(pattern, search_results, re.IGNORECASE)
        urls.extend(matches)
    
    return urls


def is_sports_related(search_text: str) -> bool:
    """
    Check if search text is sports-related.
    """
    sports_keywords = [
        'live', 'stream', 'match', 'game', 'cricket', 'football', 'soccer',
        'sports', 'highlight', 'score', 'commentary', 'broadcast',
        'tournament', 'league', 'championship', 'cup', 'final',
        'খেলা', 'লাইভ', 'ম্যাচ', 'স্পোর্টস', 'হাইলাইট', 'টুর্নামেন্ট',
        'লিগ', 'চ্যাম্পিয়নশিপ', 'কাপ', 'ফাইনাল'
    ]
    
    text_lower = search_text.lower()
    return any(keyword in text_lower for keyword in sports_keywords)


def is_live_content(search_text: str) -> bool:
    """
    Check if search text indicates live content.
    """
    live_indicators = [
        'live', 'streaming', 'live now', 'watch live', 'live match',
        'live score', 'live commentary', 'live broadcast',
        'লাইভ', 'স্ট্রিমিং', 'লাইভ এখন', 'লাইভ ম্যাচ',
        'লাইভ স্কোর', 'লাইভ কমেন্টারি', 'লাইভ সম্প্রচার'
    ]
    
    text_lower = search_text.lower()
    return any(indicator in text_lower for indicator in live_indicators)


def get_search_suggestions(query: str) -> List[str]:
    """
    Get search suggestions for better coverage.
    """
    base_suggestions = [
        f"{query} live",
        f"{query} stream",
        f"{query} watch",
        f"{query} online",
        f"{query} free",
        f"{query} highlights",
        f"{query} full match",
        f"{query} replay",
        f"{query} commentary",
        f"{query} broadcast"
    ]
    
    # Add Bengali suggestions
    bengali_suggestions = [
        f"{query} লাইভ",
        f"{query} স্ট্রিম",
        f"{query} দেখুন",
        f"{query} অনলাইন",
        f"{query} ফ্রি",
        f"{query} হাইলাইটস",
        f"{query} সম্পূর্ণ ম্যাচ",
        f"{query} রিপ্লে",
        f"{query} কমেন্টারি",
        f"{query} সম্প্রচার"
    ]
    
    return base_suggestions + bengali_suggestions
