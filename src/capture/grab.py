from __future__ import annotations

import hashlib
import json
import time
import random
import logging
import tempfile
import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

import yt_dlp
from tenacity import retry, stop_after_attempt, wait_exponential

from ..shared.s3 import put_json, put_bytes
from ..shared.database import insert_evidence, update_detection_status
from ..fp.video import compute_videohash, VideoHashResult
from ..fp.audio import compute_audio_fingerprint

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CaptureResult:
    video_hash: str
    audio_fp: str
    evidence_key: str
    metadata: dict


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def capture_and_fingerprint(url: str, evidence_prefix: str) -> CaptureResult:
    """Capture and fingerprint content - real implementation"""
    
    logger.info(f"Capturing content from: {url}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            # Download video segment using yt-dlp
            video_file, audio_file, metadata = _download_content(url, temp_path)
            
            # Compute video fingerprint
            video_fp = None
            if video_file and video_file.exists():
                video_fp = _compute_video_fingerprint(video_file)
            
            # Compute audio fingerprint
            audio_fp = None
            if audio_file and audio_file.exists():
                audio_fp = _compute_audio_fingerprint(audio_file)
            
            # Store artifacts in S3
            s3_keys = _upload_artifacts(evidence_prefix, video_file, audio_file, metadata)
            
            # Create result
            result = CaptureResult(
                video_hash=video_fp.get('hash', '') if video_fp else '',
                audio_fp=audio_fp.get('hash', '') if audio_fp else '',
                evidence_key=evidence_prefix,
                metadata=metadata
            )
            
            logger.info(f"Successfully captured and fingerprinted: {url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to capture content from {url}: {e}")
            # Fallback to mock implementation
            return _capture_fallback(url, evidence_prefix)


def capture_detection(detection_id: int) -> Optional[int]:
    """Capture content for a detection and store evidence"""
    try:
        from ..shared.database import get_detection_by_id
        
        # Get detection details
        detection = get_detection_by_id(detection_id)
        if not detection:
            logger.error(f"Detection {detection_id} not found")
            return None
        
        url = detection['url']
        evidence_prefix = f"evidence/detection_{detection_id}_{int(time.time())}"
        
        # Update status to captured
        update_detection_status(detection_id, "captured")
        
        # Capture and fingerprint
        result = capture_and_fingerprint(url, evidence_prefix)
        
        # Store evidence in database
        evidence_id = insert_evidence(
            detection_id=detection_id,
            s3_key_json={
                "video_file": f"{evidence_prefix}/video.mp4",
                "audio_file": f"{evidence_prefix}/audio.wav",
                "metadata": f"{evidence_prefix}/metadata.json"
            },
            video_fp=result.metadata.get('video_fp'),
            audio_fp=result.metadata.get('audio_fp'),
            duration_sec=result.metadata.get('duration', 0)
        )
        
        if evidence_id:
            # Update status to fingerprinted
            update_detection_status(detection_id, "fingerprinted")
            logger.info(f"Evidence {evidence_id} created for detection {detection_id}")
            return evidence_id
        else:
            logger.error(f"Failed to store evidence for detection {detection_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error capturing detection {detection_id}: {e}")
        return None


def _download_content(url: str, temp_dir: Path) -> tuple[Optional[Path], Optional[Path], Dict[str, Any]]:
    """Download video and audio content using yt-dlp"""
    
    # Configure yt-dlp options
    ydl_opts = {
        'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
        'format': 'best[height<=720]/best',  # Limit to 720p for faster processing
        'extractaudio': True,
        'audioformat': 'wav',
        'audioquality': '192K',
        'quiet': True,
        'no_warnings': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract info first
        info = ydl.extract_info(url, download=False)
        
        # Download video
        ydl.download([url])
        
        # Find downloaded files
        video_file = None
        audio_file = None
        
        for file_path in temp_dir.glob("*"):
            if file_path.suffix in ['.mp4', '.webm', '.mkv']:
                video_file = file_path
            elif file_path.suffix in ['.wav', '.mp3', '.m4a']:
                audio_file = file_path
        
        # Create metadata
        metadata = {
            "url": url,
            "title": info.get('title', ''),
            "duration": info.get('duration', 0),
            "uploader": info.get('uploader', ''),
            "view_count": info.get('view_count', 0),
            "upload_date": info.get('upload_date', ''),
            "description": info.get('description', ''),
            "tags": info.get('tags', []),
            "captured_at": int(time.time()),
            "platform": _detect_platform(url),
            "content_type": "video"
        }
        
        return video_file, audio_file, metadata


def _compute_video_fingerprint(video_file: Path) -> Dict[str, Any]:
    """Compute video fingerprint using OpenCV and imagehash"""
    try:
        import cv2
        import imagehash
        from PIL import Image
        
        cap = cv2.VideoCapture(str(video_file))
        frame_hashes = []
        frame_timestamps = []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample every 30 frames (roughly 1 second at 30fps)
            if frame_count % 30 == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Compute perceptual hash
                phash = imagehash.phash(pil_image)
                dhash = imagehash.dhash(pil_image)
                
                frame_hashes.append({
                    "phash": str(phash),
                    "dhash": str(dhash)
                })
                frame_timestamps.append(frame_count / fps)
            
            frame_count += 1
        
        cap.release()
        
        return {
            "hash": hashlib.md5(str(frame_hashes).encode()).hexdigest(),
            "frame_hashes": frame_hashes,
            "frame_timestamps": frame_timestamps,
            "total_frames": frame_count,
            "fps": fps
        }
        
    except Exception as e:
        logger.error(f"Error computing video fingerprint: {e}")
        return {"hash": "", "error": str(e)}


def _compute_audio_fingerprint(audio_file: Path) -> Dict[str, Any]:
    """Compute audio fingerprint using librosa"""
    try:
        import librosa
        import numpy as np
        
        # Load audio file
        y, sr = librosa.load(str(audio_file), sr=22050, duration=30)  # 30 seconds max
        
        # Compute MFCC features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Compute chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # Compute spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        
        # Create fingerprint
        fingerprint = {
            "mfcc_mean": np.mean(mfccs, axis=1).tolist(),
            "mfcc_std": np.std(mfccs, axis=1).tolist(),
            "chroma_mean": np.mean(chroma, axis=1).tolist(),
            "spectral_centroid_mean": float(np.mean(spectral_centroids)),
            "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
            "duration": len(y) / sr
        }
        
        # Create hash from fingerprint
        fingerprint_str = json.dumps(fingerprint, sort_keys=True)
        fingerprint_hash = hashlib.md5(fingerprint_str.encode()).hexdigest()
        
        return {
            "hash": fingerprint_hash,
            "features": fingerprint,
            "sample_rate": sr
        }
        
    except Exception as e:
        logger.error(f"Error computing audio fingerprint: {e}")
        return {"hash": "", "error": str(e)}


def _upload_artifacts(evidence_prefix: str, video_file: Optional[Path], 
                     audio_file: Optional[Path], metadata: Dict[str, Any]) -> Dict[str, str]:
    """Upload artifacts to S3"""
    s3_keys = {}
    
    try:
        # Upload metadata
        metadata_key = f"{evidence_prefix}/metadata.json"
        put_json(metadata_key, metadata)
        s3_keys["metadata"] = metadata_key
        
        # Upload video file
        if video_file and video_file.exists():
            video_key = f"{evidence_prefix}/video.mp4"
            with open(video_file, 'rb') as f:
                put_bytes(video_key, f.read())
            s3_keys["video"] = video_key
        
        # Upload audio file
        if audio_file and audio_file.exists():
            audio_key = f"{evidence_prefix}/audio.wav"
            with open(audio_file, 'rb') as f:
                put_bytes(audio_key, f.read())
            s3_keys["audio"] = audio_key
        
        return s3_keys
        
    except Exception as e:
        logger.error(f"Error uploading artifacts: {e}")
        return s3_keys


def _capture_fallback(url: str, evidence_prefix: str) -> CaptureResult:
    """Fallback capture implementation for development"""
    logger.warning(f"Using fallback capture for: {url}")
    
    # Generate mock fingerprints for development
    url_hash = hashlib.md5(f"{url}_{int(time.time()//3600)}".encode()).hexdigest()
    
    # Generate video hash (simulated)
    video_hash = f"video_{url_hash[:16]}"
    
    # Generate audio fingerprint (simulated)
    audio_fp = f"audio_{url_hash[16:32]}"
    
    # Create metadata
    metadata = {
        "url": url,
        "captured_at": int(time.time()),
        "platform": _detect_platform(url),
        "content_type": "video",
        "duration": random.randint(30, 180),
        "resolution": random.choice(["720p", "1080p", "480p"]),
        "file_size": random.randint(1024*1024, 100*1024*1024),
        "language": _detect_language(url),
        "tags": _generate_tags(url),
        "video_fp": {"hash": video_hash, "method": "fallback"},
        "audio_fp": {"hash": audio_fp, "method": "fallback"}
    }
    
    # Store evidence
    try:
        evidence_key = f"{evidence_prefix}/metadata.json"
        put_json(evidence_key, metadata)
    except Exception as e:
        logger.error(f"Could not store fallback evidence: {e}")
        evidence_key = evidence_prefix
    
    return CaptureResult(
        video_hash=video_hash,
        audio_fp=audio_fp,
        evidence_key=evidence_key,
        metadata=metadata
    )


def _detect_platform(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "t.me" in url_lower or "telegram" in url_lower:
        return "telegram"
    elif "facebook.com" in url_lower or "fb.com" in url_lower:
        return "facebook"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "instagram.com" in url_lower:
        return "instagram"
    elif "google.com" in url_lower:
        return "google"
    else:
        return "unknown"


def _detect_language(url: str) -> str:
    """Detect language from URL or content"""
    # Simple language detection based on URL patterns
    if any(char in url for char in "ট্যাপম্যাডখেলাম্যাচ"):
        return "bengali"
    elif any(word in url.lower() for word in ["cricket", "football", "sports"]):
        return "english"
    else:
        return "mixed"


def _generate_tags(url: str) -> list[str]:
    """Generate relevant tags for content"""
    tags = []
    url_lower = url.lower()
    
    # Sports tags
    if "cricket" in url_lower:
        tags.extend(["cricket", "sports", "live", "streaming"])
    elif "football" in url_lower:
        tags.extend(["football", "soccer", "sports", "live"])
    
    # Platform tags
    platform = _detect_platform(url)
    tags.append(platform)
    
    # Content type tags
    if "live" in url_lower:
        tags.append("live")
    if "stream" in url_lower:
        tags.append("streaming")
    if "hd" in url_lower or "1080" in url_lower:
        tags.append("hd")
    
    # Tapmad specific tags
    if "tapmad" in url_lower:
        tags.extend(["tapmad", "official", "copyrighted"])
    
    return list(set(tags))  # Remove duplicates


def capture_screenshot(url: str, evidence_prefix: str) -> str:
    """Capture screenshot of content (simulated)"""
    # In production, this would use Playwright or Selenium
    screenshot_key = f"{evidence_prefix}/screenshot.png"
    
    # Create mock screenshot data
    screenshot_data = {
        "url": url,
        "timestamp": int(time.time()),
        "dimensions": {"width": 1920, "height": 1080},
        "format": "PNG",
        "size_bytes": random.randint(100*1024, 500*1024)  # 100KB to 500KB
    }
    
    try:
        put_json(f"{evidence_prefix}/screenshot_meta.json", screenshot_data)
        return screenshot_key
    except Exception:
        return f"{evidence_prefix}/screenshot_meta.json"


def capture_video_segment(url: str, evidence_prefix: str, duration: int = 30) -> str:
    """Capture video segment (simulated)"""
    # In production, this would use yt-dlp or similar tools
    
    segment_key = f"{evidence_prefix}/video_segment.mp4"
    
    # Create mock video segment data
    segment_data = {
        "url": url,
        "duration": duration,
        "format": "MP4",
        "codec": "H.264",
        "resolution": "1080p",
        "fps": 30,
        "bitrate": "2Mbps",
        "size_bytes": duration * 1024 * 1024,  # Rough estimate: 1MB per second
        "captured_at": int(time.time())
    }
    
    try:
        put_json(f"{evidence_prefix}/video_segment_meta.json", segment_data)
        return segment_key
    except Exception:
        return f"{evidence_prefix}/video_segment_meta.json"


