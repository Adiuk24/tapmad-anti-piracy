from __future__ import annotations

import sqlite3
import os
from contextlib import contextmanager
from typing import Iterator
from pathlib import Path

from .config import settings


def get_db_path() -> str:
    """Get SQLite database path"""
    db_dir = Path("local_storage")
    db_dir.mkdir(exist_ok=True)
    return str(db_dir / "antipiracy.db")


def get_conn():
    """Get SQLite database connection"""
    db_path = get_db_path()
    
    # Create database and tables if they don't exist
    if not os.path.exists(db_path):
        _create_database()
    
    return sqlite3.connect(db_path)


def _create_database():
    """Create SQLite database and tables"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    
    try:
        with conn:
            # Create detections table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    video_hash TEXT,
                    audio_fp TEXT,
                    confidence REAL NOT NULL DEFAULT 0.0,
                    watermark_id TEXT,
                    evidence_key TEXT,
                    decision TEXT CHECK (decision IN ('approve','review','reject')),
                    takedown_status TEXT CHECK (takedown_status IN ('pending','sent','failed'))
                )
            """)
            
            # Create reference_fingerprints table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reference_fingerprints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL,
                    kind TEXT NOT NULL CHECK (kind IN ('video','audio')),
                    hash TEXT NOT NULL
                )
            """)
            
            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_detections_detected_at 
                ON detections (detected_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_detections_platform 
                ON detections (platform)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_detections_confidence 
                ON detections (confidence)
            """)
            
            # Insert sample reference fingerprints
            conn.execute("""
                INSERT OR IGNORE INTO reference_fingerprints (content_id, kind, hash) 
                VALUES 
                    ('tapmad_cricket_2024', 'video', 'sample_video_hash_123'),
                    ('tapmad_football_2024', 'video', 'sample_video_hash_456'),
                    ('tapmad_cricket_2024', 'audio', 'sample_audio_hash_123'),
                    ('tapmad_football_2024', 'audio', 'sample_audio_hash_456')
            """)
            
            print("✅ SQLite database created successfully")
    
    finally:
        conn.close()


@contextmanager
def db_cursor() -> Iterator[sqlite3.Cursor]:
    """Get database cursor with automatic connection management"""
    conn = get_conn()
    try:
        with conn:
            yield conn.cursor()
    finally:
        conn.close()


def test_connection() -> bool:
    """Test database connection"""
    try:
        with db_cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            return result[0] == 1
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False


def get_database_info() -> dict:
    """Get database information"""
    try:
        with db_cursor() as cur:
            # Get table counts
            cur.execute("SELECT COUNT(*) FROM detections")
            detections_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM reference_fingerprints")
            fingerprints_count = cur.fetchone()[0]
            
            # Get recent detections
            cur.execute("""
                SELECT platform, COUNT(*) 
                FROM detections 
                GROUP BY platform 
                ORDER BY COUNT(*) DESC
            """)
            platform_stats = dict(cur.fetchall())
            
            return {
                "detections_count": detections_count,
                "fingerprints_count": fingerprints_count,
                "platform_stats": platform_stats,
                "status": "connected",
                "database_type": "SQLite",
                "database_path": get_db_path()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database_type": "SQLite"
        }


def insert_detection(platform: str, url: str, title: str = None, video_hash: str = None, 
                    audio_fp: str = None, confidence: float = 0.0) -> int:
    """Insert a new detection and return its ID"""
    try:
        with db_cursor() as cur:
            cur.execute("""
                INSERT INTO detections (platform, url, title, video_hash, audio_fp, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (platform, url, title, video_hash, audio_fp, confidence))
            
            # Get the inserted ID
            cur.execute("SELECT last_insert_rowid()")
            detection_id = cur.fetchone()[0]
            
            print(f"✅ Detection inserted with ID: {detection_id}")
            return detection_id
    
    except Exception as e:
        print(f"Error inserting detection: {e}")
        return 0


def update_detection_decision(detection_id: int, decision: str) -> bool:
    """Update detection decision"""
    try:
        with db_cursor() as cur:
            cur.execute("""
                UPDATE detections 
                SET decision = ? 
                WHERE id = ?
            """, (decision, detection_id))
            
            return cur.rowcount > 0
    
    except Exception as e:
        print(f"Error updating detection decision: {e}")
        return False


def get_detections(limit: int = 100, offset: int = 0) -> list[dict]:
    """Get detections with pagination"""
    try:
        with db_cursor() as cur:
            cur.execute("""
                SELECT id, platform, url, title, detected_at, video_hash, audio_fp, 
                       confidence, decision, takedown_status
                FROM detections 
                ORDER BY detected_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            columns = [description[0] for description in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    except Exception as e:
        print(f"Error getting detections: {e}")
        return []


def get_detection_by_id(detection_id: int) -> dict:
    """Get detection by ID"""
    try:
        with db_cursor() as cur:
            cur.execute("""
                SELECT id, platform, url, title, detected_at, video_hash, audio_fp, 
                       confidence, decision, takedown_status
                FROM detections 
                WHERE id = ?
            """, (detection_id,))
            
            row = cur.fetchone()
            if row:
                columns = [description[0] for description in cur.description]
                return dict(zip(columns, row))
            return {}
    
    except Exception as e:
        print(f"Error getting detection: {e}")
        return {}


def search_detections(query: str, platform: str = None) -> list[dict]:
    """Search detections by query"""
    try:
        with db_cursor() as cur:
            if platform:
                cur.execute("""
                    SELECT id, platform, url, title, detected_at, confidence, decision
                    FROM detections 
                    WHERE (title LIKE ? OR url LIKE ?) AND platform = ?
                    ORDER BY detected_at DESC
                """, (f"%{query}%", f"%{query}%", platform))
            else:
                cur.execute("""
                    SELECT id, platform, url, title, detected_at, confidence, decision
                    FROM detections 
                    WHERE title LIKE ? OR url LIKE ?
                    ORDER BY detected_at DESC
                """, (f"%{query}%", f"%{query}%"))
            
            columns = [description[0] for description in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    except Exception as e:
        print(f"Error searching detections: {e}")
        return []


