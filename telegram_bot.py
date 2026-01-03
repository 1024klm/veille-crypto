import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from market_data_fetcher import MarketDataFetcher
from external_sources_fetcher import ExternalSourcesFetcher
from sentiment_analyzer import AdvancedSentimentAnalyzer
from technical_analyzer import TechnicalAnalyzer
from cache_manager import cache_manager

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CryptoTelegramBot:
    def __init__(self):
        """Initialise le bot Telegram."""
        load_dotenv()
        
        # Token du bot
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN non défini dans .env")
        
        # Initialisation des composants
        self.market_fetcher = MarketDataFetcher()
        self.external_fetcher = ExternalSourcesFetcher()
        self.sentiment_analyzer = AdvancedSentimentAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        
        # Configuration des alertes automatiques
        self.alert_channels = os.getenv('TELEGRAM_ALERT_CHANNELS', '').split(',')
        self.price_alert_threshold = float(os.getenv('TELEGRAM_PRICE_ALERT_THRESHOLD', '5'))
        
        # État des utilisateurs
        self.user_watchlists = {}
        self.user_alerts = {}
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start."""
        user = update.effective_user
        welcome_message = f"""
🚀 Bienvenue {user.first_name} sur Crypto Veille Bot!

Je suis votre assistant personnel pour surveiller le marché crypto 24/7.

📊 **Commandes disponibles:**
/help - Afficher l'aide détaillée
/prices - Prix des principales cryptos
/trending - Cryptos tendances du moment
/news - Dernières actualités crypto
/sentiment - Analyse de sentiment du marché
/technical <symbol> - Analyse technique (ex: /technical bitcoin)
/alerts - Gérer vos alertes personnalisées
/watchlist - Gérer votre watchlist

💡 **Fonctionnalités:**
• Prix en temps réel
• Alertes de mouvements importants
• Analyse technique avancée
• Sentiment du marché
• Actualités filtrées

