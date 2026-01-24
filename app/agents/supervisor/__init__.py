# AI assisted development
# Supervisor agent - root_agent for: adk run app/agents/supervisor
# Ensure project root in sys.path when adk run loads this (else: No module named 'app')
import sys
from pathlib import Path

_proj = Path(__file__).resolve().parent.parent.parent.parent
if str(_proj) not in sys.path:
    sys.path.insert(0, str(_proj))

from .agent import SupervisorAgent, root_agent

__all__ = ["SupervisorAgent", "root_agent"]
