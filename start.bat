@echo off
title Bazi-Pro Dev Server

echo.
echo  ======================================
echo       Bazi-Pro Quick Start
echo  ======================================
echo.

set "ROOT=%~dp0"
set "BACKEND_PORT=8711"
set "FRONTEND_PORT=3000"

echo  [1/3] Checking ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT% " ^| findstr LISTENING') do (
    echo  ! Port %BACKEND_PORT% in use ^(PID %%a^), killing...
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT% " ^| findstr LISTENING') do (
    echo  ! Port %FRONTEND_PORT% in use ^(PID %%a^), killing...
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo  [2/3] Starting backend ^(http://127.0.0.1:%BACKEND_PORT%^) ...
start "Bazi-Backend" cmd /c "cd /d "%ROOT%" && python -m uvicorn server.app:app --host 127.0.0.1 --port %BACKEND_PORT% --reload"

echo  [3/3] Starting frontend ^(http://localhost:%FRONTEND_PORT%^) ...
timeout /t 2 /nobreak >nul
start "Bazi-Frontend" cmd /c "cd /d "%ROOT%frontend" && pnpm dev"
timeout /t 3 /nobreak >nul
start http://localhost:%FRONTEND_PORT%

echo.
echo  --------------------------------------
echo   Backend:  http://127.0.0.1:%BACKEND_PORT%
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo   API Docs: http://127.0.0.1:%BACKEND_PORT%/docs
echo  --------------------------------------
echo.
echo  Close this window to stop both services.
echo.

:waitloop
timeout /t 60 /nobreak >nul
goto waitloop
