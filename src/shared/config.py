from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Settings:
    # Environment detection
    env: str = os.getenv("ENV", "development")
    
    # Database configuration - Working defaults for development
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/antipiracy")
    pg_host: str = os.getenv("PGHOST", "localhost")
    pg_port: int = int(os.getenv("PGPORT", "5432"))
    pg_db: str = os.getenv("PGDATABASE", "antipiracy")
    pg_user: str = os.getenv("PGUSER", "postgres")
    pg_password: str = os.getenv("PGPASSWORD", "postgres")
    
    # Redis configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # S3/MinIO configuration - Working defaults
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "tapmad")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "tapmadsecret")
    s3_bucket: str = os.getenv("S3_BUCKET", "evidence")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    s3_public_endpoint: str = os.getenv("S3_PUBLIC_ENDPOINT", "http://localhost:9000")
    
    # SMTP configuration - Working defaults
    smtp_host: str = os.getenv("SMTP_HOST", "localhost")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "test")
    smtp_pass: str = os.getenv("SMTP_PASS", "test")
    from_email: str = os.getenv("FROM_EMAIL", "test@localhost")
    dmca_from: str = os.getenv("DMCA_FROM", "test@localhost")
    dmca_rcpts: str = os.getenv("DMCA_RCPTS", "test@localhost")
    
    # API configuration - No authentication required
    api_key: str = os.getenv("API_KEY", "devtoken123")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:8089")
    llm_model: str = os.getenv("LLM_MODEL", "gemma-2-2b-it-q4_k_m")
    
    # Production API Keys - Your team just needs to add these
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY_HERE")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
    facebook_access_token: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "YOUR_FACEBOOK_ACCESS_TOKEN_HERE")
    twitter_bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "YOUR_TWITTER_BEARER_TOKEN_HERE")
    instagram_access_token: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "YOUR_INSTAGRAM_ACCESS_TOKEN_HERE")
    
    # Local AI Model Configuration
    local_ai_model: str = os.getenv("LOCAL_AI_MODEL", "gemma-2-2b-it-q4_k_m")
    local_ai_endpoint: str = os.getenv("LOCAL_AI_ENDPOINT", "http://localhost:8089")
    local_ai_provider: str = os.getenv("LOCAL_AI_PROVIDER", "ollama")  # ollama, llama.cpp, etc.
    
    # Rate limiting
    rate_limit_per_min: int = int(os.getenv("RATE_LIMIT_PER_MIN", "1000"))
    
    # Matching thresholds and toggles
    video_threshold: float = float(os.getenv("VIDEO_THRESHOLD", "0.18"))
    audio_threshold: float = float(os.getenv("AUDIO_THRESHOLD", "0.72"))
    video_hamming_review_threshold: int = int(os.getenv("VIDEO_HAMMING_REVIEW_THRESHOLD", "12"))
    video_hamming_approve_threshold: int = int(os.getenv("VIDEO_HAMMING_APPROVE_THRESHOLD", "8"))
    llm_min_score: float = float(os.getenv("LLM_MIN_SCORE", "0.3"))
    provider_actions_enabled: bool = os.getenv("PROVIDER_ACTIONS_ENABLED", "true").lower() in {"1","true","yes"}
    
    # Enforcement configuration
    enforcement_dry_run: bool = os.getenv("ENFORCEMENT_DRY_RUN", "true").lower() in {"1","true","yes"}
    crawl_max_per_run: int = int(os.getenv("CRAWL_MAX_PER_RUN", "25"))
    
    # Scanning configuration
    max_candidates_per_scan: int = int(os.getenv("MAX_CANDIDATES_PER_SCAN", "50"))
    scan_timeout_seconds: int = int(os.getenv("SCAN_TIMEOUT_SECONDS", "600"))
    enable_auto_enforcement: bool = os.getenv("ENABLE_AUTO_ENFORCEMENT", "true").lower() in {"1","true","yes"}
    
    # Security configuration - Open for development
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_credentials: bool = os.getenv("CORS_CREDENTIALS", "true").lower() in {"1","true","yes"}
    max_request_size: int = int(os.getenv("MAX_REQUEST_SIZE", "104857600"))  # 100MB default
    session_timeout: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour default
    
    def __post_init__(self):
        """Development-friendly configuration"""
        if self.env == "production":
            print("🚀 Production mode: API keys required")
            self._validate_production_keys()
        else:
            print("🔧 Development mode: Using working configuration")
            print(f"   Database: {self.pg_host}:{self.pg_port}/{self.pg_db}")
            print(f"   Redis: {self.redis_url}")
            print(f"   S3: {self.s3_endpoint}")
            print(f"   CORS: Open for development")
    
    def _validate_production_keys(self):
        """Validate production API keys"""
        required_keys = [
            ("YOUTUBE_API_KEY", self.youtube_api_key),
            ("TELEGRAM_BOT_TOKEN", self.telegram_bot_token),
            ("FACEBOOK_ACCESS_TOKEN", self.facebook_access_token),
            ("TWITTER_BEARER_TOKEN", self.twitter_bearer_token),
            ("INSTAGRAM_ACCESS_TOKEN", self.instagram_access_token),
        ]
        
        missing_keys = [name for name, value in required_keys if value.startswith("YOUR_") or not value]
        
        if missing_keys:
            print(f"❌ Missing production API keys: {', '.join(missing_keys)}")
            print("   Please set these environment variables before deployment")
        else:
            print("✅ All production API keys configured")
            print(f"   YouTube API: {'✓' if self.youtube_api_key else '✗'}")
            print(f"   Telegram Bot: {'✓' if self.telegram_bot_token else '✗'}")
            print(f"   Facebook: {'✓' if self.facebook_access_token else '✗'}")
            print(f"   Twitter: {'✓' if self.twitter_bearer_token else '✗'}")
            print(f"   Instagram: {'✓' if self.instagram_access_token else '✗'}")


settings = Settings()


