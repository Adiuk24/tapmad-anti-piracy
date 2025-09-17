"""
DMCA enforcement module with email sending capabilities.
Supports dry-run mode for safe testing.
"""

from __future__ import annotations

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..shared.config import settings
from ..shared.database import insert_enforcement, get_detection_by_id, get_db_session
from ..db.models import Evidence, Match

logger = logging.getLogger(__name__)


class DMCAEnforcer:
    """DMCA enforcement handler"""
    
    def __init__(self):
        self.dry_run = settings.enforcement_dry_run
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_pass = settings.smtp_pass
        self.from_email = settings.from_email
        
        # Platform-specific recipients
        self.platform_recipients = {
            "youtube": ["copyright@youtube.com", "abuse@youtube.com"],
            "facebook": ["ip@fb.com", "abuse@facebook.com"],
            "twitter": ["copyright@twitter.com", "abuse@twitter.com"],
            "instagram": ["copyright@instagram.com", "abuse@instagram.com"],
            "telegram": ["dmca@telegram.org", "abuse@telegram.org"],
        }
    
    def send_dmca_notice(self, detection_id: int, decision: str, 
                        custom_message: Optional[str] = None) -> Dict[str, Any]:
        """Send DMCA notice for a detection"""
        
        try:
            # Get detection details
            detection = get_detection_by_id(detection_id)
            if not detection:
                return {"success": False, "error": "Detection not found"}
            
            platform = detection['platform']
            url = detection['url']
            title = detection.get('title', 'Unknown Title')
            
            # Get evidence and matches
            evidence = self._get_evidence_for_detection(detection_id)
            matches = self._get_matches_for_detection(detection_id)
            
            # Generate DMCA message
            dmca_message = self._generate_dmca_message(
                detection, evidence, matches, custom_message
            )
            
            # Get recipients
            recipients = self._get_recipients(platform)
            
            # Send email (or log in dry-run mode)
            if self.dry_run:
                result = self._send_dry_run(detection_id, decision, dmca_message, recipients)
            else:
                result = self._send_real_email(detection_id, decision, dmca_message, recipients)
            
            # Store enforcement record
            enforcement_id = insert_enforcement(
                detection_id=detection_id,
                decision=decision,
                dmca_message=dmca_message,
                recipient=", ".join(recipients),
                dry_run=self.dry_run,
                sent=result.get("success", False)
            )
            
            result["enforcement_id"] = enforcement_id
            return result
            
        except Exception as e:
            logger.error(f"Error sending DMCA notice for detection {detection_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_dmca_message(self, detection: Dict[str, Any], evidence: Optional[Dict[str, Any]], 
                              matches: List[Dict[str, Any]], custom_message: Optional[str] = None) -> str:
        """Generate DMCA takedown message"""
        
        if custom_message:
            return custom_message
        
        platform = detection['platform']
        url = detection['url']
        title = detection.get('title', 'Unknown Title')
        
        # Get match information
        match_info = ""
        if matches:
            best_match = max(matches, key=lambda m: m.get('overall_confidence', 0))
            match_info = f"""
MATCHING EVIDENCE:
- Reference ID: {best_match.get('reference_id', 'N/A')}
- Video Similarity: {best_match.get('video_similarity', 0):.3f}
- Audio Similarity: {best_match.get('audio_similarity', 0):.3f}
- Overall Confidence: {best_match.get('overall_confidence', 0):.3f}
"""
        
        # Get evidence information
        evidence_info = ""
        if evidence:
            duration = evidence.get('duration_sec', 0)
            evidence_info = f"""
EVIDENCE DETAILS:
- Duration: {duration:.1f} seconds
- Video Fingerprint: {evidence.get('video_fp', {}).get('hash', 'N/A')[:16]}...
- Audio Fingerprint: {evidence.get('audio_fp', {}).get('hash', 'N/A')[:16]}...
"""
        
        dmca_message = f"""
Subject: DMCA Takedown Notice - Copyright Infringement

Dear {platform.title()} Copyright Team,

I am writing to report a copyright infringement on your platform. The following content appears to be unauthorized use of copyrighted material owned by Tapmad.

INFRINGING CONTENT:
- URL: {url}
- Title: {title}
- Platform: {platform.title()}
- Reported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

{match_info}

{evidence_info}

COPYRIGHT CLAIM:
I have a good faith belief that the use of the copyrighted material described above is not authorized by the copyright owner, its agent, or the law.

I swear, under penalty of perjury, that the information in this notification is accurate and that I am the copyright owner or am authorized to act on behalf of the owner of an exclusive right that is allegedly infringed.

I request that you remove or disable access to the infringing material as soon as possible.

CONTACT INFORMATION:
- Name: Tapmad Anti-Piracy Team
- Email: {self.from_email}
- Company: Tapmad
- Address: [Your Business Address]

Please confirm receipt of this notice and the actions taken.

Thank you for your prompt attention to this matter.

Sincerely,
Tapmad Anti-Piracy Team

---
This is an automated DMCA notice generated by the Tapmad Anti-Piracy System.
For questions about this notice, please contact: {self.from_email}
"""
        
        return dmca_message.strip()
    
    def _get_recipients(self, platform: str) -> List[str]:
        """Get email recipients for a platform"""
        return self.platform_recipients.get(platform.lower(), ["abuse@example.com"])
    
    def _send_dry_run(self, detection_id: int, decision: str, message: str, 
                     recipients: List[str]) -> Dict[str, Any]:
        """Send dry-run email (log only)"""
        
        logger.info(f"DRY RUN - DMCA Notice for Detection {detection_id}")
        logger.info(f"Decision: {decision}")
        logger.info(f"Recipients: {', '.join(recipients)}")
        logger.info(f"Message Length: {len(message)} characters")
        logger.info("=" * 50)
        logger.info("DMCA MESSAGE:")
        logger.info(message)
        logger.info("=" * 50)
        
        return {
            "success": True,
            "dry_run": True,
            "message_id": f"dry-run-{detection_id}-{int(datetime.now().timestamp())}",
            "recipients": recipients,
            "message_length": len(message)
        }
    
    def _send_real_email(self, detection_id: int, decision: str, message: str, 
                        recipients: List[str]) -> Dict[str, Any]:
        """Send real email via SMTP"""
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"DMCA Takedown Notice - Detection {detection_id}"
            
            # Add body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                
                text = msg.as_string()
                server.sendmail(self.from_email, recipients, text)
            
            logger.info(f"DMCA notice sent successfully for detection {detection_id}")
            logger.info(f"Recipients: {', '.join(recipients)}")
            
            return {
                "success": True,
                "dry_run": False,
                "message_id": f"real-{detection_id}-{int(datetime.now().timestamp())}",
                "recipients": recipients,
                "message_length": len(message)
            }
            
        except Exception as e:
            logger.error(f"Failed to send DMCA email for detection {detection_id}: {e}")
            return {
                "success": False,
                "dry_run": False,
                "error": str(e),
                "recipients": recipients
            }
    
    def _get_evidence_for_detection(self, detection_id: int) -> Optional[Dict[str, Any]]:
        """Get evidence for a detection"""
        try:
            with get_db_session() as session:
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
    
    def _get_matches_for_detection(self, detection_id: int) -> List[Dict[str, Any]]:
        """Get matches for a detection"""
        try:
            with get_db_session() as session:
                matches = session.query(Match).filter(Match.detection_id == detection_id).all()
                return [
                    {
                        "reference_id": match.reference_id,
                        "video_score": match.video_score,
                        "audio_score": match.audio_score,
                        "decision": match.decision,
                        "overall_confidence": (match.video_score + match.audio_score) / 2
                    }
                    for match in matches
                ]
        except Exception as e:
            logger.error(f"Error getting matches for detection {detection_id}: {e}")
            return []


# Celery task for async enforcement
def send_dmca_email_task(detection_id: int, decision: str = "match", 
                        custom_message: Optional[str] = None) -> Dict[str, Any]:
    """Celery task for sending DMCA emails"""
    
    enforcer = DMCAEnforcer()
    return enforcer.send_dmca_notice(detection_id, decision, custom_message)