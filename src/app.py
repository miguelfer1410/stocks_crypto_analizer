from dash import Dash, html, dcc, Input, Output
from crypto_analyzer import CryptoAnalyzer
import webbrowser
from threading import Timer
import requests

# Dicionário com explicações dos indicadores
INDICATOR_EXPLANATIONS = {
    'price': '''
    ### Preço e Bandas de Bollinger
    - **Preço**: Valor atual da criptomoeda em USD
    - **Bandas de Bollinger**: Indicador de volatilidade que consiste em:
        - Linha média (MA20)
        - Banda superior (MA20 + 2×desvio padrão)
        - Banda inferior (MA20 - 2×desvio padrão)
    
    **Como interpretar**:
    - Preço próximo à banda superior: Possível sobrecompra
    - Preço próximo à banda inferior: Possível sobrevenda
    - Bandas se estreitando: Possível movimento forte se aproximando
    ''',
    
    'macd': '''
    ### MACD (Moving Average Convergence Divergence)
    - **Linha MACD**: Diferença entre médias móveis exponenciais de 12 e 26 períodos
    - **Linha de Sinal**: Média móvel exponencial de 9 períodos do MACD
    - **Histograma**: Diferença entre MACD e Linha de Sinal
    
    **Como interpretar**:
    - MACD cruza acima da linha de sinal: Sinal de compra
    - MACD cruza abaixo da linha de sinal: Sinal de venda
    - Divergências entre preço e MACD: Possível reversão de tendência
    ''',
    
    'rsi': '''
    ### RSI (Relative Strength Index)
    Indicador de momentum que mede a velocidade e magnitude das mudanças de preço.
    - Oscila entre 0 e 100
    - Linha 70: Região de sobrecompra
    - Linha 30: Região de sobrevenda
    
    **Como interpretar**:
    - RSI > 70: Ativo possivelmente sobrecomprado
    - RSI < 30: Ativo possivelmente sobrevendido
    - Divergências entre RSI e preço podem indicar reversões
    ''',
    
    'volume': '''
    ### Volume
    Quantidade de ativos negociados em um período.
    - Inclui média móvel de 20 períodos do volume
    
    **Como interpretar**:
    - Volume alto: Confirma força do movimento atual
    - Volume baixo: Sugere movimento menos confiável
    - Volume crescente em tendência: Confirma tendência
    - Volume diminuindo em tendência: Possível reversão
    '''
}

def open_browser():
    webbrowser.open('http://127.0.0.1:8050/')

# Função para obter taxa de câmbio USD/EUR
def get_usd_eur_rate():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        data = response.json()
        return data['rates']['EUR']
    except:
        return 0.93  # Taxa aproximada caso a API falhe

# Lista atualizada com os símbolos corretos
CRYPTO_COM_COINS = [
    {'symbol': 'CRO', 'label': 'Cronos', 'balance': 424.02, 'invested_eur': 24.28},
    {'symbol': 'BTC', 'label': 'Bitcoin', 'balance': 0.0004657, 'invested_eur': 29.45},
    {'symbol': 'ETH', 'label': 'Ethereum', 'balance': 0.01177, 'invested_eur': 28.88},
    {'symbol': 'SHIB', 'label': 'Shiba Inu', 'balance': 1334000.0, 'invested_eur': 24.27},
    {'symbol': 'DOGE', 'label': 'Dogecoin', 'balance': 149.7, 'invested_eur': 29.16},
    {'symbol': 'SOL', 'label': 'Solana', 'balance': 0.1674, 'invested_eur': 24.06},
    {'symbol': 'ADA', 'label': 'Cardano', 'balance': 69.1, 'invested_eur': 24.33},
    {'symbol': 'RAY', 'label': 'Raydium', 'balance': 14.32, 'invested_eur': 29.75},
    {'symbol': 'AVAX', 'label': 'Avalanche', 'balance': 1.104, 'invested_eur': 29.02},
    {'symbol': 'AERO29270', 'label': 'Aerodrome', 'balance': 23.08, 'invested_eur': 29.54},
    {'symbol': 'LINK', 'label': 'Chainlink', 'balance': 3.512, 'invested_eur': 39.51},
    {'symbol': 'XRP', 'label': 'XRP', 'balance': 58.99, 'invested_eur': 29.83},
    {'symbol': 'USDT', 'label': 'Tether USDT', 'balance': 26.09, 'invested_eur': 24.33},
    {'symbol': 'ONDO', 'label': 'Ondo', 'balance': 36.88, 'invested_eur': 24.78},
    {'symbol': 'JASMY', 'label': 'JasmyCoin', 'balance': 1419, 'invested_eur': 29.16},
    {'symbol': 'TAO22974', 'label': 'Bittensor', 'balance': 0.04488, 'invested_eur': 24.07},
]

