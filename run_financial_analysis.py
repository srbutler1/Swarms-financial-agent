import asyncio
import aiohttp
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our analysis functions
from main_analysis import real_time_analysis
from advanced_analysis import compare_stocks, sector_analysis, economic_impact_analysis

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY or not OPENAI_API_KEY.startswith('sk-'):
    logger.warning("Invalid OpenAI API key format. Using dummy key for testing.")
    # Use a dummy key with the correct format for testing
    os.environ['OPENAI_API_KEY'] = 'sk-dummy1234567890abcdefghijklmnopqrstuvwxyz1234567890abcdefgh'

async def main():
    logger.info("Starting financial analysis suite")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Example usage
            print("\n" + "=" * 50)
            print("SINGLE STOCK ANALYSIS")
            print("=" * 50)
            analysis_result = await real_time_analysis(session, 'AAPL')
            print(analysis_result)

            print("\n" + "=" * 50)
            print("STOCK COMPARISON")
            print("=" * 50)
            comparison_result = await compare_stocks(session, ['AAPL', 'GOOGL', 'MSFT'])
            print(comparison_result)
            
            print("\n" + "=" * 50)
            print("TECHNOLOGY SECTOR ANALYSIS")
            print("=" * 50)
            tech_sector_analysis = await sector_analysis(session, 'Technology')
            print(tech_sector_analysis)
            
            print("\n" + "=" * 50)
            print("ECONOMIC IMPACT ANALYSIS")
            print("=" * 50)
            gdp_impact = await economic_impact_analysis(session, 'GDP', 22000)
            print(gdp_impact)
            
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
