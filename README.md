# Sam Butler Investment Agency - Financial Analysis System

A professional multi-agent financial analysis system built with the Swarms framework. This system emulates a real investment firm structure with specialized AI agents taking on professional roles to analyze stocks, market conditions, economic indicators, and financial news in real-time to provide comprehensive investment recommendations and generate professionally branded reports.

## Features

- Multi-stock portfolio analysis with efficient token management
- Professional PDF report generation with Sam Butler Investment Agency branding
- Visualizations including price charts and comparative performance analysis
- Real-time stock data analysis using YFinance and Financial Datasets API
- Multi-agent system with specialized professional roles for different aspects of financial analysis
- Custom agent flow implementation for reliable output handling
- Comprehensive financial insights combining stock, market, economic, and news analysis
- Final investment recommendation (BUY/SELL/HOLD) with expected returns and portfolio allocation advice

## Setup

### Prerequisites

- Python 3.11+
- API keys for:
  - OpenAI API (for the AI agents)
  - Financial Datasets API (for market data)
  - FRED API (for economic data)

### Installation

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   
   Or manually install:
   ```
   pip install -U swarms pandas numpy matplotlib aiohttp yfinance fredapi ratelimit reportlab seaborn fpdf
   ```

3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   FIN_DATA_API_KEY=your_financial_datasets_api_key
   FRED_API_KEY=your_fred_api_key
   SEC_API_KEY=your_sec_api_key
   ```

## Usage

### Single Stock Analysis

Run the test script to analyze a single stock:

```
python test_agent_system.py
```

You can set the stock ticker to analyze by setting the `TEST_TICKER` environment variable:

```
TEST_TICKER=MSFT python test_agent_system.py
```

### Multi-Stock Portfolio Analysis with PDF Reports

The primary workflow for full portfolio analysis with token-efficient processing:

```
python efficient_multi_stock.py --tickers "AAPL,MSFT,TSLA,AMZN,NVDA"
```

This will:
1. Process each stock independently through the full agent pipeline
2. Generate price charts and visualizations for each stock
3. Aggregate the investment recommendations into a comprehensive portfolio strategy
4. Create a professional, branded PDF report with Sam Butler Investment Agency formatting

Output files are stored in:
- `outputs/` - Text analysis from each agent for each stock
- `outputs/charts/` - Stock price and performance charts
- `outputs/reports/` - Final PDF investment reports

## System Architecture

### Data Sources
- **YFinance API**: Real-time prices and historical data
- **Financial Datasets API**: Financial news and additional market data
- **FRED API**: Economic indicator data

### Professional Agent Structure
The system emulates a professional investment firm with specialized roles:

- **Senior Equity Analyst (StockAgent)**: Conducts detailed technical and fundamental stock analysis
- **Head of Market Strategy (MarketAgent)**: Analyzes overall market conditions and sector trends
- **Chief Economist (MacroAgent)**: Evaluates macroeconomic indicators and policy impacts
- **Director of Financial Intelligence (NewsAgent)**: Analyzes news sentiment and market-moving events
- **Senior Portfolio Manager (InvestmentAgent)**: Provides actionable investment recommendations
- **Chief Investment Officer (ReportAggregationAgent)**: Synthesizes analyses into cohesive portfolio strategy

### Visual Report Generation

The system generates professional investment reports:

- **Stock Visualizations**: Price charts with moving averages and volume analysis
- **Comparative Analysis**: Performance benchmarking across portfolio holdings
- **Portfolio Recommendations**: Clear, visual summary of buy/sell/hold advice
- **Branded PDF Reports**: Professional formatting with Sam Butler Investment Agency branding

### Token-Efficient Processing

The system uses two approaches for handling multiple stocks:

1. **Token-optimized multi-stock analysis (`efficient_multi_stock.py`)**:
   - Processes each stock independently through the agent pipeline
   - Avoids context accumulation that would exceed token limits
   - Only aggregates at the final report stage

2. **Context-preserving analysis (`multi_stock_analysis.py`)**:
   - Preserves full context between agents but may reach token limits with many stocks
   - Better for detailed analysis of 2-3 stocks where relationships matter

## Implementation Details

### Output Handling

The system uses a custom approach to handle agent outputs:
- Each agent uses `output_type="string"` for consistent output format
- Structured markdown formatting ensures consistent parsing for visualizations
- A custom output cleaner ensures valid string formatting

### Error Handling

The system includes comprehensive error handling for API calls and agent operations:
- Graceful handling of connection errors with the OpenAI API
- Fallback mechanisms for missing or invalid API keys
- Continued execution even when errors occur with individual stocks

### Data Visualization

The system generates several types of visualizations:
- Individual stock price charts with moving averages
- Comparative performance charts normalizing multiple stocks to a common base
- Recommendation summary charts visualizing the buy/sell/hold advice

## License

MIT
