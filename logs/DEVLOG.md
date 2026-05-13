# DEVLOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** 2026-05-13
**Team:** Person A (AI/LLM), Person B (Backend), Person C (Frontend)

Chronological developer diary. Every session, decision, blocker, and resolution.
Read this file to understand WHY the project is in its current state.

---

## 2026-05-13 — Day 1 — Project initialisation & Phase 1 scaffolding
**Phase:** 1 — Infrastructure & Scaffolding
**Person:** All (driven by Claude Code on user's instruction)
**Goal:** Audit CLAUDE.md instruction file, scaffold all Phase 1 files, pass Gate 1.

### What was done
- Created git branch `dev` from `master` and pushed to origin; working branch for all hackathon iterations
- Reviewed existing CLAUDE.md (2920 lines) against project plan via subagent — surfaced 15 issues
- Applied 14 edits (one was a no-op): model ID, Windows shell, schema/contract fixes, §§14–20 collapse
- Final CLAUDE.md: 2632 lines, all stale tokens removed
- Created `requirements.txt`, `.env.example`, `.gitignore`
- Created `logs/` and initialised CHANGELOG, DEVLOG, COMMANDLOG, BUGLOG
- Created `api/models.py` with full Pydantic model set per CLAUDE.md §4.4
- Created `api/__init__.py`, `api/routes/__init__.py`, and seven route stubs so `api/main.py` imports succeed at Gate 1
- Created `api/main.py` with CORS, static-file mount for `/screenshots`, `/health` endpoint
- Created `data/simulated_change_frequency.csv`, `data/simulated_defect_history.csv`, `data/existing_tests_mock.json`

### Decisions made
- **Decision:** Add seven minimal route stubs (`scan.py`, `scan_status.py`, `graph.py`, `queue.py`, `findings.py`, `memory_routes.py`, `report.py`) in Phase 1, even though the CLAUDE.md §3 build order doesn't list them until later phases.
  **Why:** `api/main.py` imports all seven via `from api.routes import …`. Without the stub files, uvicorn would fail to start and Gate 1 would be unreachable. The stubs declare empty `APIRouter()` objects only — no business logic — so they don't pre-empt Phase 2+ implementation.
  **Alternatives considered:** (a) Comment out the route imports in main.py and re-enable per phase — rejected: would diverge from CLAUDE.md §4.5 verbatim spec and break Section 19's sync rules. (b) Skip stubbing and accept Gate 1 failure — rejected: stops the build.

- **Decision:** Working branch is `dev`; `master` stays clean.
  **Why:** User instructed at session start. Recorded as a feedback memory so future sessions also avoid landing on master without explicit approval.

### Blockers encountered
- None yet.

### What was learned
- The plan doc's tech-stack section pinned `claude-sonnet-4-20250514` (a 2025 snapshot ID); the current Sonnet family in 2026-05 is `claude-sonnet-4-6`. CLAUDE.md was updated accordingly.
- CLAUDE.md originally specified bash heredoc bootstrap for log files in §20; this fails on PowerShell 5.1 (the user's shell). Replaced with PowerShell here-string approach.

### Next session priorities
1. Begin Phase 2 — Coverage Intelligence Graph:
   - `engine/__init__.py`, `engine/crawler.py` (Playwright route discovery)
   - `engine/graph_builder.py` (NetworkX + coverage overlay)
   - `agent/__init__.py`, `agent/prompts/gap_analysis.txt`, `agent/gap_analyser.py`
   - Promote `api/routes/graph.py` from stub to real implementation reading from SCAN_STATE
2. Phase 2 Gate: `GET /graph?scan_id=...` returns real nodes/edges with coverage overlay against the demo app (or, until demo-app exists, against a fixture URL).

### What was learned (Gate 1 specifics)
- Resolved package versions are much newer than the `>=` minimums in `requirements.txt` (e.g. anthropic 0.101.0 vs. minimum 0.28.0, langgraph 1.2.0 vs. 0.2.0, fastapi 0.136.1 vs. 0.111.0). Code in later phases should target the resolved API surface, not the floor.
- Uvicorn binds `127.0.0.1` by default on Windows even without `--host`. The dashboard's CORS `allow_origins=["http://localhost:3000"]` will only work if React requests use `localhost` — keep this consistent across the stack.
- Polling `localhost:8000` before uvicorn fully bound returned ECONNREFUSED; using `127.0.0.1:8000` after startup completed succeeded immediately. Dashboard polling code should use `127.0.0.1` or accept retry on connect-refused.

### Session end: 2026-05-13
### Gate status: [PASSED] GATE 1 — `/health` returns 200, all four read-only route stubs respond 200
