import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_RAW = os.getenv('KAFKA_TOPIC_RAW', 'binance-stream')
    KAFKA_TOPIC_AGG = os.getenv('KAFKA_TOPIC_AGG', 'binance-agg')
    KAFKA_TOPIC_ALERTS = os.getenv('KAFKA_TOPIC_ALERTS', 'binance-alerts')
    KAFKA_TOPIC_ARBITRAGE = os.getenv('KAFKA_TOPIC_ARBITRAGE', 'arbitrage-opportunities')
    
    # API
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    API_WORKERS = int(os.getenv('API_WORKERS', 4))
    
    # Frontend
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    # Binance
    BINANCE_WS_URL = os.getenv('BINANCE_WS_URL', 'wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade')
    
    # Data
    MAX_TRADES_MEMORY = int(os.getenv('MAX_TRADES_MEMORY', 1000))
    MAX_AGG_MEMORY = int(os.getenv('MAX_AGG_MEMORY', 50))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

config = Config()