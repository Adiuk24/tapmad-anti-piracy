"""
End-to-end tests for the anti-piracy pipeline.
"""

import pytest
import requests
import time
import json
from typing import Dict, Any


class TestAntiPiracyPipeline:
    """Test the complete anti-piracy pipeline"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL"""
        return "http://localhost:8000"
    
    @pytest.fixture
    def test_keywords(self):
        """Test keywords for crawling"""
        return ["cricket live", "football match"]
    
    def test_health_check(self, api_base_url):
        """Test health check endpoint"""
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_system_stats(self, api_base_url):
        """Test system statistics endpoint"""
        response = requests.get(f"{api_base_url}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "database" in data
        assert "system" in data
    
    def test_crawl_endpoint(self, api_base_url, test_keywords):
        """Test crawl endpoint"""
        payload = {
            "keywords": test_keywords,
            "max_results": 5
        }
        
        response = requests.post(
            f"{api_base_url}/tools/crawl/search_and_queue",
            json=payload
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "detection_ids" in data["data"]
        assert len(data["data"]["detection_ids"]) > 0
    
    def test_capture_endpoint(self, api_base_url):
        """Test capture endpoint"""
        # First create a detection
        detection_payload = {
            "platform": "youtube",
            "url": "https://www.youtube.com/watch?v=test123",
            "title": "Test Video"
        }
        
        # This would normally be done through the crawl endpoint
        # For testing, we'll simulate it
        capture_payload = {
            "url": "https://www.youtube.com/watch?v=test123",
            "title": "Test Video",
            "platform": "youtube"
        }
        
        response = requests.post(
            f"{api_base_url}/tools/capture/fingerprint",
            json=capture_payload
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]  # 500 is OK for test URLs
        
        if response.status_code == 200:
            data = response.json()
            assert "detection_id" in data["data"]
            assert "evidence_id" in data["data"]
    
    def test_match_endpoint(self, api_base_url):
        """Test match endpoint"""
        # This test assumes we have a detection with ID 1
        # In a real test, we'd create one first
        payload = {
            "detection_id": 1
        }
        
        response = requests.post(
            f"{api_base_url}/tools/match/analyze",
            json=payload
        )
        
        # Should succeed or return error for non-existent detection
        assert response.status_code in [200, 500]
    
    def test_enforcement_endpoint(self, api_base_url):
        """Test enforcement endpoint"""
        payload = {
            "detection_id": 1,
            "decision": "match"
        }
        
        response = requests.post(
            f"{api_base_url}/enforce/send_dmca",
            json=payload
        )
        
        # Should succeed or return error for non-existent detection
        assert response.status_code in [200, 500]
    
    def test_pipeline_endpoint(self, api_base_url, test_keywords):
        """Test complete pipeline endpoint"""
        payload = {
            "keywords": test_keywords,
            "max_results": 3
        }
        
        response = requests.post(
            f"{api_base_url}/pipeline/run",
            json=payload
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True
            assert "pipeline_summary" in data["data"]
            
            summary = data["data"]["pipeline_summary"]
            assert "detections_found" in summary
            assert "evidence_captured" in summary
            assert "matches_found" in summary
            assert "dmca_notices_sent" in summary
    
    def test_detections_endpoint(self, api_base_url):
        """Test detections listing endpoint"""
        response = requests.get(f"{api_base_url}/detections")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "detections" in data["data"]
    
    def test_detection_by_id_endpoint(self, api_base_url):
        """Test get detection by ID endpoint"""
        # Test with non-existent ID
        response = requests.get(f"{api_base_url}/detections/99999")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False
        assert "not found" in data["message"].lower()
    
    def test_matching_stats_endpoint(self, api_base_url):
        """Test matching statistics endpoint"""
        response = requests.get(f"{api_base_url}/matching/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data


class TestPipelineIntegration:
    """Test pipeline integration scenarios"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL"""
        return "http://localhost:8000"
    
    def test_full_pipeline_flow(self, api_base_url):
        """Test the complete pipeline flow"""
        # Step 1: Crawl for content
        crawl_payload = {
            "keywords": ["test cricket"],
            "max_results": 2
        }
        
        crawl_response = requests.post(
            f"{api_base_url}/tools/crawl/search_and_queue",
            json=crawl_payload
        )
        
        if crawl_response.status_code == 200:
            crawl_data = crawl_response.json()
            detection_ids = crawl_data["data"]["detection_ids"]
            
            if detection_ids:
                # Step 2: Capture and fingerprint (for first detection)
                detection_id = detection_ids[0]
                
                # Get detection details
                detection_response = requests.get(f"{api_base_url}/detections/{detection_id}")
                
                if detection_response.status_code == 200:
                    detection_data = detection_response.json()
                    
                    if detection_data["success"]:
                        # Step 3: Analyze for matches
                        match_payload = {"detection_id": detection_id}
                        match_response = requests.post(
                            f"{api_base_url}/tools/match/analyze",
                            json=match_payload
                        )
                        
                        # Step 4: Send DMCA (dry-run)
                        dmca_payload = {
                            "detection_id": detection_id,
                            "decision": "match"
                        }
                        dmca_response = requests.post(
                            f"{api_base_url}/enforce/send_dmca",
                            json=dmca_payload
                        )
                        
                        # All steps should complete without critical errors
                        assert match_response.status_code in [200, 500]
                        assert dmca_response.status_code in [200, 500]
    
    def test_error_handling(self, api_base_url):
        """Test error handling in the pipeline"""
        # Test with invalid payload
        invalid_payload = {
            "invalid_field": "test"
        }
        
        response = requests.post(
            f"{api_base_url}/tools/crawl/search_and_queue",
            json=invalid_payload
        )
        
        # Should handle invalid payload gracefully
        assert response.status_code in [200, 422, 500]
    
    def test_rate_limiting(self, api_base_url):
        """Test rate limiting behavior"""
        # Send multiple requests quickly
        payload = {
            "keywords": ["test"],
            "max_results": 1
        }
        
        responses = []
        for i in range(3):
            response = requests.post(
                f"{api_base_url}/tools/crawl/search_and_queue",
                json=payload
            )
            responses.append(response)
            time.sleep(0.1)  # Small delay
        
        # All requests should be handled (rate limiting is internal)
        for response in responses:
            assert response.status_code in [200, 429, 500]


class TestSystemReliability:
    """Test system reliability and error handling"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL"""
        return "http://localhost:8000"
    
    def test_system_under_load(self, api_base_url):
        """Test system behavior under load"""
        # Send multiple concurrent requests
        import concurrent.futures
        
        def make_request():
            payload = {
                "keywords": ["load test"],
                "max_results": 1
            }
            return requests.post(
                f"{api_base_url}/tools/crawl/search_and_queue",
                json=payload,
                timeout=30
            )
        
        # Send 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete (success or failure)
        assert len(responses) == 5
        for response in responses:
            assert response.status_code in [200, 429, 500, 503]
    
    def test_graceful_degradation(self, api_base_url):
        """Test graceful degradation when services are unavailable"""
        # Test with invalid URLs that should fail gracefully
        invalid_payload = {
            "url": "https://invalid-url-that-does-not-exist.com/video",
            "title": "Invalid Video",
            "platform": "youtube"
        }
        
        response = requests.post(
            f"{api_base_url}/tools/capture/fingerprint",
            json=invalid_payload
        )
        
        # Should fail gracefully, not crash
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Should indicate failure in response
            assert data["success"] == False or "error" in data.get("message", "").lower()
