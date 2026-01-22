from .graph import analyze
from .state import initial_state
from .prompt import SYSTEM_PROMPT
from app.agents.common.common_guardrails import ensure_dict, ensure_keys
from app.agents.common.base_agent import BaseAgent

class BugAnalysisAgent(BaseAgent):
    PROMPT = SYSTEM_PROMPT

    def run(self, input, state=None):
        ensure_dict(input)
        ensure_keys(input, ["bug_id", "severity"])

        state = self.init_state(state, initial_state())
        impact = analyze(input["severity"])

        result = {"bug_id": input["bug_id"], "impact_score": impact}
        state = self.update_state(state, result)

        return result, state

# Export root_agent for ADK CLI (fallback if main.py is not found)
root_agent = BugAnalysisAgent()