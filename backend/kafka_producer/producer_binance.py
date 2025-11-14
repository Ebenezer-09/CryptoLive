import json, websocket, time, socket
from kafka import KafkaProducer

# Configuration
BINANCE_WS_URL = "wss://fstream.binance.com/stream?streams=btcusdt@aggTrade/ethusdt@aggTrade/btcusdt@markPrice/ethusdt@markPrice"
KAFKA_TOPIC = 'binance-stream'

# Fonction pour tester la connectivité réseau
def test_kafka_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('kafka', 9092))
        sock.close()
        return result == 0
    except:
        return False

# Attendre que Kafka soit prêt avec retry
def create_producer():
    while True:
        if test_kafka_connection():
            try:
                producer = KafkaProducer(
                    bootstrap_servers=['kafka:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    api_version=(2, 8, 0),
                    api_version_auto_timeout_ms=0
                )
                print("✅ Connecté à Kafka avec succès")
                return producer
            except Exception as e:
                print(f"❌ Échec création producer: {e}. Retry dans 5s...")
                time.sleep(5)
        else:
            print("⏳ Kafka non accessible. Retry dans 5s...")
            time.sleep(5)

# Créer le producer seulement quand on en a besoin
producer = None
message_count = 0

def on_message(ws, message):
    global producer, message_count
    if producer is None:
        producer = create_producer()
    
    try:
        data = json.loads(message)
        
        # Les données arrivent encapsulées : {"stream":"<streamName>","data":<rawPayload>}
        if 'stream' in data and 'data' in data:
            message_count += 1
            stream_name = data['stream']
            payload = data['data']
            
            # Identifier le type de flux
            if 'aggTrade' in stream_name:
                # Flux aggTrade : transactions agrégées
                symbol = payload.get('s', 'UNKNOWN')
                price = payload.get('p', '0')
                quantity = payload.get('q', '0')
                print(f"📊 [{message_count}] AggTrade {symbol}: Prix={price}, Qty={quantity}")
            elif 'markPrice' in stream_name:
                # Flux markPrice : prix de référence et taux de financement
                symbol = payload.get('s', 'UNKNOWN')
                mark_price = payload.get('p', '0')
                funding_rate = payload.get('r', '0')
                print(f"💰 [{message_count}] MarkPrice {symbol}: Mark={mark_price}, Funding={funding_rate}")
            
            # Envoyer à Kafka
            producer.send(KAFKA_TOPIC, data)
            
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
    except Exception as e:
        print(f"❌ Erreur traitement message: {e}")

def on_open(ws):
    print("🔌 WebSocket Binance Futures OUVERT")
    print(f"📡 Streams: btcusdt@aggTrade, ethusdt@aggTrade, btcusdt@markPrice, ethusdt@markPrice")

def on_error(ws, error):
    print(f"❌ Erreur WebSocket: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"🔒 WebSocket FERMÉ: {close_status_code}, {close_msg}")

def on_ping(ws, data):
    print("🏓 Ping reçu de Binance")

def on_pong(ws, data):
    print("🏓 Pong reçu de Binance")

if __name__ == "__main__":
    print("🚀 Démarrage Producer Binance Futures...")
    print(f"📍 URL: {BINANCE_WS_URL}")
    print(f"📤 Topic Kafka: {KAFKA_TOPIC}")
    print("-" * 60)
    
    while True:
        try:
            ws = websocket.WebSocketApp(
                BINANCE_WS_URL,
                on_message=on_message,
                on_open=on_open,
                on_error=on_error,
                on_close=on_close,
                on_ping=on_ping,
                on_pong=on_pong
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"❌ Erreur fatale: {e}")
            print("⏳ Reconnexion dans 5 secondes...")
            time.sleep(5)
