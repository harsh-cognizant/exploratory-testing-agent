# CLAUDE.md — Exploratory Testing & Coverage Gap Discovery Agent
## Instruction File for Claude Code

> This file is the single source of truth for building this project.
> Read it completely before writing any code. Refer back to it whenever making a decision.
> Never deviate from the schemas, file paths, API contracts, or architectural boundaries defined here.

---

## 0. How to Use This File

This instruction file governs the entire build. It is structured as follows:

- **Section 1** — Project identity and non-negotiable constraints
- **Section 2** — Exact folder structure to create
- **Section 3** — Build order (never skip ahead)
- **Section 4** — Every file with its exact purpose, inputs, outputs, and implementation rules
- **Section 5** — All data schemas (node, edge, finding, memory, report) — copy these exactly
- **Section 6** — All API endpoint contracts — implement exactly as specified
- **Section 7** — All prompt templates — use verbatim
- **Section 8** — Anti-hallucination rules — read before every file you write
- **Section 9** — Testing and verification gates — must pass before moving on
- **Section 10** — Demo app bug implementation guide
- **Section 11** — Dashboard component behaviour
- **Section 12** — Error handling standards
- **Section 13** — Quick reference table
- **Section 14** — Logging system overview and log file index
- **Section 15** — CHANGELOG.md format and update rules
- **Section 16** — DEVLOG.md format and update rules
- **Section 17** — COMMANDLOG.md format and update rules
- **Section 18** — BUGLOG.md format and update rules
- **Section 19** — Sync rules: when to update which files simultaneously
- **Section 20** — Log file bootstrap (Windows / PowerShell)
- **Section 21** — Python coding standards (all backend files)
- **Section 22** — JavaScript / React coding standards (all frontend files)
- **Section 23** — General code quality rules (applies to every file)

When asked to build a specific file, always:
1. Re-read the relevant section of this file first
2. Check the schema for any data structures the file produces or consumes
3. Check the API contract if the file exposes or calls an endpoint
4. Write the file
5. Run the verification gate for that phase before moving on
6. **Apply coding standards** — Section 21 for Python, Section 22 for JS/React, Section 23 for all files
7. **Update the appropriate log files** — see Section 19 for which logs to update after each action

---

## 1. Project Identity & Non-Negotiable Constraints

### What This Project Is

An AI agent that autonomously explores a web application, discovers untested areas (coverage gaps), and generates Pytest test cases for everything it finds. It does NOT run existing tests. It DISCOVERS missing tests.

### Five Layers — Always Build in This Order

```
Layer 1: Coverage Intelligence Graph   → NetworkX graph of all app routes/elements
Layer 2: Risk Prioritisation Engine    → Score and rank gaps by risk
Layer 3: Behavioural Exploration       → Playwright + 3 personas explores the app
Layer 4: Memory & Learning Loop        → ChromaDB remembers findings across runs
Layer 5: Output & Test Generation      → Claude API generates Pytest test cases
```

### Hard Constraints — Never Violate These

- **Model:** Always use `claude-sonnet-4-6` (the Sonnet 4.6 model ID) for every Claude API call — reasoning, gap analysis, risk ranking, persona action generation, and test generation. Never hardcode an older snapshot ID (e.g. `claude-sonnet-4-20250514`) and never use a vendor-neutral placeholder. Update to a newer 4.x build (e.g. when `claude-sonnet-4-7` ships) only after verifying the ID resolves against the Anthropic API.
- **ChromaDB:** Always use `chromadb.PersistentClient(path="./chroma_store")`. Never use `chromadb.Client()` — it is deprecated and does not persist across runs.
- **Ports:** demo-app=3001, dashboard=3000, FastAPI=8000. Never change these.
- **Schemas:** Every data structure (Node, Edge, Finding, MemoryEntry, Report) must match the exact schemas in Section 5. Never add or remove fields without updating all consumers.
- **API contracts:** Every endpoint must match Section 6 exactly. Never rename endpoints, change HTTP methods, or change field names in responses.
- **File placement:** `memory.py` lives in `engine/` only. The `api/routes/memory_routes.py` only imports from it — never duplicates logic.
- **Async:** `explorer.py` runs Playwright asynchronously. Use `async def` and `asyncio`. Never block the FastAPI event loop.
- **Environment variables:** API keys always come from `.env` via `python-dotenv`. Never hardcode keys. Never commit `.env`.
- **Risk formula:** `risk_score = (0.35 × change_frequency) + (0.40 × defect_density) + (0.25 × criticality)`. Weights must sum to 1.0. Never change the weights without updating the formula comment.
- **Pytest output:** Generated tests go to `tests/generated/`. Never put them anywhere else.
- **Screenshots:** Saved to `screenshots/` at project root. FastAPI serves them as static files at `/screenshots/`.
- **Windows compatibility:** This repo is developed on Windows 11 with PowerShell. Use `pathlib.Path()` for every Python path join — never hardcode `/` or `\`. For shell commands in this doc, examples, or generated scripts, prefer the PowerShell form: `venv\Scripts\activate` (not `source venv/bin/activate`), `$env:VAR='value'` (not `export VAR=value`), `Remove-Item -Recurse -Force` (not `rm -rf`), `New-Item -ItemType Directory -Force` (not `mkdir -p`). When a bash form is unavoidable, mark it explicitly as `# bash only`.
- **ANTHROPIC_API_KEY:** Must be set before starting any server. Pick one of: (a) create a `.env` file in repo root containing `ANTHROPIC_API_KEY=<key>` and load it via `python-dotenv`, or (b) set a PowerShell user-scoped env var: `[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','<key>','User')`. Never commit `.env` (it is in `.gitignore`); only `.env.example` is committed. The agent must fail fast with a clear error if the key is missing.

---

## 2. Exact Folder Structure

Create this structure exactly. Do not add, rename, or move folders.
The repo root on disk is `Exploratory_Testing_Agent/` — match this in all path examples elsewhere in this doc.

```
Exploratory_Testing_Agent/
│
├── agent/
│   ├── __init__.py
│   ├── brain.py
│   ├── personas.py
│   ├── gap_analyser.py
│   ├── test_generator.py
│   └── prompts/
│       ├── gap_analysis.txt
│       ├── risk_ranking.txt
│       ├── persona_confused.txt
│       ├── persona_power.txt
│       ├── persona_malicious.txt
│       └── test_generation.txt
│
├── engine/
│   ├── __init__.py
│   ├── crawler.py
│   ├── graph_builder.py
│   ├── risk_scorer.py
│   ├── explorer.py
│   ├── anomaly_detector.py
│   ├── memory.py
│   └── report_builder.py
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── routes/
│       ├── __init__.py
│       ├── scan.py
│       ├── scan_status.py
│       ├── graph.py
│       ├── queue.py
│       ├── findings.py
│       ├── memory_routes.py
│       └── report.py
│
├── dashboard/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
│           ├── ScanControl.jsx
│           ├── CoverageGraph.jsx
│           ├── RiskQueue.jsx
│           ├── FindingsFeed.jsx
│           ├── MemoryPanel.jsx
│           ├── ReportPanel.jsx
│           └── MetricCards.jsx
│
├── demo-app/                ← Next.js 14 pages-router, port 3001
│   ├── package.json
│   ├── next.config.js
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── README.md            ← bug repro guide, ships with the app
│   ├── BUGS_EXPLAINED_SIMPLE.md
│   ├── pages/
│   │   ├── _app.jsx         ← CartProvider + Navigation; BUG-002 lives here
│   │   ├── _document.jsx
│   │   ├── index.jsx        ← redirects to /products
│   │   ├── login.jsx        ← BUG-001
│   │   ├── products.jsx
│   │   ├── cart.jsx         ← BUG-003, BUG-005 (partial), BUG-006
│   │   └── checkout.jsx     ← BUG-004, BUG-005 (partial)
│   └── styles/
│       └── globals.css
│
├── data/
│   ├── simulated_defect_history.csv
│   ├── simulated_change_frequency.csv
│   └── existing_tests_mock.json
│
├── screenshots/          ← created at runtime, serve as static files
├── chroma_store/         ← created at runtime by ChromaDB
├── tests/
│   ├── __init__.py
│   └── generated/        ← agent writes Pytest files here at runtime
│
├── logs/                 ← all project logs — never delete, append-only
│   ├── CHANGELOG.md      ← every meaningful change, versioned
│   ├── DEVLOG.md         ← chronological diary: decisions, blockers, progress
│   ├── COMMANDLOG.md     ← every terminal command with output summary
│   └── BUGLOG.md         ← every bug encountered, diagnosed, and fixed
│
├── requirements.txt
├── .env.example
├── .env                  ← never commit, never read at runtime except via dotenv
├── .gitignore
└── README.md
```

---

## 3. Build Order

Build files in this exact order. Each phase has a verification gate in Section 9.
Do not start a phase until the previous phase's gate passes.

```
PHASE 1 — Infrastructure & Scaffolding
  Step 1.1  requirements.txt
  Step 1.2  .env.example
  Step 1.3  .gitignore
  Step 1.4  logs/CHANGELOG.md      ← initialise with project header and v0.0.0 entry
  Step 1.5  logs/DEVLOG.md         ← initialise with project header and Day 1 entry
  Step 1.6  logs/COMMANDLOG.md     ← initialise with project header
  Step 1.7  logs/BUGLOG.md         ← initialise with project header
  Step 1.8  api/models.py          ← all Pydantic models; everything imports from here
  Step 1.9  api/main.py            ← FastAPI app with CORS and static file mount
  Step 1.10 data/ CSV files        ← simulated history data
  Step 1.11 data/existing_tests_mock.json
  GATE 1: pip install, uvicorn starts, GET /health returns 200, all 4 log files exist

PHASE 2 — Coverage Intelligence Graph
  Step 2.1  engine/crawler.py
  Step 2.2  engine/graph_builder.py
  Step 2.3  agent/prompts/gap_analysis.txt
  Step 2.4  agent/gap_analyser.py
  Step 2.5  api/routes/graph.py
  Step 2.6  api/routes/scan.py     ← partial: crawl + graph only, no exploration yet
  GATE 2: POST /scan returns scan_id, GET /graph returns nodes and edges with coverage overlay

PHASE 3 — Risk Prioritisation Engine
  Step 3.1  agent/prompts/risk_ranking.txt
  Step 3.2  engine/risk_scorer.py
  Step 3.3  api/routes/queue.py
  Step 3.4  api/routes/scan_status.py
  GATE 3: GET /queue returns nodes sorted by risk_score descending; payment and auth nodes rank highest

PHASE 4 — Behavioural Exploration Engine
  Step 4.1  agent/prompts/persona_confused.txt
  Step 4.2  agent/prompts/persona_power.txt
  Step 4.3  agent/prompts/persona_malicious.txt
  Step 4.4  agent/personas.py
  Step 4.5  engine/anomaly_detector.py
  Step 4.6  engine/explorer.py
  Step 4.7  api/routes/findings.py
  Step 4.8  api/routes/scan.py     ← complete: wire exploration into scan flow
  GATE 4: Running full scan against demo-app finds at least one pre-planted bug

PHASE 5 — Memory & Learning Loop
  Step 5.1  engine/memory.py
  Step 5.2  api/routes/memory_routes.py
  Step 5.3  Update engine/risk_scorer.py to incorporate memory signals
  Step 5.4  Update api/routes/scan.py to query memory before each node exploration
  GATE 5: Run scan twice; second run has different (elevated or reduced) risk scores on nodes that had findings

PHASE 6 — Output & Test Generation
  Step 6.1  agent/prompts/test_generation.txt
  Step 6.2  agent/test_generator.py
  Step 6.3  engine/report_builder.py
  Step 6.4  api/routes/report.py
  Step 6.5  agent/brain.py         ← orchestrates all agent modules
  GATE 6: GET /report returns valid JSON; tests/generated/ contains at least one .py file that is syntactically valid Python

PHASE 7 — Demo App
  Step 7.1  demo-app/src/pages/Login.jsx      ← with BUG-001
  Step 7.2  demo-app/src/pages/Products.jsx   ← with BUG-002
  Step 7.3  demo-app/src/pages/Cart.jsx       ← with BUG-003
  Step 7.4  demo-app/src/pages/Checkout.jsx   ← with BUG-004
  Step 7.5  demo-app/src/App.jsx
  Step 7.6  demo-app/package.json
  GATE 7: All 4 bugs are accessible and reproducible manually in the browser

PHASE 8 — Dashboard
  Step 8.1  dashboard/src/api.js
  Step 8.2  dashboard/src/components/MetricCards.jsx
  Step 8.3  dashboard/src/components/ScanControl.jsx
  Step 8.4  dashboard/src/components/CoverageGraph.jsx
  Step 8.5  dashboard/src/components/RiskQueue.jsx
  Step 8.6  dashboard/src/components/FindingsFeed.jsx
  Step 8.7  dashboard/src/components/MemoryPanel.jsx
  Step 8.8  dashboard/src/components/ReportPanel.jsx
  Step 8.9  dashboard/src/App.jsx
  GATE 8: Dashboard renders graph from live API data; clicking Scan triggers a real scan; findings appear in feed

PHASE 9 — Integration & Hardening
  Step 9.1  End-to-end smoke test: fresh environment, full scan, findings, report
  Step 9.2  Error handling audit: every API endpoint handles missing data gracefully
  Step 9.3  README.md
  GATE 9: Fresh clone → install → scan → report in under 5 minutes with no crashes
```

