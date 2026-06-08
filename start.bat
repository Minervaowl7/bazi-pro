@echo off
title Bazi-Pro Dev Server
setlocal enabledelayedexpansion

echo.
echo  ======================================
echo       Bazi-Pro Quick Start
echo  ======================================
echo.

set "ROOT=%~dp0"
set "BACKEND_PORT=8711"
set "FRONTEND_PORT=3000"

REM === Find Python ===
set "PYTHON_EXE="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if "!PYTHON_EXE!"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if "!PYTHON_EXE!"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if "!PYTHON_EXE!"=="" if exist "C:\Python312\python.exe" set "PYTHON_EXE=C:\Python312\python.exe"
if "!PYTHON_EXE!"=="" for %%c in (python py python3) do @if "!PYTHON_EXE!"=="" (where %%c >nul 2>&1 && set "PYTHON_EXE=%%c")
if "!PYTHON_EXE!"=="" (
    echo  ERROR: Python not found! Install from https://python.org
    pause & exit /b 1
)
"!PYTHON_EXE!" -c "print('ok')" >nul 2>&1
if !errorlevel! neq 0 (
    echo  ERROR: !PYTHON_EXE! is not working. Install from https://python.org
    pause & exit /b 1
)
echo  [OK] Python: !PYTHON_EXE!

REM === Find pnpm ===
set "PNPM_EXE="
if exist "%APPDATA%\npm\pnpm.cmd" set "PNPM_EXE=%APPDATA%\npm\pnpm.cmd"
if "!PNPM_EXE!"=="" for %%c in (pnpm npx) do @if "!PNPM_EXE!"=="" (where %%c >nul 2>&1 && set "PNPM_EXE=%%c")
if "!PNPM_EXE!"=="" (
    echo  ERROR: pnpm not found! Run: npm install -g pnpm
    pause & exit /b 1
)
echo  [OK] pnpm: !PNPM_EXE!

REM === Kill old processes on ports ===
echo.
echo  [1/3] Cleaning ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT% " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT% " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
timeout /t 1 /nobreak >nul

REM === Start backend ===
echo  [2/3] Starting backend on :%BACKEND_PORT% ...
cd /d "!ROOT!"
start "Bazi-Backend" cmd /k "!PYTHON_EXE!" -m uvicorn server.app:app --host 127.0.0.1 --port %BACKEND_PORT%

REM === Start frontend ===
echo  [3/3] Starting frontend on :%FRONTEND_PORT% ...
timeout /t 2 /nobreak >nul
cd /d "!ROOT!frontend"
start "Bazi-Frontend" cmd /k "!PNPM_EXE!" dev
timeout /t 3 /nobreak >nul
start http://localhost:%FRONTEND_PORT%

echo.
echo  --------------------------------------
echo   Backend:  http://127.0.0.1:%BACKEND_PORT%
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo  --------------------------------------
echo.
echo  Close this window or press Ctrl+C to stop.
echo.

:waitloop
timeout /t 60 /nobreak >nul
goto waitloop
