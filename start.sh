#!/bin/bash

# ============================================
# Script de démarrage du projet Binance Real-Time
# ============================================

echo "============================================"
echo "   BINANCE REAL-TIME STREAMING SYSTEM"
echo "============================================"
echo ""
echo "[INFO] Demarrage du systeme..."
echo ""

# Vérifier que Docker est installé
echo "[CHECK] Verification de Docker..."
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker n'est pas installe."
    echo "[INFO] Installez Docker depuis: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "[OK] Docker detecte"

# Vérifier Docker Compose (V2 ou V1)
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
    echo "[INFO] Installez Docker Compose depuis: https://docs.docker.com/compose/install/"
    exit 1
fi
echo ""

# Créer les répertoires nécessaires
echo "[STEP 1/5] Creation des repertoires de donnees..."
mkdir -p backend/spark_processor/checkpoints
mkdir -p backend/spark_processor/data
chmod -R 777 backend/spark_processor/checkpoints 2>/dev/null || true
chmod -R 777 backend/spark_processor/data 2>/dev/null || true
echo "[OK] Repertoires crees"
echo ""

# Nettoyer les anciens conteneurs
echo "[STEP 2/5] Nettoyage des anciennes instances..."
$DOCKER_COMPOSE down -v 2>/dev/null
echo "[OK] Nettoyage termine"
echo ""

# Supprimer les conteneurs orphelins
echo "[STEP 3/5] Suppression des conteneurs orphelins..."
docker container prune -f > /dev/null 2>&1
docker volume prune -f > /dev/null 2>&1
echo "[OK] Conteneurs orphelins supprimes"
echo ""

# Construire les images
echo "[STEP 4/5] Construction des images Docker..."
echo "[INFO] Cette operation peut prendre plusieurs minutes..."
$DOCKER_COMPOSE build
if [ $? -eq 0 ]; then
    echo "[OK] Images construites avec succes"
else
    echo "[ERROR] Erreur lors de la construction des images"
    exit 1
fi
echo ""

# Démarrer les services
echo "[STEP 5/5] Demarrage des services..."
$DOCKER_COMPOSE up -d
if [ $? -eq 0 ]; then
    echo "[OK] Services demarres"
else
    echo "[ERROR] Erreur lors du demarrage des services"
    exit 1
fi
echo ""

echo "[INFO] Attente du demarrage complet des services..."
echo "[INFO] Verification de l'etat des services toutes les 5 secondes..."
for i in {1..6}; do
    echo "[INFO] Verification $i/6..."
    sleep 5
done
echo ""

# Vérifier l'état des services
echo "[STATUS] Etat des services:"
echo "============================================"
$DOCKER_COMPOSE ps
echo "============================================"
echo ""

echo "[SUCCESS] Systeme demarre avec succes !"
echo ""
echo "============================================"
echo "   ACCES A L'APPLICATION"
echo "============================================"
echo ""
echo "  Frontend:      http://localhost:5173"
echo "  API REST:      http://localhost:8000"
echo "  WebSocket:     ws://localhost:8765/ws"
echo "  Kafka Broker:  localhost:9093"
echo ""
echo "============================================"
echo "   COMMANDES UTILES"
echo "============================================"
echo ""
echo "  Voir les logs:        $DOCKER_COMPOSE logs -f"
echo "  Logs API:             $DOCKER_COMPOSE logs -f api-server"
echo "  Logs Producer:        $DOCKER_COMPOSE logs -f producer"
echo "  Logs Spark:           $DOCKER_COMPOSE logs -f spark"
echo "  Arreter le systeme:   ./stop.sh"
echo "  Redemarrer:           $DOCKER_COMPOSE restart"
echo ""
echo "============================================"
echo ""
