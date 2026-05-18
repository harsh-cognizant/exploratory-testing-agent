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

---

## 2026-05-14 — Day 2 (cont.) — Phase 3 Risk Prioritisation Engine
**Phase:** 3 — Risk Prioritisation Engine
**Person:** All (driven by Claude Code on user's instruction)
**Goal:** Implement the canonical three-factor risk formula, wire `/queue` to a ranked view, pass Gate 3 with `/checkout` and `/login` in the top 3.

### What was done
- Wrote `agent/prompts/risk_ranking.txt` verbatim from CLAUDE.md §7 (shipped, not yet called).
- Wrote `engine/risk_scorer.py`:
  - `W_CHANGE_FREQUENCY=0.35`, `W_DEFECT_DENSITY=0.40`, `W_CRITICALITY=0.25` (sum exactly 1.0 — asserted in smoke test).
  - `CRITICALITY_MAP` copied byte-for-byte from §4.8.
  - `_load_csv_factor` + `_normalise` divide each column by its max; unmatched URLs get `DEFAULT_FACTOR_VALUE=0.1`.
  - `score_graph(graph, memory_adjustments=None)` mutates the graph in place, clamps to `[0, 1]` after applying any memory adjustment (the §4.16-step-9b safety net even though Phase 3 never passes a non-zero adjustment).
  - `build_queue(graph, risk_band=None)` returns `List[QueueItem]` sorted by `risk_score` desc with deterministic node-id tie-break; reuses `gap_reason` when present, else synthesises a one-sentence reason from the dominant factor.
- Promoted `api/routes/queue.py` from Phase-1 stub to real endpoint reading `SCAN_STATE`.
- Extended `agent/brain.py` orchestration from steps 1–6 to steps 1–8: post-gap-analysis it calls `score_graph` then `build_queue`, stores the queue snapshot at `SCAN_STATE[scan_id]["queue"]`.
- Smoke-tested the formula offline against a hand-built 6-page graph: `/checkout`=1.0, `/cart`=0.6438, `/login`=0.6042, `/profile`=0.3771, `/products`=0.3229, `/search`=0.1937 — matches hand-computed values.
- Live Gate 3 against demo-app: scan completed in <3s, `/queue?scan_id=...` returned 16 ranked items, `/queue?risk_band=critical` returned 2 items, `/queue?risk_band=high` returned 7 items.

### Decisions made
- **Decision:** Don't call Claude for risk-ranking in Phase 3 — the formula is sufficient for `/queue` and the prompt is shipped for a possible future refinement pass.
  **Why:** CLAUDE.md §3 Phase 3 lists `risk_ranking.txt` and `risk_scorer.py` as separate build steps; the orchestration step 7 (§4.16) says "Run risk_scorer", not "Run Claude". A deterministic, explainable formula is also better for the demo narrative than a fresh LLM call per request.
  **Alternatives considered:** Wrap `build_queue` with a Claude call that re-orders the top-N items by qualitative judgement. Deferred to Phase 5/9 if needed.

- **Decision:** `build_queue` returns items ordered globally then filters; the post-filter `rank` is the position within the filtered queue.
  **Why:** Matches §6's `/queue?risk_band=` contract — clients filtering by band expect rank 1 to be the highest-risk item in that band, not a sparse list with gaps.

### Blockers encountered
- **Blocker:** Bash polling loop initially produced no status because the scan_id was saved by `Set-Content -Encoding utf8` (PowerShell 5.1) which writes UTF-8 *with* BOM. The BOM survived the `cat .gate3_scan_id` read and corrupted the curl URL.
  **How resolved:** Hardcoded the scan_id into the next poll loop, then deleted the temp file. Long-term lesson: prefer `Out-File -Encoding utf8NoBOM` (PS 6+) or just pass scan_id through stdin pipes — never save it to a file when the consumer is bash.
  **Time lost:** ~2 min.

### What was learned
- Within a single URL, all element nodes (form, button, input) share the same risk_score because the formula is URL-keyed. The Gate 3 sanity check ("no two adjacent items have same score unless 0.5 default") was written assuming distinct-URL fixtures; in the demo-app it expectedly fails because BFS surfaces multiple elements per route. Recorded in CHANGELOG 0.3.0 as a characteristic, not a defect — different URLs do produce different scores, which is the meaningful invariant.
- `_load_csv_factor` defensive `try/except OSError` is necessary on Windows even when the file exists — DictReader can raise `UnicodeDecodeError` on stray bytes from PowerShell-written CSVs; explicit `encoding="utf-8"` plus the fallback path keeps the scan alive.

### Next session priorities
1. Begin Phase 4 — Behavioural Exploration Engine:
   - `agent/prompts/persona_confused.txt`, `persona_power.txt`, `persona_malicious.txt`
   - `agent/personas.py` (Claude call → action lists; closed-set action_type filter per §4.13)
   - `engine/anomaly_detector.py` (console errors, 4xx/5xx, unexpected redirects, form-accepts-invalid, page-crash-blank)
   - `engine/explorer.py` (Playwright per-persona exploration; one screenshot per anomaly)
   - `api/routes/findings.py` promotion + `scan.py` complete wiring
2. Phase 4 Gate: full scan against demo-app finds ≥1 pre-planted bug (BUG-001..BUG-006).

### Session end: 2026-05-14
### Gate status: [PASSED] GATE 3 — `/queue` ranks `/checkout`=1.0 CRITICAL at #1, `/cart`=0.6438 HIGH at #3, `/login`=0.6042 HIGH at #5; `risk_band` filter works for `critical`/`high`/`low`.

---

## 2026-05-14 — Day 2 (cont.) — Phases 4-6 Implementation
**Phase:** 4, 5, 6 — Behavioural Exploration, Memory, Output
**Person:** All (driven by Claude Code on user's instruction)
**Goal:** Build the remaining three layers: persona-driven exploration (Phase 4), memory and learning (Phase 5), test generation and reporting (Phase 6). Wire all routes to real data.

### What was done
- **Phase 4 — Behavioural Exploration Engine:**
  - Created 3 persona prompt templates (`persona_confused.txt`, `persona_power.txt`, `persona_malicious.txt`)
  - Created `agent/personas.py` — Claude-based action list generation per persona with closed-set validation, MAX_ACTIONS_PER_PERSONA=8 cap, retry-once JSON parsing
  - Created `engine/anomaly_detector.py` — AnomalyCollector class capturing JS console errors, HTTP 4xx/5xx, unexpected redirects, form validation bypasses, page crashes; builds structured Finding dicts with reproduction steps
  - Created `engine/explorer.py` — Playwright-based explorer executing persona action lists on graph nodes, with screenshots on every finding
  - Promoted `api/routes/findings.py` from stub to real endpoint reading SCAN_STATE with severity filtering

- **Phase 5 — Memory & Learning Loop:**
  - Created `engine/memory.py` — AgentMemory using ChromaDB PersistentClient(path="./chroma_store") + sentence-transformers all-MiniLM-L6-v2. Constants: similarity_threshold=0.85, positive_adj=+0.15, negative_adj=-0.10
  - Promoted `api/routes/memory_routes.py` from stub to real endpoint
  - Wired memory adjustments into brain.py risk scoring step

- **Phase 6 — Output & Test Generation:**
  - Created `agent/prompts/test_generation.txt` — Pytest test generation prompt template
  - Created `agent/test_generator.py` — generates Pytest functions from high/critical findings via Claude with syntax validation
  - Created `engine/report_builder.py` — compiles coverage stats, severity breakdown, and summary
  - Promoted `api/routes/report.py` from stub to full ReportResponse
  - Updated `agent/brain.py` with full 13-step orchestration flow

### Verification
- All 11 Python modules import cleanly (exit code 0)
- FastAPI server starts cleanly on port 8000
- /health → 200 ✅, /findings → 200 (empty) ✅, /memory → 200 (empty) ✅, /report → 404 (no scan) ✅
- sentence-transformers model loaded successfully on first /memory request

### Decisions made
- **Decision:** Lazy-init singleton AgentMemory in brain.py rather than global init.
  **Why:** The model download (~90MB) should only happen when memory is actually needed, not at module import time. This keeps server startup fast.
- **Decision:** Explore only page-type nodes (not individual button/input nodes).
  **Why:** Buttons and inputs are explored as part of their parent page's action set via persona action lists. Exploring them individually would duplicate work and waste Claude API calls.

### Next session priorities
1. Run a full end-to-end scan against the demo-app to verify Phase 4 exploration finds pre-planted bugs
2. Build Phase 8 — Dashboard (React + D3.js)
3. Integration testing across all layers

### Session end: 2026-05-14
### Gate status: [PENDING] GATE 4-6 — all code written and imports verified; end-to-end scan pending

---

## 2026-05-18 — Day 5 — Live debugging on corp network; resilience + offline mode
**Phase:** Post-Phase-9 hardening (no new feature phase)
**Person:** All (driven by Claude Code on user's instruction)
**Goal:** Pull updated dev branch, run the application end-to-end, identify what's actually broken, fix it.

### What was done
- Pulled commit `21d160f` ("Update scanning logic and dashboard components (#1)") from `origin/dev` — 57 files added/changed including the dashboard scaffold, persona engine, anomaly detector, explorer, memory, report builder, test generator, and full orchestration in `agent/brain.py`
- Started uvicorn + demo-app, triggered an end-to-end scan against `http://localhost:3001` with the `confused_user` persona. Result: `status=completed, progress=100%, nodes_total=16, nodes_explored=0, findings=0`. Symptom: scan looks "successful" but does nothing.
- Decoded the UTF-16 uvicorn log (PowerShell `Out-File` writes UTF-16 by default) and traced four root causes:
  1. `ANTHROPIC_API_KEY` not set anywhere in the user's environment (despite the user's belief otherwise) → gap analyser and persona generator both throw, the orchestrator swallows it, scan completes silently
  2. `sentence-transformers` first-time download hit `[SSL: CERTIFICATE_VERIFY_FAILED]` against `huggingface.co` → 5-retry storm, then memory disabled
  3. `nodes_explored` was being computed as `len(set(finding.node_id))` so 0 findings always meant 0 explored — misleading
  4. Persona fallback `[{action_type: 'click', target: 'button'}]` produces false-positive click noise when LLM is unreachable
- User asked to switch the AI backend to OpenRouter (base URL `https://openrouter.ai/api`, auth token `sk-or-v1-…`, model `poolside/laguna-m.1:free`). Wrote `.env`, refactored `_get_client()` in all three agent modules to support `ANTHROPIC_AUTH_TOKEN` (Bearer auth) alongside `ANTHROPIC_API_KEY` (x-api-key)
- Replaced naïve TLS handling: installed `truststore` and inject it in `api/main.py` before any HTTPS-using import, so Python validates against the Windows trust store (which already has the corp CA via GPO)
- Tested connectivity to confirm the TLS plumbing worked: `httpx.get('https://api.anthropic.com/')` now returns a real `404`, not a TLS error. Then `https://openrouter.ai/api/v1/models` returned a 403 page — but the page body is a **Cognizant Zscaler "Security Exception" block page**, not an OpenRouter response. TLS handshake completes; the URL itself is filtered. `https://huggingface.co/` is blocked the same way
- Asked the user how to proceed; user selected "Skip AI — validate plumbing only"
- Implemented `LLM_OFFLINE=1` mode:
  - `agent/offline_mocks.py` — canned (persona, path) action lists. Each pair deliberately targets one of the demo-app bugs from CLAUDE.md §10 (BUG-001 empty password, BUG-002 NaN cart count, BUG-003 negative quantity, BUG-004 invalid card, BUG-006 non-numeric quantity)
  - `agent/personas.py` — short-circuits to mocks when `LLM_OFFLINE=1`
  - `agent/gap_analyser.py` — returns every uncovered node as a heuristic gap when offline
  - `agent/test_generator.py` — emits a deterministic Pytest stub per high/critical finding when offline (so the report panel still has something to show)
- First offline run revealed a deeper issue: every persona action on `/cart` and `/checkout` was timing out. Traced to the demo-app's `_app.jsx` CartProvider: two useEffects (read cart → write cart) race on every mount, and the write effect fires with the initial `[]` state *before* the read effect picks up the seeded value. So a hard `page.goto('/checkout')` clears any prior localStorage entry on mount and `/checkout` renders the empty-cart placeholder instead of the form
- Refactored `engine/explorer.py` to **seed the cart on /products then client-side navigate** to the target via the Next.js `<Link href="/cart">` anchor. CartProvider stays mounted, the seeded item survives the route change. `/cart` and `/checkout` now render their forms during exploration
- Verified the full pipeline runs end-to-end in offline mode: 4 pages × 3 personas explored, gap analyser annotates uncovered nodes, risk scorer ranks, memory layer disables gracefully, report compiles, generated tests directory populates. Findings produced (mostly favicon 404 console errors at this point; the form-validation-bypass detector has a separate false-negative issue noted below)

### Decisions made
- **Decision:** Use `truststore` instead of `pip-system-certs` or `python-certifi-win32` to handle the corp CA chain.
  **Why:** `truststore` is the modern Python-3.10+ standard, supports both the `ssl` module and httpx/aiohttp transitively, and is lighter than the alternatives. Documented in CLAUDE.md §1 indirectly via requirements.
  **Alternatives considered:** Setting `SSL_CERT_FILE` env var to a manually-exported corp CA bundle — rejected because the bundle path varies per machine and would need rotation.

- **Decision:** Keep the OpenRouter config in `.env` (with the user's key) and gate it behind `LLM_OFFLINE=1` while Zscaler blocks the host.
  **Why:** The OpenRouter wiring is correct and will start working immediately when the IT exception is granted (or when run from outside the corp network). Don't make the user re-paste the key. Re-flip `LLM_OFFLINE=0` and the scan goes live.
  **Alternatives considered:** Strip the OpenRouter config and ask user to paste an `sk-ant-*` key for direct Anthropic — rejected: user explicitly wanted OpenRouter.

- **Decision:** Cart-seed via client-side navigation (Next.js Link click) instead of `page.add_init_script` or direct localStorage injection.
  **Why:** The CartProvider's write-effect-on-mount cannot be defeated from outside React without modifying the demo-app source. Click-the-link is the same trick a real user would do — minimal, no code changes to the demo-app.
  **Alternatives considered:** (a) Patch the demo-app's `_app.jsx` to skip the initial write-effect — rejected: demo-app is owned by the user; we shouldn't modify it to make our test agent's life easier. (b) Run the explorer with a shared browser context across all personas/pages seeded once at scan start — rejected: bigger refactor for a future iteration.

- **Decision:** Add canned mocks rather than mock the entire Anthropic SDK call.
  **Why:** The crafted mocks per (persona, page) deliberately exercise the demo-app bugs. They give the dashboard / report meaningful content even with no LLM. The detector and the rest of the agent loop run unchanged. Mocking the SDK call would have produced more realistic API behaviour but worse test data.

- **Decision:** Bump `SCAN_TIMEOUT_SECONDS` from 180 → 600.
  **Why:** Each persona-page now does a ~2–3s cart seed + click navigation + 1–10 persona actions × (8s Playwright fill timeout + 500ms settle + form-validation check + screenshot on anomaly). With 12 (page, persona) combos that's 5–7 minutes. 180s was getting cut at /checkout malicious_user before any other page ran.
  **Alternatives considered:** Make the explorer faster (reuse browser context across personas) — same as the cart-seed alternative above; deferred.

### Blockers encountered (all environmental, not code defects)
- **Blocker:** corp Zscaler proxy blocks `openrouter.ai` and `huggingface.co` at the URL filter, even with truststore-validated TLS. The Anthropic SDK gets the Zscaler "Security Exception" HTML page back from `POST /api/v1/messages` and reports it as `Connection error`.
  **How resolved:** Not resolved at the code level — added `LLM_OFFLINE=1` mode so plumbing can be validated locally. User needs to either (a) file a ServiceNow request via `CS_Corporate Security → Unblock Specific URLs (Zscaler)` for `openrouter.ai`, or (b) point `ANTHROPIC_BASE_URL` at a Cognizant-internal AI gateway that bypasses Zscaler, or (c) use a directly-allowed endpoint (`api.anthropic.com` is reachable — sk-ant-* key needed).
  **Time lost:** ~45 min identifying the block, debugging the wrong axis first (assumed TLS, was actually URL filter).
  **See also:** BUGLOG BUG-005.

- **Blocker:** PowerShell `Out-File` writes UTF-16 LE by default. The first uvicorn log I read was unreadable.
  **How resolved:** Used `-Encoding utf8` explicitly. CLAUDE.md system reminder already warns about this; I missed it on first pass.
  **Time lost:** ~5 min.

- **Blocker:** demo-app `CartProvider` useEffect race clears localStorage on every mount, so `_seed_cart_state` via a separate page didn't survive the explorer's subsequent `page.goto('/checkout')`.
  **How resolved:** Switched to client-side navigation via the Next.js Link anchor. See decisions above.
  **Time lost:** ~25 min tracing the race.
  **See also:** BUGLOG BUG-004.

### What was learned
- `truststore.inject_into_ssl()` is a near-magic single-line fix for corporate networks with a CA in the OS trust store. Should be a near-default for any Python tool that talks HTTPS on a Windows corp machine.
- "Scan completed with 0 findings" is a worse failure mode than "Scan failed with error" — the user can't tell if it's working. The `state["error"]` field added in this session means future ops can render a diagnostic in the dashboard, e.g. "LLM unreachable: every persona action call failed; check ANTHROPIC_BASE_URL".
- The form-validation-bypass detector (`engine/anomaly_detector.py::check_form_validation`) returns `None` when *any* error element is visible, but the demo-app's /checkout shows simultaneous errors for unrelated fields (CVV too short, expiry invalid, etc.). After a click with mixed-validity input, some `.error-message` elements appear → detector misses BUG-004 even when the form does accept the invalid card. Future improvement: scope error visibility to the specific field whose validation was being tested. Not fixed in this session.

### Next session priorities
1. **System-side: file a Zscaler unblock for `openrouter.ai`** (or pick alternative AI endpoint). Without this, the agent cannot exercise real LLM-driven persona behaviour.
2. Once LLM is reachable, flip `.env` `LLM_OFFLINE=0` and re-verify the live flow surfaces more bug types than the offline mocks alone.
3. Form-validation false-negative on /checkout (BUG-004 missed): scope error visibility to the field under test in `engine/anomaly_detector.py::check_form_validation`.
4. Make the explorer share a single browser context across all personas/pages within a scan (massive speed win and removes the cart-seed-per-call cost).

### Session end: 2026-05-18
### Gate status: [PASSED — caveat] Plumbing end-to-end in offline mode. Live LLM blocked by corp network (BUGLOG BUG-005).

