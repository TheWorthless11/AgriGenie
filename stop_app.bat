@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ================================================
echo   AgriGenie Demo Stopper
echo ================================================
echo.

echo [1/2] Checking Docker Desktop...
docker version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker Desktop is not running or not installed.
  echo Please install/start Docker Desktop, then run this file again.
  echo.
  pause
  exit /b 1
)

echo [2/2] Stopping application containers...
docker compose down
if errorlevel 1 (
  echo ERROR: Failed to stop containers.
  echo Try again after opening Docker Desktop.
  echo.
  pause
  exit /b 1
)

echo.
echo App stopped successfully.
echo.
pause
