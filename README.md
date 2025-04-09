# Swarms Financial Agent

A multi-agent financial analysis system built with the Swarms framework. This system combines specialized AI agents to analyze stocks, market conditions, economic indicators, and financial news in real-time to provide investment recommendations.

## Features

- Real-time stock data analysis using Financial Datasets API
- Multi-agent system with specialized agents for different aspects of financial analysis
- Custom agent flow implementation for reliable output handling
- Comprehensive financial insights combining stock, market, economic, and news analysis
- Final investment recommendation (BUY/SELL/HOLD) with expected returns

## Setup

### Prerequisites

- Python 3.11+
- API keys for:
  - OpenAI API (for the AI agents)
  - Financial Datasets API (for market data)

### Installation

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -U swarms pandas numpy matplotlib aiohttp
   ```

3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   FIN_DATA_API_KEY=your_financial_datasets_api_key
   ```

## Usage

Run the test script to analyze a stock:

```
python test_agent_system.py
```

You can set the stock ticker to analyze by setting the `TEST_TICKER` environment variable:

```
TEST_TICKER=MSFT python test_agent_system.py
```

## System Architecture

### Data Sources
- **Financial Datasets API**: Real-time prices, historical data, and financial news

### Agent System
- **StockAgent**: Analyzes individual stock performance and trends
- **MarketAgent**: Analyzes overall market conditions and their impact on the stock
- **MacroAgent**: Analyzes macroeconomic indicators and their influence
- **NewsAgent**: Analyzes financial news and their market impact
- **InvestmentAgent**: Provides final investment recommendation based on all analyses

The agents work in a sequential flow, with each agent building upon the analysis of the previous ones.

### Custom Agent Flow

The system implements a custom agent flow to handle the output between agents properly:

1. Each agent is run individually using the `run_agent_safely` function
2. Outputs from previous agents are explicitly passed to subsequent agents
3. All analyses are combined into a comprehensive final output

This approach bypasses JSON parsing issues in the standard Swarms flow mechanism while still leveraging the specialized agent capabilities.

## Implementation Details

### Output Handling

The system uses a custom approach to handle agent outputs:
- Each agent uses `output_type="string"` for consistent output format
- A custom output cleaner ensures valid string formatting
- The `run_agent_safely` function directly accesses the agent's internal methods to bypass JSON parsing issues

### Error Handling

The system includes comprehensive error handling for API calls and agent operations, with detailed logging to help diagnose issues.

## API Integration

The system uses the Financial Datasets API (financialdatasets.ai) for retrieving:
- Real-time price snapshots for stocks
- Historical price data with customizable intervals
- Recent news articles for a given ticker

## License

MIT
