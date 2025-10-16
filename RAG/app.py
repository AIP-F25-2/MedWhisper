# app.py — simplified answer-only API with medical fallback
from __future__ import annotations
import os, time, re
from pathlib import Path
from typing import List, Optional

# import logging
# import uuid
# from prometheus_fastapi_instrumentator import Instrumentator
# from fastapi.requests import Request
# from pythonjsonlogger import jsonlogger


from dotenv import load_dotenv
from fastapi import FastAPI, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llama_index.core import Settings
from llama_index.llms.gemini import Gemini

from client import RetrievalClient
from scoring import rerank as ce_rerank, confidence as conf_score
from fallback import FallbackModel

import asyncio

# Limit simultaneous LLM calls (tune via env)
MAX_CONCURRENT_LLM = int(os.getenv("MAX_CONCURRENT_LLM", "32"))
_llm_gate = asyncio.Semaphore(MAX_CONCURRENT_LLM)

async def _maybe_async_complete(prompt: str):
    """Use async LLM if available, else run sync .complete() in a thread."""
    acomplete = getattr(Settings.llm, "acomplete", None)
    if acomplete:
        async with _llm_gate:
            return await acomplete(prompt)
    # Fallback: run sync in a worker thread
    async with _llm_gate:
        return await asyncio.to_thread(Settings.llm.complete, prompt)

async def _to_thread(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)


# ── .env & LLM init ───────────────────────────────────────────────────────────
DOTENV_PATH = Path(__file__).resolve().with_name(".env")
if not DOTENV_PATH.exists():
    raise RuntimeError(f".env not found at: {DOTENV_PATH}")
load_dotenv(dotenv_path=DOTENV_PATH)

# # ── Structured JSON Logging ──────────────────────────────────────────────
# log = logging.getLogger("medwhisper")
# log.setLevel(logging.INFO)
# handler = logging.StreamHandler()
# formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s")
# handler.setFormatter(formatter)
# log.addHandler(handler)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY missing in .env")
Settings.llm = Gemini(model="gemini-2.5-flash", api_key=GOOGLE_API_KEY)

FALLBACK_ON = os.getenv("FALLBACK_PROVIDER", "").strip() != ""

# ── helpers ───────────────────────────────────────────────────────────────────
_word = re.compile(r"[A-Za-z0-9]+")
def _coverage_ratio(q: str, ranked) -> float:
    """How much of the question vocabulary appears anywhere in the evidence."""
    q_terms = {t.lower() for t in _word.findall(q)}
    if not q_terms:
        return 0.0
    ev = " ".join((r.get("text","") or "") for r in (ranked or []))
    ev_terms = {t.lower() for t in _word.findall(ev)}
    hits = sum(1 for t in q_terms if t in ev_terms)
    return hits / max(1, len(q_terms))

