@echo off
echo Starting Community Helpdesk Chatbot...
echo ==========================================

if not exist "venv\" (
    echo Virtual environment not found!
    pause
    exit /b 1
)

if not exist "chroma_db\" (
    echo Initializing database...
    call venv\Scripts\activate.bat
    python -m database.chroma_setup
)

echo Starting Backend API...
start "Backend API" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 5 /nobreak > nul

echo Starting Frontend...
start "Frontend" cmd /k "call venv\Scripts\activate.bat && streamlit run frontend\streamlit_app.py"

echo ========================================
echo Application running
echo Frontend: http://localhost:8501
echo Backend: http://localhost:8000
echo ========================================
pause
