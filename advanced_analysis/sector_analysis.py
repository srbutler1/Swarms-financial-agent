import asyncio
import logging
from typing import Dict, List, Any

from main_analysis import real_time_analysis
from agents import agent_system

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define sector stocks
SECTOR_STOCKS = {
    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],
    'Finance': ['JPM', 'BAC', 'WFC', 'C', 'GS'],
    'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABT', 'MRK'],
    'Consumer Goods': ['PG', 'KO', 'PEP', 'COST', 'WMT'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG']
}

async def sector_analysis(session, sector: str):
    """
    Analyze an entire sector by running real-time analysis on its top stocks and then 
    prompting the multi-agent system to provide sector-wide insights.
    
    Args:
        session: The aiohttp client session
        sector: The sector to analyze (must be one of the keys in SECTOR_STOCKS)
        
    Returns:
        A comprehensive analysis of the sector
    """
    logger.info(f"Starting sector analysis for: {sector}")
    
    if sector not in SECTOR_STOCKS:
        available_sectors = ', '.join(SECTOR_STOCKS.keys())
        return f"Sector '{sector}' not found. Available sectors: {available_sectors}"
    
    stocks = SECTOR_STOCKS[sector][:5]
    sector_data = {}
    
    for stock in stocks:
        logger.info(f"Analyzing {stock} for {sector} sector analysis")
        sector_data[stock] = await real_time_analysis(session, stock)
    
    sector_prompt = f"""
    Analyze the {sector} sector based on the following data from its top stocks:
    {sector_data}
    
    Provide insights on:
    1. Overall sector performance
    2. Key trends within the sector
    3. Top performing stocks and why they're outperforming
    4. Any challenges or opportunities facing the sector
    """
    
    try:
        analysis = agent_system.run(sector_prompt)
        logger.info(f"Sector analysis completed for {sector}")
        return analysis
    except Exception as e:
        logger.error(f"Error during sector analysis for {sector}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error during sector analysis: {e}"
