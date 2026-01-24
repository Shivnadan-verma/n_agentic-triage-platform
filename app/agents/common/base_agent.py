class BaseAgent:
    """
    Plain base agent.
    NO ADK Agent inheritance.
    Deterministic pipeline only.
    """

    PROMPT = ""

    def init_state(self, state, default):
        return state if state else default

    def update_state(self, state, record):
        state["run_count"] += 1
        state["history"].append(record)
        return state

    def run(self, input, state=None):
        raise NotImplementedError
