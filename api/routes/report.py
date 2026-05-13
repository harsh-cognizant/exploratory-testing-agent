"""
Module: api/routes/report.py
Purpose: GET /report — returns the final report from a completed scan.
         Phase 1 stub: always 404s with "Scan not completed yet"; report
         compilation arrives in Phase 6 via engine/report_builder.py.
Created: 2026-05-13
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from api.models import ReportResponse

router = APIRouter()


@router.get("/report", response_model=ReportResponse)
async def get_report(scan_id: Optional[str] = None) -> ReportResponse:
    """Return the final report (summary + findings + generated tests) for a scan.

    Phase 1 stub — no report has ever been compiled, so always 404 per
    CLAUDE.md §6.

    Args:
        scan_id: Optional scan identifier. Omit to read the latest scan.

    Returns:
        ReportResponse with summary, findings, and generated tests.

    Raises:
        HTTPException(404): until Phase 6 wires report_builder.py into orchestration.
    """
    raise HTTPException(status_code=404, detail="Scan not completed yet")
