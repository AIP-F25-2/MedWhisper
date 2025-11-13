# file: voice_api/voice_api.py
from __future__ import annotations

import os
import uuid
import tempfile
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from faster_whisper import WhisperModel
from rag_engine import MedWhisperRAG

# -------------------------------------------------------------------
# Config + logging
# -------------------------------------------------------------------
logger = logging.getLogger("voice_api")

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")     # "cpu" | "cuda" | "auto"
COMPUTE_TYPE   = os.getenv("WHISPER_COMPUTE", "int8")   # "int8" works on all CPUs
DEFAULT_LANG   = os.getenv("WHISPER_LANGUAGE", "en")

_VALID_LANGS = {"en"}
_NAME_TO_LANG = {"english": "en"}


def _sanitize_language(lang: Optional[str]) -> Optional[str]:
    if not lang:
        return DEFAULT_LANG or None
    s = lang.strip().lower()
    s = _NAME_TO_LANG.get(s, s)
    return s if s in _VALID_LANGS else DEFAULT_LANG


# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------
app = FastAPI(title="MedWhisper Voice + Text QA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_asr: WhisperModel | None = None
_rag: MedWhisperRAG | None = None


@app.on_event("startup")
def _startup() -> None:
    """Create RAG and Whisper instances once at startup."""
    global _asr, _rag

    logger.info("Initializing MedWhisper RAG Engine")
    _rag = MedWhisperRAG()
    logger.info("MedWhisper RAG Engine initialized")

    logger.info(
        "Loading Whisper model '%s' on device '%s' (compute_type=%s)",
        WHISPER_MODEL,
        WHISPER_DEVICE,
        COMPUTE_TYPE,
    )
    _asr = WhisperModel(
        WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=COMPUTE_TYPE,
    )
    logger.info("Whisper model loaded")


@app.get("/health")
def health() -> Dict[str, str]:
    return {
        "status": "ok",
        "whisper_model": WHISPER_MODEL,
        "device": WHISPER_DEVICE,
    }


# -------------------------------------------------------------------
# Helper: single, correct way to call your RAG engine
# -------------------------------------------------------------------
def _run_rag_query(
    question: str,
    *,
    patient_id: Optional[str],
    include_timeline: bool,
    include_differential: bool,
    user_role: str,
) -> Dict[str, Any]:
    """Call MedWhisperRAG in the SAME way your old api_server.py did."""
    if _rag is None:
        raise HTTPException(503, "RAG engine not ready")

    if not hasattr(_rag, "query"):
        raise HTTPException(
            500,
            "MedWhisperRAG has no .query(...) method – expected one.",
        )

    # IMPORTANT: position question, only pass supported kwargs
    return _rag.query(
        question,
        patient_id=patient_id,
        include_timeline=include_timeline,
        include_differential=include_differential,
        user_role=user_role,
    )


# -------------------------------------------------------------------
# 1) TEXT CHAT – JSON body, like normal ChatGPT
# -------------------------------------------------------------------
class TextQARequest(BaseModel):
    question: str
    language: Optional[str] = None   # not sent to RAG, just here for future
    patient_id: Optional[str] = None
    include_timeline: bool = False
    include_differential: bool = False
    # 🔴 REQUIRED NOW – no default
    user_role: str


@app.post("/qa")
async def text_qa(payload: TextQARequest = Body(...)) -> Dict[str, Any]:
    """
    Text-only QA.

    Content-Type: application/json

    {
      "question": "What are the symptoms for lung cancer?",
      "language": "en",
      "patient_id": null,
      "include_timeline": false,
      "include_differential": false,
      "user_role": "clinician"  // or 'student', 'nurse', etc. – REQUIRED
    }
    """
    if not payload.question.strip():
        raise HTTPException(400, "Question cannot be empty")

    if not payload.user_role:
        raise HTTPException(400, "user_role is required")

    rag = _run_rag_query(
        question=payload.question,
        patient_id=payload.patient_id,
        include_timeline=payload.include_timeline,
        include_differential=payload.include_differential,
        user_role=payload.user_role,
    )

    return {
        "mode": "text",
        "text": {
            "question": payload.question,
            "language": payload.language,
        },
        "rag": rag,
    }


# -------------------------------------------------------------------
# 2) VOICE CHAT – multipart/form-data with audio file
# -------------------------------------------------------------------

@app.post("/voice-qa")
async def voice_qa(
    file: UploadFile = File(..., description="Audio file (mp3/m4a/wav)"),
    language: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None),
    include_timeline: bool = Form(False),
    include_differential: bool = Form(False),
    # 🔴 REQUIRED NOW – no default
    user_role: str = Form(...),
) -> Dict[str, Any]:
    """
    Voice QA:
    - User records a question with mic
    - We transcribe via Whisper
    - Then send the text to the SAME RAG pipeline as /qa

    Content-Type: multipart/form-data
    """
    if _asr is None or _rag is None:
        raise HTTPException(503, "Service not ready")

    # ---------- Windows-safe temp file handling ----------
    suffix = os.path.splitext(file.filename or "")[-1] or ".wav"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    try:
        data = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(data)

        lang = _sanitize_language(language)

        segments, info = _asr.transcribe(
            tmp_path,
            language=lang,
            vad_filter=True,
            beam_size=5,
        )
        transcript = "".join([s.text for s in segments]).strip()
    finally:
        # Clean up temp file
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if not transcript:
        raise HTTPException(400, "Could not extract any speech from audio")

    if not user_role:
        raise HTTPException(400, "user_role is required")

    rag = _run_rag_query(
        question=transcript,
        patient_id=patient_id,
        include_timeline=include_timeline,
        include_differential=include_differential,
        user_role=user_role,
    )

    return {
        "mode": "voice",
        "whisper": {
            "model": WHISPER_MODEL,
            "device": WHISPER_DEVICE,
            "compute_type": COMPUTE_TYPE,
            "language": lang,
            "language_probability": getattr(info, "language_probability", None),
            "transcript": transcript,
        },
        "rag": rag,
    }













