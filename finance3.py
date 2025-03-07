import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from textblob import TextBlob
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

# News API configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Get from https://newsapi.org/
NEWS_API_URL = "https://newsapi.org/v2/everything"

stocks = [
    "ASIANPAINT.BO", "AXISBANK.BO", "BAJFINANCE.BO",
    "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
    "BRK-B", "JPM", "JNJ", "WMT", "PG", "V", "XOM",
    "RELIANCE.BO", "TCS.BO", "INFY.BO", "HDFCBANK.BO", "ICICIBANK.BO",
    "KOTAKBANK.BO", "LT.BO", "ITC.BO", "SBIN.BO", "BHARTIARTL.BO",
    "HCLTECH.BO", "WIPRO.BO", "TITAN.BO", "ULTRACEMCO.BO", "MARUTI.BO",
    "TATAMOTORS.BO", "M&M.BO", "BAJAJFINSV.BO", "SUNPHARMA.BO", "DRREDDY.BO",
    "ONGC.BO", "POWERGRID.BO", "NTPC.BO", "ADANIENT.BO", "ADANIGREEN.BO",
    "CIPLA.BO", "DABUR.BO", "BPCL.BO", "HINDALCO.BO", "GRASIM.BO"
]



# Custom CSS styling
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .news-card {
        padding: 15px;
        margin: 10px 0;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color:black;
    }
    .news-card h4 {
        color: #000000 !important;  /* Black color for headings */
        margin-bottom: 10px;
    }
    .sentiment-positive { color: green; }
    .sentiment-negative { color: red; }
</style>
""", unsafe_allow_html=True)


def get_stock_data(ticker, period="2y"):
    try:
        return yf.Ticker(ticker).history(period=period)
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return pd.DataFrame()


def predict_arima(df, days=7):
    try:
        model = ARIMA(df['Close'], order=(5, 1, 0))
        model_fit = model.fit()
        forecast = model_fit.get_forecast(steps=days)
        return forecast.predicted_mean
    except Exception as e:
        st.error(f"ARIMA Error: {str(e)}")
        return pd.Series()


def get_news(ticker):
    try:
        params = {
            'q': ticker,
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 5
        }

        response = requests.get(NEWS_API_URL, params=params)
        if response.status_code == 200:
            return response.json().get('articles', [])
        else:
            st.error(f"News API Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"News Error: {str(e)}")
        return []


def scrape_article(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to find article text using common tags
        article_text = ""
        for paragraph in soup.find_all(['p', 'article', 'div.main-content']):
            article_text += paragraph.get_text() + "\n"

        return article_text[:5000]  # Return first 5000 characters
    except Exception as e:
        st.error(f"Scraping Error: {str(e)}")
        return ""


def analyze_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity  # Returns between -1 (negative) to 1 (positive)


# Streamlit UI
st.title("📈 Stock Analyzer with News Insights")
selected_stock = st.selectbox("Select a Stock:", stocks)
custom_article = st.text_input("Or analyze a custom article (paste URL):")

if st.button("Analyze"):
    with st.spinner("Gathering insights..."):
        # Stock Price Analysis
        st.subheader(f"{selected_stock} Analysis")
        data = get_stock_data(selected_stock)

        if not data.empty:
            # Price Prediction
            arima_pred = predict_arima(data)
            if not arima_pred.empty:
                st.subheader("Price Forecast (Next 7 Days)")
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(data.index[-30:], data['Close'][-30:], label='Historical Prices')
                forecast_dates = [data.index[-1] + timedelta(days=i) for i in range(1, 8)]
                ax.plot(forecast_dates, arima_pred, label='ARIMA Forecast', linestyle='--')
                ax.set_title("Price Prediction")
                ax.legend()
                st.pyplot(fig)

        # News Analysis
        st.subheader("Latest News")
        articles = get_news(selected_stock)

        for article in articles[:3]:  # Show top 3 articles
            with st.container():
                st.markdown(f"""
                <div class="news-card">
                    <h4>{article['title']}</h4>
                    <p>{article.get('description', 'No description available')}</p>
                    <a href="{article['url']}" target="_blank">Read full article</a>
                </div>
                """, unsafe_allow_html=True)

                # Analyze article sentiment
                if article.get('content'):
                    sentiment = analyze_sentiment(article['content'])
                    sentiment_text = "Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"
                    st.markdown(f"**Sentiment:** <span class='sentiment-{'positive' if sentiment > 0 else 'negative'}'>\
                    {sentiment_text} ({sentiment:.2f})</span>", unsafe_allow_html=True)

        # Custom Article Analysis
        if custom_article:
            st.subheader("Custom Article Analysis")
            article_text = scrape_article(custom_article)

            if article_text:
                sentiment = analyze_sentiment(article_text)
                sentiment_text = "Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("**Extracted Text Excerpt:**")
                    st.write(article_text[:1000] + "...")  # Show first 1000 characters

                with col2:
                    st.markdown("**Sentiment Analysis**")
                    st.markdown(f"""
                    <div style="font-size: 24px; text-align: center;
                        color: {'green' if sentiment > 0 else 'red'}">
                        {sentiment_text}<br>
                        {sentiment:.2f}
                    </div>
                    """, unsafe_allow_html=True)

st.markdown("---")