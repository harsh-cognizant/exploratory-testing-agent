"""
Module: api/routes/queue.py
Purpose: GET /queue — returns the risk-prioritised exploration queue.
         Phase 1 stub: returns an empty queue; populated by risk_scorer
         starting in Phase 3.
Created: 2026-05-13
"""

from typing import Optional

from fastapi import APIRouter

from api.models import QueueResponse

router = APIRouter()


@router.get("/queue", response_model=QueueResponse)
async def get_queue(
    scan_id: Optional[str] = None,
    risk_band: Optional[str] = None,
) -> QueueResponse:
    """Return the ranked exploration queue for a scan.

    Phase 1 stub — empty queue. Real data lands in Phase 3 when
    risk_scorer.py is wired into the orchestration flow.

    Args:
        scan_id: Optional scan identifier. Omit to read the latest scan.
        risk_band: Optional filter ("critical" | "high" | "medium" | "low").

    Returns:
        QueueResponse with an empty queue list.
    """
    return QueueResponse(queue=[])
