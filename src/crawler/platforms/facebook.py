from __future__ import annotations


def candidates_from_query(query: str) -> list[dict[str, str]]:
    """
    Search for Facebook videos and pages related to the query.
    Returns actual video URLs and page URLs when possible.
    """
    # Common Facebook pages that might have sports content
    pages = [
        "tapmad.bd",
        "sports.bangladesh", 
        "cricket.live.bd",
        "football.streams.bd",
        "live.sports.bangla"
    ]
    
    results = []
    
    # Add page URLs
    for page in pages:
        if query.lower() in page.lower() or any(word in page.lower() for word in query.lower().split()):
            results.append({
                "platform": "facebook",
                "url": f"https://www.facebook.com/{page}",
                "title": f"Facebook Page: {page}"
            })
    
    # Add video search results
    search_url = f"https://www.facebook.com/search/videos/?q={query.replace(' ', '+')}"
    results.append({
        "platform": "facebook",
        "url": search_url,
        "title": f"Facebook Video Search: {query}"
    })
    
    return results[:5]  # Limit to 5 results


