# CHANGELOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** 2026-05-13
**Base document:** exploratory_testing_agent_project_plan.md
**Instruction file:** CLAUDE.md

MAJOR = breaking schema/API change · MINOR = new feature or layer · PATCH = fix/refactor

---

## [Unreleased]

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
