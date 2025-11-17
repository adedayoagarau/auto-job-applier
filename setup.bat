@echo off
REM Setup script for AutoJobApplier (Windows)

echo ==========================================
echo AutoJobApplier Setup
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)
echo Python found

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    exit /b 1
)
echo Virtual environment created

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo Installing Python packages...
pip install -r requirements.txt

REM Install Playwright browsers
echo.
echo Installing Playwright browsers...
playwright install chromium

REM Create config file
if not exist config.py (
    echo.
    echo Creating config.py from template...
    copy config.example.py config.py
    echo config.py created
    echo Please edit config.py with your settings
) else (
    echo.
    echo config.py already exists
)

REM Create directories
if not exist data mkdir data
if not exist logs mkdir logs
if not exist screenshots mkdir screenshots

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit config.py with your settings
echo 2. Add your Anthropic API key
echo 3. Place your resume in data\resume.pdf
echo 4. Run: python main.py --search-only
echo.
echo To activate the environment later:
echo venv\Scripts\activate.bat
echo.
pause
