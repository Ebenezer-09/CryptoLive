@echo off
chcp 65001 >nul
cls

REM ============================================
REM Script de demarrage du projet Binance Real-Time
REM ============================================

echo ============================================
echo    BINANCE REAL-TIME STREAMING SYSTEM
echo ============================================
echo.
echo [INFO] Demarrage du systeme...
echo.

REM Verifier que Docker est installe
echo [CHECK] Verification de Docker...
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker n'est pas installe.
    echo [INFO] Installez Docker Desktop depuis: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker detecte

REM Detecter Docker Compose (V2 ou V1)
echo [CHECK] Detection de Docker Compose...
docker compose version >nul 2>nul
if %errorlevel% equ 0 (
    set "DOCKER_COMPOSE=docker compose"
    set "COMPOSE_VERSION=v2"
    echo [OK] Docker Compose v2 detecte
) else (
    where docker-compose >nul 2>nul
    if %errorlevel% equ 0 (
        set "DOCKER_COMPOSE=docker-compose"
        set "COMPOSE_VERSION=v1"
        echo [OK] Docker Compose v1 detecte
    ) else (
        echo [ERROR] Docker Compose n'est pas installe.
        echo [INFO] Installez Docker Compose depuis: https://docs.docker.com/compose/install/
        pause
        exit /b 1
    )
)
echo.

REM Creer les repertoires necessaires
echo [STEP 1/5] Creation des repertoires de donnees...
if not exist "backend\spark_processor\checkpoints" mkdir backend\spark_processor\checkpoints
if not exist "backend\spark_processor\data" mkdir backend\spark_processor\data
echo [OK] Repertoires crees
echo.

REM Nettoyer les anciennes instances
echo [STEP 2/5] Nettoyage des anciennes instances...
%DOCKER_COMPOSE% down -v >nul 2>nul
echo [OK] Nettoyage termine
echo.

REM Supprimer les conteneurs orphelins
echo [STEP 3/5] Suppression des conteneurs orphelins...
docker container prune -f >nul 2>nul
docker volume prune -f >nul 2>nul
echo [OK] Conteneurs orphelins supprimes
echo.

REM Construire les images
echo [STEP 4/5] Construction des images Docker...
echo [INFO] Cette operation peut prendre plusieurs minutes...
%DOCKER_COMPOSE% build
if %errorlevel% neq 0 (
    echo [ERROR] Erreur lors de la construction des images
    pause
    exit /b 1
)
echo [OK] Images construites avec succes
echo.

REM Demarrer les services
echo [STEP 5/5] Demarrage des services...
%DOCKER_COMPOSE% up -d
if %errorlevel% neq 0 (
    echo [ERROR] Erreur lors du demarrage des services
    pause
    exit /b 1
)
echo [OK] Services demarres
echo.

echo [INFO] Attente du demarrage complet des services...
echo [INFO] Verification de l'etat des services toutes les 5 secondes...
echo [INFO] Verification 1/6...
timeout /t 5 /nobreak >nul
echo [INFO] Verification 2/6...
timeout /t 5 /nobreak >nul
echo [INFO] Verification 3/6...
timeout /t 5 /nobreak >nul
echo [INFO] Verification 4/6...
timeout /t 5 /nobreak >nul
echo [INFO] Verification 5/6...
timeout /t 5 /nobreak >nul
echo [INFO] Verification 6/6...
timeout /t 5 /nobreak >nul
echo.

REM Verifier l'etat des services
echo [STATUS] Etat des services:
echo ============================================
%DOCKER_COMPOSE% ps
echo ============================================
echo.

echo [SUCCESS] Systeme demarre avec succes !
echo.
echo ============================================
echo    ACCES A L'APPLICATION
echo ============================================
echo.
echo   Frontend:      http://localhost:5173
echo   API REST:      http://localhost:8000
echo   WebSocket:     ws://localhost:8765/ws
echo   Kafka Broker:  localhost:9093
echo.
echo ============================================
echo    COMMANDES UTILES
echo ============================================
echo.
echo   Voir les logs:        %DOCKER_COMPOSE% logs -f
echo   Logs API:             %DOCKER_COMPOSE% logs -f api-server
echo   Logs Producer:        %DOCKER_COMPOSE% logs -f producer
echo   Logs Spark:           %DOCKER_COMPOSE% logs -f spark
echo   Arreter le systeme:   stop.bat
echo   Redemarrer:           %DOCKER_COMPOSE% restart
echo.
echo ============================================
echo.
pause
