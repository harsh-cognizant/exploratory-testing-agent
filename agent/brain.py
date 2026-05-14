"""
Module: agent/brain.py
Purpose: Central orchestrator. Owns SCAN_STATE (the module-level dict keyed by
         scan_id) and runs the agent loop as a background asyncio task per
         CLAUDE.md §4.16.

         Phase 3 implements steps 1-8 (init → crawl → graph → gap analysis →
         risk scoring → queue assembly). Steps 9-13 (exploration, memory,
         test generation, report compilation) are stubbed for later phases —
         current scans complete cleanly without them.
Created: 2026-05-14
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from agent.gap_analyser import analyse_gaps
from api.models import ScanRequest, ScanStatus
from engine.crawler import crawl
from engine.graph_builder import build_coverage_graph
from engine.risk_scorer import build_queue, score_graph

load_dotenv()

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SCAN_TIMEOUT_SECONDS: int = 180

# Module-level scan state. Keyed by scan_id. Each entry tracks progress so
# GET /scan/{id}/status and GET /graph can read from a single source of truth.
# Per CLAUDE.md §4.16 — never block the FastAPI event loop; all updates are
# made from within the async task and any reader (route handler) gets a
# snapshot at the moment of access.
SCAN_STATE: Dict[str, Dict[str, Any]] = {}


def _new_scan_id() -> str:
    """Return a new scan_id of the form `scan_YYYYMMDD_HHMMSS`."""
    return f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


def _init_scan(scan_id: str, request: ScanRequest) -> None:
    """Initialise SCAN_STATE[scan_id] with empty progress values."""
    SCAN_STATE[scan_id] = {
        "scan_id": scan_id,
        "status": ScanStatus.STARTED,
        "progress_percent": 0,
        "nodes_explored": 0,
        "nodes_total": 0,
        "findings_so_far": 0,
        "current_node": None,
        "current_persona": None,
        "request": request.model_dump(),
        "graph": None,
        "findings": [],
        "gaps": [],
        "queue": [],
        "report": None,
        "started_at": time.monotonic(),
        "error": None,
    }


def _read_timeout_seconds() -> int:
    """Read SCAN_TIMEOUT_SECONDS from env, with the §4.16 default."""
    raw = os.getenv("SCAN_TIMEOUT_SECONDS")
    if not raw:
        return DEFAULT_SCAN_TIMEOUT_SECONDS
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "SCAN_TIMEOUT_SECONDS=%r is not an int; using default %d",
            raw, DEFAULT_SCAN_TIMEOUT_SECONDS,
        )
        return DEFAULT_SCAN_TIMEOUT_SECONDS


async def _run_scan(scan_id: str, request: ScanRequest) -> None:
    """Execute the Phase 3 subset of the orchestration flow.

    Per CLAUDE.md §4.16, the full flow has 13 steps. Phase 3 covers steps
    1-8 (init, crawl, graph build, gap analysis, risk scoring, queue
    assembly). Exploration, memory query, test generation, and report
    compilation are placeholders until later phases land.

    Args:
        scan_id: The scan identifier returned by POST /scan.
        request: Validated ScanRequest from the client.
    """
    state = SCAN_STATE[scan_id]
    state["status"] = ScanStatus.RUNNING
    timeout_s = _read_timeout_seconds()
    started = state["started_at"]

    def _elapsed_over_budget() -> bool:
        """Soft timeout check per §4.16 step 9a."""
        return (time.monotonic() - started) > timeout_s

    try:
        # Step 4: crawl.
        state["current_node"] = "crawler"
        state["progress_percent"] = 10
        logger.info("Scan %s: crawling %s", scan_id, request.app_url)
        elements = await crawl(request.app_url, max_pages=request.max_nodes)
        logger.info("Scan %s: crawler returned %d elements", scan_id, len(elements))

        # Step 5: build graph.
        state["current_node"] = "graph_builder"
        state["progress_percent"] = 40
        graph = build_coverage_graph(elements, request.existing_tests_path)
        state["graph"] = graph
        state["nodes_total"] = graph.number_of_nodes()

        # Step 6: gap analysis (Claude). Skipped if API key absent — the scan
        # still finishes successfully with no gap_reason annotations.
        if _elapsed_over_budget():
            logger.warning("Scan %s: timeout before gap analysis; skipping", scan_id)
        else:
            state["current_node"] = "gap_analyser"
            state["progress_percent"] = 70
            try:
                gaps = analyse_gaps(graph)
                state["gaps"] = gaps
                logger.info("Scan %s: gap_analyser found %d gaps", scan_id, len(gaps))
            except RuntimeError as exc:
                # Missing ANTHROPIC_API_KEY — continue without gaps but record the cause.
                logger.warning("Scan %s: skipping gap analysis (%s)", scan_id, exc)
                state["gaps"] = []
                state["error"] = str(exc)

        # Step 7: risk scoring. The formula is deterministic and CSV-driven —
        # no Claude call here, so the timeout check is a courtesy only.
        if _elapsed_over_budget():
            logger.warning("Scan %s: timeout before risk scoring; skipping", scan_id)
        else:
            state["current_node"] = "risk_scorer"
            state["progress_percent"] = 85
            score_graph(graph)
            # Step 8: assemble the ranked queue snapshot for /queue consumers.
            queue_items = build_queue(graph)
            state["queue"] = [item.model_dump() for item in queue_items]
            state["nodes_total"] = graph.number_of_nodes()
            logger.info(
                "Scan %s: risk_scorer ranked %d nodes; top=%s",
                scan_id,
                len(queue_items),
                queue_items[0].node_id if queue_items else "—",
            )

        # Phase 3 stops here. Steps 9-13 will fill in across Phases 4-6.
        state["progress_percent"] = 100
        state["current_node"] = None
        state["current_persona"] = None
        state["status"] = ScanStatus.COMPLETED

    except Exception as exc:  # pragma: no cover — defensive top-level
        logger.exception("Scan %s failed", scan_id)
        state["status"] = ScanStatus.FAILED
        state["error"] = repr(exc)


async def start_scan(request: ScanRequest) -> str:
    """Generate a scan_id, register state, and schedule `_run_scan` as a task.

    Returns immediately; POST /scan must not block (CLAUDE.md §4.16 rules).

    Args:
        request: Validated ScanRequest from the route handler.

    Returns:
        The new scan_id. Caller should expose it to the client.
    """
    scan_id = _new_scan_id()
    _init_scan(scan_id, request)
    asyncio.create_task(_run_scan(scan_id, request))
    return scan_id


def get_scan_state(scan_id: str) -> Optional[Dict[str, Any]]:
    """Return the SCAN_STATE entry for scan_id, or None if unknown.

    Route handlers wrap None with a 404 per CLAUDE.md §6.
    """
    return SCAN_STATE.get(scan_id)


def get_latest_completed_scan_id() -> Optional[str]:
    """Return the most-recent scan_id with a non-None graph. Used by /graph
    and /queue when called without a scan_id query param."""
    completed = [
        sid for sid, st in SCAN_STATE.items() if st.get("graph") is not None
    ]
    if not completed:
        return None
    return sorted(completed)[-1]
