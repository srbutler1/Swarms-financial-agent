import os
import asyncio
import aiohttp
import logging
import json
import traceback
from dotenv import load_dotenv

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
def run_agent_safely(agent, task):
    """
    Run an agent directly and bypass JSON parsing issues.
    This function directly calls the agent's _run method to get the raw response.
    """
    try:
        logger.info(f"Running {agent.agent_name}...")
        
        # Use the agent's internal _run method which handles the LLM call
        # This is a more direct approach that bypasses the JSON parsing
        response = agent._run(task)
        
        # Apply the output cleaner if it exists
        if hasattr(agent, 'output_cleaner') and agent.output_cleaner:
            response = agent.output_cleaner(response)
            
        return response
    except Exception as e:
        logger.error(f"Error running agent {agent.agent_name}: {str(e)}")
        traceback.print_exc()
        
        # Try a fallback method - use the agent's completion method directly
        try:
            logger.info(f"Trying fallback method for {agent.agent_name}...")
            # Get the system prompt
            system_prompt = agent.system_prompt
            
            # Create the prompt with the task
            prompt = f"{system_prompt}\n\nTask: {task}"
            
            # Use the completion method directly
            response = agent.completion(prompt)
            
            return response
        except Exception as fallback_error:
            logger.error(f"Fallback method failed: {str(fallback_error)}")
            return f"Error: {str(e)}"

async def test_agent_with_fin_data():
    """Test the agent system with Financial Datasets API data."""
    try:
        # Create an aiohttp session for making API requests
        async with aiohttp.ClientSession() as session:
            # Get the ticker from environment or use a default
            ticker = os.getenv("TEST_TICKER", "AAPL")
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
                logger.info("\n--- STOCK AGENT OUTPUT ---")
                logger.info(stock_analysis)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Run MarketAgent with stock analysis
                market_task = base_task + f"\nStock Analysis: {stock_analysis}\n\nProvide an analysis of current market conditions and how they affect this stock."
                market_analysis = run_agent_safely(market_agent, market_task)
                logger.info("\n--- MARKET AGENT OUTPUT ---")
                logger.info(market_analysis)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Run MacroAgent with previous analyses
                macro_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\n\nProvide a macroeconomic analysis and its impact on this stock."
                macro_analysis = run_agent_safely(macro_agent, macro_task)
                logger.info("\n--- MACRO AGENT OUTPUT ---")
                logger.info(macro_analysis)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Run NewsAgent with previous analyses
                news_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\nMacroeconomic Analysis: {macro_analysis}\n\nAnalyze recent news and their potential impact on this stock."
                news_analysis = run_agent_safely(news_agent, news_task)
                logger.info("\n--- NEWS AGENT OUTPUT ---")
                logger.info(news_analysis)
                logger.info("--- END OF OUTPUT ---\n")
                
                # Run InvestmentAgent with all previous analyses
                investment_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\nMacroeconomic Analysis: {macro_analysis}\nNews Analysis: {news_analysis}\n\nBased on all these analyses, provide an investment recommendation."
                investment_recommendation = run_agent_safely(investment_agent, investment_task)
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
