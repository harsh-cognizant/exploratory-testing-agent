"""
Module: api/routes/queue.py
Purpose: GET /queue — returns the risk-prioritised exploration queue. Reads the
         scored NetworkX graph from SCAN_STATE and ranks via engine.risk_scorer.
Created: 2026-05-13
Updated: 2026-05-14 (Phase 3 — wired to risk_scorer.build_queue)
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from agent.brain import get_latest_completed_scan_id, get_scan_state
from api.models import QueueResponse
from engine.risk_scorer import build_queue

router = APIRouter()


@router.get("/queue", response_model=QueueResponse)
async def get_queue(
    scan_id: Optional[str] = None,
    risk_band: Optional[str] = None,
) -> QueueResponse:
    """Return the ranked exploration queue for a scan.

    Reads the scored graph from SCAN_STATE and produces QueueItem entries
    ordered by `risk_score` descending. Returns an empty queue if no scan
    has completed yet.

    Args:
        scan_id: Optional scan identifier. Omit to read the latest scan.
        risk_band: Optional filter ("critical" | "high" | "medium" | "low").

    Returns:
        QueueResponse with `queue` ranked by risk_score descending.

    Raises:
        HTTPException(404): if a specific scan_id is given but unknown.
    """
    if scan_id is None:
        scan_id = get_latest_completed_scan_id()
        if scan_id is None:
            return QueueResponse(queue=[])

    state = get_scan_state(scan_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"scan_id '{scan_id}' not found")

    graph = state.get("graph")
    if graph is None:
        return QueueResponse(queue=[])

    items = build_queue(graph, risk_band=risk_band)
    return QueueResponse(queue=items)
