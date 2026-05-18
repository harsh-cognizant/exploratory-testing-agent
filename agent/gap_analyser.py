"""
Module: agent/gap_analyser.py
Purpose: Use the Claude API to identify which uncovered graph nodes represent
         meaningful test gaps. Annotates the NetworkX graph in-place with
         `gap_reason` strings on identified gap nodes.
Created: 2026-05-14
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import anthropic
from dotenv import load_dotenv
import networkx as nx

load_dotenv()

logger = logging.getLogger(__name__)

# Constants per CLAUDE.md §1 hard constraints and §13 quick reference.
CLAUDE_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOKENS_GAP_ANALYSIS: int = 2000
MAX_NODES_PER_CALL: int = 30
DEFAULT_MAX_GAPS_PER_BATCH: int = 12

PROMPT_PATH: Path = Path(__file__).parent / "prompts" / "gap_analysis.txt"
STRICT_RETRY_SUFFIX: str = (
    "\n\nReturn ONLY valid JSON. No markdown, no preamble, no trailing text."
)


def safe_parse_json(text: str) -> Optional[Union[List, Dict]]:
    """Parse JSON from an LLM response, handling markdown fences and stray text.

    Strips triple-backtick fences (with or without 'json' label) before parsing.
    Falls back to regex extraction of the first JSON array/object if direct
    parse fails. Returns None when no valid JSON can be recovered — caller
    decides whether to retry.

    Args:
        text: Raw string output from a Claude API response.

    Returns:
        Parsed Python list/dict if JSON found, else None.
    """
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None


def _get_client() -> anthropic.Anthropic:
    """Construct an Anthropic-SDK-compatible client.

    Supports two auth modes:
      * Anthropic direct: ANTHROPIC_API_KEY (sent as `x-api-key` header).
      * OpenRouter / proxy: ANTHROPIC_AUTH_TOKEN (sent as `Authorization: Bearer`).
        Set ANTHROPIC_BASE_URL alongside to point at the proxy
        (e.g. https://openrouter.ai/api for OpenRouter's Anthropic-compatible
        endpoint at /v1/messages).

    Raises:
        RuntimeError: if neither credential is configured.
    """
    auth_token = (os.getenv("ANTHROPIC_AUTH_TOKEN") or "").strip()
    api_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    base_url = (os.getenv("ANTHROPIC_BASE_URL") or "").strip() or None

    if auth_token:
        return anthropic.Anthropic(auth_token=auth_token, base_url=base_url)
    if api_key and api_key != "your_key_here":
        return anthropic.Anthropic(api_key=api_key, base_url=base_url)
    raise RuntimeError(
        "No Anthropic credentials set. Set ANTHROPIC_API_KEY (direct) or "
        "ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL (proxy / OpenRouter) in .env."
    )


def _load_prompt_template() -> str:
    """Load and return the gap_analysis prompt template as a raw string."""
    if not PROMPT_PATH.is_file():
        raise FileNotFoundError(
            f"Prompt file missing: {PROMPT_PATH}. Restore it from CLAUDE.md §7."
        )
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_routes_payload(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reduce node dicts to the fields the prompt needs (id, url, type, label).

    Keeps the payload compact to stay well within the model's input budget when
    the graph has 30+ nodes.
    """
    return [
        {
            "node_id": n["id"],
            "url": n["url"],
            "type": n["type"],
            "label": n["label"],
        }
        for n in nodes
    ]


def _call_claude(client: anthropic.Anthropic, prompt: str) -> str:
    """One Claude call with the configured model and max_tokens. Returns the
    text content of the response (first text block)."""
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS_GAP_ANALYSIS,
        messages=[{"role": "user", "content": prompt}],
    )
    for block in message.content:
        if getattr(block, "type", None) == "text":
            return block.text
    return ""


