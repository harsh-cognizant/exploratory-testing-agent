"""
Module: api/routes/findings.py
Purpose: GET /findings — returns findings discovered during a scan.
         Reads from SCAN_STATE in agent.brain; supports optional severity filter.
Created: 2026-05-13
Updated: 2026-05-14 (Phase 4 — wired to real scan findings)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from agent.brain import get_latest_completed_scan_id, get_scan_state
from api.models import (
    Finding,
    FindingsResponse,
    FindingsSummary,
    SeverityLevel,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/findings", response_model=FindingsResponse)
async def get_findings(
    scan_id: Optional[str] = None,
    severity: Optional[str] = None,
) -> FindingsResponse:
    """Return all findings from a scan, optionally filtered by severity.

    Args:
        scan_id: Optional scan identifier. Omit to read the latest scan.
        severity: Optional filter ("critical" | "high" | "medium" | "low").

    Returns:
        FindingsResponse with findings list and severity summary counts.

    Raises:
        HTTPException(404): If scan_id is unknown.
    """
    # Resolve scan_id.
    if not scan_id:
        scan_id = get_latest_completed_scan_id()
    if not scan_id:
        return FindingsResponse(
            findings=[],
            summary=FindingsSummary(total=0, critical=0, high=0, medium=0, low=0),
        )

    state = get_scan_state(scan_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    raw_findings = state.get("findings", [])

    # Apply severity filter if provided.
    if severity:
        try:
            sev_enum = SeverityLevel(severity.lower())
            raw_findings = [
                f for f in raw_findings
                if (f.get("severity", "medium") if isinstance(f.get("severity"), str)
                    else getattr(f.get("severity", "medium"), "value", "medium")) == sev_enum.value
            ]
        except ValueError:
            logger.warning("Unknown severity filter: %s", severity)

    # Compute summary counts from the FULL findings list (not filtered).
    all_findings = state.get("findings", [])
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        sev = f.get("severity", "medium")
        if hasattr(sev, "value"):
            sev = sev.value
        if sev in severity_counts:
            severity_counts[sev] += 1

    # Build validated Finding objects.
    finding_objects = []
    for f in raw_findings:
        try:
            finding_objects.append(Finding(**f))
        except Exception as exc:
            logger.debug("Skipping invalid finding: %s", exc)

    return FindingsResponse(
        findings=finding_objects,
        summary=FindingsSummary(
            total=len(all_findings),
            critical=severity_counts["critical"],
            high=severity_counts["high"],
            medium=severity_counts["medium"],
            low=severity_counts["low"],
        ),
    )
