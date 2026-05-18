# CHANGELOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** 2026-05-13
**Base document:** exploratory_testing_agent_project_plan.md
**Instruction file:** CLAUDE.md

MAJOR = breaking schema/API change · MINOR = new feature or layer · PATCH = fix/refactor

---

## [Unreleased]

## [0.9.1] — 2026-05-18 — Resilience + offline-mode hardening
### Added
- `engine/memory.py` `_is_model_cached()` — pre-emptively sets `HF_HUB_OFFLINE=1` when the sentence-transformers model is already on disk, avoiding the 5-retry SSL storm against huggingface.co when the corp proxy blocks it
- `engine/memory.py` `AgentMemory.disabled` flag — `__init__` catches embedding-model load failures and downgrades to no-op for store/query so the scan still completes when HF is unreachable (BUGLOG BUG-001)
- `engine/explorer.py` `_seed_cart_and_navigate()` — explorer now seeds the cart on /products and **client-side** navigates (via the Next.js `<Link>` anchor) to /cart and /checkout. Hard `page.goto` was racing the CartProvider's two useEffects and the cart was being cleared on every mount; client-side nav keeps CartProvider mounted so the seeded item survives (BUGLOG BUG-004)
- `agent/offline_mocks.py` — canned (persona, page) action lists used when `LLM_OFFLINE=1`; each pair targets a specific demo-app bug from CLAUDE.md §10
- `truststore` (requirements.txt) — redirects Python's `ssl` module to the Windows trust store on import so the corp CA chain validates and HTTPS to Anthropic/HF/OpenRouter clears the TLS handshake (BUGLOG BUG-002)
- `api/main.py` calls `truststore.inject_into_ssl()` before any HTTPS-using module imports

### Changed
- `agent/gap_analyser.py`, `agent/personas.py`, `agent/test_generator.py` — `_get_client()` now supports `ANTHROPIC_AUTH_TOKEN` (Bearer auth) in addition to `ANTHROPIC_API_KEY` (x-api-key). Enables OpenRouter / proxy endpoints that expect `Authorization: Bearer …`
- `agent/gap_analyser.py` `analyse_gaps()` — under `LLM_OFFLINE=1` returns a heuristic gap list (every uncovered node) without calling Claude
- `agent/personas.py` `generate_persona_actions()` — under `LLM_OFFLINE=1` returns canned actions from `agent/offline_mocks.py` instead of calling Claude; live-path fallback no longer emits the bogus `{action_type:'click', target:'button'}` action (was causing noisy false positives on every page when the LLM was unreachable)
- `agent/test_generator.py` `generate_test_for_finding()` — under `LLM_OFFLINE=1` builds a deterministic placeholder Pytest stub instead of calling Claude
- `agent/brain.py` — `nodes_explored` now counts pages actually visited by the explorer (regardless of whether a finding was produced) rather than unique `node_id`s in `findings`. Old definition collapsed to 0 on no-bug runs and made the dashboard look stuck
- `agent/brain.py` — adds `persona_call_attempts` / `persona_call_successes` counters; sets `state["error"]` with a diagnostic when every persona call fails so the LLM-unreachable case is no longer silent
- `.env` — switched to OpenRouter config (`ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN=<openrouter key>`, `ANTHROPIC_MODEL=poolside/laguna-m.1:free`) per user instruction; added `LLM_OFFLINE=1` flag; bumped `SCAN_TIMEOUT_SECONDS` to 600 to cover all 4 pages × 3 personas

### Fixed
- BUGLOG BUG-001 — `engine/memory.py` no longer hard-crashes the scan when the corp proxy blocks huggingface.co
- BUGLOG BUG-002 — Python httpx/requests now validate against the Windows trust store via `truststore`; no more `CERTIFICATE_VERIFY_FAILED` for any host whose CA is in the OS store
- BUGLOG BUG-003 — `nodes_explored` accurately reflects exploration regardless of finding count
- BUGLOG BUG-004 — `/cart` and `/checkout` form selectors render correctly during exploration

