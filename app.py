# ml_api/app.py
from __future__ import annotations
import os, re, time
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path

from llama_index.core import Settings
# from llama_index.llms.google_genai import GoogleGenAI

from .client import RetrievalClient
from .scoring import rerank as ce_rerank, confidence as conf_score

import os
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini

# Always load .env from the same folder as app.py
DOTENV_PATH = Path(__file__).resolve().with_name(".env")

if not DOTENV_PATH.exists():
    raise RuntimeError(f".env file not found at: {DOTENV_PATH}")

load_dotenv(dotenv_path=DOTENV_PATH)

key = os.getenv("GOOGLE_API_KEY", "")
if key:
    Settings.llm = Gemini(model="gemini-2.5-flash", api_key=key)
else:
    raise RuntimeError("GOOGLE_API_KEY is missing in .env — cannot run LLM.")

# API_KEY = os.getenv("GOOGLE_API_KEY", "")
# if API_KEY:
#     Settings.llm = Gemini(model="gemini-1.5-flash", api_key=API_KEY)
# else:
#     Settings.llm = None  # we'll use extractive fallback if no key


# load_dotenv()  # loads RETRIEVAL_BASE_URL, GOOGLE_API_KEY if present

# # --- LLM (Gemini) optional; fallback to extractive if missing or errors ---
# try:
#     Settings.llm = GoogleGenAI(model="gemini-2.5-flash")
# except Exception:
#     Settings.llm = None

app = FastAPI(title="MedWhisper ML API — QA over Retrieval")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class QARequest(BaseModel):
    q: str = Field(..., description="User question")
    k: int = 6
    alpha: float = 0.65
    blend_ce: float = 1.0  # 1.0 = CE only; 0.7 blends with incoming score

@app.get("/ping")
def ping():
    return {"ok": True}

@app.post("/ml/qa")
def ml_qa(req: QARequest):
    """
    Pipeline:
      - call Data Engineer retrieval API for candidates
      - CE rerank (optional blend)
      - build evidence
      - LLM generate (fallback to extractive)
      - compute confidence
      - return answer + citations
    """
    t0 = time.time()
    rc = RetrievalClient()
    cands = rc.candidates(req.q, k=max(req.k, 12), alpha=req.alpha, blend_ce=req.blend_ce)

    ranked = ce_rerank(req.q, cands, blend_with_incoming=req.blend_ce)
    ranked = ranked[:req.k]

    evidence = "\n\n".join([f"[{i+1}] {r.get('text','')[:350]}" for i, r in enumerate(ranked)])
    system_instruction = (
        "You are MedWhisper, a concise and medically accurate assistant for clinicians. "
        "Use only the EHR evidence provided below to answer. If incomplete, say so briefly. "
        "Be professional and avoid hallucinations.\n"
    )
    prompt = f"""{system_instruction}

Question: {req.q}

Evidence:
{evidence}

Format your response:

**Answer:**
<short, factual, medically accurate answer in 2–3 lines>

**Supporting Evidence:**
- [1] Key fact from first source
- [2] Key fact from second source
"""

    # Generate or extractive fallback
    answer = ""
    try:
        if Settings.llm is not None:
            out = Settings.llm.complete(prompt)
            answer = (out.text or "").strip()
    except Exception:
        answer = ""
    if not answer:
        answer = " ".join([r.get("text","")[:180] for r in ranked[:3]])

    # Confidence
    conf = conf_score(req.q, answer, ranked, k=req.k)
    label = "High" if conf >= 0.75 else "Medium" if conf >= 0.55 else "Low"
    if re.search(r"(?i)\*\*Confidence.*?\*\*:", answer):
        answer = re.sub(r"(?i)\*\*Confidence.*?\*\*:\s*(High|Medium|Low)", f"**Confidence Level:** {label}", answer)
    else:
        answer += f"\n\n**Confidence Level:** {label}"
    if conf < 0.58:
        answer += f"\n\n⚠️ Model confidence **{conf:.2f} ({label})** is below the safety threshold. Please verify with external clinical sources."

    # Citations
    citations = []
    for i, r in enumerate(ranked):
        citations.append({
            "ref": f"[{i+1}]",
            "doc_id": r.get("doc_id"),
            "source": r.get("source"),
            "patient_id": r.get("patient_id"),
            "encounter_id": r.get("encounter_id"),
            "code": r.get("code"),
            "ts": r.get("ts"),
            "score": float(r.get("_final", r.get("_ce", r.get("score", 0.0)))),
            "snippet": r.get("snippet", r.get("text","")[:280]),
        })

    return {
        "q": req.q,
        "k": req.k,
        "alpha": req.alpha,
        "blend_ce": req.blend_ce,
        "answer_text": answer,
        "confidence": round(conf, 3),
        "confidence_percent": int(round(conf * 100)),
        "citations": citations,
        "latency_sec": round(time.time()-t0, 3),
    }

# ------------- Chat-style CLI (ask many Qs; empty input exits) -------------
def main():
    print("\n🧠 MedWhisper ML Chat — Connected to Retrieval API")
    print("Press ENTER on an empty line to exit.\n")
    while True:
        q = input("Question: ").strip()
        if not q:
            print("Bye!")
            break
        resp = ml_qa(QARequest(q=q))  # call local function, no network hop
        print("\n" + resp["answer_text"])
        print(f"\nConfidence: {resp['confidence']} ({resp['confidence_percent']}%)")
        print("Top Citations:")
        for c in resp["citations"][:3]:
            print(f"{c['ref']} {c['source']} ({c['doc_id']}) — {c['snippet'][:100]}...")
        print("-"*80)

if __name__ == "__main__":
    main()
