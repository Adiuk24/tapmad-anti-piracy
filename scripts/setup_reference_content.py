#!/usr/bin/env python3
"""
Script to set up realistic reference content for the Tapmad Anti-Piracy system.
This adds sample reference fingerprints to enable proper content matching.
"""

import psycopg2
import os
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': os.getenv('PGPORT', '5432'),
    'database': os.getenv('PGDATABASE', 'antipiracy'),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', 'postgres')
}

# Sample reference content for Tapmad
REFERENCE_CONTENT = [
    # Cricket content
    {
        'content_id': 'tapmad_cricket_world_cup_2024',
        'video_hash': 'a1b2c3d4e5f67890',
        'audio_hash': 'b2c3d4e5f678901a',
        'description': 'Cricket World Cup 2024 Live Streaming'
    },
    {
        'content_id': 'tapmad_bpl_2024',
        'video_hash': 'c3d4e5f678901a2b',
        'audio_hash': 'd4e5f678901a2b3c',
        'description': 'Bangladesh Premier League 2024'
    },
    {
        'content_id': 'tapmad_test_match_bd',
        'video_hash': 'e5f678901a2b3c4d',
        'audio_hash': 'f678901a2b3c4d5e',
        'description': 'Bangladesh Test Match Coverage'
    },
    # Football content
    {
        'content_id': 'tapmad_football_league_2024',
        'video_hash': 'g789012a3b4c5d6e7',
        'audio_hash': 'h89012a3b4c5d6e78',
        'description': 'Bangladesh Football League 2024'
    },
    {
        'content_id': 'tapmad_fifa_world_cup_2024',
        'video_hash': 'i9012a3b4c5d6e789',
        'audio_hash': 'j012a3b4c5d6e7890',
        'description': 'FIFA World Cup 2024 Coverage'
    },
    # Sports highlights
    {
        'content_id': 'tapmad_sports_highlights',
        'video_hash': 'k12a3b4c5d6e78901',
        'audio_hash': 'l2a3b4c5d6e789012',
        'description': 'Daily Sports Highlights'
    },
    # News and commentary
    {
        'content_id': 'tapmad_sports_news',
        'video_hash': 'm3a4b5c6d7e890123',
        'audio_hash': 'n4a5b6c7d8e901234',
        'description': 'Sports News and Commentary'
    }
]

def setup_reference_content():
    """Add reference content to the database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"Connected to database: {DB_CONFIG['database']}")
        
        # Clear existing reference content
        cur.execute("DELETE FROM reference_fingerprints")
        print("Cleared existing reference fingerprints")
        
        # Add new reference content
        for content in REFERENCE_CONTENT:
            # Add video fingerprint
            cur.execute("""
                INSERT INTO reference_fingerprints (content_id, kind, hash) 
                VALUES (%s, %s, %s)
            """, (content['content_id'], 'video', content['video_hash']))
            
            # Add audio fingerprint
            cur.execute("""
                INSERT INTO reference_fingerprints (content_id, kind, hash) 
                VALUES (%s, %s, %s)
            """, (content['content_id'], 'audio', content['audio_hash']))
            
            print(f"Added: {content['description']}")
        
        # Commit changes
        conn.commit()
        print(f"\nSuccessfully added {len(REFERENCE_CONTENT)} reference content items")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM reference_fingerprints")
        count = cur.fetchone()[0]
        print(f"Total reference fingerprints: {count}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    setup_reference_content()
