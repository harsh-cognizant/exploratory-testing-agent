# 🤖 Exploratory Testing & Coverage Gap Discovery Agent

An AI-powered autonomous agent that explores web applications, discovers untested areas (coverage gaps), and generates Pytest test cases for everything it finds. It does NOT run existing tests — it **discovers missing tests**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React + D3.js Dashboard (port 3000)   │
│   ScanControl │ CoverageGraph │ FindingsFeed │ Report   │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend (port 8000)            │
│   POST /scan  │ GET /graph │ GET /findings │ GET /report│
└────────┬───────────┬──────────┬──────────┬──────────────┘
         │           │          │          │
┌────────▼──┐ ┌──────▼────┐ ┌──▼──────┐ ┌─▼──────────┐
│ Crawler   │ │ Graph     │ │Explorer │ │ Test       │
│ (PW BFS)  │ │ Builder   │ │(PW+LLM)│ │ Generator  │
└───────────┘ │ (NetworkX)│ └─────────┘ │ (LLM→Pytest)│
              └───────────┘             └─────────────┘
                    │           │              │
              ┌─────▼─────┐ ┌──▼──────┐       │
              │Risk Scorer│ │ Memory  │       │
              │ (3-factor)│ │(ChromaDB)│       │
              └───────────┘ └─────────┘       │
                                         ┌────▼────┐
                                         │ Report  │
                                         │ Builder │
                                         └─────────┘
```

### Five Layers

| Layer | Purpose | Key Module |
|-------|---------|------------|
| 1. Coverage Intelligence Graph | Discover all routes, forms, buttons | `engine/crawler.py` + `engine/graph_builder.py` |
| 2. Risk Prioritisation Engine | Score and rank gaps by risk | `engine/risk_scorer.py` |
| 3. Behavioural Exploration | 3 AI personas explore the app | `agent/personas.py` + `engine/explorer.py` |
| 4. Memory & Learning Loop | Remember findings across runs | `engine/memory.py` (ChromaDB) |
| 5. Output & Test Generation | Auto-generate Pytest tests | `agent/test_generator.py` + `engine/report_builder.py` |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Chrome browser installed

### 1. Clone & Install

```powershell
git clone https://github.com/harshkumarshaw/exploratory-testing-agent.git
cd exploratory-testing-agent

# Python dependencies
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Demo app
cd demo-app
npm install
cd ..

# Dashboard
cd dashboard
npm install
cd ..
```

### 2. Configure Environment

Create a `.env` file in the project root (copy from `.env.example`):

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://openrouter.ai/api    # Optional: for OpenRouter
ANTHROPIC_MODEL=meta-llama/llama-3.3-70b-instruct:free  # Optional: override model
APP_URL=http://localhost:3001
MAX_NODES=50
SCAN_TIMEOUT_SECONDS=180
SCREENSHOTS_DIR=./screenshots
CHROMA_PATH=./chroma_store
TESTS_OUTPUT_DIR=./tests/generated
```

For **demo/presentation mode** (browser visible, slow motion):
```env
EXPLORER_HEADLESS=false
CRAWLER_HEADLESS=false
EXPLORER_SLOW_MO_MS=500
CRAWLER_SLOW_MO_MS=500
```

### 3. Run All Three Services

```powershell
# Terminal 1: Demo App (port 3001)
cd demo-app; npm run dev

# Terminal 2: Backend API (port 8000)
uvicorn api.main:app --port 8000

# Terminal 3: Dashboard (port 3000)
cd dashboard; npm run dev
```

### 4. Open Dashboard & Scan

1. Open **http://localhost:3000** in your browser
2. Click **▶ Start Scan**
3. Watch the AI explore the app in real-time
4. View findings, generated tests, and the coverage graph

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scan` | Start a new scan |
| `GET` | `/scan/{id}/status` | Poll scan progress |
| `GET` | `/graph` | Coverage intelligence graph |
| `GET` | `/queue` | Risk-ranked exploration queue |
| `GET` | `/findings` | All discovered anomalies |
| `GET` | `/memory` | Past scan history from ChromaDB |
| `GET` | `/report` | Full report with generated tests |
| `GET` | `/health` | Health check |

## 🐛 Demo App Bugs

The demo app (`demo-app/`) ships with 6 pre-planted bugs for testing:

| Bug | Page | Severity | Description |
|-----|------|----------|-------------|
| BUG-001 | `/login` | HIGH | Empty password accepted |
| BUG-002 | `/products` | MEDIUM | Cart count shows NaN for qty > 5 |
| BUG-003 | `/cart` | HIGH | Negative quantity accepted |
| BUG-004 | `/checkout` | HIGH | Invalid card number accepted |
| BUG-005 | `/cart`, `/checkout` | HIGH | No auth guard on protected routes |
| BUG-006 | `/cart` | MEDIUM | Non-numeric quantity removes item |

## 🧪 AI Personas

The agent uses three distinct personas during exploration:

- **Confused User** — submits wrong data types, leaves fields empty, navigates backwards
- **Power User** — rapid clicks, keyboard shortcuts, unexpected autofill formats
- **Malicious User** — SQL injection strings, XSS payloads, oversized inputs

## 📁 Project Structure

```
├── agent/           # AI orchestration (brain, personas, gap analyser, test gen)
├── engine/          # Core engines (crawler, explorer, memory, risk scorer)
├── api/             # FastAPI backend (routes, models)
├── dashboard/       # React + D3.js frontend
├── demo-app/        # Next.js demo app with pre-planted bugs
├── data/            # Simulated defect/change history CSV files
├── logs/            # CHANGELOG, DEVLOG, COMMANDLOG, BUGLOG
├── screenshots/     # Anomaly evidence (auto-generated)
├── tests/generated/ # AI-generated Pytest tests
└── chroma_store/    # ChromaDB vector memory (auto-generated)
```

## 👨‍💻 Author

**Harsh Kumar Shaw**

## 📄 License

This project is for educational and demonstration purposes.