# # file: voice_api/voice_api.py
# from __future__ import annotations

# import os
# import uuid
# import tempfile
# import logging
# from typing import Optional, Dict, Any

# from fastapi import FastAPI, UploadFile, File, Form, Body, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# from faster_whisper import WhisperModel
# from rag_engine import MedWhisperRAG

# # -------------------------------------------------------------------
# # Config + logging
# # -------------------------------------------------------------------
# logger = logging.getLogger("voice_api")

# WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
# WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")     # "cpu" | "cuda" | "auto"
# COMPUTE_TYPE   = os.getenv("WHISPER_COMPUTE", "int8")   # "int8" works on all CPUs
# DEFAULT_LANG   = os.getenv("WHISPER_LANGUAGE", "en")

# _VALID_LANGS = {"en"}
# _NAME_TO_LANG = {"english": "en"}


# def _sanitize_language(lang: Optional[str]) -> Optional[str]:
#     if not lang:
#         return DEFAULT_LANG or None
#     s = lang.strip().lower()
#     s = _NAME_TO_LANG.get(s, s)
#     return s if s in _VALID_LANGS else DEFAULT_LANG


# # -------------------------------------------------------------------
# # FastAPI app
# # -------------------------------------------------------------------
# app = FastAPI(title="MedWhisper Voice + Text QA")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# _asr: WhisperModel | None = None
# _rag: MedWhisperRAG | None = None


# @app.on_event("startup")
# def _startup() -> None:
#     """Create RAG and Whisper instances once at startup."""
#     global _asr, _rag

#     logger.info("Initializing MedWhisper RAG Engine")
#     _rag = MedWhisperRAG()
#     logger.info("MedWhisper RAG Engine initialized")

#     logger.info(
#         "Loading Whisper model '%s' on device '%s' (compute_type=%s)",
#         WHISPER_MODEL,
#         WHISPER_DEVICE,
#         COMPUTE_TYPE,
#     )
#     _asr = WhisperModel(
#         WHISPER_MODEL,
#         device=WHISPER_DEVICE,
#         compute_type=COMPUTE_TYPE,
#     )
#     logger.info("Whisper model loaded")


# @app.get("/health")
# def health() -> Dict[str, str]:
#     return {
#         "status": "ok",
#         "whisper_model": WHISPER_MODEL,
#         "device": WHISPER_DEVICE,
#     }


