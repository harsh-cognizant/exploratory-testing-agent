"""
Module: api/routes/memory_routes.py
Purpose: GET /memory — returns a summary of past runs stored in ChromaDB.
         Phase 1 stub: returns no runs; populated by engine/memory.py
         starting in Phase 5.

         Per CLAUDE.md §1 hard constraints, all memory business logic lives
         in engine/memory.py. This route file only imports and exposes it.
Created: 2026-05-13
"""

from fastapi import APIRouter

from api.models import MemoryResponse

router = APIRouter()


@router.get("/memory", response_model=MemoryResponse)
async def get_memory() -> MemoryResponse:
    """Return a summary of past run memory.

    Phase 1 stub — no runs. Real data lands in Phase 5 once
    engine/memory.py is wired up to ChromaDB.

    Returns:
        MemoryResponse with an empty runs list and total_findings_in_memory=0.
    """
    return MemoryResponse(runs=[], total_findings_in_memory=0)
