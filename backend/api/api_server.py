import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Set, List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from kafka import KafkaConsumer
import threading
import uvicorn
from queue import Queue
from email_service import send_alert_email

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,  # INFO level - DEBUG était trop verbeux avec Kafka
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Compteur de messages pour logs périodiques
message_counter = {'trades': 0, 'agg': 0}

# ============================================
# MODELS
# ============================================
class Condition(BaseModel):
    symbol: str
    type: str
    threshold: str = ""

class Alert(BaseModel):
    name: str
    conditions: List[Condition]
    email: str

# ============================================
# CONFIGURATION
# ============================================
KAFKA_BOOTSTRAP_SERVERS = ['kafka:9092']
KAFKA_TOPIC_TRADES = 'binance-stream'
KAFKA_TOPIC_AGG = 'binance-agg'

# Stockage des alertes actives
active_alerts: Dict[str, dict] = {}

# ============================================
# FASTAPI APP
# ============================================
app = FastAPI(title="Binance Real-Time API", version="1.0.0")

# CORS pour permettre les connexions depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# SERVIR LE FRONTEND STATIQUE (Production)
# ============================================
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    # Servir les fichiers statiques (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        """Servir le frontend React en production"""
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not available - use dev mode"}
    
    logger.info("✅ Frontend statique configuré")
else:
    logger.warning("⚠️  Dossier static/ non trouvé - mode dev uniquement")

# ============================================
# GESTIONNAIRE WEBSOCKET
# ============================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.latest_data = {}
        self.message_queue = Queue()  # File d'attente pour les messages
        # Stocker les données par symbole pour les alertes
        self.symbol_data = {
            'BTCUSDT': {'price': 0, 'volume': 0, 'volatility': 0, 'rsi': 0, 'macd': 0, 'bollinger_upper': 0, 'bollinger_lower': 0},
            'ETHUSDT': {'price': 0, 'volume': 0, 'volatility': 0, 'rsi': 0, 'macd': 0, 'bollinger_upper': 0, 'bollinger_lower': 0}
        }
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connecté. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Client déconnecté. Total: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        """Envoyer un message à tous les clients connectés"""
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in list(self.active_connections):  # Créer une copie de la liste
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Erreur envoi message: {e}")
                disconnected.append(connection)
        
        # Nettoyer les connexions mortes
        for conn in disconnected:
            self.disconnect(conn)
    
    def update_latest_data(self, data_type: str, data: dict):
        """Mettre à jour les dernières données"""
        self.latest_data[data_type] = data
        
        # Mettre à jour les données par symbole pour les alertes
        if data_type == 'trades' and 'symbol' in data:
            symbol = data['symbol']
            if symbol in self.symbol_data:
                self.symbol_data[symbol]['price'] = data.get('price', 0)
                logger.debug(f"Prix {symbol} mis à jour: {data.get('price', 0)}")
        
        elif data_type == 'aggregated' and 'symbol' in data:
            symbol = data['symbol']
            if symbol in self.symbol_data:
                self.symbol_data[symbol].update({
                    'volume': data.get('trade_count', 0),
                    'volatility': data.get('volatility', 0)
                })
        
        # Ajouter à la queue pour broadcast asynchrone
        self.message_queue.put(data)

manager = ConnectionManager()

