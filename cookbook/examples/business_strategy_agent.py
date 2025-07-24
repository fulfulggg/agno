"""
📈 Business Strategy Agent Team
This example demonstrates a sophisticated team of AI agents designed to perform a comprehensive business strategy analysis for a given company.
The team consists of three specialized agents:
1.  **Market Research Agent**: Conducts web searches for market trends, news, and competitor analysis.
2.  **Financial Analyst Agent**: Fetches and analyzes financial data, such as stock performance and fundamentals.
3.  **Strategy Analyst Agent**: Synthesizes the gathered information into strategic frameworks like SWOT analysis and provides recommendations.
This multi-agent system showcases how to combine specialized tools and structured outputs to tackle complex, real-world tasks.
Run `pip install openai duckduckgo-search yfinance agno` to install dependencies.
"""
from textwrap import dedent
from typing import List, Optional
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.team.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools

# --- 1. Define Structured Outputs (Pydantic Models) ---
class SWOTAnalysis(BaseModel):
    """A model for a SWOT analysis."""
    strengths: List[str] = Field(..., description="Internal strengths of the company.")
    weaknesses: List[str] = Field(..., description="Internal weaknesses of the company.")
    opportunities: List[str] = Field(..., description="External opportunities for the company.")
    threats: List[str] = Field(..., description="External threats to the company.")

class StrategyReport(BaseModel):
    """The final, comprehensive business strategy report."""
    company_name: str = Field(..., description="The name of the company being analyzed.")
    market_summary: str = Field(..., description="A summary of the current market landscape, including trends and news.")
    financial_summary: str = Field(..., description="A summary of the company's financial performance.")
    swot_analysis: SWOTAnalysis = Field(..., description="A detailed SWOT analysis.")
    strategic_recommendations: List[str] = Field(..., description="Actionable strategic recommendations based on the analysis.")

# --- 2. Create Specialized Agents ---
market_research_agent = Agent(
    name="Market Research Agent",
    role="To find the latest market trends, news, and competitor information using web searches.",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools(num_results=5)],
    instructions=dedent("""\
        - You are a world-class market researcher.
        - Your goal is to find relevant, recent, and impactful information.
        - Focus on market size, growth trends, key competitors, and recent news.
        - Provide a concise summary of your findings with sources.
    """),
)

financial_analyst_agent = Agent(
    name="Financial Analyst Agent",
    role="To provide a detailed analysis of a company's financial performance using stock market data.",
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools(stock_price=True, stock_fundamentals=True, company_info=True)],
    instructions=dedent("""\
        - You are a seasoned financial analyst.
        - Use the available tools to get stock price, fundamentals, and company info.
        - Present the data clearly, perhaps in a markdown table.
        - Provide a brief interpretation of the financial health of the company.
    """),
)

strategy_analyst_agent = Agent(
    name="Strategy Analyst Agent",
    role="To synthesize market and financial data into a strategic analysis.",
    model=OpenAIChat(id="gpt-4o"),
    instructions=dedent("""\
        - You are a master business strategist.
        - Take the information provided by the other agents.
        - Your primary output is to create a SWOT analysis.
        - Do not use any tools. Your job is to reason and structure the information.
    """),
)

# --- 3. Assemble the Team ---
business_strategy_team = Team(
    name="Business Strategy Team",
    mode="coordinate",
    model=OpenAIChat(id="gpt-4o"),
    members=[market_research_agent, financial_analyst_agent, strategy_analyst_agent],
    response_model=StrategyReport,
    instructions=dedent("""\
        Your mission is to create a comprehensive business strategy report for a given company.
        1.  **Delegate**: Assign tasks to the appropriate agents.
            - Use the Market Research Agent for news, trends, and competitor analysis.
            - Use the Financial Analyst Agent for financial data.
        2.  **Synthesize**: Once you have the market and financial data, have the Strategy Analyst Agent create a SWOT analysis.
        3.  **Report**: Compile all the information into the final `StrategyReport` format.
            - Create a high-level summary for the market and financial sections.
            - Formulate actionable strategic recommendations based on the SWOT analysis.
        - The final output must be a complete `StrategyReport`. Do not output intermediate steps.
    """),
    markdown=True,
    show_members_responses=True,
)

# --- 4. Run the Team ---
if __name__ == "__main__":
    company_query = "Analyze the business strategy for Tesla (TSLA)."
    business_strategy_team.print_response(company_query, stream=True)
