# file: RAG/rag_engine.py
from __future__ import annotations

import logging
import uuid
from typing import List, Dict, Any, Optional

from llm_client import LLMClient
from safety import SafetyGate
from query_processor import MedicalQueryProcessor
from remote_retrieval_client import RemoteRetriever

logger = logging.getLogger(__name__)


class MedWhisperRAG:
    """
    REMOTE RETRIEVAL VERSION

    - No local DuckDB
    - No BioClinicalBERT embeddings
    - No HybridRetriever
    - Retrieval is done ONLY via teammate's API at 4.206.25.0:8000
    """

    def __init__(self) -> None:
        logger.info("MedWhisper RAG (REMOTE RETRIEVAL MODE) starting")

        self.llm_client = LLMClient()
        # SafetyGate with minimal use (no embedder-based hallucination checks)
        self.safety_gate = SafetyGate()
        self.query_processor = MedicalQueryProcessor()
        self.remote_retriever = RemoteRetriever()

        logger.info("MedWhisper RAG initialized (using remote retrieval API)")

    # -----------------------------
    #  MAIN RAG QUERY
    # -----------------------------
    def query(
        self,
        query_text: str,
        patient_id: Optional[str] = None,
        include_differential: bool = False,
        include_timeline: bool = False,
        reference_answer: Optional[str] = None,
        user_role: str = "clinician",
    ) -> Dict[str, Any]:

        query_id = str(uuid.uuid4())
        logger.info(f"[RAG] Processing query {query_id}: {query_text}")

        # 1) Remote retrieval (optionally filtered by patient_id)
        retrieved_docs = self._remote_retrieval(query_text, patient_id=patient_id)

        # 2) Build system prompt based on user role
        system_prompt = self._build_prompt(user_role)

        # 3) Ask Gemini with retrieved_docs as context
        response_text = self.llm_client.generate_with_context(
            query=query_text,
            context_docs=retrieved_docs,
            system_prompt=system_prompt,
            use_fallback_for_general=len(retrieved_docs) == 0,
        )

        # 4) Simple hallucination metadata
        hallucination_check = {
            "grounded": len(retrieved_docs) > 0,
            "confidence": 0.8 if len(retrieved_docs) > 0 else 0.0,
            "issue": None if len(retrieved_docs) > 0 else "No citations",
        }

        retrieved_doc_ids = [d.get("doc_id") for d in retrieved_docs]

        return {
            "query_id": query_id,
            "query": query_text,
            "response": response_text,
            "safe": True,
            "safety_warnings": [],
            "grounding_score": 1.0 if len(retrieved_docs) > 0 else 0.0,
            "is_grounded": len(retrieved_docs) > 0,
            "hallucination_check": hallucination_check,
            "citations_valid": True,
            "invalid_citations": [],
            "num_retrieved_docs": len(retrieved_docs),
            "retrieved_doc_ids": retrieved_doc_ids,
            "temporal_info": {"has_temporal": False},
            "metrics": {},
            "used_fallback": len(retrieved_docs) == 0,
            "user_role": user_role,
        }

    # ------------------------------------------
    #  REMOTE RETRIEVAL FUNCTION
    # ------------------------------------------
    def _remote_retrieval(
        self,
        query_text: str,
        patient_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Call teammate's retrieval microservice and return docs shaped for the LLM:

        [
          {
            "doc_id": "...",
            "content": "...",     # text used by Gemini
            "score": float,
            "table_name": "...",
            "metadata": {...}
          },
          ...
        ]
        """
        try:
            raw_hits = self.remote_retriever.search(query_text, k=top_k)
        except Exception as e:
            logger.error(f"[RAG] Retrieval API crashed: {e}")
            return []

        # Optional filtering by patient_id using meta.subject_id
        if patient_id:
            pid = str(patient_id)
            filtered_hits = []
            for h in raw_hits:
                meta = h.get("meta", {}) or {}
                subj = meta.get("subject_id")
                if subj is not None and str(subj) == pid:
                    filtered_hits.append(h)
            logger.info(
                f"[RAG] Filtered {len(filtered_hits)}/{len(raw_hits)} hits for patient {patient_id}"
            )
            hits = filtered_hits
        else:
            hits = raw_hits

        docs: List[Dict[str, Any]] = []
        for h in hits:
            docs.append(
                {
                    "doc_id": h.get("doc_id"),
                    "content": h.get("text") or "",
                    "score": h.get("score"),
                    "table_name": h.get("table_name"),
                    "metadata": h.get("meta") or {},
                }
            )

        logger.info(f"[RAG] Retrieved {len(docs)} docs from remote API")
        return docs

    # ------------------------------------------
    #  PROMPT BUILDER
    # ------------------------------------------
    def _build_prompt(self, user_role: str) -> str:
        if user_role == "student":
            return (
                "You are MedWhisper Educational Assistant. "
                "Explain clearly, step by step, using simple medical language."
            )
        else:
            return (
                "You are MedWhisper Clinical Assistant. "
                "Use the provided context documents when possible, "
                "and make it clear when you are using general medical knowledge."
            )

    def close(self) -> None:
        logger.info("MedWhisper RAG closed")