# ============================================
# CONSOMMATEUR KAFKA EN ARRIÈRE-PLAN
# ============================================
def kafka_consumer_thread():
    """Thread pour consommer les messages Kafka et les broadcaster"""
    logger.info("Démarrage du consommateur Kafka...")
    
    # Attendre que Kafka soit prêt
    import time
    time.sleep(10)
    
    try:
        consumer_trades = KafkaConsumer(
            KAFKA_TOPIC_TRADES,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='api-websocket-group'
            # ❌ PAS de consumer_timeout_ms ! Ça empêche la réception
        )
        
        consumer_agg = KafkaConsumer(
            KAFKA_TOPIC_AGG,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='api-websocket-agg-group'
            # ❌ PAS de consumer_timeout_ms ! Ça empêche la réception
        )
        
        logger.info("✅ Consommateurs Kafka connectés")
        
        # Consommer les messages - boucle simple qui fonctionne !
        while True:
            # Consumer trades
            for message in consumer_trades:
                try:
                    data = message.value
                    if 'data' in data:
                        symbol = data['data']['s']
                        price = float(data['data']['p'])
                        
                        # Messages aggTrade ont 'q', markPrice n'ont pas 'q'
                        quantity = float(data['data'].get('q', 0))
                        
                        trade_data = {
                            'type': 'price',
                            'symbol': symbol,
                            'price': price,
                            'quantity': quantity,
                            'timestamp': data['data']['E']
                        }
                        
                        # Stocker par symbole pour les alertes
                        if symbol not in manager.symbol_data:
                            manager.symbol_data[symbol] = {}
                        
                        manager.symbol_data[symbol]['price'] = trade_data['price']
                        manager.symbol_data[symbol]['timestamp'] = trade_data['timestamp']
                        
                        # Broadcaster aux clients
                        manager.update_latest_data('trades', trade_data)
                        
                        # Vérifier alertes toutes les 10 messages
                        message_counter['trades'] += 1
                        if message_counter['trades'] % 10 == 0:
                            check_alerts()
                        
                        # Log tous les 100 messages
                        if message_counter['trades'] % 100 == 0:
                            logger.info(f"📊 {message_counter['trades']} messages traités - Dernier: {symbol} = ${trade_data['price']}")
                        
                except Exception as e:
                    logger.error(f"Erreur traitement trade: {e}")
            
            # Consumer aggregated data
            for message in consumer_agg:
                try:
                    data = message.value
                    symbol = data.get('symbol')
                    agg_data = {
                        'type': 'aggregated',
                        'symbol': symbol,
                        'avg_price': data.get('avg_price'),
                        'min_price': data.get('min_price'),
                        'max_price': data.get('max_price'),
                        'count': data.get('count')
                    }
                    
                    # Stocker pour les alertes
                    if symbol in manager.symbol_data:
                        manager.symbol_data[symbol].update({
                            'avg_price': agg_data['avg_price'],
                            'min_price': agg_data['min_price'],
                            'max_price': agg_data['max_price']
                        })
                    
                    manager.update_latest_data('aggregated', agg_data)
                    
                    logger.debug(f"📈 Agg {symbol}: avg=${agg_data['avg_price']}")
                    
                except Exception as e:
                    logger.error(f"Erreur traitement agg: {e}")
                    
    except Exception as e:
        logger.error(f"Erreur consommateur Kafka: {e}")

# Démarrer le thread Kafka dans un event loop séparé
import asyncio
from concurrent.futures import ThreadPoolExecutor

# ============================================
# GESTIONNAIRE ASYNC POUR KAFKA
# ============================================
async def start_kafka_consumer():
    """Démarrer le consommateur Kafka de manière asynchrone"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, kafka_consumer_thread)

# ============================================
# LIFECYCLE EVENTS
# ============================================
async def broadcast_worker():
    """Tâche asynchrone pour broadcaster les messages depuis la queue"""
    logger.info("📡 Démarrage du worker de broadcast...")
    while True:
        try:
            if not manager.message_queue.empty():
                message = manager.message_queue.get()
                await manager.broadcast(message)
                
                # Vérifier les alertes après chaque broadcast
                check_alerts()
                
            await asyncio.sleep(0.01)  # Petite pause pour ne pas surcharger
        except Exception as e:
            logger.error(f"Erreur broadcast worker: {e}")

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application"""
    logger.info("🚀 Démarrage de l'application FastAPI...")
    
    # Démarrer le worker de broadcast
    asyncio.create_task(broadcast_worker())
    
    # Démarrer le consommateur Kafka en arrière-plan après un délai
    async def delayed_start():
        await asyncio.sleep(2)  # Attendre que le serveur soit prêt
        logger.info("Démarrage du consommateur Kafka...")
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, kafka_consumer_thread)
    
    asyncio.create_task(delayed_start())

