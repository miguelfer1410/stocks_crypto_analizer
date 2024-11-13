from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash
from crypto_analyzer import CryptoAnalyzer
from dash.exceptions import PreventUpdate

# Lista atualizada com os valores reais do portfólio
CRYPTO_COM_COINS = [
    {'symbol': 'CRO', 'label': 'Cronos', 'quantity': 424.02, 'invested_eur': 24.28},
    {'symbol': 'ATH30083', 'label': 'Aethir', 'quantity': 640, 'invested_eur': 31.72},  # 640 * 0.04957
    {'symbol': 'ETH', 'label': 'Ethereum', 'quantity': 0.01177, 'invested_eur': 28.88},
    {'symbol': 'SHIB', 'label': 'Shiba Inu', 'quantity': 1334000.0, 'invested_eur': 24.27},
    {'symbol': 'DOGE', 'label': 'Dogecoin', 'quantity': 149.7, 'invested_eur': 29.16},
    {'symbol': 'SOL', 'label': 'Solana', 'quantity': 0.1674, 'invested_eur': 24.06},
    {'symbol': 'ADA', 'label': 'Cardano', 'quantity': 69.1, 'invested_eur': 24.33},
    {'symbol': 'RAY', 'label': 'Raydium', 'quantity': 14.32, 'invested_eur': 29.75},
    {'symbol': 'AVAX', 'label': 'Avalanche', 'quantity': 1.104, 'invested_eur': 29.02},
    {'symbol': 'AERO29270', 'label': 'Aerodrome', 'quantity': 23.08, 'invested_eur': 29.54},
    {'symbol': 'LINK', 'label': 'Chainlink', 'quantity': 3.512, 'invested_eur': 39.51},
    {'symbol': 'XRP', 'label': 'XRP', 'quantity': 58.99, 'invested_eur': 29.83},
    {'symbol': 'USDT', 'label': 'Tether USDT', 'quantity': 26.09, 'invested_eur': 24.33},
    {'symbol': 'ONDO', 'label': 'Ondo', 'quantity': 36.88, 'invested_eur': 24.78},
    {'symbol': 'JASMY', 'label': 'JasmyCoin', 'quantity': 1419, 'invested_eur': 29.16},
    {'symbol': 'TAO22974', 'label': 'Bittensor', 'quantity': 0.04488, 'invested_eur': 24.07},
]

# Calcular preço médio de compra para cada cripto
for coin in CRYPTO_COM_COINS:
    coin['avg_price_eur'] = coin['invested_eur'] / coin['quantity']

dash.register_page(
    __name__,
    path='/',
    title='Análise de Criptomoedas',
    name='Criptomoedas'
)

def create_portfolio_summary(analyzer):
    """Cria o resumo do portfólio com valores atuais"""
    total_invested = 0
    total_current = 0
    portfolio_data = []
    
    for coin in CRYPTO_COM_COINS:
        symbol = coin['symbol']
        quantity = coin['quantity']
        avg_price = coin['avg_price_eur']
        invested = quantity * avg_price
        
        # Pegar último preço dos dados do analisador
        current_price = None
        if symbol in analyzer.data and not analyzer.data[symbol].empty:
            current_price = analyzer.data[symbol]['Close'].iloc[-1]
            current_value = quantity * current_price
            change_pct = ((current_price - avg_price) / avg_price) * 100
            
            total_invested += invested
            total_current += current_value
            
            portfolio_data.append({
                'symbol': symbol,
                'label': coin['label'],
                'quantity': quantity,
                'avg_price': avg_price,
                'current_price': current_price,
                'invested': invested,
                'current_value': current_value,
                'change_pct': change_pct,
                'profit_loss': current_value - invested
            })
    
    total_change_pct = ((total_current - total_invested) / total_invested * 100) if total_invested > 0 else 0
    
    return html.Div([
        # Resumo geral
        html.Div([
            html.Div([
                html.H3('Total Investido'),
                html.Div(f'€{total_invested:,.2f}', className='summary-value')
            ], className='summary-card'),
            
            html.Div([
                html.H3('Valor Atual'),
                html.Div(f'€{total_current:,.2f}', className='summary-value')
            ], className='summary-card'),
            
            html.Div([
                html.H3('Lucro/Prejuízo'),
                html.Div(
                    f'€{total_current - total_invested:+,.2f}',
                    className=f'summary-value {"trend-up" if total_current >= total_invested else "trend-down"}'
                )
            ], className='summary-card'),
            
            html.Div([
                html.H3('Retorno'),
                html.Div(
                    f'{total_change_pct:+.2f}%',
                    className=f'summary-value {"trend-up" if total_change_pct >= 0 else "trend-down"}'
                )
            ], className='summary-card'),
        ], className='portfolio-overview'),
        
        # Tabela detalhada
        html.Div([
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Criptomoeda'),
                        html.Th('Quantidade'),
                        html.Th('Preço Médio'),
                        html.Th('Preço Atual'),
                        html.Th('Total Investido'),
                        html.Th('Valor Atual'),
                        html.Th('Retorno'),
                        html.Th('Lucro/Prejuízo')
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(f"{item['label']} ({item['symbol']})"),
                        html.Td(f"{item['quantity']:,.8f}"),
                        html.Td(f"€{item['avg_price']:,.8f}"),
                        html.Td(f"€{item['current_price']:,.8f}"),
                        html.Td(f"€{item['invested']:,.2f}"),
                        html.Td(f"€{item['current_value']:,.2f}"),
                        html.Td(
                            f"{item['change_pct']:+.2f}%",
                            className='trend-up' if item['change_pct'] >= 0 else 'trend-down'
                        ),
                        html.Td(
                            f"€{item['profit_loss']:+,.2f}",
                            className='trend-up' if item['profit_loss'] >= 0 else 'trend-down'
                        )
                    ]) for item in portfolio_data
                ])
            ], className='portfolio-table')
        ], className='portfolio-table-container')
    ])

