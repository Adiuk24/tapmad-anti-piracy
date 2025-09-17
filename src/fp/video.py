"""
Video fingerprinting module using perceptual hashing and difference hashing.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    import cv2
    import imagehash
    from PIL import Image
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV, imagehash, or PIL not available. Video fingerprinting will use fallback methods.")

logger = logging.getLogger(__name__)


@dataclass
class VideoHashResult:
    """Result of video fingerprinting"""
    phash: str
    dhash: str
    frame_hashes: List[Dict[str, Any]]
    total_frames: int
    fps: float
    duration: float


def compute_videohash(video_path: str) -> VideoHashResult:
    """Compute video fingerprint using perceptual and difference hashing"""
    
    if not OPENCV_AVAILABLE:
        return _compute_fallback_videohash(video_path)
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        frame_hashes = []
        frame_count = 0
        
        # Sample frames for hashing (every 30 frames or 1 second)
        sample_interval = max(1, int(fps)) if fps > 0 else 30
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frames
            if frame_count % sample_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Compute hashes
                phash = imagehash.phash(pil_image)
                dhash = imagehash.dhash(pil_image)
                
                frame_hashes.append({
                    "frame_number": frame_count,
                    "timestamp": frame_count / fps if fps > 0 else 0,
                    "phash": str(phash),
                    "dhash": str(dhash),
                    "phash_int": int(str(phash), 16),
                    "dhash_int": int(str(dhash), 16)
                })
            
            frame_count += 1
        
        cap.release()
        
        # Compute overall video hash from frame hashes
        phash_str = "".join([fh["phash"] for fh in frame_hashes])
        dhash_str = "".join([fh["dhash"] for fh in frame_hashes])
        
        video_phash = hashlib.md5(phash_str.encode()).hexdigest()
        video_dhash = hashlib.md5(dhash_str.encode()).hexdigest()
        
        return VideoHashResult(
            phash=video_phash,
            dhash=video_dhash,
            frame_hashes=frame_hashes,
            total_frames=total_frames,
            fps=fps,
            duration=duration
        )
        
    except Exception as e:
        logger.error(f"Error computing video hash: {e}")
        return _compute_fallback_videohash(video_path)


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate Hamming distance between two hashes"""
    if not hash1 or not hash2:
        return max(len(hash1 or ""), len(hash2 or ""))
    
    # If they're different lengths, return the max length
    if len(hash1) != len(hash2):
        return max(len(hash1), len(hash2))
    
    # For hex strings, convert to binary and calculate Hamming distance
    try:
        # Convert hex strings to integers
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        
        # Calculate Hamming distance
        return bin(int1 ^ int2).count('1')
    except ValueError:
        # If not hex, treat as character strings
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))


def is_similar(hash1: str, hash2: str, threshold: int = 8) -> bool:
    """Check if two hashes are similar within threshold"""
    distance = hamming_distance(hash1, hash2)
    return distance <= threshold


def compare_video_hashes(hash1: VideoHashResult, hash2: VideoHashResult, 
                        threshold: int = 8) -> Dict[str, Any]:
    """Compare two video hash results"""
    
    # Compare overall hashes
    phash_distance = hamming_distance(hash1.phash, hash2.phash)
    dhash_distance = hamming_distance(hash1.dhash, hash2.dhash)
    
    # Compare frame-by-frame hashes
    frame_matches = 0
    frame_distances = []
    
    for fh1 in hash1.frame_hashes:
        best_distance = float('inf')
        for fh2 in hash2.frame_hashes:
            distance = hamming_distance(fh1["phash"], fh2["phash"])
            best_distance = min(best_distance, distance)
        
        frame_distances.append(best_distance)
        if best_distance <= threshold:
            frame_matches += 1
    
    # Calculate similarity scores
    phash_similarity = 1.0 - (phash_distance / 64.0)  # Normalize to 0-1
    dhash_similarity = 1.0 - (dhash_distance / 64.0)
    frame_similarity = frame_matches / len(hash1.frame_hashes) if hash1.frame_hashes else 0
    
    # Overall similarity (weighted average)
    overall_similarity = (phash_similarity * 0.4 + dhash_similarity * 0.4 + frame_similarity * 0.2)
    
    return {
        "phash_distance": phash_distance,
        "dhash_distance": dhash_distance,
        "phash_similarity": phash_similarity,
        "dhash_similarity": dhash_similarity,
        "frame_similarity": frame_similarity,
        "frame_matches": frame_matches,
        "total_frames": len(hash1.frame_hashes),
        "overall_similarity": overall_similarity,
        "is_similar": overall_similarity > 0.7  # 70% similarity threshold
    }


