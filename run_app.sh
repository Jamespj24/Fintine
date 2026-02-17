#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Function to kill processes on exit
cleanup() {
    echo "🛑 Stopping Fintine..."
    pkill -f "uvicorn main:app" || true
    pkill -f "vite" || true
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
}
trap cleanup EXIT

echo "🚀 Starting Fintine..."

# Start Backend
echo "Starting Backend (FastAPI)..."
source "$SCRIPT_DIR/backend/venv/bin/activate"
uvicorn main:app --reload --port 8000 --app-dir "$SCRIPT_DIR/backend" &
BACKEND_PID=$!
echo "✅ Backend PID: $BACKEND_PID"

# Wait for backend to be ready before starting frontend
echo "⏳ Waiting for backend to start..."
for i in $(seq 1 15); do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
done

# Start Frontend
echo "Starting Frontend (Vite)..."
npm run dev --prefix "$SCRIPT_DIR/frontend" -- --port 5173 &
FRONTEND_PID=$!
echo "✅ Frontend PID: $FRONTEND_PID"

echo "------------------------------------------------"
echo "🎉 Fintine is LIVE at: http://localhost:5173"
echo "------------------------------------------------"
echo "Backend API: http://localhost:8000"
echo "Press Ctrl+C to stop."
echo "------------------------------------------------"

wait $BACKEND_PID $FRONTEND_PID
