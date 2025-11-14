import smtplib
import json
import requests
from email.mime.text import MIMEText
from datetime import datetime
from kafka import KafkaProducer

class AlertManager:
    def __init__(self, kafka_servers=['kafka:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.alert_rules = self.load_alert_rules()
    
    def load_alert_rules(self):
        """Définit les règles d'alertes"""
        return {
            "high_volatility": {
                "condition": "volatility > 0.05",
                "message": "Forte volatilité détectée",
                "severity": "HIGH",
                "channels": ["kafka", "email"]
            },
            "rsi_oversold": {
                "condition": "rsi < 30",
                "message": "Situation de survente (RSI < 30)",
                "severity": "MEDIUM",
                "channels": ["kafka", "slack"]
            },
            "rsi_overbought": {
                "condition": "rsi > 70",
                "message": "Situation de surachat (RSI > 70)",
                "severity": "MEDIUM",
                "channels": ["kafka", "slack"]
            },
            "price_breakout": {
                "condition": "price > upper_band OR price < lower_band",
                "message": "Cassure des bandes de Bollinger",
                "severity": "HIGH",
                "channels": ["kafka", "email", "slack"]
            },
            "macd_signal": {
                "condition": "macd_line > signal_line AND prev_macd_line <= prev_signal_line",
                "message": "Signal d'achat MACD détecté",
                "severity": "MEDIUM",
                "channels": ["kafka"]
            },
            "volume_spike": {
                "condition": "trade_count > avg_trade_count * 3",
                "message": "Pic de volume anormal",
                "severity": "HIGH",
                "channels": ["kafka", "email"]
            }
        }
    
    def evaluate_alerts(self, data_row):
        """Évalue toutes les règles d'alertes pour une ligne de données"""
        alerts = []
        
        for rule_name, rule in self.alert_rules.items():
            if self._evaluate_condition(rule["condition"], data_row):
                alert = {
                    "rule_name": rule_name,
                    "symbol": data_row.get("symbol"),
                    "message": rule["message"],
                    "severity": rule["severity"],
                    "timestamp": datetime.now().isoformat(),
                    "data": data_row,
                    "channels": rule["channels"]
                }
                alerts.append(alert)
        
        return alerts
    
    def _evaluate_condition(self, condition, data):
        """Évalue une condition d'alerte (logique simplifiée)"""
        try:
            # Remplace les noms de variables par leurs valeurs
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    condition = condition.replace(key, str(value))
            
            # Évaluation simple (en production, utiliser un parser sécurisé)
            return eval(condition)
        except:
            return False
    
    def send_alerts(self, alerts):
        """Envoie les alertes via différents canaux"""
        for alert in alerts:
            for channel in alert["channels"]:
                if channel == "kafka":
                    self._send_to_kafka(alert)
                elif channel == "email":
                    self._send_email(alert)
                elif channel == "slack":
                    self._send_slack(alert)
    
    def _send_to_kafka(self, alert):
        """Envoie l'alerte vers un topic Kafka dédié"""
        self.producer.send('binance-alerts', alert)
        print(f"✅ Alerte envoyée vers Kafka: {alert['message']}")
    
    def _send_email(self, alert):
        """Envoie l'alerte par email (configuration à adapter)"""
        try:
            msg = MIMEText(f"""
            Alerte Trading - {alert['severity']}
            
            Symbole: {alert['symbol']}
            Message: {alert['message']}
            Timestamp: {alert['timestamp']}
            
            Données: {json.dumps(alert['data'], indent=2)}
            """)
            
            msg['Subject'] = f"Alerte {alert['symbol']} - {alert['severity']}"
            msg['From'] = "trading-bot@example.com"
            msg['To'] = "trader@example.com"
            
            # Configuration SMTP à adapter
            # server = smtplib.SMTP('smtp.gmail.com', 587)
            # server.send_message(msg)
            print(f"📧 Alerte email préparée: {alert['message']}")
        except Exception as e:
            print(f"❌ Erreur envoi email: {e}")
    
    def _send_slack(self, alert):
        """Envoie l'alerte vers Slack (webhook à configurer)"""
        try:
            webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
            payload = {
                "text": f"🚨 {alert['message']}",
                "attachments": [
                    {
                        "color": "danger" if alert['severity'] == "HIGH" else "warning",
                        "fields": [
                            {"title": "Symbole", "value": alert['symbol'], "short": True},
                            {"title": "Sévérité", "value": alert['severity'], "short": True},
                            {"title": "Timestamp", "value": alert['timestamp'], "short": False}
                        ]
                    }
                ]
            }
            
            # requests.post(webhook_url, json=payload)
            print(f"💬 Alerte Slack préparée: {alert['message']}")
        except Exception as e:
            print(f"❌ Erreur envoi Slack: {e}")

# Intégration avec Spark Streaming
def process_alerts_stream(df):
    """Traite les alertes dans Spark Streaming"""
    alert_manager = AlertManager()
    
    def process_batch(batch_df, batch_id):
        # Convertir en format approprié et évaluer les alertes
        for row in batch_df.collect():
            data = row.asDict()
            alerts = alert_manager.evaluate_alerts(data)
            if alerts:
                alert_manager.send_alerts(alerts)
    
    return df.writeStream \
        .foreachBatch(process_batch) \
        .outputMode("update") \
        .start()