@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ================================================
echo   AgriGenie Demo Launcher
echo ================================================
echo.

echo [1/5] Checking Docker Desktop...
docker version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker Desktop is not running or not installed.
  echo Please install/start Docker Desktop, then run this file again.
  echo.
  pause
  exit /b 1
)

echo [2/5] Checking Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker Compose is not available.
  echo Please update Docker Desktop, then run this file again.
  echo.
  pause
  exit /b 1
)

echo [3/5] Loading prebuilt image archive...
if not exist "agrigenie.tar" (
  echo ERROR: agrigenie.tar not found in this folder.
  echo Put agrigenie.tar next to this file and try again.
  echo.
  pause
  exit /b 1
)

set "NEED_LOAD=0"
for %%I in (
  agrigenie-web:latest
  agrigenie-celery_worker:latest
  agrigenie-celery_beat:latest
  postgres:16-alpine
  redis:7-alpine
) do (
  docker image inspect "%%I" >nul 2>&1
  if errorlevel 1 set "NEED_LOAD=1"
)

if "!NEED_LOAD!"=="1" (
  echo Importing images from agrigenie.tar ^(first run may take several minutes^)...
  docker load -i "agrigenie.tar"
  if errorlevel 1 (
    echo ERROR: Failed to load agrigenie.tar
    echo The tar file may be incomplete or corrupted.
    echo.
    pause
    exit /b 1
  )
) else (
  echo Required images already exist locally. Skipping docker load.
)

set "APP_PORT=8000"
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if not errorlevel 1 (
  set "APP_PORT=8001"
  echo Port 8000 is busy. Fallback to port 8001.
)
set "APP_URL=http://localhost:%APP_PORT%"

echo [4/5] Starting application with Docker Compose...
set "APP_PORT=%APP_PORT%"
docker rm -f agrigenie-db agrigenie-redis agrigenie-web agrigenie-celery-worker agrigenie-celery-beat >nul 2>&1
docker compose down --remove-orphans
docker compose up -d --no-build --remove-orphans
if errorlevel 1 (
  echo ERROR: Failed to start containers.
  echo If this is your first export, ensure agrigenie.tar includes:
  echo   agrigenie-web:latest
  echo   agrigenie-celery_worker:latest
  echo   agrigenie-celery_beat:latest
  echo.
  pause
  exit /b 1
)

echo [5/5] Opening browser...
start "" "%APP_URL%"
echo App is starting at:
echo   %APP_URL%
echo.
echo To stop the app later, run: docker compose down
echo.
exit /b 0
