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

# Demo-app pages that gate their form rendering on a non-empty cart. The
# explorer launches a fresh BrowserContext (no shared cookies / localStorage),
# so we have to re-seed the cart here using the same UI-driven approach the
# crawler uses (engine/crawler.py:_seed_cart_state). Without this, /cart and
# /checkout render the empty-cart placeholder and every persona fill times
# out against selectors that don't exist.
STATE_DEPENDENT_PATHS: set = {"/cart", "/checkout"}
SEED_ADD_TO_CART_SELECTOR: str = "[data-testid='add-to-cart-btn-1']"


async def _seed_cart_and_navigate(page: Page, app_url: str, target_path: str) -> bool:
    """Seed the cart on /products then navigate client-side to target_path.

    Why client-side navigation: the demo-app's CartProvider has two competing
    useEffects (read cart from localStorage, write cart to localStorage on
    every cartItems change). On a hard navigation (page.goto), the write
    effect fires with the initial `[]` state — overwriting any localStorage
    entry — *before* the read effect can pick up the seeded cart. The result
    is that /cart and /checkout always render the empty-cart placeholder
    when reached via page.goto, so persona fills time out against form
    selectors that aren't in the DOM.

    Client-side nav via the Next.js `<Link>` anchor in the nav header keeps
    the CartProvider mounted — its state survives the route change — and the
    seeded item stays in `cartItems`. /cart and /checkout then render their
    full form surface and the persona actions can run normally.

    Args:
        page: The page to operate on (state listeners already attached).
        app_url: Application base URL, e.g. http://localhost:3001.
        target_path: Final path to land on, e.g. /cart or /checkout.

    Returns:
        True if seeded and navigated successfully, False on any failure
        (caller falls back to a hard navigation as last resort).
    """
    try:
        await page.goto(
            urljoin(app_url, "/products"),
            timeout=PAGE_LOAD_TIMEOUT_MS,
            wait_until="domcontentloaded",
        )
        try:
            await page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            pass
        await page.wait_for_selector(SEED_ADD_TO_CART_SELECTOR, timeout=PAGE_LOAD_TIMEOUT_MS)
        await page.click(SEED_ADD_TO_CART_SELECTOR)
        await page.wait_for_timeout(ACTION_SETTLE_WAIT_MS)

        # Click the in-nav Next.js Link. Selector matches the <a href="/X">
        # anchors emitted by _app.jsx's Navigation. Stays in client-side
        # routing so CartProvider does not remount.
        nav_selector = f"a[href='{target_path}']"
        await page.click(nav_selector, timeout=PAGE_LOAD_TIMEOUT_MS)
        try:
            await page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            pass
        # Extra settle so React commits the new route's first render. /cart
        # and /checkout gate form rendering on `cartItems.length > 0` so the
        # first render after navigation still shows the empty branch until
        # the next tick.
        await page.wait_for_timeout(ACTION_SETTLE_WAIT_MS)
        logger.debug("Explorer seeded cart + client-side navigated to %s", target_path)
        return True
    except PlaywrightTimeoutError:
        logger.warning("Cart-seed/navigate timed out for %s", target_path)
        return False
    except Exception as exc:
        logger.warning("Cart-seed/navigate error for %s: %s", target_path, exc)
        return False


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
    slow_mo_ms = int(os.getenv("EXPLORER_SLOW_MO_MS") or "0")

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=headless,
            slow_mo=slow_mo_ms,
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
            # For state-dependent routes (/cart, /checkout), seed the cart
            # on /products then *client-side* navigate to the target. The
            # CartProvider stays mounted across the Next.js Link click, so
            # the seeded item survives the route change and the target's
            # form actually renders. Falls back to a hard navigation if the
            # nav Link is unavailable for any reason.
            seeded = False
            if page_url in STATE_DEPENDENT_PATHS:
                seeded = await _seed_cart_and_navigate(page, app_url, page_url)

            if not seeded:
                # Either not a state-dependent route, or seed failed: do a
                # plain navigation to the target.
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
