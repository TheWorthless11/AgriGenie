@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if "%~1"=="" (
  echo Usage: .\setup_named_tunnel.bat app.yourdomain.com
  exit /b 1
)

set "HOSTNAME=%~1"
shift

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_named_tunnel.ps1" -Hostname "%HOSTNAME%" %*
if errorlevel 1 (
  echo.
  echo Failed to configure named Cloudflare tunnel.
  exit /b 1
)

exit /b 0