def _compute_fallback_videohash(video_path: str) -> VideoHashResult:
    """Fallback video hashing when OpenCV is not available"""
    logger.warning(f"Using fallback video hashing for: {video_path}")
    
    # Generate deterministic hash based on file content only
    try:
        import os
        with open(video_path, 'rb') as f:
            file_content = f.read()
        
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Generate mock frame hashes
        frame_hashes = []
        phash_parts = []
        dhash_parts = []
        
        for i in range(10):  # Mock 10 frames
            frame_hash = hashlib.md5(f"{file_hash}_{i}".encode()).hexdigest()
            phash_part = frame_hash[:16]
            dhash_part = frame_hash[16:32]
            
            phash_parts.append(phash_part)
            dhash_parts.append(dhash_part)
            
            frame_hashes.append({
                "frame_number": i * 30,
                "timestamp": i,
                "phash": phash_part,
                "dhash": dhash_part,
                "phash_int": int(phash_part, 16),
                "dhash_int": int(dhash_part, 16)
            })
        
        # Create overall video hashes
        video_phash = hashlib.md5("".join(phash_parts).encode()).hexdigest()
        video_dhash = hashlib.md5("".join(dhash_parts).encode()).hexdigest()
        
        return VideoHashResult(
            phash=video_phash,
            dhash=video_dhash,
            frame_hashes=frame_hashes,
            total_frames=300,  # Mock 300 frames
            fps=30.0,
            duration=10.0
        )
        
    except Exception as e:
        logger.error(f"Fallback video hashing failed: {e}")
        return VideoHashResult(
            phash="",
            dhash="",
            frame_hashes=[],
            total_frames=0,
            fps=0.0,
            duration=0.0
        )


def extract_key_frames(video_path: str, max_frames: int = 10) -> List[Dict[str, Any]]:
    """Extract key frames from video for analysis"""
    
    if not OPENCV_AVAILABLE:
        return []
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate frame intervals
        if total_frames <= max_frames:
            frame_indices = list(range(total_frames))
        else:
            frame_indices = [int(i * total_frames / max_frames) for i in range(max_frames)]
        
        key_frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count in frame_indices:
                # Convert to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Compute hash
                phash = imagehash.phash(pil_image)
                
                key_frames.append({
                    "frame_number": frame_count,
                    "timestamp": frame_count / fps if fps > 0 else 0,
                    "phash": str(phash),
                    "width": frame.shape[1],
                    "height": frame.shape[0]
                })
            
            frame_count += 1
        
        cap.release()
        return key_frames
        
    except Exception as e:
        logger.error(f"Error extracting key frames: {e}")
        return []


def detect_scene_changes(video_path: str, threshold: float = 0.3) -> List[Dict[str, Any]]:
    """Detect scene changes in video"""
    
    if not OPENCV_AVAILABLE:
        return []
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        scene_changes = []
        prev_frame = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, gray)
                diff_score = np.mean(diff) / 255.0
                
                if diff_score > threshold:
                    scene_changes.append({
                        "frame_number": frame_count,
                        "timestamp": frame_count / fps if fps > 0 else 0,
                        "diff_score": diff_score
                    })
            
            prev_frame = gray
            frame_count += 1
        
        cap.release()
        return scene_changes
        
    except Exception as e:
        logger.error(f"Error detecting scene changes: {e}")
        return []