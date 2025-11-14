#!/bin/bash

# ============================================
# PROJET SPARK - CRYPTOLIVE
# ============================================
#
# Developpe par:
#   - BAKOUAN Ebenezer
#   - KONE Aiman
#   - PITROIPA Soraya
#
# ============================================

clear

echo "============================================"
echo "   INSTALLATION CRYPTOLIVE"
echo "============================================"
echo ""
echo "Developpe par:"
echo "  - BAKOUAN Ebenezer"
echo "  - KONE Aiman"
echo "  - PITROIPA Soraya"
echo ""
echo "============================================"
echo ""

# Variables
REPO_URL="https://github.com/Ebenezer-09/CryptoLive.git"
PROJECT_DIR="CryptoLive"

# Verifier Git
echo "[CHECK] Verification de Git..."
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git n'est pas installe."
    echo "[INFO] Installez Git depuis: https://git-scm.com/downloads"
    exit 1
fi
echo "[OK] Git detecte"
echo ""

# Cloner le repository
echo "[STEP 1/3] Clonage du repository depuis GitHub..."
echo "[INFO] URL: $REPO_URL"
echo ""

if [ -d "$PROJECT_DIR" ]; then
    echo "[WARNING] Le dossier $PROJECT_DIR existe deja."
    read -p "[INPUT] Voulez-vous le supprimer et re-cloner? (o/n): " response
    if [ "$response" = "o" ] || [ "$response" = "O" ]; then
        rm -rf "$PROJECT_DIR"
        echo "[INFO] Dossier supprime"
    else
        echo "[INFO] Utilisation du dossier existant"
    fi
fi

if [ ! -d "$PROJECT_DIR" ]; then
    git clone "$REPO_URL"
    if [ $? -ne 0 ]; then
        echo "[ERROR] Echec du clonage du repository"
        exit 1
    fi
fi
echo "[OK] Repository clone avec succes"
echo ""

# Entrer dans le dossier
echo "[STEP 2/3] Acces au dossier du projet..."
cd "$PROJECT_DIR" || {
    echo "[ERROR] Impossible d'acceder au dossier $PROJECT_DIR"
    exit 1
}
echo "[OK] Dossier: $(pwd)"
echo ""

# Demander le systeme d'exploitation
echo "[STEP 3/3] Selection du systeme d'exploitation..."
echo ""
echo "============================================"
echo "   CHOIX DU SYSTEME"
echo "============================================"
echo ""
echo "  1 - Windows"
echo "  2 - Linux / Mac"
echo ""
read -p "[INPUT] Tapez 1 pour Windows ou 2 pour Linux/Mac: " os_choice
echo ""

case $os_choice in
    1)
        echo "[INFO] Systeme selectionne: Windows"
        echo "[INFO] Preparation pour Windows..."
        echo ""
        if [ -f "start.bat" ]; then
            echo "[WARNING] Vous etes sur Linux/Mac mais avez choisi Windows."
            echo "[INFO] Pour executer sur Windows, copiez ce dossier sur Windows"
            echo "[INFO] et double-cliquez sur start.bat"
            echo ""
            echo "[INFO] Si vous voulez lancer maintenant sur Linux/Mac,"
            echo "[INFO] relancez ce script et choisissez l'option 2."
        else
            echo "[ERROR] Fichier start.bat introuvable"
            exit 1
        fi
        ;;
    2)
        echo "[INFO] Systeme selectionne: Linux / Mac"
        echo "[INFO] Lancement de start.sh..."
        echo ""
        if [ -f "start.sh" ]; then
            chmod +x start.sh
            ./start.sh
        else
            echo "[ERROR] Fichier start.sh introuvable"
            exit 1
        fi
        ;;
    *)
        echo "[ERROR] Choix invalide. Veuillez taper 1 ou 2."
        exit 1
        ;;
esac

echo ""
echo "============================================"
echo ""
