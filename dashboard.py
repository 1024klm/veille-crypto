import os
import json
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de l'application Dash
app = dash.Dash(__name__, title="Crypto Veille Dashboard")
app.config.suppress_callback_exceptions = True

# Style CSS personnalisé
external_stylesheets = ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Couleurs du thème
COLORS = {
    'background': '#1e1e1e',
    'background_secondary': '#2d2d2d',
    'text': '#ffffff',
    'text_secondary': '#b0b0b0',
    'accent': '#3498db',
    'success': '#2ecc71',
    'danger': '#e74c3c',
    'warning': '#f39c12'
}

def load_data(filename: str) -> Dict[str, Any]:
    """Charge les données depuis un fichier JSON."""
    filepath = os.path.join('data', filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {filename}: {str(e)}")
    return {}

def create_price_chart(market_data: Dict[str, Any]) -> go.Figure:
    """Crée un graphique des prix des cryptos."""
    if not market_data or 'prices' not in market_data:
        return go.Figure()
    
    prices_data = market_data['prices']
    if 'prices' not in prices_data:
        return go.Figure()
    
    cryptos = list(prices_data['prices'].keys())
    prices = list(prices_data['prices'].values())
    changes = [prices_data['changes_24h'].get(crypto, 0) for crypto in cryptos]
    
    # Création du graphique en barres
    fig = go.Figure()
    
    # Couleurs basées sur les changements
    colors = [COLORS['success'] if change > 0 else COLORS['danger'] for change in changes]
    
    fig.add_trace(go.Bar(
        x=[c.upper() for c in cryptos],
        y=prices,
        text=[f"${p:,.2f}<br>({c:+.2f}%)" for p, c in zip(prices, changes)],
        textposition='outside',
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>Prix: $%{y:,.2f}<br>24h: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Prix des Cryptomonnaies",
        xaxis_title="Cryptomonnaie",
        yaxis_title="Prix (USD)",
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font_color=COLORS['text'],
        height=500
    )
    
    return fig

def create_sentiment_gauge(sentiment_data: Dict[str, Any]) -> go.Figure:
    """Crée une jauge de sentiment du marché."""
    if not sentiment_data or 'metrics' not in sentiment_data:
        return go.Figure()
    
    metrics = sentiment_data['metrics']
    bullish = metrics.get('bullish_count', 0)
    bearish = metrics.get('bearish_count', 0)
    total = bullish + bearish
    
    if total == 0:
        sentiment_score = 50
    else:
        sentiment_score = (bullish / total) * 100
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sentiment_score,
        title={'text': "Sentiment du Marché"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': COLORS['accent']},
            'steps': [
                {'range': [0, 30], 'color': COLORS['danger']},
                {'range': [30, 70], 'color': COLORS['warning']},
                {'range': [70, 100], 'color': COLORS['success']}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['background'],
        font={'color': COLORS['text'], 'size': 16},
        height=300
    )
    
    return fig

def create_trending_table(market_data: Dict[str, Any]) -> html.Div:
    """Crée un tableau des cryptos tendances."""
    if not market_data or 'trending' not in market_data:
        return html.Div("Aucune donnée de tendance disponible")
    
    trending = market_data['trending'][:10]
    
    rows = []
    for i, coin in enumerate(trending, 1):
        rows.append(
            html.Tr([
                html.Td(f"#{i}", style={'width': '10%'}),
                html.Td(coin.get('name', 'N/A'), style={'fontWeight': 'bold'}),
                html.Td(coin.get('symbol', 'N/A').upper()),
                html.Td(f"#{coin.get('market_cap_rank', 'N/A')}")
            ])
        )
    
    return html.Table([
        html.Thead([
            html.Tr([
                html.Th("Rang"),
                html.Th("Nom"),
                html.Th("Symbole"),
                html.Th("Cap. Rang")
            ])
        ]),
        html.Tbody(rows)
    ], style={
        'width': '100%',
        'color': COLORS['text'],
        'borderCollapse': 'collapse'
    })

def create_alerts_feed(alerts_history: List[Dict[str, Any]]) -> html.Div:
    """Crée un flux des dernières alertes."""
    if not alerts_history:
        return html.Div("Aucune alerte récente", style={'color': COLORS['text_secondary']})
    
    # Prendre les 20 dernières alertes
    recent_alerts = alerts_history[-20:][::-1]
    
    alert_items = []
    for alert in recent_alerts:
        icon = ""
        color = COLORS['text']
        
        if alert['type'] == 'price_change':
            icon = "📈" if alert.get('change', 0) > 0 else "📉"
            color = COLORS['success'] if alert.get('change', 0) > 0 else COLORS['danger']
            text = f"{alert.get('crypto', 'N/A').upper()}: {alert.get('change', 0):+.2f}%"
        elif alert['type'] == 'whale_movement':
            icon = "🐋"
            color = COLORS['warning']
            text = f"{alert.get('amount', 0):,.0f} {alert.get('symbol', 'N/A')}"
        elif alert['type'] == 'trending':
            icon = "🔥"
            color = COLORS['accent']
            text = f"{alert.get('name', 'N/A')} (#{alert.get('rank', 'N/A')})"
        else:
            continue
        
        alert_items.append(
            html.Div([
                html.Span(icon, style={'fontSize': '20px', 'marginRight': '10px'}),
                html.Span(text, style={'color': color}),
                html.Span(
                    datetime.fromisoformat(alert.get('timestamp', '')).strftime('%H:%M'),
                    style={'color': COLORS['text_secondary'], 'float': 'right'}
                )
            ], style={
                'padding': '10px',
                'borderBottom': f'1px solid {COLORS["background_secondary"]}',
                'display': 'flex',
                'alignItems': 'center'
            })
        )
    
    return html.Div(alert_items, style={
        'maxHeight': '400px',
        'overflowY': 'auto',
        'backgroundColor': COLORS['background_secondary'],
        'borderRadius': '5px',
        'padding': '10px'
    })

def create_news_feed(external_data: Dict[str, Any]) -> html.Div:
    """Crée un flux des dernières actualités."""
    news_items = []
    
    # Récupération des news de différentes sources
    categories = {
        'media': ('📰', 'Médias'),
        'regulatory': ('⚖️', 'Régulation'),
        'analytics': ('📊', 'Analyses'),
        'french': ('🇫🇷', 'FR')
    }
    
    for category, (icon, label) in categories.items():
        if category in external_data:
            for item in external_data[category][:3]:
                news_items.append(
                    html.Div([
                        html.Div([
                            html.Span(icon, style={'marginRight': '5px'}),
                            html.Span(label, style={
                                'fontSize': '12px',
                                'color': COLORS['text_secondary'],
                                'marginRight': '10px'
                            }),
                            html.A(
                                item.get('title', 'Sans titre')[:100] + '...',
                                href=item.get('link', '#'),
                                target='_blank',
                                style={'color': COLORS['accent'], 'textDecoration': 'none'}
                            )
                        ]),
                        html.Div(
                            item.get('source', ''),
                            style={'fontSize': '11px', 'color': COLORS['text_secondary']}
                        )
                    ], style={
                        'padding': '10px',
                        'borderBottom': f'1px solid {COLORS["background_secondary"]}'
                    })
                )
    
    return html.Div(news_items, style={
        'maxHeight': '500px',
        'overflowY': 'auto',
        'backgroundColor': COLORS['background_secondary'],
        'borderRadius': '5px'
    })

# Layout de l'application
app.layout = html.Div([
    # Header
    html.Div([
        html.H1([
            html.I(className="fas fa-chart-line", style={'marginRight': '10px'}),
            "Crypto Veille Dashboard"
        ], style={
            'textAlign': 'center',
            'color': COLORS['text'],
            'marginBottom': '30px'
        }),
        
        # Timestamp de dernière mise à jour
        html.Div(id='last-update', style={
            'textAlign': 'center',
            'color': COLORS['text_secondary'],
            'marginBottom': '20px'
        })
    ]),
    
    # Contenu principal
    html.Div([
        # Ligne 1: Prix et Sentiment
        html.Div([
            html.Div([
                dcc.Graph(id='price-chart')
            ], style={'width': '70%', 'display': 'inline-block', 'padding': '10px'}),
            
            html.Div([
                dcc.Graph(id='sentiment-gauge'),
                html.Div(id='market-stats', style={
                    'padding': '20px',
                    'backgroundColor': COLORS['background_secondary'],
                    'borderRadius': '5px',
                    'marginTop': '20px'
                })
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'})
        ]),
        
        # Ligne 2: Trending et Alertes
        html.Div([
            html.Div([
                html.H3("🔥 Cryptos Tendances", style={'color': COLORS['text']}),
                html.Div(id='trending-table')
            ], style={
                'width': '30%',
                'display': 'inline-block',
                'padding': '20px',
                'backgroundColor': COLORS['background_secondary'],
                'borderRadius': '5px',
                'margin': '10px'
            }),
            
            html.Div([
                html.H3("🚨 Alertes Récentes", style={'color': COLORS['text']}),
                html.Div(id='alerts-feed')
            ], style={
                'width': '30%',
                'display': 'inline-block',
                'padding': '20px',
                'backgroundColor': COLORS['background_secondary'],
                'borderRadius': '5px',
                'margin': '10px'
            }),
            
            html.Div([
                html.H3("📰 Dernières Actualités", style={'color': COLORS['text']}),
                html.Div(id='news-feed')
            ], style={
                'width': '35%',
                'display': 'inline-block',
                'padding': '20px',
                'backgroundColor': COLORS['background_secondary'],
                'borderRadius': '5px',
                'margin': '10px',
                'verticalAlign': 'top'
            })
        ])
    ]),
    
    # Intervalle de rafraîchissement (30 secondes)
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # en millisecondes
        n_intervals=0
    )
], style={
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'padding': '20px',
    'fontFamily': 'Arial, sans-serif'
})

# Callbacks
@app.callback(
    [Output('price-chart', 'figure'),
     Output('sentiment-gauge', 'figure'),
     Output('trending-table', 'children'),
     Output('alerts-feed', 'children'),
     Output('news-feed', 'children'),
     Output('market-stats', 'children'),
     Output('last-update', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Met à jour tous les composants du dashboard."""
    # Chargement des données
    all_data = load_data('all_data.json')
    alerts_history = load_data('alerts_history.json')
    
    market_data = all_data.get('market', {})
    external_data = all_data.get('external', {})
    
    # Création des graphiques
    price_chart = create_price_chart(market_data)
    sentiment_gauge = create_sentiment_gauge(market_data.get('sentiment', {}))
    trending_table = create_trending_table(market_data)
    alerts_feed = create_alerts_feed(alerts_history if isinstance(alerts_history, list) else [])
    news_feed = create_news_feed(external_data)
    
    # Statistiques du marché
    market_cap_data = market_data.get('market_cap', {})
    market_stats = html.Div([
        html.H4("📊 Statistiques Globales", style={'color': COLORS['text'], 'marginBottom': '15px'}),
        html.Div([
            html.Div([
                html.Div("Cap. Totale", style={'color': COLORS['text_secondary'], 'fontSize': '12px'}),
                html.Div(
                    f"${market_cap_data.get('total_market_cap', 0):,.0f}",
                    style={'color': COLORS['text'], 'fontSize': '18px', 'fontWeight': 'bold'}
                )
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Div("Volume 24h", style={'color': COLORS['text_secondary'], 'fontSize': '12px'}),
                html.Div(
                    f"${market_cap_data.get('total_volume', 0):,.0f}",
                    style={'color': COLORS['text'], 'fontSize': '18px', 'fontWeight': 'bold'}
                )
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Div("Cryptos Actives", style={'color': COLORS['text_secondary'], 'fontSize': '12px'}),
                html.Div(
                    f"{market_cap_data.get('active_cryptocurrencies', 0):,}",
                    style={'color': COLORS['text'], 'fontSize': '18px', 'fontWeight': 'bold'}
                )
            ])
        ])
    ])
    
    # Timestamp de dernière mise à jour
    timestamp = all_data.get('timestamp', '')
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp)
            last_update = f"Dernière mise à jour: {dt.strftime('%d/%m/%Y %H:%M:%S')}"
        except:
            last_update = "Dernière mise à jour: N/A"
    else:
        last_update = "Dernière mise à jour: N/A"
    
    return price_chart, sentiment_gauge, trending_table, alerts_feed, news_feed, market_stats, last_update

if __name__ == '__main__':
    print(f"\n🚀 Dashboard disponible sur: http://localhost:8050\n")
    app.run_server(debug=True, host='0.0.0.0', port=8050)