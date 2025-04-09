import asyncio
import logging
from typing import List, Dict, Any

from main_analysis import real_time_analysis
from agents import agent_system

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def compare_stocks(session, tickers: List[str]):
    """
    Compare multiple stocks by running a real-time analysis on each and then
    prompting the multi-agent system to compare the results.
    
    Args:
        session: The aiohttp client session
        tickers: List of stock tickers to compare
        
    Returns:
        A comprehensive comparison of the stocks
    """
    logger.info(f"Starting stock comparison for: {', '.join(tickers)}")
    
    results = {}
    for ticker in tickers:
        results[ticker] = await real_time_analysis(session, ticker)
    
    comparison_prompt = f"""
    Compare the following stocks based on the provided analyses:
    {results}
    
    Highlight key differences and similarities. Provide a ranking of these stocks based on their current performance and future prospects.
    """
    
    try:
        comparison = agent_system.run(comparison_prompt)
        logger.info(f"Stock comparison completed for {tickers}")
        return comparison
    except Exception as e:
        logger.error(f"Error during stock comparison: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error during comparison: {e}"
