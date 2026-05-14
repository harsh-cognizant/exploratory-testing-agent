"""
Module: engine/anomaly_detector.py
Purpose: Detect anomalies during Playwright exploration and return structured
         findings. Captures console errors, HTTP errors, form validation bypasses,
         unexpected redirects, and page crashes. Does NOT make Claude API calls —
         it captures raw events only.
Author: Team / Claude Code
Created: 2026-05-14
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Anomaly type definitions per CLAUDE.md §4.10.
ANOMALY_TYPES: Dict[str, Dict[str, str]] = {
    "js_console_error": {
        "detection": "page.on('console') where msg.type == 'error'",
        "severity": "medium",
    },
    "http_4xx_5xx": {
        "detection": "page.on('response') where response.status >= 400",
        "severity": "high",
    },
    "unexpected_redirect": {
        "detection": "URL after action != expected URL",
        "severity": "medium",
    },
    "form_accepts_invalid_data": {
        "detection": "form submits without validation error element visible",
        "severity": "high",
    },
    "page_crash_blank": {
        "detection": "page.content() is empty or contains only error text",
        "severity": "critical",
    },
}


class AnomalyCollector:
    """Collects anomaly events during a single page exploration session.

    Attach this to Playwright event listeners before performing actions.
    After all actions on a page, call `build_findings()` to convert
    captured anomalies into Finding-compatible dicts.

    Args:
        page_url: The URL path being explored (e.g. '/checkout').
        node_id: The graph node ID being explored.
        persona: The persona name performing the exploration.
    """

    def __init__(self, page_url: str, node_id: str, persona: str) -> None:
        """Initialize the anomaly collector for a page exploration session."""
        self.page_url: str = page_url
        self.node_id: str = node_id
        self.persona: str = persona
        self.console_errors: List[str] = []
        self.http_errors: List[Dict[str, Any]] = []
        self.redirects: List[Dict[str, str]] = []
        self.actions_taken: List[Dict[str, Any]] = []
        self._expected_url: Optional[str] = None

    def set_expected_url(self, url: str) -> None:
        """Set the expected URL before performing an action.

        Args:
            url: The URL we expect to remain on after the action.
        """
        self._expected_url = url

    def on_console_message(self, msg: Any) -> None:
        """Handle console message events from Playwright.

        Args:
            msg: Playwright ConsoleMessage object.
        """
        try:
            msg_type = msg.type
            if msg_type == "error":
                text = msg.text
                # Filter out common React dev-mode noise.
                if "Download the React DevTools" in text:
                    return
                if "Warning:" in text and "React" in text:
                    return
                self.console_errors.append(text)
                logger.debug("Console error captured: %s", text[:200])
        except Exception as exc:
            logger.debug("Error processing console message: %s", exc)

    def on_response(self, response: Any) -> None:
        """Handle HTTP response events from Playwright.

        Args:
            response: Playwright Response object.
        """
        try:
            status = response.status
            if status >= 400:
                self.http_errors.append({
                    "url": response.url,
                    "status": status,
                    "status_text": response.status_text,
                })
                logger.debug("HTTP %d captured: %s", status, response.url)
        except Exception as exc:
            logger.debug("Error processing response: %s", exc)

    def check_redirect(self, actual_url: str) -> None:
        """Check if the page redirected unexpectedly after an action.

        Args:
            actual_url: The actual URL after the action completed.
        """
        if self._expected_url and actual_url != self._expected_url:
            # Only flag if it's a different path, not just query/hash change.
            from urllib.parse import urlparse
            expected_path = urlparse(self._expected_url).path
            actual_path = urlparse(actual_url).path
            if expected_path != actual_path:
                self.redirects.append({
                    "expected": self._expected_url,
                    "actual": actual_url,
                })
                logger.debug(
                    "Redirect detected: expected %s, got %s",
                    self._expected_url, actual_url,
                )

    def record_action(self, action: Dict[str, Any]) -> None:
        """Record an action that was performed for reproduction steps.

        Args:
            action: The action dict (action_type, target, value, reason).
        """
        self.actions_taken.append(action)

    async def check_page_crash(self, page: Any) -> Optional[Dict[str, str]]:
        """Check if the page has crashed or gone blank.

        Args:
            page: Playwright Page object.

        Returns:
            Anomaly dict if crash detected, None otherwise.
        """
        try:
            content = await page.content()
            if not content or len(content.strip()) < 50:
                return {
                    "anomaly_type": "page_crash_blank",
                    "detail": "Page content is empty or minimal after action",
                }
            # Check for common error page indicators.
            lower_content = content.lower()
            error_indicators = [
                "application error",
                "internal server error",
                "unhandled runtime error",
                "this page isn't working",
            ]
            for indicator in error_indicators:
                if indicator in lower_content:
                    return {
                        "anomaly_type": "page_crash_blank",
                        "detail": f"Error page detected: '{indicator}' found in content",
                    }
        except Exception as exc:
            logger.debug("Error checking page crash: %s", exc)
            return {
                "anomaly_type": "page_crash_blank",
                "detail": f"Page content check failed: {exc}",
            }
        return None

    async def check_form_validation(
        self,
        page: Any,
        action: Dict[str, Any],
    ) -> Optional[Dict[str, str]]:
        """Check if a form accepted invalid data without showing validation errors.

        Only checks after 'fill' or 'submit' actions that used intentionally
        bad input data (empty fields, wrong types, etc.).

        Args:
            page: Playwright Page object.
            action: The action that was performed.

        Returns:
            Anomaly dict if invalid data was accepted, None otherwise.
        """
        action_type = action.get("action_type", "")
        if action_type not in ("submit", "click"):
            return None

        try:
            # Check if any validation error elements are visible.
            error_selectors = [
                ".error-message",
                "[data-testid='error-message']",
                ".error",
                ".field-error",
                "[role='alert']",
            ]
            for selector in error_selectors:
                try:
                    error_el = page.locator(selector)
                    count = await error_el.count()
                    if count > 0:
                        # Validation errors are visible — form is working correctly.
                        return None
                except Exception:
                    continue

            # If we submitted a form and no validation errors appeared,
            # this could indicate the form accepted invalid data.
            # Only flag this if we previously filled with intentionally bad data.
            reason = action.get("reason", "").lower()
            bad_data_keywords = [
                "empty", "invalid", "wrong", "negative", "sql",
                "injection", "xss", "script", "blank", "missing",
            ]
            if any(kw in reason for kw in bad_data_keywords):
                return {
                    "anomaly_type": "form_accepts_invalid_data",
                    "detail": f"Form may have accepted invalid data. Action reason: {action.get('reason', '')}",
                }
        except Exception as exc:
            logger.debug("Error checking form validation: %s", exc)

        return None

    def _build_reproduction_steps(self) -> List[str]:
        """Generate reproduction steps from the recorded action sequence.

        Returns:
            List of human-readable step strings.
        """
        steps: List[str] = []
        steps.append(f"Navigate to {self.page_url}")
        for action in self.actions_taken:
            action_type = action.get("action_type", "unknown")
            target = action.get("target", "unknown")
            value = action.get("value")
            reason = action.get("reason", "")

            if action_type == "fill":
                steps.append(f"Fill '{target}' with '{value}'")
            elif action_type == "click":
                steps.append(f"Click '{target}'")
            elif action_type == "navigate":
                steps.append(f"Navigate to '{value}'")
            elif action_type == "submit":
                steps.append(f"Submit form via '{target}'")
            elif action_type == "clear":
                steps.append(f"Clear field '{target}'")
        return steps

    def build_findings(self) -> List[Dict[str, Any]]:
        """Convert all captured anomalies into Finding-compatible dicts.

        Per CLAUDE.md §4.10: populates all Finding fields except screenshot_url
        (added by explorer after saving file).

        Returns:
            List of finding dicts matching the Finding schema.
        """
        findings: List[Dict[str, Any]] = []
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        repro_steps = self._build_reproduction_steps()

        # Console errors → findings.
        for error_text in self.console_errors:
            finding_id = f"finding_{uuid.uuid4().hex[:8]}"
            findings.append({
                "id": finding_id,
                "timestamp": timestamp,
                "persona": self.persona,
                "page": self.page_url,
                "node_id": self.node_id,
                "action": "Browser interaction triggered JavaScript console error",
                "anomaly": f"JS console error: {error_text[:300]}",
                "anomaly_type": "js_console_error",
                "severity": "medium",
                "screenshot_path": None,
                "screenshot_url": None,
                "reproduction_steps": repro_steps,
                "suggested_assertion": f"Assert no JavaScript console errors on {self.page_url}",
            })

        # HTTP errors → findings.
        for http_err in self.http_errors:
            finding_id = f"finding_{uuid.uuid4().hex[:8]}"
            status = http_err["status"]
            severity = "critical" if status >= 500 else "high"
            findings.append({
                "id": finding_id,
                "timestamp": timestamp,
                "persona": self.persona,
                "page": self.page_url,
                "node_id": self.node_id,
                "action": f"Request to {http_err['url']} returned HTTP {status}",
                "anomaly": f"HTTP {status} {http_err.get('status_text', '')} on {http_err['url']}",
                "anomaly_type": "http_4xx_5xx",
                "severity": severity,
                "screenshot_path": None,
                "screenshot_url": None,
                "reproduction_steps": repro_steps,
                "suggested_assertion": f"Assert all API calls on {self.page_url} return 2xx status",
            })

        # Redirects → findings.
        for redirect in self.redirects:
            finding_id = f"finding_{uuid.uuid4().hex[:8]}"
            findings.append({
                "id": finding_id,
                "timestamp": timestamp,
                "persona": self.persona,
                "page": self.page_url,
                "node_id": self.node_id,
                "action": f"Expected to stay on {redirect['expected']}",
                "anomaly": f"Unexpected redirect from {redirect['expected']} to {redirect['actual']}",
                "anomaly_type": "unexpected_redirect",
                "severity": "medium",
                "screenshot_path": None,
                "screenshot_url": None,
                "reproduction_steps": repro_steps,
                "suggested_assertion": f"Assert page remains on {redirect['expected']} after action",
            })

        return findings
