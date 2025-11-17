#!/bin/bash

# AutoJobApplier - Full Stack Startup Script (Backend + Frontend)

echo "================================================"
echo "  AutoJobApplier - Full Stack Application"
echo "================================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating Python virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Install playwright browsers if needed
echo "Setting up Playwright..."
playwright install chromium 2>/dev/null || echo "Playwright browsers already installed"

# Check if config exists
if [ ! -f "config.py" ]; then
    echo ""
    echo "WARNING: config.py not found!"
    echo "Copying config.example.py to config.py..."
    cp config.example.py config.py
    echo "Please edit config.py with your API keys and settings."
    echo ""
fi

# Create necessary directories
mkdir -p data/resumes data/exports data/screenshots

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start backend server in background
echo ""
echo "Starting backend server on http://localhost:8000..."
python web_app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend development server
echo "Starting frontend server on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "================================================"
echo "  Application started successfully!"
echo "================================================"
echo ""
echo "  Backend API: http://localhost:8000"
echo "  Frontend UI: http://localhost:3000"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo "================================================"
echo ""

# Wait for both processes
wait
