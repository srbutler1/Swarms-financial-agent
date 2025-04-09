import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import logging
import pandas as pd
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key
FIN_DATA_API_KEY = os.getenv('FIN_DATA_API_KEY')
FIN_DATA_BASE_URL = "https://api.financialdatasets.ai"

async def test_api_connection():
    """Test the basic connection to the Financial Datasets API"""
    logger.info(f"Testing API connection with key: {FIN_DATA_API_KEY[:5]}...{FIN_DATA_API_KEY[-5:]}")
    
    headers = {"X-API-KEY": FIN_DATA_API_KEY}
    
    async with aiohttp.ClientSession() as session:
        # Test endpoint 1: Prices snapshot
        ticker = "AAPL"
        url = f"{FIN_DATA_BASE_URL}/prices/snapshot"
        params = {"ticker": ticker}
        
        logger.info(f"Testing endpoint: {url} with params: {params}")
        try:
            async with session.get(url, params=params, headers=headers) as response:
                status = response.status
                logger.info(f"Response status: {status}")
                
                if status == 200:
                    data = await response.json()
                    logger.info(f"Success! Received data: {json.dumps(data, indent=2)[:500]}...")
                else:
                    text = await response.text()
                    logger.error(f"Error response: {text}")
                    
                    # Check for common error codes
                    if status == 401 or status == 403:
                        logger.error("Authentication error. Check your API key.")
                    elif status == 404:
                        logger.error("Endpoint not found. Check the API URL.")
                    elif status == 429:
                        logger.error("Rate limit exceeded.")
        except Exception as e:
            logger.error(f"Exception during API call: {e}")
        
        # Test endpoint 2: News (with corrected endpoint)
        logger.info("\nTesting news endpoint")
        url = f"{FIN_DATA_BASE_URL}/news"  # Corrected endpoint
        params = {"ticker": ticker, "limit": 2}
        
        try:
            async with session.get(url, params=params, headers=headers) as response:
                status = response.status
                logger.info(f"Response status: {status}")
                
                if status == 200:
                    data = await response.json()
                    logger.info(f"Success! Received data: {json.dumps(data, indent=2)[:500]}...")
                else:
                    text = await response.text()
                    logger.error(f"Error response: {text}")
        except Exception as e:
            logger.error(f"Exception during API call: {e}")
            
        # Test endpoint 3: Historical data
        logger.info("\nTesting historical data endpoint")
        url = f"{FIN_DATA_BASE_URL}/prices/"
        params = {
            "ticker": ticker,
            "interval": "day",
            "interval_multiplier": 1,
            "start_date": "2023-01-01",
            "end_date": "2023-01-10"
        }
        
        try:
            async with session.get(url, params=params, headers=headers) as response:
                status = response.status
                logger.info(f"Response status: {status}")
                
                if status == 200:
                    data = await response.json()
                    logger.info(f"Success! Received data: {json.dumps(data, indent=2)[:500]}...")
                else:
                    text = await response.text()
                    logger.error(f"Error response: {text}")
        except Exception as e:
            logger.error(f"Exception during API call: {e}")

async def test_financial_agent_functions():
    """Test the functions from financial_agent.py with the corrected endpoints"""
    logger.info("\nTesting financial_agent.py functions")
    
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
            return {"error": str(e)}
    
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
            # Get news for the ticker with corrected endpoint
            news_endpoint = "/news"  # Corrected from "/news/company"
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
    
    async with aiohttp.ClientSession() as session:
        ticker = "AAPL"
        
        # Test get_fin_data_realtime
        logger.info(f"\nTesting get_fin_data_realtime for {ticker}")
        realtime_data = await get_fin_data_realtime(session, ticker)
        if realtime_data:
            logger.info(f"Realtime data: {json.dumps(realtime_data, indent=2)[:500]}...")
        else:
            logger.error("Failed to get realtime data")
        
        # Test get_fin_data_news with corrected endpoint
        logger.info(f"\nTesting get_fin_data_news for {ticker}")
        news_data = await get_fin_data_news(session, ticker)
        if news_data:
            logger.info(f"News data: {json.dumps(news_data, indent=2)[:500]}...")
        else:
            logger.error("Failed to get news data or no news available")
        
        # Test get_fin_data_historical
        logger.info(f"\nTesting get_fin_data_historical for {ticker}")
        historical_data = await get_fin_data_historical(
            session, 
            ticker,
            start_date="2023-01-01",
            end_date="2023-01-10"
        )
        if not historical_data.empty:
            logger.info(f"Historical data: \n{historical_data.head().to_string()}")
        else:
            logger.error("Failed to get historical data")

async def test_multiple_tickers():
    """Test API with multiple tickers to ensure it works for all cases"""
    logger.info("\nTesting multiple tickers")
    
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    async with aiohttp.ClientSession() as session:
        headers = {"X-API-KEY": FIN_DATA_API_KEY}
        
        for ticker in tickers:
            logger.info(f"\nTesting snapshot for {ticker}")
            url = f"{FIN_DATA_BASE_URL}/prices/snapshot"
            params = {"ticker": ticker}
            
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    status = response.status
                    logger.info(f"Response status: {status}")
                    
                    if status == 200:
                        data = await response.json()
                        logger.info(f"Success! Price: {data['snapshot']['price'] if 'snapshot' in data else 'N/A'}")
                    else:
                        text = await response.text()
                        logger.error(f"Error response: {text}")
            except Exception as e:
                logger.error(f"Exception during API call for {ticker}: {e}")

if __name__ == "__main__":
    logger.info("Starting Financial Datasets API tests")
    
    # Print API key details (partially masked)
    if FIN_DATA_API_KEY:
        masked_key = f"{FIN_DATA_API_KEY[:5]}...{FIN_DATA_API_KEY[-5:]}"
        logger.info(f"Using API key: {masked_key}")
    else:
        logger.error("No API key found in environment variables")
    
    # Run the tests
    asyncio.run(test_api_connection())
    asyncio.run(test_financial_agent_functions())
    asyncio.run(test_multiple_tickers())
