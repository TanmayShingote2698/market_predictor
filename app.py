import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timedelta
from pycoingecko import CoinGeckoAPI
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

# Get historical data
def get_price_data(symbol, start, end):
    historical_data = yf.download(symbol, start=start, end=end, auto_adjust=True)
    return historical_data

# Intraday Strategy (EMA 7 & EMA 21)
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

# Choose between Intraday and Long-term
strategy_type = st.sidebar.selectbox("Choose Strategy Type:", ("Intraday", "Long-term"))

# Define date range
days = st.sidebar.slider("Select number of days:", 7, 90, 30)
end_date = datetime.now()
start_date = end_date - timedelta(days=days)

# Fetch data
data = get_price_data(symbol, start=start_date, end=end_date)

if data.empty:
    st.error("No data found for this asset.")
else:
    st.line_chart(data['Close'])

    # Get live price
    live_price = get_live_price("bitcoin" if "BTC-USD" in symbol else "ethereum")
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
        # Placeholder for email alert function (set it up with your own function)

# --- Continuous Run with Threading ---
def run_continuous():
    while True:
        # Fetch the data and apply strategy every minute (for intraday) or daily (for long-term)
        data = get_price_data(symbol, start=start_date, end=end_date)
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
thread = threading.Thread(target=run_continuous, daemon=True)
thread.start()

