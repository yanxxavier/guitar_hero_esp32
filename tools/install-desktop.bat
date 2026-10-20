@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt
if errorlevel 1 goto error
echo Instalado. Abra tools\start-guitar-lab.bat para iniciar.
pause
exit /b 0
:error
echo Instalacao interrompida. Confira Python 3.10 ou mais recente e conexao com a internet.
pause
exit /b 1
