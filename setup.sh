#!/bin/bash
# Setup script for AutoJobApplier

echo "=========================================="
echo "AutoJobApplier Setup"
echo "=========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment created and activated"
else
    echo "Error: Failed to create virtual environment"
    exit 1
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing Python packages..."
pip install -r requirements.txt

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers..."
playwright install chromium

# Create config file if it doesn't exist
if [ ! -f "config.py" ]; then
    echo ""
    echo "Creating config.py from template..."
    cp config.example.py config.py
    echo "✓ config.py created"
    echo "⚠️  Please edit config.py with your settings"
else
    echo ""
    echo "✓ config.py already exists"
fi

# Create data directory
mkdir -p data logs screenshots

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config.py with your settings"
echo "2. Add your Anthropic API key"
echo "3. Place your resume in data/resume.pdf"
echo "4. Run: python main.py --search-only"
echo ""
echo "To activate the environment later:"
echo "source venv/bin/activate"
echo ""
