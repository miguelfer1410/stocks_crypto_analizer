from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash
from stock_analyzer import StockAnalyzer
from dash.exceptions import PreventUpdate

# Lista personalizada de ações e ETFs com quantidade e preço médio de compra
MY_STOCKS = [
    {'symbol': 'BAC', 'label': 'Bank of America', 'quantity': 0.716679, 'avg_price': 41.87},
    {'symbol': 'CNDX.L', 'label': 'iShares NASDAQ 100', 'quantity': 0.02828628, 'avg_price': 1059.2},
    {'symbol': 'IUIT.L', 'label': 'iShares S&P 500 IT', 'quantity': 1, 'avg_price': 30.53},
    {'symbol': 'MSTR', 'label': 'MicroStrategy', 'quantity': 0.1981424, 'avg_price': 242.15},
    {'symbol': 'NOC', 'label': 'Northrop Grumman', 'quantity': 0.0922378, 'avg_price': 491.23},
    {'symbol': 'NVDA', 'label': 'Nvidia', 'quantity': 0.2317619, 'avg_price': 127.24},
    {'symbol': 'PLTR', 'label': 'Palantir', 'quantity': 0.57801, 'avg_price': 51.82},
    {'symbol': 'VLO', 'label': 'Valero Energy', 'quantity': 0.2330904, 'avg_price': 128.75},
]

dash.register_page(
    __name__,
    path='/stocks',
    title='Análise de Ações e ETFs',
    name='Ações e ETFs'
)

def create_portfolio_summary(analyzer):
    """Cria o resumo do portfólio com valores atuais"""
    total_invested = 0
    total_current = 0
    portfolio_data = []
    
    for stock in MY_STOCKS:
        symbol = stock['symbol']
        quantity = stock['quantity']
        avg_price = stock['avg_price']
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
                'label': stock['label'],
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
                        html.Th('Ativo'),
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
                        html.Td(f"{item['quantity']:,.0f}"),
                        html.Td(f"€{item['avg_price']:,.2f}"),
                        html.Td(f"€{item['current_price']:,.2f}"),
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
            id='loading-overlay-stocks',
            className='loading-overlay',
            children=[
                html.Div(className='loading-spinner'),
                html.Div('Carregando dados...', className='loading-text')
            ],
            style={'display': 'none'}
        ),
        
        # Adicionar o componente Interval para atualização automática
        dcc.Interval(
            id='interval-component-stocks',
            interval=10*1000,  # em milissegundos (10 segundos)
            n_intervals=0
        ),
        
        html.Div([
            html.H1('Análise de Ações e ETFs'),
            html.P('Acompanhamento em tempo real da sua carteira de ações e ETFs')
        ], className='header'),
        
        html.Div([
            # Seção de Portfólio
            html.Div(id='portfolio-section', className='portfolio-section'),
            
            # Seção de Gráficos
            html.Div([
                html.Div([
                    html.Label('Selecione seus ativos:', className='control-label'),
                    dcc.Dropdown(
                        id='stock-selector',
                        options=[{
                            'label': f"{stock['label']} ({stock['symbol']})", 
                            'value': stock['symbol']
                        } for stock in MY_STOCKS],
                        value=[MY_STOCKS[0]['symbol']],
                        multi=True,
                        className='dropdown'
                    ),
                ], className='control-group'),
                
                html.Div([
                    html.Label('Selecione o período:', className='control-label'),
                    dcc.Dropdown(
                        id='period-selector-stocks',
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
                dcc.Graph(id='stock-graph', className='graph')
            ], className='card graph-container'),
        ], className='container')
    ])

@dash.callback(
    [Output('stock-graph', 'figure'),
     Output('portfolio-section', 'children'),
     Output('loading-overlay-stocks', 'style')],
    [Input('stock-selector', 'value'),
     Input('period-selector-stocks', 'value'),
     Input('interval-component-stocks', 'n_intervals')]
)
def update_page(selected_stocks, selected_period, n_intervals):
    if not selected_stocks:
        raise PreventUpdate
        
    # Mostrar loader
    loading_style = {'display': 'flex'}
    
    try:
        # Buscar dados
        analyzer = StockAnalyzer(selected_stocks)
        analyzer.fetch_data(period=selected_period)
        
        portfolio_analyzer = StockAnalyzer([stock['symbol'] for stock in MY_STOCKS])
        portfolio_analyzer.fetch_data(period='1d')
        
        # Esconder loader
        loading_style = {'display': 'none'}
        
        return analyzer.get_figure(), create_portfolio_summary(portfolio_analyzer), loading_style
    except Exception as e:
        print(f"Erro ao atualizar dados: {str(e)}")
        # Esconder loader em caso de erro
        loading_style = {'display': 'none'}
        return go.Figure(), html.Div("Erro ao carregar dados"), loading_style