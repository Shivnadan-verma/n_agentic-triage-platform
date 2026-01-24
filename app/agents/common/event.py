import time
import uuid
from google.adk.events import Event, EventActions

def state_delta_event(author: str, delta: dict) -> Event:
    return Event(
        invocation_id=str(uuid.uuid4()),
        author=author,
        timestamp=time.time(),
        actions=EventActions(state_delta=delta),
    )
