import os
import json
from swarms import Agent
from dotenv import load_dotenv
from custom_agent_rearrange import CustomAgentRearrange

# Load environment variables
load_dotenv()

# Get API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validate OpenAI API key format
if not OPENAI_API_KEY or not OPENAI_API_KEY.startswith('sk-'):
    print("Warning: Invalid OpenAI API key format. Using dummy key for testing.")
    # Use a dummy key with the correct format for testing
    OPENAI_API_KEY = 'sk-dummy1234567890abcdefghijklmnopqrstuvwxyz1234567890abcdefgh'
    
# Set the API key in the environment
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Define a simple output cleaner function that ensures the output is a string
def simple_output_cleaner(text):
    """
    A simple function to ensure the output is a valid string format.
    """
    return text

# Create specialized agents
stock_agent = Agent(
    agent_name="StockAgent",
    system_prompt="""You are an expert stock analyst. Your task is to analyze real-time stock data and provide insights.
    Consider price movements, trading volume, and any available company information.
    Provide a concise summary of the stock's current status and any notable trends or events.""",
    model_name="gpt-4o",
    temperature=0.7,
    max_loops=1,
    streaming_on=False,
    output_cleaner=simple_output_cleaner,
    output_type="string",
    verbose=True,
    api_key=OPENAI_API_KEY,  
)

market_agent = Agent(
    agent_name="MarketAgent",
    system_prompt="""You are a market analysis expert. Your task is to analyze overall market conditions using real-time data.
    Consider major indices, sector performance, and market-wide trends.
    Provide a concise summary of current market conditions and any significant developments.""",
    model_name="gpt-4o",
    temperature=0.7,
    max_loops=1,
    streaming_on=False,
    output_cleaner=simple_output_cleaner,
    output_type="string",
    verbose=True,
    api_key=OPENAI_API_KEY,  
)

macro_agent = Agent(
    agent_name="MacroAgent",
    system_prompt="""You are a macroeconomic analysis expert. Your task is to analyze key economic indicators and provide insights on the overall economic situation.
    Consider GDP growth, inflation rates, unemployment figures, and other relevant economic data.
    Provide a concise summary of the current economic situation and any potential impacts on financial markets.""",
    model_name="gpt-4o",
    temperature=0.7,
    max_loops=1,
    streaming_on=False,
    output_cleaner=simple_output_cleaner,
    output_type="string",
    verbose=True,
    api_key=OPENAI_API_KEY,  
)

news_agent = Agent(
    agent_name="NewsAgent",
    system_prompt="""You are a financial news analyst. Your task is to analyze recent news articles related to specific stocks or the overall market.
    Consider the potential impact of news events on stock prices or market trends.
    Provide a concise summary of key news items and their potential market implications.""",
    model_name="gpt-4o",
    temperature=0.7,
    max_loops=1,
    streaming_on=False,
    output_cleaner=simple_output_cleaner,
    output_type="string",
    verbose=True,
    api_key=OPENAI_API_KEY,  
)

investment_agent = Agent(
    agent_name="InvestmentAgent",
    system_prompt="""You are an investment advisor specializing in stock recommendations. 
    Your task is to analyze the combined insights from stock analysis, market conditions, macroeconomic factors, and news events.
    Based on this comprehensive analysis, provide a clear BUY, SELL, or HOLD recommendation for the stock.
    Include your reasoning and expected 1-year returns (percentage estimate).
    Format your recommendation as follows:
    
    RECOMMENDATION: [BUY/SELL/HOLD]
    EXPECTED 1-YEAR RETURN: [percentage]
    CONFIDENCE: [High/Medium/Low]
    RATIONALE: [Your detailed explanation]
    RISK FACTORS: [Key risks to your recommendation]
    """,
    model_name="gpt-4o",
    temperature=0.7,
    max_loops=1,
    streaming_on=False,
    output_cleaner=simple_output_cleaner,
    output_type="string",
    verbose=True,
    api_key=OPENAI_API_KEY,  
)

# Combine specialized agents into a multi-agent system
agents = [stock_agent, market_agent, macro_agent, news_agent, investment_agent]
flow = "StockAgent -> MarketAgent -> MacroAgent -> NewsAgent -> InvestmentAgent"

# Create the agent system using CustomAgentRearrange
agent_system = CustomAgentRearrange(
    agents=[stock_agent, market_agent, macro_agent, news_agent, investment_agent],
    flow="StockAgent -> MarketAgent -> MacroAgent -> NewsAgent -> InvestmentAgent",
    max_loops=1,
    output_type="string",  # Use string output type to avoid JSON parsing issues
    verbose=True,
)
