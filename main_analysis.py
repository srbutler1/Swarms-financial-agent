import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta

# Import our custom modules
from financial_agent import (
    get_yahoo_finance_data,
    get_yahoo_finance_realtime,
    get_fin_data_realtime,
    get_fin_data_news,
    get_fin_data_historical,
    get_fred_realtime
)
from agents import agent_system

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def real_time_analysis(session, ticker):
    logger.info(f"Starting real-time analysis for {ticker}")
    
    # Initialize data containers
    yf_data = None
    yf_info = None
    yf_realtime = None
    fin_data_snapshot = None
    fin_data_historical = None
    fin_data_news = None
    fred_data = None
    
    # Fetch data with error handling
    try:
        logger.info(f"Fetching Yahoo Finance data for {ticker}")
        yf_data, yf_info = await get_yahoo_finance_data(session, ticker)
        yf_realtime = await get_yahoo_finance_realtime(session, ticker)
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance data: {e}")
    
    try:
        logger.info(f"Fetching Financial Datasets snapshot for {ticker}")
        fin_data_snapshot = await get_fin_data_realtime(session, ticker)
    except Exception as e:
        logger.error(f"Error fetching Financial Datasets snapshot for {ticker}: {e}")
    
    try:
        logger.info(f"Fetching Financial Datasets news for {ticker}")
        fin_data_news = await get_fin_data_news(session, ticker)
    except Exception as e:
        logger.error(f"Error fetching Financial Datasets news for {ticker}: {e}")
        
    try:
        logger.info(f"Fetching Financial Datasets historical data for {ticker}")
        # Get 30 days of daily data
        fin_data_historical = await get_fin_data_historical(session, ticker, interval='day', interval_multiplier=1)
    except Exception as e:
        logger.error(f"Error fetching Financial Datasets historical data for {ticker}: {e}")
    
    try:
        logger.info("Fetching FRED economic data")
        fred_data = await get_fred_realtime(session, ['GDP', 'UNRATE', 'CPIAUCSL'])
    except Exception as e:
        logger.error(f"Error fetching FRED data: {e}")
    
    # Prepare input for the multi-agent system
    input_data = f"""
    Yahoo Finance Data:
    {yf_realtime if yf_realtime else 'Data unavailable'}
    
    Recent Stock History:
    {yf_data.tail().to_string() if yf_data is not None and not yf_data.empty else 'Data unavailable'}
    
    Stock Information:
    {yf_info if yf_info else 'Data unavailable'}
    
    Financial Datasets Snapshot:
    {fin_data_snapshot['snapshot'] if fin_data_snapshot and 'snapshot' in fin_data_snapshot else 'Data unavailable'}
    
    Financial Datasets Historical Data (Last 5 days):
    {fin_data_historical.tail().to_string() if fin_data_historical is not None and not fin_data_historical.empty else 'Data unavailable'}
    
    Recent News:
    {fin_data_news[:3] if fin_data_news else 'No recent news available'}
    
    Economic Indicators:
    {fred_data if fred_data else 'Data unavailable'}
    
    Analyze this real-time financial data for {ticker}. Provide insights on the stock's performance, overall market conditions, relevant economic factors, and any significant news that might impact the stock or market.
    Use whatever data is available to form your analysis, even if some data sources are unavailable.
    """
    # Run the multi-agent analysis
    try:
        logger.info(f"Starting multi-agent analysis for {ticker}")
        analysis = agent_system.run(input_data)
        logger.info(f"Analysis completed for {ticker}")
        return analysis
    except Exception as e:
        logger.error(f"Error during multi-agent analysis for {ticker}: {e}")
        # Print the full error traceback for debugging
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error during analysis: {e}"

# Main function to run the analysis
async def main(ticker):
    # Configure logging for better visibility
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Log the start of the analysis
    logger.info(f"Starting financial analysis for {ticker}")
    
    async with aiohttp.ClientSession() as session:
        try:
            analysis = await real_time_analysis(session, ticker)
            print(f"\n===== ANALYSIS FOR {ticker} =====\n")
            print(analysis)
            print("\n===== END OF ANALYSIS =====\n")
            return analysis
        except Exception as e:
            logger.error(f"Critical error in main analysis: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

# Entry point for running the script directly
if __name__ == "__main__":
    import sys
    
    # Default ticker if none provided
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    
    # Run the analysis
    asyncio.run(main(ticker))
