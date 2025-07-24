"""Simple AGNO WebUI Demo - No Database Required"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.app.fastapi import FastAPIApp

# Create a simple agent without database dependencies
simple_agent = Agent(
    name="Simple Assistant",
    model=OpenAIChat(id="gpt-4o"),
    instructions="""You are a helpful AI assistant. 
    Be friendly, concise, and informative in your responses.""",
    markdown=True,
)

# Create the FastAPI app
fastapi_app = FastAPIApp(
    agents=[simple_agent],
    name="Simple AGNO WebUI",
    app_id="simple-webui",
    description="A simple WebUI demo without database requirements",
)

app = fastapi_app.get_app()

if __name__ == "__main__":
    print("\n🚀 Starting AGNO WebUI Demo...")
    print("📌 Access the WebUI at: http://localhost:8000/docs")
    print("⏹️  Press Ctrl+C to stop the server\n")
    
    fastapi_app.serve(app="simple_webui_demo:app", port=8000, reload=True)
