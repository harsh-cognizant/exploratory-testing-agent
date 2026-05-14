"""
Module: engine/risk_scorer.py
Purpose: Compute risk scores for every graph node using the canonical three-factor
         formula from CLAUDE.md §4.8:

             risk_score = (0.35 * change_frequency)
                        + (0.40 * defect_density)
                        + (0.25 * criticality)

         Annotates nodes in-place (`risk_score`, `risk_band`,
         `defect_count_historical`, `business_criticality`) and provides
         `build_queue` for the /queue endpoint.
Created: 2026-05-14
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from api.models import QueueItem, RiskBand

logger = logging.getLogger(__name__)

# Weights — sum to 1.0 exactly per CLAUDE.md §1 hard constraint.
W_CHANGE_FREQUENCY: float = 0.35
W_DEFECT_DENSITY: float = 0.40
W_CRITICALITY: float = 0.25

# Risk-band thresholds per CLAUDE.md §4.8.
RISK_THRESHOLD_CRITICAL: float = 0.8
RISK_THRESHOLD_HIGH: float = 0.6
RISK_THRESHOLD_MEDIUM: float = 0.4

# Default for nodes whose URL is not present in the simulated CSVs.
DEFAULT_FACTOR_VALUE: float = 0.1

# Criticality lookup — keys are URL substrings; first match wins per insertion
# order. Values copied verbatim from CLAUDE.md §4.8.
CRITICALITY_MAP: Dict[str, float] = {
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
}
DEFAULT_CRITICALITY: float = 0.4

# Map criticality bucket → business_criticality label written to the node.
def _criticality_label(value: float) -> str:
    if value >= 0.9:
        return "high"
    if value >= 0.6:
        return "medium"
    return "low"


# Data file locations relative to repo root.
DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DEFECT_CSV: Path = DATA_DIR / "simulated_defect_history.csv"
DEFAULT_CHANGE_CSV: Path = DATA_DIR / "simulated_change_frequency.csv"


def _load_csv_factor(csv_path: Path, value_column: str) -> Dict[str, float]:
    """Read a two-column simulated-history CSV and return a raw {url: value} map.

    Args:
        csv_path: Path to the CSV file.
        value_column: Name of the numeric column to extract.

    Returns:
        Dict keyed by URL with the raw integer/float value. Empty dict if the
        file is missing or unreadable — caller treats absence as zero and
        applies DEFAULT_FACTOR_VALUE downstream.
    """
    if not csv_path.is_file():
        logger.warning("Factor CSV not found at %s; nodes will use default %.2f", csv_path, DEFAULT_FACTOR_VALUE)
        return {}
    out: Dict[str, float] = {}
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                url = (row.get("url") or "").strip()
                raw = (row.get(value_column) or "").strip()
                if not url or not raw:
                    continue
                try:
                    out[url] = float(raw)
                except ValueError:
                    logger.warning("Bad numeric value %r for url=%s in %s", raw, url, csv_path)
    except OSError as exc:
        logger.warning("Failed to read %s (%s); using defaults", csv_path, exc)
        return {}
    return out


def _normalise(values: Dict[str, float]) -> Dict[str, float]:
    """Min/max-normalise values into [0, 1] by dividing by the column max.

    If all values are zero, returns the same zero map (no scaling).
    """
    if not values:
        return {}
    max_v = max(values.values())
    if max_v <= 0:
        return {k: 0.0 for k in values}
    return {k: v / max_v for k, v in values.items()}


def _lookup_factor(url: str, normalised: Dict[str, float]) -> float:
    """Look up a normalised factor for a node URL. Falls back to default.

    Tries exact match first, then a prefix match (e.g. node URL `/login?from=x`
    matches CSV key `/login`).
    """
    if not normalised:
        return DEFAULT_FACTOR_VALUE
    if url in normalised:
        return normalised[url]
    for key, val in normalised.items():
        if url.startswith(key):
            return val
    return DEFAULT_FACTOR_VALUE


def _criticality_for_url(url: str) -> float:
    """Return the criticality weight for a URL by substring match against
    CRITICALITY_MAP. Falls back to DEFAULT_CRITICALITY.
    """
    lowered = url.lower()
    for keyword, value in CRITICALITY_MAP.items():
        if keyword in lowered:
            return value
    return DEFAULT_CRITICALITY


def _band_for_score(score: float) -> RiskBand:
    """Map a numeric risk_score to a RiskBand enum per §4.8 thresholds."""
    if score >= RISK_THRESHOLD_CRITICAL:
        return RiskBand.CRITICAL
    if score >= RISK_THRESHOLD_HIGH:
        return RiskBand.HIGH
    if score >= RISK_THRESHOLD_MEDIUM:
        return RiskBand.MEDIUM
    return RiskBand.LOW


def _raw_defect_count(url: str, raw_defects: Dict[str, float]) -> int:
    """Return the integer historical defect count for a URL (pre-normalisation).

    Used to populate `defect_count_historical` on the node — the schema field
    is the absolute count, not the normalised factor.
    """
    if url in raw_defects:
        return int(raw_defects[url])
    for key, val in raw_defects.items():
        if url.startswith(key):
            return int(val)
    return 0


def _reason_for_node(attrs: Dict[str, Any]) -> str:
    """Produce a one-sentence reason for the queue entry.

    Prefers `gap_reason` from gap_analyser if present (already a sentence).
    Otherwise synthesises from the dominant factor: business criticality first,
    then defect count, then risk band.
    """
    gap_reason = attrs.get("gap_reason")
    if gap_reason:
        return gap_reason
    crit_label = attrs.get("business_criticality", "medium")
    defects = attrs.get("defect_count_historical", 0)
    band = attrs.get("risk_band")
    band_str = band.value if hasattr(band, "value") else str(band)
    url = attrs.get("url", "?")
    return (
        f"{band_str.title()}-risk node on {url}: {crit_label} business criticality"
        f" with {defects} historical defect(s)."
    )


def score_graph(
    graph: nx.DiGraph,
    defect_csv: Optional[Path] = None,
    change_csv: Optional[Path] = None,
    memory_adjustments: Optional[Dict[str, float]] = None,
) -> nx.DiGraph:
    """Compute and apply risk scores to every node in the graph.

    Args:
        graph: NetworkX DiGraph produced by `engine.graph_builder.build_coverage_graph`.
        defect_csv: Optional override path for simulated_defect_history.csv.
        change_csv: Optional override path for simulated_change_frequency.csv.
        memory_adjustments: Optional {node_id: adjustment in [-0.3, +0.3]} to
            add to the base formula score before clamping. Used by Phase 5
            memory layer; safe to omit in Phases 3–4.

    Returns:
        The same `graph` (mutated in place), with the following attributes
        written to each node:
          - `risk_score`: float in [0, 1]
          - `risk_band`: RiskBand
          - `defect_count_historical`: int (raw count from CSV)
          - `business_criticality`: "high" | "medium" | "low"
    """
    defect_path = defect_csv or DEFAULT_DEFECT_CSV
    change_path = change_csv or DEFAULT_CHANGE_CSV

    raw_defects = _load_csv_factor(defect_path, "defects_last_6_months")
    raw_changes = _load_csv_factor(change_path, "commits_last_30_days")
    norm_defects = _normalise(raw_defects)
    norm_changes = _normalise(raw_changes)

    adjustments = memory_adjustments or {}

    for node_id, attrs in graph.nodes(data=True):
        url = attrs.get("url", "")
        change_freq = _lookup_factor(url, norm_changes)
        defect_density = _lookup_factor(url, norm_defects)
        criticality = _criticality_for_url(url)

        base = (
            W_CHANGE_FREQUENCY * change_freq
            + W_DEFECT_DENSITY * defect_density
            + W_CRITICALITY * criticality
        )
        adjusted = base + float(adjustments.get(node_id, 0.0))
        # Clamp final score per §4.16 step 9b — base and adjustment can each be
        # in-range individually while their sum falls outside [0, 1].
        score = max(0.0, min(1.0, adjusted))
        band = _band_for_score(score)

        attrs["risk_score"] = round(score, 4)
        attrs["risk_band"] = band
        attrs["defect_count_historical"] = _raw_defect_count(url, raw_defects)
        attrs["business_criticality"] = _criticality_label(criticality)

    logger.info(
        "risk_scorer: scored %d nodes (defect rows=%d, change rows=%d, mem_adj=%d)",
        graph.number_of_nodes(),
        len(raw_defects),
        len(raw_changes),
        len(adjustments),
    )
    return graph


def build_queue(graph: nx.DiGraph, risk_band: Optional[str] = None) -> List[QueueItem]:
    """Return graph nodes ranked by risk_score descending as QueueItem objects.

    Optionally filter by risk_band ("critical" | "high" | "medium" | "low").

    Args:
        graph: NetworkX DiGraph that has already been scored by `score_graph`.
        risk_band: Optional filter string. Case-insensitive. Invalid values
            are ignored (return the full queue) with a warning.

    Returns:
        Ranked list of QueueItem. `rank` starts at 1.
    """
    band_filter: Optional[RiskBand] = None
    if risk_band:
        try:
            band_filter = RiskBand(risk_band.lower())
        except ValueError:
            logger.warning("Unknown risk_band filter %r; returning unfiltered queue", risk_band)

    ranked: List[Tuple[float, str, Dict[str, Any]]] = []
    for node_id, attrs in graph.nodes(data=True):
        ranked.append((float(attrs.get("risk_score", 0.0)), node_id, attrs))
    # Sort by score descending; tie-break by node_id for determinism.
    ranked.sort(key=lambda triple: (-triple[0], triple[1]))

    items: List[QueueItem] = []
    for idx, (score, node_id, attrs) in enumerate(ranked, start=1):
        band = attrs.get("risk_band")
        if not isinstance(band, RiskBand):
            band = _band_for_score(score)
        if band_filter is not None and band != band_filter:
            continue
        items.append(
            QueueItem(
                rank=len(items) + 1,
                node_id=node_id,
                risk_score=round(score, 4),
                risk_band=band,
                reason=_reason_for_node(attrs),
            )
        )
        # Note: rank reflects position within the filtered queue, not the
        # original ranking — matches the §6 contract for /queue?risk_band=...
        _ = idx
    return items
