@echo off
echo ========================================
echo    MedWhisper Chatbot Launcher
echo ========================================
echo.

echo Starting FastAPI Backend...
start "FastAPI Backend" cmd /k "cd /d E:\MedWhisper_frontend\pulseai_scaffold\api && pip install -r requirements.txt && python -m uvicorn main:app --reload --port 8001"

timeout /t 3 /nobreak >nul

echo Starting React Frontend...
start "React Frontend" cmd /k "cd /d E:\MedWhisper_frontend\MedWhisper & npm start"

echo.
echo ========================================
echo   IMPORTANT: You need to run RASA too!
echo ========================================
echo.
echo 1. FastAPI Backend: http://localhost:8001
echo 2. React Frontend: http://localhost:3000  
echo 3. Rasa Server: http://localhost:5005 (MANUAL START REQUIRED)
echo.
echo To start Rasa:
echo   cd RasaBot
echo   .\rasa_venv\Scripts\Activate.ps1
echo   rasa run --enable-api --cors "*"
echo.
echo ========================================
echo.
echo Press any key to exit this launcher...
pause >nul

