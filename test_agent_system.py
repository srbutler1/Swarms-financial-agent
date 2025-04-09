import os
import asyncio
import aiohttp
import logging
import json
import traceback
from dotenv import load_dotenv
from pathlib import Path
import datetime

# Import our custom modules
from financial_agent import get_fin_data_realtime, get_fin_data_news, get_fin_data_historical
from agents import stock_agent, market_agent, macro_agent, news_agent, investment_agent, agent_system
from swarms.structs.rearrange import AgentRearrange

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create a wrapper function to run agents directly and bypass JSON parsing
def run_agent_safely(agent, task, **kwargs):
    """Run an agent safely, bypassing JSON parsing issues."""
    try:
        # First try the direct _run method
        return agent._run(task, **kwargs)
    except Exception as e:
        logger.warning(f"Error running agent with _run method: {e}")
        # Fallback to completion method
        try:
            return agent.completion(task)
        except Exception as e2:
            logger.error(f"Error running agent with completion method: {e2}")
            return f"Error running agent: {e2}"

def save_output_to_file(agent_name, output, ticker):
    """Save agent output to a file in the outputs directory."""
    # Create outputs directory if it doesn't exist
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Create a filename with timestamp, agent name, and ticker
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{ticker}_{agent_name}.txt"
    
    # Save the output to the file
    with open(output_dir / filename, "w") as f:
        f.write(output)
    
    logger.info(f"Saved {agent_name} output to {filename}")

async def test_agent_with_fin_data():
    """Test the agent system with Financial Datasets API data."""
    try:
        # Create an aiohttp session for making API requests
        async with aiohttp.ClientSession() as session:
            # Get the ticker from environment or use a default
            ticker = os.getenv("TEST_TICKER", "NVDA")
            logger.info(f"Testing with ticker: {ticker}")
            
            # Fetch data from Financial Datasets API
            try:
                realtime_data = await get_fin_data_realtime(session, ticker)
                news_data = await get_fin_data_news(session, ticker)
                historical_data = await get_fin_data_historical(session, ticker)
                
                logger.info(f"Successfully fetched data for {ticker}")
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                return
            
            # Create the base task with the fetched data
            base_task = f"""
            Analyze the stock {ticker} using the following data:
            
            Real-time data: {realtime_data}
            
            News data: {news_data}
            
            Historical data: {historical_data}
            """
            
            # Run each agent individually and collect their outputs
            try:
                logger.info("Running agents sequentially...")
                
                # Run StockAgent
                stock_task = base_task + "\nProvide a detailed analysis of the stock's current status and trends."
                stock_analysis = run_agent_safely(stock_agent, stock_task)
                save_output_to_file("StockAgent", stock_analysis, ticker)
                logger.info("\n--- STOCK AGENT OUTPUT ---")
                logger.info(stock_analysis)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Run MarketAgent with stock analysis
                market_task = base_task + f"\nStock Analysis: {stock_analysis}\n\nProvide an analysis of current market conditions and how they affect this stock."
                market_analysis = run_agent_safely(market_agent, market_task)
                save_output_to_file("MarketAgent", market_analysis, ticker)
                logger.info("\n--- MARKET AGENT OUTPUT ---")
                logger.info(market_analysis)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Run MacroAgent with previous analyses
                macro_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\n\nProvide a macroeconomic analysis and its impact on this stock."
                macro_analysis = run_agent_safely(macro_agent, macro_task)
                save_output_to_file("MacroAgent", macro_analysis, ticker)
                logger.info("\n--- MACRO AGENT OUTPUT ---")
                logger.info(macro_analysis)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Run NewsAgent with previous analyses
                news_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\nMacroeconomic Analysis: {macro_analysis}\n\nAnalyze recent news and their potential impact on this stock."
                news_analysis = run_agent_safely(news_agent, news_task)
                save_output_to_file("NewsAgent", news_analysis, ticker)
                logger.info("\n--- NEWS AGENT OUTPUT ---")
                logger.info(news_analysis)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Run InvestmentAgent with all previous analyses
                investment_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\nMacroeconomic Analysis: {macro_analysis}\nNews Analysis: {news_analysis}\n\nBased on all these analyses, provide an investment recommendation."
                investment_recommendation = run_agent_safely(investment_agent, investment_task)
                save_output_to_file("InvestmentAgent", investment_recommendation, ticker)
                logger.info("\n--- INVESTMENT AGENT OUTPUT ---")
                logger.info(investment_recommendation)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Combine all outputs into a comprehensive analysis
                combined_output = f"""
                # Comprehensive Stock Analysis for {ticker}
                
                ## Stock Analysis
                {stock_analysis}
                
                ## Market Analysis
                {market_analysis}
                
                ## Macroeconomic Analysis
                {macro_analysis}
                
                ## News Analysis
                {news_analysis}
                
                ## Investment Recommendation
                {investment_recommendation}
                """
                
                logger.info("\n--- COMBINED OUTPUT ---")
                logger.info(combined_output)
                logger.info("--- END OF COMBINED OUTPUT ---\n")
                
                return combined_output
            except Exception as e:
                logger.error(f"Error running agents: {str(e)}")
                # Print the traceback for debugging
                import traceback
                traceback.print_exc()
                return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    logger.info("Starting agent system test")
    asyncio.run(test_agent_with_fin_data())
