@echo off

echo ================================================
echo   AutoJobApplier - Web Interface
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install playwright browsers if needed
echo Setting up Playwright...
playwright install

REM Check if config exists
if not exist "config.py" (
    echo.
    echo WARNING: config.py not found!
    echo Please copy config.example.py to config.py and configure it.
    echo.
    pause
)

REM Create necessary directories
if not exist "data\resumes" mkdir data\resumes
if not exist "data\exports" mkdir data\exports
if not exist "data\screenshots" mkdir data\screenshots

echo.
echo Starting web server...
echo Access the application at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the web server
python web_app.py

pause
