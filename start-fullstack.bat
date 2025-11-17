@echo off

echo ================================================
echo   AutoJobApplier - Full Stack Application
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Setting up Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating Python virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -q -r requirements.txt

REM Install playwright browsers if needed
echo Setting up Playwright...
playwright install chromium 2>nul || echo Playwright browsers already installed

REM Check if config exists
if not exist "config.py" (
    echo.
    echo WARNING: config.py not found!
    echo Copying config.example.py to config.py...
    copy config.example.py config.py
    echo Please edit config.py with your API keys and settings.
    echo.
)

REM Create necessary directories
if not exist "data\resumes" mkdir data\resumes
if not exist "data\exports" mkdir data\exports
if not exist "data\screenshots" mkdir data\screenshots

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules\" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

REM Start backend server
echo.
echo Starting backend server on http://localhost:8000...
start "AutoJobApplier Backend" python web_app.py

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend development server
echo Starting frontend server on http://localhost:3000...
cd frontend
start "AutoJobApplier Frontend" npm run dev

echo.
echo ================================================
echo   Application started successfully!
echo ================================================
echo.
echo   Backend API: http://localhost:8000
echo   Frontend UI: http://localhost:3000
echo.
echo   Close the terminal windows to stop servers
echo ================================================
echo.

cd ..
pause
