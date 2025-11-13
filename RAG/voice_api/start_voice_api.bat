@echo off
REM --- Voice→Text→RAG Startup Script ---

REM 1. Activate your virtual environment (adjust if your folder name differs)
if exist "%~dp0..\venv\Scripts\activate.bat" (
    call "%~dp0..\venv\Scripts\activate.bat"
) else if exist "%~dp0..\ .venv\Scripts\activate.bat" (
    call "%~dp0..\ .venv\Scripts\activate.bat"
) else (
    echo [!] No venv found. Activate manually if needed.
)

REM 2. Install dependencies for Whisper Voice API
pip install -r "%~dp0requirements_voice.txt"

REM 3. Check FFmpeg availability
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [!] FFmpeg not found on PATH. Install with: choco install ffmpeg -y
)

REM 4. Run the FastAPI server
cd /d "%~dp0.."
uvicorn voice_api.voice_api:app --host 0.0.0.0 --port 8088
