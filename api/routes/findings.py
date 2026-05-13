"""
Module: api/routes/findings.py
Purpose: GET /findings — returns findings discovered during a scan.
         Phase 1 stub: returns an empty list; populated by explorer.py
         starting in Phase 4.
Created: 2026-05-13
"""

from typing import Optional

from fastapi import APIRouter

from api.models import FindingsResponse, FindingsSummary

router = APIRouter()


@router.get("/findings", response_model=FindingsResponse)
async def get_findings(
    scan_id: Optional[str] = None,
    severity: Optional[str] = None,
) -> FindingsResponse:
    """Return all findings from a scan, optionally filtered by severity.

    Phase 1 stub — empty list. Real findings appear in Phase 4 once
    explorer.py executes persona action lists against the demo app.

    Args:
        scan_id: Optional scan identifier. Omit to read the latest scan.
        severity: Optional filter ("critical" | "high" | "medium" | "low").

    Returns:
        FindingsResponse with empty findings and zeroed summary counts.
    """
    return FindingsResponse(
        findings=[],
        summary=FindingsSummary(total=0, critical=0, high=0, medium=0, low=0),
    )
