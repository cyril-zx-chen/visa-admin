@echo off
echo === Visa Admin Installer ===
echo.

REM Check uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo uv not found. Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo ERROR: Failed to install uv. Please install it manually from https://docs.astral.sh/uv/
        pause
        exit /b 1
    )
    echo uv installed successfully.
)

echo Installing dependencies with uv...
uv sync
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo Downloading Bootstrap 5 and icons for offline use...
uv run python -c "import urllib.request, os; os.makedirs('static/css/fonts', exist_ok=True); [urllib.request.urlretrieve(u, f) for u, f in [('https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css','static/css/bootstrap.min.css'),('https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js','static/js/bootstrap.bundle.min.js'),('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css','static/css/bootstrap-icons.min.css'),('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff2','static/css/fonts/bootstrap-icons.woff2'),('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/fonts/bootstrap-icons.woff','static/css/fonts/bootstrap-icons.woff')]]"

echo Initialising database...
uv run python -c "from database import init_db; init_db()"
if errorlevel 1 (
    echo ERROR: Database initialisation failed.
    pause
    exit /b 1
)

echo.
echo === Installation complete! Double-click run.bat to start. ===
pause
