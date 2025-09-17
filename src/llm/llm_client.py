from __future__ import annotations

from typing import Any, Iterable
import random
import json
import requests

from ..shared.config import settings
from ..shared.redis_client import get_redis


class LLMClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.local_ai_endpoint
        self.model = settings.local_ai_model
        self.provider = settings.local_ai_provider
        self.local_ai_available = self._check_local_ai_available()
    
    def _check_local_ai_available(self) -> bool:
        """Check if local AI model is available"""
        try:
            if self.provider == "ollama":
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            else:
                # For other local providers, just check if endpoint is reachable
                response = requests.get(f"{self.base_url}/health", timeout=5)
                return response.status_code == 200
        except Exception:
            return False
    
    def generate(self, prompt: str) -> str:
        """Generate response using local AI model"""
        
        # Try local AI first
        if self.local_ai_available:
            try:
                return self._generate_local_ai(prompt)
            except Exception as e:
                print(f"Local AI generation failed: {e}")
        
        # Fallback to local logic
        return self._generate_fallback(prompt)
    
    def _generate_local_ai(self, prompt: str) -> str:
        """Generate response using local AI model"""
        try:
            if self.provider == "ollama":
                return self._generate_ollama(prompt)
            else:
                return self._generate_generic_local(prompt)
                
        except Exception as e:
            raise Exception(f"Local AI API error: {str(e)}")
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate response using Ollama"""
        payload = {
            "model": self.model,
            "prompt": f"System: You are Tapmad's Anti-Piracy AI assistant. Be concise and helpful.\nUser: {prompt}\nAssistant:",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('response', '').strip()
    
    def _generate_generic_local(self, prompt: str) -> str:
        """Generate response using generic local AI endpoint"""
        payload = {
            "prompt": f"System: You are Tapmad's Anti-Piracy AI assistant. Be concise and helpful.\nUser: {prompt}\nAssistant:",
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/generate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('response', data.get('text', '')).strip()
    
    def _generate_fallback(self, prompt: str) -> str:
        """Local fallback response generation"""
        # Simple keyword-based responses for development
        if "scan" in prompt.lower() or "search" in prompt.lower():
            return "I'll help you scan for content. Use the /tools/crawl/search_and_queue endpoint."
        elif "takedown" in prompt.lower() or "dmca" in prompt.lower():
            return "I'll help with takedown requests. Use the /tools/enforce/takedown endpoint."
        elif "report" in prompt.lower() or "status" in prompt.lower():
            return "I'll provide status reports. Use the /tools/report/status endpoint."
        else:
            return "I'm your Tapmad Anti-Piracy AI assistant. I can help with content scanning, takedowns, and reporting."
    
    def expand_keywords(self, request: dict[str, Any]) -> list[str]:
        """Expand seed keywords using local AI"""
        
        seeds = request.get("seeds", [])
        date = request.get("date", "today")
        language = request.get("language", "both")
        
        # Try local AI expansion first
        if self.local_ai_available:
            try:
                return self._expand_keywords_local_ai(seeds, date, language)
            except Exception as e:
                print(f"Local AI keyword expansion failed: {e}")
        
        # Fallback to local expansion
        return self._expand_keywords_local(seeds, date, language)
    
    def _expand_keywords_local_ai(self, seeds: list[str], date: str, language: str) -> list[str]:
        """Expand keywords using local AI"""
        prompt = f"""
        Expand these seed keywords for content discovery:
        Seeds: {', '.join(seeds)}
        Date: {date}
        Language: {language}
        
        Generate 20-30 relevant keywords for finding pirated sports content.
        Include variations, synonyms, and related terms.
        Return only the keywords, one per line.
        """
        
        try:
            response = self.generate(prompt)
            # Parse response into keywords
            keywords = [line.strip() for line in response.split('\n') if line.strip()]
            return keywords[:30]  # Limit to 30 keywords
        except Exception:
            return self._expand_keywords_local(seeds, date, language)
    
    def _expand_keywords_local(self, seeds: list[str], date: str, language: str) -> list[str]:
        """Local keyword expansion fallback"""
        expanded = []
        
        # Base keywords
        base_keywords = [
            "tapmad live", "live cricket", "live football", "live sports",
            "free stream", "free match", "live match", "live game",
            "cricket live", "football live", "sports live", "match live"
        ]
        
        # Add seed-based variations
        for seed in seeds:
            expanded.extend([
                seed,
                f"{seed} live",
                f"live {seed}",
                f"{seed} stream",
                f"free {seed}",
                f"{seed} free"
            ])
        
        # Add language-specific keywords
        if language in ["bn", "both"]:
            bengali_keywords = [
                "ট্যাপম্যাড লাইভ", "লাইভ ক্রিকেট", "লাইভ ফুটবল",
                "ফ্রি স্ট্রিম", "ফ্রি ম্যাচ", "লাইভ ম্যাচ",
                "ক্রিকেট লাইভ", "ফুটবল লাইভ", "স্পোর্টস লাইভ"
            ]
            expanded.extend(bengali_keywords)
        
        # Add date-specific keywords
        if "today" in date.lower():
            expanded.extend(["today", "live now", "streaming now"])
        elif "recent" in date.lower():
            expanded.extend(["recent", "latest", "new"])
        
        # Remove duplicates and limit
        unique_keywords = list(dict.fromkeys(expanded))
        return unique_keywords[:30]
    
    def classify_page(self, content: str, url: str) -> dict[str, Any]:
        """Classify page content using local AI"""
        
        # Try local AI classification first
        if self.local_ai_available:
            try:
                return self._classify_page_local_ai(content, url)
            except Exception as e:
                print(f"Local AI classification failed: {e}")
        
        # Fallback to local classification
        return self._classify_page_local(content, url)
    
    def _classify_page_local_ai(self, content: str, url: str) -> str:
        """Classify page using local AI"""
        prompt = f"""
        Classify this content for anti-piracy purposes:
        
        URL: {url}
        Content: {content[:1000]}...
        
        Analyze and classify:
        1. Content type (sports, entertainment, news, etc.)
        2. Piracy risk level (low, medium, high)
        3. Platform type (social media, streaming, download, etc.)
        4. Recommended action (monitor, flag, takedown)
        
        Return as JSON with these fields.
        """
        
        try:
            response = self.generate(prompt)
            # Try to parse JSON response
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # Fallback if response isn't JSON
                return self._classify_page_local(content, url)
        except Exception:
            return self._classify_page_local(content, url)
    
    def _classify_page_local(self, content: str, url: str) -> dict[str, Any]:
        """Local content classification fallback"""
        content_lower = content.lower()
        url_lower = url.lower()
        
        # Content type detection
        content_type = "unknown"
        if any(word in content_lower for word in ["cricket", "football", "sports", "match", "game"]):
            content_type = "sports"
        elif any(word in content_lower for word in ["movie", "film", "series", "show"]):
            content_type = "entertainment"
        elif any(word in content_lower for word in ["news", "article", "blog"]):
            content_type = "news"
        
        # Piracy risk assessment
        risk_level = "low"
        if any(word in content_lower for word in ["free", "download", "stream", "watch online"]):
            risk_level = "medium"
        if any(word in content_lower for word in ["pirate", "torrent", "crack", "hack"]):
            risk_level = "high"
        
        # Platform detection
        platform_type = "unknown"
        if any(domain in url_lower for domain in ["youtube.com", "youtu.be"]):
            platform_type = "video_sharing"
        elif any(domain in url_lower for domain in ["telegram.org", "t.me"]):
            platform_type = "messaging"
        elif any(domain in url_lower for domain in ["facebook.com", "fb.com"]):
            platform_type = "social_media"
        
        # Recommended action
        action = "monitor"
        if risk_level == "high":
            action = "takedown"
        elif risk_level == "medium":
            action = "flag"
        
        return {
            "content_type": content_type,
            "risk_level": risk_level,
            "platform_type": platform_type,
            "recommended_action": action,
            "confidence": 0.7
        }
    
    def draft_takedown(self, platform: str, url: str, evidence: dict[str, Any]) -> str:
        """Draft DMCA takedown notice using local AI"""
        
        # Try local AI drafting first
        if self.local_ai_available:
            try:
                return self._draft_takedown_local_ai(platform, url, evidence)
            except Exception as e:
                print(f"Local AI takedown drafting failed: {e}")
        
        # Fallback to template
        return self._draft_takedown_template(platform, url, evidence)
    
    def _draft_takedown_local_ai(self, platform: str, url: str, evidence: dict[str, Any]) -> str:
        """Draft takedown using local AI"""
        prompt = f"""
        Draft a professional DMCA takedown notice for this content:
        
        Platform: {platform}
        URL: {url}
        Evidence: {json.dumps(evidence, indent=2)}
        
        Create a formal, professional DMCA takedown notice that includes:
        1. Copyright holder identification
        2. Description of copyrighted work
        3. Description of infringing material
        4. Good faith belief statement
        5. Accuracy statement
        6. Contact information
        
        Make it formal and legally appropriate.
        """
        
        try:
            return self.generate(prompt)
        except Exception:
            return self._draft_takedown_template(platform, url, evidence)
    
    def _draft_takedown_template(self, platform: str, url: str, evidence: dict[str, Any]) -> str:
        """Template-based takedown notice"""
        return f"""
        DMCA TAKEDOWN NOTICE
        
        To: {platform.title()} Legal Department
        From: Tapmad Anti-Piracy Team
        Date: {evidence.get('detected_at', 'Current Date')}
        
        RE: Copyright Infringement - DMCA Takedown Request
        
        Dear {platform.title()} Legal Team,
        
        We are writing to request the immediate removal of content that infringes upon our copyrights.
        
        COPYRIGHTED WORK:
        The content identified below infringes upon our exclusive rights in copyrighted material.
        
        INFRINGING MATERIAL:
        URL: {url}
        Platform: {platform}
        Content Type: {evidence.get('content_type', 'Video/Audio Content')}
        Detection Date: {evidence.get('detected_at', 'Current Date')}
        
        GOOD FAITH BELIEF:
        We have a good faith belief that the use of the copyrighted material is not authorized by the copyright owner, its agent, or the law.
        
        ACCURACY STATEMENT:
        The information in this notice is accurate, and under penalty of perjury, we are authorized to act on behalf of the copyright owner.
        
        REQUESTED ACTION:
        We request that you immediately remove or disable access to the infringing material.
        
        CONTACT INFORMATION:
        Tapmad Anti-Piracy Team
        Email: legal@tapmad.com
        Phone: +880-XXX-XXX-XXXX
        
        We appreciate your prompt attention to this matter.
        
        Sincerely,
        Tapmad Anti-Piracy Team
        """