def _analyse_batch(
    client: anthropic.Anthropic,
    template: str,
    nodes_batch: List[Dict[str, Any]],
    covered_node_ids: List[str],
    max_gaps: int,
) -> List[Dict[str, Any]]:
    """Run one analysis call for a batch of ≤30 nodes with retry-once policy.

    Per CLAUDE.md §4.12: on first JSON parse failure, retry once with a stricter
    suffix appended. On second failure, log to COMMANDLOG (via logger.error) and
    return [] — never crash the scan.

    Args:
        client: Anthropic SDK client.
        template: Prompt template with {routes_json}/{covered_nodes_json}/{max_gaps}.
        nodes_batch: Up to MAX_NODES_PER_CALL node dicts.
        covered_node_ids: Subset of node ids already covered by existing tests.
        max_gaps: Cap on gaps the model should return for this batch.

    Returns:
        List of gap dicts: [{node_id, page, gap_reason, risk_factors}, ...].
    """
    routes_payload = _build_routes_payload(nodes_batch)
    prompt = template.format(
        routes_json=json.dumps(routes_payload, indent=2),
        covered_nodes_json=json.dumps(covered_node_ids, indent=2),
        max_gaps=max_gaps,
    )

    for attempt in (1, 2):
        try:
            text = _call_claude(client, prompt if attempt == 1 else prompt + STRICT_RETRY_SUFFIX)
        except anthropic.AnthropicError as exc:
            logger.error("Claude API error on gap-analysis attempt %d: %s", attempt, exc)
            return []

        parsed = safe_parse_json(text)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict) and "node_id" in item]

        logger.warning(
            "gap_analyser: JSON parse failed on attempt %d. Raw response head: %r",
            attempt,
            text[:200],
        )

    logger.error("gap_analyser: returning empty gap list after 2 failed parses")
    return []


def _is_offline() -> bool:
    """Return True when LLM_OFFLINE=1 in env (see agent/personas.py for context)."""
    return (os.getenv("LLM_OFFLINE") or "").strip().lower() in ("1", "true", "yes")


def analyse_gaps(
    graph: nx.DiGraph,
    max_gaps_total: int = DEFAULT_MAX_GAPS_PER_BATCH * 4,
) -> List[Dict[str, Any]]:
    """Identify meaningful coverage gaps in the graph using Claude.

    Only uncovered nodes are sent to Claude. If there are more than
    MAX_NODES_PER_CALL uncovered nodes, they are batched per CLAUDE.md §4.12.

    Side effect: annotates each gap node in `graph` with a `gap_reason` string.

    Args:
        graph: NetworkX DiGraph produced by graph_builder.build_coverage_graph.
        max_gaps_total: Soft cap on total gaps to surface across all batches.

    Returns:
        List of gap dicts, each {node_id, page, gap_reason, risk_factors}.
    """
    uncovered: List[Dict[str, Any]] = []
    covered_ids: List[str] = []
    for node_id, attrs in graph.nodes(data=True):
        node_payload = {
            "id": attrs["id"],
            "url": attrs["url"],
            "type": attrs["type"].value if hasattr(attrs["type"], "value") else attrs["type"],
            "label": attrs["label"],
        }
        if attrs.get("covered"):
            covered_ids.append(node_id)
        else:
            uncovered.append(node_payload)

    if not uncovered:
        logger.info("gap_analyser: no uncovered nodes; skipping Claude call")
        return []

    # Offline mode: mark every uncovered node as a heuristic gap. No LLM call.
    if _is_offline():
        gaps: List[Dict[str, Any]] = []
        for node in uncovered[:max_gaps_total]:
            reason = (
                f"Uncovered {node['type']} surface at {node['url']} "
                f"({node['label']}) — heuristic gap (offline mode)."
            )
            gaps.append({
                "node_id": node["id"],
                "page": node["url"],
                "gap_reason": reason,
                "risk_factors": [],
            })
            if node["id"] in graph.nodes:
                graph.nodes[node["id"]]["gap_reason"] = reason
        logger.info("gap_analyser [offline]: returning %d heuristic gaps", len(gaps))
        return gaps

    client = _get_client()
    template = _load_prompt_template()

    # Batch in groups of MAX_NODES_PER_CALL per CLAUDE.md §4.12 batching rule.
    batches = [
        uncovered[i:i + MAX_NODES_PER_CALL]
        for i in range(0, len(uncovered), MAX_NODES_PER_CALL)
    ]

    all_gaps: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    per_batch_cap = max(1, max_gaps_total // max(1, len(batches)))

    for idx, batch in enumerate(batches, start=1):
        logger.info(
            "gap_analyser: batch %d/%d (%d nodes, asking for up to %d gaps)",
            idx, len(batches), len(batch), per_batch_cap,
        )
        gaps = _analyse_batch(client, template, batch, covered_ids, per_batch_cap)
        for gap in gaps:
            nid = gap.get("node_id")
            if not nid or nid in seen_ids:
                continue
            seen_ids.add(nid)
            all_gaps.append(gap)
            if nid in graph.nodes:
                graph.nodes[nid]["gap_reason"] = gap.get("gap_reason")

    logger.info("gap_analyser: returning %d unique gaps across %d batches", len(all_gaps), len(batches))
    return all_gaps
