import json
import asyncio
import websockets
from kafka import KafkaProducer
from datetime import datetime

class MultiExchangeProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Configuration des exchanges
        self.exchanges = {
            'binance': {
                'url': 'wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade',
                'parser': self.parse_binance
            },
            'coinbase': {
                'url': 'wss://ws-feed.pro.coinbase.com',
                'parser': self.parse_coinbase
            },
            'kraken': {
                'url': 'wss://ws.kraken.com',
                'parser': self.parse_kraken
            }
        }
    
    def parse_binance(self, message):
        """Parse les données Binance"""
        data = json.loads(message)
        if 'data' in data:
            trade_data = data['data']
            return {
                'exchange': 'binance',
                'symbol': trade_data.get('s', '').lower(),
                'price': float(trade_data.get('p', 0)),
                'volume': float(trade_data.get('q', 0)),
                'timestamp': datetime.now().isoformat(),
                'trade_id': trade_data.get('t')
            }
        return None
    
    def parse_coinbase(self, message):
        """Parse les données Coinbase Pro"""
        data = json.loads(message)
        if data.get('type') == 'match':
            return {
                'exchange': 'coinbase',
                'symbol': data.get('product_id', '').lower().replace('-', ''),
                'price': float(data.get('price', 0)),
                'volume': float(data.get('size', 0)),
                'timestamp': data.get('time', datetime.now().isoformat()),
                'trade_id': data.get('trade_id')
            }
        return None
    
    def parse_kraken(self, message):
        """Parse les données Kraken"""
        data = json.loads(message)
        if isinstance(data, list) and len(data) > 1:
            trades = data[1]
            pair = data[-1] if len(data) > 2 else 'unknown'
            
            if isinstance(trades, list) and len(trades) > 0:
                trade = trades[0]
                return {
                    'exchange': 'kraken',
                    'symbol': pair.lower(),
                    'price': float(trade[0]),
                    'volume': float(trade[1]),
                    'timestamp': datetime.now().isoformat(),
                    'trade_id': None
                }
        return None
    
    async def connect_exchange(self, exchange_name, config):
        """Connecte à un exchange spécifique"""
        try:
            async with websockets.connect(config['url']) as websocket:
                print(f"✅ Connecté à {exchange_name}")
                
                # Configuration spécifique pour chaque exchange
                if exchange_name == 'coinbase':
                    subscribe_msg = {
                        "type": "subscribe",
                        "channels": [{"name": "matches", "product_ids": ["BTC-USD", "ETH-USD"]}]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                elif exchange_name == 'kraken':
                    subscribe_msg = {
                        "event": "subscribe",
                        "pair": ["XBT/USD", "ETH/USD"],
                        "subscription": {"name": "trade"}
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                
                # Écoute des messages
                async for message in websocket:
                    parsed_data = config['parser'](message)
                    if parsed_data:
                        # Envoie vers Kafka avec topic spécifique
                        self.producer.send(f'exchange-{exchange_name}', parsed_data)
                        self.producer.send('all-exchanges', parsed_data)  # Topic unifié
                        
        except Exception as e:
            print(f"❌ Erreur {exchange_name}: {e}")
            # Reconnexion automatique après 5 secondes
            await asyncio.sleep(5)
            await self.connect_exchange(exchange_name, config)
    
    async def start_all_exchanges(self):
        """Lance la connexion à tous les exchanges en parallèle"""
        tasks = []
        for exchange_name, config in self.exchanges.items():
            task = asyncio.create_task(self.connect_exchange(exchange_name, config))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

# Script principal pour lancer le producer multi-exchange
if __name__ == "__main__":
    producer = MultiExchangeProducer()
    asyncio.run(producer.start_all_exchanges())