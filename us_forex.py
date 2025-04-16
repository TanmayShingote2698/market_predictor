import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
import requests
import time
import threading

# --- Functions ---
# Fetch live price from CoinGecko
def get_live_price(symbol):
    cg = CoinGeckoAPI()
    coin_id = symbol.lower()
    try:
        data = cg.get_price(ids=coin_id, vs_currencies='usd')
        return data[coin_id]['usd'] if coin_id in data else None
    except Exception as e:
        print(f"Error fetching live price from CoinGecko: {e}")
        return None

# Fetch live price from Alpha Vantage for BTC/XAU, XAU/USD, ETH/USD
def get_alpha_vantage_price(from_currency, to_currency):
    ALPHA_VANTAGE_API_KEY = 'MKT0GGOLQOGFH753'  # Replace with your API key
    url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={ALPHA_VANTAGE_API_KEY}"
    
    response = requests.get(url)
    data = response.json()
    
    if "Realtime Currency Exchange Rate" in data:
        price = data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
        return float(price)
    else:
        return None

# Fetch historical data from Yahoo Finance
def get_price_data(symbol, start, end):
    historical_data = yf.download(symbol, start=start, end=end, auto_adjust=True)
    return historical_data

# Fetch historical data for XAU/USD from Alpha Vantage
def get_xau_usd_data(start, end):
    ALPHA_VANTAGE_API_KEY = 'MKT0GGOLQOGFH753'  # Replace with your API key
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=XAUUSD=X&apikey={ALPHA_VANTAGE_API_KEY}"
    
    response = requests.get(url)
    data = response.json()
    
    if "Time Series (Daily)" in data:
        time_series = data["Time Series (Daily)"]
        dates = []
        close_prices = []
        
        for date, stats in time_series.items():
            dates.append(date)
            close_prices.append(float(stats["4. close"]))  # Closing price
        
        # Create a DataFrame from the fetched data
        xau_data = pd.DataFrame({
            'Date': pd.to_datetime(dates),
            'Close': close_prices
        })
        
        # Set the date column as the index
        xau_data.set_index('Date', inplace=True)
        
        # Filter data between the start and end date
        xau_data = xau_data.loc[start:end]
        return xau_data
    else:
        return None

# Intraday Strategy (EMA 3 & EMA 5)
def intraday_strategy(data):
    # Calculate short-term EMAs (for fast trading)
    data['EMA_3'] = data['Close'].ewm(span=3, adjust=False).mean()
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()

    latest_price = float(data['Close'].iloc[-1])
    ema_3 = float(data['EMA_3'].iloc[-1])
    ema_5 = float(data['EMA_5'].iloc[-1])

    signal = ""
    stop_loss_pct = 0.01  # 1% loss for intraday
    profit_pct = stop_loss_pct * 1.5  # 1.5% profit for intraday

    if ema_3 > ema_5:
        signal = "Buy"
        target_price = latest_price * (1 + profit_pct)
        stop_loss = latest_price * (1 - stop_loss_pct)
    elif ema_3 < ema_5:
        signal = "Sell"
        target_price = latest_price * (1 - profit_pct)
        stop_loss = latest_price * (1 + stop_loss_pct)
    else:
        signal = "Hold"
        target_price = latest_price
        stop_loss = latest_price

    return signal, round(target_price, 2), round(stop_loss, 2)

# Long-term Strategy (Trend Following with EMA 200)
def longterm_strategy(data):
    latest_price = float(data['Close'].iloc[-1])
    ema_200_series = data['Close'].ewm(span=200, adjust=False).mean()
    ema_200 = float(ema_200_series.iloc[-1])

    stop_loss_pct = 0.03  # 3% loss for long-term
    profit_pct = stop_loss_pct * 3  # 9% profit for long-term

    if latest_price > ema_200:
        signal = "Buy"
        target_price = latest_price * (1 + profit_pct)
        stop_loss = latest_price * (1 - stop_loss_pct)
    elif latest_price < ema_200:
        signal = "Sell"
        target_price = latest_price * (1 - profit_pct)
        stop_loss = latest_price * (1 + stop_loss_pct)
    else:
        signal = "Hold"
        target_price = latest_price
        stop_loss = latest_price

    return signal, round(target_price, 2), round(stop_loss, 2)

