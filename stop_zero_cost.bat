@echo off
setlocal EnableExtensions
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_zero_cost.ps1" %*
if errorlevel 1 (
  echo.
  echo Failed to fully stop AgriGenie zero-cost deployment.
  pause
  exit /b 1
)

exit /b 0
