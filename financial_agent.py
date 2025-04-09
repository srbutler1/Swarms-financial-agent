import os
import time
from datetime import datetime, timedelta
import yfinance as yf
import requests
from fredapi import Fred
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from swarms import Agent, AgentRearrange
from swarm_models import OpenAIChat
import logging
from dotenv import load_dotenv
import asyncio
import aiohttp
from ratelimit import limits, sleep_and_retry

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API keys
FIN_DATA_API_KEY = os.getenv('FIN_DATA_API_KEY')
FRED_API_KEY = os.getenv('FRED_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize FRED client
fred_client = Fred(api_key=FRED_API_KEY)

# Financial Datasets API base URL
FIN_DATA_BASE_URL = "https://api.financialdatasets.ai"

# Rate limiting decorators for API calls
@sleep_and_retry
@limits(calls=5, period=60)  # Adjust these values based on your Financial Datasets API tier
async def call_fin_data_api(session, endpoint, params=None):
    url = f"{FIN_DATA_BASE_URL}{endpoint}"
    params = params or {}
    headers = {"X-API-KEY": FIN_DATA_API_KEY}
    
    try:
        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        logger.error(f"Financial Datasets API error: {e}, URL: {url}")
        # Check if API key is valid
        if hasattr(e, 'status') and e.status == 403:
            logger.error(f"Financial Datasets API authentication failed. Please check your API key.")
        raise

@sleep_and_retry
@limits(calls=120, period=60)  # FRED allows 120 requests per minute
def call_fred_api(func, *args, **kwargs):
    return func(*args, **kwargs)

# Yahoo Finance data retrieval functions
async def get_yahoo_finance_data(session, ticker, period="1d", interval="1m"):
    try:
        stock = yf.Ticker(ticker)
        hist = await asyncio.to_thread(stock.history, period=period, interval=interval)
        info = await asyncio.to_thread(lambda: stock.info)
        return hist, info
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance data for {ticker}: {e}")
        return None, None

async def get_yahoo_finance_realtime(session, ticker):
    try:
        stock = yf.Ticker(ticker)
        return await asyncio.to_thread(lambda: stock.fast_info)
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance realtime data for {ticker}: {e}")
        return None

# FRED Integration
async def get_fred_data(session, series_id, start_date, end_date):
    try:
        data = await asyncio.to_thread(call_fred_api, fred_client.get_series, series_id, start_date, end_date)
        return data
    except Exception as e:
        logger.error(f"Error fetching FRED data for {series_id}: {e}")
        return None

async def get_fred_realtime(session, series_ids):
    try:
        data = {}
        for series_id in series_ids:
            series = await asyncio.to_thread(call_fred_api, fred_client.get_series, series_id)
            data[series_id] = series.iloc[-1]  # Get the most recent value
        return data
    except Exception as e:
        logger.error(f"Error fetching FRED realtime data: {e}")
        return {}

# Financial Datasets API Integration
async def get_fin_data_realtime(session, ticker):
    try:
        # Get real-time price snapshot
        snapshot_endpoint = "/prices/snapshot"
        params = {"ticker": ticker}
        snapshot_data = await call_fin_data_api(session, snapshot_endpoint, params)
        
        return snapshot_data
    except Exception as e:
        logger.error(f"Error fetching Financial Datasets realtime data for {ticker}: {e}")
        return None

async def get_fin_data_news(session, ticker):
    try:
        # Get news for the ticker
        news_endpoint = "/news"
        params = {
            'ticker': ticker,
            'limit': 5  # Limit to 5 recent news items
        }
        news_data = await call_fin_data_api(session, news_endpoint, params)
        
        # Format news data for easier consumption
        if news_data and 'news' in news_data:
            formatted_news = []
            for item in news_data['news']:
                formatted_news.append({
                    'title': item.get('title', 'No title'),
                    'published_date': item.get('published_date', ''),
                    'url': item.get('url', ''),
                    'source': item.get('source', 'Unknown source')
                })
            return formatted_news
        return []
    except Exception as e:
        logger.error(f"Error fetching Financial Datasets news for {ticker}: {e}")
        return []

async def get_fin_data_historical(session, ticker, interval='day', interval_multiplier=1, start_date=None, end_date=None):
    try:
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
        # Get historical price data
        prices_endpoint = "/prices/"
        params = {
            'ticker': ticker,
            'interval': interval,
            'interval_multiplier': interval_multiplier,
            'start_date': start_date,
            'end_date': end_date
        }
        price_data = await call_fin_data_api(session, prices_endpoint, params)
        
        if price_data and 'prices' in price_data:
            # Convert to pandas DataFrame for easier analysis
            df = pd.DataFrame(price_data['prices'])
            if not df.empty and 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching Financial Datasets historical data for {ticker}: {e}")
        return pd.DataFrame()
