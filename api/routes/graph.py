"""
Module: api/routes/graph.py
Purpose: GET /graph — returns the coverage intelligence graph for a scan,
         serialised from the NetworkX graph held in SCAN_STATE.
Created: 2026-05-13
Updated: 2026-05-14 (Phase 2 — wired to SCAN_STATE and graph_builder)
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from agent.brain import get_latest_completed_scan_id, get_scan_state
from api.models import GraphResponse, GraphStats
from engine.graph_builder import graph_to_response_dict

router = APIRouter()


@router.get("/graph", response_model=GraphResponse)
async def get_graph(scan_id: Optional[str] = None) -> GraphResponse:
    """Return the coverage graph for a scan (latest scan if scan_id omitted).

    Args:
        scan_id: Optional scan identifier. Omit to read the latest completed scan.

    Returns:
        GraphResponse with nodes, edges, and summary stats. Empty response if
        no scan has produced a graph yet.

    Raises:
        HTTPException(404): if a specific scan_id is given but unknown.
    """
    if scan_id is None:
        scan_id = get_latest_completed_scan_id()
        if scan_id is None:
            # No completed scan yet — return an empty contract-shaped response.
            return GraphResponse(
                nodes=[],
                edges=[],
                stats=GraphStats(total_nodes=0, covered=0, gaps=0, coverage_percent=0.0),
            )

    state = get_scan_state(scan_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"scan_id '{scan_id}' not found")

    graph = state.get("graph")
    if graph is None:
        # Scan exists but hasn't built the graph yet.
        return GraphResponse(
            nodes=[],
            edges=[],
            stats=GraphStats(total_nodes=0, covered=0, gaps=0, coverage_percent=0.0),
        )

    payload = graph_to_response_dict(graph)
    return GraphResponse(**payload)