# # -------------------------------------------------------------------
# # Helper: single, correct way to call your RAG engine
# # -------------------------------------------------------------------
# def _run_rag_query(
#     question: str,
#     *,
#     patient_id: Optional[str],
#     include_timeline: bool,
#     include_differential: bool,
#     user_role: str,
# ) -> Dict[str, Any]:
#     """Call MedWhisperRAG in the SAME way your old api_server.py did."""
#     if _rag is None:
#         raise HTTPException(503, "RAG engine not ready")

#     if not hasattr(_rag, "query"):
#         raise HTTPException(
#             500,
#             "MedWhisperRAG has no .query(...) method – expected one.",
#         )

#     # IMPORTANT: position question, only pass supported kwargs
#     return _rag.query(
#         question,
#         patient_id=patient_id,
#         include_timeline=include_timeline,
#         include_differential=include_differential,
#         user_role=user_role,
#     )


# # -------------------------------------------------------------------
# # 1) TEXT CHAT – JSON body, like normal ChatGPT
# # -------------------------------------------------------------------
# class TextQARequest(BaseModel):
#     question: str
#     language: Optional[str] = None  # not sent to RAG, just here for future
#     patient_id: Optional[str] = None
#     include_timeline: bool = False
#     include_differential: bool = False
#     user_role: str = "clinician"


# @app.post("/qa")
# async def text_qa(payload: TextQARequest = Body(...)) -> Dict[str, Any]:
#     """
#     Text-only QA.

#     Content-Type: application/json

#     {
#       "question": "What are the symptoms for lung cancer?",
#       "language": "en",
#       "patient_id": null,
#       "include_timeline": false,
#       "include_differential": false,
#       "user_role": "clinician"
#     }
#     """
#     if not payload.question.strip():
#         raise HTTPException(400, "Question cannot be empty")

#     rag = _run_rag_query(
#         question=payload.question,
#         patient_id=payload.patient_id,
#         include_timeline=payload.include_timeline,
#         include_differential=payload.include_differential,
#         user_role=payload.user_role,
#     )

#     return {
#         "mode": "text",
#         "text": {
#             "question": payload.question,
#             "language": payload.language,
#         },
#         "rag": rag,
#     }


# # -------------------------------------------------------------------
# # 2) VOICE CHAT – multipart/form-data with audio file
# # -------------------------------------------------------------------

# @app.post("/voice-qa")
# async def voice_qa(
#     file: UploadFile = File(..., description="Audio file (mp3/m4a/wav)"),
#     language: Optional[str] = Form(None),
#     patient_id: Optional[str] = Form(None),
#     include_timeline: bool = Form(False),
#     include_differential: bool = Form(False),
#     user_role: str = Form("clinician"),
# ) -> Dict[str, Any]:
#     """
#     Voice QA:
#     - User records a question with mic
#     - We transcribe via Whisper
#     - Then send the text to the SAME RAG pipeline as /qa

#     Content-Type: multipart/form-data
#     """
#     if _asr is None or _rag is None:
#         raise HTTPException(503, "Service not ready")

#     # ---------- Windows-safe temp file handling ----------
#     suffix = os.path.splitext(file.filename or "")[-1] or ".wav"
#     fd, tmp_path = tempfile.mkstemp(suffix=suffix)
#     os.close(fd)

#     try:
#         data = await file.read()
#         with open(tmp_path, "wb") as f:
#             f.write(data)

#         lang = _sanitize_language(language)

#         segments, info = _asr.transcribe(
#             tmp_path,
#             language=lang,
#             vad_filter=True,
#             beam_size=5,
#         )
#         transcript = "".join([s.text for s in segments]).strip()
#     finally:
#         # Clean up temp file
#         try:
#             os.remove(tmp_path)
#         except OSError:
#             pass

#     if not transcript:
#         raise HTTPException(400, "Could not extract any speech from audio")

#     rag = _run_rag_query(
#         question=transcript,
#         patient_id=patient_id,
#         include_timeline=include_timeline,
#         include_differential=include_differential,
#         user_role=user_role,
#     )

#     return {
#         "mode": "voice",
#         "whisper": {
#             "model": WHISPER_MODEL,
#             "device": WHISPER_DEVICE,
#             "compute_type": COMPUTE_TYPE,
#             "language": lang,
#             "language_probability": getattr(info, "language_probability", None),
#             "transcript": transcript,
#         },
#         "rag": rag,
#     }
















