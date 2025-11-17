#!/bin/bash

# AutoJobApplier Web Server Startup Script

echo "================================================"
echo "  AutoJobApplier - Web Interface"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install playwright browsers if needed
echo "Setting up Playwright..."
playwright install

# Check if config exists
if [ ! -f "config.py" ]; then
    echo ""
    echo "WARNING: config.py not found!"
    echo "Please copy config.example.py to config.py and configure it."
    echo ""
    read -p "Press Enter to continue anyway or Ctrl+C to exit..."
fi

# Create necessary directories
mkdir -p data/resumes
mkdir -p data/exports
mkdir -p data/screenshots

echo ""
echo "Starting web server..."
echo "Access the application at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the web server
python web_app.py
