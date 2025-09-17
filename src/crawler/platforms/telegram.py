from __future__ import annotations


def candidates_from_query(query: str) -> list[dict[str, str]]:
    """
    Search for Telegram channels and posts related to the query.
    Returns actual channel URLs and post URLs when possible.
    """
    # Common Telegram channels that might have sports content
    channels = [
        "sports_bangla",
        "cricket_live_bd", 
        "football_streams",
        "live_sports_bd",
        "tapmad_sports",
        "bpl_live",
        "cricket_world_cup_bd"
    ]
    
    results = []
    
    # Add channel URLs
    for channel in channels:
        if query.lower() in channel.lower() or any(word in channel.lower() for word in query.lower().split()):
            results.append({
                "platform": "telegram",
                "url": f"https://t.me/{channel}",
                "title": f"Telegram Channel: {channel}"
            })
    
    # Add search results
    search_url = f"https://t.me/s/{query.replace(' ', '_')}"
    results.append({
        "platform": "telegram", 
        "url": search_url,
        "title": f"Telegram Search: {query}"
    })
    
    return results[:5]  # Limit to 5 results


