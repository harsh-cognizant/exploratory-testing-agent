"""
Module: api/routes/report.py
Purpose: GET /report — returns the final report from a completed scan.
         Reads from SCAN_STATE in agent.brain and constructs the ReportResponse.
Created: 2026-05-13
Updated: 2026-05-14 (Phase 6 — wired to report_builder)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException

from agent.brain import get_latest_completed_scan_id, get_scan_state
from api.models import (
    Finding,
    GeneratedTest,
    ReportResponse,
    ReportSummary,
    ScanStatus,
    SeverityLevel,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/report", response_model=ReportResponse)
async def get_report(scan_id: Optional[str] = None) -> ReportResponse:
    """Return the final report (summary + findings + generated tests) for a scan.

    Args:
        scan_id: Optional scan identifier. Omit to read the latest scan.

    Returns:
        ReportResponse with summary, findings, and generated tests.

    Raises:
        HTTPException(404): If scan_id is unknown.
        HTTPException(202): If scan is still running.
    """
    # Resolve scan_id.
    if not scan_id:
        scan_id = get_latest_completed_scan_id()
    if not scan_id:
        raise HTTPException(status_code=404, detail="No completed scan found")

    state = get_scan_state(scan_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    status = state.get("status")
    if isinstance(status, ScanStatus):
        status_val = status.value
    else:
        status_val = str(status)

    if status_val not in ("completed",):
        raise HTTPException(status_code=202, detail="Scan not completed yet")

    # Build report from scan state.
    graph = state.get("graph")
    raw_findings = state.get("findings", [])
    raw_tests = state.get("generated_tests", [])
    request_data = state.get("request", {})
    app_url = request_data.get("app_url", "http://localhost:3001")

    # Compute coverage stats.
    total_nodes = 0
    covered_before = 0
    if graph:
        total_nodes = graph.number_of_nodes()
        for _, attrs in graph.nodes(data=True):
            if attrs.get("covered"):
                covered_before += 1

    explored_nodes = set(f.get("node_id", "") for f in raw_findings)
    covered_after = covered_before + len(explored_nodes)
    if covered_after > total_nodes:
        covered_after = total_nodes

    coverage_before_pct = round((covered_before / total_nodes) * 100, 1) if total_nodes else 0.0
    coverage_after_pct = round((covered_after / total_nodes) * 100, 1) if total_nodes else 0.0

    # Severity counts.
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in raw_findings:
        sev = f.get("severity", "medium")
        if hasattr(sev, "value"):
            sev = sev.value
        if sev in severity_counts:
            severity_counts[sev] += 1

    # Build validated objects.
    finding_objects = []
    for f in raw_findings:
        try:
            finding_objects.append(Finding(**f))
        except Exception as exc:
            logger.debug("Skipping invalid finding in report: %s", exc)

    test_objects = []
    for t in raw_tests:
        try:
            test_objects.append(GeneratedTest(**t))
        except Exception as exc:
            logger.debug("Skipping invalid test in report: %s", exc)

    return ReportResponse(
        report_id=f"report_{scan_id}",
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        app_url=app_url,
        summary=ReportSummary(
            total_nodes_discovered=total_nodes,
            nodes_covered_before=covered_before,
            coverage_before_percent=coverage_before_pct,
            gaps_found=len(raw_findings),
            critical_findings=severity_counts["critical"],
            high_findings=severity_counts["high"],
            medium_findings=severity_counts["medium"],
            estimated_coverage_after_percent=coverage_after_pct,
        ),
        findings=finding_objects,
        generated_tests=test_objects,
    )
