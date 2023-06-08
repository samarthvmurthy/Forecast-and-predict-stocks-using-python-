import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta
import requests

# Define the correct username and password
correct_username = "admin"
correct_password = "password"

# Define the layout using Streamlit components
st.title("Stonks20.com")

# Create a login page
login_page = st.beta_container()
dashboard = st.beta_container()

with login_page:
    st.image("https://i.ytimg.com/vi/if-2M3K1tqk/maxresdefault.jpg", use_column_width=True)
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == correct_username and password == correct_password:
            st.success("Login successful!")
            dashboard.write("You can now access other pages.")
            st.session_state["logged_in"] = True
        else:
            st.error("Invalid username or password. Please try again.")

if st.session_state.get("logged_in"):
    with dashboard:
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("", ["Stock Analysis", "News", "Predict"])

        if page == "Stock Analysis":
            st.header("Stock Analysis")
            stock_symbol = st.text_input("Enter the stock symbol:", "AAPL")
            date_range = st.date_input(
                "Select the dates:",
                [(datetime.today() - timedelta(days=365)).date(), datetime.today().date()],
            )
            submit_button = st.button("Submit")

            # Fetch stock data and update the graphs
            if submit_button:
                try:
                    start_date, end_date = date_range
                    stock_data = yf.download(stock_symbol, start=start_date, end=end_date)

                    # Create a Candlestick chart
                    candlestick_fig = go.Figure(
                        data=[
                            go.Candlestick(
                                x=stock_data.index,
                                open=stock_data["Open"],
                                high=stock_data["High"],
                                low=stock_data["Low"],
                                close=stock_data["Close"],
                            )
                        ]
                    )
                    candlestick_fig.update_layout(
                        title=f"{stock_symbol} Stock Price",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        autosize=True,
                    )
                    st.plotly_chart(candlestick_fig)

                    # Create a Volume chart
                    volume_fig = go.Figure(
                        data=[go.Bar(x=stock_data.index, y=stock_data["Volume"])]
                    )
                    volume_fig.update_layout(
                        title="Volume",
                        xaxis_title="Date",
                        yaxis_title="Volume",
                        autosize=True,
                    )
                    st.plotly_chart(volume_fig)

                    # Create a Moving Average chart
                    moving_average_fig = go.Figure(
                        data=[
                            go.Scatter(
                                x=stock_data.index, y=stock_data["Close"], name="Price"
                            ),
                            go.Scatter(
                                x=stock_data.index,
                                y=stock_data["Close"].rolling(window=50).mean(),
                                name="50-day MA",
                            ),
                            go.Scatter(
                                x=stock_data.index,
                                y=stock_data["Close"].rolling(window=200).mean(),
                                name="200-day MA",
                            ),
                        ]
                    )
                    moving_average_fig.update_layout(
                        title="Moving Averages",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        autosize=True,
                    )
                    st.plotly_chart(moving_average_fig)

                    # Create an RSI chart
                    delta = stock_data["Close"].diff()
                    gain = delta.mask(delta < 0, 0)
                    loss = -delta.mask(delta > 0, 0)
                    avg_gain = gain.rolling(window=14).mean()
                    avg_loss = loss.rolling(window=14).mean()
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))

                    rsi_fig = go.Figure(
                        data=[go.Scatter(x=stock_data.index, y=rsi, name="RSI", line=dict(color="blue"))]
                    )
                    rsi_fig.update_layout(
                        title="Relative Strength Index (RSI)",
                        xaxis_title="Date",
                        yaxis_title="RSI",
                        autosize=True,
                    )
                    st.plotly_chart(rsi_fig)

                except Exception as e:
                    st.error(f"Error: {str(e)}")

        elif page == "News":
            st.header("News")
            stock_symbol = st.text_input("Enter the stock symbol:", "AAPL")
            response = requests.get(
                f"https://gnews.io/api/v4/search?q={stock_symbol}&token=09fdb169f86cad27b874f8a4872bd913"
            )
            if response.status_code == 200:
                news_articles = response.json()["articles"]
                if news_articles:
                    for article in news_articles:
                        st.markdown(f"## {article['title']}")
                        st.markdown(article["description"])
                        st.markdown(f"[Read More]({article['url']})")
                else:
                    st.warning("No news articles found for the given stock symbol.")
            else:
                st.error("Failed to fetch news articles. Please check your API key and try again.")

        elif page == "Predict":
            st.header("Predict")
            stock_symbol = st.text_input("Enter the stock symbol:", "AAPL")
            submit_button = st.button("Predict")

            if submit_button:
                try:
                    # Fetch the historical data
                    end_date = datetime.today().date()
                    start_date = end_date - timedelta(days=365)
                    stock_data = yf.download(stock_symbol, start=start_date, end=end_date)

                    # Perform the prediction using moving average
                    closing_prices = stock_data["Close"]
                    prediction_dates = pd.date_range(end=end_date + timedelta(days=10), periods=10, freq="D")
                    predicted_prices = closing_prices.rolling(window=10).mean().iloc[-1]  # Use 10-day moving average for prediction

                    # Create a prediction chart
                    prediction_fig = go.Figure()
                    prediction_fig.add_trace(
                        go.Scatter(x=closing_prices.index, y=closing_prices, name="Actual Prices")
                    )
                    prediction_fig.add_trace(
                        go.Scatter(x=prediction_dates, y=[predicted_prices] * 10, name="Predicted Prices")
                    )
                    prediction_fig.update_layout(
                        title=f"{stock_symbol} Stock Price Prediction",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        autosize=True,
                    )
                    st.plotly_chart(prediction_fig)

                except Exception as e:
                    st.error(f"Error: {str(e)}")
