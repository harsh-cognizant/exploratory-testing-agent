"""
Module: engine/explorer.py
Purpose: Run Playwright-based exploration using persona action lists. Capture all
         anomalies as findings. Uses async_playwright with Chromium per CLAUDE.md §4.9.
Author: Team / Claude Code
Created: 2026-05-14
"""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from dotenv import load_dotenv
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from engine.anomaly_detector import AnomalyCollector

load_dotenv()

logger = logging.getLogger(__name__)

# Constants per CLAUDE.md §4.9 and §13.
PAGE_LOAD_TIMEOUT_MS: int = 8000
ACTION_SETTLE_WAIT_MS: int = 500
SCREENSHOT_DIR: str = os.getenv("SCREENSHOTS_DIR", "./screenshots")
BROWSER_CHANNEL: str = "chrome"


async def execute_action(page: Page, action: Dict[str, Any]) -> None:
    """Execute a single persona action on the page.

    Per CLAUDE.md §4.9 pattern: handles fill, click, navigate, submit, clear.

    Args:
        page: Playwright Page object.
        action: Action dict with action_type, target, value.

    Raises:
        PlaywrightTimeoutError: If the action times out.
    """
    action_type = action.get("action_type", "")
    target = action.get("target", "")
    value = action.get("value")

    if action_type == "fill":
        await page.fill(target, value or "")
    elif action_type == "click":
        await page.click(target, timeout=PAGE_LOAD_TIMEOUT_MS)
    elif action_type == "navigate":
        await page.goto(value or "", timeout=PAGE_LOAD_TIMEOUT_MS)
    elif action_type == "submit":
        await page.press(target, "Enter")
    elif action_type == "clear":
        await page.fill(target, "")


async def _take_screenshot(page: Page, finding_id: str) -> Optional[str]:
    """Take a screenshot and save it to the screenshots directory.

    Args:
        page: Playwright Page object.
        finding_id: The finding ID for the filename.

    Returns:
        Relative path to the saved screenshot, or None on failure.
    """
    Path(SCREENSHOT_DIR).mkdir(exist_ok=True)
    filename = f"{finding_id}.png"
    filepath = Path(SCREENSHOT_DIR) / filename
    try:
        await page.screenshot(path=str(filepath), full_page=True)
        logger.debug("Screenshot saved: %s", filepath)
        return str(filepath)
    except Exception as exc:
        logger.warning("Failed to take screenshot: %s", exc)
        return None