def layout():
    return html.Div([
        # Loader
        html.Div(
            id='loading-overlay',
            className='loading-overlay',
            children=[
                html.Div(className='loading-spinner'),
                html.Div('Carregando dados...', className='loading-text')
            ],
            style={'display': 'none'}
        ),
        
        # Adicionar o componente Interval para atualização automática
        dcc.Interval(
            id='interval-component',
            interval=10*1000,  # em milissegundos (10 segundos)
            n_intervals=0
        ),
        
        html.Div([
            html.H1('Análise de Criptomoedas'),
            html.P('Acompanhamento em tempo real do mercado de criptomoedas')
        ], className='header'),
        
        html.Div([
            # Seção de Portfólio
            html.Div(id='crypto-portfolio-section', className='portfolio-section'),
            
            # Seção de Gráficos
            html.Div([
                html.Div([
                    html.Label('Selecione suas criptomoedas:', className='control-label'),
                    dcc.Dropdown(
                        id='crypto-selector',
                        options=[{
                            'label': f"{coin['label']} ({coin['symbol']})", 
                            'value': coin['symbol']
                        } for coin in CRYPTO_COM_COINS],
                        value=[CRYPTO_COM_COINS[0]['symbol']],
                        multi=True,
                        className='dropdown'
                    ),
                ], className='control-group'),
                
                html.Div([
                    html.Label('Selecione o período:', className='control-label'),
                    dcc.Dropdown(
                        id='period-selector-crypto',
                        options=[
                            {'label': '1 Mês', 'value': '1mo'},
                            {'label': '3 Meses', 'value': '3mo'},
                            {'label': '6 Meses', 'value': '6mo'},
                            {'label': '1 Ano', 'value': '1y'},
                            {'label': '2 Anos', 'value': '2y'}
                        ],
                        value='1y',
                        className='dropdown'
                    ),
                ], className='control-group'),
            ], className='controls-container card'),
            
            html.Div([
                dcc.Graph(id='crypto-graph', className='graph')
            ], className='card graph-container'),
        ], className='container')
    ])

@dash.callback(
    [Output('crypto-graph', 'figure'),
     Output('crypto-portfolio-section', 'children'),
     Output('loading-overlay', 'style')],
    [Input('crypto-selector', 'value'),
     Input('period-selector-crypto', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_page(selected_cryptos, selected_period, n_intervals):
    if not selected_cryptos:
        raise PreventUpdate
        
    # Mostrar loader
    loading_style = {'display': 'flex'}
    
    try:
        # Buscar dados
        analyzer = CryptoAnalyzer(selected_cryptos)
        analyzer.fetch_data(period=selected_period)
        
        portfolio_analyzer = CryptoAnalyzer([coin['symbol'] for coin in CRYPTO_COM_COINS])
        portfolio_analyzer.fetch_data(period='1d')
        
        # Esconder loader
        loading_style = {'display': 'none'}
        
        return analyzer.get_figure(), create_portfolio_summary(portfolio_analyzer), loading_style
    except Exception as e:
        print(f"Erro ao atualizar dados: {str(e)}")
        # Esconder loader em caso de erro
        loading_style = {'display': 'none'}
        return go.Figure(), html.Div("Erro ao carregar dados"), loading_style