# Inicializa o analisador com as criptomoedas da Crypto.com
analyzer = CryptoAnalyzer([coin['symbol'] for coin in CRYPTO_COM_COINS[:2]])  # Começa com as 2 primeiras
analyzer.fetch_data()
analyzer.calculate_indicators()

# Cria a aplicação Dash
app = Dash(__name__)

# Função para calcular valor total da carteira
def get_portfolio_summary(analyzer):
    summary = []
    total_eur = 0
    total_invested = 0
    eur_rate = get_usd_eur_rate()
    
    for coin in CRYPTO_COM_COINS:
        symbol = coin['symbol']
        balance = coin['balance']
        invested = coin['invested_eur']
        total_invested += invested
        
        try:
            if symbol in analyzer.data and not analyzer.data[symbol].empty and len(analyzer.data[symbol]) >= 2:
                current_price_usd = analyzer.data[symbol]['Close'].iloc[-1]
                previous_price_usd = analyzer.data[symbol]['Close'].iloc[-2]
                current_price_eur = current_price_usd * eur_rate
                value_eur = balance * current_price_eur
                
                profit_eur = value_eur - invested
                profit_percentage = ((value_eur - invested) / invested * 100) if invested > 0 else 0
                
                change_24h = ((current_price_usd - previous_price_usd) / previous_price_usd * 100)
                
                summary.append({
                    'symbol': symbol,
                    'label': coin['label'],
                    'balance': balance,
                    'price_eur': current_price_eur,
                    'value_eur': value_eur,
                    'invested_eur': invested,
                    'profit_eur': profit_eur,
                    'profit_percentage': profit_percentage,
                    'change_24h': change_24h
                })
                
                total_eur += value_eur
            else:
                # Se não houver dados, adicionar com valores zerados
                summary.append({
                    'symbol': symbol,
                    'label': coin['label'],
                    'balance': balance,
                    'price_eur': 0,
                    'value_eur': 0,
                    'invested_eur': invested,
                    'profit_eur': -invested,  # Todo o investimento é considerado perdido
                    'profit_percentage': -100,
                    'change_24h': 0
                })
                print(f"Aviso: Dados insuficientes para {symbol}")
        except Exception as e:
            print(f"Erro ao processar {symbol}: {str(e)}")
            # Adicionar a moeda com valores zerados em caso de erro
            summary.append({
                'symbol': symbol,
                'label': coin['label'],
                'balance': balance,
                'price_eur': 0,
                'value_eur': 0,
                'invested_eur': invested,
                'profit_eur': -invested,
                'profit_percentage': -100,
                'change_24h': 0
            })
    
    total_profit = total_eur - total_invested
    total_profit_percentage = ((total_eur - total_invested) / total_invested * 100) if total_invested > 0 else 0
    
    return summary, total_eur, total_invested, total_profit, total_profit_percentage

# Define o layout
app.layout = html.Div([
    html.Div([
        # Cabeçalho
        html.Div([
            html.H1('Análise de Carteira Crypto.com'),
            html.P('Acompanhamento em tempo real da sua carteira de criptomoedas')
        ], className='header'),
        
        # Resumo da carteira
        html.Div([
            html.Div([
                html.H2('Resumo da Carteira', className='section-title'),
                html.Div(id='portfolio-summary', className='portfolio-summary'),
            ], className='card'),
            
            # Container principal
            html.Div([
                # Coluna da esquerda - Controles e gráfico
                html.Div([
                    # Controles
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
                                id='period-selector',
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
                    
                    # Gráfico
                    html.Div([
                        dcc.Graph(id='crypto-graph', className='graph')
                    ], className='card graph-container'),
                ], className='left-column'),
                
                # Coluna da direita - Guia e dicas
                html.Div([
                    html.Div([
                        html.H2('Guia de Indicadores', className='section-title'),
                        dcc.Tabs([
                            dcc.Tab(
                                label='Preço/BB',
                                children=[dcc.Markdown(INDICATOR_EXPLANATIONS['price'])],
                                className='custom-tab',
                                selected_className='custom-tab--selected'
                            ),
                            dcc.Tab(
                                label='MACD',
                                children=[dcc.Markdown(INDICATOR_EXPLANATIONS['macd'])],
                                className='custom-tab',
                                selected_className='custom-tab--selected'
                            ),
                            dcc.Tab(
                                label='RSI',
                                children=[dcc.Markdown(INDICATOR_EXPLANATIONS['rsi'])],
                                className='custom-tab',
                                selected_className='custom-tab--selected'
                            ),
                            dcc.Tab(
                                label='Volume',
                                children=[dcc.Markdown(INDICATOR_EXPLANATIONS['volume'])],
                                className='custom-tab',
                                selected_className='custom-tab--selected'
                            ),
                        ], className='custom-tabs'),
                    ], className='card guide-container'),
                    
                    # Dicas e alertas
                    html.Div([
                        html.H3('Alertas e Recomendações', className='section-title'),
                        html.Div(id='alerts-container', className='alerts-container')
                    ], className='card')
                ], className='right-column'),
            ], className='main-container')
        ], className='container')
    ], className='app-container')
])