---

## 4. File Specifications

### 4.1 `requirements.txt`

```
anthropic>=0.28.0
langgraph>=0.2.0
playwright>=1.44.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
networkx>=3.3
chromadb>=0.5.0
sentence-transformers>=3.0.0
scikit-learn>=1.5.0
numpy>=1.26.0
pandas>=2.2.0
python-dotenv>=1.0.0
httpx>=0.27.0
pytest>=8.2.0
pytest-playwright>=0.5.0
```

### 4.2 `.env.example`

```
ANTHROPIC_API_KEY=your_key_here
APP_URL=http://localhost:3001
MAX_NODES=50
SCAN_TIMEOUT_SECONDS=180
SCREENSHOTS_DIR=./screenshots
CHROMA_PATH=./chroma_store
TESTS_OUTPUT_DIR=./tests/generated
```

### 4.3 `.gitignore`

```
.env
__pycache__/
*.pyc
venv/
chroma_store/
screenshots/
tests/generated/
node_modules/
.next/
dist/
*.egg-info/
```

### 4.4 `api/models.py` — Pydantic Models

This file defines ALL data models. Every other file imports from here. Never define models inline in route files.

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RiskBand(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class NodeType(str, Enum):
    PAGE = "page"
    FORM = "form"
    BUTTON = "button"
    API = "api"
    STATE = "state"

class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ScanStatus(str, Enum):
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class GraphNode(BaseModel):
    id: str
    label: str
    url: str
    type: NodeType
    covered: bool
    risk_score: float
    risk_band: RiskBand
    last_changed: Optional[str] = None
    defect_count_historical: int = 0
    business_criticality: str = "medium"
    gap_reason: Optional[str] = None
    has_memory: bool = False
    # has_memory is set to True by agent/brain.py orchestration immediately after
    # engine/memory.py's query_similar() returns >=1 result for this node.
    # The dashboard reads it to render a memory-indicator badge on the node.

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    transition: Optional[str] = None

class GraphStats(BaseModel):
    total_nodes: int
    covered: int
    gaps: int
    coverage_percent: float

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: GraphStats

class QueueItem(BaseModel):
    rank: int
    node_id: str
    risk_score: float
    risk_band: RiskBand
    reason: str

class QueueResponse(BaseModel):
    queue: List[QueueItem]

class Finding(BaseModel):
    id: str
    timestamp: str
    persona: str
    page: str
    node_id: str
    action: str
    anomaly: str
    anomaly_type: str
    severity: SeverityLevel
    screenshot_path: Optional[str] = None
    screenshot_url: Optional[str] = None
    reproduction_steps: List[str]
    suggested_assertion: str

class FindingsSummary(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int = 0

class FindingsResponse(BaseModel):
    findings: List[Finding]
    summary: FindingsSummary

class ScanRequest(BaseModel):
    app_url: str
    existing_tests_path: str = "./data/existing_tests_mock.json"
    max_nodes: int = 50
    personas: List[str] = ["confused_user", "power_user", "malicious_user"]

class ScanResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    estimated_duration_seconds: int = 120

class ScanStatusResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    progress_percent: int
    nodes_explored: int
    nodes_total: int
    findings_so_far: int
    current_node: Optional[str] = None
    current_persona: Optional[str] = None

class MemoryRun(BaseModel):
    run_id: str
    date: str
    findings_count: int
    top_finding: Optional[str] = None

class MemoryResponse(BaseModel):
    runs: List[MemoryRun]
    total_findings_in_memory: int

class ReportSummary(BaseModel):
    total_nodes_discovered: int
    nodes_covered_before: int
    coverage_before_percent: float
    gaps_found: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    estimated_coverage_after_percent: float

class GeneratedTest(BaseModel):
    finding_id: str
    test_function_name: str
    test_code: str
    severity: SeverityLevel
    page: str

class ReportResponse(BaseModel):
    report_id: str
    generated_at: str
    app_url: str
    summary: ReportSummary
    findings: List[Finding]
    generated_tests: List[GeneratedTest]
```

### 4.5 `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import all route modules
from api.routes import scan, scan_status, graph, queue, findings, memory_routes, report

app = FastAPI(title="Exploratory Testing Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist
Path("screenshots").mkdir(exist_ok=True)
Path("tests/generated").mkdir(parents=True, exist_ok=True)

# Serve screenshots as static files
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")

# Register routers
app.include_router(scan.router)
app.include_router(scan_status.router)
app.include_router(graph.router)
app.include_router(queue.router)
app.include_router(findings.router)
app.include_router(memory_routes.router)
app.include_router(report.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "exploratory-agent"}
```

### 4.6 `engine/crawler.py`

**Purpose:** Discover all routes, pages, forms, and interactive elements by visiting the app with Playwright.

**Input:** `app_url: str`

**Output:** `list[dict]` — list of discovered elements, each matching this structure:
```python
{
    "url": "/checkout",
    "element_type": "form",  # page | form | button | input | link
    "element_id": "payment_form",
    "element_selector": "[data-testid='payment-form']",
    "label": "Payment Form on /checkout",
    "parent_url": "/cart"
}
```

**Rules:**
- Use Playwright async API (`async_playwright`)
- Wait for `networkidle` before scraping each page
- Discover all `<a>` tags, `<form>` tags, `<button>` tags, and `<input>` tags
- Do NOT crawl external URLs (check that href starts with `/` or matches `app_url`)
- Maximum depth: 3 levels from root
- If a page requires authentication, skip gracefully — log a warning, do not crash
- Return deduplicated list (same URL + element_type + element_id = one entry)
- Handle timeouts with a 10-second per-page limit

### 4.7 `engine/graph_builder.py`

**Purpose:** Convert crawler output into a NetworkX directed graph with coverage overlay.

**Input:**
- `elements: list[dict]` — from crawler
- `coverage_path: str` — path to existing_tests_mock.json

**Output:** `networkx.DiGraph` — with node attributes matching `GraphNode` schema

**Rules:**
- Each element from crawler becomes one node
- Node ID format: `node_{page_slug}_{element_type}` e.g. `node_checkout_form`
- Add node attributes: `id`, `label`, `url`, `type`, `covered`, `risk_score` (default 0.5), `risk_band` (default "medium")
- Add edges between nodes that are on the same page or connected by navigation
- Load `existing_tests_mock.json` and mark covered nodes — set `covered=True` for any node whose URL appears in the mock test file's `covered_urls` array
- Never crash if coverage file is missing — treat all nodes as uncovered and log a warning

**existing_tests_mock.json format:**
```json
{
  "covered_urls": ["/login", "/products"],
  "covered_elements": ["login_form", "product_list"],
  "total_existing_tests": 8,
  "framework": "playwright"
}
```

### 4.8 `engine/risk_scorer.py`

**Purpose:** Compute a risk score for every graph node using the canonical formula.

**The formula — implement exactly:**
```
risk_score = (0.35 × change_frequency) + (0.40 × defect_density) + (0.25 × criticality)
```

**Criticality lookup — use exactly these values:**
```python
CRITICALITY_MAP = {
    "auth": 1.0,
    "login": 1.0,
    "payment": 1.0,
    "checkout": 1.0,
    "cart": 0.9,
    "data": 0.9,
    "profile": 0.8,
    "search": 0.6,
    "navigation": 0.5,
    "product": 0.5,
    "ui": 0.3,
    "default": 0.4
}
```

**Rules:**
- Load `data/simulated_defect_history.csv` with columns: `url,defects_last_6_months`
- Load `data/simulated_change_frequency.csv` with columns: `url,commits_last_30_days`
- Normalise both to 0–1 range by dividing by the column max
- Match nodes to CSV rows by URL; use 0.1 as default for unmatched nodes
- Determine criticality by checking which key from `CRITICALITY_MAP` appears in the node's URL
- After computing score, assign `risk_band` using:
  - `>= 0.8` → `critical`
  - `>= 0.6` → `high`
  - `>= 0.4` → `medium`
  - `< 0.4` → `low`
- Update the NetworkX graph node attributes in-place and also return the scored graph
- Memory adjustment (added in Phase 5): accept optional `memory_adjustments: dict[node_id, float]` and add each adjustment to the base score before clamping to [0, 1]

**Simulated CSV data to create in `data/`:**

`simulated_defect_history.csv`:
```
url,defects_last_6_months
/login,4
/checkout,6
/cart,3
/products,1
/profile,2
/search,0
```

`simulated_change_frequency.csv`:
```
url,commits_last_30_days
/login,2
/checkout,8
/cart,5
/products,3
/profile,1
/search,1
```

### 4.9 `engine/explorer.py`

**Purpose:** Run Playwright-based exploration using persona action lists. Capture all anomalies as findings.

**Input:**
- `node: GraphNode`
- `persona_actions: list[dict]` — from `agent/personas.py`
- `app_url: str`

**Output:** `list[Finding]`

**Rules:**
- Use `async_playwright` with Chromium
- For each action in `persona_actions`:
  - Set up console error listener BEFORE navigating: `page.on("console", handler)`
  - Set up network response listener: `page.on("response", handler)`
  - Execute the action (fill, click, navigate, submit, clear)
  - After each action, check for anomalies (see anomaly_detector.py)
  - Take a screenshot on every anomaly: save to `screenshots/finding_{uuid}.png`
- Wrap every Playwright call in try/except — never let a single action crash the entire exploration
- Use `page.wait_for_load_state("networkidle", timeout=8000)` after navigations
- Use `page.wait_for_timeout(500)` between rapid actions to allow UI to settle
- Each finding gets a UUID: `f"finding_{uuid.uuid4().hex[:8]}"`
- Never hardcode selectors — use selectors from the action dict
- After exploration, close the browser context

**Playwright action execution pattern:**
```python
async def execute_action(page, action: dict):
    action_type = action["action_type"]
    target = action["target"]
    value = action.get("value")

    if action_type == "fill":
        await page.fill(target, value or "")
    elif action_type == "click":
        await page.click(target)
    elif action_type == "navigate":
        await page.goto(value)
    elif action_type == "submit":
        await page.press(target, "Enter")
    elif action_type == "clear":
        await page.fill(target, "")
```

### 4.10 `engine/anomaly_detector.py`

**Purpose:** Detect anomalies during Playwright exploration and return structured findings.

**Anomaly types to detect — implement all of these:**

```python
ANOMALY_TYPES = {
    "js_console_error": {
        "detection": "page.on('console') where msg.type == 'error'",
        "severity": "medium"
    },
    "http_4xx_5xx": {
        "detection": "page.on('response') where response.status >= 400",
        "severity": "high"
    },
    "unexpected_redirect": {
        "detection": "URL after action != expected URL",
        "severity": "medium"
    },
    "form_accepts_invalid_data": {
        "detection": "form submits without validation error element visible",
        "severity": "high"
    },
    "page_crash_blank": {
        "detection": "page.content() is empty or contains only error text",
        "severity": "critical"
    }
}
```

**Rules:**
- The detector receives events from explorer.py's listeners
- It maintains a list of captured anomalies per page visit
- It does NOT make Claude API calls — it just captures raw events
- After all actions complete on a page, call `build_finding()` for each anomaly
- `build_finding()` populates all Finding fields except `screenshot_url` (added by explorer after saving file)
- Reproduction steps must be auto-generated from the sequence of actions taken

### 4.11 `engine/memory.py`

**Purpose:** Store findings as vector embeddings and query for similar past findings.

**Implementation:**
```python
import chromadb
from sentence_transformers import SentenceTransformer
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class AgentMemory:
    def __init__(self):
        chroma_path = os.getenv("CHROMA_PATH", "./chroma_store")
        # CRITICAL: use PersistentClient — NOT chromadb.Client()
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name="findings",
            metadata={"hnsw:space": "cosine"}
        )
        # Use this exact model — it's small, fast, and runs locally
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def _embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def store_finding(self, finding: dict, run_id: str) -> None:
        text = f"{finding['page']} {finding['anomaly']} {finding['persona']} {finding['anomaly_type']}"
        embedding = self._embed(text)
        self.collection.add(
            ids=[finding['id']],
            embeddings=[embedding],
            metadatas=[{
                "node_id": finding['node_id'],
                "severity": finding['severity'],
                "persona": finding['persona'],
                "anomaly_type": finding['anomaly_type'],
                "resolved": False,
                "run_id": run_id,
                "run_date": finding['timestamp'][:10],
                "page": finding['page']
            }]
        )

    def query_similar(self, node_id: str, context: str, top_k: int = 3) -> list[dict]:
        """Returns list of similar past findings with similarity scores."""
        try:
            embedding = self._embed(context)
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where={"node_id": node_id}
            )
            if not results["ids"][0]:
                return []
            return [
                {
                    "id": results["ids"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # cosine distance to similarity
                    "metadata": results["metadatas"][0][i]
                }
                for i in range(len(results["ids"][0]))
            ]
        except Exception:
            return []  # Never crash on memory query failure

    def get_memory_adjustment(self, node_id: str, context: str) -> float:
        """Returns a risk score adjustment based on memory: positive if unresolved issues, negative if resolved."""
        similar = self.query_similar(node_id, context)
        if not similar:
            return 0.0
        high_similarity = [s for s in similar if s["similarity"] > 0.85]
        if not high_similarity:
            return 0.0
        unresolved = [s for s in high_similarity if not s["metadata"].get("resolved", False)]
        resolved = [s for s in high_similarity if s["metadata"].get("resolved", False)]
        adjustment = (len(unresolved) * 0.15) - (len(resolved) * 0.10)
        return max(-0.3, min(0.3, adjustment))  # Clamp to [-0.3, 0.3]

    def get_run_summaries(self) -> list[dict]:
        """Returns a list of past runs for the memory panel."""
        try:
            all_data = self.collection.get()
            if not all_data["ids"]:
                return []
            runs = {}
            for i, meta in enumerate(all_data["metadatas"]):
                run_id = meta.get("run_id", "unknown")
                if run_id not in runs:
                    runs[run_id] = {"run_id": run_id, "date": meta.get("run_date", ""), "findings_count": 0, "top_finding": None}
                runs[run_id]["findings_count"] += 1
                if runs[run_id]["top_finding"] is None and meta.get("severity") in ["critical", "high"]:
                    runs[run_id]["top_finding"] = f"{meta.get('anomaly_type')} on {meta.get('page')}"
            return list(runs.values())
        except Exception:
            return []
```

### 4.12 `agent/gap_analyser.py`

**Purpose:** Use Claude API to identify which uncovered nodes are meaningful test gaps.

**Rules:**
- Import the prompt from `agent/prompts/gap_analysis.txt` — never inline prompts
- Parse Claude's JSON response — always wrap `json.loads()` in try/except using `safe_parse_json` below
- **JSON parse retry policy:** On the first parse failure, retry the same call once with the suffix `\n\nReturn ONLY valid JSON. No markdown, no preamble, no trailing text.` appended to the prompt. On a second consecutive failure for the same call, log the failure to `logs/COMMANDLOG.md` and return an empty list — never crash the scan.
- Set `max_tokens=2000` for this call
- Add a `gap_reason` string to each node that is identified as a gap
- Never pass more than 30 nodes at once to Claude. **Batching:** if the gap-candidate list exceeds 30, split with `batches = [nodes[i:i+30] for i in range(0, len(nodes), 30)]`, call gap_analyser per batch, then concatenate the resulting gap lists in order. Do not parallelise — sequential calls keep rate-limit behaviour predictable.

**JSON parsing safety pattern — always use this:**
```python
import json
import re

def safe_parse_json(text: str) -> list | dict | None:
    """Extract and parse JSON from LLM response, handling markdown fences."""
    # Strip markdown code fences if present
    text = re.sub(r'```(?:json)?\s*', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array or object within the text
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None
```

### 4.13 `agent/personas.py`

**Purpose:** For a given page and node, generate persona-specific action lists using Claude.

**Rules:**
- Loads the correct prompt template based on persona name
- Returns a `list[dict]` of actions, each with: `action_type`, `target`, `value`, `reason`
- **Valid `action_type` values are exactly these five (closed set):** `fill`, `click`, `navigate`, `submit`, `clear`. After parsing Claude's response, iterate and drop any action whose `action_type` is not in this set; log each dropped action at DEBUG with the persona name, page, and offending value. Do not silently extend this set — if a new action type is genuinely needed (e.g. `hover`), update Section 4.6 (`engine/crawler.py`) and `engine/explorer.py` to support it first, then add it here in one coordinated change.
- If Claude returns invalid action_types, filter them out per the rule above — never pass invalid actions to explorer
- Cap action list at 8 actions per persona per page — trim to 8 if Claude returns more
- Always use `safe_parse_json()` from gap_analyser.py

### 4.14 `agent/test_generator.py`

**Purpose:** Generate a Pytest test function for each high or critical finding.

**Rules:**
- Only generate tests for findings with severity `high` or `critical`
- Use the prompt from `agent/prompts/test_generation.txt`
- After generating, validate the code is syntactically valid: `compile(code, '<string>', 'exec')`
- If validation fails: retry once with a stricter prompt; if it fails again, log and skip
- Write each test to `tests/generated/test_{finding_id}.py`
- Each file must start with the imports: `import pytest` and `from playwright.sync_api import Page`
- Never overwrite an existing test file — append a suffix if the file already exists

### 4.15 `engine/report_builder.py`

**Purpose:** Compile all findings and generated tests into a complete report object.

**Rules:**
- Import `ReportResponse` from `api/models.py`
- Compute `estimated_coverage_after_percent` as `(covered_before + gaps_found) / total_nodes * 100`
- Clamp to max 100.0
- `generated_at` uses `datetime.utcnow().isoformat() + "Z"`
- Read generated test files from `tests/generated/` and include their code in `GeneratedTest` objects
- Return a `ReportResponse` Pydantic object — not a raw dict

### 4.16 `agent/brain.py`

**Purpose:** The main orchestration loop that coordinates all agent modules for a full scan.

**Scan state — maintain this in a module-level dict keyed by scan_id:**
```python
SCAN_STATE: dict[str, dict] = {}
# Structure per scan_id:
# {
#   "status": ScanStatus,
#   "progress_percent": int,
#   "nodes_explored": int,
#   "nodes_total": int,
#   "findings_so_far": int,
#   "current_node": str | None,
#   "current_persona": str | None,
#   "graph": nx.DiGraph | None,
#   "findings": list[Finding],
#   "report": ReportResponse | None
# }
```

**Orchestration flow — implement in this exact order:**
```
1. Generate scan_id = f"scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
2. Initialise SCAN_STATE[scan_id]
3. Capture t_start = time.monotonic() and read SCAN_TIMEOUT_SECONDS from env (default 180)
4. Run crawler → get elements list
5. Run graph_builder → get NetworkX graph
6. Run gap_analyser (Claude) → identify gap nodes, add gap_reason to graph
7. Run risk_scorer → score all nodes, update SCAN_STATE progress
8. Sort nodes by risk_score descending → exploration queue
9. For each node in queue:
   a. Check elapsed time: if time.monotonic() - t_start > SCAN_TIMEOUT_SECONDS, break
      out of the loop and proceed to step 10 with whatever findings exist.
   b. Query memory for similar past findings on this node.
      - If results > 0: set graph.nodes[node_id]['has_memory'] = True
      - Compute memory_adjustment in [-0.3, +0.3] using rules in Section 4.11
      - Combined score = max(0.0, min(1.0, base_score + memory_adjustment))
        Always clamp the final value — base and adjustment can each be in-range
        individually while their sum falls outside [0, 1].
      - Persist the clamped score back to graph.nodes[node_id]['risk_score']
   c. Update SCAN_STATE current_node
   d. For each persona in scan request:
      - Re-check the timeout (same as 9a); break if exceeded
      - Update SCAN_STATE current_persona
      - Call personas.py → get action list from Claude
      - Call explorer.py → run Playwright, get findings
      - For each finding: store in memory, append to SCAN_STATE findings
      - Update SCAN_STATE progress
10. Call test_generator → generate Pytest for high/critical findings
11. Call report_builder → compile report
12. Set SCAN_STATE[scan_id]["status"] = "completed"
13. Set SCAN_STATE[scan_id]["report"] = report
```

**Rules:**
- Run exploration in a background `asyncio.Task` — POST /scan must return immediately
- Never block the FastAPI event loop
- All state updates to SCAN_STATE must be thread-safe (use asyncio, not threading)
- The timeout check (steps 9a, 9d) is a soft cap: it never interrupts an in-flight Playwright action or LLM call mid-execution — it only prevents starting the next one. The scan must still finish steps 10–13 (test generation and report compilation) even if the timeout fired.

---

## 5. Data Schemas

These schemas are canonical. Every part of the system must use them exactly.

### Node Schema
```json
{
  "id": "node_checkout_form",
  "label": "Payment Form on /checkout",
  "url": "/checkout",
  "type": "form",
  "covered": false,
  "risk_score": 0.91,
  "risk_band": "critical",
  "last_changed": "2026-05-01",
  "defect_count_historical": 3,
  "business_criticality": "high",
  "gap_reason": "Payment form has no negative path coverage",
  "has_memory": false
}
```

### Edge Schema
```json
{
  "source": "node_cart_page",
  "target": "node_checkout_form",
  "type": "navigation",
  "transition": "click_proceed_to_checkout"
}
```

### Finding Schema
```json
{
  "id": "finding_a1b2c3d4",
  "timestamp": "2026-05-12T10:23:11Z",
  "persona": "confused_user",
  "page": "/checkout",
  "node_id": "node_checkout_form",
  "action": "Submitted payment form with empty card number",
  "anomaly": "Form submitted successfully, no validation error shown",
  "anomaly_type": "form_accepts_invalid_data",
  "severity": "high",
  "screenshot_path": "screenshots/finding_a1b2c3d4.png",
  "screenshot_url": "/screenshots/finding_a1b2c3d4.png",
  "reproduction_steps": [
    "Navigate to /cart with at least one item",
    "Click Proceed to Checkout",
    "Leave card number field empty",
    "Click Pay Now"
  ],
  "suggested_assertion": "Assert that payment form rejects empty card number with visible error"
}
```

### Memory Entry Schema
```json
{
  "node_id": "node_checkout_form",
  "severity": "high",
  "persona": "confused_user",
  "anomaly_type": "form_accepts_invalid_data",
  "resolved": false,
  "run_id": "scan_20260512_1023",
  "run_date": "2026-05-12",
  "page": "/checkout"
}
```

### Report Schema
```json
{
  "report_id": "report_20260512_1045",
  "generated_at": "2026-05-12T10:45:00Z",
  "app_url": "http://localhost:3001",
  "summary": {
    "total_nodes_discovered": 47,
    "nodes_covered_before": 21,
    "coverage_before_percent": 44.7,
    "gaps_found": 12,
    "critical_findings": 3,
    "high_findings": 5,
    "medium_findings": 4,
    "estimated_coverage_after_percent": 70.2
  },
  "findings": [...],
  "generated_tests": [
    {
      "finding_id": "finding_a1b2c3d4",
      "test_function_name": "test_checkout_form_rejects_empty_card_number",
      "test_code": "def test_checkout_form_rejects_empty_card_number(page):\n    ...",
      "severity": "high",
      "page": "/checkout"
    }
  ]
}
```

---

## 6. API Endpoint Contracts

Implement every endpoint exactly as specified. Do not rename, reorder fields, or change HTTP methods.

### `POST /scan`
```
Request body: ScanRequest
Response: ScanResponse
Side effect: starts async background task
```

### `GET /scan/{scan_id}/status`
```
Response: ScanStatusResponse
Source: reads from SCAN_STATE[scan_id] in brain.py
404 if scan_id not found
```

### `GET /graph`
```
Query params: scan_id (optional — returns latest if omitted)
Response: GraphResponse
Source: reads graph from SCAN_STATE
```

### `GET /queue`
```
Query params: scan_id (optional), risk_band (optional filter)
Response: QueueResponse
Source: graph nodes sorted by risk_score descending, filtered if risk_band provided
```

### `GET /findings`
```
Query params: scan_id (optional), severity (optional filter)
Response: FindingsResponse
Source: SCAN_STATE[scan_id]["findings"]
```

### `GET /memory`
```
Response: MemoryResponse
Source: engine/memory.py AgentMemory.get_run_summaries()
```

### `GET /report`
```
Query params: scan_id (optional)
Response: ReportResponse
Source: SCAN_STATE[scan_id]["report"]
404 with message "Scan not completed yet" if report is None
```

### `GET /screenshots/{filename}`
```
Served as static files by FastAPI StaticFiles mount in main.py
```

### `GET /health`
```
Response: {"status": "ok", "service": "exploratory-agent"}
```

---

## 7. Prompt Templates

Write these to `agent/prompts/` as plain text files. Import them with `Path(__file__).parent / "prompts" / "filename.txt"`. Never inline these prompts in Python code.

### `gap_analysis.txt`
```
You are a senior QA engineer reviewing test coverage for a web application.

Application routes and elements discovered:
{routes_json}

Currently covered by existing tests:
{covered_nodes_json}

Identify the top {max_gaps} most meaningful coverage gaps.
For each gap, explain why it is a risk — consider: is it an auth flow?
Does it handle user data? Are there edge cases in form inputs?
Do not include gaps for static content pages or navigation links.

Return ONLY a JSON array. Each item must have:
- node_id: string (must match one of the node ids provided above; the specific element/flow is already encoded inside node_id, do NOT return a separate "element" field)
- page: URL path string
- gap_reason: one clear sentence explaining the testing gap
- risk_factors: array of strings from ["auth", "payment", "data", "input_validation", "navigation", "error_handling"]

Return ONLY valid JSON. No explanation, no markdown code fences.
```

### `risk_ranking.txt`
```
You are a QA risk analyst. Rank the following untested nodes by risk priority.

Nodes to rank:
{gap_nodes_json}

Application context: {app_description}

Consider these risk factors in order of importance:
1. Business criticality (auth and payment flows = highest risk)
2. Potential for user data loss or corruption
3. Frequency of user interaction
4. Complexity of the flow (more steps = more risk)

Return ONLY a JSON array of objects in order from highest to lowest risk.
Each object must have:
- node_id: string (must match exactly one of the node_ids provided above)
- reason: one sentence explaining why this node is ranked at this position

Return ONLY valid JSON. No explanation, no markdown code fences.
```

### `persona_confused.txt`
```
You are simulating a confused, non-technical user testing the page at {page_url}.

Page description: {page_description}
Available form fields (use these exact selectors): {form_fields}
Available buttons (use these exact selectors): {buttons}

Generate exactly 6 realistic actions a confused user might take on this page.
A confused user: submits forms with wrong data types, leaves required fields empty,
navigates backwards mid-flow, refreshes mid-transaction, double-clicks submit buttons,
and tries to access pages out of sequence.

Return ONLY a JSON array. Each action must have:
- action_type: one of exactly ["fill", "click", "navigate", "submit", "clear"]
- target: the CSS selector or data-testid selector (e.g. "[data-testid='submit-btn']")
- value: the value to enter as a string (use null for non-fill actions)
- reason: one sentence explaining why a confused user would do this

Return ONLY valid JSON. No explanation, no markdown code fences.
```

### `persona_power.txt`
```
You are simulating a power user who is highly experienced testing the page at {page_url}.

Page description: {page_description}
Available form fields (use these exact selectors): {form_fields}
Available buttons (use these exact selectors): {buttons}

Generate exactly 6 realistic actions a power user might take on this page.
A power user: uses keyboard shortcuts, clicks rapidly, skips optional steps,
uses browser autofill with unexpected formats, and completes flows in non-standard order.

Return ONLY a JSON array. Each action must have:
- action_type: one of exactly ["fill", "click", "navigate", "submit", "clear"]
- target: the CSS selector or data-testid selector
- value: the value to enter as a string (use null for non-fill actions)
- reason: one sentence explaining why a power user would do this

Return ONLY valid JSON. No explanation, no markdown code fences.
```

### `persona_malicious.txt`
```
You are simulating a malicious user attempting to find security and validation weaknesses
on the page at {page_url}.

Page description: {page_description}
Available form fields (use these exact selectors): {form_fields}
Available buttons (use these exact selectors): {buttons}

Generate exactly 6 actions that test input validation and security boundaries.
Focus on: oversized inputs, special characters, SQL-injection-style strings,
XSS payload strings, negative numbers in numeric fields, manipulated URL parameters.

Return ONLY a JSON array. Each action must have:
- action_type: one of exactly ["fill", "click", "navigate", "submit", "clear"]
- target: the CSS selector or data-testid selector
- value: the value to enter as a string (use null for non-fill actions)
- reason: one sentence explaining what vulnerability this tests

Return ONLY valid JSON. No explanation, no markdown code fences.
```

### `test_generation.txt`
```
You are a senior QA automation engineer writing Playwright-based Pytest tests.

Finding to document:
{finding_json}

Application base URL: {base_url}
Page URL: {page_url}

Write a complete, runnable Pytest test function that:
1. Sets up the required precondition (gets the app to the correct starting state)
2. Performs the exact sequence of actions that triggered the anomaly
3. Asserts the CORRECT expected behaviour (what should happen, not what did happen)
4. Includes a docstring with: what is being tested, why it matters, discovery context
5. Uses [data-testid] selectors wherever possible, CSS selectors as fallback
6. Includes teardown if any state was modified (e.g. items added to cart)

The test must FAIL against the current buggy application.
The test must PASS after the bug described in the finding is fixed.

Imports to use at top of file:
import pytest
from playwright.sync_api import Page

Return ONLY the Python function code starting with "def test_".
No markdown, no explanation, no import statements (they are added automatically).
Function name must follow this format exactly: test_{page_slug}_{element}_{scenario}
```

---

## 8. Anti-Hallucination Rules

Read these before writing every file.

### Never invent these
- **Selectors:** Never hardcode CSS selectors like `#checkout-btn` or `.payment-form`. Selectors must come from the crawler's discovered elements or from the persona prompt's output. The demo app uses `data-testid` attributes — reference those.
- **URLs:** Never hardcode application URLs except `http://localhost:3001` (demo app) and `http://localhost:8000` (API). All app paths (`/login`, `/checkout` etc.) come from the crawler.
- **Port numbers:** Always `3000` (dashboard), `3001` (demo app), `8000` (API). Never change.
- **Risk scores:** Never hardcode risk scores in business logic. They must always be computed from the formula.
- **Model names:** Always `claude-sonnet-4-6` (Sonnet 4.6). Never use older snapshot IDs like `claude-sonnet-4-20250514`, never use prior families like `claude-3-5-sonnet` or `claude-3-opus`, and never use a placeholder. See Section 1 hard constraints for upgrade policy.
- **ChromaDB API:** Always `PersistentClient`. Never `Client()`.
- **Node IDs:** Must follow format `node_{url_slug}_{element_type}`. Generate programmatically, never hardcode.

### Always do these
- **Import models from `api/models.py`** — never redefine Pydantic models elsewhere
- **Load env vars at top of every Python file that needs them** — `load_dotenv()` then `os.getenv()`
- **Guard against None** — every SCAN_STATE access must handle missing key with a 404 response
- **Validate generated Pytest** — always run `compile()` before writing to disk
- **Parse JSON safely** — always use `safe_parse_json()` for all Claude API responses
- **Use `data-testid` attributes in demo app** — every interactive element in demo-app must have a `data-testid` attribute so Playwright can target it reliably
- **Test with demo app running** — never test against production URLs

### CORS — always allow localhost:3000
```python
allow_origins=["http://localhost:3000"]
```

### Async rules
- `explorer.py` is async — use `asyncio.run()` only at the top level if running as script
- FastAPI background tasks: use `asyncio.create_task()` inside the route handler, not `BackgroundTasks`
- Never use `time.sleep()` in async code — use `await asyncio.sleep()`

---

## 9. Verification Gates

Run these checks before moving to the next phase. If a gate fails, fix the issue before continuing.

### Gate 1 — Infrastructure
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
curl http://localhost:8000/health
# Expected: {"status": "ok", "service": "exploratory-agent"}
```

### Gate 2 — Coverage Graph
```bash
# With demo-app running on port 3001:
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"app_url": "http://localhost:3001"}'
# Expected: {"scan_id": "scan_...", "status": "started", ...}

curl http://localhost:8000/graph
# Expected: JSON with "nodes" array (min 4 nodes), "edges" array, "stats" object
# Check: at least 2 nodes have "covered": false
```

### Gate 3 — Risk Queue
```bash
curl http://localhost:8000/queue
# Expected: JSON with "queue" array sorted by risk_score descending
# Check: checkout or login node appears in top 3
# Check: no two adjacent items have same risk_score (unless both are 0.5 default)
```

### Gate 4 — Exploration
```bash
# Run a full scan against demo-app
curl -X POST http://localhost:8000/scan \
  -d '{"app_url": "http://localhost:3001", "personas": ["confused_user"]}'
# Poll status until completed:
curl http://localhost:8000/scan/{scan_id}/status

curl http://localhost:8000/findings
# Expected: at least 1 finding with severity "high" or "critical"
# Check: findings have screenshot_url populated
# Check: at least one finding's page is "/login" or "/checkout" (pre-planted bugs)
```

### Gate 5 — Memory
```bash
# Run scan twice with same demo-app
# After second scan, compare risk scores:
curl http://localhost:8000/queue  # after run 1 - save output
# ... run again ...
curl http://localhost:8000/queue  # after run 2
# Check: at least one node has a different risk_score between run 1 and run 2

curl http://localhost:8000/memory
# Expected: "runs" array with 2 entries, "total_findings_in_memory" > 0
```

### Gate 6 — Test Generation
**Precheck (manual, do this first):** Before running pytest, manually reproduce all 4 pre-planted bugs (BUG-001 through BUG-004) against a fresh `npm run dev` of `demo-app/` per the reproduction steps in Section 10. If any bug has been accidentally fixed during development (login validation suddenly rejects empty password, cart quantity rejects -1, etc.), re-introduce the original buggy implementation per Section 10's code samples. Only then run the pytest checks below — otherwise the gate will pass for the wrong reason (test passing because bug is fixed, not because generation is correct).

```powershell
# PowerShell on Windows
Get-ChildItem tests/generated/
# Expected: at least one .py file

python -m py_compile tests/generated/*.py
# Expected: no syntax errors (exit code 0)

Set-Location tests; pytest generated/ -v --tb=short
# Expected: at least one test FAILS (proving it caught a real bug in demo app)
```
*(Bash equivalent: replace `Get-ChildItem` with `ls` and `Set-Location` with `cd`.)*

### Gate 7 — Demo App
```bash
cd demo-app && npm run dev
# Navigate to http://localhost:3001/login
# Manually reproduce BUG-001: submit empty password → form should accept it (that's the bug)
# Navigate to http://localhost:3001/cart
# Manually reproduce BUG-003: enter -1 quantity → subtotal should go negative (that's the bug)
# Verify all 4 data-testid attributes exist on interactive elements
```

### Gate 8 — Dashboard
```bash
cd dashboard && npm run dev
# Navigate to http://localhost:3000
# Check: coverage graph renders with coloured nodes
# Check: clicking a node opens detail panel
# Check: ScanControl has URL input and Scan button
# Check: clicking Scan calls POST /scan and status polling begins
# Check: findings appear in feed after scan completes
```

### Gate 9 — Integration
```bash
# Fresh environment (new terminal, no running servers)
git clone . /tmp/test-clone && cd /tmp/test-clone
pip install -r requirements.txt
playwright install chromium
cd demo-app && npm install && npm run dev &
cd ../dashboard && npm install && npm run dev &
cd .. && uvicorn api.main:app --port 8000 &
sleep 5
curl -X POST http://localhost:8000/scan -d '{"app_url":"http://localhost:3001"}'
# Wait 3 minutes
curl http://localhost:8000/report
# Expected: valid JSON report with findings and generated_tests populated
```

---

## 10. Demo App — Pre-Planted Bug Catalogue

The demo-app at `demo-app/` is a Next.js 14 e-commerce SPA running on port 3001 (pages router, lowercase filenames per Next.js routing convention). It ships **six pre-planted bugs**, distributed across the three personas so each persona class surfaces at least one finding during exploration. Bugs 1–4 carry inline `// BUG-NNN` comments in the source; bugs 5–6 are emergent — present in the same code but never flagged with a comment.

Run with `cd demo-app && npm install && npm run dev` (binds port 3001). `/` redirects to `/products`. Public routes: `/login`, `/products`. Routes that *should* require auth but don't: `/cart`, `/checkout` — see BUG-005.

### Required `data-testid` attributes

These are the selectors the crawler will discover. Extracted from the implemented JSX — keep this list and `demo-app/pages/*.jsx` in sync via §19 sync rules. `{id}` placeholders are product ids `1`–`6`.

**Global nav (`pages/_app.jsx`):**
- `cart-count` — badge in nav header, visible only when cart count > 0

**`/login` (`pages/login.jsx`):**
- `email-input`, `password-input` — form fields
- `login-button` — submit
- `error-message` — appears only when `error` state is non-empty

**`/products` (`pages/products.jsx`):**
- `product-page-cart-count` — wrapper for the "Items in cart: N" banner
- `cart-count-display` — numeric span inside that banner
- `product-name-{id}`, `product-price-{id}`, `add-to-cart-btn-{id}` — one set per product
- `bug-explanation` — human-facing yellow panel; agent should ignore

**`/cart` (`pages/cart.jsx`):**
- `cart-item-{id}` — row container
- `item-price-{id}`, `item-total-{id}`, `quantity-input-{id}`, `remove-btn-{id}` — per row
- `subtotal`, `total-price` — order summary
- `proceed-to-checkout-btn`
- `bug-explanation` — human-facing panel

**`/checkout` (`pages/checkout.jsx`):**
- Shipping: `fullname-input`, `email-input`, `address-input`, `city-input`, `state-input`, `zipcode-input`
- Payment: `card-number-input`, `expiry-input`, `cvv-input`
- `place-order-btn` — submit
- `checkout-subtotal`, `checkout-total`, `order-item-{id}` — order summary
- `bug-explanation` — human-facing panel
- Per-field validation errors render via `.error-message` class (no specific testid)

### Bug catalogue (six bugs total)

| ID | Page | Severity | Persona | One-line |
|---|---|---|---|---|
| BUG-001 | `/login` | HIGH | Confused | Empty password accepted; navigates to `/products` |
| BUG-002 | `/products`, `/cart`, nav | MEDIUM | Power | Cart count renders `NaN` once any line-item quantity > 5 |
| BUG-003 | `/cart` | HIGH | Confused / Malicious | Negative quantity accepted; subtotal goes negative |
| BUG-004 | `/checkout` | HIGH | Malicious / Confused | Card number accepted regardless of format (letters, length) |
| BUG-005 | `/cart`, `/checkout` | HIGH | Malicious | Protected routes reachable without ever logging in (no auth guard) |
| BUG-006 | `/cart` | MEDIUM | Confused | Non-numeric text in quantity field silently removes the item |

### Per-bug detail (current implementation snippets)

**BUG-001 — Login form accepts empty password** (`pages/login.jsx` `handleSubmit`)
```jsx
// BUG STARTS HERE: No check for empty password
// A correct implementation would have:
// if (!password) { setError('Password is required'); setLoading(false); return; }
localStorage.setItem('userEmail', email);
setIsLoggedIn(true);
router.push('/products');
```
Trigger: Confused User submits the login form with `email` filled and `password` empty.

**BUG-002 — Cart count NaN once any item quantity > 5** (`pages/_app.jsx` `getCartCount`)
```jsx
const getCartCount = () => {
  let count = 0;
  for (let item of cartItems) {
    if (item.quantity > 5) {
      count = count + (item.quantity * "invalid");   // string * number = NaN
    } else {
      count = count + item.quantity;
    }
  }
  return count || 0;
};
```
Trigger: Power User clicks the same product's Add-to-Cart 6+ times. Both the in-page cart-count badge and the nav header badge render `NaN`. Anomaly: visible incorrect numeric display.

**BUG-003 — Negative quantity accepted** (`pages/cart.jsx` `handleQuantityChange`)
```jsx
const handleQuantityChange = (productId, value) => {
  const quantity = parseInt(value) || 0;
  // BUG: Missing validation here
  // Should check: if (quantity < 0) { showError; return; }
  updateQuantity(productId, quantity);
};
```
Trigger: Confused / Malicious User enters `-5` in any `quantity-input-{id}`. `item-total-{id}` becomes negative; `subtotal` and `total-price` become negative.

**BUG-004 — Card number format not validated** (`pages/checkout.jsx` `validateForm`)
```jsx
if (!formData.cardNumber.trim()) {
  newErrors.cardNumber = 'Card number is required';
}
// BUG: Missing validation for card format
// Should have: else if (!/^\d{13,19}$/.test(formData.cardNumber.replace(/\s/g, '')))
//   newErrors.cardNumber = 'Card number must be 13-19 digits';
```
Trigger: Malicious User submits checkout with `card-number-input` set to `abcdefgh`, `12345`, or a 25-digit string. Form accepts and proceeds to success page.

**BUG-005 — Protected routes reachable without authentication** (`pages/cart.jsx`, `pages/checkout.jsx`)
Neither page reads `isLoggedIn` from `CartContext` to guard rendering. There is no router-level or component-level redirect from `/cart` or `/checkout` to `/login` when `isLoggedIn === false`. The nav swaps Login↔Logout but does not prevent direct URL access.

Trigger: Malicious User navigates directly to `http://localhost:3001/checkout` from a cold session (no prior login). The checkout form renders and is fully usable. Suggested fix:
```jsx
useEffect(() => {
  if (!isLoggedIn) router.replace('/login');
}, [isLoggedIn, router]);
```
in both protected pages. Anomaly type: `auth_boundary_bypass`.

**BUG-006 — Non-numeric quantity silently removes the item** (`pages/cart.jsx` + `pages/_app.jsx`)
```jsx
// cart.jsx handleQuantityChange:
const quantity = parseInt(value) || 0;          // parseInt("abc") → NaN, || 0 → 0
updateQuantity(productId, quantity);

// _app.jsx updateQuantity:
if (quantity <= 0) {
  removeFromCart(productId);                    // 0 path triggers removal
}
```
Trigger: Confused User types `abc` (or any non-numeric) into a `quantity-input-{id}`. The row disappears without any error message — the user has no feedback that the input was invalid. Same `anomaly_type` family as BUG-003 (`form_accepts_invalid_data`) but different symptom (silent state change vs. wrong numeric).

### Verification

The companion files `demo-app/README.md` and `demo-app/BUGS_EXPLAINED_SIMPLE.md` ship with the demo app and document manual reproduction for BUG-001..BUG-004. BUG-005 and BUG-006 manual repro:

- **BUG-005:** open a fresh incognito window → go directly to `http://localhost:3001/checkout` → confirm checkout form renders without redirect.
- **BUG-006:** add any item to cart → on `/cart`, change quantity-input value to `abc` → press Tab → confirm row disappears with no error message.

---

## 11. Dashboard Component Behaviour

### `ScanControl.jsx`
- Text input pre-filled with `http://localhost:3001`
- "Start Scan" button triggers `POST /scan`
- On response, stores `scan_id` in React state
- Starts polling `GET /scan/{scan_id}/status` every 2 seconds
- Shows a progress bar using `progress_percent`
- Shows `current_node` and `current_persona` as status text
- Stops polling when status is `completed` or `failed`

### `CoverageGraph.jsx`
- Uses D3.js force simulation
- Node colours: `critical`=`#EF4444`, `high`=`#F97316`, `medium`=`#EAB308`, `low`=`#22C55E`, `covered`=`#6B7280`
- Node radius: proportional to risk_score (min 8px, max 20px)
- On node click: emit event to parent with node data for detail panel
- Nodes with `has_memory=true` show a small circle indicator
- Re-renders when `/graph` data updates (poll every 3 seconds during active scan)

### `FindingsFeed.jsx`
- Polls `GET /findings` every 3 seconds during active scan
- Each finding card shows: persona badge, severity badge (coloured), page, anomaly text
- Severity colours: `critical`=red, `high`=orange, `medium`=yellow, `low`=grey
- Clicking a finding calls parent handler to highlight node in graph
- Shows screenshot thumbnail if `screenshot_url` is present

### `ReportPanel.jsx`
- Loads `GET /report` once when scan is completed
- Shows 4 metric cards: total gaps, critical findings, coverage before %, coverage after %
- Lists findings sorted by severity
- For each generated test: shows code in a `<pre>` block with syntax highlighting
- Each test has a "Copy" button that copies the code to clipboard

---

## 12. Error Handling Standards

Every endpoint must return proper HTTP status codes:

```python
from fastapi import HTTPException

# Scan not found
raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

# Scan still running, report not ready
raise HTTPException(status_code=202, detail="Scan not completed yet")

# Claude API failure
raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
```

Every Claude API call must be wrapped:
```python
try:
    response = client.messages.create(...)
    result = safe_parse_json(response.content[0].text)
    if result is None:
        logger.error(f"Failed to parse Claude response: {response.content[0].text[:200]}")
        return []  # Graceful degradation
    return result
except anthropic.APIError as e:
    logger.error(f"Claude API error: {e}")
    return []  # Never crash — return empty result and continue
```

---

## 13. Quick Reference — Exact Values to Use Everywhere

| Constant | Value | Used in |
|---|---|---|
| Claude model | `claude-sonnet-4-6` | all `client.messages.create()` calls |
| max_tokens for gap analysis | `2000` | gap_analyser.py |
| max_tokens for persona | `1000` | personas.py |
| max_tokens for test gen | `1500` | test_generator.py |
| Risk w1 | `0.35` | risk_scorer.py |
| Risk w2 | `0.40` | risk_scorer.py |
| Risk w3 | `0.25` | risk_scorer.py |
| Memory similarity threshold | `0.85` | memory.py |
| Memory positive adjustment | `+0.15` | memory.py |
| Memory negative adjustment | `-0.10` | memory.py |
| Max actions per persona | `8` | personas.py |
| Max nodes to Claude at once | `30` | gap_analyser.py |
| Crawler max depth | `3` | crawler.py |
| Page load timeout | `8000ms` | explorer.py |
| Action settle wait | `500ms` | explorer.py |
| Status poll interval | `2000ms` | ScanControl.jsx |
| Graph poll interval | `3000ms` | CoverageGraph.jsx |
| Findings poll interval | `3000ms` | FindingsFeed.jsx |
| Demo app port | `3001` | everywhere |
| Dashboard port | `3000` | everywhere |
| API port | `8000` | everywhere |
| ChromaDB collection | `"findings"` | memory.py |
| Embedding model | `'all-MiniLM-L6-v2'` | memory.py |

---

## 14. Logging System Overview

Four append-only log files live in `logs/`. Never delete entries — write a correction below the original.

| File | Purpose | Update when |
|---|---|---|
| `logs/CHANGELOG.md` | Versioned record of code/schema/architecture changes | Phase gate passes, schema/API change, bug fix |
| `logs/DEVLOG.md` | Diary of decisions, blockers, progress, context | Session start/end, gate result, significant decision |
| `logs/COMMANDLOG.md` | Every terminal command with timestamp and output summary | Every command (especially failures and gate checks) |
| `logs/BUGLOG.md` | Every bug — symptom, repro, root cause, fix | Bug discovered or fixed |

**Golden rules (all four files):** append only, timestamp `YYYY-MM-DD HH:MM`, be specific (`"fixed a bug"` is useless — name the file, symptom, and cause), cross-reference (BUGLOG ↔ CHANGELOG), log failures too. If a hard constraint, schema, or API contract changes in code, update the matching section of CLAUDE.md in the same change and note it in CHANGELOG.

Initialise all four files during Phase 1 Step 1.4–1.7 using the templates in §§15–18. See §20 for bootstrap (Windows / PowerShell).

---

## 15. CHANGELOG.md — Format and Rules

### Initial file template (use verbatim, fill date in)

```markdown
# CHANGELOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** YYYY-MM-DD
**Base document:** exploratory_testing_agent_project_plan.md
**Instruction file:** CLAUDE.md

MAJOR = breaking schema/API change · MINOR = new feature or layer · PATCH = fix/refactor

---

## [Unreleased]

## [0.0.0] — YYYY-MM-DD
### Initialised
- Project scaffolded from CLAUDE.md instruction file
- Log files created: CHANGELOG.md, DEVLOG.md, COMMANDLOG.md, BUGLOG.md
```

### Entry format

```markdown
## [X.Y.Z] — YYYY-MM-DD
### Added — new files/features (include filenames)
### Changed — before/after for schemas, endpoints
### Fixed — one line per bug; cross-ref `BUGLOG BUG-XXX`
### Removed — what and why
### Notes — context, decision rationale
```

### Version Bump Rules

| Change type | Version bump | Example |
|---|---|---|
| Phase gate passed (new layer working) | MINOR | 0.0.0 → 0.1.0 |
| Bug fix applied | PATCH | 0.1.0 → 0.1.1 |
| Schema field added or removed | MAJOR | 0.1.1 → 1.0.0 |
| API endpoint renamed or response changed | MAJOR | 1.0.0 → 2.0.0 |
| Prompt template updated | PATCH | 0.3.0 → 0.3.1 |
| Refactor with no behaviour change | PATCH | 0.3.1 → 0.3.2 |
| New phase started | no bump — add to [Unreleased] | — |

### Milestone Versions to Target

| Version | Milestone |
|---|---|
| 0.1.0 | Phase 1 gate passes — API starts, health check returns 200 |
| 0.2.0 | Phase 2 gate passes — graph endpoint returns real data |
| 0.3.0 | Phase 3 gate passes — risk queue correctly ordered |
| 0.4.0 | Phase 4 gate passes — agent finds a pre-planted bug |
| 0.5.0 | Phase 5 gate passes — memory layer active, Run 2 differs from Run 1 |
| 0.6.0 | Phase 6 gate passes — report and generated tests working |
| 0.7.0 | Phase 7 gate passes — demo app running with all 4 bugs present |
| 0.8.0 | Phase 8 gate passes — dashboard fully connected to live API |
| 0.9.0 | Phase 9 gate passes — full integration smoke test passes, demo rehearsed |

`v1.0.0` is reserved for a future post-hackathon production release (CI/CD integration, multi-app support, real defect-history data source), not the hackathon demo. Do not auto-bump to 1.0.0 on Phase 9 — `0.9.0` is correct for "feature-complete hackathon demo".

---

## 16. DEVLOG.md — Format and Rules

### Initial file header

```markdown
# DEVLOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** YYYY-MM-DD
**Team:** Person A (AI/LLM), Person B (Backend), Person C (Frontend)

Chronological developer diary. Every session, decision, blocker, and resolution.
Read this file to understand WHY the project is in its current state.

---
```

### Entry format (one block per session/day)

```markdown
## YYYY-MM-DD — Day N — [Session title]
**Session start:** HH:MM  **Phase:** N — [name]  **Person:** A/B/C/All
**Goal:** [one sentence]

### What was done — bullet list (files, commands of note, gates passed/failed)
### Decisions made — Decision / Why / Alternatives considered
### Blockers encountered — Blocker / How resolved / Time lost / See BUGLOG BUG-XXX
### What was learned — anything unexpected about stack, API, or system behaviour
### Next session priorities — ordered list

### Session end: HH:MM
### Gate status: [PASSED / FAILED / PENDING] GATE N
```

**Add an entry:** at every session start and end; after every gate result; after any significant decision (dependency change, module redesign); after any blocker is resolved.

---

## 17. COMMANDLOG.md — Format and Rules

### Initial file header

```markdown
# COMMANDLOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** YYYY-MM-DD

Append-only chronological record of every terminal command run.

---
```

### Entry format (one block per command, no exceptions)

```markdown
### YYYY-MM-DD HH:MM — [Purpose in one line]
**Directory:** [working dir — use `(Get-Location).Path` in PowerShell]
**Command:** `[exact command as typed]`
**Exit code:** 0 (success) / N (failure) / — (background process)
**Output summary:** [key lines only — not full output]
**Result:** SUCCESS / FAILURE / PARTIAL
**Notes:** [only if unexpected, or if this led to a state change]
```

### Always log

- Every `pip install`, `npm install`, `playwright install`
- Every server start (`uvicorn`, `npm run dev`) — record process disposition
- Every API test (`curl`, `Invoke-RestMethod`)
- Every `pytest` run with pass/fail counts
- Every `git commit`, `git push`, branch switch
- Every command that errors (especially important)
- Every command run during a verification gate (§9)

---

## 18. BUGLOG.md — Format and Rules

### Initial file header

```markdown
# BUGLOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** YYYY-MM-DD

Bugs numbered sequentially: BUG-001, BUG-002, ...
Status: OPEN | INVESTIGATING | FIXED | WONTFIX | DEFERRED

---
```

### Entry format

```markdown
## BUG-XXX — [Short title] — Status: OPEN/FIXED
**Discovered:** YYYY-MM-DD HH:MM by [person / gate / Claude Code]
**Phase / File(s) / Severity:** CRITICAL | HIGH | MEDIUM | LOW

### Symptoms — exact error, observed behaviour, relevant traceback
### Reproduction steps — numbered, specific, with values and env state
### Root cause — confirmed only; leave "Under investigation" until confirmed
### Fix applied — before/after code snippet for small fixes; approach for larger
### Fix verified by — exact command/test/output

**Fixed:** YYYY-MM-DD HH:MM  **See also:** CHANGELOG vX.Y.Z
```

### Severity

| Severity | Definition |
|---|---|
| CRITICAL | Blocks all development or causes data loss — fix immediately |
| HIGH | Breaks a gate test or core feature — fix before next phase |
| MEDIUM | Works incorrectly but workaround exists — fix before integration |
| LOW | Cosmetic, edge-case, non-blocking — fix in polish |

---

## 19. Sync Rules — When to Update Which Files

Follow these without exception. Never skip a log update.

### After creating or modifying source files

| Action | CHANGELOG | DEVLOG | COMMANDLOG | CLAUDE.md to update |
|---|---|---|---|---|
| New file | `[Unreleased] Added` | "What was done" | log commands | §2 only if folder layout changed |
| Modified, non-breaking | `[Unreleased] Changed` | "What was done" | log commands | — |
| Schema field add/remove | MAJOR bump, before/after | decisions | log commands | **§5** |
| API endpoint add | `[Unreleased] Added` | decisions | log commands | **§6** |
| API endpoint change | MAJOR bump, before/after | decisions | log commands | **§6** |
| Prompt template change | PATCH | decisions + rationale | log commands | **§7** |
| Hard constraint change | MAJOR | decisions | log commands | **§1** |

### After running commands
Every `pip`/`npm`/`playwright install`, server start/stop, API test, pytest run, `git` op, and erroring command → COMMANDLOG every time. Also DEVLOG if it's a gate test, blocked work, or a significant `git` action (merge, branch switch).

### Gate result rules

- **Passed:** COMMANDLOG (cmd + output) → CHANGELOG (bump to milestone version per §15) → DEVLOG (PASSED, lessons, next priorities) → CLAUDE.md (only if the gate definition was wrong).
- **Failed:** COMMANDLOG (failed cmd + error) → DEVLOG (what failed, what was tried) → BUGLOG (open BUG-XXX if defect) → do **not** bump CHANGELOG version.

### After fixing a bug
BUGLOG status → FIXED with root cause + fix; CHANGELOG PATCH entry citing BUG-XXX; DEVLOG resolution note in "Blockers encountered"; COMMANDLOG verification commands. If the bug revealed an incorrect rule, update the relevant CLAUDE.md section.

### After any schema or API change (most important)
Atomically update **all** of these before writing any other code:
1. `api/models.py` — the Pydantic model
2. CLAUDE.md §5 — JSON example
3. CLAUDE.md §6 — endpoint spec if response changed
4. CHANGELOG — MAJOR bump with before/after
5. DEVLOG — decision + why
6. Every consumer of the changed model

### End-of-session checklist
- DEVLOG end time, gate status, next priorities written
- COMMANDLOG: every command from this session logged
- CHANGELOG: `[Unreleased]` reflects today's changes
- BUGLOG: today's bugs entered; fixed ones updated to FIXED
- CLAUDE.md: any constraint/schema changes reflected in the right section

---

## 20. Log File Bootstrap (Windows / PowerShell)

This repo is developed on Windows + PowerShell, so the project does **not** use the bash `cat > file << 'EOF'` heredoc bootstrap pattern — it does not parse in `powershell.exe` 5.1 and the `$(date)` expansions don't expand. Instead, do one of the following during Phase 1 Step 1.4–1.7:

**Option A — manual (recommended for clarity):** Create `logs/` in your editor, then create each of the four files and paste the corresponding initial-file header from §§15–18, replacing `YYYY-MM-DD` with today's date and `HH:MM` with the current time. Commit them in a single Phase 1 setup commit.

**Option B — scripted in PowerShell:** Use single-quoted here-strings so PowerShell does not try to expand `$()` or backticks:

```powershell
New-Item -ItemType Directory -Force -Path logs | Out-Null
$today = Get-Date -Format 'yyyy-MM-dd'
$now   = Get-Date -Format 'HH:mm'

# Paste the §15 CHANGELOG header into a single-quoted here-string, replace dates
@"
# CHANGELOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** $today
...
"@ | Set-Content -Path logs\CHANGELOG.md -Encoding utf8
```

Repeat for DEVLOG.md, COMMANDLOG.md, BUGLOG.md using their respective §16 / §17 / §18 headers. Always use `-Encoding utf8` so downstream tools (git, Python, Node) read the file without a UTF-16 BOM.

---

## 21. Python Coding Standards

Apply every rule in this section to every `.py` file written in this project without exception.

### 21.1 File Structure — Every Python file must follow this order

```python
# 1. Module docstring (required on every file)
"""
Module: engine/crawler.py
Purpose: Discover all routes, pages, forms, and interactive elements by visiting
         the application with Playwright headless browser.
Author: Team / Claude Code
Created: YYYY-MM-DD
"""

# 2. Standard library imports (alphabetical)
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# 3. Third-party imports (alphabetical)
import networkx as nx
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# 4. Internal imports (alphabetical)
from api.models import GraphNode, NodeType

# 5. load_dotenv() immediately after imports if this file uses env vars
load_dotenv()

# 6. Module-level constants (SCREAMING_SNAKE_CASE)
MAX_CRAWL_DEPTH = 3
PAGE_TIMEOUT_MS = 8000

# 7. Classes, then functions, then module-level code
```

### 21.2 Type Hints — Required on every function

Every function and method must have full type hints on all parameters and the return type.
No exceptions — not even for simple helper functions.

```python
# WRONG — no type hints
def compute_risk(url, defects, commits):
    return defects * 0.4 + commits * 0.35

# CORRECT — full type hints
def compute_risk(url: str, defects: float, commits: float) -> float:
    return defects * 0.4 + commits * 0.35

# For complex types, use typing module
from typing import Optional, List, Dict, Tuple, Any

async def explore_node(
    node: GraphNode,
    persona_actions: List[Dict[str, Any]],
    app_url: str,
    timeout_ms: int = 8000
) -> List[Dict[str, Any]]:
    ...

# For functions that return nothing
def update_state(scan_id: str, progress: int) -> None:
    ...

# For optional parameters
def query_memory(node_id: str, context: str, top_k: int = 3) -> Optional[List[Dict]]:
    ...
```

### 21.3 Docstrings — Required on every class and function

Use Google-style docstrings. Every function needs: a one-line summary, Args section (if it has parameters), Returns section (if it returns something), Raises section (if it raises exceptions).

```python
# WRONG — no docstring
def safe_parse_json(text: str) -> Optional[dict]:
    text = re.sub(r'```(?:json)?\s*', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

# CORRECT — Google-style docstring
def safe_parse_json(text: str) -> Optional[dict | list]:
    """Parse JSON from an LLM response, handling markdown code fences.

    Strips triple-backtick fences (with or without 'json' label) before
    parsing. Falls back to regex extraction if direct parse fails.

    Args:
        text: Raw string output from a Claude API response.

    Returns:
        Parsed Python dict or list if JSON found, None if parsing fails.

    Raises:
        Does not raise — all exceptions are caught and return None.
    """
    text = re.sub(r'```(?:json)?\s*', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None
```

### 21.4 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Variables | `snake_case` | `risk_score`, `node_id` |
| Functions | `snake_case` | `compute_risk_score()`, `build_graph()` |
| Classes | `PascalCase` | `AgentMemory`, `RiskScorer` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_CRAWL_DEPTH`, `PAGE_TIMEOUT_MS` |
| Private methods | `_leading_underscore` | `_embed()`, `_build_finding()` |
| Async functions | `snake_case` same as sync | `async def explore_node()` |
| File names | `snake_case` | `graph_builder.py`, `risk_scorer.py` |
| Test functions | `test_` prefix | `test_checkout_form_rejects_empty_input` |

### 21.5 Constants — Never use magic numbers or magic strings inline

Every number and string that appears more than once OR has a non-obvious meaning must be a named constant at the top of the file or in a shared constants module.

```python
# WRONG — magic numbers scattered through code
if risk_score >= 0.8:
    band = "critical"
elif risk_score >= 0.6:
    band = "high"

# CORRECT — named constants
RISK_THRESHOLD_CRITICAL = 0.8
RISK_THRESHOLD_HIGH = 0.6
RISK_THRESHOLD_MEDIUM = 0.4

RISK_BAND_CRITICAL = "critical"
RISK_BAND_HIGH = "high"
RISK_BAND_MEDIUM = "medium"
RISK_BAND_LOW = "low"

if risk_score >= RISK_THRESHOLD_CRITICAL:
    band = RISK_BAND_CRITICAL
elif risk_score >= RISK_THRESHOLD_HIGH:
    band = RISK_BAND_HIGH
```

### 21.6 Error Handling — Be explicit and specific

```python
# WRONG — bare except, swallows everything silently
try:
    result = json.loads(text)
except:
    pass

# WRONG — too broad, logs nothing
try:
    result = some_function()
except Exception:
    return None

# CORRECT — specific exception, log the error, graceful return
import logging
logger = logging.getLogger(__name__)

try:
    result = json.loads(text)
except json.JSONDecodeError as e:
    logger.warning(f"JSON parse failed for input '{text[:100]}...': {e}")
    return None
except ValueError as e:
    logger.error(f"Unexpected value error in JSON parse: {e}")
    return None
```

Every module must define its own logger at the top:
```python
import logging
logger = logging.getLogger(__name__)
```

Never use `print()` for logging in production code — use `logger.debug/info/warning/error`.

### 21.7 Async Rules

```python
# WRONG — blocking call inside async function
async def explore(url: str) -> List[dict]:
    time.sleep(2)          # blocks the event loop
    result = requests.get(url)  # blocking HTTP

# CORRECT — async equivalents
async def explore(url: str) -> List[dict]:
    await asyncio.sleep(2)         # non-blocking
    async with httpx.AsyncClient() as client:
        result = await client.get(url)  # non-blocking

# WRONG — running async from sync context incorrectly
result = explore("http://localhost:3001")  # returns coroutine, not result

# CORRECT — use asyncio.run() only at top-level entry points
result = asyncio.run(explore("http://localhost:3001"))

# Inside FastAPI route handlers — use await directly
@app.post("/scan")
async def start_scan(request: ScanRequest):
    asyncio.create_task(run_scan(request))  # non-blocking background task
    return ScanResponse(...)
```

### 21.8 Imports — Absolute, never relative (except within same package)

```python
# WRONG — relative imports across packages
from ..engine.memory import AgentMemory
from .models import GraphNode

# CORRECT — absolute imports
from engine.memory import AgentMemory
from api.models import GraphNode

# Within the same package, relative is acceptable
# Inside agent/gap_analyser.py importing from agent/personas.py:
from agent.personas import PersonaEngine  # absolute preferred
```

### 21.9 Functions — Single responsibility, max 50 lines

Every function does exactly one thing. If a function exceeds 50 lines, split it.

```python
# WRONG — one giant function doing crawl + graph + score
async def run_full_analysis(url: str) -> dict:
    # 200 lines of mixed concerns

# CORRECT — each step is its own function
async def crawl_application(url: str) -> List[dict]:
    """Discover all routes and elements."""
    ...

def build_coverage_graph(elements: List[dict], coverage_path: str) -> nx.DiGraph:
    """Construct NetworkX graph from crawl results."""
    ...

def score_graph_nodes(graph: nx.DiGraph) -> nx.DiGraph:
    """Apply risk scores to all nodes."""
    ...

async def run_full_analysis(url: str) -> dict:
    """Orchestrate the full analysis pipeline."""
    elements = await crawl_application(url)
    graph = build_coverage_graph(elements, COVERAGE_PATH)
    scored_graph = score_graph_nodes(graph)
    return scored_graph
```

### 21.10 Pydantic Models — Validation everywhere

```python
# WRONG — raw dict passed around
def store_finding(finding: dict) -> None:
    node_id = finding["node_id"]  # KeyError risk

# CORRECT — Pydantic model, validated at boundary
from api.models import Finding

def store_finding(finding: Finding) -> None:
    node_id = finding.node_id  # type-safe, validated
```

Always validate at the boundary (when data enters from external sources like Claude API or Playwright). Inside the system, pass Pydantic objects not raw dicts.

### 21.11 Environment Variables — Validated at startup

```python
# WRONG — silent None if key missing
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)  # fails later with cryptic error

# CORRECT — validate at startup, fail fast with clear message
def get_required_env(key: str) -> str:
    """Get required environment variable, raising clear error if missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in your values."
        )
    return value

ANTHROPIC_API_KEY = get_required_env("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
```

---

## 22. JavaScript / React Coding Standards

Apply every rule in this section to every `.jsx`, `.js` file in `dashboard/` and `demo-app/`.

### 22.1 File Structure — Every component file

```jsx
// 1. React and hook imports
import { useState, useEffect, useCallback, useRef } from "react";

// 2. Third-party library imports (alphabetical)
import * as d3 from "d3";

// 3. Internal imports (alphabetical by path)
import { fetchGraph, fetchFindings } from "../api";
import MetricCards from "./MetricCards";

// 4. Constants (SCREAMING_SNAKE_CASE)
const POLL_INTERVAL_MS = 3000;
const API_BASE = "http://localhost:8000";

// 5. Component definition — always named, never anonymous default export inline
function CoverageGraph({ onNodeClick, scanId }) {
  // 6. State declarations first
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 7. Refs
  const svgRef = useRef(null);

  // 8. Effects
  useEffect(() => { ... }, [scanId]);

  // 9. Handlers (useCallback for handlers passed as props)
  const handleNodeClick = useCallback((node) => {
    onNodeClick?.(node);
  }, [onNodeClick]);

  // 10. Render helpers (small functions that return JSX)
  const renderNodeBadge = (riskBand) => { ... };

  // 11. Return — JSX only, no logic here
  return (
    <div className="coverage-graph">
      ...
    </div>
  );
}

// 12. Named export at bottom
export default CoverageGraph;
```

### 22.2 PropTypes / TypeScript-style prop documentation

Since this project uses React (not TypeScript), document all props with a JSDoc comment above every component:

```jsx
/**
 * CoverageGraph — D3.js force-directed graph of application coverage.
 *
 * @param {string|null} scanId - Active scan ID to poll for graph updates. Null if no scan active.
 * @param {Function} onNodeClick - Called with node data when a graph node is clicked.
 * @param {boolean} showMemoryIndicators - Whether to show memory indicator icons on nodes.
 */
function CoverageGraph({ scanId, onNodeClick, showMemoryIndicators = false }) {
```

### 22.3 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Components | `PascalCase` | `CoverageGraph`, `ScanControl` |
| Functions / handlers | `camelCase` | `handleNodeClick`, `fetchGraph` |
| Variables | `camelCase` | `riskScore`, `nodeId` |
| Constants | `SCREAMING_SNAKE_CASE` | `POLL_INTERVAL_MS`, `API_BASE` |
| CSS classes | `kebab-case` | `coverage-graph`, `risk-badge` |
| Files | `PascalCase` for components | `CoverageGraph.jsx` |
| Hook files | `camelCase` with `use` prefix | `usePolling.js` |
| Boolean variables | `is/has/should` prefix | `isLoading`, `hasError`, `shouldPoll` |

### 22.4 State Management Rules

```jsx
// WRONG — mutating state directly
const addFinding = (finding) => {
  findings.push(finding);  // mutates array, React won't re-render
  setFindings(findings);
};

// CORRECT — new array reference
const addFinding = (finding) => {
  setFindings(prev => [...prev, finding]);
};

// WRONG — multiple related state updates without batching
setLoading(true);
setData(null);
setError(null);

// CORRECT — use useReducer for complex related state, or batch with React 18 automatic batching
// For simple cases, React 18 batches these automatically inside event handlers and effects
```

### 22.5 useEffect Rules

```jsx
// WRONG — missing dependency array (runs on every render)
useEffect(() => {
  fetchData();
});

// WRONG — missing dependency (stale closure)
useEffect(() => {
  fetchData(scanId);  // scanId used but not listed
}, []);

// CORRECT — all dependencies listed
useEffect(() => {
  if (!scanId) return;
  fetchData(scanId);
}, [scanId]);

// CORRECT — cleanup for intervals and subscriptions
useEffect(() => {
  if (!isPolling) return;
  const interval = setInterval(() => {
    fetchFindings(scanId).then(setFindings);
  }, POLL_INTERVAL_MS);
  return () => clearInterval(interval);  // cleanup on unmount or dep change
}, [scanId, isPolling]);
```

### 22.6 API Calls — Always in `api.js`, never inline in components

```jsx
// WRONG — fetch inside component
function FindingsFeed() {
  useEffect(() => {
    fetch("http://localhost:8000/findings")  // hardcoded URL in component
      .then(r => r.json())
      .then(setFindings);
  }, []);
}

// CORRECT — all API calls in dashboard/src/api.js
// api.js:
const API_BASE = "http://localhost:8000";

export async function fetchFindings(scanId = null, severity = null) {
  const params = new URLSearchParams();
  if (scanId) params.append("scan_id", scanId);
  if (severity) params.append("severity", severity);
  const res = await fetch(`${API_BASE}/findings?${params}`);
  if (!res.ok) throw new Error(`GET /findings failed: ${res.status}`);
  return res.json();
}

// Component:
import { fetchFindings } from "../api";
useEffect(() => {
  fetchFindings(scanId).then(setFindings).catch(setError);
}, [scanId]);
```

### 22.7 Error Handling in Components

Every component that makes API calls must have:
- A loading state displayed while fetching
- An error state displayed if the call fails
- Never a blank screen when data is missing

```jsx
function RiskQueue({ scanId }) {
  const [queue, setQueue] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setIsLoading(true);
    fetchQueue(scanId)
      .then(data => { setQueue(data.queue); setError(null); })
      .catch(err => setError(err.message))
      .finally(() => setIsLoading(false));
  }, [scanId]);

  if (isLoading) return <div className="loading">Loading queue...</div>;
  if (error) return <div className="error">Failed to load queue: {error}</div>;
  if (!queue.length) return <div className="empty">No gaps found yet.</div>;

  return <ul>{queue.map(item => <QueueItem key={item.node_id} item={item} />)}</ul>;
}
```

### 22.8 Keys in Lists — Always stable, never array index

```jsx
// WRONG — index as key (causes issues with reordering/dynamic lists)
{findings.map((finding, index) => (
  <FindingCard key={index} finding={finding} />
))}

// CORRECT — stable unique ID as key
{findings.map(finding => (
  <FindingCard key={finding.id} finding={finding} />
))}
```

### 22.9 Demo App data-testid Requirement

Every interactive element in `demo-app/` must have a `data-testid` attribute.
This is non-negotiable — Playwright relies on these for reliable test generation.

```jsx
// WRONG — no data-testid
<button onClick={handleLogin}>Login</button>
<input type="password" value={password} onChange={e => setPassword(e.target.value)} />

// CORRECT — data-testid on every interactive element
<button data-testid="login-btn" onClick={handleLogin}>Login</button>
<input
  data-testid="password-input"
  type="password"
  value={password}
  onChange={e => setPassword(e.target.value)}
/>
<span data-testid="login-error-msg" className="error">{loginError}</span>
```

---

## 23. General Code Quality Rules

These rules apply to every file in the project — Python, JavaScript, JSX, markdown, JSON, and shell scripts.

### 23.1 The Single Responsibility Rule

Every file, class, and function does exactly one thing and has one reason to change.

| File | Does exactly | Does NOT do |
|---|---|---|
| `crawler.py` | Discover app routes and elements | Build graphs, score risk, call LLM |
| `risk_scorer.py` | Compute risk scores | Fetch data, update graph, call LLM |
| `memory.py` | Store and retrieve vector embeddings | Score risk, generate tests, call LLM |
| `CoverageGraph.jsx` | Render the D3 graph | Fetch data itself, manage scan state |
| `api.js` | All HTTP calls to the backend | Render UI, manage component state |

### 23.2 No Dead Code

Never leave commented-out code in committed files. If code is removed, remove it completely.
If it might be needed later, note it in `DEVLOG.md` instead of commenting it out.

```python
# WRONG — commented out code left in file
def compute_risk(url: str) -> float:
    # old_score = url_length * 0.1  # tried this, didn't work
    # return old_score
    return new_risk_formula(url)

# CORRECT — clean, no history preserved in code (history is in git)
def compute_risk(url: str) -> float:
    return new_risk_formula(url)
```

### 23.3 No Magic Numbers or Strings Anywhere

```python
# WRONG
if similarity > 0.85:        # what is 0.85?
    adjustment += 0.15       # why 0.15?

# CORRECT
MEMORY_SIMILARITY_THRESHOLD = 0.85   # defined in constants
MEMORY_RISK_INCREASE = 0.15          # from CLAUDE.md Section 13

if similarity > MEMORY_SIMILARITY_THRESHOLD:
    adjustment += MEMORY_RISK_INCREASE
```

### 23.4 Fail Fast, Fail Loudly at Startup

At application startup, validate everything that is required. Never let a missing config
cause a cryptic error 10 minutes into a scan.

```python
# In api/main.py startup event:
@app.on_event("startup")
async def startup_validation():
    """Validate all required config and dependencies at startup."""
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set. Check your .env file.")

    # Check data files exist
    required_files = [
        "data/simulated_defect_history.csv",
        "data/simulated_change_frequency.csv",
        "data/existing_tests_mock.json",
    ]
    for path in required_files:
        if not Path(path).exists():
            raise RuntimeError(f"Required data file missing: {path}")

    # Check output directories writable
    Path("screenshots").mkdir(exist_ok=True)
    Path("tests/generated").mkdir(parents=True, exist_ok=True)

    logger.info("✓ Startup validation passed")
```

### 23.5 Logging Levels — Use Correctly

| Level | When to use | Example |
|---|---|---|
| `DEBUG` | Detailed internal state, loop iterations | `logger.debug(f"Processing node {node_id}")` |
| `INFO` | High-level progress, gate events | `logger.info(f"Scan {scan_id} started")` |
| `WARNING` | Recoverable issues, fallback used | `logger.warning(f"Coverage file not found, treating all nodes as uncovered")` |
| `ERROR` | Failed operation, returning error state | `logger.error(f"Claude API call failed: {e}")` |
| `CRITICAL` | System cannot continue | `logger.critical(f"ChromaDB unavailable: {e}")` |

Never use `print()` in any Python file. Use the module logger.

### 23.6 Function Length and Complexity Limits

| Metric | Limit | Action if exceeded |
|---|---|---|
| Function length | 50 lines | Split into smaller functions |
| Nesting depth | 3 levels | Extract inner logic to named function |
| Parameters | 5 | Group into a dataclass or Pydantic model |
| Return points | 3 | Restructure with early returns or extract logic |

### 23.7 Comments — Explain Why, Not What

Code explains what. Comments explain why.

```python
# WRONG — comment states what the code obviously does
risk_score = min(1.0, base_score + adjustment)  # clamp to 1.0

# CORRECT — comment explains why this choice was made
# Clamp to 1.0 to prevent runaway risk scores when multiple
# unresolved memory findings stack up on the same node
risk_score = min(1.0, base_score + adjustment)

# WRONG — comment restates the code
x = x + 0.15  # add 0.15 to x

# CORRECT — use a named constant instead, no comment needed
risk_score = risk_score + MEMORY_RISK_INCREASE
```

### 23.8 Git Commit Message Standards

Every commit must follow this format:

```
type(scope): short description (max 72 chars)

Optional body explaining WHY this change was made.
Reference: BUGLOG BUG-XXX or CHANGELOG vX.Y.Z
```

Types:
- `feat` — new feature or file
- `fix` — bug fix
- `refactor` — code change with no behaviour change
- `test` — adding or modifying tests
- `docs` — documentation or log files only
- `chore` — config, dependencies, tooling

Examples:
```
feat(engine): add crawler.py with Playwright route discovery
fix(memory): handle empty ChromaDB collection on first run (BUG-001)
refactor(risk_scorer): extract criticality lookup to named constants
docs(logs): add DEVLOG entry for Phase 2 gate pass
chore(deps): pin chromadb to 0.5.3 to avoid breaking API change
```

### 23.9 No `TODO` or `FIXME` Left in Committed Code

If something is not done, do not commit it with a `TODO` comment. Either:
- Finish it before committing, or
- Open a BUGLOG entry with severity LOW and reference it in DEVLOG

```python
# WRONG — committed TODO
def build_graph(elements):
    # TODO: handle authentication-gated routes
    pass

# CORRECT — log it, don't commit it
# In BUGLOG.md:
## BUG-004 — Auth-gated routes not handled in crawler — Status: OPEN
# In code — either implement it or skip gracefully with a log:
def build_graph(elements: List[dict]) -> nx.DiGraph:
    """Build graph. Note: auth-gated routes are skipped (see BUGLOG BUG-004)."""
    ...
```

### 23.10 Self-Review Checklist

Before considering any file complete, Claude Code must verify:

**For Python files:**
```
[ ] Module docstring present at top
[ ] All imports grouped and ordered (stdlib → third-party → internal)
[ ] load_dotenv() called if file uses env vars
[ ] All functions have type hints
[ ] All functions have Google-style docstrings
[ ] No magic numbers — all are named constants
[ ] No bare except blocks
[ ] Module logger defined: logger = logging.getLogger(__name__)
[ ] No print() statements
[ ] No commented-out code
[ ] No function longer than 50 lines
[ ] All Pydantic models imported from api/models.py
```

**For React/JSX files:**
```
[ ] Component has JSDoc comment with all props documented
[ ] All state variables have meaningful names (not data, info, stuff)
[ ] All boolean state vars use is/has/should prefix
[ ] useEffect has correct dependency array
[ ] Polling effects have cleanup (return () => clearInterval/clearTimeout)
[ ] All API calls are in api.js, not inline
[ ] Loading, error, and empty states all handled
[ ] All list items have stable key prop (never array index)
[ ] All interactive elements in demo-app have data-testid
[ ] No console.log left in committed code
[ ] No inline styles — use className only
```

**For all files:**
```
[ ] No TODO or FIXME comments
[ ] No hardcoded secrets, keys, or passwords
[ ] No hardcoded URLs except localhost ports defined in Section 13
[ ] File name matches its exported class/function name
[ ] DEVLOG and CHANGELOG updated if this file is new or significantly changed
```

---

*CLAUDE.md v3.0 — Exploratory Testing & Coverage Gap Discovery Agent*
*Base document: exploratory_testing_agent_project_plan.md*
*Coding standards added: Sections 21–23*
*Logging system: Sections 14–20*
