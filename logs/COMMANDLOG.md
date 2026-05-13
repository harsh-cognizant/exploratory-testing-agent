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
