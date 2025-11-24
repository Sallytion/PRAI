#!/bin/bash

echo "🚀 Starting PRAI PR Review Agent (MongoDB + Groq)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your credentials before continuing."
    exit 1
fi

# Check if MongoDB is running
echo "🍃 Checking MongoDB..."
if ! pgrep -x "mongod" > /dev/null; then
    echo "Starting MongoDB..."
    # Try Homebrew service (Mac)
    if command -v brew &> /dev/null; then
        brew services start mongodb-community
    # Try systemd (Linux)
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start mongodb
    # Try direct mongod
    else
        mongod --fork --logpath /var/log/mongodb.log
    fi
    sleep 2
fi

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

echo ""
echo "✅ PRAI is running!"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Database: MongoDB (PRAI_db)"
echo "   - LLM: Groq (llama-3.3-70b-versatile)"
echo ""
echo "Press Ctrl+C to stop the server"

# Wait for Ctrl+C
trap "kill $API_PID; exit" INT
wait