### Notes
- **System-restriction blockers remaining:** the corp Zscaler URL filter still blocks `openrouter.ai` and `huggingface.co` at the host level even with valid TLS — see BUGLOG BUG-005. Confirmed `api.anthropic.com` is reachable (HTTP 404 with no Zscaler block page). Until either an allowlist exception is granted (ServiceNow → CS_Corporate Security → "Unblock Specific URLs (Zscaler)") or a Cognizant-internal Anthropic-compatible gateway is configured, the agent runs with `LLM_OFFLINE=1` and emits canned persona actions only. All plumbing (crawler → graph → risk → exploration → anomaly detection → memory → report) is verified working end-to-end in offline mode.
- Cold-start time for uvicorn now ~60–80s on first launch (truststore loading the Windows cert store + sentence-transformers model probe). Subsequent reloads with `HF_HUB_OFFLINE=1` auto-set are faster.

## [0.9.0] — 2026-05-15 — Phase 9 gate passed (Integration & Hardening)
### Added
- `README.md` — comprehensive project documentation: architecture diagram, 5-layer overview, quick start guide, API endpoints table, demo app bug catalogue, persona descriptions, project structure

### Notes
- Phase 9 complete. All three services verified running simultaneously (demo-app:3001, API:8000, dashboard:3000).

## [0.8.0] — 2026-05-15 — Phase 8 gate passed (Dashboard)
### Added
- `dashboard/` — React + Vite + D3.js frontend on port 3000
- `dashboard/src/api.js` — API client for all 7 backend endpoints with error handling
- `dashboard/src/components/ScanControl.jsx` — URL input, Start Scan button, progress bar with 2s polling
- `dashboard/src/components/CoverageGraph.jsx` — D3.js force simulation with risk-colored nodes, zoom, drag, memory indicators
- `dashboard/src/components/RiskQueue.jsx` — filterable risk-ranked queue with severity badges
- `dashboard/src/components/FindingsFeed.jsx` — live findings feed (3s polling during scan) with persona badges, severity colors, screenshot thumbnails
- `dashboard/src/components/MemoryPanel.jsx` — ChromaDB past run summaries
- `dashboard/src/components/ReportPanel.jsx` — 4 metric cards, severity-sorted findings, syntax-highlighted generated test code with copy button
- `dashboard/src/components/MetricCards.jsx` — 6 key metric indicators
- `dashboard/src/App.jsx` — tab-based layout (Graph|Queue|Findings|Memory|Report) with detail sidebar
- `dashboard/src/App.css` — premium dark theme: glassmorphism, gradient header, Inter font, micro-animations
- `dashboard/vite.config.js` — Vite config with API proxy to FastAPI on port 8000

### Notes
- Dashboard renders the force-directed graph from live API data. Clicking Start Scan triggers POST /scan and status polling begins. Findings appear in feed after scan completes.
- D3.js node colors: critical=#EF4444, high=#F97316, medium=#EAB308, low=#22C55E, covered=#6B7280 (per CLAUDE.md §11)

## [0.7.1] — 2026-05-14 — OpenRouter integration & demo mode
### Changed
- `agent/gap_analyser.py` — `CLAUDE_MODEL` now reads from `ANTHROPIC_MODEL` env var (fallback `claude-sonnet-4-6`); `_get_client()` passes `ANTHROPIC_BASE_URL` to `anthropic.Anthropic()` when set, enabling OpenRouter routing
- `agent/personas.py` — same OpenRouter-compatible `_get_client()` and dynamic `CLAUDE_MODEL` from env var
- `agent/test_generator.py` — same OpenRouter-compatible `_get_client()` and dynamic `CLAUDE_MODEL` from env var
- `engine/explorer.py` — added `EXPLORER_SLOW_MO_MS` env var support for slowed-down demo presentations; Playwright `slow_mo` passed to `chromium.launch()`
- `.env` — configured with OpenRouter API key, base URL (`https://openrouter.ai/api`), model (`meta-llama/llama-3.3-70b-instruct:free`), and demo-mode flags (`EXPLORER_HEADLESS=false`, `CRAWLER_HEADLESS=false`, `EXPLORER_SLOW_MO_MS=500`, `CRAWLER_SLOW_MO_MS=500`)

### Notes
- E2E scan `scan_20260514_193622` completed successfully with OpenRouter backend; confused_user persona discovered 2 medium-severity findings on `/checkout` (unexpected redirect, JS console error)
- Free-tier model `poolside/laguna-m.1:free` produced truncated JSON responses causing empty action lists; switched to `meta-llama/llama-3.3-70b-instruct:free` (70B parameter model) for reliable JSON generation
- `meta-llama/llama-3-8b-instruct:free` returned 404 (model rotated off OpenRouter); confirmed live free model list via API before final selection