@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt de l'application"""
    logger.info("🛑 Arrêt de l'application FastAPI...")

# ============================================
# ENDPOINTS WEBSOCKET
# ============================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Envoyer les dernières données au nouveau client
        if manager.latest_data:
            for data in manager.latest_data.values():
                await websocket.send_json(data)
        
        # Garder la connexion ouverte
        while True:
            # Recevoir les messages du client (ping/pong)
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
    finally:
        manager.disconnect(websocket)

# ============================================
# ENDPOINTS REST
# ============================================
@app.get("/")
async def root():
    return {
        "message": "Binance Real-Time API",
        "status": "running",
        "websocket": "ws://localhost:8000/ws",
        "active_connections": len(manager.active_connections)
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "kafka_connected": True,
        "active_connections": len(manager.active_connections),
        "latest_data_types": list(manager.latest_data.keys()),
        "active_alerts": len(active_alerts)
    }

@app.get("/api/latest")
async def get_latest():
    """Récupérer les dernières données disponibles"""
    return manager.latest_data

# ============================================
# ENDPOINTS ALERTES
# ============================================
@app.post("/api/alerts")
async def create_alert(alert: Alert):
    """
    Créer une nouvelle alerte avec conditions multiples
    """
    try:
        alert_id = f"{alert.name}_{len(active_alerts)}"
        
        active_alerts[alert_id] = {
            "id": alert_id,
            "name": alert.name,
            "conditions": [c.dict() for c in alert.conditions],
            "email": alert.email,
            "status": "active",
            "triggered": False
        }
        
        logger.info(f"✅ Alerte créée: {alert.name} ({len(alert.conditions)} conditions)")
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Alerte '{alert.name}' créée avec succès"
        }
    except Exception as e:
        logger.error(f"❌ Erreur création alerte: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts():
    """
    Récupérer toutes les alertes actives
    """
    return {"alerts": list(active_alerts.values())}

@app.delete("/api/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """
    Supprimer une alerte
    """
    if alert_id in active_alerts:
        del active_alerts[alert_id]
        logger.info(f"🗑️ Alerte supprimée: {alert_id}")
        return {"success": True, "message": "Alerte supprimée"}
    else:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")

# ============================================
# VÉRIFICATION DES ALERTES
# ============================================
def check_alert_condition(condition: dict, symbol_data: dict) -> bool:
    """
    Vérifie si une condition d'alerte est remplie
    """
    try:
        symbol = condition['symbol']
        cond_type = condition['type']
        threshold = float(condition.get('threshold', 0)) if condition.get('threshold') else 0
        
        # Récupérer les données du symbole depuis manager.symbol_data
        data = symbol_data.get(symbol, {})
        if not data:
            logger.debug(f"Pas de données pour {symbol}")
            return False
        
        # Log pour debug
        logger.debug(f"Vérification condition: {symbol} {cond_type} {threshold} - Prix actuel: {data.get('price', 0)}")
        
        # Vérifier selon le type de condition
        if cond_type == 'price_above':
            result = data.get('price', 0) > threshold
            if result:
                logger.info(f"✓ Condition remplie: {symbol} prix {data.get('price')} > {threshold}")
            return result
        
        elif cond_type == 'price_below':
            result = data.get('price', 0) < threshold
            if result:
                logger.info(f"✓ Condition remplie: {symbol} prix {data.get('price')} < {threshold}")
            return result
        
        elif cond_type == 'volatility_above':
            result = data.get('volatility', 0) > threshold
            if result:
                logger.info(f"✓ Condition remplie: {symbol} volatilité {data.get('volatility')}% > {threshold}%")
            return result
        
        elif cond_type == 'volume_above':
            result = data.get('volume', 0) > threshold
            if result:
                logger.info(f"✓ Condition remplie: {symbol} volume {data.get('volume')} > {threshold}")
            return result
        
        elif cond_type == 'rsi_above':
            result = data.get('rsi', 0) > threshold
            if result:
                logger.info(f"✓ Condition remplie: {symbol} RSI {data.get('rsi')} > {threshold}")
            return result
        
        elif cond_type == 'rsi_below':
            result = data.get('rsi', 0) < threshold
            if result:
                logger.info(f"✓ Condition remplie: {symbol} RSI {data.get('rsi')} < {threshold}")
            return result
        
        elif cond_type == 'macd_positive':
            result = data.get('macd', 0) > 0
            if result:
                logger.info(f"✓ Condition remplie: {symbol} MACD {data.get('macd')} > 0")
            return result
        
        elif cond_type == 'macd_negative':
            result = data.get('macd', 0) < 0
            if result:
                logger.info(f"✓ Condition remplie: {symbol} MACD {data.get('macd')} < 0")
            return result
        
        elif cond_type == 'bollinger_upper':
            price = data.get('price', 0)
            bb_upper = data.get('bollinger_upper', 0)
            result = price >= bb_upper * 0.99  # 99% de la bande supérieure
            if result:
                logger.info(f"✓ Condition remplie: {symbol} prix {price} >= Bollinger sup {bb_upper}")
            return result
        
        elif cond_type == 'bollinger_lower':
            price = data.get('price', 0)
            bb_lower = data.get('bollinger_lower', 0)
            result = price <= bb_lower * 1.01  # 101% de la bande inférieure
            if result:
                logger.info(f"✓ Condition remplie: {symbol} prix {price} <= Bollinger inf {bb_lower}")
            return result
        
        return False
        
    except Exception as e:
        logger.error(f"Erreur vérification condition: {e}")
        return False

def check_alerts():
    """
    Vérifie toutes les alertes actives
    """
    logger.info(f"🔍 Vérification alertes... ({len(active_alerts)} actives, symbol_data: {list(manager.symbol_data.keys())})")
    
    if not active_alerts:
        logger.info("⚠️ Aucune alerte active à vérifier")
        return
        
    for alert_id, alert_data in list(active_alerts.items()):
        if alert_data['triggered']:
            continue  # Ignorer les alertes déjà déclenchées
        
        conditions = alert_data['conditions']
        
        # Vérifier que TOUTES les conditions sont remplies (AND logic)
        all_conditions_met = all(
            check_alert_condition(cond, manager.symbol_data)
            for cond in conditions
        )
        
        if all_conditions_met:
            logger.info(f"🚨 ALERTE DÉCLENCHÉE: {alert_data['name']}")
            
            # Marquer comme déclenchée
            alert_data['triggered'] = True
            alert_data['status'] = 'triggered'
            
            # Envoyer l'email
            email_sent = send_alert_email(
                to_email=alert_data['email'],
                alert_name=alert_data['name'],
                conditions=conditions,
                symbol=conditions[0]['symbol'] if conditions else 'N/A'
            )
            
            if email_sent:
                logger.info(f"✅ Email envoyé à {alert_data['email']}")
            else:
                logger.error(f"❌ Échec envoi email à {alert_data['email']}")
            
            # Notifier le frontend via WebSocket
            manager.message_queue.put({
                'type': 'alert_triggered',
                'alert_id': alert_id,
                'alert_name': alert_data['name'],
                'status': 'triggered'
            })


@app.get("/api/latest")
async def get_latest():
    """Récupérer les dernières données disponibles"""
    return manager.latest_data

# ============================================
# DÉMARRAGE DU SERVEUR
# ============================================
if __name__ == "__main__":
    logger.info("🚀 Démarrage du serveur API...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,  # Port principal pour API REST + WebSocket
        log_level="info"
    )
