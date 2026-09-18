@echo off
setlocal
title Stop Dalil AI
cd /d "%~dp0"

echo Stopping Dalil AI containers...
docker compose down
if errorlevel 1 (
  echo.
  echo Dalil AI could not be stopped. Make sure Docker Desktop is running.
) else (
  echo.
  echo Dalil AI has stopped. Your database and uploads are still saved.
)
echo.
if /i "%DALIL_NO_PAUSE%"=="1" exit /b %errorlevel%
pause
