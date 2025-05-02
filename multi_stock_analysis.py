"""
Multi-stock analysis and report generation system for Sam Butler Investment Agency.
Uses the Swarms financial agent system to analyze multiple stocks and generate a comprehensive report.
"""
import os
import asyncio
import aiohttp
import logging
import json
import traceback
from dotenv import load_dotenv
from pathlib import Path
import datetime
import argparse
import time
import yfinance as yf

# Import our custom modules
from financial_agent import get_fin_data_realtime, get_fin_data_news, get_fin_data_historical
from agents import stock_agent, market_agent, macro_agent, news_agent, investment_agent, report_aggregation_agent
from agents import agent_system
from custom_agent_rearrange import CustomAgentRearrange
from report_generation.pdf_utilities import create_stock_chart, generate_pdf_report

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

async def analyze_stock(session, ticker):
    """Analyze a single stock with all agents."""
    try:
        logger.info(f"Starting analysis for {ticker}")
        
        # Fetch data from Financial Datasets API
        try:
            realtime_data = await get_fin_data_realtime(session, ticker)
            news_data = await get_fin_data_news(session, ticker)
            historical_data = await get_fin_data_historical(session, ticker)
            
            logger.info(f"Successfully fetched data for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return f"Error analyzing {ticker}: {str(e)}"
        
        # Create the base task with the fetched data
        base_task = f"""
        Analyze the stock {ticker} using the following data:
        
        Real-time data: {realtime_data}
        
        News data: {news_data}
        
        Historical data: {historical_data}
        """
        
        # Generate stock chart in the background
        logger.info(f"Generating chart for {ticker}")
        chart_path = create_stock_chart(ticker)
        if chart_path:
            logger.info(f"Chart generated for {ticker} at {chart_path}")
        else:
            logger.warning(f"Failed to generate chart for {ticker}")
        
        # Run each agent individually and collect their outputs
        try:
            logger.info(f"Running agents sequentially for {ticker}...")
            
            # Run StockAgent
            stock_task = base_task + "\nProvide a detailed analysis of the stock's current status and trends."
            stock_analysis = run_agent_safely(stock_agent, stock_task)
            save_output_to_file("StockAgent", stock_analysis, ticker)
            logger.info(f"\n--- STOCK AGENT OUTPUT for {ticker} ---")
            logger.info(stock_analysis[:300] + "..." if len(stock_analysis) > 300 else stock_analysis)
            logger.info("--- END OF OUTPUT ---\n")
            
            # Run MarketAgent with stock analysis
            market_task = base_task + f"\nStock Analysis: {stock_analysis}\n\nProvide an analysis of current market conditions and how they affect this stock."
            market_analysis = run_agent_safely(market_agent, market_task)
            save_output_to_file("MarketAgent", market_analysis, ticker)
            logger.info(f"\n--- MARKET AGENT OUTPUT for {ticker} ---")
            logger.info(market_analysis[:300] + "..." if len(market_analysis) > 300 else market_analysis)
            logger.info("--- END OF OUTPUT ---\n")
            
            # Run MacroAgent with previous analyses
            macro_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\n\nProvide a macroeconomic analysis and its impact on this stock."
            macro_analysis = run_agent_safely(macro_agent, macro_task)
            save_output_to_file("MacroAgent", macro_analysis, ticker)
            logger.info(f"\n--- MACRO AGENT OUTPUT for {ticker} ---")
            logger.info(macro_analysis[:300] + "..." if len(macro_analysis) > 300 else macro_analysis)
            logger.info("--- END OF OUTPUT ---\n")
            
            # Run NewsAgent with previous analyses
            news_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\nMacroeconomic Analysis: {macro_analysis}\n\nAnalyze recent news and their potential impact on this stock."
            news_analysis = run_agent_safely(news_agent, news_task)
            save_output_to_file("NewsAgent", news_analysis, ticker)
            logger.info(f"\n--- NEWS AGENT OUTPUT for {ticker} ---")
            logger.info(news_analysis[:300] + "..." if len(news_analysis) > 300 else news_analysis)
            logger.info("--- END OF OUTPUT ---\n")
            
            # Run InvestmentAgent with all previous analyses
            investment_task = base_task + f"\nStock Analysis: {stock_analysis}\nMarket Analysis: {market_analysis}\nMacroeconomic Analysis: {macro_analysis}\nNews Analysis: {news_analysis}\n\nBased on all these analyses, provide an investment recommendation."
            investment_recommendation = run_agent_safely(investment_agent, investment_task)
            save_output_to_file("InvestmentAgent", investment_recommendation, ticker)
            logger.info(f"\n--- INVESTMENT AGENT OUTPUT for {ticker} ---")
            logger.info(investment_recommendation[:300] + "..." if len(investment_recommendation) > 300 else investment_recommendation)
            logger.info("--- END OF OUTPUT ---\n")
            
            # Combine all outputs into a comprehensive analysis
            combined_output = f"""
            # {ticker} - Comprehensive Stock Analysis
            
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
            
            # Save the combined output
            save_output_to_file("CombinedAnalysis", combined_output, ticker)
            
            logger.info(f"Completed analysis for {ticker}")
            return combined_output
        except Exception as e:
            logger.error(f"Error running agents for {ticker}: {str(e)}")
            # Print the traceback for debugging
            traceback.print_exc()
            return f"Error analyzing {ticker}: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error analyzing {ticker}: {str(e)}")
        traceback.print_exc()
        return f"Error analyzing {ticker}: {str(e)}"

async def multi_stock_analysis(tickers):
    """Analyze multiple stocks and generate a comprehensive report."""
    try:
        logger.info(f"Starting multi-stock analysis for: {', '.join(tickers)}")
        
        # Create an aiohttp session for making API requests
        async with aiohttp.ClientSession() as session:
            # Analyze each stock
            stock_analyses = {}
            for ticker in tickers:
                try:
                    # Analyze the stock
                    analysis = await analyze_stock(session, ticker)
                    stock_analyses[ticker] = analysis
                    
                    # Add a small delay between stocks to avoid rate limits
                    if ticker != tickers[-1]:  # Don't delay after the last stock
                        logger.info("Waiting 5 seconds before processing next stock...")
                        await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Error analyzing {ticker}: {str(e)}")
                    stock_analyses[ticker] = f"Error analyzing {ticker}: {str(e)}"
            
            # Process all stock analyses with the report aggregation agent
            try:
                logger.info("Generating aggregated investment report...")
                
                # Prepare the task for the report aggregation agent
                report_task = f"""
                # Multi-Stock Investment Analysis Report
                
                Please create a comprehensive investment report for the following stocks:
                
                """
                
                # Add each stock's analysis to the task
                for ticker, analysis in stock_analyses.items():
                    report_task += f"\n## {ticker} Analysis\n{analysis}\n\n"
                
                # Add specific instructions for the report format
                report_task += """
                Create a professional investment report for Sam Butler Investment Agency with:
                
                1. Executive Summary: Overall market assessment and key findings
                2. Market Overview: General market and economic conditions
                3. Individual Stock Analyses: Concise summary for each stock
                4. Comparative Analysis: How stocks compare to each other
                5. Investment Recommendations: Clear buy/sell/hold guidance for each
                6. Portfolio Strategy: Suggested allocations and weightings
                7. Risk Factors: Common and specific risks to be aware of
                
                Format the report professionally with clear section headings.
                """
                
                # Generate the report
                logger.info("Sending to ReportAggregationAgent...")
                investment_report = run_agent_safely(report_aggregation_agent, report_task)
                save_output_to_file("InvestmentReport", investment_report, "_".join(tickers[:3]))
                
                # Generate PDF report
                logger.info("Generating PDF report...")
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                pdf_path = generate_pdf_report(investment_report, tickers, today)
                
                logger.info(f"PDF report generated: {pdf_path}")
                
                return pdf_path
            except Exception as e:
                logger.error(f"Error generating report: {str(e)}")
                traceback.print_exc()
                return None
    except Exception as e:
        logger.error(f"Unexpected error in multi_stock_analysis: {str(e)}")
        traceback.print_exc()
        return None

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze multiple stocks and generate a comprehensive report.")
    parser.add_argument("--tickers", "-t", type=str, required=True,
                      help="Comma-separated list of stock tickers to analyze (e.g., AAPL,MSFT,GOOGL)")
    return parser.parse_args()

if __name__ == "__main__":
    logger.info("Starting multi-stock analysis system")
    
    # Parse command line arguments or use default tickers
    try:
        args = parse_args()
        tickers = [ticker.strip() for ticker in args.tickers.split(",")]
    except:
        # Default tickers if no args provided or parsing fails
        tickers = ["AAPL", "MSFT", "GOOGL"]
    
    logger.info(f"Analyzing tickers: {', '.join(tickers)}")
    
    # Run the multi-stock analysis
    pdf_path = asyncio.run(multi_stock_analysis(tickers))
    
    if pdf_path:
        logger.info(f"Analysis complete. PDF report generated at: {pdf_path}")
        # Try to open the PDF report
        try:
            os.system(f"open {pdf_path}")
        except:
            logger.info(f"Please open the PDF report manually at: {pdf_path}")
    else:
        logger.error("Failed to generate PDF report.")
