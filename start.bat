@echo off
echo 🚀 Starting PRAI PR Review Agent (MongoDB + Groq)...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from .env.example...
    copy .env.example .env
    echo Please edit .env with your credentials before continuing.
    pause
    exit /b 1
)

REM Check if MongoDB is running
echo 🍃 Checking MongoDB connection...
mongosh --eval "db.adminCommand('ping')" > nul 2>&1
if errorlevel 1 (
    echo ⚠️  MongoDB is not running. Starting MongoDB...
    start /B mongod
    timeout /t 3 /nobreak > nul
)

REM Start FastAPI server
echo 🌐 Starting FastAPI server...
start "FastAPI Server" cmd /k uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

timeout /t 2 /nobreak > nul

echo.
echo ✅ PRAI is running!
echo    - API: http://localhost:8000
echo    - Docs: http://localhost:8000/docs
echo    - Database: MongoDB (PRAI_db)
echo    - LLM: Groq (llama-3.3-70b-versatile)
echo.
echo Press any key to open the application in your browser...
pause > nul
start http://localhost:8000
