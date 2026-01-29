import json
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event

from app.config import get_engineers_path
from app.agents.common.common_guardrails import ensure_dict, ensure_list, ensure_keys
from app.agents.common.event import state_delta_event
from app.schemas.engineer_schema import REQUIRED_ENGINEER_FIELDS
from .graph import pick_best
from .state import initial_state


class AssignmentAgent(BaseAgent):
    """
    ADK Custom Agent (no LLM).
    Reads bug from ctx.session.state["bug"].
    Loads engineers from configurable path (env: ENGINEERS_FILENAME, DATA_FOLDER).
    Writes assignment into ctx.session.state["assignment"].
    """

    def __init__(self, name="AssignmentAgent"):
        super().__init__(name=name, sub_agents=[])

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        ctx.session.state.setdefault("assignment_state", initial_state())

        bug = ctx.session.state.get("bug")
        ensure_dict(bug, "bug")
        ensure_keys(bug, ["bug_id", "product", "severity", "description"], "bug")

        eng_path = get_engineers_path()
        with open(eng_path, "r", encoding="utf-8") as f:
            engineers = json.load(f)
        ensure_list(engineers, "engineers")

        for e in engineers:
            ensure_dict(e, "engineer")
            ensure_keys(e, REQUIRED_ENGINEER_FIELDS, "engineer")

        chosen = pick_best(engineers, bug)

        assignment = {
            "bug_id": bug["bug_id"],
            "assigned_to": {
                "ldap_id": chosen["ldap_id"],
                "name": chosen["name"],
                "role": chosen["role"],
            },
        }

        st = ctx.session.state["assignment_state"]
        st["run_count"] += 1
        st["history"].append(assignment)

        yield state_delta_event(self.name, {
            "assignment": assignment,
            "engineer": chosen,                 # full details
            "assignment_state": st,
        })
