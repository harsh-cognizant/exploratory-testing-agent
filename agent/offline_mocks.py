"""
Module: agent/offline_mocks.py
Purpose: Canned persona action lists used when LLM_OFFLINE=1 in .env.
         Replaces live Claude calls so the rest of the pipeline (crawler,
         graph, risk, explorer, anomaly detector, report) can be validated
         end-to-end in air-gapped / proxy-blocked environments.

         Each (persona, path) entry is deliberately crafted to either
         trigger one of the planted demo-app bugs (see CLAUDE.md §10) or
         exercise a meaningful surface area the live LLM would target.
         Reason strings include keywords (`empty`, `invalid`, `negative`,
         `injection`) that engine.anomaly_detector.check_form_validation
         pattern-matches to flag form_accepts_invalid_data anomalies.
Created: 2026-05-18
"""

from typing import Any, Dict, List
from urllib.parse import urlparse

# Canned actions keyed by (persona, normalised_path). Paths are extracted from
# the full page_url with urlparse so that http://localhost:3001/login resolves
# to /login. Unknown (persona, path) pairs return [] — brain.py then skips
# that pair, which counts as 'attempted but no actions' instead of a fake
# explored success.
_MOCK_ACTIONS: Dict[tuple, List[Dict[str, Any]]] = {
    # ── confused_user ────────────────────────────────────────────────
    ("confused_user", "/login"): [
        {"action_type": "fill", "target": "[data-testid='email-input']",
         "value": "confused@example.com", "reason": "types email but skips the password field"},
        {"action_type": "click", "target": "[data-testid='login-button']",
         "value": None, "reason": "submits the form with the password field still empty (BUG-001)"},
    ],
    ("confused_user", "/cart"): [
        {"action_type": "fill", "target": "[data-testid='quantity-input-1']",
         "value": "abc", "reason": "types non-numeric text into a quantity field by mistake (BUG-006 — invalid input)"},
    ],
    ("confused_user", "/checkout"): [
        {"action_type": "fill", "target": "[data-testid='fullname-input']", "value": "Alice",
         "reason": "fills first field"},
        {"action_type": "click", "target": "[data-testid='place-order-btn']",
         "value": None, "reason": "clicks Place Order with most fields still empty / missing"},
    ],
    ("confused_user", "/products"): [
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-1']",
         "value": None, "reason": "adds the first product"},
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-2']",
         "value": None, "reason": "adds a second product to confirm cart works"},
    ],
    # ── power_user ───────────────────────────────────────────────────
    ("power_user", "/products"): [
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-1']",
         "value": None, "reason": "rapid click #1 on Add-to-Cart"},
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-1']",
         "value": None, "reason": "rapid click #2"},
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-1']",
         "value": None, "reason": "rapid click #3"},
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-1']",
         "value": None, "reason": "rapid click #4"},
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-1']",
         "value": None, "reason": "rapid click #5"},
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-1']",
         "value": None, "reason": "rapid click #6 — quantity now >5 (BUG-002 should manifest as NaN)"},
    ],
    ("power_user", "/cart"): [
        {"action_type": "fill", "target": "[data-testid='quantity-input-1']",
         "value": "99", "reason": "power-user sets quantity to 99 to exercise the cart-count code path"},
        {"action_type": "click", "target": "[data-testid='proceed-to-checkout-btn']",
         "value": None, "reason": "advances to checkout"},
    ],
    ("power_user", "/login"): [
        {"action_type": "fill", "target": "[data-testid='email-input']",
         "value": "power@user.test", "reason": "types via autofill format"},
        {"action_type": "fill", "target": "[data-testid='password-input']",
         "value": "Hunter2!Hunter2!Hunter2!", "reason": "long autofilled password"},
        {"action_type": "submit", "target": "[data-testid='password-input']",
         "value": None, "reason": "submits with Enter rather than clicking"},
    ],
    # ── malicious_user ───────────────────────────────────────────────
    ("malicious_user", "/cart"): [
        {"action_type": "fill", "target": "[data-testid='quantity-input-1']",
         "value": "-5", "reason": "negative quantity to bypass cart validation (BUG-003)"},
    ],
    ("malicious_user", "/checkout"): [
        # BUG-005: this URL is reachable without /login first. Just being
        # here in a fresh session is the finding; we also exercise BUG-004.
        {"action_type": "fill", "target": "[data-testid='fullname-input']",
         "value": "<script>alert(1)</script>", "reason": "XSS injection in name field"},
        {"action_type": "fill", "target": "[data-testid='email-input']",
         "value": "x@y.z", "reason": "minimal email"},
        {"action_type": "fill", "target": "[data-testid='address-input']",
         "value": "1 Main", "reason": "minimal address"},
        {"action_type": "fill", "target": "[data-testid='city-input']",
         "value": "X", "reason": "minimal city"},
        {"action_type": "fill", "target": "[data-testid='state-input']",
         "value": "XX", "reason": "minimal state"},
        {"action_type": "fill", "target": "[data-testid='zipcode-input']",
         "value": "00000", "reason": "minimal zip"},
        {"action_type": "fill", "target": "[data-testid='card-number-input']",
         "value": "abcdefgh", "reason": "invalid (non-numeric) card number to test card-format validation (BUG-004)"},
        {"action_type": "fill", "target": "[data-testid='expiry-input']",
         "value": "13/99", "reason": "invalid expiry month"},
        {"action_type": "fill", "target": "[data-testid='cvv-input']",
         "value": "1", "reason": "invalid (too short) CVV"},
        {"action_type": "click", "target": "[data-testid='place-order-btn']",
         "value": None, "reason": "submits order with invalid card payload to confirm validation bypass"},
    ],
    ("malicious_user", "/login"): [
        {"action_type": "fill", "target": "[data-testid='email-input']",
         "value": "' OR '1'='1", "reason": "SQL injection payload in email field"},
        {"action_type": "fill", "target": "[data-testid='password-input']",
         "value": "<script>alert(1)</script>", "reason": "XSS payload in password field"},
        {"action_type": "click", "target": "[data-testid='login-button']",
         "value": None, "reason": "submits injection payloads to test input validation"},
    ],
    ("malicious_user", "/products"): [
        {"action_type": "click", "target": "[data-testid='add-to-cart-btn-3']",
         "value": None, "reason": "stages cart state to attack downstream pages"},
    ],
}


def get_mock_actions(persona: str, page_url: str) -> List[Dict[str, Any]]:
    """Return canned persona actions for the given (persona, page_url).

    Args:
        persona: One of 'confused_user', 'power_user', 'malicious_user'.
        page_url: Full URL of the page, e.g. 'http://localhost:3001/login'.

    Returns:
        List of action dicts compatible with the live persona output. Empty
        list when no mock is defined — caller treats this the same as a
        failed LLM call (skip the page-persona pair).
    """
    path = urlparse(page_url).path or "/"
    return list(_MOCK_ACTIONS.get((persona, path), []))
