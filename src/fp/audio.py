"""
Audio fingerprinting module using MFCC, chroma features, and spectral analysis.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

try:
    import librosa
    import numpy as np
    import scipy.stats
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logging.warning("librosa or scipy not available. Audio fingerprinting will use fallback methods.")

logger = logging.getLogger(__name__)


@dataclass
class AudioFingerprint:
    """Audio fingerprint result"""
    hash: str
    mfcc_features: List[float]
    chroma_features: List[float]
    spectral_features: Dict[str, float]
    tempo: float
    duration: float
    sample_rate: int


def compute_audio_fingerprint(audio_path: str) -> AudioFingerprint:
    """Compute audio fingerprint using librosa features"""
    
    if not LIBROSA_AVAILABLE:
        return _compute_fallback_audio_fingerprint(audio_path)
    
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=22050, duration=30)  # 30 seconds max
        
        # Compute MFCC features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfccs, axis=1).tolist()
        mfcc_std = np.std(mfccs, axis=1).tolist()
        
        # Compute chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1).tolist()
        
        # Compute spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
        
        # Compute tempo
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Create feature vector
        features = {
            "mfcc_mean": mfcc_mean,
            "mfcc_std": mfcc_std,
            "chroma_mean": chroma_mean,
            "spectral_centroid_mean": float(np.mean(spectral_centroids)),
            "spectral_centroid_std": float(np.std(spectral_centroids)),
            "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
            "spectral_rolloff_std": float(np.std(spectral_rolloff)),
            "spectral_bandwidth_mean": float(np.mean(spectral_bandwidth)),
            "spectral_bandwidth_std": float(np.std(spectral_bandwidth)),
            "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
            "zero_crossing_rate_std": float(np.std(zero_crossing_rate)),
            "tempo": float(tempo),
            "duration": len(y) / sr,
            "sample_rate": sr
        }
        
        # Create hash from features
        fingerprint_str = json.dumps(features, sort_keys=True)
        fingerprint_hash = hashlib.md5(fingerprint_str.encode()).hexdigest()
        
        return AudioFingerprint(
            hash=fingerprint_hash,
            mfcc_features=mfcc_mean,
            chroma_features=chroma_mean,
            spectral_features={
                "centroid": features["spectral_centroid_mean"],
                "rolloff": features["spectral_rolloff_mean"],
                "bandwidth": features["spectral_bandwidth_mean"],
                "zcr": features["zero_crossing_rate_mean"]
            },
            tempo=tempo,
            duration=duration,
            sample_rate=sr
        )
        
    except Exception as e:
        logger.error(f"Error computing audio fingerprint: {e}")
        return _compute_fallback_audio_fingerprint(audio_path)


def compare_audio_fingerprints(fp1: AudioFingerprint, fp2: AudioFingerprint) -> Dict[str, Any]:
    """Compare two audio fingerprints"""
    
    try:
        # Convert features to numpy arrays
        mfcc1 = np.array(fp1.mfcc_features)
        mfcc2 = np.array(fp2.mfcc_features)
        chroma1 = np.array(fp1.chroma_features)
        chroma2 = np.array(fp2.chroma_features)
        
        # Calculate cosine similarity for MFCC
        mfcc_similarity = _cosine_similarity(mfcc1, mfcc2)
        
        # Calculate cosine similarity for chroma
        chroma_similarity = _cosine_similarity(chroma1, chroma2)
        
        # Calculate spectral feature similarity
        spectral_similarity = _compare_spectral_features(fp1.spectral_features, fp2.spectral_features)
        
        # Calculate tempo similarity
        tempo_similarity = _compare_tempo(fp1.tempo, fp2.tempo)
        
        # Overall similarity (weighted average)
        overall_similarity = (
            mfcc_similarity * 0.4 +
            chroma_similarity * 0.3 +
            spectral_similarity * 0.2 +
            tempo_similarity * 0.1
        )
        
        return {
            "mfcc_similarity": mfcc_similarity,
            "chroma_similarity": chroma_similarity,
            "spectral_similarity": spectral_similarity,
            "tempo_similarity": tempo_similarity,
            "overall_similarity": overall_similarity,
            "is_similar": overall_similarity > 0.7  # 70% similarity threshold
        }
        
    except Exception as e:
        logger.error(f"Error comparing audio fingerprints: {e}")
        return {
            "mfcc_similarity": 0.0,
            "chroma_similarity": 0.0,
            "spectral_similarity": 0.0,
            "tempo_similarity": 0.0,
            "overall_similarity": 0.0,
            "is_similar": False
        }


def compare_audio_fingerprints_from_hashes(hash1: str, hash2: str) -> float:
    """Compare audio fingerprints from hash strings (fallback method)"""
    try:
        if hash1 == hash2:
            return 1.0
        
        # Simple hash-based similarity (not very accurate)
        if len(hash1) != len(hash2):
            return 0.0
        
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        similarity = matches / len(hash1)
        
        return similarity
        
    except Exception:
        return 0.0


def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    try:
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
        
    except Exception:
        return 0.0


def _compare_spectral_features(features1: Dict[str, float], features2: Dict[str, float]) -> float:
    """Compare spectral features"""
    try:
        similarities = []
        
        for key in features1:
            if key in features2:
                val1 = features1[key]
                val2 = features2[key]
                
                # Normalize values and calculate similarity
                if val1 == 0 and val2 == 0:
                    similarity = 1.0
                elif val1 == 0 or val2 == 0:
                    similarity = 0.0
                else:
                    # Use relative difference
                    diff = abs(val1 - val2) / max(val1, val2)
                    similarity = max(0.0, 1.0 - diff)
                
                similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
        
    except Exception:
        return 0.0


def _compare_tempo(tempo1: float, tempo2: float) -> float:
    """Compare tempo values"""
    try:
        if tempo1 == 0 and tempo2 == 0:
            return 1.0
        elif tempo1 == 0 or tempo2 == 0:
            return 0.0
        
        # Tempo similarity based on relative difference
        diff = abs(tempo1 - tempo2) / max(tempo1, tempo2)
        return max(0.0, 1.0 - diff)
        
    except Exception:
        return 0.0


def _compute_fallback_audio_fingerprint(audio_path: str) -> AudioFingerprint:
    """Fallback audio fingerprinting when librosa is not available"""
    logger.warning(f"Using fallback audio fingerprinting for: {audio_path}")
    
    try:
        import os
        file_size = os.path.getsize(audio_path)
        file_hash = hashlib.md5(f"{audio_path}_{file_size}".encode()).hexdigest()
        
        # Generate mock features
        mfcc_features = [float(int(file_hash[i:i+2], 16)) / 255.0 for i in range(0, 26, 2)]
        chroma_features = [float(int(file_hash[i:i+2], 16)) / 255.0 for i in range(26, 38, 2)]
        
        return AudioFingerprint(
            hash=file_hash,
            mfcc_features=mfcc_features,
            chroma_features=chroma_features,
            spectral_features={
                "centroid": float(int(file_hash[38:42], 16)),
                "rolloff": float(int(file_hash[42:46], 16)),
                "bandwidth": float(int(file_hash[46:50], 16)),
                "zcr": float(int(file_hash[50:54], 16)) / 1000.0
            },
            tempo=float(int(file_hash[54:58], 16)),
            duration=10.0,  # Mock duration
            sample_rate=22050
        )
        
    except Exception as e:
        logger.error(f"Fallback audio fingerprinting failed: {e}")
        return AudioFingerprint(
            hash="",
            mfcc_features=[],
            chroma_features=[],
            spectral_features={},
            tempo=0.0,
            duration=0.0,
            sample_rate=0
        )


def extract_audio_features(audio_path: str) -> Dict[str, Any]:
    """Extract comprehensive audio features"""
    
    if not LIBROSA_AVAILABLE:
        return _extract_fallback_audio_features(audio_path)
    
    try:
        y, sr = librosa.load(audio_path, sr=22050, duration=30)
        
        # Basic features
        features = {
            "duration": len(y) / sr,
            "sample_rate": sr,
            "rms_energy": float(np.mean(librosa.feature.rms(y=y))),
            "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(y))),
        }
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        features.update({
            "spectral_centroid_mean": float(np.mean(spectral_centroids)),
            "spectral_centroid_std": float(np.std(spectral_centroids)),
        })
        
        # MFCC features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features.update({
            "mfcc_mean": np.mean(mfccs, axis=1).tolist(),
            "mfcc_std": np.std(mfccs, axis=1).tolist(),
        })
        
        # Chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features.update({
            "chroma_mean": np.mean(chroma, axis=1).tolist(),
            "chroma_std": np.std(chroma, axis=1).tolist(),
        })
        
        # Tempo and rhythm
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        features.update({
            "tempo": float(tempo),
            "beat_count": len(beats),
        })
        
        return features
        
    except Exception as e:
        logger.error(f"Error extracting audio features: {e}")
        return _extract_fallback_audio_features(audio_path)


def _extract_fallback_audio_features(audio_path: str) -> Dict[str, Any]:
    """Fallback audio feature extraction"""
    try:
        import os
        file_size = os.path.getsize(audio_path)
        file_hash = hashlib.md5(f"{audio_path}_{file_size}".encode()).hexdigest()
        
        return {
            "duration": 10.0,
            "sample_rate": 22050,
            "rms_energy": float(int(file_hash[:4], 16)) / 1000.0,
            "zero_crossing_rate": float(int(file_hash[4:8], 16)) / 1000.0,
            "spectral_centroid_mean": float(int(file_hash[8:12], 16)),
            "spectral_centroid_std": float(int(file_hash[12:16], 16)),
            "mfcc_mean": [float(int(file_hash[i:i+2], 16)) / 255.0 for i in range(16, 42, 2)],
            "mfcc_std": [float(int(file_hash[i:i+2], 16)) / 255.0 for i in range(42, 68, 2)],
            "chroma_mean": [float(int(file_hash[i:i+2], 16)) / 255.0 for i in range(68, 92, 2)],
            "chroma_std": [float(int(file_hash[i:i+2], 16)) / 255.0 for i in range(92, 116, 2)],
            "tempo": float(int(file_hash[116:120], 16)),
            "beat_count": int(file_hash[120:124], 16),
        }
        
    except Exception as e:
        logger.error(f"Fallback audio feature extraction failed: {e}")
        return {}