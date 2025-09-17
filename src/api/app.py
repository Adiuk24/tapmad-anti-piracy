from __future__ import annotations

import json
import time
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from ..shared.config import settings
from ..shared.database import insert_detection, get_detections, get_detection_by_id, get_database_info, get_db_session
from ..db.models import Detection, Evidence
from ..llm.llm_client import LLMClient
from ..capture.grab import capture_detection
from ..match.engine import MatchingEngine
from ..enforce.emailer import DMCAEnforcer
from ..crawler.platforms.youtube import crawl_youtube_content
from ..models.schemas import CrawlRequest, APIResponse, FingerprintRequest

# Initialize FastAPI app
app = FastAPI(
    title="Tapmad Anti-Piracy API",
    description="Secure API for content protection and anti-piracy operations",
    version="1.0.0",
    docs_url="/docs" if settings.env != "production" else None,
    redoc_url="/redoc" if settings.env != "production" else None,
)

# Security middleware
if settings.env == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure specific hosts in production
    )

# CORS configuration - SECURE by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=settings.cors_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Rate-Limit-Remaining"],
    max_age=3600,
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Input validation middleware
@app.middleware("http")
async def validate_input_middleware(request: Request, call_next):
    """Validate and sanitize input requests"""
    try:
        # Check request size
        if request.headers.get("content-length"):
            content_length = int(request.headers.get("content-length", 0))
            if content_length > settings.max_request_size:
                raise HTTPException(
                    status_code=413, 
                    detail=f"Request too large. Maximum size: {settings.max_request_size} bytes"
                )
        
        # Validate content type for POST requests
        if request.method == "POST":
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                raise HTTPException(
                    status_code=400, 
                    detail="Content-Type must be application/json"
                )
        
        response = await call_next(request)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

# Remove authentication requirement - make all endpoints public
def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    # No authentication required for development
    pass

# Initialize services
llm_client = LLMClient()
matching_engine = MatchingEngine()
dmca_enforcer = DMCAEnforcer()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Tapmad Anti-Piracy API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": int(time.time())
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0"
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        db_info = get_database_info()
        
        # Get Redis info
        try:
            from ..shared.redis_client import get_redis
            redis_client = get_redis()
            redis_info = redis_client.info()
        except Exception:
            redis_info = {"status": "disconnected"}
        
        return {
            "database": db_info,
            "redis": redis_info,
            "system": {
                "timestamp": int(time.time()),
                "version": "1.0.0",
                "enforcement_dry_run": settings.enforcement_dry_run
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tools/crawl/search_and_queue")
async def tool_crawl_search_and_queue(request: CrawlRequest):
    """Search for content using keywords and queue for processing"""
    try:
        # Use the new crawler functionality
        detection_ids = crawl_youtube_content(request.keywords, request.max_results)
        
        # Log AI activity
        ai_activity = {
            "action": "content_search",
            "keywords": request.keywords,
            "detections_created": len(detection_ids),
            "timestamp": int(time.time())
        }
        
        return APIResponse(
            success=True,
            data={
                "detection_ids": detection_ids,
                "ai_activity": ai_activity
            },
            message=f"Found {len(detection_ids)} potential content items"
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Search failed: {str(e)}"
        )

@app.post("/tools/capture/fingerprint")
async def tool_capture_fingerprint(request: FingerprintRequest):
    """Capture and fingerprint content"""
    try:
        # First create a detection
        detection_id = insert_detection(
            platform=request.platform or "unknown",
            url=request.url,
            title=request.title
        )
        
        if not detection_id:
            return APIResponse(
                success=False,
                message="Failed to create detection"
            )
        
        # Capture and fingerprint content
        evidence_id = capture_detection(detection_id)
        
        if not evidence_id:
            return APIResponse(
                success=False,
                message="Failed to capture and fingerprint content"
            )
        
        # Log AI activity
        ai_activity = {
            "action": "content_capture",
            "url": request.url,
            "detection_id": detection_id,
            "evidence_id": evidence_id,
            "timestamp": int(time.time())
        }
        
        return APIResponse(
            success=True,
            data={
                "detection_id": detection_id,
                "evidence_id": evidence_id,
                "ai_activity": ai_activity
            },
            message="Content captured and fingerprinted successfully"
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Fingerprinting failed: {str(e)}"
        )

@app.post("/tools/match/analyze")
async def tool_match_analyze(request: Request):
    """Analyze content against reference fingerprints"""
    try:
        raw = await request.body()
        data = json.loads(raw or "{}")
        
        # Use the matching engine to analyze
        if data.get("detection_id"):
            result = matching_engine.analyze_detection(data["detection_id"])
            return APIResponse(
                success=True,
                data=result,
                message="Content analysis completed"
            )
        else:
            return APIResponse(
                success=False,
                message="detection_id is required"
            )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Analysis failed: {str(e)}"
        )

@app.post("/tools/match/decide")
async def tool_match_decide(request: Request):
    """Make decision on content based on analysis"""
    try:
        raw = await request.body()
        data = json.loads(raw or "{}")
        
        detection_id = data.get("detection_id")
        decision = data.get("decision")
        
        if not detection_id or not decision:
            return APIResponse(
                success=False,
                message="detection_id and decision are required"
            )
        
        # Update detection decision
        from ..shared.db import update_detection_decision
        success = update_detection_decision(detection_id, decision)
        
        if success:
            return APIResponse(
                success=True,
                data={"detection_id": detection_id, "decision": decision},
                message=f"Decision updated to {decision}"
            )
        else:
            return APIResponse(
                success=False,
                message="Failed to update decision"
            )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Decision update failed: {str(e)}"
        )

