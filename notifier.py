import os
import json
import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoNotifier:
    def __init__(self):
        """Initialise le notifier avec les configurations nécessaires."""
        load_dotenv()
        
        # Configuration email
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_from = os.getenv('EMAIL_FROM')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_to = os.getenv('EMAIL_TO', '').split(',')
        
        # Configuration des seuils d'alerte
        self.price_change_threshold = float(os.getenv('PRICE_CHANGE_THRESHOLD', '5'))  # 5% par défaut
        self.whale_alert_threshold = float(os.getenv('WHALE_ALERT_THRESHOLD', '1000000'))  # 1M USD par défaut
        
        # Configuration Discord/Slack (optionnel)
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK')
        self.slack_webhook = os.getenv('SLACK_WEBHOOK')
        
    def check_price_alerts(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vérifie les changements de prix significatifs."""
        alerts = []
        
        if 'prices' in market_data and 'changes_24h' in market_data['prices']:
            for crypto, change in market_data['prices']['changes_24h'].items():
                if abs(change) >= self.price_change_threshold:
                    alert = {
                        'type': 'price_change',
                        'crypto': crypto,
                        'change': change,
                        'price': market_data['prices']['prices'].get(crypto, 0),
                        'timestamp': datetime.now().isoformat()
                    }
                    alerts.append(alert)
                    
        return alerts
        
    def check_whale_alerts(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vérifie les mouvements de baleines significatifs."""
        alerts = []
        
        if 'whale_alerts' in market_data:
            for alert in market_data['whale_alerts']:
                try:
                    amount = float(alert.get('amount', 0))
                    if amount >= self.whale_alert_threshold:
                        alerts.append({
                            'type': 'whale_movement',
                            'amount': amount,
                            'symbol': alert.get('symbol', 'UNKNOWN'),
                            'transaction_type': alert.get('type', 'unknown'),
                            'timestamp': datetime.now().isoformat()
                        })
                except (ValueError, TypeError):
                    continue
                    
        return alerts
        
    def check_trending_alerts(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vérifie les nouvelles cryptos tendances."""
        alerts = []
        
        if 'trending' in market_data:
            for coin in market_data['trending'][:3]:  # Top 3 tendances
                alerts.append({
                    'type': 'trending',
                    'name': coin.get('name', 'Unknown'),
                    'symbol': coin.get('symbol', 'N/A'),
                    'rank': coin.get('market_cap_rank', 'N/A'),
                    'timestamp': datetime.now().isoformat()
                })
                
        return alerts
        
    def format_alerts_html(self, alerts: List[Dict[str, Any]]) -> str:
        """Formate les alertes en HTML pour l'email."""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .alert { margin: 20px 0; padding: 15px; border-radius: 5px; }
                .price-alert { background-color: #e8f4f8; border-left: 4px solid #1e88e5; }
                .whale-alert { background-color: #f3e5f5; border-left: 4px solid #8e24aa; }
                .trending-alert { background-color: #fff3e0; border-left: 4px solid #ff6f00; }
                .positive { color: #4caf50; }
                .negative { color: #f44336; }
            </style>
        </head>
        <body>
            <h2>🚨 Alertes Crypto Veille</h2>
        """
        
        for alert in alerts:
            if alert['type'] == 'price_change':
                change_class = 'positive' if alert['change'] > 0 else 'negative'
                html += f"""
                <div class="alert price-alert">
                    <h3>💰 Changement de Prix Significatif</h3>
                    <p><strong>{alert['crypto'].upper()}</strong>: 
                    <span class="{change_class}">{alert['change']:+.2f}%</span></p>
                    <p>Prix actuel: ${alert['price']:,.2f}</p>
                </div>
                """
            elif alert['type'] == 'whale_movement':
                html += f"""
                <div class="alert whale-alert">
                    <h3>🐋 Mouvement de Baleine Détecté</h3>
                    <p><strong>{alert['amount']:,.0f} {alert['symbol']}</strong></p>
                    <p>Type: {alert['transaction_type']}</p>
                </div>
                """
            elif alert['type'] == 'trending':
                html += f"""
                <div class="alert trending-alert">
                    <h3>🔥 Crypto Tendance</h3>
                    <p><strong>{alert['name']}</strong> ({alert['symbol']})</p>
                    <p>Rang: #{alert['rank']}</p>
                </div>
                """
                
        html += """
            <hr>
            <p><small>Généré le """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</small></p>
        </body>
        </html>
        """
        
        return html
        
    def send_email_alert(self, alerts: List[Dict[str, Any]]):
        """Envoie les alertes par email."""
        if not self.email_from or not self.email_password or not self.email_to:
            logger.warning("Configuration email manquante")
            return
            
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 Crypto Veille - {len(alerts)} alertes détectées"
            msg['From'] = self.email_from
            msg['To'] = ', '.join(self.email_to)
            
            # Version texte
            text = f"Crypto Veille - {len(alerts)} alertes détectées\n\n"
            for alert in alerts:
                text += f"- {alert['type']}: {alert}\n"
                
            # Version HTML
            html = self.format_alerts_html(alerts)
            
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Envoi de l'email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
                
            logger.info(f"Email envoyé avec {len(alerts)} alertes")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
            
    def send_discord_alert(self, alerts: List[Dict[str, Any]]):
        """Envoie les alertes sur Discord."""
        if not self.discord_webhook:
            return

        try:
            for alert in alerts[:5]:  # Limite à 5 alertes
                embed = {
                    "title": "🚨 Alerte Crypto",
                    "color": 15158332,
                    "fields": [],
                    "timestamp": alert['timestamp']
                }

                if alert['type'] == 'price_change':
                    embed["title"] = f"💰 {alert['crypto'].upper()} - Changement de prix"
                    embed["color"] = 3066993 if alert['change'] > 0 else 15158332
                    embed["fields"] = [
                        {"name": "Changement 24h", "value": f"{alert['change']:+.2f}%", "inline": True},
                        {"name": "Prix actuel", "value": f"${alert['price']:,.2f}", "inline": True}
                    ]
                elif alert['type'] == 'whale_movement':
                    embed["title"] = f"🐋 Mouvement de baleine - {alert['symbol']}"
                    embed["color"] = 10181046
                    embed["fields"] = [
                        {"name": "Montant", "value": f"{alert['amount']:,.0f} {alert['symbol']}", "inline": True},
                        {"name": "Type", "value": alert['transaction_type'], "inline": True}
                    ]
                elif alert['type'] == 'trending':
                    embed["title"] = f"🔥 Crypto Tendance - {alert['name']}"
                    embed["color"] = 16750848
                    embed["fields"] = [
                        {"name": "Symbole", "value": alert['symbol'], "inline": True},
                        {"name": "Rang", "value": f"#{alert['rank']}", "inline": True}
                    ]

                payload = {"embeds": [embed]}
                response = requests.post(self.discord_webhook, json=payload, timeout=10)
                response.raise_for_status()

            logger.info(f"Alertes Discord envoyées")

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi Discord : {str(e)}")

    def send_slack_alert(self, alerts: List[Dict[str, Any]]):
        """Envoie les alertes sur Slack."""
        if not self.slack_webhook:
            return

        try:
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"🚨 Crypto Veille - {len(alerts)} alertes"}
                }
            ]

            for alert in alerts[:10]:  # Limite à 10 alertes
                if alert['type'] == 'price_change':
                    emoji = "📈" if alert['change'] > 0 else "📉"
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{emoji} *{alert['crypto'].upper()}*: {alert['change']:+.2f}% | Prix: ${alert['price']:,.2f}"
                        }
                    })
                elif alert['type'] == 'whale_movement':
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🐋 *Baleine*: {alert['amount']:,.0f} {alert['symbol']} ({alert['transaction_type']})"
                        }
                    })
                elif alert['type'] == 'trending':
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🔥 *Tendance*: {alert['name']} ({alert['symbol']}) - Rang #{alert['rank']}"
                        }
                    })

            payload = {"blocks": blocks}
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Alertes Slack envoyées")

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi Slack : {str(e)}")
            
    def check_and_notify(self, all_data: Dict[str, Any]):
        """Vérifie toutes les alertes et envoie les notifications."""
        all_alerts = []

        # Vérification des alertes de marché
        if 'market' in all_data:
            all_alerts.extend(self.check_price_alerts(all_data['market']))
            all_alerts.extend(self.check_whale_alerts(all_data['market']))
            all_alerts.extend(self.check_trending_alerts(all_data['market']))

        if all_alerts:
            logger.info(f"{len(all_alerts)} alertes détectées")

            # Envoi des notifications sur tous les canaux configurés
            self.send_email_alert(all_alerts)
            self.send_discord_alert(all_alerts)
            self.send_slack_alert(all_alerts)

            # Sauvegarde des alertes
            self.save_alerts(all_alerts)
        else:
            logger.info("Aucune alerte détectée")
            
    def save_alerts(self, alerts: List[Dict[str, Any]]):
        """Sauvegarde les alertes dans un fichier."""
        try:
            alerts_file = 'data/alerts_history.json'
            
            # Chargement de l'historique existant
            history = []
            if os.path.exists(alerts_file):
                with open(alerts_file, 'r') as f:
                    history = json.load(f)
                    
            # Ajout des nouvelles alertes
            history.extend(alerts)
            
            # Limitation de l'historique (garder les 1000 dernières)
            history = history[-1000:]
            
            # Sauvegarde
            os.makedirs('data', exist_ok=True)
            with open(alerts_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            logger.info(f"{len(alerts)} alertes sauvegardées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des alertes : {str(e)}")