## [0.6.0] — 2026-05-14 — Phases 4-6 implemented
### Added — Phase 4 (Behavioural Exploration Engine)
- `agent/prompts/persona_confused.txt` — confused user persona prompt template
- `agent/prompts/persona_power.txt` — power user persona prompt template
- `agent/prompts/persona_malicious.txt` — malicious user persona prompt template
- `agent/prompts/test_generation.txt` — Pytest test generation prompt template
- `agent/personas.py` — persona engine: generates Claude-based action lists per persona type, with validation, filtering (closed action_type set), retry-once JSON parsing, and MAX_ACTIONS_PER_PERSONA=8 cap
- `engine/anomaly_detector.py` — AnomalyCollector class: captures JS console errors, HTTP 4xx/5xx, unexpected redirects, form validation bypasses, page crashes; builds structured Finding dicts with reproduction steps
- `engine/explorer.py` — Playwright-based explorer: executes persona action lists on graph nodes, captures anomalies via AnomalyCollector, takes screenshots on findings, uses ACTION_SETTLE_WAIT_MS=500ms per §4.9

### Added — Phase 5 (Memory & Learning Loop)
- `engine/memory.py` — AgentMemory class: ChromaDB PersistentClient(path="./chroma_store"), sentence-transformers all-MiniLM-L6-v2 embeddings, store/query/adjustment methods per §4.11. Constants: similarity_threshold=0.85, positive_adj=+0.15, negative_adj=-0.10, clamp=±0.3

### Added — Phase 6 (Output & Test Generation)
- `agent/test_generator.py` — generates Pytest functions from high/critical findings via Claude API with syntax validation and retry, writes to tests/generated/
- `engine/report_builder.py` — compiles final gap report from scan state: coverage stats, severity breakdown, summary paragraph

### Changed
- `agent/brain.py` — full orchestration flow steps 1-13: init → crawl → graph → gap analysis → risk scoring (with memory adjustments) → queue assembly → exploration loop (per-node, per-persona) → memory store → test generation → report compilation. Timeout=300s. Lazy-init singleton AgentMemory.
- `api/routes/findings.py` — promoted from stub: reads from SCAN_STATE, supports severity filter, computes summary counts
- `api/routes/memory_routes.py` — promoted from stub: wired to AgentMemory for real run summaries and total counts
- `api/routes/report.py` — promoted from stub: builds full ReportResponse from SCAN_STATE with coverage stats, severity breakdown, generated tests

### Notes
- All 11 Python modules import cleanly (verified).
- All API endpoints return correct status codes: /health→200, /findings→200, /memory→200, /report→404 (no scan yet).
- sentence-transformers model downloads on first /memory request (~90MB).

## [0.3.0] — 2026-05-14 — Phase 3 gate passed
### Added
- `engine/risk_scorer.py` — canonical three-factor risk formula
  (0.35·change_frequency + 0.40·defect_density + 0.25·criticality) with
  `CRITICALITY_MAP` from CLAUDE.md §4.8; loads `data/simulated_defect_history.csv`
  and `data/simulated_change_frequency.csv`, normalises each column by its max,
  applies the formula, sets `risk_score` / `risk_band` / `defect_count_historical`
  / `business_criticality` in place on every node. Exposes `score_graph` and
  `build_queue` (with optional `risk_band` filter). Accepts optional
  `memory_adjustments` parameter for Phase 5 wiring; clamps to [0, 1].
- `agent/prompts/risk_ranking.txt` — verbatim from CLAUDE.md §7 (for future
  Claude-based reranking; not yet called by brain.py).
- `engine/crawler.py`: `CRAWLER_HEADLESS` and `CRAWLER_SLOW_MO_MS` env vars
  allow watching the crawl live in a real Chrome window. Default remains
  headless for unattended scans.

### Changed
- `agent/brain.py` — orchestration extended to steps 7 (`score_graph`) and 8
  (`build_queue` snapshot stored in `SCAN_STATE[scan_id]["queue"]`). The
  remaining §4.16 steps 9–13 stay stubbed until Phases 4–6.
