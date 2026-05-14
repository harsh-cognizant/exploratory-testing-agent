"""
Module: engine/graph_builder.py
Purpose: Convert crawler output (list[dict]) into a NetworkX DiGraph with the
         coverage overlay applied. Node attributes match the GraphNode schema
         in api/models.py.
Created: 2026-05-14
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import networkx as nx

from api.models import NodeType, RiskBand

logger = logging.getLogger(__name__)

# Constants
DEFAULT_RISK_SCORE: float = 0.5
DEFAULT_RISK_BAND: RiskBand = RiskBand.MEDIUM

# Map crawler element_type → NodeType enum. inputs and links don't have direct
# enum members; we represent them via the closest semantic match:
#   - input → FORM  (input is part of a form's testable surface)
#   - link  → STATE (navigation state element; the edge it implies is more
#                    important than the node itself)
ELEMENT_TYPE_TO_NODE_TYPE: Dict[str, NodeType] = {
    "page": NodeType.PAGE,
    "form": NodeType.FORM,
    "button": NodeType.BUTTON,
    "input": NodeType.FORM,
    "link": NodeType.STATE,
}


def _node_id(url: str, element_type: str, element_id: str) -> str:
    """Build a deterministic node id from a discovered element.

    Format: `node_{url_slug}_{element_id}` for page-level elements,
            `node_{element_id}` for the page-type entry itself.
    Per CLAUDE.md §4.7 + §8 anti-hallucination rules.
    """
    slug = url.strip("/").replace("/", "_") or "home"
    if element_type == "page":
        return f"node_{slug}"
    return f"node_{slug}_{element_id}"


def _load_coverage(coverage_path: str) -> Dict[str, Any]:
    """Load existing_tests_mock.json and return parsed dict. Returns empty
    fallback (treat all nodes as uncovered) if the file is missing or invalid.
    """
    path = Path(coverage_path)
    if not path.is_file():
        logger.warning("Coverage file not found at %s; treating all nodes as uncovered", path)
        return {"covered_urls": [], "covered_elements": []}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read coverage file %s (%s); treating all nodes as uncovered", path, exc)
        return {"covered_urls": [], "covered_elements": []}
    return data


def build_coverage_graph(
    elements: List[Dict[str, Any]],
    coverage_path: str,
) -> nx.DiGraph:
    """Build a NetworkX directed graph from crawler output with coverage overlay.

    Each crawler element becomes a node. Edges:
      - Page → element: every form/button/input on a page gets an edge from
        the page node to itself (so the graph reflects element-of relationships).
      - Page → page: link elements with parent_url create a navigation edge
        from the source page node to the target page node.

    Args:
        elements: Crawler output list per CLAUDE.md §4.6.
        coverage_path: Path to existing_tests_mock.json.

    Returns:
        nx.DiGraph with node attributes matching the GraphNode Pydantic schema.
    """
    coverage = _load_coverage(coverage_path)
    covered_urls = set(coverage.get("covered_urls") or [])
    covered_elements = set(coverage.get("covered_elements") or [])

    graph = nx.DiGraph()

    # First pass: create all nodes.
    # `link` elements never get their own node — they only contribute a
    # navigation edge in the second pass below. Keeping them out as nodes
    # avoids visually duplicating each anchor with the page it targets
    # (which already has a PAGE node from the crawler).
    for entry in elements:
        node_type_str = entry["element_type"]
        if node_type_str == "link":
            continue
        node_type = ELEMENT_TYPE_TO_NODE_TYPE.get(node_type_str, NodeType.STATE)
        nid = _node_id(entry["url"], node_type_str, entry["element_id"])
        is_covered = (
            entry["url"] in covered_urls
            or entry["element_id"] in covered_elements
        )

        # If a node was already created (e.g. a link earlier inserted a STATE
        # placeholder for /products and the BFS then visited /products as a
        # page), upgrade the type to PAGE so the canonical entry wins.
        if nid in graph.nodes:
            existing_type = graph.nodes[nid].get("type")
            if node_type == NodeType.PAGE or existing_type != NodeType.PAGE:
                graph.nodes[nid]["type"] = node_type
                graph.nodes[nid]["label"] = entry["label"]
                graph.nodes[nid]["selector"] = entry["element_selector"]
            graph.nodes[nid]["covered"] = graph.nodes[nid].get("covered") or is_covered
            continue

        graph.add_node(
            nid,
            id=nid,
            label=entry["label"],
            url=entry["url"],
            type=node_type,
            covered=is_covered,
            risk_score=DEFAULT_RISK_SCORE,
            risk_band=DEFAULT_RISK_BAND,
            last_changed=None,
            defect_count_historical=0,
            business_criticality="medium",
            gap_reason=None,
            has_memory=False,
            selector=entry["element_selector"],
            element_type=node_type_str,
        )

    # Second pass: edges.
    for entry in elements:
        node_type_str = entry["element_type"]
        nid = _node_id(entry["url"], node_type_str, entry["element_id"])
        parent_url = entry.get("parent_url")

        if node_type_str == "link" and parent_url:
            # Navigation edge: from the source page node to the target page node.
            source_nid = _node_id(parent_url, "page", "_unused")
            target_nid = _node_id(entry["url"], "page", "_unused")
            if source_nid in graph.nodes and target_nid in graph.nodes:
                graph.add_edge(
                    source_nid,
                    target_nid,
                    type="navigation",
                    transition=entry["element_id"],
                )
        elif parent_url and node_type_str != "page":
            # Element-of-page edge: page node → element node.
            page_nid = _node_id(parent_url, "page", "_unused")
            if page_nid in graph.nodes:
                graph.add_edge(
                    page_nid,
                    nid,
                    type="contains",
                    transition=None,
                )

    logger.info(
        "Graph built: %d nodes, %d edges, %d covered, %d uncovered",
        graph.number_of_nodes(),
        graph.number_of_edges(),
        sum(1 for _, attrs in graph.nodes(data=True) if attrs.get("covered")),
        sum(1 for _, attrs in graph.nodes(data=True) if not attrs.get("covered")),
    )
    return graph


def graph_to_response_dict(graph: nx.DiGraph) -> Dict[str, Any]:
    """Serialise a NetworkX graph into the shape expected by GraphResponse.

    Pulls node attributes into the GraphNode schema fields and emits edges
    as `{source, target, type, transition}` dicts. Computes stats inline.

    Args:
        graph: NetworkX DiGraph produced by `build_coverage_graph`.

    Returns:
        Dict matching GraphResponse: {"nodes": [...], "edges": [...], "stats": {...}}.
    """
    nodes: List[Dict[str, Any]] = []
    for node_id, attrs in graph.nodes(data=True):
        nodes.append({
            "id": attrs["id"],
            "label": attrs["label"],
            "url": attrs["url"],
            "type": attrs["type"].value if hasattr(attrs["type"], "value") else attrs["type"],
            "covered": bool(attrs["covered"]),
            "risk_score": float(attrs["risk_score"]),
            "risk_band": (
                attrs["risk_band"].value
                if hasattr(attrs["risk_band"], "value")
                else attrs["risk_band"]
            ),
            "last_changed": attrs.get("last_changed"),
            "defect_count_historical": attrs.get("defect_count_historical", 0),
            "business_criticality": attrs.get("business_criticality", "medium"),
            "gap_reason": attrs.get("gap_reason"),
            "has_memory": bool(attrs.get("has_memory", False)),
        })

    edges: List[Dict[str, Any]] = []
    for source, target, attrs in graph.edges(data=True):
        edges.append({
            "source": source,
            "target": target,
            "type": attrs.get("type", "contains"),
            "transition": attrs.get("transition"),
        })

    total = graph.number_of_nodes()
    covered = sum(1 for _, attrs in graph.nodes(data=True) if attrs.get("covered"))
    gaps = total - covered
    coverage_percent = round((covered / total) * 100, 1) if total else 0.0

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": total,
            "covered": covered,
            "gaps": gaps,
            "coverage_percent": coverage_percent,
        },
    }
