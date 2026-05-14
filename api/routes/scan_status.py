"""
Module: api/routes/scan_status.py
Purpose: GET /scan/{scan_id}/status — reads SCAN_STATE in agent.brain and
         returns the current progress snapshot.
Created: 2026-05-13
Updated: 2026-05-14 (Phase 2 — wired to SCAN_STATE)
"""

from fastapi import APIRouter, HTTPException

from agent.brain import get_scan_state
from api.models import ScanStatusResponse, ScanStatus

router = APIRouter()


@router.get("/scan/{scan_id}/status", response_model=ScanStatusResponse)
async def get_status(scan_id: str) -> ScanStatusResponse:
    """Return current progress for a scan identified by scan_id.

    Args:
        scan_id: The scan identifier returned by POST /scan.

    Returns:
        ScanStatusResponse populated from SCAN_STATE.

    Raises:
        HTTPException(404): if scan_id is unknown.
    """
    state = get_scan_state(scan_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"scan_id '{scan_id}' not found")
    status = state.get("status", ScanStatus.STARTED)
    return ScanStatusResponse(
        scan_id=scan_id,
        status=status if isinstance(status, ScanStatus) else ScanStatus(status),
        progress_percent=int(state.get("progress_percent", 0)),
        nodes_explored=int(state.get("nodes_explored", 0)),
        nodes_total=int(state.get("nodes_total", 0)),
        findings_so_far=int(state.get("findings_so_far", 0)),
        current_node=state.get("current_node"),
        current_persona=state.get("current_persona"),
    )
