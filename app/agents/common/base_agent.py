from typing import ClassVar
import os
from google.adk import Agent

# Set default model to gemini-1.5-flash via environment variable
os.environ.setdefault("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")

class BaseAgent(Agent):
    PROMPT: ClassVar[str] = ""

    def __init__(self, name: str = None):
        # Use instruction instead of system_prompt, and name is required
        # Model is set via GOOGLE_GENAI_MODEL environment variable
        super().__init__(
            name=name or self.__class__.__name__,
            instruction=self.PROMPT
        )

    def init_state(self, state, default):
        return state if state else default

    def update_state(self, state, record):
        state["run_count"] += 1
        state["history"].append(record)
        return state
