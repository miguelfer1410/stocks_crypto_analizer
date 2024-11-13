from crypto_analyzer import CryptoAnalyzer
from stock_analyzer import StockAnalyzer
import dash
from dash import html, dcc
import sys

app = dash.Dash(__name__, use_pages=True)

app.layout = html.Div([
    html.Nav([
        html.Ul([
            html.Li(
                dcc.Link(
                    f"{page['name']}", 
                    href=page["relative_path"]
                )
            )
            for page in dash.page_registry.values()
        ])
    ]),
    dash.page_container
])

def main():
    try:
        app.run_server(debug=True)
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 