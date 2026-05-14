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

---

## 2026-05-14 — Day 2 — Phase 7 (demo-app) out-of-order integration
**Phase:** 7 — Demo App (executed early because user supplied a complete demo)
**Person:** All (driven by Claude Code on user's instruction)
**Goal:** Integrate user-supplied demo-app into the project, document additional bugs found in code, pass Phase 7 Gate.

### What was done
- Read user-supplied demo-app at `C:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\demo-app\` (5 JSX, package.json, 7 markdown docs, README, BUGS_EXPLAINED_SIMPLE)
- Copied source files to `Exploratory_Testing_Agent/demo-app/pages/` and `demo-app/styles/` (proper Next.js pages-router layout)
- Created missing files the upstream package was missing: `pages/_document.jsx`, `pages/index.jsx` (redirects to /products), `next.config.js`, `postcss.config.js`, `tailwind.config.js`, `styles/globals.css` (custom CSS for the class names referenced in JSX since the markup uses `.header`, `.card`, etc., not Tailwind utilities)
- Ran `npm install` in `demo-app/` — 380+ packages resolved, exit 0
- Started `npm run dev` (port 3001), confirmed all 5 routes (`/`, `/products`, `/login`, `/cart`, `/checkout`) return 200
- Updated CLAUDE.md §2 demo-app subtree to match the actual files and lowercase Next.js convention
- Rewrote CLAUDE.md §10 as a "Pre-Planted Bug Catalogue": corrected all data-testids to match the shipped JSX (the original spec had many mismatches — `login-btn` → `login-button`, `pay-now-btn` → `place-order-btn`, suffixed ids like `add-to-cart-btn-{id}`, etc.)
- Documented **BUG-005** (auth bypass on `/cart` and `/checkout`) and **BUG-006** (non-numeric quantity silently removes cart item) — both already present in the JSX, just unflagged

### Decisions made
- **Decision:** Execute Phase 7 ahead of Phases 2–6 because the user supplied a finished demo-app.
  **Why:** The plan order is sequential, but having the demo-app ready earlier *helps* Phase 2 (which needs something to crawl) and Phase 4 (which needs something for personas to explore). No downside to early integration — the demo-app doesn't depend on any of the agent code.
  **Alternatives considered:** Park the demo-app and stick to plan order — rejected: the crawler in Phase 2 would have nothing to crawl, forcing us to crawl against a fixture or external URL.

- **Decision:** Document BUG-005 and BUG-006 (already present in code) rather than introducing brand-new defects by code mods.
  **Why:** The user asked "add some more bugs if required". Two real bugs are already in the code but uncommented (auth bypass; garbage-input removes item). Documenting these adds Malicious User (BUG-005) and Confused User (BUG-006) coverage without changing the app — minimum-risk way to expand the bug surface. New bug count: 6 (was 4).
  **Alternatives considered:** Add a third new bug via XSS in success page using `dangerouslySetInnerHTML` — rejected: requires code change, demo-app should reflect what users typically ship, and 6 bugs across 3 personas is already a fuller demo.

- **Decision:** Keep `pages/_app.jsx` in pages/ rather than under `src/`.
  **Why:** Next.js pages-router convention. The user-supplied app didn't use `src/`. CLAUDE.md §2 originally suggested `src/`, but that's optional in Next.js and the shipped app is simpler without it.

### Blockers encountered
- None.

### What was learned
- The demo-app's empty-cart conditional rendering means `/cart` and `/checkout` show 0 testids in a cold session. The crawler in Phase 2 must seed cart state (e.g. click Add-to-Cart on one product, or set `localStorage.cart` directly) before crawling `/cart` and `/checkout`, otherwise the form elements never appear. Add this to crawler design.
- Original CLAUDE.md §10 testids drifted significantly from the implemented app (probably written without seeing the final JSX). Lesson for future sections: when a section describes code that exists elsewhere, treat the code as source-of-truth and audit the spec against it before relying on it.
- The shipped `getCartCount()` uses `count = count + (item.quantity * "invalid")` to trigger NaN (BUG-002), not the `reduce` approach the original CLAUDE.md §10 spec described. Same intent, different implementation. CLAUDE.md updated to reflect actual code.

### Next session priorities
1. Begin Phase 2 — Coverage Intelligence Graph:
   - `engine/__init__.py`, `engine/crawler.py` (Playwright route discovery against `http://localhost:3001`)
   - Crawler must seed cart state before crawling `/cart` and `/checkout` (see "What was learned")
   - `engine/graph_builder.py` (NetworkX + coverage overlay using `data/existing_tests_mock.json`)
   - `agent/__init__.py`, `agent/prompts/gap_analysis.txt`, `agent/gap_analyser.py`
   - Promote `api/routes/graph.py` from stub to real (read from SCAN_STATE)
   - Wire crawler into `agent/brain.py` orchestration step 4

### Session end: 2026-05-14
### Gate status: [PASSED] GATE 7 — demo-app boots cleanly; all 5 routes return 200; 6 bugs documented and verified present in shipped JSX
