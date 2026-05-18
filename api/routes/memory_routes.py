"""
Module: api/routes/memory_routes.py
Purpose: GET /memory — returns a summary of past runs stored in ChromaDB.
         Per CLAUDE.md §1 hard constraints, all memory business logic lives
         in engine/memory.py. This route file only imports and exposes it.
Created: 2026-05-13
Updated: 2026-05-14 (Phase 5 — wired to AgentMemory)
"""

import logging

from fastapi import APIRouter

from api.models import MemoryResponse, MemoryRun

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/memory", response_model=MemoryResponse)
async def get_memory() -> MemoryResponse:
    """Return a summary of past run memory from ChromaDB.

    Returns:
        MemoryResponse with run summaries and total findings count.
    """
    try:
        from engine.memory import AgentMemory
        memory = AgentMemory()
        runs = memory.get_run_summaries()
        total = memory.get_total_findings_count()

        run_objects = [
            MemoryRun(
                run_id=r["run_id"],
                date=r.get("date", ""),
                findings_count=r.get("findings_count", 0),
                top_finding=r.get("top_finding"),
            )
            for r in runs
        ]

        return MemoryResponse(
            runs=run_objects,
            total_findings_in_memory=total,
        )
    except Exception as exc:
        logger.warning("Memory query failed: %s; returning empty", exc)
        return MemoryResponse(runs=[], total_findings_in_memory=0)
