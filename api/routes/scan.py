"""
Module: api/routes/scan.py
Purpose: POST /scan — kicks off an async background scan via agent.brain.
         The endpoint must return immediately (CLAUDE.md §4.16); the scan
         runs as an asyncio task tracked in SCAN_STATE.
Created: 2026-05-13
Updated: 2026-05-14 (Phase 2 — wired to agent.brain)
"""

from fastapi import APIRouter

from agent.brain import start_scan
from api.models import ScanRequest, ScanResponse, ScanStatus

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def post_scan(request: ScanRequest) -> ScanResponse:
    """Start a new scan against the target application.

    Args:
        request: ScanRequest with app_url, existing_tests_path, max_nodes, personas.

    Returns:
        ScanResponse with a generated scan_id and status=STARTED. The actual
        crawl runs in the background; poll GET /scan/{scan_id}/status to track.
    """
    scan_id = await start_scan(request)
    return ScanResponse(scan_id=scan_id, status=ScanStatus.STARTED)
