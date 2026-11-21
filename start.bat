@echo off
rem ============================================================================
rem  start.bat - lance TOUT TenderIQ en un double-clic.
rem  Relancable sans risque : chaque etape verifie d'abord si c'est deja fait.
rem ============================================================================
setlocal
chcp 65001 >nul
title TenderIQ - demarrage
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PY=.venv\Scripts\python.exe"

echo.
echo  ===========================================
echo     TenderIQ - lancement automatique
echo  ===========================================
echo.

rem (pour attendre N secondes on utilise 'ping -n N+1 127.0.0.1' : contrairement a 'timeout',
rem  il marche aussi quand le .bat est lance depuis un autre programme)

rem ---------- 1. Environnement Python ----------
if exist "%PY%" goto :venv_ok
echo [1/8] Creation de l'environnement Python (une seule fois, quelques minutes)...
python -m venv .venv || goto :error
"%PY%" -m pip install -r backend\requirements.txt || goto :error
:venv_ok
echo [1/8] Environnement Python : OK

rem ---------- 2. Fichier .env ----------
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [2/8] .env cree a partir de .env.example - pense a changer les mots de passe
) else (
    echo [2/8] Fichier .env : OK
)

rem ---------- 3. Docker Desktop ----------
docker info >nul 2>&1 && goto :docker_ok
echo [3/8] Demarrage de Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
set /a tries=0
:wait_docker
docker info >nul 2>&1 && goto :docker_ok
set /a tries+=1
if %tries% gtr 60 (
    echo     Docker ne demarre pas. Ouvre Docker Desktop a la main puis relance start.bat.
    goto :error
)
ping -n 4 127.0.0.1 >nul
goto :wait_docker
:docker_ok
echo [3/8] Docker : OK

rem ---------- 4. Ollama (le LLM local) ----------
curl -s -o nul http://localhost:11434/api/tags && goto :ollama_ok
echo [4/8] Demarrage d'Ollama...
start "" "%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"
:ollama_ok
echo [4/8] Ollama : lance

rem ---------- 5. Conteneurs (3 essais si la connexion coupe un telechargement) ----------
echo [5/8] Conteneurs : PostgreSQL, Qdrant, Mailpit, Prometheus, Grafana...
set /a tries=0
:compose
docker compose up -d postgres qdrant mailpit prometheus grafana && goto :compose_ok
set /a tries+=1
if %tries% geq 3 goto :error
echo     Nouvel essai dans 5 s...
ping -n 6 127.0.0.1 >nul
goto :compose
:compose_ok

rem ---------- 6. MLflow (suivi des experiences ML) ----------
call :port_busy 5000 && goto :mlflow_ok
start "TenderIQ - MLflow" /min cmd /k .venv\Scripts\mlflow.exe server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 127.0.0.1 --port 5000
:mlflow_ok
echo [6/8] MLflow : lance

rem ---------- 7. Donnees : ne prepare que ce qui manque ----------
echo [7/8] Verification des donnees...
"%PY%" -m backend.bootstrap || goto :error

rem ---------- 8. API + interface web ----------
call :port_busy 8000 && goto :api_ok
start "TenderIQ - API" cmd /k .venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000 --reload --reload-dir backend
:api_ok
if not exist "frontend\node_modules" (
    echo     Installation des dependances du front, une seule fois...
    pushd frontend && call npm install --no-audit --no-fund && popd
)
call :port_busy 5173 && goto :front_ok
start "TenderIQ - Front" cmd /k "cd frontend && npm run dev"
:front_ok
echo [8/8] API et interface : lancees

echo.
echo     Attente de l'API...
set /a tries=0
:wait_api
curl -s -o nul http://localhost:8000/health && goto :api_ready
set /a tries+=1
if %tries% gtr 40 goto :error
ping -n 3 127.0.0.1 >nul
goto :wait_api
:api_ready

start "" http://localhost:5173

echo.
echo  ===========================================
echo     TenderIQ est pret
echo  ===========================================
echo     Interface      http://localhost:5173   (analyste / analyste123 ou admin / admin123)
echo     API (Swagger)  http://localhost:8000/docs
echo     Grafana        http://localhost:3001   (admin / admin)
echo     Prometheus     http://localhost:9090
echo     MLflow         http://localhost:5000
echo     Qdrant         http://localhost:6333/dashboard
echo     Mailpit        http://localhost:8025   (e-mails envoyes)
echo.
echo     Pour tout arreter : double-clic sur stop.bat
echo.
pause
exit /b 0

rem ---------- Petite fonction : le port %1 est-il deja utilise ? (code 0 = oui) ----------
:port_busy
netstat -ano | findstr /R /C:":%1 .*LISTENING" >nul
exit /b %errorlevel%

:error
echo.
echo  *** Le lancement a echoue a l'etape ci-dessus. Lis le message d'erreur, corrige, puis relance start.bat. ***
echo.
pause
exit /b 1
