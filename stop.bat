@echo off
chcp 65001 >nul
cls

REM ============================================
REM Script d'arret du projet Binance Real-Time
REM ============================================

echo ============================================
echo    ARRET DU SYSTEME
echo ============================================
echo.

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
        pause
        exit /b 1
    )
)
echo.

echo [INFO] Arret de tous les services...
%DOCKER_COMPOSE% down -v

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Tous les services sont arretes
    echo [INFO] Les volumes ont ete supprimes
) else (
    echo.
    echo [ERROR] Erreur lors de l'arret des services
    pause
    exit /b 1
)

echo.
echo ============================================
echo.
pause
