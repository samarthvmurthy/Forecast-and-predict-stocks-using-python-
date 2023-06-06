import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta
import requests
import sqlite3

# Establish a connection to the SQLite database
conn = sqlite3.connect('user_credentials.db')
cursor = conn.cursor()

# Create a table to store user credentials if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
conn.commit()

# Define the layout using Streamlit components
st.title("Stonks20.com")
st.sidebar.text("")  # Add some spacing

# Add username and password input fields
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

# Check if the user is logged in
if st.sidebar.button("Login"):
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    if result and result[1] == password:
        st.sidebar.success("Login successful!")
        st.sidebar.info("You can now access other pages.")
        st.session_state["logged_in"] = True
    else:
        st.sidebar.error("Invalid username or password. Please try again.")

# Add a register button
if st.sidebar.button("Register as a New User"):
    signup_username = st.sidebar.text_input("New Username")
    signup_password = st.sidebar.text_input("New Password", type="password")
    if signup_username and signup_password:
        cursor.execute("SELECT * FROM users WHERE username=?", (signup_username,))
        result = cursor.fetchone()
        if result:
            st.sidebar.error("Username already exists. Please choose a different username.")
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (signup_username, signup_password))
            conn.commit()
            st.sidebar.success("Registration successful! Please log in with your new credentials.")
    else:
        st.sidebar.warning("Please enter a username and password.")

# Add a logout button to the top right corner
if st.sidebar.button("Logout"):
    st.session_state.pop("logged_in")
    st.sidebar.success("Logged out successfully!")

def write_user_credentials(username, password):
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

def read_user_credentials():
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    user_credentials = {row[0]: row[1] for row in rows}
    return user_credentials

# Rest of the code remains the same

if st.session_state.get("logged_in"):
    page = st.sidebar.radio("Navigation", ["Stock Analysis", "News"])

    if page == "Stock Analysis":
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

                # Rest of the code remains the same

            except Exception as e:
                st.error(f"Error: {str(e)}")

    elif page == "News":
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
else:
    image_url = "https://i.ytimg.com/vi/if-2M3K1tqk/maxresdefault.jpg"  # Replace with your image URL
    st.image(image_url, use_column_width=True)