async def explore_node(
    node_id: str,
    node_attrs: Dict[str, Any],
    persona_actions: List[Dict[str, Any]],
    app_url: str,
    persona: str,
) -> List[Dict[str, Any]]:
    """Run Playwright-based exploration on a single node with persona actions.

    Per CLAUDE.md §4.9:
    - Sets up console/network listeners BEFORE navigating.
    - Executes each action, checking for anomalies after each.
    - Takes screenshots on every anomaly.
    - Wraps every Playwright call in try/except.

    Args:
        node_id: Graph node ID being explored.
        node_attrs: Node attributes from the graph.
        persona_actions: List of action dicts from personas.py.
        app_url: Application base URL (e.g. 'http://localhost:3001').
        persona: Persona name for finding metadata.

    Returns:
        List of finding dicts matching the Finding schema.
    """
    page_url = node_attrs.get("url", "/")
    target_url = urljoin(app_url, page_url)

    all_findings: List[Dict[str, Any]] = []

    # Allow headless override for demos.
    raw_headless = (os.getenv("EXPLORER_HEADLESS") or "true").strip().lower()
    headless = raw_headless not in ("false", "0", "no")

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=headless,
            channel=BROWSER_CHANNEL,
        )
        context: BrowserContext = await browser.new_context()
        page: Page = await context.new_page()

        # Initialize anomaly collector.
        collector = AnomalyCollector(
            page_url=page_url,
            node_id=node_id,
            persona=persona,
        )

        # Set up event listeners BEFORE navigating per §4.9.
        page.on("console", collector.on_console_message)
        page.on("response", collector.on_response)

        try:
            # Navigate to the target page.
            await page.goto(target_url, timeout=PAGE_LOAD_TIMEOUT_MS)
            try:
                await page.wait_for_load_state(
                    "networkidle", timeout=PAGE_LOAD_TIMEOUT_MS
                )
            except PlaywrightTimeoutError:
                logger.debug("networkidle timeout on %s; proceeding", page_url)

            # Execute each persona action.
            for action_idx, action in enumerate(persona_actions):
                try:
                    # Record expected URL before action.
                    collector.set_expected_url(page.url)
                    collector.record_action(action)

                    logger.debug(
                        "Explorer: %s action %d/%d on %s: %s %s",
                        persona, action_idx + 1, len(persona_actions),
                        page_url, action.get("action_type"), action.get("target"),
                    )

                    # Execute the action.
                    await execute_action(page, action)

                    # Wait for UI to settle per §4.9.
                    await page.wait_for_timeout(ACTION_SETTLE_WAIT_MS)

                    # Check for redirect anomaly.
                    collector.check_redirect(page.url)

                    # Check for page crash.
                    crash = await collector.check_page_crash(page)
                    if crash:
                        finding_id = f"finding_{uuid.uuid4().hex[:8]}"
                        screenshot_path = await _take_screenshot(page, finding_id)
                        all_findings.append({
                            "id": finding_id,
                            "timestamp": collector.build_findings()[0]["timestamp"]
                                if collector.build_findings() else
                                __import__("datetime").datetime.now(
                                    __import__("datetime").timezone.utc
                                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "persona": persona,
                            "page": page_url,
                            "node_id": node_id,
                            "action": f"Action '{action.get('action_type')}' on '{action.get('target')}'",
                            "anomaly": crash["detail"],
                            "anomaly_type": crash["anomaly_type"],
                            "severity": "critical",
                            "screenshot_path": screenshot_path,
                            "screenshot_url": f"/screenshots/{finding_id}.png" if screenshot_path else None,
                            "reproduction_steps": collector._build_reproduction_steps(),
                            "suggested_assertion": f"Assert page does not crash on {page_url}",
                        })

                    # Check for form validation bypass.
                    form_bypass = await collector.check_form_validation(page, action)
                    if form_bypass:
                        finding_id = f"finding_{uuid.uuid4().hex[:8]}"
                        screenshot_path = await _take_screenshot(page, finding_id)
                        all_findings.append({
                            "id": finding_id,
                            "timestamp": __import__("datetime").datetime.now(
                                __import__("datetime").timezone.utc
                            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "persona": persona,
                            "page": page_url,
                            "node_id": node_id,
                            "action": f"Action '{action.get('action_type')}' on '{action.get('target')}'",
                            "anomaly": form_bypass["detail"],
                            "anomaly_type": form_bypass["anomaly_type"],
                            "severity": "high",
                            "screenshot_path": screenshot_path,
                            "screenshot_url": f"/screenshots/{finding_id}.png" if screenshot_path else None,
                            "reproduction_steps": collector._build_reproduction_steps(),
                            "suggested_assertion": f"Assert form on {page_url} rejects invalid data with visible error",
                        })

                except PlaywrightTimeoutError:
                    logger.warning(
                        "Timeout on action %d for %s on %s; continuing",
                        action_idx, persona, page_url,
                    )
                except Exception as exc:
                    logger.warning(
                        "Error on action %d for %s on %s: %s; continuing",
                        action_idx, persona, page_url, exc,
                    )

            # Build findings from collected anomalies (console errors, HTTP errors, redirects).
            event_findings = collector.build_findings()
            for finding in event_findings:
                screenshot_path = await _take_screenshot(page, finding["id"])
                finding["screenshot_path"] = screenshot_path
                finding["screenshot_url"] = (
                    f"/screenshots/{finding['id']}.png" if screenshot_path else None
                )
                all_findings.append(finding)

        except PlaywrightTimeoutError:
            logger.warning("Failed to load %s; skipping exploration", target_url)
        except Exception as exc:
            logger.error("Explorer error on %s: %s", target_url, exc)
        finally:
            await page.close()
            await context.close()
            await browser.close()

    logger.info(
        "Explorer: %s found %d findings on %s (%s)",
        persona, len(all_findings), page_url, node_id,
    )
    return all_findings
