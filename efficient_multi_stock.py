"""
Efficient multi-stock analysis system for Sam Butler Investment Agency.
This implementation manages context more efficiently to avoid token limit issues.
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
from custom_agent_rearrange import CustomAgentRearrange
from report_generation.pdf_utilities import create_stock_chart, generate_pdf_report

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create outputs directory if it doesn't exist
outputs_dir = Path("outputs")
outputs_dir.mkdir(exist_ok=True)

def save_output_to_file(agent_name, output, ticker):
    """Save agent output to a file in the outputs directory."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{ticker}_{agent_name}.txt"
    
    with open(outputs_dir / filename, "w") as f:
        f.write(output)
    
    logger.info(f"Saved {agent_name} output to {filename}")
    return outputs_dir / filename

async def analyze_single_stock(session, ticker):
    """Analyze a single stock using the specialized agents without accumulating context."""
    logger.info(f"Starting analysis for {ticker}")
    
    try:
        # Fetch data
        realtime_data = await get_fin_data_realtime(session, ticker)
        news_data = await get_fin_data_news(session, ticker)
        historical_data = await get_fin_data_historical(session, ticker)
        
        logger.info(f"Successfully fetched data for {ticker}")
        
        # Generate stock chart
        chart_path = create_stock_chart(ticker)
        if chart_path:
            logger.info(f"Chart generated for {ticker} at {chart_path}")
        
        # Base task with data
        base_task = f"""
        Analyze the stock {ticker} using the following data:
        
        Real-time data: {realtime_data}
        
        News data: {news_data}
        
        Historical data: {historical_data}
        """
        
        # Step 1: Stock Analysis - Run independently
        stock_task = base_task + "\nAs the Senior Equity Analyst, provide a detailed analysis of this stock's current status and trends."
        stock_analysis = stock_agent.run(stock_task)
        stock_file = save_output_to_file("StockAgent", stock_analysis, ticker)
        logger.info(f"Completed stock analysis for {ticker}")
        
        # Step 2: Market Analysis - Use minimal context from stock analysis
        market_task = base_task + f"\nThe Senior Equity Analyst has completed their analysis. As the Head of Market Strategy, analyze current market conditions affecting {ticker}."
        market_analysis = market_agent.run(market_task)
        market_file = save_output_to_file("MarketAgent", market_analysis, ticker)
        logger.info(f"Completed market analysis for {ticker}")
        
        # Step 3: Macro Analysis - Run independently
        macro_task = base_task + f"\nAs the Chief Economist, analyze macroeconomic factors affecting {ticker}."
        macro_analysis = macro_agent.run(macro_task)
        macro_file = save_output_to_file("MacroAgent", macro_analysis, ticker)
        logger.info(f"Completed macro analysis for {ticker}")
        
        # Step 4: News Analysis - Run independently
        news_task = base_task + f"\nAs the Director of Financial Intelligence, analyze recent news and sentiment affecting {ticker}."
        news_analysis = news_agent.run(news_task)
        news_file = save_output_to_file("NewsAgent", news_analysis, ticker)
        logger.info(f"Completed news analysis for {ticker}")
        
        # Step 5: Investment Recommendation - Use summaries of previous analyses
        investment_task = f"""
        You are a Senior Portfolio Manager at Sam Butler Investment Agency evaluating {ticker}.
        
        The research team has provided the following summarized insights:
        
        1. Key points from Equity Analysis: {stock_analysis[:500]}...
        
        2. Key points from Market Analysis: {market_analysis[:500]}...
        
        3. Key points from Economic Analysis: {macro_analysis[:500]}...
        
        4. Key points from News Analysis: {news_analysis[:500]}...
        
        Based on these insights, provide an investment recommendation for {ticker}.
        """
        
        investment_recommendation = investment_agent.run(investment_task)
        investment_file = save_output_to_file("InvestmentAgent", investment_recommendation, ticker)
        logger.info(f"Completed investment recommendation for {ticker}")
        
        # Create a summary for this stock (short version for the final report)
        stock_summary = {
            "ticker": ticker,
            "recommendation": investment_recommendation,
            "stock_analysis_file": str(stock_file),
            "market_analysis_file": str(market_file),
            "macro_analysis_file": str(macro_file),
            "news_analysis_file": str(news_file),
            "investment_file": str(investment_file),
            "chart_path": str(chart_path) if chart_path else None
        }
        
        return stock_summary
        
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {str(e)}")
        traceback.print_exc()
        return {
            "ticker": ticker,
            "error": f"Error analyzing {ticker}: {str(e)}"
        }

