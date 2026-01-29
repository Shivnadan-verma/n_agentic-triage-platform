# AI assisted development
"""
Main entry point for Agentic Triage Platform.

Uses ADK Runner + InMemorySessionService. For each bug: create session with
input_bug, run_async with new_message, read final_result from session.state.

ADK: adk run app/agents/supervisor — for interactive mode.
"""
import asyncio
import json
import sys
from pathlib import Path

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config import get_data_path, get_bugs_filenames
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.supervisor.configuration import APP_NAME

USER_ID = "main_user"
NEW_MESSAGE = types.Content(role="user", parts=[types.Part(text="Process bug")])


async def run_one(session_service, runner, bug, session_id):
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
        state={"input_bug": bug},
    )
    async for _ in runner.run_async(
        user_id=USER_ID, session_id=session_id, new_message=NEW_MESSAGE
    ):
        pass
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session_id
    )
    return session.state.get("final_result") if session else None


async def main_async():
    print("=" * 60)
    print("Agentic Triage Platform - Multiple Bug Analysis")
    print("=" * 60)

    session_service = InMemorySessionService()
    agent = SupervisorAgent()
    runner = Runner(
        app_name=APP_NAME, session_service=session_service, agent=agent
    )

    bugs_file = None
    for name in get_bugs_filenames():
        path = get_data_path(name)
        if path.exists():
            bugs_file = path
            break
    if not bugs_file:
        raise FileNotFoundError("No bugs file found; set BUGS_FILENAMES or add bugs.json/bug.json in data folder")
    with open(bugs_file, "r", encoding="utf-8") as f:
        bugs = json.load(f)
    bugs = bugs if isinstance(bugs, list) else [bugs]
    print(f"\n[Input] Loading bugs from {bugs_file}...")
    print(f"Found {len(bugs)} bugs to process\n")

    all_results = []
    for idx, bug in enumerate(bugs, 1):
        print("=" * 60)
        print(f"Processing Bug {idx}/{len(bugs)}: {bug['bug_id']}")
        print("=" * 60)
        sid = f"triage_{idx}_{bug['bug_id']}"
        result = await run_one(session_service, runner, bug, sid)
        if not result:
            print("\n[Error] No final_result in session.\n")
            continue
        if "error" in result:
            print(f"\n[Error] {result['error']}\n")
            continue

        b = result["bug"]
        a = result.get("analysis") or {}
        asn = result.get("assignment") or {}
        eng = result.get("engineer")

        print(f"\n[1] Bug Data:")
        print(f"   Bug ID: {b['bug_id']}")
        print(f"   Severity: {b['severity']}")
        print(f"   Product: {b['product']}")
        print(f"   Description: {b['description']}")
        print(f"   Routes: {result.get('routes', [])}")

        print(f"\n[2] Bug Analysis:")
        print(f"   Impact Score: {a.get('impact_score', '?')}")

        ato = asn.get("assigned_to") or {}
        ato_ldap = ato.get("ldap_id") if isinstance(ato, dict) else asn.get("assigned_to")
        ato_name = ato.get("name", ato_ldap) if isinstance(ato, dict) else ato_ldap
        print(f"\n[3] Assignment:")
        print(f"   Assigned to: {ato_name} ({ato_ldap})")
        if eng:
            print(f"   Engineer: {eng.get('name')} ({eng.get('role')})")
            print(f"   Skills: {', '.join(eng.get('skill_set', []))}")
            print(f"   Product: {eng.get('product')}")
            print(f"   Rating: {eng.get('rating')}")
            print(f"   Workload: {eng.get('total_no_of_bugs')} bugs")

        all_results.append(result)
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY - All Bugs Processed")
    print("=" * 60)
    print(f"\nTotal Bugs: {len(all_results)}")
    print(f"\nBreakdown by Severity:")
    severity_count = {}
    for r in all_results:
        sev = r["bug"]["severity"]
        severity_count[sev] = severity_count.get(sev, 0) + 1
    for sev, count in sorted(severity_count.items()):
        print(f"  {sev}: {count}")

    print(f"\nBreakdown by Product:")
    product_count = {}
    for r in all_results:
        prod = r["bug"]["product"]
        product_count[prod] = product_count.get(prod, 0) + 1
    for prod, count in sorted(product_count.items()):
        print(f"  {prod}: {count}")

    print(f"\nBreakdown by Impact Score:")
    high_impact = sum(1 for r in all_results if (r.get("analysis") or {}).get("impact_score") == 80)
    low_impact = sum(1 for r in all_results if (r.get("analysis") or {}).get("impact_score") == 40)
    print(f"  High Impact (80): {high_impact}")
    print(f"  Low Impact (40): {low_impact}")

    print(f"\nAssignment Summary:")
    engineer_assignments = {}
    for r in all_results:
        asn = r.get("assignment") or {}
        ato = asn.get("assigned_to")
        eng_id = ato.get("ldap_id") if isinstance(ato, dict) else str(ato)
        engineer_assignments[eng_id] = engineer_assignments.get(eng_id, 0) + 1
    for eng_id, count in sorted(engineer_assignments.items()):
        eng_name = eng_id
        for r in all_results:
            asn = r.get("assignment") or {}
            ato = asn.get("assigned_to")
            eid = ato.get("ldap_id") if isinstance(ato, dict) else str(ato)
            if eid == eng_id and r.get("engineer"):
                eng_name = r["engineer"].get("name", eng_id)
                break
        print(f"  {eng_name} ({eng_id}): {count} bugs")

    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main_async())
