@echo off
setlocal
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv directory.
    echo Please create it first using: python -m venv .venv
    pause
    exit /b 1
)

echo [INFO] Starting HOU-S-RIMS survey analysis tool...
echo [INFO] Using virtual environment: %CD%\.venv
echo.

:: Run the application
".venv\Scripts\python.exe" app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%
    pause
)
endlocal
