"""
Module: api/routes/scan.py
Purpose: POST /scan — starts an async background scan task in agent/brain.py.
         Phase 1 stub: declares the endpoint and returns a placeholder
         ScanResponse with status=STARTED. Full orchestration arrives in Phase 4.
Created: 2026-05-13
"""

from datetime import datetime

from fastapi import APIRouter

from api.models import ScanRequest, ScanResponse, ScanStatus

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest) -> ScanResponse:
    """Start a new scan against the target application.

    Phase 1 stub — does not yet trigger brain.py orchestration. Returns a
    well-formed ScanResponse so the dashboard can wire up against the contract.

    Args:
        request: ScanRequest with app_url, existing_tests_path, max_nodes, personas.

    Returns:
        ScanResponse with a generated scan_id, status=STARTED, and
        the default estimated_duration_seconds.
    """
    scan_id = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    return ScanResponse(scan_id=scan_id, status=ScanStatus.STARTED)
