from __future__ import annotations

import time
import logging
from typing import Any, Iterator, Optional, List, Dict
from dataclasses import dataclass

from ..shared.database import get_db_session, get_references, insert_match, update_detection_status
from ..shared.config import settings
from ..fp.video import hamming_distance, is_similar, compare_video_hashes
from ..fp.audio import compare_audio_fingerprints, compare_audio_fingerprints_from_hashes

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MatchResult:
    detection_id: int
    reference_id: str
    video_similarity: float
    audio_similarity: float
    overall_confidence: float
    match_type: str
    evidence: dict


class MatchingEngine:
    def __init__(self):
        self.video_threshold = settings.video_threshold
        self.audio_threshold = settings.audio_threshold
        self.llm_threshold = settings.llm_min_score

    def find_matches(self, detection_id: int, video_hash: str, audio_fp: str) -> List[MatchResult]:
        """Find matches for given fingerprints"""
        
        matches = []
        logger.info(f"Finding matches for detection {detection_id}")
        
        try:
            # Get reference fingerprints
            references = get_references()
            
            for reference in references:
                ref_id = reference['id']
                ref_video_fp = reference.get('ref_hash_video', {})
                ref_audio_fp = reference.get('ref_hash_audio', {})
                
                video_similarity = 0.0
                audio_similarity = 0.0
                
                # Compare video fingerprints
                if video_hash and ref_video_fp:
                    video_similarity = self._compare_video_fingerprints(video_hash, ref_video_fp)
                
                # Compare audio fingerprints
                if audio_fp and ref_audio_fp:
                    audio_similarity = self._compare_audio_fingerprints(audio_fp, ref_audio_fp)
                
                # Calculate overall confidence
                if video_similarity > 0 and audio_similarity > 0:
                    overall_confidence = (video_similarity + audio_similarity) / 2
                else:
                    overall_confidence = max(video_similarity, audio_similarity)
                
                # Determine match decision
                if overall_confidence >= 0.8:
                    decision = "match"
                elif overall_confidence >= 0.6:
                    decision = "likely"
                else:
                    decision = "none"
                
                # Only store matches above threshold
                if overall_confidence >= self.llm_threshold:
                    # Store match in database
                    match_id = insert_match(
                        detection_id=detection_id,
                        reference_id=ref_id,
                        video_score=video_similarity,
                        audio_score=audio_similarity,
                        decision=decision,
                        threshold_video=self.video_threshold,
                        threshold_audio=self.audio_threshold
                    )
                    
                    if match_id:
                        evidence = {
                            "video_similarity": video_similarity,
                            "audio_similarity": audio_similarity,
                            "reference_id": ref_id,
                            "match_timestamp": int(time.time()),
                            "thresholds": {
                                "video": self.video_threshold,
                                "audio": self.audio_threshold
                            }
                        }
                        
                        matches.append(MatchResult(
                            detection_id=detection_id,
                            reference_id=str(ref_id),
                            video_similarity=video_similarity,
                            audio_similarity=audio_similarity,
                            overall_confidence=overall_confidence,
                            match_type=decision,
                            evidence=evidence
                        ))
                        
                        logger.info(f"Match found: detection {detection_id} -> reference {ref_id} (confidence: {overall_confidence:.3f})")
        
        except Exception as e:
            logger.error(f"Error finding matches for detection {detection_id}: {e}")
        
        return matches

    def _compare_video_fingerprints(self, detection_fp: str, reference_fp: Dict[str, Any]) -> float:
        """Compare video fingerprints"""
        try:
            if isinstance(reference_fp, dict) and 'hash' in reference_fp:
                ref_hash = reference_fp['hash']
            else:
                ref_hash = str(reference_fp)
            
            # Calculate Hamming distance
            distance = hamming_distance(detection_fp, ref_hash)
            
            # Normalize to similarity score (0-1)
            max_distance = len(detection_fp) * 4  # Assuming 64-bit hashes
            similarity = max(0.0, 1.0 - (distance / max_distance))
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error comparing video fingerprints: {e}")
            return 0.0

    def _compare_audio_fingerprints(self, detection_fp: str, reference_fp: Dict[str, Any]) -> float:
        """Compare audio fingerprints"""
        try:
            if isinstance(reference_fp, dict) and 'hash' in reference_fp:
                ref_hash = reference_fp['hash']
            else:
                ref_hash = str(reference_fp)
            
            # Use hash-based comparison for now
            similarity = compare_audio_fingerprints_from_hashes(detection_fp, ref_hash)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error comparing audio fingerprints: {e}")
            return 0.0

    def analyze_detection(self, detection_id: int) -> dict[str, Any]:
        """Analyze a detection and find matches"""
        
        try:
            from ..shared.database import get_detection_by_id
            
            # Get detection details
            detection = get_detection_by_id(detection_id)
            if not detection:
                return {"error": "Detection not found"}
            
            # Get evidence for this detection
            evidence = self._get_evidence_for_detection(detection_id)
            if not evidence:
                return {"error": "No evidence found for detection"}
            
            video_hash = evidence.get('video_fp', {}).get('hash', '') if evidence.get('video_fp') else ''
            audio_fp = evidence.get('audio_fp', {}).get('hash', '') if evidence.get('audio_fp') else ''
            
            # Find matches
            matches = self.find_matches(detection_id, video_hash, audio_fp)
            
            # Update detection status to matched
            if matches:
                update_detection_status(detection_id, "matched")
            
            # Analyze content
            content_analysis = self._analyze_content(detection['url'], detection['title'], detection['platform'])
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(matches, content_analysis)
            
            # Determine decision
            decision = self._determine_decision(risk_score, matches)
            
            return {
                "detection_id": detection_id,
                "matches": [
                    {
                        "reference_id": m.reference_id,
                        "confidence": m.overall_confidence,
                        "match_type": m.match_type,
                        "evidence": m.evidence
                    }
                    for m in matches
                ],
                "content_analysis": content_analysis,
                "risk_score": risk_score,
                "decision": decision,
                "recommendation": self._get_recommendation(decision, risk_score),
                "timestamp": int(time.time())
            }
        
        except Exception as e:
            logger.error(f"Analysis failed for detection {detection_id}: {e}")
            return {"error": f"Analysis failed: {e}"}

    def _get_evidence_for_detection(self, detection_id: int) -> Optional[Dict[str, Any]]:
        """Get evidence for a detection"""
        try:
            with get_db_session() as session:
                from ..db.models import Evidence
                
                evidence = session.query(Evidence).filter(Evidence.detection_id == detection_id).first()
                if evidence:
                    return {
                        "video_fp": evidence.video_fp,
                        "audio_fp": evidence.audio_fp,
                        "duration_sec": evidence.duration_sec,
                        "s3_key_json": evidence.s3_key_json
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting evidence for detection {detection_id}: {e}")
            return None

    def _analyze_content(self, url: str, title: str, platform: str) -> dict[str, Any]:
        """Analyze content for suspicious patterns"""
        
        analysis = {
            "suspicious_patterns": [],
            "language_detection": "unknown",
            "content_type": "unknown",
            "risk_indicators": []
        }
        
        # Check for suspicious patterns in title
        title_lower = title.lower() if title else ""
        url_lower = url.lower()
        
        # Suspicious keywords
        suspicious_keywords = [
            "free", "download", "stream", "watch", "online", "hd", "full",
            "live", "cricket", "football", "match", "game", "sports"
        ]
        
        for keyword in suspicious_keywords:
            if keyword in title_lower or keyword in url_lower:
                analysis["suspicious_patterns"].append(keyword)
        
        # Language detection
        if any(char in title for char in "ট্যাপম্যাডখেলাম্যাচ"):
            analysis["language_detection"] = "bengali"
        elif any(word in title_lower for word in ["cricket", "football", "sports"]):
            analysis["language_detection"] = "english"
        else:
            analysis["language_detection"] = "mixed"
        
        # Content type detection
        if any(word in title_lower for word in ["live", "stream"]):
            analysis["content_type"] = "live_streaming"
        elif any(word in title_lower for word in ["match", "game", "sports"]):
            analysis["content_type"] = "sports_content"
        elif any(word in title_lower for word in ["full", "complete"]):
            analysis["content_type"] = "full_content"
        else:
            analysis["content_type"] = "unknown"
        
        # Risk indicators
        if "free" in title_lower:
            analysis["risk_indicators"].append("free_content")
        if "download" in title_lower:
            analysis["risk_indicators"].append("downloadable")
        if "stream" in title_lower:
            analysis["risk_indicators"].append("streaming")
        if platform in ["youtube", "telegram"]:
            analysis["risk_indicators"].append("popular_platform")
        
        return analysis

    def _calculate_risk_score(self, matches: list[MatchResult], content_analysis: dict) -> float:
        """Calculate overall risk score"""
        
        base_score = 0.0
        
        # Add score based on matches
        if matches:
            best_match = max(matches, key=lambda m: m.overall_confidence)
            base_score += best_match.overall_confidence * 0.6
        
        # Add score based on content analysis
        suspicious_count = len(content_analysis["suspicious_patterns"])
        base_score += min(suspicious_count * 0.1, 0.3)
        
        # Add score based on risk indicators
        risk_count = len(content_analysis["risk_indicators"])
        base_score += min(risk_count * 0.05, 0.2)
        
        # Add score based on platform
        if content_analysis.get("content_type") == "live_streaming":
            base_score += 0.1
        
        # Normalize to 0-1 range
        return min(1.0, base_score)

    def _determine_decision(self, risk_score: float, matches: list[MatchResult]) -> str:
        """Determine decision based on risk score and matches"""
        
        if risk_score >= 0.8:
            return "approve"
        elif risk_score >= 0.6:
            return "review"
        elif risk_score >= 0.4:
            return "review"
        else:
            return "reject"

    def _get_recommendation(self, decision: str, risk_score: float) -> str:
        """Get recommendation based on decision and risk score"""
        
        if decision == "approve":
            return "High confidence match. Proceed with takedown request."
        elif decision == "review":
            if risk_score >= 0.6:
                return "Moderate confidence. Manual review recommended before action."
            else:
                return "Low confidence. Additional analysis needed."
        else:
            return "No action required. Content appears legitimate."

    def batch_analyze(self, detection_ids: list[int]) -> list[dict[str, Any]]:
        """Analyze multiple detections in batch"""
        
        results = []
        
        for detection_id in detection_ids:
            try:
                result = self.analyze_detection(detection_id)
                results.append(result)
            except Exception as e:
                results.append({
                    "detection_id": detection_id,
                    "error": f"Analysis failed: {e}"
                })
        
        return results

    def update_reference_fingerprints(self, content_id: str, video_hash: str, audio_fp: str):
        """Update reference fingerprints"""
        
        try:
            with db_cursor() as cur:
                # Update or insert video fingerprint
                if video_hash:
                    cur.execute("""
                        INSERT INTO reference_fingerprints (content_id, kind, hash)
                        VALUES (%s, 'video', %s)
                        ON CONFLICT (content_id, kind) 
                        DO UPDATE SET hash = EXCLUDED.hash
                    """, (content_id, video_hash))
                
                # Update or insert audio fingerprint
                if audio_fp:
                    cur.execute("""
                        INSERT INTO reference_fingerprints (content_id, kind, hash)
                        VALUES (%s, 'audio', %s)
                        ON CONFLICT (content_id, kind) 
                        DO UPDATE SET hash = EXCLUDED.hash
                    """, (content_id, audio_fp))
                
                print(f"✅ Updated reference fingerprints for {content_id}")
        
        except Exception as e:
            print(f"Error updating reference fingerprints: {e}")

    def get_matching_stats(self) -> dict[str, Any]:
        """Get matching engine statistics"""
        
        try:
            with db_cursor() as cur:
                # Get total detections
                cur.execute("SELECT COUNT(*) FROM detections")
                total_detections = cur.fetchone()[0]
                
                # Get detections by decision
                cur.execute("""
                    SELECT decision, COUNT(*) 
                    FROM detections 
                    GROUP BY decision
                """)
                decisions = dict(cur.fetchall())
                
                # Get reference fingerprints count
                cur.execute("SELECT COUNT(*) FROM reference_fingerprints")
                total_references = cur.fetchone()[0]
                
                return {
                    "total_detections": total_detections,
                    "decisions": decisions,
                    "total_references": total_references,
                    "matching_thresholds": {
                        "video": self.video_threshold,
                        "audio": self.audio_threshold,
                        "llm": self.llm_threshold
                    }
                }
        
        except Exception as e:
            return {"error": f"Failed to get stats: {e}"}


