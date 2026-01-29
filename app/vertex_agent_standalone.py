# AI assisted development
# app/vertex_agent_standalone.py
import os
from google.adk import Agent

os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")

PROMPT = (
    "You are a Supervisor Agent for bug triage. "
    "You orchestrate bug analysis and assignment."
)

class VertexSupervisorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="SupervisorAgent",
            instruction=PROMPT,
        )

    def run(self, input, state=None):
        state = state or {"run_count": 0, "bugs_processed": []}

        if not isinstance(input, dict) or "bug_id" not in input:
            return {
                "error": "Expect bug payload with bug_id, severity, product, description."
            }, state

        bug = input
        routes = ["bug_analysis", "assignment"]

        state["run_count"] += 1
        state.setdefault("bugs_processed", []).append(bug["bug_id"])

        return {
            "routes": routes,
            "bug": bug,
        }, state


vertex_root_agent = VertexSupervisorAgent()
