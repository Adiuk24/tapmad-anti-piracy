from __future__ import annotations

from typing import Dict, Any


def build_form_payload(url: str, summary: str) -> Dict[str, Any]:
    """Render a data payload structure for manual Twitter/X submission.

    This payload is a helper for human operators to paste into provider forms.
    """
    return {
        "provider": "twitter",
        "url": url,
        "description": summary,
        "rights_holder": "Tapmad",
        "contact_email": "anti-piracy@tapmad.com",
    }


