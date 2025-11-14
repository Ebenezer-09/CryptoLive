from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer
import json
import asyncio
from typing import List
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Binance Real-Time API", version="1.0.0")

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire des dernières données
latest_data = {
    "raw_trades": [],
    "aggregated_data": [],
    "alerts": [],
    "arbitrage": []
}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connecté. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client déconnecté. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

def consume_kafka_raw():
    """Consomme les données brutes de Kafka"""
    try:
        consumer = KafkaConsumer(
            'binance-stream',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='api-raw-consumer'
        )
        
        for message in consumer:
            data = message.value
            if 'data' in data:
                trade = {
                    'symbol': data['data'].get('s'),
                    'price': float(data['data'].get('p', 0)),
                    'quantity': float(data['data'].get('q', 0)),
                    'timestamp': datetime.now().isoformat()
                }
                
                latest_data['raw_trades'].append(trade)
                if len(latest_data['raw_trades']) > 100:
                    latest_data['raw_trades'].pop(0)
                
                # Broadcast via WebSocket
                asyncio.run(manager.broadcast({
                    'type': 'trade',
                    'data': trade
                }))
    except Exception as e:
        logger.error(f"Erreur consumer raw: {e}")

def consume_kafka_aggregated():
    """Consomme les données agrégées de Kafka"""
    try:
        consumer = KafkaConsumer(
            'binance-agg',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='api-agg-consumer'
        )
        
        for message in consumer:
            data = message.value
            agg_data = {
                'symbol': data.get('symbol'),
                'avg_price': float(data.get('avg_price', 0)),
                'min_price': float(data.get('min_price', 0)),
                'max_price': float(data.get('max_price', 0)),
                'trade_count': int(data.get('trade_count', 0)),
                'volatility': float(data.get('volatility', 0)),
                'trend': float(data.get('trend', 0)),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update ou ajoute dans latest_data
            existing = next((x for x in latest_data['aggregated_data'] 
                           if x['symbol'] == agg_data['symbol']), None)
            if existing:
                latest_data['aggregated_data'].remove(existing)
            latest_data['aggregated_data'].append(agg_data)
            
            # Broadcast via WebSocket
            asyncio.run(manager.broadcast({
                'type': 'aggregated',
                'data': agg_data
            }))
    except Exception as e:
        logger.error(f"Erreur consumer aggregated: {e}")

# Démarrage des consumers Kafka en arrière-plan
import threading
threading.Thread(target=consume_kafka_raw, daemon=True).start()
threading.Thread(target=consume_kafka_aggregated, daemon=True).start()

# ==================== REST API ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "Binance Real-Time Trading API",
        "version": "1.0.0",
        "endpoints": {
            "trades": "/api/trades",
            "aggregated": "/api/aggregated",
            "symbols": "/api/symbols",
            "websocket": "/ws"
        }
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "consumers": {
            "raw_trades": len(latest_data['raw_trades']),
            "aggregated": len(latest_data['aggregated_data'])
        },
        "websocket_clients": len(manager.active_connections)
    }

@app.get("/api/trades")
async def get_trades(limit: int = 50, symbol: str = None):
    """Récupère les derniers trades"""
    trades = latest_data['raw_trades'][-limit:]
    
    if symbol:
        trades = [t for t in trades if t['symbol'] == symbol]
    
    return {
        "count": len(trades),
        "data": trades
    }

@app.get("/api/aggregated")
async def get_aggregated(symbol: str = None):
    """Récupère les données agrégées"""
    data = latest_data['aggregated_data']
    
    if symbol:
        data = [d for d in data if d['symbol'] == symbol]
    
    return {
        "count": len(data),
        "data": data
    }

@app.get("/api/symbols")
async def get_symbols():
    """Liste tous les symboles disponibles"""
    symbols = list(set([d['symbol'] for d in latest_data['aggregated_data']]))
    return {
        "count": len(symbols),
        "symbols": symbols
    }

@app.get("/api/symbol/{symbol}")
async def get_symbol_details(symbol: str):
    """Détails complets d'un symbole"""
    agg = next((d for d in latest_data['aggregated_data'] if d['symbol'] == symbol), None)
    recent_trades = [t for t in latest_data['raw_trades'][-50:] if t['symbol'] == symbol]
    
    if not agg:
        return {"error": "Symbol not found"}
    
    return {
        "symbol": symbol,
        "aggregated": agg,
        "recent_trades": recent_trades,
        "stats": {
            "trades_count": len(recent_trades),
            "avg_price": sum([t['price'] for t in recent_trades]) / len(recent_trades) if recent_trades else 0,
            "total_volume": sum([t['quantity'] for t in recent_trades])
        }
    }

@app.get("/api/market-overview")
async def market_overview():
    """Vue d'ensemble du marché"""
    overview = []
    
    for agg in latest_data['aggregated_data']:
        symbol = agg['symbol']
        recent = [t for t in latest_data['raw_trades'][-100:] if t['symbol'] == symbol]
        
        overview.append({
            'symbol': symbol,
            'current_price': agg['avg_price'],
            'change_24h': agg['trend'],
            'volatility': agg['volatility'],
            'volume': len(recent),
            'high': agg['max_price'],
            'low': agg['min_price']
        })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "markets": overview
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour streaming temps réel"""
    await manager.connect(websocket)
    
    try:
        # Envoie les données initiales
        await websocket.send_json({
            'type': 'connected',
            'message': 'WebSocket connecté',
            'data': {
                'trades': latest_data['raw_trades'][-10:],
                'aggregated': latest_data['aggregated_data']
            }
        })
        
        # Maintient la connexion ouverte
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
