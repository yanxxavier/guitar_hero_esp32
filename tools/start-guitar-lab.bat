@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\pythonw.exe" (
  echo Primeiro execute tools\install-desktop.bat
  pause
  exit /b 1
)
start "Guitar Lab" ".venv\Scripts\pythonw.exe" -m desktop.app
