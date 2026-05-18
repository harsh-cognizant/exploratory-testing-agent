"""
Module: api/models.py
Purpose: Canonical Pydantic models for the entire project. Every API route,
         engine module, and agent module imports its data types from here.
         Never redefine these models elsewhere.
Created: 2026-05-13
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


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
    # Coverage stats — computed from the graph when available.
    covered_nodes: int = 0
    gap_nodes: int = 0
    coverage_percent: float = 0.0


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