async def analyze_multiple_stocks(tickers):
    """Analyze multiple stocks efficiently without accumulating excessive context."""
    logger.info(f"Starting analysis for {len(tickers)} stocks: {', '.join(tickers)}")
    
    async with aiohttp.ClientSession() as session:
        # Process each stock sequentially to avoid rate limits
        stock_results = {}
        for ticker in tickers:
            result = await analyze_single_stock(session, ticker)
            stock_results[ticker] = result
            
            if ticker != tickers[-1]:  # Don't delay after the last stock
                logger.info("Waiting 3 seconds before processing next stock...")
                await asyncio.sleep(3)
        
        return stock_results

async def generate_portfolio_report(stock_results, tickers, today):
    """Generate a professional portfolio report by aggregating individual stock analyses."""
    print("Aggregating stock analyses and generating portfolio report...")
    
    # Collect all stock analyses and recommendations into a structured format for the report generator
    stock_analyses = []
    for ticker in tickers:
        analysis = {}
        analysis['ticker'] = ticker
        
        # Get recommendation if available
        recommendation_path = outputs_dir / f"{today}_{ticker}_InvestmentAgent.txt"
        if recommendation_path.exists():
            with open(recommendation_path, 'r') as f:
                analysis['recommendation'] = f.read()
        else:
            analysis['recommendation'] = f"No recommendation available for {ticker}"
            
        stock_analyses.append(analysis)
    
    # Generate stock charts for each ticker
    for ticker in tickers:
        try:
            create_stock_chart(ticker)
        except Exception as e:
            print(f"Error creating chart for {ticker}: {e}")
    
    # Format all stock results for the report aggregation agent
    all_analyses = ""
    for ticker in tickers:
        ticker_result = stock_results.get(ticker, {})
        investment_rec = ticker_result.get('recommendation', f"No recommendation available for {ticker}")
        all_analyses += f"\n\n## {ticker} Analysis\n\n{investment_rec}\n\n"
    
    # Generate the portfolio report using the report aggregation agent
    try:
        # Create a task for the report agent
        report_task = f"""
        As Chief Investment Officer, create a comprehensive portfolio analysis report for the following tickers: {', '.join(tickers)}.
        
        Structure the report with the following sections:
        
        1. Executive Summary (overall portfolio recommendation)
        2. Market Overview (key trends affecting these securities)
        3. Portfolio Strategy (allocation recommendations and rationale)
        4. Individual Stock Analyses (brief summary of each stock)
        5. Risk Management (diversification and hedging strategies)
        6. Performance Expectations (projected returns and timeline)
        
        Make this a professional report for the Sam Butler Investment Agency with actionable recommendations.
        
        Base your analysis on the following individual stock analyses:
        
        {all_analyses}
        """
        
        # Run the report aggregation agent
        print("Running report aggregation agent...")
        portfolio_report = report_aggregation_agent.run(report_task)
        
        # Generate and save the PDF report
        print("Generating PDF report...")
        pdf_path = generate_pdf_report(portfolio_report, tickers, today, stock_analyses)
        
        print(f"PDF report generated successfully: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        print(f"Error generating portfolio report: {str(e)}")
        import traceback
        traceback.print_exc()
        print("Failed to generate PDF report.")
        return None

async def run_portfolio_analysis(tickers):
    """Run the complete portfolio analysis workflow."""
    # Step 1: Analyze each stock independently
    stock_results = await analyze_multiple_stocks(tickers)
    
    # Step 2: Generate the portfolio report
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    pdf_path = await generate_portfolio_report(stock_results, tickers, today)
    
    return pdf_path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Efficient multi-stock analysis for Sam Butler Investment Agency.")
    parser.add_argument("--tickers", "-t", type=str, required=True,
                      help="Comma-separated list of stock tickers to analyze (e.g., AAPL,MSFT,GOOGL)")
    return parser.parse_args()

if __name__ == "__main__":
    logger.info("Starting Sam Butler Investment Agency Portfolio Analysis")
    
    # Parse command line arguments or use default tickers
    try:
        args = parse_args()
        tickers = [ticker.strip() for ticker in args.tickers.split(",")]
    except:
        # Default tickers if no args provided or parsing fails
        tickers = ["AAPL", "MSFT", "GOOGL"]
    
    logger.info(f"Analyzing tickers: {', '.join(tickers)}")
    
    # Run the portfolio analysis
    pdf_path = asyncio.run(run_portfolio_analysis(tickers))
    
    if pdf_path:
        logger.info(f"Analysis complete. PDF report generated at: {pdf_path}")
        # Try to open the PDF report
        try:
            os.system(f"open {pdf_path}")
        except:
            logger.info(f"Please open the PDF report manually at: {pdf_path}")
    else:
        logger.error("Failed to generate PDF report.")
