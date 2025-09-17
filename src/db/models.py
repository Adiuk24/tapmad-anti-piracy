from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, JSON, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class Reference(Base):
    """Reference content fingerprints for matching"""
    __tablename__ = 'references'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    platform = Column(String(50), nullable=False)
    content_type = Column(String(50), nullable=False, default='video')
    ref_hash_video = Column(JSONB, nullable=True)  # Video fingerprint data
    ref_hash_audio = Column(JSONB, nullable=True)  # Audio fingerprint data
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    matches = relationship("Match", back_populates="reference")
    
    # Indexes
    __table_args__ = (
        Index('idx_references_platform', 'platform'),
        Index('idx_references_content_type', 'content_type'),
        Index('idx_references_created_at', 'created_at'),
    )


class Detection(Base):
    """Detected content candidates"""
    __tablename__ = 'detections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    video_hash = Column(String(255), nullable=True)
    audio_fp = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    watermark_id = Column(String(255), nullable=True)
    evidence_key = Column(String(255), nullable=True)
    decision = Column(String(20), nullable=True)
    takedown_status = Column(String(20), nullable=True)
    
    # Relationships
    evidence = relationship("Evidence", back_populates="detection", uselist=False)
    matches = relationship("Match", back_populates="detection")
    enforcements = relationship("Enforcement", back_populates="detection")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "decision IN ('approve', 'review', 'reject')",
            name='ck_detections_decision'
        ),
        CheckConstraint(
            "takedown_status IN ('pending', 'sent', 'failed')",
            name='ck_detections_takedown_status'
        ),
        Index('idx_detections_platform', 'platform'),
        Index('idx_detections_decision', 'decision'),
        Index('idx_detections_detected_at', 'detected_at'),
        Index('idx_detections_url', 'url'),
        Index('idx_detections_confidence', 'confidence'),
        UniqueConstraint('platform', 'url', name='uq_detections_platform_url'),
    )


class Evidence(Base):
    """Evidence artifacts and fingerprints"""
    __tablename__ = 'evidence'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    detection_id = Column(Integer, ForeignKey('detections.id'), nullable=False)
    s3_key_json = Column(JSONB, nullable=True)  # S3 keys for artifacts
    video_fp = Column(JSONB, nullable=True)  # Video fingerprint data
    audio_fp = Column(JSONB, nullable=True)  # Audio fingerprint data
    duration_sec = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    detection = relationship("Detection", back_populates="evidence")
    
    # Indexes
    __table_args__ = (
        Index('idx_evidence_detection_id', 'detection_id'),
        Index('idx_evidence_created_at', 'created_at'),
    )


class Match(Base):
    """Matching results between detections and references"""
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    detection_id = Column(Integer, ForeignKey('detections.id'), nullable=False)
    reference_id = Column(Integer, ForeignKey('references.id'), nullable=False)
    video_score = Column(Float, nullable=False, default=0.0)
    audio_score = Column(Float, nullable=False, default=0.0)
    decision = Column(
        String(20), 
        nullable=False, 
        default='none',
        server_default='none'
    )
    threshold_video = Column(Float, nullable=False, default=0.18)
    threshold_audio = Column(Float, nullable=False, default=0.72)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    detection = relationship("Detection", back_populates="matches")
    reference = relationship("Reference", back_populates="matches")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "decision IN ('match', 'likely', 'none')",
            name='ck_matches_decision'
        ),
        CheckConstraint(
            "video_score >= 0.0 AND video_score <= 1.0",
            name='ck_matches_video_score'
        ),
        CheckConstraint(
            "audio_score >= 0.0 AND audio_score <= 1.0",
            name='ck_matches_audio_score'
        ),
        Index('idx_matches_detection_id', 'detection_id'),
        Index('idx_matches_reference_id', 'reference_id'),
        Index('idx_matches_decision', 'decision'),
        Index('idx_matches_created_at', 'created_at'),
        UniqueConstraint('detection_id', 'reference_id', name='uq_matches_detection_reference'),
    )


class Enforcement(Base):
    """DMCA enforcement actions"""
    __tablename__ = 'enforcements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    detection_id = Column(Integer, ForeignKey('detections.id'), nullable=False)
    decision = Column(String(20), nullable=False)
    dmca_message = Column(Text, nullable=True)
    recipient = Column(String(500), nullable=True)
    sent = Column(Boolean, nullable=False, default=False)
    dry_run = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    detection = relationship("Detection", back_populates="enforcements")
    
    # Indexes
    __table_args__ = (
        Index('idx_enforcements_detection_id', 'detection_id'),
        Index('idx_enforcements_sent', 'sent'),
        Index('idx_enforcements_dry_run', 'dry_run'),
        Index('idx_enforcements_created_at', 'created_at'),
    )


class PlatformAccount(Base):
    """Platform-specific account configurations"""
    __tablename__ = 'platform_accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    account_name = Column(String(200), nullable=False)
    credentials = Column(JSONB, nullable=True)  # Encrypted credentials
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_platform_accounts_platform', 'platform'),
        Index('idx_platform_accounts_active', 'is_active'),
        UniqueConstraint('platform', 'account_name', name='uq_platform_accounts_platform_name'),
    )


# Legacy table for backward compatibility (will be migrated)
class LegacyDetection(Base):
    """Legacy detections table for migration"""
    __tablename__ = 'legacy_detections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    video_hash = Column(String(64), nullable=True)
    audio_fp = Column(String(64), nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    watermark_id = Column(String(100), nullable=True)
    evidence_key = Column(String(200), nullable=True)
    decision = Column(String(20), nullable=True)
    takedown_status = Column(String(20), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_legacy_detections_detected_at', 'detected_at'),
        Index('idx_legacy_detections_platform', 'platform'),
        Index('idx_legacy_detections_confidence', 'confidence'),
    )


class LegacyReferenceFingerprint(Base):
    """Legacy reference fingerprints table for migration"""
    __tablename__ = 'legacy_reference_fingerprints'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String(200), nullable=False)
    kind = Column(String(20), nullable=False)
    hash = Column(String(64), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_legacy_ref_fp_content_id', 'content_id'),
        Index('idx_legacy_ref_fp_kind', 'kind'),
    )
