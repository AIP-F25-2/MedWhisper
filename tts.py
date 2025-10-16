from fastapi import APIRouter, Form
from fastapi.responses import FileResponse
from backend.backend_app.services.text_engine import generate_response
from backend.backend_app.services.voice_engine import text_to_speech
import os

router = APIRouter()

@router.post("/")
def llm_to_speech(text: str = Form(...)):
    """
    Takes input text, generates LLM response, converts that response to speech,
    and returns both the text and audio file.
    """
    # Step 1: Generate LLM response
    llm_reply = generate_response(text)

    # Step 2: Convert LLM response to speech
    audio_path = text_to_speech(llm_reply)
    filename = os.path.basename(audio_path)

    # Step 3: Return both response and audio file
    return {
        "user_input": text,
        "bot_response": llm_reply,
        "audio_file": filename,
        "audio_path": audio_path
    }
