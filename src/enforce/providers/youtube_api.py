from __future__ import annotations

"""
YouTube takedown submission provider.

Two supported modes:
1) webform (default): Automates the YouTube copyright complaint flow via Playwright.
   - Requires an authenticated session (cookie jar path), provided via env `YOUTUBE_COOKIES_PATH`.
   - DRY_RUN supported via env `YOUTUBE_DRY_RUN` (true|false). In dry-run we navigate and capture a screenshot
     but do not submit the final form.

2) api (restricted): If you have access to YouTube Content ID/Partner APIs, wire OAuth and submit via API.
   - Not enabled by default; will return requires_config until credentials provided.

Returns structured dicts with status and references; never returns plain strings.
"""

import json
import os
from typing import Optional, Dict, Any


class YouTubeEnforcer:
    def __init__(self) -> None:
        self.mode = os.getenv("YOUTUBE_MODE", "webform").lower()
        self.cookies_path = os.getenv("YOUTUBE_COOKIES_PATH")
        self.dry_run = os.getenv("YOUTUBE_DRY_RUN", "true").lower() in {"1", "true", "yes"}
        # Official help center entrypoint for copyright complaints
        self.form_url = os.getenv(
            "YOUTUBE_COPYRIGHT_FORM_URL",
            "https://support.google.com/youtube/contact/copyright",
        )

    def submit_takedown(self, url: str, reason: str, oauth_token: Optional[str] = None) -> Dict[str, Any]:
        if self.mode == "api":
            return self._submit_via_api(url, reason, oauth_token)
        return self._submit_via_webform(url, reason)

    def _submit_via_api(self, url: str, reason: str, oauth_token: Optional[str]) -> Dict[str, Any]:
        # Placeholder for future OAuth flow. Return requires_config until wired.
        return {
            "status": "requires_config",
            "message": "YouTube API mode not configured. Provide OAuth credentials and scopes.",
        }

    def _submit_via_webform(self, url: str, reason: str) -> Dict[str, Any]:
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception:
            return {
                "status": "error",
                "message": "Playwright not available in environment",
            }

        if not self.cookies_path or not os.path.exists(self.cookies_path):
            return {
                "status": "requires_config",
                "message": "Missing YOUTUBE_COOKIES_PATH for authenticated YouTube session",
            }

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            # Load cookies
            try:
                with open(self.cookies_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
            except Exception as e:
                browser.close()
                return {"status": "error", "message": f"Failed to load cookies: {e}"}

            page = context.new_page()
            try:
                page.goto(self.form_url, wait_until="domcontentloaded", timeout=60000)
                # Basic presence check
                title = page.title()
                # In dry-run, capture screenshot for audit and stop
                screenshot_path = None
                if self.dry_run:
                    screenshot_path = "/tmp/youtube_copyright_form.png"
                    page.screenshot(path=screenshot_path, full_page=True)
                    browser.close()
                    return {
                        "status": "dry_run",
                        "message": "Navigated to copyright form; dry run mode enabled",
                        "page_title": title,
                        "screenshot_path": screenshot_path,
                        "webform_url": self.form_url,
                    }

                # TODO: Implement full form automation safely once account-specific flow is confirmed.
                # For now, we return requires_config to avoid risky automated submissions by default.
                browser.close()
                return {
                    "status": "requires_config",
                    "message": "Automated submission disabled. Confirm selectors and enable non-dry run.",
                    "webform_url": self.form_url,
                }
            except Exception as e:
                try:
                    browser.close()
                except Exception:
                    pass
                return {"status": "error", "message": f"Webform navigation failed: {e}"}


def submit_takedown(url: str, reason: str, oauth_token: Optional[str] = None) -> Dict[str, Any]:
    """Submit a takedown to YouTube using configured mode.

    Returns structured dict with status and references.
    """
    return YouTubeEnforcer().submit_takedown(url, reason, oauth_token)


