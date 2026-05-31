@echo off
echo === Starting Visa Admin ===

uv --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found. Please run install.bat first.
    pause
    exit /b 1
)

echo Server starting at http://localhost:5001
echo Close this window to stop.
uv run python app.py
