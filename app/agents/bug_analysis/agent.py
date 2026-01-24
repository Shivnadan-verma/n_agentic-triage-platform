from typing import AsyncGenerator
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event

from app.agents.common.common_guardrails import ensure_dict, ensure_keys
from app.agents.common.event import state_delta_event
from .graph import impact_score
from .state import initial_state

class BugAnalysisAgent(BaseAgent):
    """
    ADK Custom Agent (no LLM).
    Writes analysis into ctx.session.state["analysis"].
    """

    def __init__(self, name="BugAnalysisAgent"):
        super().__init__(name=name, sub_agents=[])

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # init agent local state
        ctx.session.state.setdefault("bug_analysis_state", initial_state())

        bug = ctx.session.state.get("bug")
        ensure_dict(bug, "bug")
        ensure_keys(bug, ["bug_id", "severity"], "bug")

        analysis = {
            "bug_id": bug["bug_id"],
            "impact_score": impact_score(bug["severity"]),
        }

        st = ctx.session.state["bug_analysis_state"]
        st["run_count"] += 1
        st["history"].append(analysis)

        # persist in session.state via state_delta
        yield state_delta_event(self.name, {
            "analysis": analysis,
            "bug_analysis_state": st,
        })