# --- Streamlit Interface ---
st.set_page_config(page_title="Smart Profit Predictor", layout="wide")
st.title("📈 Smart Profit Predictor")

# Sidebar for Asset Selection
st.sidebar.title("Asset Selection")
asset_choice = st.sidebar.selectbox("Choose an asset:", (
    "Bitcoin (BTC-USD)",
    "Gold (XAU/USD)",
    "Silver (SI=F)",
    "Crude Oil (CL=F)",
    "EUR/USD (EURUSD=X)",
    "BTC/XAU (BTC=XAU)",
    "ETH/USD (ETH-USD)"
))

symbol_map = {
    "Bitcoin (BTC-USD)": "BTC-USD",
    "Gold (XAU/USD)": "XAUUSD=X",  # XAU/USD for Gold
    "Silver (SI=F)": "SI=F",
    "Crude Oil (CL=F)": "CL=F",
    "EUR/USD (EURUSD=X)": "EURUSD=X",
    "BTC/XAU (BTC=XAU)": "BTC-XAU",  # BTC/XAU exchange rate
    "ETH/USD (ETH-USD)": "ETH-USD"   # ETH/USD exchange rate
}

symbol = symbol_map[asset_choice]

# Choose between Intraday and Long-term
strategy_type = st.sidebar.selectbox("Choose Strategy Type:", ("Intraday", "Long-term"))

# Define date range
days = st.sidebar.slider("Select number of days:", 7, 90, 30)
end_date = datetime.now()
start_date = end_date - timedelta(days=days)

# Fetch data
if asset_choice == "Gold (XAU/USD)":
    data = get_xau_usd_data(start=start_date, end=end_date)
else:
    data = get_price_data(symbol, start=start_date, end=end_date)

if data is None or data.empty:
    st.error(f"No data found for {asset_choice}.")
else:
    st.line_chart(data['Close'])

    # Get live price based on the selected asset
    if asset_choice == "Bitcoin (BTC-USD)":
        live_price = get_live_price("bitcoin")
    elif asset_choice == "ETH/USD (ETH-USD)":
        live_price = get_live_price("ethereum")
    elif asset_choice == "Gold (XAU/USD)":
        live_price = get_alpha_vantage_price("XAU", "USD")
    elif asset_choice == "BTC/XAU (BTC=XAU)":
        live_price = get_alpha_vantage_price("BTC", "XAU")
    else:
        live_price = get_live_price(symbol.split('-')[0].lower())

    if live_price:
        st.subheader(f"Live Price: ${live_price}")

    # Choose Strategy Logic
    if strategy_type == "Intraday":
        signal, target_price, stop_loss = intraday_strategy(data)
    elif strategy_type == "Long-term":
        signal, target_price, stop_loss = longterm_strategy(data)

    # Display results
    st.subheader(f"📊 {strategy_type} Strategy Results")
    st.metric("Signal", signal)
    st.metric("Target Price", f"${target_price:.2f}")
    st.metric("Stop Loss", f"${stop_loss:.2f}")

    # Sending email alert for actions
    if signal in ["Buy", "Sell"]:
        st.success(f"Action: {signal} | Target: {target_price} | Stop-Loss: {stop_loss}")

# --- Continuous Run with Threading ---
def run_continuous():
    while True:
        # Fetch the data and apply strategy every minute (for intraday) or daily (for long-term)
        data = get_price_data(symbol, start=start_date, end=end_date)
        
        if data.empty:
            st.error(f"No data found for {symbol}.")
            return

        if strategy_type == "Intraday":
            signal, target_price, stop_loss = intraday_strategy(data)
        elif strategy_type == "Long-term":
            signal, target_price, stop_loss = longterm_strategy(data)
        
        # Placeholder for email alert
        if signal in ["Buy", "Sell"]:
            # Placeholder email alert
            pass
        
        # Sleep for 60 seconds (for intraday) or set for longer intervals for long-term strategies
        time.sleep(60)  # Adjust time for long-term strategies

# Run continuous process in a separate thread
if 'thread' not in st.session_state:
    thread = threading.Thread(target=run_continuous, daemon=True)
    thread.start()
    st.session_state['thread'] = thread
