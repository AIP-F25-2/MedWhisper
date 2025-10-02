import whisper
from gtts import gTTS
import tempfile
import os

# Explicitly set FFmpeg path on Windows (adjust if needed)
os.environ["IMAGEIO_FFMPEG_EXE"] = r"C:\Users\singh\Downloads\ffmpeg-master-latest-win64-gpl-shared\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"

# Load Whisper model once
model = whisper.load_model("base")

def speech_to_text(audio_bytes: bytes) -> str:
    """Convert speech audio to text using Whisper"""
    # Save bytes to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    # Close file to allow FFmpeg access
    tmp.close()

    # Transcribe audio
    result = model.transcribe(tmp_path)

    # Optionally delete temp file
    os.remove(tmp_path)

    return result["text"]

def text_to_speech(text: str) -> str:
    """Convert text to speech using gTTS"""
    tts = gTTS(text=text, lang="en")
    
    # Save to temp mp3 file
    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    tts.save(tmp_path)

    return tmp_path