Commencez par /prices pour voir les prix actuels!
"""
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Prix", callback_data='prices'),
                InlineKeyboardButton("🔥 Tendances", callback_data='trending')
            ],
            [
                InlineKeyboardButton("📰 News", callback_data='news'),
                InlineKeyboardButton("📊 Sentiment", callback_data='sentiment')
            ],
            [
                InlineKeyboardButton("📈 Analyse Tech", callback_data='technical_menu'),
                InlineKeyboardButton("🔔 Alertes", callback_data='alerts_menu')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /help."""
        help_text = """
📚 **AIDE DÉTAILLÉE**

**Commandes de base:**
• /start - Menu principal
• /help - Cette aide
• /prices - Prix actuels des cryptos majeures
• /trending - Top 10 des cryptos tendances

**Analyse de marché:**
• /sentiment - Analyse de sentiment globale
• /news [source] - Actualités (source: media, regulatory, french)
• /technical <coin> - Analyse technique complète
  Exemple: `/technical bitcoin` ou `/technical ethereum`

**Gestion des alertes:**
• /alerts - Voir vos alertes actives
• /setalert <coin> <price> - Créer une alerte de prix
  Exemple: `/setalert bitcoin 45000`
• /removealert <id> - Supprimer une alerte

**Watchlist personnelle:**
• /watchlist - Voir votre watchlist
• /addwatch <coin> - Ajouter une crypto
• /removewatch <coin> - Retirer une crypto

**Notifications automatiques:**
• Mouvements de prix > 5%
• Alertes de baleines
• Actualités importantes
• Signaux techniques

**Tips:**
💡 Utilisez les boutons du menu pour naviguer rapidement
💡 Les analyses sont mises en cache 5-15 minutes
💡 Créez des alertes pour ne rien manquer

Des questions? Contactez @YourUsername
"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def get_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Récupère et affiche les prix actuels."""
        await update.message.reply_text("📊 Récupération des prix...")
        
        try:
            # Utilisation du cache
            market_data = cache_manager.get('market_data', 'market_prices')
            if not market_data:
                market_data = self.market_fetcher.fetch_all_market_data()
                cache_manager.set('market_data', market_data, 'market_prices')
            
            if 'prices' not in market_data:
                await update.message.reply_text("❌ Erreur lors de la récupération des données")
                return
            
            prices_data = market_data['prices']
            message = "💰 **PRIX DES CRYPTOMONNAIES**\n\n"
            
            # Tri par market cap (approximatif)
            sorted_cryptos = sorted(
                prices_data['prices'].items(),
                key=lambda x: prices_data['market_caps'].get(x[0], 0),
                reverse=True
            )
            
            for crypto, price in sorted_cryptos[:15]:
                change = prices_data['changes_24h'].get(crypto, 0)
                emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
                
                # Formatage du prix
                if price >= 1000:
                    price_str = f"${price:,.0f}"
                elif price >= 1:
                    price_str = f"${price:.2f}"
                else:
                    price_str = f"${price:.4f}"
                
                message += f"{emoji} **{crypto.upper()}**: {price_str} ({change:+.2f}%)\n"
            
            # Ajout des statistiques globales
            if 'market_cap' in market_data:
                mc_data = market_data['market_cap']
                message += f"\n📊 **Statistiques Globales:**\n"
                message += f"• Cap. totale: ${mc_data.get('total_market_cap', 0):,.0f}\n"
                message += f"• Volume 24h: ${mc_data.get('total_volume', 0):,.0f}\n"
            
            message += f"\n_Dernière MAJ: {datetime.now().strftime('%H:%M:%S')}_"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur get_prices: {str(e)}")
            await update.message.reply_text("❌ Erreur lors de la récupération des prix")
    
    async def get_trending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche les cryptos tendances."""
        await update.message.reply_text("🔥 Recherche des cryptos tendances...")
        
        try:
            market_data = cache_manager.get('market_data', 'market_prices')
            if not market_data:
                market_data = self.market_fetcher.fetch_all_market_data()
                cache_manager.set('market_data', market_data, 'market_prices')
            
            if 'trending' not in market_data:
                await update.message.reply_text("❌ Données de tendance non disponibles")
                return
            
            message = "🔥 **TOP 10 CRYPTOS TENDANCES**\n\n"
            
            for i, coin in enumerate(market_data['trending'][:10], 1):
                message += f"{i}. **{coin.get('name', 'N/A')}** ({coin.get('symbol', 'N/A').upper()})\n"
                message += f"   • Rang: #{coin.get('market_cap_rank', 'N/A')}\n"
                if coin.get('price_btc'):
                    message += f"   • Prix: {coin['price_btc']:.8f} BTC\n"
                message += "\n"
            
            message += "_Source: CoinGecko Trending_"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur get_trending: {str(e)}")
            await update.message.reply_text("❌ Erreur lors de la récupération des tendances")
    
    async def get_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Récupère les dernières actualités."""
        # Détermination de la source
        source = 'media'  # Par défaut
        if context.args:
            source = context.args[0].lower()
        
        await update.message.reply_text(f"📰 Récupération des actualités ({source})...")
        
        try:
            external_data = cache_manager.get('external_data', 'rss_feeds')
            if not external_data:
                external_data = self.external_fetcher.fetch_all_sources()
                cache_manager.set('external_data', external_data, 'rss_feeds')
            
            if source not in external_data:
                await update.message.reply_text(
                    "❌ Source invalide. Utilisez: media, regulatory, french, analytics"
                )
                return
            
            news_items = external_data[source][:10]
            
            if not news_items:
                await update.message.reply_text("❌ Aucune actualité disponible")
                return
            
            source_names = {
                'media': '📰 MÉDIAS CRYPTO',
                'regulatory': '⚖️ RÉGULATION',
                'french': '🇫🇷 ACTUALITÉS FR',
                'analytics': '📊 ANALYSES'
            }
            
            message = f"**{source_names.get(source, source.upper())}**\n\n"
            
            for item in news_items:
                title = item.get('title', 'Sans titre')
                link = item.get('link', '#')
                source_name = item.get('source', 'Unknown')
                
                # Troncature du titre si trop long
                if len(title) > 100:
                    title = title[:97] + "..."
                
                message += f"• [{title}]({link})\n"
                message += f"  _Source: {source_name}_\n\n"
            
            # Telegram limite la longueur des messages
            if len(message) > 4000:
                message = message[:3997] + "..."
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Erreur get_news: {str(e)}")
            await update.message.reply_text("❌ Erreur lors de la récupération des actualités")
    
    async def get_sentiment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyse le sentiment du marché."""
        await update.message.reply_text("🧠 Analyse du sentiment en cours...")
        
        try:
            # Récupération des dernières données
            external_data = self.external_fetcher.fetch_all_sources()
            
            # Extraction des textes pour l'analyse
            texts = []
            for source in ['media', 'french']:
                if source in external_data:
                    for item in external_data[source][:20]:
                        if 'title' in item:
                            texts.append(item['title'])
                        if 'summary' in item and len(item['summary']) > 50:
                            texts.append(item['summary'][:500])
            
            if not texts:
                await update.message.reply_text("❌ Pas assez de données pour l'analyse")
                return
            
            # Analyse de sentiment
            analysis = self.sentiment_analyzer.analyze_batch(texts[:30])
            
            # Création du message
            avg_sentiment = analysis['average_sentiment']
            sentiment_emoji = "🚀" if avg_sentiment > 0.5 else "📈" if avg_sentiment > 0.1 else "➖" if avg_sentiment > -0.1 else "📉" if avg_sentiment > -0.5 else "💥"
            
            message = f"{sentiment_emoji} **ANALYSE DE SENTIMENT DU MARCHÉ**\n\n"
            message += f"**Score Global:** {avg_sentiment:.3f}\n"
            message += f"**Interprétation:** {self.sentiment_analyzer._categorize_sentiment(avg_sentiment).replace('_', ' ').title()}\n\n"
            
            # Distribution
            message += "**Distribution des sentiments:**\n"
            total = analysis['total_analyzed']
            for category, count in analysis['sentiment_distribution'].items():
                percentage = (count / total * 100) if total > 0 else 0
                bar_length = int(percentage / 5)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                
                emoji_map = {
                    'très_positif': '🚀',
                    'positif': '📈',
                    'neutre': '➖',
                    'négatif': '📉',
                    'très_négatif': '💥'
                }
                
                message += f"{emoji_map.get(category, '')} {bar} {percentage:.1f}%\n"
            
            # Top cryptos mentionnées
            if analysis['top_mentioned_cryptos']:
                message += "\n**🏆 Top Cryptos Mentionnées:**\n"
                for crypto, count in analysis['top_mentioned_cryptos'][:5]:
                    message += f"• {crypto}: {count} mentions\n"
            
            # Sujets tendances
            if analysis['trending_topics']:
                message += "\n**🏷️ Sujets Tendances:**\n"
                for topic, count in analysis['trending_topics']:
                    message += f"• {topic}: {count} occurrences\n"
            
            message += f"\n_Analyse basée sur {total} textes_"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur get_sentiment: {str(e)}")
            await update.message.reply_text("❌ Erreur lors de l'analyse de sentiment")
    
    async def technical_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Effectue une analyse technique."""
        if not context.args:
            await update.message.reply_text(
                "❌ Veuillez spécifier une crypto\nExemple: `/technical bitcoin`",
                parse_mode='Markdown'
            )
            return
        
        coin_id = context.args[0].lower()
        await update.message.reply_text(f"📈 Analyse technique de {coin_id} en cours...")
        
        try:
            # Analyse technique
            analysis = self.technical_analyzer.analyze_coin(coin_id)
            
            if 'error' in analysis:
                await update.message.reply_text(f"❌ {analysis['error']}")
                return
            
            # Génération du rapport
            report = self.technical_analyzer.generate_report(analysis)
            
            # Envoi du rapport texte
            await update.message.reply_text(f"```\n{report}\n```", parse_mode='Markdown')
            
            # Si un graphique est disponible, l'envoyer
            if analysis.get('chart'):
                # Note: Pour envoyer l'image, il faudrait la convertir depuis base64
                # Pour l'instant, on indique juste qu'un graphique est disponible
                await update.message.reply_text(
                    "📊 Graphique disponible sur le dashboard web",
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            logger.error(f"Erreur technical_analysis: {str(e)}")
            await update.message.reply_text("❌ Erreur lors de l'analyse technique")
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les callbacks des boutons inline."""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'prices':
            # Simulation d'un message pour réutiliser la fonction
            update.message = query.message
            await self.get_prices(update, context)
        
        elif query.data == 'trending':
            update.message = query.message
            await self.get_trending(update, context)
        
        elif query.data == 'news':
            update.message = query.message
            await self.get_news(update, context)
        
        elif query.data == 'sentiment':
            update.message = query.message
            await self.get_sentiment(update, context)
        
        elif query.data == 'technical_menu':
            keyboard = [
                [InlineKeyboardButton("Bitcoin", callback_data='tech_bitcoin')],
                [InlineKeyboardButton("Ethereum", callback_data='tech_ethereum')],
                [InlineKeyboardButton("Solana", callback_data='tech_solana')],
                [InlineKeyboardButton("⬅️ Retour", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📈 Choisissez une crypto pour l'analyse technique:",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith('tech_'):
            coin = query.data.replace('tech_', '')
            update.message = query.message
            context.args = [coin]
            await self.technical_analysis(update, context)
        
        elif query.data == 'main_menu':
            # Retour au menu principal
            update.message = query.message
            update.effective_user = query.from_user
            await self.start(update, context)
    
    async def send_price_alert(self, context: ContextTypes.DEFAULT_TYPE):
        """Envoie des alertes de prix automatiques."""
        try:
            market_data = self.market_fetcher.fetch_all_market_data()
            
            if 'prices' not in market_data:
                return
            
            prices_data = market_data['prices']
            alerts = []
            
            # Vérification des changements significatifs
            for crypto, change in prices_data['changes_24h'].items():
                if abs(change) >= self.price_alert_threshold:
                    alerts.append({
                        'crypto': crypto,
                        'price': prices_data['prices'].get(crypto, 0),
                        'change': change
                    })
            
            if not alerts:
                return
            
            # Envoi des alertes aux canaux configurés
            for channel_id in self.alert_channels:
                if not channel_id:
                    continue
                
                message = "🚨 **ALERTES DE PRIX**\n\n"
                
                for alert in alerts[:5]:  # Limite à 5 alertes
                    emoji = "🚀" if alert['change'] > 0 else "💥"
                    message += f"{emoji} **{alert['crypto'].upper()}**\n"
                    message += f"Prix: ${alert['price']:,.2f}\n"
                    message += f"Variation 24h: {alert['change']:+.2f}%\n\n"
                
                try:
                    await context.bot.send_message(
                        chat_id=channel_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Erreur envoi alerte au canal {channel_id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Erreur send_price_alert: {str(e)}")
    
    async def watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la watchlist de l'utilisateur."""
        user_id = str(update.effective_user.id)
        watchlist = self.user_watchlists.get(user_id, [])

        if not watchlist:
            await update.message.reply_text(
                "📋 Votre watchlist est vide.\n\n"
                "Utilisez `/addwatch <coin>` pour ajouter une crypto.\n"
                "Exemple: `/addwatch bitcoin`",
                parse_mode='Markdown'
            )
            return

        await update.message.reply_text("📊 Récupération des prix de votre watchlist...")

        try:
            market_data = self.market_fetcher.fetch_all_market_data()
            prices_data = market_data.get('prices', {}).get('prices', {})
            changes_data = market_data.get('prices', {}).get('changes_24h', {})

            message = "📋 **VOTRE WATCHLIST**\n\n"

            for coin in watchlist:
                price = prices_data.get(coin, 0)
                change = changes_data.get(coin, 0)
                emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"

                if price >= 1:
                    price_str = f"${price:,.2f}"
                else:
                    price_str = f"${price:.6f}"

                message += f"{emoji} **{coin.upper()}**: {price_str} ({change:+.2f}%)\n"

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Erreur watchlist: {str(e)}")
            await update.message.reply_text("❌ Erreur lors de la récupération des données")

    async def add_to_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ajoute une crypto à la watchlist."""
        if not context.args:
            await update.message.reply_text(
                "❌ Veuillez spécifier une crypto.\n"
                "Exemple: `/addwatch bitcoin`",
                parse_mode='Markdown'
            )
            return

        user_id = str(update.effective_user.id)
        coin = context.args[0].lower()

        if user_id not in self.user_watchlists:
            self.user_watchlists[user_id] = []

        if coin in self.user_watchlists[user_id]:
            await update.message.reply_text(f"ℹ️ {coin.upper()} est déjà dans votre watchlist")
            return

        self.user_watchlists[user_id].append(coin)
        await update.message.reply_text(
            f"✅ {coin.upper()} ajouté à votre watchlist!\n\n"
            f"Utilisez /watchlist pour voir votre liste."
        )

    async def remove_from_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Retire une crypto de la watchlist."""
        if not context.args:
            await update.message.reply_text(
                "❌ Veuillez spécifier une crypto.\n"
                "Exemple: `/removewatch bitcoin`",
                parse_mode='Markdown'
            )
            return

        user_id = str(update.effective_user.id)
        coin = context.args[0].lower()

        if user_id not in self.user_watchlists or coin not in self.user_watchlists[user_id]:
            await update.message.reply_text(f"ℹ️ {coin.upper()} n'est pas dans votre watchlist")
            return

        self.user_watchlists[user_id].remove(coin)
        await update.message.reply_text(f"✅ {coin.upper()} retiré de votre watchlist!")

    async def set_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Définit une alerte de prix personnalisée."""
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Format: `/setalert <coin> <prix>`\n"
                "Exemple: `/setalert bitcoin 100000`",
                parse_mode='Markdown'
            )
            return

        user_id = str(update.effective_user.id)
        coin = context.args[0].lower()

        try:
            target_price = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Prix invalide")
            return

        if user_id not in self.user_alerts:
            self.user_alerts[user_id] = []

        alert = {
            'coin': coin,
            'target_price': target_price,
            'created_at': datetime.now().isoformat()
        }

        self.user_alerts[user_id].append(alert)

        await update.message.reply_text(
            f"🔔 Alerte créée!\n\n"
            f"Vous serez notifié quand **{coin.upper()}** atteint ${target_price:,.2f}",
            parse_mode='Markdown'
        )

    async def list_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Liste les alertes de l'utilisateur."""
        user_id = str(update.effective_user.id)
        alerts = self.user_alerts.get(user_id, [])

        if not alerts:
            await update.message.reply_text(
                "🔔 Vous n'avez aucune alerte active.\n\n"
                "Utilisez `/setalert <coin> <prix>` pour en créer une.",
                parse_mode='Markdown'
            )
            return

        message = "🔔 **VOS ALERTES**\n\n"
        for i, alert in enumerate(alerts, 1):
            message += f"{i}. **{alert['coin'].upper()}** → ${alert['target_price']:,.2f}\n"

        message += "\n_Utilisez `/removealert <numéro>` pour supprimer_"
        await update.message.reply_text(message, parse_mode='Markdown')

    async def remove_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Supprime une alerte."""
        if not context.args:
            await update.message.reply_text(
                "❌ Veuillez spécifier le numéro de l'alerte.\n"
                "Utilisez /alerts pour voir la liste.",
                parse_mode='Markdown'
            )
            return

        user_id = str(update.effective_user.id)

        try:
            index = int(context.args[0]) - 1
            alerts = self.user_alerts.get(user_id, [])

            if 0 <= index < len(alerts):
                removed = alerts.pop(index)
                await update.message.reply_text(
                    f"✅ Alerte supprimée: {removed['coin'].upper()} → ${removed['target_price']:,.2f}"
                )
            else:
                await update.message.reply_text("❌ Numéro d'alerte invalide")
        except ValueError:
            await update.message.reply_text("❌ Numéro invalide")

    def run(self):
        """Lance le bot Telegram."""
        # Création de l'application
        application = Application.builder().token(self.token).build()

        # Ajout des handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("prices", self.get_prices))
        application.add_handler(CommandHandler("trending", self.get_trending))
        application.add_handler(CommandHandler("news", self.get_news))
        application.add_handler(CommandHandler("sentiment", self.get_sentiment))
        application.add_handler(CommandHandler("technical", self.technical_analysis))
        application.add_handler(CommandHandler("watchlist", self.watchlist))
        application.add_handler(CommandHandler("addwatch", self.add_to_watchlist))
        application.add_handler(CommandHandler("removewatch", self.remove_from_watchlist))
        application.add_handler(CommandHandler("setalert", self.set_alert))
        application.add_handler(CommandHandler("alerts", self.list_alerts))
        application.add_handler(CommandHandler("removealert", self.remove_alert))
        application.add_handler(CallbackQueryHandler(self.callback_handler))

        # Job pour les alertes automatiques (toutes les 5 minutes)
        job_queue = application.job_queue
        job_queue.run_repeating(self.send_price_alert, interval=300, first=10)

        # Démarrage du bot
        logger.info("Bot Telegram démarré!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = CryptoTelegramBot()
    bot.run()