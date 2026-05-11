@echo off
title Wedding Photo Ranker - Setup and Run
color 0A
cls

echo.
echo  =====================================================
echo    WEDDING PHOTO RANKER  -  Windows Edition
echo  =====================================================
echo.

:: ── STEP 1: Check if Python is installed ────────────────
echo  [1/4] Checking if Python is installed ...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: Python is NOT installed on this computer.
    echo.
    echo  Please do the following:
    echo  1. Open your web browser
    echo  2. Go to:  https://www.python.org/downloads/
    echo  3. Click "Download Python" (the big yellow button)
    echo  4. Run the installer
    echo     IMPORTANT: Tick "Add Python to PATH" checkbox!
    echo  5. After installing, run this file again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo  OK - Found %PYVER%
echo.

:: ── STEP 2: Upgrade pip silently ─────────────────────────
echo  [2/4] Updating pip ...
python -m pip install --upgrade pip -q >nul 2>&1
echo  OK
echo.

:: ── STEP 3: Install required packages ────────────────────
echo  [3/4] Installing required packages (first time only) ...
echo  (This may take 1-2 minutes on first run - please wait)
echo.
python -m pip install opencv-python Pillow imagehash numpy tqdm rawpy pillow-heif -q
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo  Some packages failed to install.
    echo  Please make sure your internet connection is working
    echo  and try again.
    echo.
    pause
    exit /b 1
)
echo.
echo  OK - All packages ready
echo.

:: ── STEP 4: Run the ranker ────────────────────────────────
echo  [4/4] Starting Wedding Photo Ranker ...
echo.
echo  =====================================================
echo.

python "%~dp0wedding_photo_ranker.py"

:: If Python crashed, show error
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo  Something went wrong. Please take a screenshot
    echo  of this window and share with your tech team.
    echo.
    pause
)
