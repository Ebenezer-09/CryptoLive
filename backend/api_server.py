from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer
import json
import asyncio
from typing import List
from collections import deque
import threading

app = FastAPI(title="Binance Real-Time API")

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire des dernières données
latest_trades = deque(maxlen=100)
latest_aggregated = {}
latest_alerts = deque(maxlen=50)
latest_arbitrage = deque(maxlen=20)
websocket_connections: List[WebSocket] = []

# Thread pour consommer Kafka en arrière-plan
def consume_kafka_trades():
    """Consomme les trades bruts depuis Kafka"""
    consumer = KafkaConsumer(
        'binance-stream',
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        group_id='api-trades'
    )
    
    for message in consumer:
        try:
            data = message.value
            if 'data' in data:
                trade = {
                    'symbol': data['data'].get('s'),
                    'price': float(data['data'].get('p', 0)),
                    'quantity': float(data['data'].get('q', 0)),
                    'timestamp': data['data'].get('E')
                }
                latest_trades.append(trade)
                
                # Broadcast to WebSocket clients
                asyncio.run(broadcast_message({
                    'type': 'trade',
                    'data': trade
                }))
        except Exception as e:
            print(f"Error processing trade: {e}")

def consume_kafka_aggregated():
    """Consomme les données agrégées depuis Spark"""
    consumer = KafkaConsumer(
        'binance-agg',
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        group_id='api-agg'
    )
    
    for message in consumer:
        try:
            data = message.value
            symbol = data.get('symbol')
            latest_aggregated[symbol] = {
                'symbol': symbol,
                'avg_price': data.get('avg_price'),
                'min_price': data.get('min_price'),
                'max_price': data.get('max_price'),
                'trade_count': data.get('trade_count'),
                'volatility': data.get('volatility'),
                'trend': data.get('trend'),
                'window_start': data.get('window_start'),
                'window_end': data.get('window_end')
            }
            
            # Broadcast to WebSocket clients
            asyncio.run(broadcast_message({
                'type': 'aggregated',
                'data': latest_aggregated[symbol]
            }))
        except Exception as e:
            print(f"Error processing aggregated: {e}")

# Démarrage des threads Kafka
threading.Thread(target=consume_kafka_trades, daemon=True).start()
threading.Thread(target=consume_kafka_aggregated, daemon=True).start()

async def broadcast_message(message: dict):
    """Envoie un message à tous les clients WebSocket connectés"""
    if websocket_connections:
        disconnected = []
        for ws in websocket_connections:
            try:
                await ws.send_json(message)
            except:
                disconnected.append(ws)
        
        # Nettoyer les connexions fermées
        for ws in disconnected:
            if ws in websocket_connections:
                websocket_connections.remove(ws)

@app.get("/")
async def root():
    return {
        "message": "Binance Real-Time API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "trades": "/api/trades",
            "aggregated": "/api/aggregated",
            "symbols": "/api/symbols",
            "market_overview": "/api/market-overview",
            "websocket": "/ws"
        }
    }

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "trades_count": len(latest_trades),
        "aggregated_symbols": len(latest_aggregated),
        "websocket_clients": len(websocket_connections)
    }

@app.get("/api/trades")
async def get_trades(limit: int = 50, symbol: str = None):
    """Récupère les derniers trades"""
    trades = list(latest_trades)
    
    if symbol:
        trades = [t for t in trades if t['symbol'] == symbol]
    
    return {
        "success": True,
        "count": len(trades[-limit:]),
        "data": trades[-limit:]
    }

@app.get("/api/aggregated")
async def get_aggregated(symbol: str = None):
    """Récupère les données agrégées"""
    if symbol:
        data = latest_aggregated.get(symbol)
        if data:
            return {"success": True, "data": data}
        return {"success": False, "message": "Symbol not found"}
    
    return {
        "success": True,
        "count": len(latest_aggregated),
        "data": list(latest_aggregated.values())
    }

@app.get("/api/symbols")
async def get_symbols():
    """Liste des symboles disponibles"""
    symbols = list(latest_aggregated.keys())
    return {
        "success": True,
        "count": len(symbols),
        "symbols": symbols
    }

@app.get("/api/symbol/{symbol}")
async def get_symbol_details(symbol: str):
    """Détails d'un symbole spécifique"""
    agg_data = latest_aggregated.get(symbol)
    recent_trades = [t for t in latest_trades if t['symbol'] == symbol][-10:]
    
    if not agg_data and not recent_trades:
        return {"success": False, "message": "Symbol not found"}
    
    return {
        "success": True,
        "symbol": symbol,
        "aggregated": agg_data,
        "recent_trades": recent_trades
    }

@app.get("/api/market-overview")
async def market_overview():
    """Vue d'ensemble du marché"""
    overview = []
    
    for symbol, agg in latest_aggregated.items():
        recent_trades = [t for t in latest_trades if t['symbol'] == symbol]
        
        overview.append({
            'symbol': symbol,
            'current_price': agg.get('avg_price'),
            'change_24h': agg.get('trend'),
            'volume': agg.get('trade_count'),
            'volatility': agg.get('volatility'),
            'high_24h': agg.get('max_price'),
            'low_24h': agg.get('min_price'),
            'last_update': agg.get('window_end')
        })
    
    return {
        "success": True,
        "timestamp": asyncio.get_event_loop().time(),
        "markets": overview
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour streaming temps réel"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    print(f"✅ Client WebSocket connecté. Total: {len(websocket_connections)}")
    
    # Envoyer les données initiales
    try:
        await websocket.send_json({
            "type": "welcome",
            "message": "Connecté au flux temps réel Binance",
            "data": {
                "aggregated": list(latest_aggregated.values()),
                "recent_trades": list(latest_trades)[-20:]
            }
        })
        
        # Maintenir la connexion ouverte
        while True:
            try:
                # Ping pour garder la connexion active
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        print(f"❌ Client déconnecté. Restants: {len(websocket_connections)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage du serveur API sur http://localhost:8000")
    print("📡 WebSocket disponible sur ws://localhost:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)