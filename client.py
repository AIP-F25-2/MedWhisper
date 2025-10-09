# ml_api/client.py
from __future__ import annotations
import os, requests
from typing import Dict, Any, List

RETRIEVAL_BASE_URL = os.getenv("RETRIEVAL_BASE_URL", "http://127.0.0.1:8000")

class RetrievalClient:
    def __init__(self, base_url: str | None = None, timeout: float = 20.0):
        self.base_url = (base_url or RETRIEVAL_BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout

    def _post(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        r = self.session.post(f"{self.base_url}{path}", json=json, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        r = self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def candidates(self, q: str, k: int = 12, alpha: float = 0.65, blend_ce: float = 1.0) -> List[Dict[str, Any]]:
        """
        Tries POST /search_rerank first (if DE exposed it).
        Falls back to GET /search?engine=hybrid if that’s what’s available.
        Returns a list of dicts with at least: text, doc_id, source, score (if present).
        """
        # Try modern route
        try:
            data = self._post("/search_rerank", {
                "q": q, "k": k, "alpha": alpha, "blend_ce": blend_ce, "filters": None
            })
            results = data.get("results", [])
            # normalize
            out = []
            for r in results:
                out.append({
                    "text": r.get("text", ""),
                    "snippet": r.get("snippet", r.get("text", "")[:280]),
                    "doc_id": r.get("doc_id"),
                    "source": r.get("source"),
                    "patient_id": r.get("patient_id"),
                    "encounter_id": r.get("encounter_id"),
                    "code": r.get("code"),
                    "ts": r.get("ts"),
                    "score": r.get("final", r.get("ce", r.get("score", 0.0))),
                })
            return out[:k] if out else []
        except Exception:
            pass

        # Fallback to legacy /search
        try:
            data = self._get("/search", {"q": q, "engine": "hybrid", "k": k})
            results = data.get("results", [])
            out = []
            for r in results:
                # examples from DE usually include 'text' & 'doc_id'
                out.append({
                    "text": r.get("text", ""),
                    "snippet": r.get("snippet", r.get("text", "")[:280]),
                    "doc_id": r.get("doc_id"),
                    "source": r.get("source"),
                    "patient_id": r.get("patient_id"),
                    "encounter_id": r.get("encounter_id"),
                    "code": r.get("code"),
                    "ts": r.get("ts"),
                    "score": r.get("combo", r.get("faiss", r.get("bm25", 0.0))),
                })
            return out[:k] if out else []
        except Exception as e:
            # As a last resort, return empty to signal no evidence
            return []
