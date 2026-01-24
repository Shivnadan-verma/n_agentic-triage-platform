import json
import re
from pathlib import Path
from typing import AsyncGenerator

from google.genai import types
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions

from app.agents.common.common_guardrails import ensure_dict, ensure_keys
from app.agents.common.event import state_delta_event
from app.agents.bug_analysis.agent import BugAnalysisAgent
from app.agents.assignment.agent import AssignmentAgent
from app.schemas.bug_schema import REQUIRED_BUG_FIELDS
from .state import initial_state
from .graph import routes

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "app" / "data" / "input"

_HELP_MSG = """I need a bug to process. Options:
1. Put a bug in session state as input_bug (when using Runner/session).
2. Say a bug_id (e.g. 1001 or BUG-1001) to load from app/data/input/bugs.json.
3. Paste JSON: {"bug_id":"BUG-1001","severity":"High","product":"Checkout","description":"...","required_skills":["Payments"]}.
4. I'll also try app/data/input/bug.json if none of the above."""


def _get_user_text(ctx: InvocationContext) -> str:
    if not ctx.user_content or not ctx.user_content.parts:
        return ""
    return " ".join((p.text or "") for p in ctx.user_content.parts).strip()


def _resolve_bug_from_input(ctx: InvocationContext) -> dict | None:
    bug = ctx.session.state.get("input_bug")
    if isinstance(bug, dict):
        return bug
    text = _get_user_text(ctx)
    if not text:
        return None
    # Try JSON
    text = text.strip()
    if text.startswith("{"):
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and obj.get("bug_id"):
                return obj
        except json.JSONDecodeError:
            pass
    # Try bug_id: 1001, BUG-1001, "bug 1001", "bug id 1001"
    m = re.search(r"(?:BUG-)?(\d+)", text, re.IGNORECASE)
    if m:
        bid = f"BUG-{m.group(1)}"
        path = _DATA_DIR / "bugs.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            bugs = data if isinstance(data, list) else [data]
            for b in bugs:
                if (b.get("bug_id") or "").upper() == bid:
                    return b
    return None


def _load_default_bug() -> dict | None:
    path = _DATA_DIR / "bug.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else (data[0] if data else None)


class SupervisorAgent(BaseAgent):
    """
    ADK Custom Agent orchestrator.
    """

    def __init__(self, name="SupervisorAgent"):
        bug_analysis = BugAnalysisAgent()
        assignment = AssignmentAgent()
        super().__init__(name=name, sub_agents=[bug_analysis, assignment])

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        ctx.session.state.setdefault("supervisor_state", initial_state())

        bug = _resolve_bug_from_input(ctx)
        if not isinstance(bug, dict):
            bug = _load_default_bug()
        if not isinstance(bug, dict):
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                content=types.Content(role="model", parts=[types.Part(text=_HELP_MSG)]),
            )
            return
        try:
            ensure_dict(bug, "input_bug")
            ensure_keys(bug, REQUIRED_BUG_FIELDS, "bug")
        except ValueError as e:
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                content=types.Content(role="model", parts=[types.Part(text=f"Invalid bug: {e}")]),
            )
            return

        # update supervisor state
        st = ctx.session.state["supervisor_state"]
        st["run_count"] += 1
        st["bugs_processed"].append(bug["bug_id"])

        # store canonical bug for downstream agents
        yield state_delta_event(self.name, {
            "bug": bug,
            "routes": routes(),
            "supervisor_state": st,
        })

        # run sub-agents (order: bug_analysis, then assignment)
        bug_analysis = next(a for a in self.sub_agents if a.name == "BugAnalysisAgent")
        assignment = next(a for a in self.sub_agents if a.name == "AssignmentAgent")
        async for ev in bug_analysis.run_async(ctx):
            yield ev
        async for ev in assignment.run_async(ctx):
            yield ev

        # build final output
        analysis = ctx.session.state.get("analysis")
        assignment = ctx.session.state.get("assignment")
        engineer = ctx.session.state.get("engineer")

        final_result = {
            "routes": ctx.session.state.get("routes", []),
            "bug": bug,
            "analysis": analysis,
            "assignment": assignment,
            "engineer": engineer,
        }

        # Build user-visible summary (ADK CLI shows Event.content, not state_delta)
        ato = (assignment or {}).get("assigned_to") or {}
        eng = engineer or {}
        an = ato.get("name") if isinstance(ato, dict) else None
        if not an:
            an = eng.get("name") or (ato.get("ldap_id") if isinstance(ato, dict) else None) or "—"
        ldap = ato.get("ldap_id") if isinstance(ato, dict) else str(ato) if ato else "—"
        impact = (analysis or {}).get("impact_score", "?")
        summary = (
            f"Bug {bug['bug_id']} has been processed.\n"
            f"- Impact score: {impact}\n"
            f"- Assigned to: {an} ({ldap})"
        )
        if eng and eng.get("skill_set"):
            summary += f"\n- Skills: {', '.join(eng.get('skill_set', []))}"
        summary += "\n"

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=summary)]),
            actions=EventActions(state_delta={"final_result": final_result}),
        )


root_agent = SupervisorAgent()
