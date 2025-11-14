import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
FROM_EMAIL = os.getenv('FROM_EMAIL')


def send_alert_email(to_email: str, alert_name: str, conditions: list, symbol: str):
    """
    Envoie un email de notification d'alerte
    """
    try:
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🚨 Alerte Crypto: {alert_name}'
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        
        # Construire le corps du message
        conditions_text = "\n".join([
            f"  • {cond.get('symbol', 'N/A')}: {cond['type'].replace('_', ' ')} {cond.get('threshold', '')}"
            for cond in conditions
        ])
        
        text_body = f"""
🚨 ALERTE CRYPTO DÉCLENCHÉE 🚨

Nom de l'alerte: {alert_name}
Symbole: {symbol}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

CONDITIONS REMPLIES:
{conditions_text}

Cette alerte a été créée sur votre plateforme Crypto Trading Analytics.

---
CryptoLive - Trading en temps réel avec Binance API
        """
        
        html_body = f"""
        <html>
          <head>
            <style>
              body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
              }}
              .container {{
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                max-width: 600px;
                margin: 0 auto;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
              }}
              .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 20px;
              }}
              .alert-icon {{
                font-size: 48px;
                margin-bottom: 10px;
              }}
              .content {{
                color: #333;
                line-height: 1.6;
              }}
              .conditions {{
                background-color: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
              }}
              .condition-item {{
                padding: 8px 0;
                border-bottom: 1px solid #e0e0e0;
              }}
              .condition-item:last-child {{
                border-bottom: none;
              }}
              .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                color: #666;
                font-size: 12px;
              }}
              .badge {{
                display: inline-block;
                padding: 5px 10px;
                background-color: #667eea;
                color: white;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
              }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <div class="alert-icon">🚨</div>
                <h1 style="margin: 0;">ALERTE DÉCLENCHÉE</h1>
              </div>
              
              <div class="content">
                <h2 style="color: #667eea;">{alert_name}</h2>
                <p><strong>Symbole:</strong> <span class="badge">{symbol}</span></p>
                <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
                
                <div class="conditions">
                  <h3 style="margin-top: 0; color: #667eea;">Conditions remplies:</h3>
                  {"".join([f'<div class="condition-item">✓ <strong>{cond.get("symbol", "N/A")}</strong>: {cond["type"].replace("_", " ")} {cond.get("threshold", "")}</div>' for cond in conditions])}
                </div>
                
                <p>Toutes les conditions définies ont été satisfaites simultanément.</p>
              </div>
              
              <div class="footer">
                <p><strong>CryptoLive</strong> - Trading Analytics en temps réel</p>
                <p>Propulsé par Binance API, Apache Kafka & Spark</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        # Attacher les deux versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Envoyer l'email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email envoyé à {to_email} pour l'alerte '{alert_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return False


def test_email_connection():
    """
    Test de connexion au serveur SMTP
    """
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("✅ Connexion SMTP réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur connexion SMTP: {e}")
        return False


if __name__ == "__main__":
    # Test de connexion
    test_email_connection()
