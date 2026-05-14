"""
Module: engine/crawler.py
Purpose: Discover all reachable routes and interactive elements in a web app
         using Playwright's async API. Emits one dict per discovered surface
         (page, form, button, input, link). Output feeds graph_builder.py.
Created: 2026-05-14
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

logger = logging.getLogger(__name__)

# Constants — magic numbers/strings live here per Section 21.5
MAX_CRAWL_DEPTH: int = 3
PAGE_TIMEOUT_MS: int = 10_000
NETWORKIDLE_TIMEOUT_MS: int = 5_000
# After networkidle the React useEffects that populate cart state from
# localStorage still need a tick to mount and re-render. 500ms is comfortably
# more than enough for the demo-app's CartProvider effect to run.
CLIENT_SETTLE_MS: int = 500

# Use the user's system-installed Chrome via Playwright's "channel" mechanism
# instead of downloading Playwright's bundled chromium. This avoids the corporate
# TLS proxy that blocks downloads from cdn.playwright.dev (see DEVLOG 2026-05-14).
BROWSER_CHANNEL: str = "chrome"

# Demo-app pages that require cart state to render their full element surface.
# The crawler seeds localStorage with a sample item before visiting these.
STATE_DEPENDENT_PATHS: Set[str] = {"/cart", "/checkout"}

# `data-testid` of any Add-to-Cart button on /products. The crawler clicks
# this once before crawling state-dependent routes to seed real cart state.
# Doing it via UI (rather than localStorage injection) is the only reliable
# way given the demo-app's `useEffect(() => save, [cartItems])` writes `[]`
# back to localStorage on every fresh page mount and races any pre-seed.
SEED_ADD_TO_CART_SELECTOR: str = "[data-testid='add-to-cart-btn-1']"


def _path_of(url: str) -> str:
    """Return the path component of a URL or the input if already a path.

    Strips query string and fragment (e.g. `/login#` and `/cart?foo=1` both
    normalise to their path). Empty path collapses to "/".

    Args:
        url: Either an absolute URL ("http://localhost:3001/login") or a path ("/login").

    Returns:
        Path string with leading slash, e.g. "/login".
    """
    parsed = urlparse(url)
    if parsed.scheme:
        return parsed.path or "/"
    cleaned = url.split("#", 1)[0].split("?", 1)[0]
    if not cleaned:
        return "/"
    return cleaned if cleaned.startswith("/") else f"/{cleaned}"


def _is_internal(href: Optional[str], app_url: str) -> bool:
    """Return True if href points at the same origin as app_url (or is a relative path)."""
    if not href:
        return False
    if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
        return False
    if href.startswith("/"):
        return True
    parsed_href = urlparse(href)
    parsed_app = urlparse(app_url)
    return parsed_href.netloc == parsed_app.netloc or not parsed_href.netloc


def _slug(path: str) -> str:
    """Convert a URL path to a short slug suitable for node ids.

    Examples:
        "/" → "home"
        "/products" → "products"
        "/checkout/step-1" → "checkout_step-1"
    """
    cleaned = path.strip("/")
    if not cleaned:
        return "home"
    return cleaned.replace("/", "_")


def _dedup_key(entry: Dict[str, Any]) -> str:
    """Key used to deduplicate discovered elements: url + element_type + element_id."""
    return f"{entry['url']}|{entry['element_type']}|{entry['element_id']}"


def _clean_id_token(raw: Optional[str]) -> str:
    """Reduce arbitrary text to an ASCII-safe identifier token.

    Strips emojis and other non-word characters, lowercases, and collapses
    runs of underscores. Returns empty string for inputs that contain no
    alphanumeric characters at all (caller must supply a fallback).
    """
    if not raw:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").lower()
    return cleaned


async def _seed_cart_state(context: BrowserContext, app_url: str) -> None:
    """Seed cart state by clicking Add-to-Cart on /products in a real page.

    The demo-app's `_app.jsx` has a useEffect that writes `JSON.stringify(cartItems)`
    to localStorage whenever cartItems changes — including the initial change
    from `undefined` → `[]` on mount. That race overwrites any localStorage
    pre-seed before the read-effect can populate state. UI-driven seeding
    (a real click) is the only path that survives a fresh _app.jsx mount on
    subsequent pages because by then cartItems is non-empty and persists
    correctly back through the write-effect.

    Args:
        context: Playwright browser context the BFS will reuse.
        app_url: Application base URL, e.g. "http://localhost:3001".
    """
    page = await context.new_page()
    try:
        await page.goto(
            urljoin(app_url, "/products"),
            timeout=PAGE_TIMEOUT_MS,
            wait_until="domcontentloaded",
        )
        try:
            await page.wait_for_load_state("networkidle", timeout=NETWORKIDLE_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            logger.debug("networkidle timeout during cart seed; proceeding")
        await page.wait_for_selector(SEED_ADD_TO_CART_SELECTOR, timeout=PAGE_TIMEOUT_MS)
        await page.click(SEED_ADD_TO_CART_SELECTOR)
        # Wait for the React state update + useEffect write to propagate.
        await page.wait_for_timeout(CLIENT_SETTLE_MS)
        logger.info("Seeded cart via real Add-to-Cart click on /products")
    except PlaywrightTimeoutError:
        logger.warning("Failed to seed cart state; /cart and /checkout may render empty branches")
    finally:
        await page.close()


async def _discover_on_page(page: Page, path: str) -> List[Dict[str, Any]]:
    """Return all interactive elements discovered on the currently-loaded page.

    Always emits a `page` entry first, then one entry per `<form>`, `<button>`,
    `<input>`, and `<a>` found. Selectors prefer `[data-testid='…']`.

    Args:
        page: Playwright Page already navigated to `path`.
        path: The URL path being scanned (e.g. "/login").

    Returns:
        List of element dicts matching the schema in CLAUDE.md §4.6.
    """
    elements: List[Dict[str, Any]] = []

    # Page-level entry — represents the page itself as a discoverable node.
    elements.append({
        "url": path,
        "element_type": "page",
        "element_id": _slug(path),
        "element_selector": "body",
        "label": f"{_slug(path).replace('_', ' ').title()} page ({path})",
        "parent_url": None,
    })

    # Forms — use JS to extract data-testid + id + first child input names.
    form_handles = await page.query_selector_all("form")
    for handle in form_handles:
        testid = await handle.get_attribute("data-testid")
        form_id = await handle.get_attribute("id")
        element_id = testid or form_id or f"form_{len(elements)}"
        selector = (
            f"[data-testid='{testid}']" if testid
            else (f"#{form_id}" if form_id else "form")
        )
        elements.append({
            "url": path,
            "element_type": "form",
            "element_id": element_id,
            "element_selector": selector,
            "label": f"Form '{element_id}' on {path}",
            "parent_url": path,
        })

    # Buttons — discover all submittable and non-submittable buttons.
    button_handles = await page.query_selector_all("button")
    for handle in button_handles:
        testid = await handle.get_attribute("data-testid")
        btn_id = await handle.get_attribute("id")
        text = (await handle.text_content() or "").strip() or None
        element_id = (
            testid or btn_id or _clean_id_token(text) or f"btn_{len(elements)}"
        )
        selector = (
            f"[data-testid='{testid}']" if testid
            else (f"#{btn_id}" if btn_id else f"button:has-text('{text}')" if text else "button")
        )
        elements.append({
            "url": path,
            "element_type": "button",
            "element_id": element_id,
            "element_selector": selector,
            "label": f"Button '{text or element_id}' on {path}",
            "parent_url": path,
        })

    # Inputs — every <input> with a data-testid or id becomes a node.
    input_handles = await page.query_selector_all("input")
    for handle in input_handles:
        testid = await handle.get_attribute("data-testid")
        inp_id = await handle.get_attribute("id")
        inp_name = await handle.get_attribute("name")
        inp_type = (await handle.get_attribute("type")) or "text"
        element_id = testid or inp_id or inp_name or f"input_{len(elements)}"
        selector = (
            f"[data-testid='{testid}']" if testid
            else (f"#{inp_id}" if inp_id else f"input[name='{inp_name}']" if inp_name else "input")
        )
        elements.append({
            "url": path,
            "element_type": "input",
            "element_id": element_id,
            "element_selector": selector,
            "label": f"Input '{element_id}' (type={inp_type}) on {path}",
            "parent_url": path,
        })

    # Links — emit one entry per internal anchor; external links are skipped at
    # crawl-queue level but emitted here for completeness so graph_builder can
    # draw navigation edges. parent_url is the current page; url is the target.
    link_handles = await page.query_selector_all("a[href]")
    for handle in link_handles:
        href = await handle.get_attribute("href")
        text = (await handle.text_content() or "").strip()
        if not href:
            continue
        target = _path_of(href)
        # Don't emit links to the same page (e.g. anchor "#" buttons) — those
        # already appear as buttons or are visual-only "Forgot password?" links.
        if target == path:
            continue
        element_id = _clean_id_token(text) or _slug(target)
        elements.append({
            "url": target,
            "element_type": "link",
            "element_id": element_id,
            "element_selector": f"a[href='{href}']",
            "label": f"Link '{text or element_id}' from {path} → {target}",
            "parent_url": path,
        })

    return elements


async def _enumerate_internal_links(page: Page, app_url: str) -> List[str]:
    """Return distinct internal hrefs discovered on the currently-loaded page."""
    hrefs = await page.eval_on_selector_all(
        "a[href]",
        "elements => elements.map(e => e.getAttribute('href'))",
    )
    targets: List[str] = []
    seen: Set[str] = set()
    for raw in hrefs:
        if not _is_internal(raw, app_url):
            continue
        path = _path_of(raw)
        if path in seen:
            continue
        seen.add(path)
        targets.append(path)
    return targets


async def crawl(app_url: str, max_pages: int = 50) -> List[Dict[str, Any]]:
    """Crawl the demo-app starting at app_url and return discovered elements.

    Performs a BFS with depth limit `MAX_CRAWL_DEPTH`. Seeds localStorage cart
    before visiting state-dependent routes so form elements appear. Skips
    external URLs and gracefully handles per-page timeouts.

    Args:
        app_url: Application base URL, e.g. "http://localhost:3001".
        max_pages: Hard cap on pages visited (defence against infinite crawls).

    Returns:
        Deduplicated list of element dicts per CLAUDE.md §4.6 schema.
    """
    discovered: List[Dict[str, Any]] = []
    seen_keys: Set[str] = set()
    visited: Set[str] = set()
    queue: List[tuple[str, int]] = [("/", 0)]

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(headless=True, channel=BROWSER_CHANNEL)
        context: BrowserContext = await browser.new_context()
        try:
            await _seed_cart_state(context, app_url)

            while queue and len(visited) < max_pages:
                path, depth = queue.pop(0)
                if path in visited:
                    continue
                visited.add(path)

                target_url = urljoin(app_url, path)
                page = await context.new_page()
                try:
                    await page.goto(target_url, timeout=PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
                    try:
                        await page.wait_for_load_state("networkidle", timeout=NETWORKIDLE_TIMEOUT_MS)
                    except PlaywrightTimeoutError:
                        # SPAs often never reach networkidle; proceed with discovery anyway.
                        logger.debug("networkidle timeout on %s; proceeding", path)

                    # Give React useEffects a moment to mount and re-render with
                    # localStorage-driven state. Crucial for /cart and /checkout
                    # which gate their form rendering on the cart being non-empty.
                    await page.wait_for_timeout(CLIENT_SETTLE_MS)

                    # After client-side redirects (e.g. `/` → `/products`), discover
                    # under the actual resting URL, not the requested one. Mark the
                    # original path as visited too so we don't re-crawl it.
                    actual_path = _path_of(page.url)
                    if actual_path != path:
                        logger.info("Redirect detected: %s → %s; using actual path", path, actual_path)
                        visited.add(actual_path)
                    page_elements = await _discover_on_page(page, actual_path)
                    for entry in page_elements:
                        key = _dedup_key(entry)
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        discovered.append(entry)

                    if depth < MAX_CRAWL_DEPTH:
                        for next_path in await _enumerate_internal_links(page, app_url):
                            if next_path not in visited:
                                queue.append((next_path, depth + 1))

                except PlaywrightTimeoutError:
                    logger.warning("Timed out loading %s; skipping", target_url)
                except Exception as exc:  # pragma: no cover — defensive
                    logger.warning("Error crawling %s: %s; skipping", target_url, exc)
                finally:
                    await page.close()
        finally:
            await context.close()
            await browser.close()

    logger.info("Crawl complete: %d pages, %d discovered elements", len(visited), len(discovered))
    return discovered
