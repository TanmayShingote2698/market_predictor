import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
import time
import threading

# --- Functions ---
# Fetch live price from CoinGecko
@st.cache_data(ttl=30) 
def get_live_price(symbol):
    cg = CoinGeckoAPI()
    coin_id = symbol.lower()
    try:
        data = cg.get_price(ids=coin_id, vs_currencies='usd')
        return data[coin_id]['usd'] if coin_id in data else None
    except Exception as e:
        print(f"Error fetching live price from CoinGecko: {e}")
        return None

# Get historical data
def get_price_data(symbol, start, end):
    historical_data = yf.download(symbol, start=start, end=end, auto_adjust=True)
    return historical_data

# Intraday Strategy (EMA 3 & EMA 5)
def intraday_strategy(data):
    data['EMA_3'] = data['Close'].ewm(span=3, adjust=False).mean()
    data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()

    latest_price = float(data['Close'].iloc[-1])
    ema_3 = float(data['EMA_3'].iloc[-1])
    ema_5 = float(data['EMA_5'].iloc[-1])

    signal = ""
    stop_loss_pct = 0.01
    profit_pct = stop_loss_pct * 1.5

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

# Long-term Strategy (EMA 200)
def longterm_strategy(data):
    data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()

    latest_price = float(data['Close'].iloc[-1])
    ema_200 = float(data['EMA_200'].iloc[-1])

    stop_loss_pct = 0.03
    profit_pct = stop_loss_pct * 3

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
    "Gold (GC=F)",
    "Silver (SI=F)",
    "Crude Oil (CL=F)",
    "EUR/USD (EURUSD=X)"
))

symbol_map = {
    "Bitcoin (BTC-USD)": "BTC-USD",
    "Gold (GC=F)": "GC=F",
    "Silver (SI=F)": "SI=F",
    "Crude Oil (CL=F)": "CL=F",
    "EUR/USD (EURUSD=X)": "EURUSD=X"
}

symbol = symbol_map[asset_choice]

# Choose Strategy
strategy_type = st.sidebar.selectbox("Choose Strategy Type:", ("Intraday", "Long-term"))

# Date Range
days = st.sidebar.slider("Select number of days:", 7, 90, 30)
end_date = datetime.now()
start_date = end_date - timedelta(days=days)

# Get Data
data = get_price_data(symbol, start=start_date, end=end_date)

if data.empty:
    st.error("No data found for this asset.")
else:
    st.line_chart(data['Close'])

    # Live price
    live_price = get_live_price("bitcoin" if "BTC-USD" in symbol else "ethereum")
    if live_price:
        st.subheader(f"Live Price: ${live_price}")

    # Strategy result
    if strategy_type == "Intraday":
        signal, target_price, stop_loss = intraday_strategy(data)
    elif strategy_type == "Long-term":
        signal, target_price, stop_loss = longterm_strategy(data)

    st.subheader(f"📊 {strategy_type} Strategy Results")
    st.metric("Signal", signal)
    st.metric("Target Price", f"${target_price:.2f}")
    st.metric("Stop Loss", f"${stop_loss:.2f}")

    if signal in ["Buy", "Sell"]:
        st.success(f"Action: {signal} | Target: {target_price} | Stop-Loss: {stop_loss}")

# --- Background Task for Continuous Monitoring ---
def run_continuous():
    while True:
        data = get_price_data(symbol, start=start_date, end=end_date)
        if strategy_type == "Intraday":
            signal, target_price, stop_loss = intraday_strategy(data)
        elif strategy_type == "Long-term":
            signal, target_price, stop_loss = longterm_strategy(data)

        # Add alert or logging here if needed
        time.sleep(60)

thread = threading.Thread(target=run_continuous, daemon=True)
thread.start()
