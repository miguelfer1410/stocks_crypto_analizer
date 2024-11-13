import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from prophet import Prophet
import requests
import time

class StockAnalyzer:
    def __init__(self, symbols=None):
        self.symbols = symbols if symbols else []
        self.data = {}
        self.predictions = {}
        # Buscar taxa de câmbio atual e cachear por 1 hora
        self.last_rate_update = 0
        self.exchange_rates = None
        self._update_exchange_rates()
        
    def _update_exchange_rates(self):
        """Atualiza taxas de câmbio se necessário (cache de 1 hora)"""
        current_time = time.time()
        if not self.exchange_rates or (current_time - self.last_rate_update) > 3600:
            self.exchange_rates = self._get_exchange_rates()
            self.last_rate_update = current_time
    
    def _get_exchange_rates(self):
        """Busca taxas de câmbio atuais"""
        try:
            # Tentar API do BCE (European Central Bank)
            response = requests.get('https://api.exchangerate.host/latest?base=EUR&source=ecb')
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return {
                        'USD': 1/data['rates']['USD'],
                        'GBP': 1/data['rates']['GBP']
                    }
            
            # Fallback para Frankfurter
            response = requests.get('https://api.frankfurter.app/latest')
            if response.status_code == 200:
                data = response.json()
                return {
                    'USD': 1/data['rates']['USD'],
                    'GBP': 1/data['rates']['GBP']
                }
            
        except Exception as e:
            print(f"Erro ao buscar taxas de câmbio: {str(e)}")
        
        # Taxas de fallback mais precisas (atualizadas manualmente)
        return {'USD': 0.9132, 'GBP': 0.8561}
    
    def _convert_to_eur(self, df, symbol):
        """Converte preços para EUR baseado no tipo de ativo"""
        self._update_exchange_rates()  # Atualizar taxas se necessário
        
        if symbol.endswith('.L'):  # ETFs da LSE (em GBP)
            rate = self.exchange_rates['GBP']
        else:  # Ações americanas (em USD)
            rate = self.exchange_rates['USD']
        
        # Criar cópia do DataFrame para evitar modificações no original
        df = df.copy()
        
        # Converter colunas de preço
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in df.columns:
                df[col] = df[col] * rate
        
        # Converter volume para unidades inteiras
        if 'Volume' in df.columns:
            df['Volume'] = df['Volume'].astype(int)
        
        return df
    
    def get_stock_data(self, symbol, period='1d'):
        try:
            ticker = yf.Ticker(symbol)
            
            # Ajustar intervalo baseado no período
            if period == '1d':
                end_time = datetime.now()
                start_time = end_time - timedelta(days=1)
                df = ticker.history(start=start_time, end=end_time, interval='1m')
            elif period == '5d':
                df = ticker.history(period=period, interval='5m')
            elif period in ['1mo', '3mo']:
                df = ticker.history(period=period, interval='15m')
            else:
                df = ticker.history(period=period, interval='1d')
            
            if df.empty:
                print(f"Nenhum dado encontrado para {symbol}")
                return None
            
            # Verificar qualidade dos dados
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                print(f"Dados incompletos para {symbol}")
                return None
            
            if df['Close'].isnull().all():
                print(f"Dados inválidos para {symbol}")
                return None
            
            # Preencher valores nulos com o último valor válido usando ffill()
            df = df.ffill()
            
            return df
            
        except Exception as e:
            print(f"Erro ao obter dados para {symbol}: {str(e)}")
            return None
    
    def fetch_data(self, period='1d'):
        print(f"Tentando buscar dados para: {self.symbols} com período {period}")
        for symbol in self.symbols:
            try:
                df = self.get_stock_data(symbol, period)
                if df is not None:
                    # Converter preços para EUR
                    df = self._convert_to_eur(df, symbol)
                    print(f"Dados obtidos para {symbol}: {len(df)} linhas")
                    self.data[symbol] = df
                else:
                    print(f"Nenhum dado obtido para {symbol}")
            except Exception as e:
                print(f"Erro ao buscar dados para {symbol}: {str(e)}")
        self.calculate_indicators()
    
    def calculate_indicators(self):
        for symbol in self.data:
            df = self.data[symbol]
            if df is None or df.empty:
                continue
            
            # Bandas de Bollinger (20 períodos, 2 desvios padrão)
            df['MA20'] = df['Close'].rolling(window=20).mean()
            std = df['Close'].rolling(window=20).std()
            df['BB_upper'] = df['MA20'] + (std * 2)
            df['BB_lower'] = df['MA20'] - (std * 2)
            
            # MACD (12, 26, 9)
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_histogram'] = df['MACD'] - df['Signal_Line']
            
            # RSI (14 períodos)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Volume Médio Móvel (20 períodos)
            df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
            
            self.data[symbol] = df

    def predict_price(self, symbol, days=30):
        """Faz previsão de preço para os próximos dias"""
        try:
            ticker = yf.Ticker(symbol)
            historical_data = ticker.history(period='2y', interval='1d')
            
            if historical_data.empty:
                print(f"Sem dados históricos para {symbol}")
                return None
            
            # Converter dados históricos para EUR
            historical_data = self._convert_to_eur(historical_data, symbol)
            
            if len(historical_data) < 30:
                print(f"Dados históricos insuficientes para {symbol}")
                return None
            
            prophet_df = pd.DataFrame({
                'ds': historical_data.index.tz_localize(None),
                'y': historical_data['Close']
            }).reset_index(drop=True)
            
            prophet_df = prophet_df.dropna()
            
            if len(prophet_df) < 30:
                print(f"Dados insuficientes após limpeza para {symbol}")
                return None
            
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.01,
                interval_width=0.95
            )
            
            model.add_seasonality(
                name='monthly',
                period=30.5,
                fourier_order=5
            )
            
            model.fit(prophet_df)
            future_dates = model.make_future_dataframe(periods=days, freq='D')
            forecast = model.predict(future_dates)
            
            self.predictions[symbol] = {
                'forecast': forecast,
                'model': model,
                'historical_data': historical_data
            }
            
            return forecast
            
        except Exception as e:
            print(f"Erro na previsão para {symbol}: {str(e)}")
            return None

    def get_figure(self, period='1y'):
        if not self.data:
            return go.Figure()
        
        end_date = datetime.now()
        
        if period == '1mo':
            start_date = end_date.replace(day=1)
        elif period == '3mo':
            start_date = (end_date - timedelta(days=90)).replace(day=1)
        elif period == '6mo':
            start_date = (end_date - timedelta(days=180)).replace(day=1)
        elif period == '1y':
            start_date = (end_date - timedelta(days=365)).replace(day=1)
        elif period == '2y':
            start_date = (end_date - timedelta(days=730)).replace(day=1)
        else:
            start_date = end_date - timedelta(days=365)

        fig = make_subplots(
            rows=5, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.35, 0.15, 0.15, 0.15, 0.2],
            subplot_titles=('Preço e Bandas de Bollinger', 'MACD', 'RSI', 'Volume', 'Previsão')
        )

        colors = ['#00c853', '#2196f3', '#ff9800', '#e91e63', '#9c27b0', '#00bcd4']
        
        for idx, symbol in enumerate(self.data):
            color = colors[idx % len(colors)]
            df = self.data[symbol]
            if df is None or df.empty:
                continue

            # Customizar o formato do hover para o candlestick
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=f"Preço ({symbol})",
                    showlegend=True,
                    text=[
                        f"Data: {x}<br>" +
                        f"Abertura: €{o:.2f}<br>" +
                        f"Máxima: €{h:.2f}<br>" +
                        f"Mínima: €{l:.2f}<br>" +
                        f"Fechamento: €{c:.2f}"
                        for x, o, h, l, c in zip(df.index, df['Open'], df['High'], df['Low'], df['Close'])
                    ],
                    hoverlabel=dict(
                        bgcolor="rgba(0,0,0,0.8)",
                        font_size=12,
                        font_family="Inter",
                        namelength=-1  # Mostra o nome completo
                    )
                ), row=1, col=1
            )
            
            # Customizar hover para MA20 e Bandas de Bollinger
            fig.add_trace(
                go.Scatter(
                    x=df.index, 
                    y=df['MA20'],
                    name=f'MA20 ({symbol})',
                    line=dict(color=color, width=1, dash='dot'),
                    opacity=0.7,
                    text=[f"MA20: €{y:.2f}" for y in df['MA20']],
                    hoverinfo='text+x'
                ), row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df.index, 
                    y=df['BB_upper'],
                    name=f'BB Superior ({symbol})',
                    line=dict(color=color, width=1, dash='dash'),
                    opacity=0.3,
                    text=[f"BB Superior: €{y:.2f}" for y in df['BB_upper']],
                    hoverinfo='text+x'
                ), row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df.index, 
                    y=df['BB_lower'],
                    name=f'BB Inferior ({symbol})',
                    line=dict(color=color, width=1, dash='dash'),
                    opacity=0.3,
                    fill='tonexty',
                    text=[f"BB Inferior: €{y:.2f}" for y in df['BB_lower']],
                    hoverinfo='text+x'
                ), row=1, col=1
            )

            # Customizar hover para MACD
            fig.add_trace(
                go.Scatter(
                    x=df.index, 
                    y=df['MACD'],
                    name=f'MACD ({symbol})',
                    line=dict(color=color, width=1),
                    text=[f"MACD: {y:.4f}" for y in df['MACD']],
                    hoverinfo='text+x'
                ), row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df.index, 
                    y=df['Signal_Line'],
                    name=f'Sinal MACD ({symbol})',
                    line=dict(color=color, width=1, dash='dot'),
                    opacity=0.7,
                    text=[f"Sinal: {y:.4f}" for y in df['Signal_Line']],
                    hoverinfo='text+x'
                ), row=2, col=1
            )

            # Customizar hover para RSI
            fig.add_trace(
                go.Scatter(
                    x=df.index, 
                    y=df['RSI'],
                    name=f'RSI ({symbol})',
                    line=dict(color=color, width=1),
                    text=[f"RSI: {y:.1f}" for y in df['RSI']],
                    hoverinfo='text+x'
                ), row=3, col=1
            )

            # Customizar hover para Volume
            fig.add_trace(
                go.Bar(
                    x=df.index, 
                    y=df['Volume'],
                    name=f'Volume ({symbol})',
                    marker_color=color,
                    opacity=0.7,
                    text=[f"Volume: {y:,.0f}" for y in df['Volume']],
                    hoverinfo='text+x'
                ), row=4, col=1
            )
            
            # Customizar hover para Previsão
            forecast = self.predict_price(symbol)
            if forecast is not None and symbol in self.predictions:
                fig.add_trace(
                    go.Scatter(
                        x=forecast['ds'], 
                        y=forecast['yhat'],
                        name=f'Previsão ({symbol})',
                        line=dict(color=color, dash='dash'),
                        mode='lines',
                        text=[f"Previsão: €{y:.2f}" for y in forecast['yhat']],
                        hoverinfo='text+x'
                    ), row=5, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=forecast['ds'], 
                        y=forecast['yhat_upper'],
                        fill=None,
                        mode='lines',
                        line_color='rgba(0,0,0,0)',
                        showlegend=False,
                        hoverinfo='skip'
                    ), row=5, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=forecast['ds'], 
                        y=forecast['yhat_lower'],
                        fill='tonexty',
                        mode='lines',
                        line_color='rgba(0,0,0,0)',
                        fillcolor=f'rgba({",".join(map(str, hex_to_rgb(color)))},0.2)',
                        name=f'IC ({symbol})',
                        text=[f"Intervalo: €{y:.2f}" for y in forecast['yhat_lower']],
                        hoverinfo='text+x'
                    ), row=5, col=1
                )

        # Adicionar linhas de referência do RSI
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        # Configurar layout
        fig.update_layout(
            title='Análise Técnica de Ações e ETFs',
            template='plotly_dark',
            height=1200,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis_rangeslider_visible=False,
            margin=dict(l=50, r=50, t=50, b=50),
            hoverlabel=dict(
                bgcolor="rgba(0,0,0,0.8)",
                font_size=12,
                font_family="Inter",
                namelength=-1
            ),
            hovermode='x unified',
            uirevision=True,  # Mantém o estado do zoom
            # Configuração correta de transição
            transition={
                'duration': 500,
                'easing': 'cubic-in-out'
            }
        )

        # Atualizar eixos X
        for i in range(1, 6):
            fig.update_xaxes(
                range=[start_date, end_date],
                row=i,
                col=1
            )

        # Atualizar eixos Y
        fig.update_yaxes(title_text="Preço (EUR)", row=1, col=1)
        fig.update_yaxes(title_text="MACD", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)
        fig.update_yaxes(title_text="Volume", row=4, col=1)
        fig.update_yaxes(title_text="Previsão (EUR)", row=5, col=1)

        return fig

def hex_to_rgb(hex_color):
    """Converte cor hexadecimal para RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) 