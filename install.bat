@echo off
chcp 65001 >nul
cls

REM ============================================
REM PROJET SPARK - CRYPTOLIVE
REM ============================================
REM
REM Developpe par:
REM   - BAKOUAN Ebenezer
REM   - KONE Aiman
REM   - PITROIPA Soraya
REM
REM ============================================

echo ============================================
echo    INSTALLATION CRYPTOLIVE
echo ============================================
echo.
echo Developpe par:
echo   - BAKOUAN Ebenezer
echo   - KONE Aiman
echo   - PITROIPA Soraya
echo.
echo ============================================
echo.

REM Variables
set "REPO_URL=https://github.com/Ebenezer-09/CryptoLive.git"
set "PROJECT_DIR=CryptoLive"

REM Verifier Git
echo [CHECK] Verification de Git...
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git n'est pas installe.
    echo [INFO] Installez Git depuis: https://git-scm.com/downloads
    pause
    exit /b 1
)
echo [OK] Git detecte
echo.

REM Cloner le repository
echo [STEP 1/3] Clonage du repository depuis GitHub...
echo [INFO] URL: %REPO_URL%
echo.

setlocal enabledelayedexpansion
if exist "%PROJECT_DIR%" (
    echo [WARNING] Le dossier %PROJECT_DIR% existe deja.
    set /p "response=[INPUT] Voulez-vous le supprimer et re-cloner? (o/n): "
    if /i "!response!"=="o" (
        rmdir /s /q "%PROJECT_DIR%"
        echo [INFO] Dossier supprime
    ) else (
        echo [INFO] Utilisation du dossier existant
    )
)

if not exist "%PROJECT_DIR%" (
    git clone "%REPO_URL%"
    if %errorlevel% neq 0 (
        echo [ERROR] Echec du clonage du repository
        pause
        exit /b 1
    )
)
echo [OK] Repository clone avec succes
echo.

REM Entrer dans le dossier
echo [STEP 2/3] Acces au dossier du projet...
cd "%PROJECT_DIR%" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Impossible d'acceder au dossier %PROJECT_DIR%
    pause
    exit /b 1
)
echo [OK] Dossier: %cd%
echo.

REM Demander le systeme d'exploitation
echo [STEP 3/3] Selection du systeme d'exploitation...
echo.
echo ============================================
echo    CHOIX DU SYSTEME
echo ============================================
echo.
echo   1 - Windows
echo   2 - Linux / Mac
echo.
set /p "os_choice=[INPUT] Tapez 1 pour Windows ou 2 pour Linux/Mac: "
echo.

if "%os_choice%"=="1" (
    echo [INFO] Systeme selectionne: Windows
    echo [INFO] Lancement de start.bat...
    echo.
    if exist "start.bat" (
        call start.bat
    ) else (
        echo [ERROR] Fichier start.bat introuvable
        pause
        exit /b 1
    )
) else if "%os_choice%"=="2" (
    echo [INFO] Systeme selectionne: Linux / Mac
    echo [INFO] Preparation pour Linux/Mac...
    echo.
    if exist "start.sh" (
        echo [WARNING] Vous etes sur Windows mais avez choisi Linux/Mac.
        echo [INFO] Pour executer sur Linux/Mac, copiez ce dossier sur Linux/Mac
        echo [INFO] et executez: ./install.sh
        echo.
        echo [INFO] Si vous voulez lancer maintenant sur Windows,
        echo [INFO] relancez ce script et choisissez l'option 1.
        pause
    ) else (
        echo [ERROR] Fichier start.sh introuvable
        pause
        exit /b 1
    )
) else (
    echo [ERROR] Choix invalide. Veuillez taper 1 ou 2.
    pause
    exit /b 1
)

echo.
echo ============================================
echo.
endlocal