def _clean_answer(s: str) -> str:
    """Strip tags/labels and template echoes; return plain answer."""
    if not s:
        return ""
    # Remove XML/HTML-like tags and odd separators
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("▃", " ")
    # Drop common label echoes
    s = re.sub(r"(?i)\b(question|evidence|final answer|answer|output)\s*:\s*", " ", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # If the model still returned instructions instead of content, blank it
    if re.search(r"(?i)answer in \d|medically accurate sentences|respond without citations|select the answer", s):
        return ""
    return s


# ── FastAPI ───────────────────────────────────────────────────────────────────
app = FastAPI(title="MedWhisper QA API — Answer Only + Medical Fallback")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# # ── Middleware for request IDs and latency logging ───────────────────────
# @app.middleware("http")
# async def add_request_id_and_log(request: Request, call_next):
#     request_id = str(uuid.uuid4())
#     request.state.request_id = request_id
#     start_time = time.time()

#     response = await call_next(request)
#     process_time = time.time() - start_time

#     # Add request ID to response headers
#     response.headers["X-Request-ID"] = request_id

#     log.info({
#         "event": "request_completed",
#         "request_id": request_id,
#         "method": request.method,
#         "path": request.url.path,
#         "client": request.client.host if request.client else None,
#         "duration_ms": round(process_time * 1000, 2),
#         "status_code": response.status_code,
#     })
#     return response

# # ── Prometheus Metrics (guarded; add BEFORE app starts) ───────────────────────
# try:
#     from prometheus_fastapi_instrumentator import Instrumentator
#     _METRICS_OK = True
# except Exception:
#     Instrumentator = None
#     _METRICS_OK = False

# if _METRICS_OK:
#     Instrumentator().instrument(app).expose(
#         app,
#         endpoint="/metrics",           # GET /metrics
#         include_instrumentation=True,  # adds middleware now (before startup)
#     )



# ── Schemas ───────────────────────────────────────────────
class QARequest(BaseModel):
    q: str = Field(..., description="User question")
    k: int = 6
    alpha: float = 0.65
    blend_ce: float = 1.0
    role: str = Field("general", description="User role (doctor, clinician, or general)")

class QAResponse(BaseModel):
    answer: str
    confidence: Optional[float] = None
    citations: Optional[List[str]] = None


# # ── Schemas (answer-only) ─────────────────────────────────────────────────────
# class QARequest(BaseModel):
#     q: str = Field(..., description="User question")
#     k: int = 6
#     alpha: float = 0.65
#     blend_ce: float = 1.0

# class SimpleQAResponse(BaseModel):
#     answer: str

@app.post("/ml/qa")
async def ml_qa(req: QARequest, x_user_role: str = Header(default="")):
    # 1) Retrieve candidates (likely blocking I/O -> thread)
    try:
        rc = RetrievalClient()
        cands = await _to_thread(rc.candidates, req.q, max(req.k, 12), req.alpha, req.blend_ce)
    except Exception:
        cands = []

    # 2) Rerank (CPU-bound small -> thread)
    try:
        ranked = await _to_thread(ce_rerank, req.q, cands, req.blend_ce)
        ranked = ranked[:req.k]
    except Exception:
        ranked = []

    # 3) Build evidence
    evidence = "\n\n".join([f"[{i+1}] {r.get('text','')[:350]}" for i, r in enumerate(ranked)])

    # 4) Prompt with optional CoT for doctors/clinicians (controlled by ENABLE_COT)
    system_instruction = (
        "You are MedWhisper, a concise and medically accurate assistant.\n"
        "Use ONLY the evidence below if it is relevant. If evidence is insufficient, rely on general medical knowledge cautiously.\n"
        "RULES: Output ONLY the final answer as plain text. No preamble. No labels. No citations. 2–4 sentences."
    )
    if req.role.lower() in ("doctor", "clinician") and os.getenv("ENABLE_COT", "false").lower() == "true":
        prompt = f"""{system_instruction}

Explain your reasoning briefly (1–2 sentences) before giving the final answer.

EVIDENCE:
{evidence}

QUESTION: {req.q}

FINAL ANSWER:"""
    else:
        prompt = f"""{system_instruction}

EVIDENCE:
{evidence}

QUESTION: {req.q}

FINAL ANSWER:"""

    # 5) Primary LLM call (async if supported)
    answer = ""
    try:
        out = await _maybe_async_complete(prompt)
        answer = _clean_answer(getattr(out, "text", "") or str(out))
    except Exception:
        answer = ""

    if not answer:
        try:
            out2 = await _maybe_async_complete(
                f"Answer concisely (2–4 sentences), no labels/citations. Question: {req.q}\nAnswer:"
            )
            answer = _clean_answer(getattr(out2, "text", "") or str(out2))
        except Exception:
            answer = ""

    # 6) Confidence / coverage (thread to avoid blocking)
    try:
        cov = _coverage_ratio(req.q, ranked)
    except Exception:
        cov = 0.0
    try:
        conf = await _to_thread(conf_score, req.q, answer, ranked, req.k) if answer else 0.0
    except Exception:
        conf = 0.0

    should_fallback = (not ranked) or (cov < 0.25) or (conf < 0.50) or (not answer)

    # 7) Fallback (Gemini 2.5 Flash per your fallback.py)
    if should_fallback and FALLBACK_ON:
        try:
            fb = FallbackModel()
            fb_ans = _clean_answer(fb.generate(req.q, role=req.role) or "")
            if fb_ans:
                answer = fb_ans
                try:
                    conf = await _to_thread(conf_score, req.q, answer, ranked, req.k)
                except Exception:
                    conf = 0.0
        except Exception:
            pass

    if not answer:
        answer = "I'm sorry—I can't provide a reliable medical answer right now."

    citations = [f"[{i+1}]" for i, _ in enumerate(ranked)]
    role = (req.role or x_user_role or "general").lower()

    # Role-based payload (no nulls for general)
    if role in ("doctor", "clinician"):
        return {"answer": answer, "confidence": round(conf, 3), "citations": citations}
    else:
        return {"answer": answer}


# @app.post("/ml/qa")
# def ml_qa(req: QARequest, x_user_role: str = Header(default="")):
#     # 1) Retrieve candidates
#     try:
#         rc = RetrievalClient()
#         cands = rc.candidates(req.q, k=max(req.k, 12), alpha=req.alpha, blend_ce=req.blend_ce)
#     except Exception:
#         cands = []

#     # 2) Rerank
#     try:
#         ranked = ce_rerank(req.q, cands, blend_with_incoming=req.blend_ce)[:req.k]
#     except Exception:
#         ranked = []

#     # 3) Build evidence
#     evidence = "\n\n".join([f"[{i+1}] {r.get('text','')[:350]}" for i, r in enumerate(ranked)])

#     # 4) Primary (Gemini) — prompt tuned to avoid echoing
#     system_instruction = (
#         "You are MedWhisper, a concise and medically accurate assistant.\n"
#         "Use ONLY the evidence below if it is relevant. If evidence is insufficient, rely on general medical knowledge cautiously.\n"
#         "RULES: Output ONLY the final answer as plain text. No preamble. No labels. No citations. 2–4 sentences."
#     )

#     # ✅ Optional CoT mode (for explainability)
#     if req.role.lower() in ("doctor", "clinician") and os.getenv("ENABLE_COT", "false").lower() == "true":
#         prompt = f"""{system_instruction}

#     Explain your reasoning briefly (1–2 sentences) before giving the final answer.

#     EVIDENCE:
#     {evidence}

#     QUESTION: {req.q}

#     FINAL ANSWER:"""
#     else:
#         prompt = f"""{system_instruction}

#     EVIDENCE:
#     {evidence}

#     QUESTION: {req.q}

#     FINAL ANSWER:"""


# #     # 4) Prompt for Gemini
# #     system_instruction = (
# #         "You are MedWhisper, a concise and medically accurate assistant.\n"
# #         "Use ONLY the evidence below if it is relevant. If evidence is insufficient, rely on general medical knowledge cautiously.\n"
# #         "RULES: Output ONLY the final answer as plain text. No preamble. No labels. No citations. 2–4 sentences."
# #     )
# #     prompt = f"""{system_instruction}

# # EVIDENCE:
# # {evidence}

# # QUESTION: {req.q}

# # FINAL ANSWER:"""

#     answer = ""
#     try:
#         out = Settings.llm.complete(prompt)
#         answer = _clean_answer(getattr(out, "text", "") or str(out))
#     except Exception:
#         answer = ""

#     if not answer:
#         try:
#             out2 = Settings.llm.complete(
#                 f"Answer concisely (2–4 sentences), no labels/citations. Question: {req.q}\nAnswer:"
#             )
#             answer = _clean_answer(getattr(out2, "text", "") or str(out2))
#         except Exception:
#             answer = ""

#     # Confidence & coverage
#     try:
#         cov = _coverage_ratio(req.q, ranked)
#     except Exception:
#         cov = 0.0
#     try:
#         conf = conf_score(req.q, answer, ranked, k=req.k) if answer else 0.0
#     except Exception:
#         conf = 0.0

#     should_fallback = (not ranked) or (cov < 0.25) or (conf < 0.50) or (not answer)

#     # Fallback
#     if should_fallback and FALLBACK_ON:
#         try:
#             fb = FallbackModel()
#             fb_ans = _clean_answer(fb.generate(req.q, role=req.role) or "")
#             if fb_ans:
#                 answer = fb_ans
#                 try:
#                     conf = conf_score(req.q, answer, ranked, k=req.k)
#                 except Exception:
#                     conf = 0.0
#         except Exception:
#             pass

#     if not answer:
#         answer = "I'm sorry—I can't provide a reliable medical answer right now."

#     citations = [f"[{i+1}]" for i, _ in enumerate(ranked)]

#     # Determine role (JSON field or header)
#     role = (req.role or x_user_role or "general").lower()

#     # ✅ Return depending on role
#     if role in ("doctor", "clinician"):
#         return {"answer": answer, "confidence": round(conf, 3), "citations": citations}
#     else:
#         return {"answer": answer}




# ── Debug: inspect reranked evidence (unchanged, dev-only) ────────────────────
@app.get("/ml/qa/debug")
def qa_debug(q: str = Query(...), k: int = 6, alpha: float = 0.65, blend_ce: float = 1.0):
    rc = RetrievalClient()
    cands = rc.candidates(q, k=max(k, 12), alpha=alpha, blend_ce=blend_ce)
    ranked = ce_rerank(q, cands, blend_with_incoming=blend_ce)[:k]
    return {"ranked": ranked}
