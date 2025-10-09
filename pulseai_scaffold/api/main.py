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
    # Only use Rasa for replies (OpenAI removed)
    # Force Rasa URL to port 5005 regardless of .env
    rasa_url = "http://localhost:5005/webhooks/rest/webhook"
    print("Using Rasa URL:", rasa_url)
    logger.info(f"/chat from sender={req.sender!r}: {req.message!r} -> {rasa_url}")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                rasa_url,
                json={"sender": req.sender, "message": req.message},
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            logger.info(f"Raw Rasa response: {r.text}")
            try:
                data = r.json()
            except Exception as json_err:
                logger.error(f"JSON decode error: {json_err}. Raw response: {r.text}")
                return JSONResponse(content={"replies": [f"Rasa returned invalid JSON: {r.text}"]})
        replies = [m.get("text") for m in data if isinstance(m, dict) and "text" in m]
        reply = replies[0] if replies else "Sorry, I couldn't answer that."
        # If reply looks like JSON, extract text value
        if reply and reply.strip().startswith("{"):
            try:
                import json
                parsed = json.loads(reply)
                if parsed and isinstance(parsed, dict) and parsed.get("text"):
                    reply = parsed["text"]
            except Exception as inner_json_err:
                logger.error(f"Inner JSON decode error: {inner_json_err}. Raw reply: {reply}")
                pass
        return JSONResponse(content={"replies": [reply]})
    except Exception as e:
        logger.error(f"Rasa call failed, using mock. Error: {e}")
        reply = f"You said: {req.message}. Med-Whisper reply coming soon."
        return JSONResponse(content={"replies": [reply]})
