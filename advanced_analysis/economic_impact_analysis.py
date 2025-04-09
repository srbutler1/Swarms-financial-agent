import asyncio
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

from financial_agent import get_fred_data
from agents import agent_system

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def economic_impact_analysis(session, indicator: str, threshold: float):
    """
    Analyze the economic impact when an indicator crosses a specified threshold.
    
    Args:
        session: The aiohttp client session
        indicator: The FRED indicator code (e.g., 'GDP', 'UNRATE', 'CPIAUCSL')
        threshold: The threshold value to monitor for crossings
        
    Returns:
        An analysis of the economic impact if the threshold is crossed
    """
    logger.info(f"Starting economic impact analysis for indicator {indicator} with threshold {threshold}")
    
    # Fetch historical data for the indicator
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    try:
        indicator_data = await get_fred_data(session, indicator, start_date, end_date)
        
        if indicator_data is None or len(indicator_data) < 2:
            logger.error(f"Insufficient data for indicator {indicator}")
            return f"Insufficient data for indicator {indicator}"
        
        # Check if the latest value crosses the threshold
        latest_value = indicator_data.iloc[-1]
        previous_value = indicator_data.iloc[-2]
        crossed_threshold = (latest_value > threshold and previous_value <= threshold) or \
                          (latest_value < threshold and previous_value >= threshold)
        
        if crossed_threshold:
            logger.info(f"Threshold {threshold} crossed for {indicator}. Current value: {latest_value}")
            
            impact_prompt = f"""
            The economic indicator {indicator} has crossed the threshold of {threshold}. Its current value is {latest_value}.
            
            Historical data:
            {indicator_data.tail().to_string()}
            
            Analyze the potential impacts of this change on:
            1. Overall economic conditions
            2. Different market sectors
            3. Specific types of stocks (e.g., growth vs. value)
            4. Other economic indicators
            
            Provide a comprehensive analysis of the potential consequences and any recommended actions for investors.
            """
            
            try:
                analysis = agent_system.run(impact_prompt)
                logger.info(f"Economic impact analysis completed for {indicator}")
                return analysis
            except Exception as e:
                logger.error(f"Error during economic impact analysis for {indicator}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return f"Error during economic impact analysis: {e}"
        else:
            logger.info(f"The {indicator} indicator has not crossed the threshold of {threshold}. Current value: {latest_value}")
            return f"The {indicator} indicator has not crossed the threshold of {threshold}. Current value: {latest_value}"
    
    except Exception as e:
        logger.error(f"Error fetching data for indicator {indicator}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error fetching data for indicator {indicator}: {e}"
