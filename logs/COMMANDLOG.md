# COMMANDLOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** 2026-05-13

Append-only chronological record of every terminal command run.

---

### 2026-05-13 — Create and push `dev` branch
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `git checkout -b dev`
**Exit code:** 0
**Output summary:** Switched to a new branch 'dev'
**Result:** SUCCESS

---

### 2026-05-13 — Push `dev` to origin and set upstream
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `git push -u origin dev`
**Exit code:** 0
**Output summary:** `[new branch] dev -> dev`; tracking `origin/dev`
**Result:** SUCCESS

---

### 2026-05-13 — Initial line count of CLAUDE.md (pre-edit)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `wc -l CLAUDE.md`
**Exit code:** 0
**Output summary:** 2920 lines
**Result:** SUCCESS

---

### 2026-05-13 — Post-edit line count of CLAUDE.md
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `wc -l CLAUDE.md`
**Exit code:** 0
**Output summary:** 2632 lines (≈10% smaller after §§14–20 collapse)
**Result:** SUCCESS

---

### 2026-05-13 — Probe Python toolchain
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `python --version; python -m pip --version; (Get-Command python).Source`
**Exit code:** 0
**Output summary:** Python 3.13.2, pip 26.0.1, `C:\Program Files\Python313\python.exe`. No venv present yet.
**Result:** SUCCESS

---

### 2026-05-13 — Create Python virtual environment
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `python -m venv venv`
**Exit code:** 0
**Output summary:** `.\venv\` created with `Scripts\python.exe`. Confirmed via `Test-Path .\venv\Scripts\python.exe` → `True`.
**Result:** SUCCESS

---

### 2026-05-13 — Upgrade pip inside venv
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `.\venv\Scripts\python.exe -m pip install --upgrade pip`
**Exit code:** 0
**Output summary:** Uninstalled pip 24.3.1, installed pip 26.1.1.
**Result:** SUCCESS

---

### 2026-05-13 — Install all requirements (Phase 1 deps + future-phase deps)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `.\venv\Scripts\python.exe -m pip install -r requirements.txt`
**Exit code:** 0
**Output summary:** Installed 130+ packages incl. anthropic 0.101.0, fastapi 0.136.1, chromadb 1.5.9, sentence-transformers 5.5.0, torch 2.11.0, langgraph 1.2.0, playwright 1.59.0, networkx 3.6.1, pydantic 2.13.4, uvicorn 0.46.0, pytest 9.0.3, pytest-playwright 0.7.2, scikit-learn 1.8.0, pandas 3.0.3, numpy 2.4.4, python-dotenv 1.2.2, httpx 0.28.1.
**Result:** SUCCESS — backgrounded; took ≈10 minutes including torch download.
**Notes:** Resolved versions are far newer than the `>=` floors in `requirements.txt`. Future phase code should target the resolved API surface.

---

### 2026-05-13 — Start uvicorn (Phase 1 Gate 1 verification)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `.\venv\Scripts\python.exe -m uvicorn api.main:app --port 8000 --log-level info`
**Exit code:** — (background process, still running)
**Output summary:** `INFO: Started server process [23148]` → `Application startup complete` → `Uvicorn running on http://127.0.0.1:8000`. CORS configured for `http://localhost:3000`. Static mount `/screenshots` active. All 7 routers registered.
**Result:** SUCCESS

---

### 2026-05-13 — Hit /health and verify read-only stubs (Gate 1 main check)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `Invoke-RestMethod http://127.0.0.1:8000/health` (plus spot-check of `/graph`, `/queue`, `/findings`, `/memory`)
**Exit code:** 0
**Output summary:**
- `GET /health` → `{"status":"ok","service":"exploratory-agent"}`
- `GET /graph` → 200, `stats.total_nodes = 0`
- `GET /queue` → 200, 0 items
- `GET /findings` → 200, 0 findings, `summary.total = 0`
- `GET /memory` → 200, `total_findings_in_memory = 0`
**Result:** SUCCESS — GATE 1 PASSED
**Notes:** Polling `localhost:8000` returned ECONNREFUSED while uvicorn was still binding; polling `127.0.0.1:8000` succeeded immediately after `Application startup complete`. Lesson: prefer `127.0.0.1` in startup polling code.

---

### 2026-05-14 — Check node/npm toolchain
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `node --version; npm --version`
**Exit code:** 0
**Output summary:** Node v24.13.0, npm 11.6.2.
**Result:** SUCCESS

---

### 2026-05-14 — Copy user-supplied demo-app into project (Phase 7a)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** PowerShell `Copy-Item` of `_app.jsx`, `login.jsx`, `products.jsx`, `cart.jsx`, `checkout.jsx`, `package.json`, `README.md`, `BUGS_EXPLAINED_SIMPLE.md` from `Hackathon\demo-app\` (source) to `Exploratory_Testing_Agent\demo-app\pages\` and `Exploratory_Testing_Agent\demo-app\` (dest)
**Exit code:** 0
**Output summary:** 8 files copied into the proper Next.js pages-router structure.
**Result:** SUCCESS

---

### 2026-05-14 — npm install in demo-app
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent\demo-app`
**Command:** `npm install`
**Exit code:** 0
**Output summary:** 380+ packages resolved (next 14.0.0, react 18.2.0, react-dom 18.2.0, tailwindcss 3.3.5, postcss 8.4.31, autoprefixer 10.4.16). Ran in background (≈90 s).
**Result:** SUCCESS

---

### 2026-05-14 — Start demo-app dev server (Phase 7d)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent\demo-app`
**Command:** `npm run dev` (runs `next dev -p 3001`)
**Exit code:** — (background process)
**Output summary:** Next.js 14.0.0 ready on `http://localhost:3001`.
**Result:** SUCCESS

