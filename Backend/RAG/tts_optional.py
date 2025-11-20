# file: voice_api/tts_optional.py
import os
import pyttsx3
from pathlib import Path
import logging

logger = logging.getLogger("voice_api.tts")

# Enable TTS via environment variable
ENABLE_TTS = os.getenv("ENABLE_TTS", "false").lower() in {"true", "1", "yes"}

# Default Windows voice
TTS_VOICE = os.getenv("TTS_VOICE", "Microsoft Zira Desktop")

# Output folder (persistent)
BASE_TTS_DIR = Path.home() / "Desktop" / "TTS_Audio"
BASE_TTS_DIR.mkdir(parents=True, exist_ok=True)


def synthesize_tts(text: str) -> str | None:
    """
    Convert text → speech using pyttsx3 and save to Desktop/TTS_Audio.
    Returns the file path.
    """
    logger.info(f"TTS called | ENABLE_TTS={ENABLE_TTS}, text_len={len(text) if text else 0}")

    if not ENABLE_TTS:
        logger.warning("TTS disabled — skipping synthesis")
        return None

    if not text:
        return None

    try:
        engine = pyttsx3.init()

        # Set voice
        voices = engine.getProperty('voices')
        for v in voices:
            if TTS_VOICE.lower() in v.name.lower():
                engine.setProperty('voice', v.id)
                break

        # Output file
        out_path = BASE_TTS_DIR / f"tts_output_{abs(hash(text))}.mp3"

        engine.save_to_file(text, str(out_path))
        engine.runAndWait()

        logger.info(f"TTS saved to {out_path}")
        return str(out_path)

    except Exception as e:
        logger.exception(f"TTS synthesis failed: {e}")
        return None