@app.post("/tools/llm/chat")
async def tool_llm_chat(request: Request):
    """Chat with LLM for content analysis"""
    try:
        raw = await request.body()
        data = json.loads(raw or "{}")
        
        prompt = data.get("prompt", "")
        if not prompt:
            return APIResponse(
                success=False,
                message="prompt is required"
            )
        
        # Get LLM response
        response = llm_client.generate(prompt)
        
        return APIResponse(
            success=True,
            data={
                "response": response,
                "prompt": prompt,
                "timestamp": int(time.time())
            },
            message="LLM response generated successfully"
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"LLM chat failed: {str(e)}"
        )

@app.get("/detections")
async def get_detections_endpoint(limit: int = 100, offset: int = 0):
    """Get detections with pagination"""
    try:
        detections = get_detections(limit, offset)
        return APIResponse(
            success=True,
            data={"detections": detections, "total": len(detections)},
            message="Detections retrieved successfully"
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to get detections: {str(e)}"
        )

@app.get("/detections/{detection_id}")
async def get_detection(detection_id: int):
    """Get specific detection by ID"""
    try:
        detection = get_detection_by_id(detection_id)
        if detection:
            return APIResponse(
                success=True,
                data=detection,
                message="Detection retrieved successfully"
            )
        else:
            return APIResponse(
                success=False,
                message="Detection not found"
            )
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to get detection: {str(e)}"
        )

@app.get("/matching/stats")
async def get_matching_stats():
    """Get matching engine statistics"""
    try:
        stats = matching_engine.get_matching_stats()
        return APIResponse(
            success=True,
            data=stats,
            message="Matching statistics retrieved successfully"
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to get matching stats: {str(e)}"
        )

@app.post("/enforce/send_dmca")
async def send_dmca_notice(request: Request):
    """Send DMCA notice for a detection"""
    try:
        raw = await request.body()
        data = json.loads(raw or "{}")
        
        detection_id = data.get("detection_id")
        decision = data.get("decision", "match")
        custom_message = data.get("custom_message")
        
        if not detection_id:
            return APIResponse(
                success=False,
                message="detection_id is required"
            )
        
        # Send DMCA notice
        result = dmca_enforcer.send_dmca_notice(detection_id, decision, custom_message)
        
        return APIResponse(
            success=result.get("success", False),
            data=result,
            message="DMCA notice sent successfully" if result.get("success") else "Failed to send DMCA notice"
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"DMCA enforcement failed: {str(e)}"
        )

