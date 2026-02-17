#!/bin/bash

# Function to kill processes on exit
cleanup() {
    echo "🛑 Stopping Balance AI..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
}
trap cleanup EXIT

echo "🚀 Starting Balance AI Hackathon Solution..."

# Start Backend
echo "Starting Backend (FastAPI)..."
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo "✅ Backend ID: $BACKEND_PID"

# Start Frontend
echo "Starting Frontend (Vite)..."
cd ../frontend
npm run dev -- --port 5173 &
FRONTEND_PID=$!
echo "✅ Frontend ID: $FRONTEND_PID"

echo "------------------------------------------------"
echo "🎉 Balance AI is LIVE at: http://localhost:5173"
echo "------------------------------------------------"
echo "Backend API: http://localhost:8000"
echo "Press Ctrl+C to stop."
echo "------------------------------------------------"

wait $BACKEND_PID $FRONTEND_PID
