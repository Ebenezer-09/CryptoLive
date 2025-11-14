#!/usr/bin/env python3
"""Test simple du consumer Kafka"""

from kafka import KafkaConsumer
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Attendre Kafka
import time
time.sleep(5)

consumer = KafkaConsumer(
    'binance-stream',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',
    enable_auto_commit=True,
    group_id='test-group'
)

logger.info("✅ Consumer connecté, en attente de messages...")

count = 0
for message in consumer:
    try:
        data = message.value
        if 'data' in data:
            symbol = data['data']['s']
            price = float(data['data']['p'])
            logger.info(f"📊 Message {count}: {symbol} = ${price}")
            count += 1
            
            if count >= 10:
                break
    except Exception as e:
        logger.error(f"Erreur: {e}")

logger.info(f"✅ Test terminé: {count} messages reçus")
