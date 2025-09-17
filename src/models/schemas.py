from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, validator, HttpUrl
import re
from dataclasses import field

Decision = Literal["approve", "review", "reject"]
TakedownStatus = Literal["pending", "sent", "failed"]

class Detection(BaseModel):
    id: int = Field(..., gt=0, description="Unique detection identifier")
    platform: str = Field(..., min_length=1, max_length=50, description="Platform name")
    url: str = Field(..., description="Content URL")
    title: Optional[str] = Field(None, max_length=500, description="Content title")
    detected_at: datetime = Field(..., description="Detection timestamp")
    video_hash: Optional[str] = Field(None, max_length=64, description="Video fingerprint hash")
    audio_fp: Optional[str] = Field(None, max_length=64, description="Audio fingerprint")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    watermark_id: Optional[str] = Field(None, max_length=100, description="Watermark identifier")
    evidence_key: Optional[str] = Field(None, max_length=200, description="Evidence storage key")
    decision: Optional[Decision] = Field(None, description="Detection decision")
    takedown_status: Optional[TakedownStatus] = Field(None, description="Takedown status")

    @validator('platform')
    def validate_platform(cls, v):
        allowed_platforms = ['youtube', 'telegram', 'facebook', 'twitter', 'instagram', 'google']
        if v.lower() not in allowed_platforms:
            raise ValueError(f'Platform must be one of: {", ".join(allowed_platforms)}')
        return v.lower()

    @validator('url')
    def validate_url(cls, v):
        if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', v):
            raise ValueError('Invalid URL format')
        return v

    @validator('video_hash', 'audio_fp')
    def validate_hash(cls, v):
        if v is not None:
            if not re.match(r'^[a-fA-F0-9]{16,64}$', v):
                raise ValueError('Hash must be hexadecimal string')
        return v

class DetectionCreate(BaseModel):
    platform: str = Field(..., min_length=1, max_length=50)
    url: str = Field(..., description="Content URL")
    title: Optional[str] = Field(None, max_length=500)
    video_hash: Optional[str] = Field(None, max_length=64)
    audio_fp: Optional[str] = Field(None, max_length=64)
    confidence: float = Field(..., ge=0.0, le=1.0)
    watermark_id: Optional[str] = Field(None, max_length=100)
    evidence_key: Optional[str] = Field(None, max_length=200)
    decision: Optional[Decision] = None

    @validator('platform')
    def validate_platform(cls, v):
        allowed_platforms = ['youtube', 'telegram', 'facebook', 'twitter', 'instagram', 'google']
        if v.lower() not in allowed_platforms:
            raise ValueError(f'Platform must be one of: {", ".join(allowed_platforms)}')
        return v.lower()

    @validator('url')
    def validate_url(cls, v):
        if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', v):
            raise ValueError('Invalid URL format')
        return v

# New validation schemas for API endpoints
class CrawlRequest(BaseModel):
    keywords: list[str] = Field(..., min_items=1, max_items=100, description="Search keywords")
    platforms: list[str] = Field(default_factory=lambda: ["youtube"], min_items=1, max_items=10, description="Platforms to search")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum results to return")
    urls: Optional[list[str]] = Field(default=None, description="Direct URLs to process")
    titles: Optional[list[str]] = Field(default=None, description="Titles for direct URLs")
    max_items: int = Field(default=50, ge=1, le=200, description="Maximum items to process")

    @validator('platforms')
    def validate_platforms(cls, v):
        allowed_platforms = ['youtube', 'telegram', 'facebook', 'twitter', 'instagram', 'google']
        for platform in v:
            if platform.lower() not in allowed_platforms:
                raise ValueError(f'Invalid platform: {platform}')
        return [p.lower() for p in v]

    @validator('keywords')
    def validate_keywords(cls, v):
        if v is not None:
            for keyword in v:
                if len(keyword.strip()) == 0 or len(keyword) > 200:
                    raise ValueError('Keywords must be non-empty and under 200 characters')
        return v

    @validator('urls')
    def validate_urls(cls, v):
        if v is not None:
            for url in v:
                if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', url):
                    raise ValueError(f'Invalid URL: {url}')
        return v

class FingerprintRequest(BaseModel):
    url: str = Field(..., description="URL to capture and fingerprint")
    title: Optional[str] = Field(default=None, description="Content title")
    platform: Optional[str] = Field(default=None, description="Platform name")

class MatchRequest(BaseModel):
    candidate_id: int = Field(..., gt=0, description="Candidate identifier")

class TakedownRequest(BaseModel):
    detection_id: int = Field(..., gt=0, description="Detection identifier")
    providers: Optional[list[str]] = Field(None, max_items=20, description="Platform providers")

class ThresholdUpdateRequest(BaseModel):
    video_hamming: Optional[int] = Field(None, ge=0, le=64, description="Video hamming threshold")
    approve_conf: Optional[float] = Field(None, ge=0.0, le=1.0, description="Approval confidence threshold")

class KeywordExpansionRequest(BaseModel):
    seeds: list[str] = Field(..., min_items=1, max_items=50, description="Seed keywords")
    date: Optional[str] = Field(None, description="Date context for expansion")
    language: Optional[str] = Field("both", description="Language preference")

    @validator('seeds')
    def validate_seeds(cls, v):
        for seed in v:
            if len(seed.strip()) == 0 or len(seed) > 200:
                raise ValueError('Seed keywords must be non-empty and under 200 characters')
        return v

    @validator('language')
    def validate_language(cls, v):
        allowed_languages = ['en', 'bn', 'both']
        if v not in allowed_languages:
            raise ValueError(f'Language must be one of: {", ".join(allowed_languages)}')
        return v

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Chat message")

    @validator('message')
    def validate_message(cls, v):
        # Basic content filtering
        if re.search(r'<script|javascript:|data:text/html', v, re.IGNORECASE):
            raise ValueError('Message contains potentially dangerous content')
        return v.strip()

# Response schemas
class APIResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[dict] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


