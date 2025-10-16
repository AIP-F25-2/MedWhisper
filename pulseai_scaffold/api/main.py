# main.py

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, httpx, logging
import openai
from dotenv import load_dotenv


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
logger = logging.getLogger("medwhisper")
logging.basicConfig(level=logging.INFO)

# Backend selection: 'rasa' or 'gemini'. Default to 'gemini'.
QA_BACKEND = os.getenv("QA_BACKEND", "gemini").lower()
GEMINI_QA_URL = os.getenv("GEMINI_QA_URL", "https://b946f3a056f1.ngrok-free.app/ml/qa")

app = FastAPI(title="Med-Whisper Gateway")

# Allow the React dev server to call the API
# (add more origins if you use a different port or host)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    sender: str
    message: str



from fastapi.responses import StreamingResponse, JSONResponse
import asyncio

@app.post("/chat")
async def chat(req: ChatRequest):
    """Forward message to OpenAI with streaming if API key is set, else Rasa. Returns AI reply."""
    logger.info(f"/chat from sender={req.sender!r}: {req.message!r} -> backend={QA_BACKEND}")
    try:
        reply = ""
        if QA_BACKEND == "rasa":
            rasa_url = "http://localhost:5005/webhooks/rest/webhook"
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    rasa_url,
                    json={"sender": req.sender, "message": req.message},
                    headers={"Content-Type": "application/json"},
                )
                r.raise_for_status()
                logger.info(f"Raw Rasa response: {r.text}")
                data = r.json()
            replies = [m.get("text") for m in data if isinstance(m, dict) and "text" in m]
            reply = replies[0] if replies else "Sorry, I couldn't answer that."
            # Recursively unwrap reply if it is a JSON string with 'replies' or 'text'
            def extract_plain_text(val):
                import json
                if isinstance(val, str) and val.strip().startswith("{"):
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, dict):
                            if parsed.get("text") and isinstance(parsed["text"], str):
                                return extract_plain_text(parsed["text"])
                            if parsed.get("replies") and isinstance(parsed["replies"], list) and parsed["replies"]:
                                return extract_plain_text(parsed["replies"][0])
                    except Exception as inner_json_err:
                        logger.error(f"Inner JSON decode error: {inner_json_err}. Raw reply: {val}")
                        pass
                return val
            reply = extract_plain_text(reply)
        else:
            # Use Gemini QA
            async with httpx.AsyncClient(timeout=10) as client:
                payload = {"q": req.message, "role": "doctor"}
                r = await client.post(
                    GEMINI_QA_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                r.raise_for_status()
                logger.info(f"Raw Gemini QA response: {r.text}")
                data = r.json()
            # For doctor role, include confidence and citations if available
            reply = data.get("answer_text") or data.get("answer") or data.get("text") or "Sorry, I couldn't answer that."
            
            # Add confidence and citations for doctor responses
            if "confidence" in data:
                reply += f"\n\nConfidence: {data['confidence']}"
            if "citations" in data and data["citations"]:
                citations_str = ", ".join(data["citations"])
                reply += f"\nCitations: {citations_str}"
        return JSONResponse(content={"text": reply})
    except Exception as e:
        logger.error(f"Error in /chat: {e}")
        return JSONResponse(content={"text": f"[ERROR]: {str(e)}"}, status_code=500)
