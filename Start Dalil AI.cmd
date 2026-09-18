@echo off
setlocal
title Dalil AI Launcher
cd /d "%~dp0"

cls
echo ============================================================
echo                    DALIL AI LAUNCHER
echo ============================================================
echo.
echo Starting Docker, Ollama, backend, and frontend...
echo The first run can take several minutes. Later runs are faster.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-dalil.ps1"
if errorlevel 1 goto failed

cls
echo ============================================================
echo                    Dalil AI is running
echo ============================================================
echo.
echo Website:  http://localhost:3000
echo API:      http://localhost:8000
echo Health:   http://localhost:8000/health
echo.
echo You can close this window. Docker will keep Dalil AI running.
echo To stop it later, run: docker compose down
echo.
if /i "%DALIL_NO_PAUSE%"=="1" exit /b 0
pause
exit /b 0

:failed
echo.
echo ============================================================
echo Dalil AI could not start.
echo Read the error above, then double-click this file to try again.
echo ============================================================
echo.
if /i "%DALIL_NO_PAUSE%"=="1" exit /b 1
pause
exit /b 1
