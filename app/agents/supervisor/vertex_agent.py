# AI assisted development
"""
Minimal Supervisor Agent for Vertex AI Agent Engine deployment.

No app.config, no file I/O – only accepts direct bug payload (dict with bug_id).
Use this agent for deploy_vertex_agent.py so the remote container starts without
depending on local paths or config.
"""
import os
from google.adk import Agent

from .prompts import SYSTEM_PROMPT
from .state import initial_state
from .graph import determine_routes

os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")


class VertexSupervisorAgent(Agent):
    """
    Supervisor Agent for Vertex: in-memory only, no file paths.
    Input must be a dict with bug_id (direct bug payload).
    """

    def __init__(self):
        super().__init__(
            name="SupervisorAgent",
            instruction=SYSTEM_PROMPT,
        )

    def run(self, input, state=None):
        if state is None:
            state = initial_state()

        if not isinstance(input, dict) or "bug_id" not in input:
            return {
                "error": "Vertex agent expects direct bug payload with bug_id, severity, product, description."
            }, state

        bug = input
        routes = determine_routes()
        state["run_count"] = state.get("run_count", 0) + 1
        if "bugs_processed" in state:
            state["bugs_processed"].append(bug["bug_id"])

        return {"routes": routes, "bug": bug}, state


# Use this for Vertex Agent Engine deploy (no file I/O)
vertex_root_agent = VertexSupervisorAgent()
