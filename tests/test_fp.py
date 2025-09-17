"""
Tests for fingerprinting modules.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.fp.video import compute_videohash, hamming_distance, is_similar
from src.fp.audio import compute_audio_fingerprint, compare_audio_fingerprints_from_hashes


class TestVideoFingerprinting:
    """Test video fingerprinting functionality"""
    
    def test_hamming_distance(self):
        """Test Hamming distance calculation"""
        # Test identical hashes
        assert hamming_distance("abc123", "abc123") == 0
        
        # Test different hashes
        assert hamming_distance("abc123", "def456") > 0
        
        # Test hex strings - a1b2c3 vs a1b2c4 has 3 bits different
        assert hamming_distance("a1b2c3", "a1b2c4") == 3
        
        # Test single bit difference
        assert hamming_distance("a1b2c3", "a1b2c2") == 1
    
    def test_is_similar(self):
        """Test similarity check"""
        # Test identical hashes
        assert is_similar("abc123", "abc123", threshold=0) == True
        
        # Test similar hashes (1 bit difference)
        assert is_similar("abc123", "abc122", threshold=1) == True
        
        # Test different hashes
        assert is_similar("abc123", "def456", threshold=1) == False
    
    def test_compute_videohash_fallback(self):
        """Test video hash computation with fallback"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(b"fake video content")
            tmp_path = tmp.name
        
        try:
            result = compute_videohash(tmp_path)
            
            # Should return a valid result even with fallback
            assert result.phash is not None
            assert result.dhash is not None
            assert result.total_frames >= 0
            assert result.fps >= 0
            assert result.duration >= 0
            
        finally:
            os.unlink(tmp_path)


class TestAudioFingerprinting:
    """Test audio fingerprinting functionality"""
    
    def test_compare_audio_fingerprints_from_hashes(self):
        """Test audio fingerprint comparison from hashes"""
        # Test identical hashes
        assert compare_audio_fingerprints_from_hashes("abc123", "abc123") == 1.0
        
        # Test different hashes
        similarity = compare_audio_fingerprints_from_hashes("abc123", "def456")
        assert 0.0 <= similarity <= 1.0
    
    def test_compute_audio_fingerprint_fallback(self):
        """Test audio fingerprint computation with fallback"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(b"fake audio content")
            tmp_path = tmp.name
        
        try:
            result = compute_audio_fingerprint(tmp_path)
            
            # Should return a valid result even with fallback
            assert result.hash is not None
            assert isinstance(result.mfcc_features, list)
            assert isinstance(result.chroma_features, list)
            assert isinstance(result.spectral_features, dict)
            assert result.tempo >= 0
            assert result.duration >= 0
            assert result.sample_rate >= 0
            
        finally:
            os.unlink(tmp_path)


class TestFingerprintingIntegration:
    """Test fingerprinting integration"""
    
    def test_deterministic_hashes(self):
        """Test that same input produces same hash"""
        # Create temporary files with same content
        content = b"test content for fingerprinting"
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp1:
            tmp1.write(content)
            tmp1_path = tmp1.name
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp2:
            tmp2.write(content)
            tmp2_path = tmp2.name
        
        try:
            # Compute hashes for both files
            hash1 = compute_videohash(tmp1_path)
            hash2 = compute_videohash(tmp2_path)
            
            # Hashes should be identical for same content (using fallback method)
            assert hash1.phash == hash2.phash
            assert hash1.dhash == hash2.dhash
            
        finally:
            os.unlink(tmp1_path)
            os.unlink(tmp2_path)
    
    def test_different_content_different_hashes(self):
        """Test that different content produces different hashes"""
        # Create temporary files with different content
        content1 = b"test content 1"
        content2 = b"test content 2"
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp1:
            tmp1.write(content1)
            tmp1_path = tmp1.name
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp2:
            tmp2.write(content2)
            tmp2_path = tmp2.name
        
        try:
            # Compute hashes for both files
            hash1 = compute_videohash(tmp1_path)
            hash2 = compute_videohash(tmp2_path)
            
            # Hashes should be different for different content (using fallback method)
            assert hash1.phash != hash2.phash
            assert hash1.dhash != hash2.dhash
            
        finally:
            os.unlink(tmp1_path)
            os.unlink(tmp2_path)
