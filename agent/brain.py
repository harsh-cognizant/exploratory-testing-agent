"""
Module: agent/brain.py
Purpose: Central orchestrator. Owns SCAN_STATE (the module-level dict keyed by
         scan_id) and runs the agent loop as a background asyncio task per
         CLAUDE.md §4.16.

         Full flow: init → crawl → graph → gap analysis → risk scoring →
         queue assembly → exploration (per-node per-persona) → memory store →
         test generation → report compilation.
Created: 2026-05-14
Updated: 2026-05-14 (Phase 4-6 — full orchestration flow)
"""

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from agent.gap_analyser import analyse_gaps
from agent.personas import generate_persona_actions
from agent.test_generator import generate_tests_for_findings
from api.models import ScanRequest, ScanStatus
from engine.crawler import crawl
from engine.explorer import explore_node
from engine.graph_builder import build_coverage_graph
from engine.memory import AgentMemory
from engine.report_builder import compile_report
from engine.risk_scorer import build_queue, score_graph

load_dotenv()

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SCAN_TIMEOUT_SECONDS: int = 180
DEFAULT_PERSONAS: List[str] = ["confused_user", "power_user", "malicious_user"]

# Module-level scan state. Keyed by scan_id. Each entry tracks progress so
# GET /scan/{id}/status and GET /graph can read from a single source of truth.
# Per CLAUDE.md §4.16 — never block the FastAPI event loop; all updates are
# made from within the async task and any reader (route handler) gets a
# snapshot at the moment of access.
SCAN_STATE: Dict[str, Dict[str, Any]] = {}

# Singleton AgentMemory — lazily initialized on first use.
_memory: Optional[AgentMemory] = None


def _get_memory() -> AgentMemory:
    """Return the singleton AgentMemory instance, initializing on first call.

    Returns:
        AgentMemory instance backed by ChromaDB.
    """
    global _memory
    if _memory is None:
        _memory = AgentMemory()
    return _memory