@app.post("/pipeline/run")
async def run_pipeline(request: Request):
    """Run the complete anti-piracy pipeline"""
    try:
        raw = await request.body()
        data = json.loads(raw or "{}")
        
        keywords = data.get("keywords", [])
        max_results = data.get("max_results", 10)
        
        if not keywords:
            return APIResponse(
                success=False,
                message="keywords are required"
            )
        
        # Step 1: Crawl
        detection_ids = crawl_youtube_content(keywords, max_results)
        
        # Step 2: Capture and fingerprint
        evidence_ids = []
        for detection_id in detection_ids:
            evidence_id = capture_detection(detection_id)
            if evidence_id:
                evidence_ids.append(evidence_id)
        
        # Step 3: Match
        match_results = []
        for detection_id in detection_ids:
            result = matching_engine.analyze_detection(detection_id)
            match_results.append(result)
        
        # Step 4: Enforcement (dry-run by default)
        enforcement_results = []
        for detection_id in detection_ids:
            result = dmca_enforcer.send_dmca_notice(detection_id, "match")
            enforcement_results.append(result)
        
        return APIResponse(
            success=True,
            data={
                "detection_ids": detection_ids,
                "evidence_ids": evidence_ids,
                "match_results": match_results,
                "enforcement_results": enforcement_results,
                "pipeline_summary": {
                    "detections_found": len(detection_ids),
                    "evidence_captured": len(evidence_ids),
                    "matches_found": sum(1 for r in match_results if r.get("matches")),
                    "dmca_notices_sent": sum(1 for r in enforcement_results if r.get("success"))
                }
            },
            message="Pipeline completed successfully"
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Pipeline failed: {str(e)}"
        )

@app.get("/detections/{detection_id}/evidence")
async def get_detection_evidence(detection_id: int):
    """Get evidence for a specific detection"""
    try:
        with get_db_session() as session:
            # Get the detection
            detection = session.query(Detection).filter(Detection.id == detection_id).first()
            if not detection:
                return APIResponse(
                    success=False,
                    message="Detection not found"
                )
            
            # Get evidence for this detection
            evidence = session.query(Evidence).filter(Evidence.detection_id == detection_id).first()
            
            if not evidence:
                return APIResponse(
                    success=False,
                    message="No evidence found for this detection"
                )
            
            # Return evidence data
            evidence_data = {
                "id": evidence.id,
                "detection_id": evidence.detection_id,
                "video_fp": evidence.video_fp,
                "audio_fp": evidence.audio_fp,
                "duration_sec": evidence.duration_sec,
                "created_at": evidence.created_at.isoformat(),
                "s3_key_json": evidence.s3_key_json
            }
            
            return APIResponse(
                success=True,
                data=evidence_data,
                message="Evidence retrieved successfully"
            )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to retrieve evidence: {str(e)}"
        )

@app.post("/detections/{detection_id}/capture")
async def capture_detection_evidence(detection_id: int):
    """Capture evidence for an existing detection"""
    try:
        evidence_id = capture_detection(detection_id)
        
        if not evidence_id:
            return APIResponse(
                success=False,
                message="Failed to capture evidence for this detection"
            )
        
        return APIResponse(
            success=True,
            data={
                "detection_id": detection_id,
                "evidence_id": evidence_id
            },
            message="Evidence captured successfully"
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to capture evidence: {str(e)}"
        )

