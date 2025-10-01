# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, httpx, logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("medwhisper")
logging.basicConfig(level=logging.INFO)

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

@app.get("/")
async def root():
    return {"service": "Med-Whisper Gateway", "endpoints": ["/health", "/chat"]}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(req: ChatRequest):
    """Forward message to Rasa. If Rasa is unavailable, return a mock reply."""
    rasa_url = os.getenv("RASA_REST_URL", "http://localhost:5005/webhooks/rest/webhook")
    logger.info(f"/chat from sender={req.sender!r}: {req.message!r} -> {rasa_url}")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                rasa_url,
                json={"sender": req.sender, "message": req.message},
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()  # Rasa typically returns a list of message dicts
        replies = [m.get("text") for m in data if isinstance(m, dict) and "text" in m]
        if not replies:
            replies = ["Sorry, I couldn't answer that."]
        return {"replies": replies, "raw": data}

    except Exception as e:
        logger.warning(f"Rasa call failed, using mock. Error: {e}")
        replies = [f"(mock) You said: {req.message}. Med-Whisper reply coming soon."]
        return {"replies": replies, "raw": []}