---

### 2026-05-14 — Verify all 5 demo-app routes (Phase 7 Gate)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent\demo-app`
**Command:** `Invoke-WebRequest` against `/`, `/products`, `/login`, `/cart`, `/checkout`
**Exit code:** 0
**Output summary:**
- `/` 200 (2013 bytes, loading splash before client-side redirect to `/products`)
- `/products` 200 (5222 bytes, 21 data-testids — 6 products × 3 + cart-count + cart-count-display + product-page-cart-count + bug-explanation)
- `/login` 200 (2940 bytes, 3 testids — email-input, password-input, login-button)
- `/cart` 200 (2193 bytes, 0 testids — empty-cart state, no form rendered)
- `/checkout` 200 (2176 bytes, 0 testids — empty-cart state, no form rendered)
**Result:** SUCCESS — GATE 7 PASSED
**Notes:** Empty-cart conditional rendering means `/cart` and `/checkout` only expose their form testids after cart is seeded. The Phase 2 crawler must Add-to-Cart at least one product before crawling those routes.

---

### 2026-05-14 14:08 — Smoke-test risk_scorer offline against 6-page graph
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `.\venv\Scripts\python.exe _smoke_risk.py` (temp script, deleted after)
**Exit code:** 0
**Output summary:**
- `#1 node_checkout    score=1.0000 band=critical`
- `#2 node_cart        score=0.6438 band=high`
- `#3 node_login       score=0.6042 band=high`
- `#4 node_profile     score=0.3771 band=low`
- `#5 node_products    score=0.3229 band=low`
- `#6 node_search      score=0.1937 band=low`
**Result:** SUCCESS — matches hand-computed values exactly; weights sum to 1.0; formula clamps applied; band thresholds (`>=0.8`/`>=0.6`/`>=0.4`/`<0.4`) honoured.
**Notes:** Temp script `_smoke_risk.py` removed after success (`.gitignore` covers `/_*.py` so it never reached git anyway).

---

### 2026-05-14 14:09 — Start FastAPI for Gate 3
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `.\venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --log-level info`
**Exit code:** — (run_in_background; stopped via TaskStop after gate)
**Output summary:** Uvicorn bound 127.0.0.1:8000; `/health` returned `{"status":"ok","service":"exploratory-agent"}`.
**Result:** SUCCESS

---

### 2026-05-14 14:09 — POST /scan against demo-app (Phase 3 Gate)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/scan -ContentType 'application/json' -Body '{"app_url":"http://127.0.0.1:3001"}'`
**Exit code:** 0
**Output summary:** `{"scan_id":"scan_20260514_140944","status":"started","estimated_duration_seconds":120}`
**Result:** SUCCESS

---

### 2026-05-14 14:10 — Poll /scan/{id}/status until completed
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `for i in 1..20; curl -s http://127.0.0.1:8000/scan/scan_20260514_140944/status; sleep 3` (bash loop)
**Exit code:** 0
**Output summary:** `t=1: {...,"status":"completed","progress_percent":100,"nodes_total":16,...}` (loop broke on first iteration)
**Result:** SUCCESS — scan completed in <3s end-to-end (no Claude calls needed for Phase 3 since gap analysis fails open and risk scoring is local-CSV-driven).
**Notes:** First polling attempt used `cat .gate3_scan_id` whose contents had a UTF-8 BOM (PowerShell `Set-Content -Encoding utf8` writes BOM in PS 5.1) — silent URL corruption. Fixed by hardcoding scan_id.

---

### 2026-05-14 14:10 — GET /queue (Phase 3 Gate)
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `curl -s "http://127.0.0.1:8000/queue?scan_id=scan_20260514_140944"`
**Exit code:** 0
**Output summary:** 16-item ranked queue. Top entries (rank: node_id, score, band):
- #1 `node_checkout` 1.0000 critical
- #2 `node_checkout_continue_shopping` 1.0000 critical
- #3 `node_cart` 0.6438 high
- #5 `node_login` 0.6042 high
- #10..#16 `/products` family 0.3229 low
**Result:** SUCCESS — GATE 3 PASSED. `/checkout` at #1 and `/login` in top 5, formula applied (not default 0.5), distinct scores per distinct URL.

---

### 2026-05-14 14:11 — GET /queue?risk_band=critical and ?risk_band=high
**Directory:** `c:\Users\2437925\OneDrive - Cognizant\Desktop\Hackathon\Exploratory_Testing_Agent`
**Command:** `curl -s "http://127.0.0.1:8000/queue?risk_band=critical"` and `curl -s "http://127.0.0.1:8000/queue?risk_band=high"`
**Exit code:** 0
**Output summary:** `critical` → 2 items (both `/checkout`), `high` → 7 items (cart family + login family), `low` → 7 items (products family).
**Result:** SUCCESS — filter contract honoured.

---

### 2026-05-14 14:12 — Stop FastAPI server
**Directory:** —
**Command:** TaskStop on background uvicorn (task_id `bkpsdv8v9`)
**Exit code:** —
**Output summary:** Successfully stopped.
**Result:** SUCCESS
