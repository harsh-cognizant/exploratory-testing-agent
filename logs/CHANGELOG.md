# CHANGELOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** 2026-05-13
**Base document:** exploratory_testing_agent_project_plan.md
**Instruction file:** CLAUDE.md

MAJOR = breaking schema/API change · MINOR = new feature or layer · PATCH = fix/refactor

---

## [Unreleased]

## [0.7.0] — 2026-05-14 — Phase 7 gate passed (demo-app out of order)
### Added
- `demo-app/` — Next.js 14 e-commerce SPA on port 3001 (user-provided)
- `demo-app/pages/` — `_app.jsx`, `_document.jsx`, `index.jsx`, `login.jsx`, `products.jsx`, `cart.jsx`, `checkout.jsx`
- `demo-app/styles/globals.css` — custom CSS for class names referenced in JSX (`.header`, `.container`, `.card`, `.product-grid`, `.btn`, etc.)
- `demo-app/next.config.js`, `tailwind.config.js`, `postcss.config.js`
- `demo-app/README.md`, `demo-app/BUGS_EXPLAINED_SIMPLE.md` (ship with the app)
- Two additional bugs documented (BUG-005, BUG-006) — already present in code, previously unflagged

### Changed
- CLAUDE.md §2 — demo-app subtree updated: lowercase Next.js page filenames, full file list incl. `_app.jsx`/`_document.jsx`/`index.jsx`/`styles/globals.css` and config files
- CLAUDE.md §10 — rewritten as "Pre-Planted Bug Catalogue" (was "Implementation Guide"); data-testids corrected to match shipped app (`login-button` not `login-btn`, `place-order-btn` not `pay-now-btn`, suffixed ids like `add-to-cart-btn-{id}`, `quantity-input-{id}`, etc.); per-bug detail aligned to actual JSX

### Notes
- Phase 7 done out of plan order because the user supplied a complete demo-app. Phases 2–6 still pending.
- npm install resolved 380+ packages (Next.js 14.0.0, React 18.2.0, Tailwind 3.3.5). Dev server starts cleanly; `/`, `/products`, `/login`, `/cart`, `/checkout` all return 200.
- `/cart` and `/checkout` render an empty-state message when cart is empty — their form testids are conditional. Phase 2 crawler must seed cart state (e.g. click Add-to-Cart on one product) before crawling those routes to discover all elements.
- The dashboard's CORS allow_origins still targets `localhost:3000` (per CLAUDE.md §4.5); demo-app on `localhost:3001` is the *target*, not a CORS origin.

## [0.1.0] — 2026-05-13 — Phase 1 gate passed
### Added
- CLAUDE.md instruction file (2632 lines) authored by user, reviewed and edited
- `requirements.txt`, `.env.example`, `.gitignore`
- `logs/` directory with all four log files initialised
- `api/models.py` with full Pydantic model set per CLAUDE.md §4.4
- `api/__init__.py`, `api/routes/__init__.py` and seven route stubs (`scan`, `scan_status`, `graph`, `queue`, `findings`, `memory_routes`, `report`)
- `api/main.py` with CORS, static-file mount for `/screenshots`, and `/health` endpoint
- `data/simulated_defect_history.csv`, `data/simulated_change_frequency.csv` (data per CLAUDE.md §4.8)
- `data/existing_tests_mock.json`
- Python virtual environment at `./venv/` (Python 3.13.2, gitignored)
- Installed all 16 deps from requirements.txt (resolved to: anthropic 0.101.0, fastapi 0.136.1, chromadb 1.5.9, sentence-transformers 5.5.0, torch 2.11.0, langgraph 1.2.0, playwright 1.59.0, networkx 3.6.1, pydantic 2.13.4, uvicorn 0.46.0, etc.)

### Changed
- CLAUDE.md hard constraints: model ID standardised to `claude-sonnet-4-6`; Windows/PowerShell compatibility and `ANTHROPIC_API_KEY` Windows-fallback rules added; folder root corrected to `Exploratory_Testing_Agent/`
- CLAUDE.md §§4.4, 4.12, 4.13, 4.16, 7: orchestration, persona, gap-analyser, and schema sections aligned (clamping rule, retry policy, batching, action-type closed set, timeout termination, `has_memory` lifecycle)
- CLAUDE.md §§14–20 condensed from ~570 lines of templates to a directive logging checklist
- CHANGELOG milestone version `1.0.0 → 0.9.0` (reserve 1.0.0 for post-hackathon)

### Notes
- GATE 1 PASSED at 2026-05-13. `uvicorn api.main:app --port 8000` starts cleanly; `GET /health` returns `{"status":"ok","service":"exploratory-agent"}`; spot-check confirms `/graph`, `/queue`, `/findings`, `/memory` stubs respond 200 with empty/zeroed payloads matching CLAUDE.md §6 contracts.
- Working branch: `dev` (master untouched per user instruction).

## [0.0.0] — 2026-05-13
### Initialised
- Project scaffolded from CLAUDE.md instruction file
- Log files created: CHANGELOG.md, DEVLOG.md, COMMANDLOG.md, BUGLOG.md
- Working branch: `dev` (master kept clean; no merge to master without explicit approval)
