"""
Module: engine/memory.py
Purpose: Store findings as vector embeddings using ChromaDB and query for similar
         past findings. Implements the Memory & Continuous Learning Loop (Layer 4)
         per CLAUDE.md §4.11.
Author: Team / Claude Code
Created: 2026-05-14
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

logger = logging.getLogger(__name__)


def _is_model_cached(model_name: str) -> bool:
    """Return True if the sentence-transformers model is already on disk.

    Checks both HF Hub's cache layout (~/.cache/huggingface/hub/models--*)
    and sentence-transformers' legacy cache. A True result means we can
    safely flip HF_HUB_OFFLINE=1 and skip the network probe.
    """
    home = Path.home()
    safe = model_name.replace("/", "_")
    candidates = [
        home / ".cache" / "huggingface" / "hub" / f"models--sentence-transformers--{safe}",
        home / ".cache" / "huggingface" / "hub" / f"models--{safe}",
        home / ".cache" / "torch" / "sentence_transformers" / f"sentence-transformers_{safe}",
    ]
    return any(p.is_dir() and any(p.iterdir()) for p in candidates)

# Constants per CLAUDE.md §13 quick reference.
MEMORY_SIMILARITY_THRESHOLD: float = 0.85
MEMORY_POSITIVE_ADJUSTMENT: float = 0.15
MEMORY_NEGATIVE_ADJUSTMENT: float = -0.10
MEMORY_ADJUSTMENT_CLAMP: float = 0.3
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
COLLECTION_NAME: str = "findings"


class AgentMemory:
    """Persistent memory layer backed by ChromaDB vector store.

    Stores findings as embedded vectors and provides semantic similarity
    queries to enable cross-run learning. Uses PersistentClient per
    CLAUDE.md §1 hard constraint — never chromadb.Client().
    """

    def __init__(self) -> None:
        """Initialize ChromaDB persistent client and sentence transformer model.

        If the embedding model can't be loaded (typical cause: corporate TLS
        proxy blocks the first-time HuggingFace download), the instance falls
        back into a disabled state where every operation becomes a no-op. The
        scan still completes; only the memory-driven risk adjustment is lost.
        """
        chroma_path = os.getenv("CHROMA_PATH", "./chroma_store")
        # CRITICAL: use PersistentClient — NOT chromadb.Client()
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        # Prefer offline mode when the model is already cached — avoids the
        # 5-retry SSL storm against huggingface.co that the corp proxy blocks.
        if not os.getenv("HF_HUB_OFFLINE") and _is_model_cached(EMBEDDING_MODEL):
            os.environ["HF_HUB_OFFLINE"] = "1"
            logger.debug("HF model cached locally; enabled HF_HUB_OFFLINE")

        self.model: Optional[SentenceTransformer] = None
        self.disabled: bool = False
        try:
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(
                "AgentMemory initialized: path=%s, collection=%s, model=%s",
                chroma_path, COLLECTION_NAME, EMBEDDING_MODEL,
            )
        except Exception as exc:
            self.disabled = True
            logger.warning(
                "AgentMemory disabled — embedding model unavailable (%s). "
                "Memory-driven risk adjustment will be skipped this run. "
                "First-time setup needs reachable huggingface.co to download '%s'.",
                exc.__class__.__name__, EMBEDDING_MODEL,
            )

    def _embed(self, text: str) -> List[float]:
        """Encode text to a vector embedding.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        return self.model.encode(text).tolist()

    def store_finding(self, finding: Dict[str, Any], run_id: str) -> None:  # noqa: D401
        if self.disabled or self.model is None:
            return
        self._store_finding_impl(finding, run_id)

    def _store_finding_impl(self, finding: Dict[str, Any], run_id: str) -> None:
        """Store a finding as a vector embedding in ChromaDB.

        Args:
            finding: Finding dict with page, anomaly, persona, anomaly_type, etc.
            run_id: The scan/run ID this finding belongs to.
        """
        text = (
            f"{finding.get('page', '')} {finding.get('anomaly', '')} "
            f"{finding.get('persona', '')} {finding.get('anomaly_type', '')}"
        )
        embedding = self._embed(text)

        severity = finding.get("severity", "medium")
        if hasattr(severity, "value"):
            severity = severity.value

        try:
            self.collection.add(
                ids=[finding["id"]],
                embeddings=[embedding],
                metadatas=[{
                    "node_id": finding.get("node_id", ""),
                    "severity": severity,
                    "persona": finding.get("persona", ""),
                    "anomaly_type": finding.get("anomaly_type", ""),
                    "resolved": False,
                    "run_id": run_id,
                    "run_date": finding.get("timestamp", "")[:10],
                    "page": finding.get("page", ""),
                }],
            )
            logger.debug("Stored finding %s in memory", finding["id"])
        except Exception as exc:
            logger.warning("Failed to store finding %s: %s", finding.get("id"), exc)

    def query_similar(
        self, node_id: str, context: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Query for semantically similar past findings on a given node.

        Args:
            node_id: The graph node ID to filter by.
            context: Text context to search for similar findings.
            top_k: Maximum number of similar findings to return.

        Returns:
            List of similar findings with similarity scores.
        """
        if self.disabled or self.model is None:
            return []
        try:
            embedding = self._embed(context)
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where={"node_id": node_id},
            )
            if not results["ids"][0]:
                return []
            return [
                {
                    "id": results["ids"][0][i],
                    "similarity": 1 - results["distances"][0][i],
                    "metadata": results["metadatas"][0][i],
                }
                for i in range(len(results["ids"][0]))
            ]
        except Exception:
            return []  # Never crash on memory query failure.

    def get_memory_adjustment(self, node_id: str, context: str) -> float:
        """Compute a risk score adjustment based on memory.

        Positive if unresolved issues found, negative if all resolved.

        Args:
            node_id: The graph node ID.
            context: Text context for similarity search.

        Returns:
            Float adjustment in [-0.3, +0.3].
        """
        similar = self.query_similar(node_id, context)
        if not similar:
            return 0.0
        high_similarity = [
            s for s in similar if s["similarity"] > MEMORY_SIMILARITY_THRESHOLD
        ]
        if not high_similarity:
            return 0.0
        unresolved = [
            s for s in high_similarity
            if not s["metadata"].get("resolved", False)
        ]
        resolved = [
            s for s in high_similarity
            if s["metadata"].get("resolved", False)
        ]
        adjustment = (
            len(unresolved) * MEMORY_POSITIVE_ADJUSTMENT
            + len(resolved) * MEMORY_NEGATIVE_ADJUSTMENT
        )
        return max(-MEMORY_ADJUSTMENT_CLAMP, min(MEMORY_ADJUSTMENT_CLAMP, adjustment))

    def get_run_summaries(self) -> List[Dict[str, Any]]:
        """Return a list of past runs for the memory panel.

        Returns:
            List of run summary dicts with run_id, date, findings_count, top_finding.
        """
        try:
            all_data = self.collection.get()
            if not all_data["ids"]:
                return []
            runs: Dict[str, Dict[str, Any]] = {}
            for i, meta in enumerate(all_data["metadatas"]):
                run_id = meta.get("run_id", "unknown")
                if run_id not in runs:
                    runs[run_id] = {
                        "run_id": run_id,
                        "date": meta.get("run_date", ""),
                        "findings_count": 0,
                        "top_finding": None,
                    }
                runs[run_id]["findings_count"] += 1
                if (
                    runs[run_id]["top_finding"] is None
                    and meta.get("severity") in ["critical", "high"]
                ):
                    runs[run_id]["top_finding"] = (
                        f"{meta.get('anomaly_type')} on {meta.get('page')}"
                    )
            return list(runs.values())
        except Exception:
            return []

    def get_total_findings_count(self) -> int:
        """Return total number of findings stored in memory.

        Returns:
            Integer count of findings.
        """
        try:
            return self.collection.count()
        except Exception:
            return 0
