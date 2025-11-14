#!/bin/bash

# ============================================
# Script d'arret du projet Binance Real-Time
# ============================================

echo "============================================"
echo "   ARRET DU SYSTEME"
echo "============================================"
echo ""

# Détecter Docker Compose (V2 ou V1)
echo "[CHECK] Detection de Docker Compose..."
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
    COMPOSE_VERSION="v2"
    echo "[OK] Docker Compose v2 detecte"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    COMPOSE_VERSION="v1"
    echo "[OK] Docker Compose v1 detecte"
else
    echo "[ERROR] Docker Compose n'est pas installe."
    exit 1
fi
echo ""

echo "[INFO] Arret de tous les services..."
$DOCKER_COMPOSE down -v

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Tous les services sont arretes"
    echo "[INFO] Les volumes ont ete supprimes"
else
    echo ""
    echo "[ERROR] Erreur lors de l'arret des services"
    exit 1
fi

echo ""
echo "============================================"
echo ""
