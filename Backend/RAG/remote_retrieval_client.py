# file: Backend/RAG/remote_retrieval_client.py
from __future__ import annotations

import os
import logging
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)

# Default base URL of teammate's retrieval service
# You can override this via environment variable:
#   set RETRIEVAL_API_BASE=http://10.0.0.166:8000   (Windows)
RETRIEVAL_API_BASE = os.getenv("RETRIEVAL_API_BASE", "http://4.206.25.0:8000")


class RemoteRetriever:
    """
    Simple client for the remote retrieval API.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0) -> None:
        """
        timeout: HTTP timeout in seconds (default: 120 seconds)
        """
        self.base_url = (base_url or RETRIEVAL_API_BASE).rstrip("/")
        self.timeout = timeout   # 120-second timeout

    # -----------------------------
    #  HEALTH CHECK
    # -----------------------------
    def health(self) -> Dict[str, Any]:
        url = f"{self.base_url}/health"
        logger.info(f"[RemoteRetriever] GET {url}")

        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # -----------------------------
    #  SEARCH
    # -----------------------------
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Call /search on the remote API and return a list of normalized docs.
        """
        url = f"{self.base_url}/search"
        params = {"q": query, "k": k}

        logger.info(f"[RemoteRetriever] GET {url} params={params}")

        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()

        data = resp.json()
        hits = data.get("hits", [])

        docs: List[Dict[str, Any]] = []
        for hit in hits:
            docs.append(
                {
                    "doc_id": hit.get("doc_id"),
                    "content": hit.get("text", ""),
                    "retrieval_score": hit.get("score", 0.0),
                    "table_name": hit.get("table_name"),
                    "metadata": hit.get("meta", {}) or {},
                }
            )

        logger.info(f"[RemoteRetriever] normalized {len(docs)} docs")
        return docs