def _new_scan_id() -> str:
    """Return a new scan_id of the form `scan_YYYYMMDD_HHMMSS`."""
    return f"scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"


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
        "generated_tests": [],
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
    """Execute the full orchestration flow (steps 1-13).

    Per CLAUDE.md §4.16:
    Steps 1-3: Init (already done by start_scan)
    Step 4: Crawl the application
    Step 5: Build the coverage graph
    Step 6: Gap analysis via Claude
    Step 7: Risk scoring
    Step 8: Assemble ranked queue
    Step 9: Exploration loop (per-node, per-persona)
    Step 10: Memory query and store
    Step 11: Test generation
    Step 12: Report compilation
    Step 13: Mark complete

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
        # ── Step 4: Crawl ────────────────────────────────────────────
        state["current_node"] = "crawler"
        state["progress_percent"] = 5
        logger.info("Scan %s: crawling %s", scan_id, request.app_url)
        elements = await crawl(request.app_url, max_pages=request.max_nodes)
        logger.info("Scan %s: crawler returned %d elements", scan_id, len(elements))

        # ── Step 5: Build graph ──────────────────────────────────────
        state["current_node"] = "graph_builder"
        state["progress_percent"] = 15
        graph = build_coverage_graph(elements, request.existing_tests_path)
        state["graph"] = graph
        state["nodes_total"] = graph.number_of_nodes()

        # ── Step 6: Gap analysis (Claude) ────────────────────────────
        if _elapsed_over_budget():
            logger.warning("Scan %s: timeout before gap analysis; skipping", scan_id)
        else:
            state["current_node"] = "gap_analyser"
            state["progress_percent"] = 25
            try:
                gaps = analyse_gaps(graph)
                state["gaps"] = gaps
                logger.info("Scan %s: gap_analyser found %d gaps", scan_id, len(gaps))
            except RuntimeError as exc:
                logger.warning("Scan %s: skipping gap analysis (%s)", scan_id, exc)
                state["gaps"] = []
                state["error"] = str(exc)

        # ── Step 7: Risk scoring ─────────────────────────────────────
        if _elapsed_over_budget():
            logger.warning("Scan %s: timeout before risk scoring; skipping", scan_id)
        else:
            state["current_node"] = "risk_scorer"
            state["progress_percent"] = 35

            # Query memory for adjustments (Phase 5 integration).
            memory_adjustments: Dict[str, float] = {}
            try:
                memory = _get_memory()
                for node_id, attrs in graph.nodes(data=True):
                    url = attrs.get("url", "")
                    context = f"{url} {attrs.get('label', '')}"
                    adj = memory.get_memory_adjustment(node_id, context)
                    if adj != 0.0:
                        memory_adjustments[node_id] = adj
                        # Set has_memory flag on graph node.
                        attrs["has_memory"] = True
                logger.info(
                    "Scan %s: memory provided %d adjustments",
                    scan_id, len(memory_adjustments),
                )
            except Exception as exc:
                logger.warning("Scan %s: memory query failed (%s); scoring without", scan_id, exc)

            score_graph(graph, memory_adjustments=memory_adjustments)

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

        # ── Step 9: Exploration loop ─────────────────────────────────
        personas = request.personas or DEFAULT_PERSONAS
        all_findings: List[Dict[str, Any]] = []

        if _elapsed_over_budget():
            logger.warning("Scan %s: timeout before exploration; skipping", scan_id)
        else:
            state["current_node"] = "explorer"
            state["progress_percent"] = 40

            # Build the exploration queue from the risk-ranked queue.
            # Only explore page-type nodes (buttons/inputs are explored
            # as part of their parent page's action set).
            explore_queue: List[Dict[str, Any]] = []
            for node_id, attrs in graph.nodes(data=True):
                element_type = attrs.get("element_type", "")
                if element_type == "page":
                    explore_queue.append({"node_id": node_id, "attrs": attrs})

            # Sort by risk_score descending (explore highest-risk first).
            explore_queue.sort(
                key=lambda x: float(x["attrs"].get("risk_score", 0)),
                reverse=True,
            )

            total_explore = len(explore_queue) * len(personas)
            explored_count = 0

            for page_item in explore_queue:
                if _elapsed_over_budget():
                    logger.warning("Scan %s: timeout during exploration; stopping early", scan_id)
                    break

                node_id = page_item["node_id"]
                node_attrs = page_item["attrs"]
                page_url = node_attrs.get("url", "/")

                for persona in personas:
                    if _elapsed_over_budget():
                        break

                    state["current_node"] = node_id
                    state["current_persona"] = persona
                    explored_count += 1
                    progress = 40 + int((explored_count / max(total_explore, 1)) * 35)
                    state["progress_percent"] = min(progress, 75)

                    logger.info(
                        "Scan %s: exploring %s with %s (%d/%d)",
                        scan_id, page_url, persona, explored_count, total_explore,
                    )

                    # Generate persona-specific actions via Claude.
                    try:
                        actions = generate_persona_actions(
                            persona=persona,
                            page_url=f"{request.app_url}{page_url}",
                            graph=graph,
                            node_id=node_id,
                        )
                    except Exception as exc:
                        logger.warning(
                            "Scan %s: persona generation failed for %s/%s: %s",
                            scan_id, persona, page_url, exc,
                        )
                        actions = []

                    if not actions:
                        continue

                    # Run Playwright exploration with the action list.
                    try:
                        findings = await explore_node(
                            node_id=node_id,
                            node_attrs=node_attrs,
                            persona_actions=actions,
                            app_url=request.app_url,
                            persona=persona,
                        )
                    except Exception as exc:
                        logger.warning(
                            "Scan %s: exploration failed for %s/%s: %s",
                            scan_id, persona, page_url, exc,
                        )
                        findings = []

                    all_findings.extend(findings)
                    state["findings"] = all_findings
                    state["findings_so_far"] = len(all_findings)
                    state["nodes_explored"] = len(set(
                        f.get("node_id") for f in all_findings
                    ))

            logger.info(
                "Scan %s: exploration complete — %d findings from %d node-persona combos",
                scan_id, len(all_findings), explored_count,
            )

        # ── Step 10: Memory store ────────────────────────────────────
        state["current_node"] = "memory"
        state["current_persona"] = None
        state["progress_percent"] = 80

        try:
            memory = _get_memory()
            for finding in all_findings:
                memory.store_finding(finding, run_id=scan_id)
            logger.info(
                "Scan %s: stored %d findings in memory", scan_id, len(all_findings),
            )
        except Exception as exc:
            logger.warning("Scan %s: memory store failed (%s)", scan_id, exc)

        # ── Step 11: Test generation ─────────────────────────────────
        if _elapsed_over_budget():
            logger.warning("Scan %s: timeout before test generation; skipping", scan_id)
        else:
            state["current_node"] = "test_generator"
            state["progress_percent"] = 85

            try:
                generated = generate_tests_for_findings(
                    all_findings, app_url=request.app_url,
                )
                state["generated_tests"] = generated
                logger.info(
                    "Scan %s: generated %d tests", scan_id, len(generated),
                )
            except Exception as exc:
                logger.warning(
                    "Scan %s: test generation failed (%s)", scan_id, exc,
                )
                state["generated_tests"] = []

        # ── Step 12: Report compilation ──────────────────────────────
        state["current_node"] = "report_builder"
        state["progress_percent"] = 95

        try:
            report = compile_report(state)
            state["report"] = report
            logger.info("Scan %s: report compiled", scan_id)
        except Exception as exc:
            logger.warning("Scan %s: report compilation failed (%s)", scan_id, exc)

        # ── Step 13: Mark complete ───────────────────────────────────
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
