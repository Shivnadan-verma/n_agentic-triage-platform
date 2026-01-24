import asyncio
import json

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from app.agents.supervisor.agent import SupervisorAgent
from app.agents.supervisor.configuration import APP_NAME

USER_ID = "local_user_1"
SESSION_ID = "triage_session_1"
NEW_MESSAGE = types.Content(role="user", parts=[types.Part(text="Process bug")])


async def main():
    session_service = InMemorySessionService()
    agent = SupervisorAgent()
    runner = Runner(app_name=APP_NAME, session_service=session_service, agent=agent)

    with open("app/data/input/bug.json", "r", encoding="utf-8") as f:
        bug = json.load(f)

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={"input_bug": bug},
    )

    async for _ in runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=NEW_MESSAGE
    ):
        pass

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    print(json.dumps(session.state.get("final_result"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
