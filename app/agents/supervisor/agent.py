# AI assisted development
"""
Supervisor Agent - Entry Point and Orchestrator

ADK Usage:
Inherits from google.adk.Agent (ADK base class)
Uses ADK's initialization: name, instruction
Uses ADK's run(input, state) method signature
Exports root_agent for ADK CLI

Manual Calls:
Currently calls other agents manually (not using ADK's sub_agents)
Could use: self.find_sub_agent() instead
"""
import json
import os
from google.adk import Agent  
from .prompts import SYSTEM_PROMPT
from .state import initial_state
from .graph import determine_routes

# Set default model to gemini-1.5-flash via environment variable
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")

class SupervisorAgent(Agent):
    """
    Supervisor Agent using Google ADK.
    
    ADK Features Used:
    - Inherits from google.adk.Agent
    - Uses ADK's __init__(name, instruction) pattern
    - Uses ADK's run(input, state) method signature
    - Uses gemini-1.5-flash model
    """

    def __init__(self):
        # Model is set via GOOGLE_GENAI_MODEL environment variable (gemini-1.5-flash)
        super().__init__(
            name="SupervisorAgent",      
            instruction=SYSTEM_PROMPT
        )

    def run(self, input, state=None):
        if state is None:
            state = initial_state()

        # Support both file_path and direct bug payload
        if isinstance(input, dict) and "file_path" in input:
            # Load bug from data folder
            file_path = input["file_path"]
            try:
                with open(file_path, "r") as f:
                    bug = json.load(f)
                print(f"[Supervisor] Loaded bug from: {file_path}")
            except FileNotFoundError:
                return {"error": f"File not found: {file_path}"}, state
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON in file: {file_path}"}, state
        elif isinstance(input, dict) and "bug_id" in input:
            # Direct bug payload
            bug = input
            print("[Supervisor] Received direct bug payload")
        else:
            # Default: try to load from default data folder
            default_path = "app/data/input/bug.json"
            try:
                with open(default_path, "r") as f:
                    bug = json.load(f)
                print(f"[Supervisor] Loaded bug from default: {default_path}")
            except FileNotFoundError:
                return {"error": "Input must contain either 'file_path' or bug payload with 'bug_id'"}, state

        routes = determine_routes()

        state["run_count"] += 1
        if "bugs_processed" in state:
            state["bugs_processed"].append(bug["bug_id"])

        return {"routes": routes, "bug": bug}, state

# Export root_agent for ADK CLI (fallback if main.py is not found)
root_agent = SupervisorAgent()
