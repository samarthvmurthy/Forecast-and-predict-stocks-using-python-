import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from newsapi import NewsApiClient
from dash.exceptions import PreventUpdate

# Define the Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the News API client
newsapi = NewsApiClient(api_key='30f892ddb31d43709e5a7a77833f824a')

# Define the layout
app.layout = dbc.Container(
    children=[
        html.H1('Stonks20.com'),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button("Home", id="home-button", color="primary", className="mr-1"),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Button("News", id="news-button", color="primary", className="mr-1"),
                    width="auto"
                ),
                html.Img(src="https://compote.slate.com/images/926e5009-c10a-48fe-b90e-fa0760f82fcd.png?crop=680%2C453%2Cx0%2Cy0", style={'position': 'absolute', 'top': 20, 'right': 20, 'height': '220px', 'width': '300px'})
            ],
            className="mb-3",
        ),
        html.Div(
            children=[
                html.Label('Enter the stock symbol:',style={'font-size': '30px'}),
                dcc.Input(id='stock-input', type='text', value='AAPL',style={'width': '200px','height':'30px','margin-left':'10px'}),
                html.Br(),
                html.Label('Select the dates:',style={'font-size': '30px'}),
                dcc.DatePickerRange(
                    id='date-range',
                    min_date_allowed='2000-01-01',
                    max_date_allowed=pd.Timestamp.today().date(),
                    initial_visible_month=pd.Timestamp.today().date(),
                    start_date=(pd.Timestamp.today() - pd.DateOffset(days=365)).date(),
                    end_date=pd.Timestamp.today().date(),
                    style={'width': '300px', 'height':'30px','margin-left':'10px'}
                ),
                dbc.Button("Submit", id="submit-button", color="primary", className="mt-3", style={'margin-left': '10px'})
            ],
            style={'marginBottom': 20}
        ),
        html.Div(id='news-output', style={'marginBottom': 20}),
        dcc.Graph(id='candlestick-graph'),
        dcc.Graph(id='volume-graph'),
        dcc.Graph(id='moving-average-graph'),
        dcc.Graph(id='rsi-graph'),
    ],
    fluid=True,
    style={'padding': '20px', 'background-color': 'lightblue'}
)


# Callback function to update the stock graphs based on user input
@app.callback(
    [Output('candlestick-graph', 'figure'),
     Output('volume-graph', 'figure'),
     Output('moving-average-graph', 'figure'),
     Output('rsi-graph', 'figure')],
    [Input('submit-button', 'n_clicks')],
    [State('stock-input', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date')]
)
def update_stock_graph(n_clicks, stock_symbol, start_date, end_date):
    if n_clicks is None:
        # Return empty figures if the button hasn't been clicked yet
        return go.Figure(), go.Figure(), go.Figure(), go.Figure()

    try:
        # Fetch stock data from Yahoo Finance within the selected date range
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)

        # Create a Candlestick chart
        candlestick_fig = go.Figure(data=[go.Candlestick(x=stock_data.index,
                                                         open=stock_data['Open'],
                                                         high=stock_data['High'],
                                                         low=stock_data['Low'],
                                                         close=stock_data['Close'])])
        candlestick_fig.update_layout(
            title=f'{stock_symbol} Stock Price',
            xaxis_title='Date',
            yaxis_title='Price',
            autosize=True
        )

        # Create a Volume chart
        volume_fig = go.Figure(data=[go.Bar(x=stock_data.index,
                                            y=stock_data['Volume'])])
        volume_fig.update_layout(
            title='Volume',
            xaxis_title='Date',
            yaxis_title='Volume',
            autosize=True
        )

        # Create a Moving Average chart
        moving_average_fig = go.Figure(data=[
            go.Scatter(x=stock_data.index, y=stock_data['Close'], name='Price'),
            go.Scatter(x=stock_data.index, y=stock_data['Close'].rolling(window=50).mean(), name='50-day MA'),
            go.Scatter(x=stock_data.index, y=stock_data['Close'].rolling(window=200).mean(), name='200-day MA')
        ])
        moving_average_fig.update_layout(
            title='Moving Averages',
            xaxis_title='Date',
            yaxis_title='Price',
            autosize=True
        )

        # Create an RSI chart
        delta = stock_data['Close'].diff()
        gain = delta.mask(delta < 0, 0)
        loss = -delta.mask(delta > 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        rsi_fig = go.Figure(data=[go.Scatter(x=stock_data.index, y=rsi, name='RSI', line=dict(color='blue'))])
        rsi_fig.update_layout(
            title='Relative Strength Index (RSI)',
            xaxis_title='Date',
            yaxis_title='RSI',
            autosize=True
        )

        return candlestick_fig, volume_fig, moving_average_fig, rsi_fig

    except Exception as e:
        error_layout = go.Layout(
            title=f'Error: {str(e)}',
            xaxis_title='Date',
            yaxis_title='Price',
            autosize=True
        )
        error_fig = go.Figure(data=[], layout=error_layout)
        return error_fig, error_fig, error_fig, error_fig


# Callback function to handle the context of the triggered clicks
@app.callback(
    [Output('stock-input', 'value'),
     Output('news-output', 'children')],
    [Input('home-button', 'n_clicks'),
     Input('news-button', 'n_clicks')],
    [State('stock-input', 'value')]
)
def handle_clicks(home_clicks, news_clicks, stock_symbol):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'home-button':
        stock_symbol = 'AAPL'
        news_output = []

    elif trigger_id == 'news-button':
        if not stock_symbol:
            raise PreventUpdate

        # Fetch news articles related to the stock symbol
        news = newsapi.get_everything(q=stock_symbol, language='en', sort_by='publishedAt')

        # Create a list of news article elements
        articles = []
        for article in news['articles']:
            articles.append(html.Div(
                [
                    html.H4(article['title']),
                    html.P(article['description']),
                    html.A('Read More', href=article['url'], target='_blank')
                ],
                style={'marginBottom': 20}
            ))
        
        news_output = articles

    else:
        raise PreventUpdate

    return stock_symbol, news_output


# Callback function to update the background color dynamically
@app.callback(
    [Output('home-button', 'style'),
     Output('news-button', 'style')],
    [Input('home-button', 'n_clicks'),
     Input('news-button', 'n_clicks')]
)
def update_button_style(home_clicks, news_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'home-button':
        return {'background-color': 'lightblue'}, {'background-color': ''}

    elif trigger_id == 'news-button':
        return {'background-color': ''}, {'background-color': 'lightblue'}

    else:
        raise PreventUpdate

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
