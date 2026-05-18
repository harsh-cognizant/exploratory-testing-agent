"""
Module: agent/personas.py
Purpose: For a given page and node, generate persona-specific action lists using
         the Claude API. Loads prompt templates from agent/prompts/ and returns
         validated action dicts for explorer.py to execute.
Author: Team / Claude Code
Created: 2026-05-14
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic
from dotenv import load_dotenv

from agent.gap_analyser import safe_parse_json
from agent.offline_mocks import get_mock_actions

load_dotenv()


def _is_offline() -> bool:
    """Return True when the operator wants LLM steps mocked.

    Toggle: set LLM_OFFLINE=1 in .env. Useful when the corporate proxy
    blocks the LLM endpoint (openrouter.ai, api.anthropic.com, etc.) and
    the goal is to validate the rest of the pipeline.
    """
    return (os.getenv("LLM_OFFLINE") or "").strip().lower() in ("1", "true", "yes")

logger = logging.getLogger(__name__)

# Constants per CLAUDE.md §1 and §13 quick reference.
CLAUDE_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOKENS_PERSONA: int = 1000
MAX_ACTIONS_PER_PERSONA: int = 8

# The closed set of valid action types per CLAUDE.md §4.13.
VALID_ACTION_TYPES: set = {"fill", "click", "navigate", "submit", "clear"}

# Prompt template directory.
PROMPTS_DIR: Path = Path(__file__).parent / "prompts"

# Persona name → prompt file mapping.
PERSONA_PROMPT_FILES: Dict[str, str] = {
    "confused_user": "persona_confused.txt",
    "power_user": "persona_power.txt",
    "malicious_user": "persona_malicious.txt",
}


def _get_client() -> anthropic.Anthropic:
    """Construct an Anthropic-SDK-compatible client.

    Supports both direct Anthropic (ANTHROPIC_API_KEY → x-api-key) and proxy /
    OpenRouter (ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL → Bearer auth).
    """
    auth_token = (os.getenv("ANTHROPIC_AUTH_TOKEN") or "").strip()
    api_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    base_url = (os.getenv("ANTHROPIC_BASE_URL") or "").strip() or None

    if auth_token:
        return anthropic.Anthropic(auth_token=auth_token, base_url=base_url)
    if api_key and api_key != "your_key_here":
        return anthropic.Anthropic(api_key=api_key, base_url=base_url)
    raise RuntimeError(
        "No Anthropic credentials set. Set ANTHROPIC_API_KEY or "
        "ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL in .env."
    )


def _load_prompt_template(persona: str) -> str:
    """Load the prompt template for the given persona.

    Args:
        persona: One of 'confused_user', 'power_user', 'malicious_user'.

    Returns:
        Raw prompt template string with placeholders.

    Raises:
        FileNotFoundError: If the template file doesn't exist.
        ValueError: If persona name is unknown.
    """
    filename = PERSONA_PROMPT_FILES.get(persona)
    if not filename:
        raise ValueError(
            f"Unknown persona '{persona}'. "
            f"Valid personas: {list(PERSONA_PROMPT_FILES.keys())}"
        )
    path = PROMPTS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Prompt file missing: {path}. Restore it from CLAUDE.md §7."
        )
    return path.read_text(encoding="utf-8")


def _extract_page_context(node_attrs: Dict[str, Any]) -> Dict[str, str]:
    """Extract page description, form fields, and buttons from a node's graph attrs.

    Args:
        node_attrs: NetworkX node attribute dict.

    Returns:
        Dict with 'page_description', 'form_fields', 'buttons' strings.
    """
    url = node_attrs.get("url", "unknown")
    label = node_attrs.get("label", "Unknown page")
    node_type = node_attrs.get("type", "page")
    if hasattr(node_type, "value"):
        node_type = node_type.value
    selector = node_attrs.get("selector", "body")

    return {
        "page_description": f"{label} (type: {node_type})",
        "form_fields": selector if "input" in str(selector).lower() or "form" in str(node_type).lower() else "[]",
        "buttons": selector if "button" in str(node_type).lower() else "[]",
    }


def _build_page_context_from_graph(
    graph: Any,
    node_id: str,
    url: str,
) -> Dict[str, str]:
    """Build comprehensive page context from all nodes on the same URL.

    Scans the graph for all nodes sharing the same URL to collect form fields
    and buttons, giving Claude accurate selector information.

    Args:
        graph: NetworkX DiGraph with scored nodes.
        node_id: The specific node being explored.
        url: The URL of the page.

    Returns:
        Dict with 'page_description', 'form_fields', 'buttons' strings.
    """
    form_fields: List[str] = []
    buttons: List[str] = []
    page_label = url

    for nid, attrs in graph.nodes(data=True):
        if attrs.get("url") != url:
            continue
        element_type = attrs.get("element_type", "")
        selector = attrs.get("selector", "")
        label = attrs.get("label", "")

        if element_type == "page":
            page_label = label
        elif element_type == "input":
            form_fields.append(selector)
        elif element_type == "form":
            form_fields.append(selector)
        elif element_type == "button":
            buttons.append(selector)

    return {
        "page_description": page_label,
        "form_fields": json.dumps(form_fields) if form_fields else "[]",
        "buttons": json.dumps(buttons) if buttons else "[]",
    }


def _filter_valid_actions(
    actions: List[Dict[str, Any]],
    persona: str,
    page_url: str,
) -> List[Dict[str, Any]]:
    """Filter out actions with invalid action_types and cap at MAX_ACTIONS_PER_PERSONA.

    Per CLAUDE.md §4.13: drop any action whose action_type is not in the closed set,
    log each dropped action at DEBUG.

    Args:
        actions: Raw action dicts from Claude response.
        persona: Persona name for logging.
        page_url: Page URL for logging.

    Returns:
        Filtered and capped list of valid action dicts.
    """
    valid: List[Dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        action_type = action.get("action_type", "")
        if action_type not in VALID_ACTION_TYPES:
            logger.debug(
                "Dropped invalid action_type '%s' from persona=%s, page=%s",
                action_type, persona, page_url,
            )
            continue
        valid.append(action)

    # Cap at MAX_ACTIONS_PER_PERSONA per CLAUDE.md §4.13.
    if len(valid) > MAX_ACTIONS_PER_PERSONA:
        logger.debug(
            "Trimming %d actions to %d for persona=%s, page=%s",
            len(valid), MAX_ACTIONS_PER_PERSONA, persona, page_url,
        )
        valid = valid[:MAX_ACTIONS_PER_PERSONA]

    return valid


def generate_persona_actions(
    persona: str,
    page_url: str,
    graph: Any = None,
    node_id: str = "",
    node_attrs: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate persona-specific actions for a page using Claude.

    Args:
        persona: One of 'confused_user', 'power_user', 'malicious_user'.
        page_url: Full URL of the page being tested.
        graph: Optional NetworkX graph for rich context extraction.
        node_id: Node ID being explored.
        node_attrs: Node attributes if graph is not provided.

    Returns:
        List of action dicts, each with: action_type, target, value, reason.
        Returns empty list on failure (never crashes).
    """
    # Offline mode short-circuit — bypass the LLM entirely.
    if _is_offline():
        actions = get_mock_actions(persona, page_url)
        logger.info(
            "Persona '%s' [offline] returned %d mock actions for %s",
            persona, len(actions), page_url,
        )
        return _filter_valid_actions(actions, persona, page_url)

    try:
        template = _load_prompt_template(persona)
    except (ValueError, FileNotFoundError) as exc:
        logger.error("Failed to load persona template: %s", exc)
        return []

    # Build page context.
    if graph is not None and node_id:
        url_path = ""
        if node_id in graph.nodes:
            url_path = graph.nodes[node_id].get("url", "")
        context = _build_page_context_from_graph(graph, node_id, url_path)
    elif node_attrs:
        context = _extract_page_context(node_attrs)
    else:
        context = {
            "page_description": f"Page at {page_url}",
            "form_fields": "[]",
            "buttons": "[]",
        }

    prompt = template.format(
        page_url=page_url,
        page_description=context["page_description"],
        form_fields=context["form_fields"],
        buttons=context["buttons"],
    )

    try:
        client = _get_client()
    except RuntimeError as exc:
        logger.error("Cannot generate persona actions: %s", exc)
        return []

    # Call Claude with retry-once policy for JSON parse failures.
    strict_suffix = "\n\nReturn ONLY valid JSON. No markdown, no preamble, no trailing text."
    for attempt in (1, 2):
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS_PERSONA,
                messages=[{
                    "role": "user",
                    "content": prompt if attempt == 1 else prompt + strict_suffix,
                }],
            )
            text = ""
            for block in message.content:
                if getattr(block, "type", None) == "text":
                    text = block.text
                    break

            parsed = safe_parse_json(text)
            if isinstance(parsed, list):
                actions = _filter_valid_actions(parsed, persona, page_url)
                logger.info(
                    "Persona '%s' generated %d valid actions for %s",
                    persona, len(actions), page_url,
                )
                return actions

            logger.warning(
                "Persona '%s' attempt %d: JSON parse failed. Head: %r",
                persona, attempt, text[:200],
            )

        except anthropic.AnthropicError as exc:
            logger.error(
                "Claude API error for persona '%s' attempt %d: %s",
                persona, attempt, exc,
            )
            # Do not return [] here, allow it to fall through or return fallback directly.
            break

    # No fallback action — a generic `click button` selector can match anything
    # on the page (or nothing), produces noisy false-positive findings on every
    # node, and obscures the real failure mode (API unreachable or JSON parse
    # failed). Return [] and let brain.py's `if not actions: continue` skip
    # the page-persona pair while leaving the page counted as visited.
    logger.warning(
        "Persona '%s': no valid actions returned for %s; skipping this pair",
        persona, page_url,
    )
    return []
