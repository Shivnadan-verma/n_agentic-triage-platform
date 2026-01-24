# AI assisted development
"""
A2A Server for Supervisor Agent
Run this to start the Supervisor Agent as an A2A server with A2A tools
"""
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import AgentTool
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Load environment variables
load_dotenv()

# Set up logging for A2A
log_dir = os.path.join(os.getenv("TEMP", "."), "agents_log")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir,
    f"supervisor_agent.{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
# -> logging done for A2A in the terminal and saved in a local file
logging.getLogger("google.adk").setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.INFO)

# Create A2A tools for other agents
bug_analysis_tool = AgentTool(
    RemoteA2aAgent(
        name="bug_analysis",
        description="Agent that analyzes bugs by calculating impact scores based on severity. High/Critical severity gets 80, others get 40.",
        agent_card="http://localhost:19001/.well-known/agent-card.json"
    )
)

assignment_tool = AgentTool(
    RemoteA2aAgent(
        name="assignment",
        description="Agent that assigns bugs to engineers based on skills, product match, workload, rating, and acceptance rate.",
        agent_card="http://localhost:19002/.well-known/agent-card.json"
    )
)

# Create root agent with A2A tools
root_agent = Agent(
    name="supervisor_agent",
    model="gemini-1.5-flash",
    instruction="""You are a Supervisor Agent that orchestrates bug triage workflow.

    Your workflow:
    1. Receive bug payload (from file_path or direct input)
    2. Load/create bug JSON object
    3. Use bug_analysis tool to analyze the bug
    4. Use assignment tool to assign the bug to an engineer
    5. Return the complete result
    
    Always use the tools to delegate work to specialized agents.
    """,
    tools=[bug_analysis_tool, assignment_tool],
)

# Convert to A2A app
a2a_app = to_a2a(root_agent, port=19000)

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Supervisor Agent A2A server on port 19000...")
    print("Make sure Bug Analysis Agent (port 19001) and Assignment Agent (port 19002) are running!")
    print(f"Log file: {log_file}")
    print("=" * 60)
    a2a_app.run()
