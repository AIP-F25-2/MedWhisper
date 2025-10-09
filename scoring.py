# ml_api/scoring.py
from __future__ import annotations
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, CrossEncoder

# Light-weight models for ML-side processing
BIOCLINICALBERT = "emilyalsentzer/Bio_ClinicalBERT"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_emb = SentenceTransformer(BIOCLINICALBERT)
_ce  = CrossEncoder(RERANKER_MODEL)

def _normalize(x: np.ndarray) -> np.ndarray:
    if x.size == 0:
        return x
    mn, mx = float(x.min()), float(x.max())
    if abs(mx - mn) < 1e-12:
        return np.ones_like(x) * 0.5
    return (x - mn) / (mx - mn + 1e-12)

def _softmax(x: np.ndarray) -> np.ndarray:
    if x.size == 0:
        return np.array([])
    x = x - x.max()
    e = np.exp(x)
    return e / (e.sum() + 1e-12)

def _cos(a: np.ndarray, b: np.ndarray) -> float:
    a = a / (np.linalg.norm(a) + 1e-12)
    b = b / (np.linalg.norm(b) + 1e-12)
    return float(np.dot(a, b))

def rerank(query: str, rows: List[Dict[str, Any]], blend_with_incoming: float = 1.0, max_chars: int = 1000) -> List[Dict[str, Any]]:
    """Cross-encoder reranking over the DE-provided candidates."""
    if not rows:
        return []
    texts = [str(r.get("text",""))[:max_chars] for r in rows]
    ce = _ce.predict([(query, t) for t in texts]).astype(float)
    ce_n = _normalize(ce)
    if blend_with_incoming >= 1.0:
        final = ce_n
    else:
        inc = np.array([float(r.get("score", 0.0)) for r in rows], dtype=float)
        inc_n = _normalize(inc)
        final = blend_with_incoming*ce_n + (1.0 - blend_with_incoming)*inc_n
    # attach & sort
    for i, r in enumerate(rows):
        r["_ce"] = float(ce[i])
        r["_final"] = float(final[i])
    return sorted(rows, key=lambda r: r["_final"], reverse=True)

def confidence(query: str, answer_text: str, rows: List[Dict[str, Any]], k: int, weights=(0.5, 0.3, 0.2)) -> float:
    """[0,1] blend of retrieval strength, faithfulness, coverage."""
    use = rows[:k]
    # retrieval strength on final scores
    scores = np.array([float(r.get("_final", r.get("_ce", r.get("score", 0.0)))) for r in use], dtype=float)
    if scores.size == 0:
        ret = 0.0
    else:
        p = _softmax(scores)
        order = np.argsort(scores)[::-1]
        ret = float(p[order][0])
    # faithfulness
    ev = "\n".join([str(r.get("text",""))[:350] for r in use])
    ans = _emb.encode([answer_text or ""], convert_to_numpy=True)[0]
    evv = _emb.encode([ev], convert_to_numpy=True)[0]
    faith = max(0.0, min(1.0, _cos(ans, evv)))
    # coverage
    doc_ids = [r.get("doc_id") for r in use if r.get("doc_id")]
    cov = 0.0 if k == 0 else min(1.0, len(set(doc_ids)) / float(k))
    w1, w2, w3 = weights
    c = w1*ret + w2*faith + w3*cov
    return float(max(0.0, min(1.0, c)))
