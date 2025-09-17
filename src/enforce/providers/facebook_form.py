from __future__ import annotations

from typing import Dict, Any


def build_form_payload(url: str, summary: str) -> Dict[str, Any]:
    """Render a data payload structure for manual Facebook submission."""
    return {
        "provider": "facebook",
        "url": url,
        "description": summary,
        "rights_holder": "Tapmad",
        "contact_email": "anti-piracy@tapmad.com",
    }


