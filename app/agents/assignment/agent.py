from app.agents.common.base_agent import BaseAgent
from app.agents.common.common_guardrails import ensure_dict, ensure_list, ensure_keys
from app.schemas.engineer_schema import REQUIRED_ENGINEER_FIELDS
from .graph import select
from .state import initial_state
from .prompt import SYSTEM_PROMPT

class AssignmentAgent(BaseAgent):
    PROMPT = SYSTEM_PROMPT

    def run(self, input, state=None):
        ensure_dict(input)
        ensure_dict(input["bug"])
        ensure_list(input["engineers"])

        for e in input["engineers"]:
            ensure_keys(e, REQUIRED_ENGINEER_FIELDS)

        state = self.init_state(state, initial_state())
        chosen = select(input["engineers"], input["bug"])

        result = {
            "bug_id": input["bug"]["bug_id"],
            "assigned_to": chosen["ldap_id"]
        }

        state = self.update_state(state, result)
        return result, state

# Export root_agent for ADK CLI (fallback if main.py is not found)
root_agent = AssignmentAgent()