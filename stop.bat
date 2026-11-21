@echo off
rem ============================================================================
rem  stop.bat - arrete TenderIQ. Les donnees sont conservees (volumes Docker).
rem  Docker Desktop et Ollama restent allumes : ils servent aussi a d'autres projets.
rem ============================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo Arret de l'API, de l'interface et de MLflow...
for %%P in (8000 5173 5000) do (
    for /f "tokens=5" %%I in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do taskkill /PID %%I /T /F >nul 2>&1
)
taskkill /FI "WINDOWTITLE eq TenderIQ - *" /T /F >nul 2>&1

echo Arret des conteneurs...
docker compose stop

echo.
echo TenderIQ est arrete. Relance-le avec start.bat.
pause
