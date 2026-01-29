# AI assisted development
"""
Supervisor Agent - Entry Point and Orchestrator

ADK Usage:
- Inherits from google.adk.Agent (ADK base class)
- Uses ADK's initialization: name, instruction
- Uses ADK's run(input, state) method signature
- Exports root_agent for ADK CLI

A2A Usage (via server.py):
- Uses RemoteA2aAgent for agent-to-agent communication
- Uses AgentTool to wrap agents as tools
- Uses to_a2a() to create A2A server
"""
import json
import os
from pathlib import Path
from google.adk import Agent  
from .prompts import SYSTEM_PROMPT
from .state import initial_state
from .graph import determine_routes

# Set default model to gemini-1.5-flash via environment variable
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")

from app.config import get_data_folder, get_default_bug_file, get_workspace_root


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

    def _resolve_path(self, file_path):
        """
        Resolve file path to absolute path.
        Supports:
        - Absolute paths
        - Relative paths from workspace root
        - Relative paths from data folder
        """
        path = Path(file_path)
        root = get_workspace_root()
        data_folder = get_data_folder()

        if path.is_absolute():
            return path

        workspace_path = root / file_path
        if workspace_path.exists():
            return workspace_path

        data_path = root / data_folder / file_path
        if data_path.exists():
            return data_path

        return workspace_path

    def _load_bug_file(self, file_path):
        """
        Load bug data from a JSON file.
        Supports both single bug object and array of bugs.
        Returns the bug data and a flag indicating if it's an array.
        """
        resolved_path = self._resolve_path(file_path)
        root = get_workspace_root()
        data_folder = get_data_folder()

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}\n"
                f"Tried paths:\n"
                f"  - {resolved_path}\n"
                f"  - {root / data_folder / file_path}"
            )

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            is_array = isinstance(data, list)
            return data, is_array, str(resolved_path)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file: {file_path}\nError: {str(e)}")

    def run(self, input, state=None):
        if state is None:
            state = initial_state()

        bug = None
        bugs_list = None
        
        # Support multiple input formats
        if isinstance(input, dict):
            # Format 1: file_path specified
            if "file_path" in input:
                file_path = input["file_path"]
                try:
                    data, is_array, resolved_path = self._load_bug_file(file_path)
                    if is_array:
                        bugs_list = data
                        print(f"[Supervisor] Loaded {len(bugs_list)} bugs from: {resolved_path}")
                        # Use first bug for processing
                        bug = bugs_list[0] if bugs_list else None
                    else:
                        bug = data
                        print(f"[Supervisor] Loaded bug from: {resolved_path}")
                except (FileNotFoundError, ValueError) as e:
                    return {"error": str(e)}, state
            
            # Format 2: bug_id specified (direct bug payload)
            elif "bug_id" in input:
                bug = input
                print("[Supervisor] Received direct bug payload")
            
            # Format 3: bug_file_name (short name in data folder)
            elif "bug_file_name" in input:
                file_name = input["bug_file_name"]
                # Auto-add .json if not present
                if not file_name.endswith(".json"):
                    file_name += ".json"
                try:
                    data, is_array, resolved_path = self._load_bug_file(file_name)
                    if is_array:
                        bugs_list = data
                        print(f"[Supervisor] Loaded {len(bugs_list)} bugs from: {resolved_path}")
                        bug = bugs_list[0] if bugs_list else None
                    else:
                        bug = data
                        print(f"[Supervisor] Loaded bug from: {resolved_path}")
                except (FileNotFoundError, ValueError) as e:
                    return {"error": str(e)}, state
        
        # Default: try to load from default data folder (configurable via env)
        if bug is None:
            default_path = get_default_bug_file()
            try:
                data, is_array, resolved_path = self._load_bug_file(default_path)
                if is_array:
                    bugs_list = data
                    print(f"[Supervisor] Loaded {len(bugs_list)} bugs from default: {resolved_path}")
                    bug = bugs_list[0] if bugs_list else None
                else:
                    bug = data
                    print(f"[Supervisor] Loaded bug from default: {resolved_path}")
            except (FileNotFoundError, ValueError) as e:
                return {
                    "error": f"Could not load default bug file. {str(e)}\n"
                            f"Please provide input with 'file_path', 'bug_file_name', or 'bug_id'"
                }, state

        if bug is None:
            return {"error": "No bug data found or loaded"}, state

        routes = determine_routes()

        state["run_count"] += 1
        if "bugs_processed" in state:
            state["bugs_processed"].append(bug["bug_id"])

        result = {"routes": routes, "bug": bug}
        if bugs_list:
            result["bugs_list"] = bugs_list

        return result, state

# Export root_agent for ADK CLI (fallback if main.py is not found)
root_agent = SupervisorAgent()
