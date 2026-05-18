"""
Module: api/main.py
Purpose: FastAPI application entry point. Mounts every route module, configures
         CORS for the React dashboard, and serves screenshots as static files.
         Run with: uvicorn api.main:app --reload --port 8000
Created: 2026-05-13
"""

import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

# Import all route modules — order doesn't matter for correctness, only readability.
from api.routes import (  # noqa: E402  (must come after load_dotenv)
    findings,
    graph,
    memory_routes,
    queue,
    report,
    scan,
    scan_status,
)

app = FastAPI(title="Exploratory Testing Agent API", version="0.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist — runtime artefacts not in git.
Path("screenshots").mkdir(exist_ok=True)
Path("tests/generated").mkdir(parents=True, exist_ok=True)

# Serve screenshots as static files at /screenshots/{filename}
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
async def health() -> dict:
    """Health check used by Gate 1 and by the dashboard during scan polling."""
    return {"status": "ok", "service": "exploratory-agent"}
