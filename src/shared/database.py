from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from .config import settings
from ..db.models import Base, Detection, Evidence, Match, Reference, Enforcement, PlatformAccount

logger = logging.getLogger(__name__)

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,  # Use NullPool for development
    echo=settings.env == "development",
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise


def drop_tables():
    """Drop all tables"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Database tables dropped successfully")
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except SQLAlchemyError as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def get_database_info() -> Dict[str, Any]:
    """Get database information"""
    try:
        with get_db_session() as session:
            # Get table counts
            detections_count = session.query(Detection).count()
            evidence_count = session.query(Evidence).count()
            matches_count = session.query(Match).count()
            references_count = session.query(Reference).count()
            enforcements_count = session.query(Enforcement).count()
            
            # Get detections by status
            status_stats = {}
            for status in ['found', 'captured', 'fingerprinted', 'matched', 'enforced', 'error']:
                count = session.query(Detection).filter(Detection.decision == status).count()
                if count > 0:
                    status_stats[status] = count
            
            # Get platform stats
            platform_stats = {}
            platforms = session.query(Detection.platform).distinct().all()
            for (platform,) in platforms:
                count = session.query(Detection).filter(Detection.platform == platform).count()
                platform_stats[platform] = count
            
            return {
                "detections_count": detections_count,
                "evidence_count": evidence_count,
                "matches_count": matches_count,
                "references_count": references_count,
                "enforcements_count": enforcements_count,
                "status_stats": status_stats,
                "platform_stats": platform_stats,
                "status": "connected",
                "database_type": "PostgreSQL",
                "database_url": settings.database_url.split('@')[1] if '@' in settings.database_url else "hidden"
            }
    except SQLAlchemyError as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "status": "error",
            "error": str(e),
            "database_type": "PostgreSQL"
        }


# Database operations for detections
def insert_detection(
    platform: str, 
    url: str, 
    title: Optional[str] = None,
    decision: str = "review"
) -> Optional[int]:
    """Insert a new detection and return its ID"""
    try:
        with get_db_session() as session:
            detection = Detection(
                platform=platform,
                url=url,
                title=title,
                decision=decision
            )
            session.add(detection)
            session.flush()  # Get the ID without committing
            
            detection_id = detection.id
            logger.info(f"✅ Detection inserted with ID: {detection_id}")
            return detection_id
    except SQLAlchemyError as e:
        logger.error(f"Error inserting detection: {e}")
        return None


def update_detection_status(detection_id: int, status: str) -> bool:
    """Update detection status"""
    try:
        with get_db_session() as session:
            detection = session.query(Detection).filter(Detection.id == detection_id).first()
            if detection:
                detection.decision = status
                return True
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error updating detection status: {e}")
        return False


def get_detections(limit: int = 100, offset: int = 0, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get detections with pagination"""
    try:
        with get_db_session() as session:
            query = session.query(Detection)
            if status:
                query = query.filter(Detection.decision == status)
            
            detections = query.order_by(Detection.detected_at.desc()).offset(offset).limit(limit).all()
            
            return [
                {
                    "id": d.id,
                    "platform": d.platform,
                    "url": d.url,
                    "title": d.title,
                    "status": d.decision,
                    "created_at": d.detected_at.isoformat() if d.detected_at else None,
                    "detected_at": d.detected_at.isoformat() if d.detected_at else None,
                }
                for d in detections
            ]
    except SQLAlchemyError as e:
        logger.error(f"Error getting detections: {e}")
        return []


def get_detection_by_id(detection_id: int) -> Optional[Dict[str, Any]]:
    """Get detection by ID"""
    try:
        with get_db_session() as session:
            detection = session.query(Detection).filter(Detection.id == detection_id).first()
            if detection:
                return {
                    "id": detection.id,
                    "platform": detection.platform,
                    "url": detection.url,
                    "title": detection.title,
                    "status": detection.decision,
                    "created_at": detection.detected_at.isoformat() if detection.detected_at else None,
                    "detected_at": detection.detected_at.isoformat() if detection.detected_at else None,
                }
            return None
    except SQLAlchemyError as e:
        logger.error(f"Error getting detection: {e}")
        return None


