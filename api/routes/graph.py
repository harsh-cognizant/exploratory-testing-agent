"""
Module: api/routes/graph.py
Purpose: GET /graph — returns the coverage intelligence graph for a scan.
         Phase 1 stub: returns an empty graph; populated by graph_builder
         starting in Phase 2.
Created: 2026-05-13
"""

from typing import Optional

from fastapi import APIRouter

from api.models import GraphResponse, GraphStats

router = APIRouter()


@router.get("/graph", response_model=GraphResponse)
async def get_graph(scan_id: Optional[str] = None) -> GraphResponse:
    """Return the coverage graph for a scan (latest scan if scan_id omitted).

    Phase 1 stub — returns an empty graph with zero stats. Real data lands
    in Phase 2 when graph_builder.py is wired into the orchestration flow.

    Args:
        scan_id: Optional scan identifier. Omit to read the latest scan.

    Returns:
        GraphResponse with empty nodes/edges and zeroed stats.
    """
    return GraphResponse(
        nodes=[],
        edges=[],
        stats=GraphStats(total_nodes=0, covered=0, gaps=0, coverage_percent=0.0),
    )
