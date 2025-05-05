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

# Compute RSI (Relative Strength Index)
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Handling NaN values during rolling mean calculation
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # Return only non-NaN RSI values
    return rsi


# Compute ATR (Average True Range)
def compute_atr(data, period=14):
    high = data['High']
    low = data['Low']
    close = data['Close']

    # Calculate True Range (TR)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR with a rolling window
    atr = tr.rolling(window=period, min_periods=1).mean()
    
    return atr


# Intraday Strategy (EMA 10 & EMA 30 with RSI and ATR)
# Intraday Strategy (EMA 10 & EMA 30 with RSI and ATR)
def intraday_strategy(data, target_profit_percent=0.05, stop_loss_percent=0.03):
    # Calculate indicators
    data['EMA_10'] = data['Close'].ewm(span=10, adjust=False).mean()
    data['EMA_30'] = data['Close'].ewm(span=30, adjust=False).mean()
    data['RSI'] = compute_rsi(data['Close'], period=14)
    data['ATR'] = compute_atr(data, period=14)

    # Get latest values
    latest_price = float(data['Close'].iloc[-1])
    ema_10 = float(data['EMA_10'].iloc[-1])
    ema_30 = float(data['EMA_30'].iloc[-1])
    rsi = float(data['RSI'].iloc[-1])
    atr = float(data['ATR'].iloc[-1])

    # Signal logic
    signal = ""
    target_price = latest_price
    stop_loss = latest_price

    # Adjusted ATR threshold for small intraday moves
    min_atr_threshold = latest_price * 0.0003  # e.g., 0.03%
    if atr < min_atr_threshold:
        return "Hold", round(latest_price, 2), round(latest_price, 2)

    # Buy Signal
    if ema_10 > ema_30 and rsi > 50:
        signal = "Buy"
        target_price = latest_price * (1 + target_profit_percent / 100)
        stop_loss = latest_price * (1 - stop_loss_percent / 100)

    # Sell Signal
    elif ema_10 < ema_30 and rsi < 50:
        signal = "Sell"
        target_price = latest_price * (1 - target_profit_percent / 100)
        stop_loss = latest_price * (1 + stop_loss_percent / 100)
    else:
        signal = "Hold"

    return signal, round(target_price, 2), round(stop_loss, 2)

def longterm_strategy(data, target_profit_percent=5.0, stop_loss_percent=2.0):
    data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()
    data['RSI'] = compute_rsi(data['Close'], period=14)
    data['ATR'] = compute_atr(data, period=14)

    latest_price = float(data['Close'].iloc[-1])
    ema_200 = float(data['EMA_200'].iloc[-1])
    rsi = float(data['RSI'].iloc[-1])
    atr = float(data['ATR'].iloc[-1])
    signal = "Hold"
    target_price = latest_price
    stop_loss = latest_price

    if latest_price > ema_200 and rsi > 50:
        signal = "Buy"
        target_price = latest_price * (1 + target_profit_percent / 100)
        stop_loss = latest_price * (1 - stop_loss_percent / 100)
    elif latest_price < ema_200 and rsi < 50:
        signal = "Sell"
        target_price = latest_price * (1 - target_profit_percent / 100)
        stop_loss = latest_price * (1 + stop_loss_percent / 100)

    return signal, round(target_price, 2), round(stop_loss, 2)



# --- Streamlit Interface ---
st.set_page_config(page_title="Smart Profit Predictor", layout="wide")
st.title("📈 Smart Profit Predictor")

# Sidebar for Asset Selection
st.sidebar.title("Asset Selection")
asset_choice = st.sidebar.selectbox("Choose an asset:", (
    "Gold (GC=F)",
))

symbol_map = {
    "Gold (GC=F)": "GC=F",
}

symbol = symbol_map[asset_choice]

# Choose Strategy
strategy_type = st.sidebar.selectbox("Choose Strategy Type:", ("Intraday", "Long-term"))

# Date Range
days = st.sidebar.slider("Select number of days:", 7, 90, 30)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=days)
print(start_date)
print(end_date)

# Get Data
data = get_price_data(symbol, start=start_date, end=end_date)
print(data)

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
            signal,buy, target_price, stop_loss = intraday_strategy(data)
        elif strategy_type == "Long-term":
            signal,target_price, stop_loss = longterm_strategy(data)

        # Add alert or logging here if needed
        time.sleep(30)

thread = threading.Thread(target=run_continuous, daemon=True)
thread.start()
