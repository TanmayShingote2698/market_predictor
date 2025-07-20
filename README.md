# 📈 Market Predictor

An intelligent and real-time forecasting system that predicts future trends and prices for Forex currencies and cryptocurrencies using AI/ML models, market sentiment, and technical indicators.

---

### 📖 Description

This application is designed to help traders and investors make informed decisions by predicting short-term price movements of popular Forex pairs (like EUR/USD, GBP/INR) and cryptocurrencies (like Bitcoin, Ethereum, Dogecoin). It combines machine learning, real-time data, and sentiment analysis to provide accurate and actionable trading insights.

---

### 🧠 Features

- 📊 Predict prices for major cryptocurrencies and Forex pairs
- 🤖 AI/ML models like ARIMA, LSTM for forecasting
- 💬 Sentiment analysis using live news or Twitter data
- ⚙️ Technical indicators: EMA, RSI, ATR, volume analysis
- 📈 Buy/Sell signal generation with target profit/stop-loss
- 🌐 Real-time price updates and chart visualization *(optional)

---

### 🛠️ Tech Stack

- **Languages:** Python
- **Libraries:** pandas, numpy, scikit-learn, statsmodels, TensorFlow/Keras, yfinance, requests, matplotlib
- **ML Models:** ARIMA, LSTM, Random Forest
- **Data Sources:** Yahoo Finance, CoinGecko API
- **Sentiment Analysis:** VADER, TextBlob, or transformer-based models

---

### 🚀 How to Run Locally

```bash
# Clone the repo
git clone https://github.com/your-username/market_predictor.git

# Navigate into the folder
cd market_predictor

# Install required packages
pip install -r requirements.txt

# Run the main script
python main.py
