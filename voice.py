from fastapi import APIRouter, UploadFile, File
from backend_app.services.voice_engine import speech_to_text, text_to_speech
from backend_app.services.text_engine import generate_response

router = APIRouter()

@router.post("/chat-voice")
async def chat_with_voice(file: UploadFile = File(...)):
    # Read uploaded audio
    audio_bytes = await file.read()

    # Step 1: Speech → Text
    user_text = speech_to_text(audio_bytes)

    # Step 2: Text → LLM
    bot_text = generate_response(user_text)

    # Step 3: LLM Response → Speech
    audio_path = text_to_speech(bot_text)

    return {
        "user_input": user_text,
        "bot_response": bot_text,
        "audio_file": audio_path
    }