@app.callback(
    Output('crypto-graph', 'figure'),
    [Input('crypto-selector', 'value'),
     Input('period-selector', 'value')]
)
def update_graph(selected_cryptos, selected_period):
    analyzer = CryptoAnalyzer(selected_cryptos)
    analyzer.fetch_data(period=selected_period)
    analyzer.calculate_indicators()
    return analyzer.get_figure()

@app.callback(
    Output('portfolio-summary', 'children'),
    [Input('crypto-selector', 'value')]
)
def update_portfolio_summary(selected_cryptos):
    try:
        analyzer = CryptoAnalyzer([coin['symbol'] for coin in CRYPTO_COM_COINS])
        analyzer.fetch_data(period='1d')
        
        summary, total_eur, total_invested, total_profit, total_profit_percentage = get_portfolio_summary(analyzer)
        
        return [
            # Cards de resumo
            html.Div([
                html.Div([
                    html.H3('Valor Total'),
                    html.Div(f'€{total_eur:,.2f}', className='summary-value')
                ], className='summary-card'),
                
                html.Div([
                    html.H3('Total Investido'),
                    html.Div(f'€{total_invested:,.2f}', className='summary-value')
                ], className='summary-card'),
                
                html.Div([
                    html.H3('Lucro/Prejuízo'),
                    html.Div(
                        f'€{total_profit:+,.2f}',
                        className=f'summary-value {"trend-up" if total_profit >= 0 else "trend-down"}'
                    )
                ], className='summary-card'),
                
                html.Div([
                    html.H3('Retorno'),
                    html.Div(
                        f'{total_profit_percentage:+.2f}%',
                        className=f'summary-value {"trend-up" if total_profit_percentage >= 0 else "trend-down"}'
                    )
                ], className='summary-card'),
            ], className='portfolio-overview'),
            
            # Tabela detalhada
            html.Div([
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th('Moeda'),
                            html.Th('Quantidade'),
                            html.Th('Preço (EUR)'),
                            html.Th('Valor (EUR)'),
                            html.Th('Investido'),
                            html.Th('Lucro/Prejuízo'),
                            html.Th('24h %')
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(f"{coin['label']} ({coin['symbol']})"),
                            html.Td(f"{coin['balance']:,.8f}"),
                            html.Td(f"€{coin['price_eur']:,.2f}"),
                            html.Td(f"€{coin['value_eur']:,.2f}"),
                            html.Td(f"€{coin['invested_eur']:,.2f}"),
                            html.Td(
                                f"€{coin['profit_eur']:+,.2f} ({coin['profit_percentage']:+.2f}%)",
                                className='trend-up' if coin['profit_eur'] >= 0 else 'trend-down'
                            ),
                            html.Td(
                                f"{coin['change_24h']:+.2f}%" if coin['price_eur'] > 0 else "N/A",
                                className='trend-up' if coin['change_24h'] > 0 else 'trend-down'
                            )
                        ]) for coin in summary
                    ])
                ], className='portfolio-table')
            ], className='portfolio-table-container')
        ]
    except Exception as e:
        print(f"Erro ao atualizar resumo: {str(e)}")
        return html.Div("Erro ao carregar dados. Por favor, tente novamente.", className='error-message')

def update_crypto_data(symbol):
    try:
        analyzer = CryptoAnalyzer()
        df = analyzer.get_crypto_data(symbol)
        
        if df is not None and not df.empty:
            # Processar dados normalmente
            return create_figure(df, symbol)
        else:
            return {
                'data': [],
                'layout': {
                    'title': f'Dados não disponíveis para {symbol}',
                    'xaxis': {'title': 'Data'},
                    'yaxis': {'title': 'Preço (USD)'}
                }
            }
    except Exception as e:
        print(f"Erro ao processar {symbol}: {str(e)}")
        return {
            'data': [],
            'layout': {
                'title': f'Erro ao processar dados para {symbol}',
                'xaxis': {'title': 'Data'},
                'yaxis': {'title': 'Preço (USD)'}
            }
        }

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=False)