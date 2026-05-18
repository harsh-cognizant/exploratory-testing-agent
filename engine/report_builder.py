"""
Module: engine/report_builder.py
Purpose: Compile the final gap report from scan state. Aggregates findings,
         generated tests, coverage stats, and risk breakdown into the
         ReportResponse schema per CLAUDE.md §4.15.
Author: Team / Claude Code
Created: 2026-05-14
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def compile_report(
    scan_state: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the complete gap report from a finished scan's state.

    Per CLAUDE.md §4.15: the report aggregates scan-level metrics, findings
    by severity, generated tests by page, and before/after coverage stats.

    Args:
        scan_state: The SCAN_STATE dict for a completed scan.

    Returns:
        Dict matching the ReportResponse schema.
    """
    graph = scan_state.get("graph")
    findings = scan_state.get("findings", [])
    generated_tests = scan_state.get("generated_tests", [])

    # Compute coverage stats.
    total_nodes = 0
    covered_before = 0
    covered_after = 0

    if graph:
        total_nodes = graph.number_of_nodes()
        for _, attrs in graph.nodes(data=True):
            if attrs.get("covered"):
                covered_before += 1

    # After agent explores, any node with findings is now "explored"
    # so coverage_after includes explored nodes.
    explored_nodes = set()
    for f in findings:
        explored_nodes.add(f.get("node_id", ""))

    covered_after = covered_before + len(explored_nodes)
    if covered_after > total_nodes:
        covered_after = total_nodes

    coverage_before_pct = round((covered_before / total_nodes) * 100, 1) if total_nodes else 0.0
    coverage_after_pct = round((covered_after / total_nodes) * 100, 1) if total_nodes else 0.0

    # Severity counts.
    severity_counts: Dict[str, int] = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    for f in findings:
        sev = f.get("severity", "medium")
        if hasattr(sev, "value"):
            sev = sev.value
        if sev in severity_counts:
            severity_counts[sev] += 1

    critical_findings = severity_counts["critical"] + severity_counts["high"]

    # Sort findings by severity weight (critical first).
    severity_weight = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_findings = sorted(
        findings,
        key=lambda f: severity_weight.get(
            f.get("severity", "medium") if isinstance(f.get("severity"), str)
            else getattr(f.get("severity", "medium"), "value", "medium"),
            4,
        ),
    )

    report = {
        "total_gaps": len(findings),
        "critical_findings": critical_findings,
        "coverage_before_percent": coverage_before_pct,
        "coverage_after_percent": coverage_after_pct,
        "findings": sorted_findings,
        "generated_tests": generated_tests,
        "severity_breakdown": severity_counts,
        "summary": _build_summary(
            len(findings), critical_findings,
            coverage_before_pct, coverage_after_pct,
            len(generated_tests),
        ),
    }

    logger.info(
        "Report compiled: %d findings, %d tests, coverage %.1f%% → %.1f%%",
        len(findings), len(generated_tests),
        coverage_before_pct, coverage_after_pct,
    )
    return report


def _build_summary(
    total_gaps: int,
    critical_findings: int,
    coverage_before: float,
    coverage_after: float,
    test_count: int,
) -> str:
    """Build a human-readable summary paragraph for the report.

    Args:
        total_gaps: Total number of findings.
        critical_findings: Count of critical + high findings.
        coverage_before: Coverage percentage before agent run.
        coverage_after: Coverage percentage after agent run.
        test_count: Number of generated tests.

    Returns:
        Summary string.
    """
    coverage_improvement = round(coverage_after - coverage_before, 1)

    return (
        f"The exploratory testing agent discovered {total_gaps} coverage gap(s), "
        f"of which {critical_findings} are high or critical severity. "
        f"Coverage improved from {coverage_before}% to {coverage_after}% "
        f"(+{coverage_improvement}%). "
        f"{test_count} automated test(s) were generated to prevent regressions."
    )
