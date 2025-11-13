@echo off
echo ========================================
echo    MedWhisper Complete Chatbot System
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "pulseai_scaffold\api\main.py" (
    echo ERROR: Please run this from the MedWhisper_frontend directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo This will start ALL required services:
echo 1. FastAPI Backend (port 8001)
echo 2. Rasa Server (port 5005) 
echo 3. Rasa Actions Server (port 5055)
echo 4. React Frontend (port 3000)
echo.
echo ========================================
echo.

REM Start FastAPI Backend
echo [1/4] Starting FastAPI Backend...
start "FastAPI Backend" cmd /k "cd /d %CD%\pulseai_scaffold\api && pip install -r requirements.txt && python -m uvicorn main:app --reload --port 8001"

timeout /t 3 /nobreak >nul

REM Check if Rasa virtual environment exists
if not exist "RasaBot\rasa_venv\Scripts\Activate.bat" (
    echo.
    echo ========================================
    echo    RASA SETUP REQUIRED
    echo ========================================
    echo.
    echo Rasa virtual environment not found!
    echo Please run: RasaBot\setup_venv.bat
    echo.
    echo After setup, run this script again.
    pause
    exit /b 1
)

REM Start Rasa Actions Server
echo [2/4] Starting Rasa Actions Server...
start "Rasa Actions" cmd /k "cd /d %CD%\RasaBot && rasa_venv\Scripts\Activate.bat && rasa run actions"

timeout /t 3 /nobreak >nul

REM Start Rasa Server  
echo [3/4] Starting Rasa Server...
start "Rasa Server" cmd /k "cd /d %CD%\RasaBot && rasa_venv\Scripts\Activate.bat && rasa run --enable-api --cors *"

timeout /t 3 /nobreak >nul

REM Start React Frontend
echo [4/4] Starting React Frontend...
start "React Frontend" cmd /k "cd /d %CD%\MedWhisper && npm start"

echo.
echo ========================================
echo    All Services Starting!
echo ========================================
echo.
echo Services:
echo   FastAPI Backend: http://localhost:8001
echo   Rasa Server: http://localhost:5005
echo   Rasa Actions: http://localhost:5055  
echo   React App: http://localhost:3000
echo.
echo Wait 30 seconds for all services to start up,
echo then open: http://localhost:3000
echo.
echo Press any key to exit this launcher...
pause >nul
