# AI assisted development
"""
Deploy Supervisor Agent (ADK root_agent) to Vertex AI Agent Engine.

Run from project root:
  python deploy_vertex_agent.py

Requires: google-cloud-aiplatform[agent_engines,adk] or equivalent.
Set PROJECT_ID, LOCATION, STAGING_BUCKET and ensure:
  - gcloud auth application-default login
  - Vertex AI API enabled
  - Staging bucket exists (e.g. gs://YOUR_PROJECT-agent-engine)

If deployment fails with "failed to start and cannot serve traffic":
  - Check Cloud Logging for the Reasoning Engine resource (project/region)
  - https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/troubleshooting/deploy
"""
import sys
from pathlib import Path

# Run from project root so app package is importable
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import vertexai
# Agent under app/ so remote bundle (which has app/) can import it
from app.vertex_agent_standalone import vertex_root_agent

# Vertex AI Agent Engine: AdkApp (use reasoning_engines if agent_engines not in your SDK)
try:
    from vertexai.agent_engines import AdkApp
except (ImportError, AttributeError):
    from vertexai.preview.reasoning_engines import AdkApp

PROJECT_ID = "agents-485801"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://agents-485801-agent-engine"


def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

    # Pickle must reference app.vertex_agent_standalone so remote (which has app/) can unpickle
    agent_module = vertex_root_agent.__class__.__module__
    if agent_module != "app.vertex_agent_standalone":
        raise RuntimeError(
            f"Agent class module is '{agent_module}'; must be 'app.vertex_agent_standalone'. "
            "Fix: from app.vertex_agent_standalone import vertex_root_agent"
        )
    print("Agent module for remote:", agent_module)

    app = AdkApp(agent=vertex_root_agent)

    # Run from project root so SDK bundles app/ (app/__init__.py + app/vertex_agent_standalone.py)
    if not (_project_root / "app" / "vertex_agent_standalone.py").is_file():
        raise FileNotFoundError("app/vertex_agent_standalone.py not found; run from project root")

    # Staging bucket must exist and be in same region as LOCATION; Vertex uses Python 3.10
    # Deployment can take 5–15+ minutes; do not interrupt
    print("Creating agent on Vertex AI Agent Engine (this may take several minutes)...")
    remote_agent = client.agent_engines.create(
        agent=app,
        config={
            "staging_bucket": STAGING_BUCKET,
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk]>=1.49.0",
                "google-adk",
                "google-genai",
                "pydantic>=2.6.4",
                "cloudpickle>=2.2.0,<4",
                "python-dotenv",
            ],
        },
    )

    print("DEPLOYED:", remote_agent.resource_name)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        err = str(e)
        if "failed to start" in err.lower() and "reasoningEngines/" in err:
            import re
            m = re.search(r"projects/(\d+)/locations/([^/]+)/reasoningEngines/(\d+)", err)
            if m:
                proj_num, loc, re_id = m.group(1), m.group(2), m.group(3)
                log_url = (
                    "https://console.cloud.google.com/logs/query;"
                    f'query=resource.type="aiplatform.googleapis.com/ReasoningEngine"%0Aresource.labels.reasoning_engine_id="{re_id}"%0Aseverity>=ERROR;'
                    f"projectNumber={proj_num}"
                )
                print("\n--- Real error is in Cloud Logging (not this traceback) ---")
                print("Open:", log_url)
                print("Or: Logs Explorer → Resource type = Vertex AI Reasoning Engine → reasoning_engine_id =", re_id)
            print("Troubleshooting: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/troubleshooting/deploy")
        raise