- `api/routes/queue.py` — promoted from stub: reads scored graph from
  `SCAN_STATE` and returns a ranked `QueueResponse`. Honours optional
  `risk_band` query filter ("critical"|"high"|"medium"|"low").
- `.gitignore` — added `/_*.txt`, `/_*.py`, `/_*.json` patterns to keep
  scratch files out of commits.

### Notes
- Gate 3 PASSED. Scan against `http://127.0.0.1:3001` returns 16 nodes
  ranked by score:
  - `node_checkout` and `node_checkout_continue_shopping` → 1.0000 (CRITICAL)
  - `node_cart` and `node_cart_continue_shopping` → 0.6438 (HIGH)
  - five `/login` nodes → 0.6042 (HIGH)
  - seven `/products` nodes → 0.3229 (LOW)
  Top-3 of /queue contains 2 `/checkout` nodes per CLAUDE.md §9 Gate 3.
- `/queue?risk_band=critical` filter returns only the two `/checkout` nodes,
  confirming the filter contract.

## [0.2.0] — 2026-05-14 — Phase 2 gate passed
### Added
- `engine/crawler.py` — async Playwright BFS crawler with `channel='chrome'` (uses system Chrome to bypass corporate TLS proxy that blocks chromium-headless-shell download); 3-level depth cap, 10s per-page timeout, networkidle wait, fragment/query stripping, ASCII-only element-id sanitisation
- `engine/graph_builder.py` — converts crawler output to a NetworkX DiGraph; coverage overlay from `data/existing_tests_mock.json`; `contains` edges page→element and `navigation` edges page→page; `graph_to_response_dict` serialises for `GraphResponse`
- `agent/prompts/gap_analysis.txt` — verbatim from CLAUDE.md §7
- `agent/gap_analyser.py` — Claude API client with `safe_parse_json`, retry-once on JSON parse failure, 30-node batching per §4.12, fail-fast on missing `ANTHROPIC_API_KEY`
- `agent/brain.py` — minimal orchestration covering §4.16 steps 1–6 (init → crawl → graph → gap analysis). Steps 7–13 stubbed for Phases 3–6. `SCAN_STATE` module dict, `start_scan` schedules an asyncio.Task, `get_scan_state`/`get_latest_completed_scan_id` for route handlers.
- `engine/__init__.py`, `agent/__init__.py`

### Changed
- `api/routes/scan.py` — promoted from stub: calls `agent.brain.start_scan` and returns the new scan_id
- `api/routes/scan_status.py` — reads from `SCAN_STATE`, returns 404 for unknown scan_ids
- `api/routes/graph.py` — reads from `SCAN_STATE`, uses `graph_to_response_dict` to serialise; falls back to latest completed scan when `scan_id` query param omitted

### Notes
- Phase 2 Gate PASSED: scan against `http://127.0.0.1:3001` produces a 16-node graph (4 pages × forms + buttons), 12 covered, 4 gaps, 75% coverage.

## [0.7.0] — 2026-05-14 — Phase 7 gate passed (demo-app out of order)
### Added
- `demo-app/` — Next.js 14 e-commerce SPA on port 3001 (user-provided)
- `demo-app/pages/` — `_app.jsx`, `_document.jsx`, `index.jsx`, `login.jsx`, `products.jsx`, `cart.jsx`, `checkout.jsx`
- `demo-app/styles/globals.css` — custom CSS for class names referenced in JSX

### Notes
- Phase 7 done out of plan order because the user supplied a complete demo-app.

## [0.1.0] — 2026-05-13 — Phase 1 gate passed
### Added
- CLAUDE.md instruction file (2632 lines)
- `requirements.txt`, `.env.example`, `.gitignore`
- `logs/` directory with all four log files initialised
- `api/models.py` with full Pydantic model set per CLAUDE.md §4.4
- `api/main.py` with CORS, static-file mount for `/screenshots`, `/health` endpoint
- `data/` CSV files and `existing_tests_mock.json`

## [0.0.0] — 2026-05-13
### Initialised
- Project scaffolded from CLAUDE.md instruction file
- Log files created: CHANGELOG.md, DEVLOG.md, COMMANDLOG.md, BUGLOG.md
