"""
Module: api/routes/scan_status.py
Purpose: GET /scan/{scan_id}/status — returns ScanStatusResponse from
         SCAN_STATE in agent/brain.py.
         Phase 1 stub: returns a 404 because no scan state exists yet.
Created: 2026-05-13
"""

from fastapi import APIRouter, HTTPException

from api.models import ScanStatusResponse

router = APIRouter()


@router.get("/scan/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str) -> ScanStatusResponse:
    """Return current progress for a scan identified by scan_id.

    Phase 1 stub — SCAN_STATE is not yet populated by brain.py, so this
    always 404s. The endpoint shape is defined now so the dashboard can
    wire up the polling loop against the contract.

    Args:
        scan_id: The scan identifier returned by POST /scan.

    Returns:
        ScanStatusResponse with progress metrics.

    Raises:
        HTTPException(404): always raised in Phase 1.
    """
    raise HTTPException(status_code=404, detail=f"scan_id '{scan_id}' not found")