def search_detections(query: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search detections by query"""
    try:
        with get_db_session() as session:
            db_query = session.query(Detection).filter(
                Detection.title.ilike(f"%{query}%") | Detection.url.ilike(f"%{query}%")
            )
            if platform:
                db_query = db_query.filter(Detection.platform == platform)
            
            detections = db_query.order_by(Detection.created_at.desc()).limit(100).all()
            
            return [
                {
                    "id": d.id,
                    "platform": d.platform,
                    "url": d.url,
                    "title": d.title,
                    "status": d.decision,
                    "created_at": d.detected_at.isoformat() if d.detected_at else None,
                }
                for d in detections
            ]
    except SQLAlchemyError as e:
        logger.error(f"Error searching detections: {e}")
        return []


# Evidence operations
def insert_evidence(
    detection_id: int,
    s3_key_json: Optional[Dict[str, Any]] = None,
    video_fp: Optional[Dict[str, Any]] = None,
    audio_fp: Optional[Dict[str, Any]] = None,
    duration_sec: Optional[float] = None
) -> Optional[int]:
    """Insert evidence record"""
    try:
        with get_db_session() as session:
            evidence = Evidence(
                detection_id=detection_id,
                s3_key_json=s3_key_json,
                video_fp=video_fp,
                audio_fp=audio_fp,
                duration_sec=duration_sec
            )
            session.add(evidence)
            session.flush()
            
            evidence_id = evidence.id
            logger.info(f"✅ Evidence inserted with ID: {evidence_id}")
            return evidence_id
    except SQLAlchemyError as e:
        logger.error(f"Error inserting evidence: {e}")
        return None


# Match operations
def insert_match(
    detection_id: int,
    reference_id: int,
    video_score: float,
    audio_score: float,
    decision: str,
    threshold_video: float = 0.18,
    threshold_audio: float = 0.72
) -> Optional[int]:
    """Insert match record"""
    try:
        with get_db_session() as session:
            match = Match(
                detection_id=detection_id,
                reference_id=reference_id,
                video_score=video_score,
                audio_score=audio_score,
                decision=decision,
                threshold_video=threshold_video,
                threshold_audio=threshold_audio
            )
            session.add(match)
            session.flush()
            
            match_id = match.id
            logger.info(f"✅ Match inserted with ID: {match_id}")
            return match_id
    except SQLAlchemyError as e:
        logger.error(f"Error inserting match: {e}")
        return None


# Enforcement operations
def insert_enforcement(
    detection_id: int,
    decision: str,
    dmca_message: Optional[str] = None,
    recipient: Optional[str] = None,
    dry_run: bool = True
) -> Optional[int]:
    """Insert enforcement record"""
    try:
        with get_db_session() as session:
            enforcement = Enforcement(
                detection_id=detection_id,
                decision=decision,
                dmca_message=dmca_message,
                recipient=recipient,
                dry_run=dry_run
            )
            session.add(enforcement)
            session.flush()
            
            enforcement_id = enforcement.id
            logger.info(f"✅ Enforcement inserted with ID: {enforcement_id}")
            return enforcement_id
    except SQLAlchemyError as e:
        logger.error(f"Error inserting enforcement: {e}")
        return None


# Reference operations
def insert_reference(
    title: str,
    platform: str,
    content_type: str = "video",
    ref_hash_video: Optional[Dict[str, Any]] = None,
    ref_hash_audio: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """Insert reference record"""
    try:
        with get_db_session() as session:
            reference = Reference(
                title=title,
                platform=platform,
                content_type=content_type,
                ref_hash_video=ref_hash_video,
                ref_hash_audio=ref_hash_audio
            )
            session.add(reference)
            session.flush()
            
            reference_id = reference.id
            logger.info(f"✅ Reference inserted with ID: {reference_id}")
            return reference_id
    except SQLAlchemyError as e:
        logger.error(f"Error inserting reference: {e}")
        return None


def get_references(platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get reference records"""
    try:
        with get_db_session() as session:
            query = session.query(Reference)
            if platform:
                query = query.filter(Reference.platform == platform)
            
            references = query.all()
            
            return [
                {
                    "id": r.id,
                    "title": r.title,
                    "platform": r.platform,
                    "content_type": r.content_type,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in references
            ]
    except SQLAlchemyError as e:
        logger.error(f"Error getting references: {e}")
        return []