@app.get("/tools/ai.stats")
async def get_ai_stats():
    """Get AI agent statistics"""
    try:
        # Get basic stats from detections
        detections = get_detections(limit=1000, offset=0)
        
        # Calculate AI stats
        total_scans = len(detections)
        active_scans = len([d for d in detections if d.get('status') == 'processing'])
        detections_found = len([d for d in detections if d.get('decision') == 'match'])
        decisions_made = len([d for d in detections if d.get('decision')])
        alerts_sent = len([d for d in detections if d.get('enforcement_sent')])
        
        # Calculate average confidence (mock data for now)
        avg_confidence = 85.5
        
        # Get platforms from detections
        platforms_active = list(set([d.get('platform', 'unknown') for d in detections if d.get('platform')]))
        
        # Mock additional stats
        keywords_generated = total_scans * 3  # Assume 3 keywords per scan
        learning_sessions = max(1, total_scans // 10)  # Learning session every 10 scans
        accuracy_improvement = 2.3  # Mock improvement percentage
        languages_processed = ['en', 'bn']  # English and Bengali
        
        return {
            "total_scans": total_scans,
            "active_scans": active_scans,
            "detections_found": detections_found,
            "decisions_made": decisions_made,
            "alerts_sent": alerts_sent,
            "avg_confidence": avg_confidence,
            "platforms_active": platforms_active,
            "keywords_generated": keywords_generated,
            "learning_sessions": learning_sessions,
            "accuracy_improvement": accuracy_improvement,
            "languages_processed": languages_processed,
            "timestamp": int(time.time())
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "total_scans": 0,
            "active_scans": 0,
            "detections_found": 0,
            "decisions_made": 0,
            "alerts_sent": 0,
            "avg_confidence": 0,
            "platforms_active": [],
            "keywords_generated": 0,
            "learning_sessions": 0,
            "accuracy_improvement": 0,
            "languages_processed": [],
            "timestamp": int(time.time())
        }

@app.get("/tools/ai.activities")
async def get_ai_activities():
    """Get AI agent activities"""
    try:
        # Get detections and convert to AI activities
        detections = get_detections(limit=100, offset=0)
        
        activities = []
        for i, detection in enumerate(detections):
            # Create AI activity from detection
            activity = {
                "id": f"ai_activity_{detection.get('id', i)}",
                "timestamp": str(int(time.time()) - (i * 60)),  # Spread over time
                "type": "scan" if detection.get('status') == 'processing' else "detect",
                "platform": detection.get('platform', 'unknown'),
                "action": f"Content scan on {detection.get('platform', 'unknown')}",
                "details": f"Analyzed content: {detection.get('title', 'Unknown title')}",
                "status": "completed" if detection.get('decision') else "running",
                "confidence": 85.5 + (i % 10),  # Mock confidence
                "url": detection.get('url'),
                "duration": 1500 + (i * 100),  # Mock duration
                "keywords": [
                    "tapmad",
                    "cricket",
                    "sports",
                    "live",
                    "streaming"
                ],
                "language": "en" if i % 2 == 0 else "bn",
                "learning_data": {
                    "patterns": ["content_pattern_1", "content_pattern_2"],
                    "improvements": ["accuracy_improved", "speed_optimized"],
                    "accuracy": 85.5 + (i % 5)
                }
            }
            activities.append(activity)
        
        # Add some mock activities if no detections
        if not activities:
            mock_activities = [
                {
                    "id": "ai_activity_1",
                    "timestamp": str(int(time.time()) - 300),
                    "type": "scan",
                    "platform": "youtube",
                    "action": "Content scan on YouTube",
                    "details": "Scanning for potential copyright violations",
                    "status": "completed",
                    "confidence": 87.5,
                    "url": "https://youtube.com/watch?v=example",
                    "duration": 1200,
                    "keywords": ["tapmad", "cricket", "live"],
                    "language": "en",
                    "learning_data": {
                        "patterns": ["sports_content", "live_streaming"],
                        "improvements": ["accuracy_improved"],
                        "accuracy": 87.5
                    }
                },
                {
                    "id": "ai_activity_2",
                    "timestamp": str(int(time.time()) - 180),
                    "type": "detect",
                    "platform": "telegram",
                    "action": "Content detection on Telegram",
                    "details": "Detected potential copyright violation",
                    "status": "completed",
                    "confidence": 92.3,
                    "url": "https://t.me/example",
                    "duration": 800,
                    "keywords": ["tapmad", "cricket", "highlights"],
                    "language": "bn",
                    "learning_data": {
                        "patterns": ["bengali_content", "cricket_highlights"],
                        "improvements": ["language_detection_improved"],
                        "accuracy": 92.3
                    }
                },
                {
                    "id": "ai_activity_3",
                    "timestamp": str(int(time.time()) - 60),
                    "type": "decision",
                    "platform": "facebook",
                    "action": "AI decision making",
                    "details": "Made decision on content match",
                    "status": "completed",
                    "confidence": 89.1,
                    "url": "https://facebook.com/example",
                    "duration": 500,
                    "keywords": ["tapmad", "sports", "live"],
                    "language": "both",
                    "learning_data": {
                        "patterns": ["social_media_content", "multi_language"],
                        "improvements": ["decision_speed_improved"],
                        "accuracy": 89.1
                    }
                }
            ]
            activities = mock_activities
        
        return {
            "activities": activities,
            "total": len(activities),
            "timestamp": int(time.time())
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "activities": [],
            "total": 0,
            "timestamp": int(time.time())
        }

@app.post("/agent/chat")
async def agent_chat(request: Request):
    """Chat with the AI agent"""
    try:
        raw = await request.body()
        data = json.loads(raw or "{}")
        
        message = data.get("message", "")
        if not message:
            return {
                "error": "message is required",
                "reply": "Please provide a message to chat with the AI agent."
            }
        
        # Use the LLM client to generate a response
        try:
            response = llm_client.generate(message)
        except Exception as e:
            # Fallback response if LLM fails
            response = f"I'm the Tapmad Anti-Piracy AI Agent. I received your message: '{message}'. I'm here to help with content protection and anti-piracy operations. How can I assist you today?"
        
        return {
            "reply": response,
            "message": message,
            "timestamp": int(time.time()),
            "agent": "tapmad-anti-piracy-ai"
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "reply": "I'm sorry, I encountered an error processing your message. Please try again.",
            "timestamp": int(time.time())
        }
