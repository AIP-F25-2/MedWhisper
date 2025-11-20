# file: RAG/remote_retrieval_client.py
from __future__ import annotations

import os
from typing import List, Dict, Any

import requests

RETRIEVAL_API_BASE = os.getenv("RETRIEVAL_API_BASE", "http://4.206.25.0:8000")


class RemoteRetriever:
    """
    Simple client for the remote retrieval API.

    Expected endpoints:

      GET /health
        -> {"ok": true, "documents": ..., "embeddings": ...}

      GET /search?q=<text>&k=<int>
        -> {
             "query": "...",
             "k": 5,
             "hits": [
               {
                 "doc_id": 12345,
                 "score": 0.82,
                 "table_name": "labevents",
                 "meta": {
                     "subject_id": 10000032,
                     "hadm_id": 23456789
                 },
                 "text": "INR(PT) result 1.4 ..."
               },
               ...
             ]
           }
    """

    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or RETRIEVAL_API_BASE).rstrip("/")
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Call /search on the remote API and return list of hit dicts.
        """
        params = {"q": query, "k": k}
        resp = requests.get(f"{self.base_url}/search", params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        # This returns raw "hits" – MedWhisperRAG will adapt them.
        return data.get("hits", [])
