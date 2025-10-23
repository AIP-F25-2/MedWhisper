import whisper
from gtts import gTTS
import tempfile
import os

os.environ["IMAGEIO_FFMPEG_EXE"] = r"C:\Users\singh\Downloads\ffmpeg-master-latest-win64-gpl-shared\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"

model = whisper.load_model("base")

def speech_to_text(audio_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    result = model.transcribe(tmp_path)
    os.remove(tmp_path)
    return result["text"]

def text_to_speech(text: str) -> str:
    tts = gTTS(text=text, lang="en")
    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    tts.save(tmp_path)
    return tmp_path
