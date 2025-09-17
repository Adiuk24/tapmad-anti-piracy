from __future__ import annotations

from typing import Dict, Any, List


def build_abuse_email(url: str, summary: str, attachments: List[str] | None = None) -> Dict[str, Any]:
    """Build an evidence-pack email structure for Telegram.

    Returns a dictionary containing 'subject', 'body', and 'attachments' entries.
    Attachments should be S3 keys or file paths prepared by the evidence pipeline.
    """
    return {
        "to": "dmca@telegram.org",
        "subject": "DMCA - Unauthorized content",
        "body": (
            "Dear Telegram Abuse Team,\n\n"
            f"We have identified unauthorized content at: {url}\n"
            f"Summary: {summary}\n\n"
            "Please remove the content under DMCA. Evidence is attached.\n\n"
            "Regards,\nTapmad Anti-Piracy"
        ),
        "attachments": attachments or [],
    }


