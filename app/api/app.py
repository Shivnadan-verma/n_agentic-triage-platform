# AI assisted development
"""
FastAPI application for Agentic Triage Platform.

Endpoints:
- GET  /health          — Health check (Vertex / load balancers)
- POST /predict         — Vertex AI custom prediction (instances → predictions), port 8080
- POST /triage          — Triage a single bug (JSON body)
- POST /triage/batch    — Triage multiple bugs (JSON array)
- GET  /data/bugs       — List bugs from default data file
- GET  /data/engineers  — List engineers from default data file
"""
import asyncio
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root is on sys.path so "app" package resolves (e.g. when running python app/api/app.py)
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import get_data_path, get_bugs_filenames, get_engineers_filename
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.supervisor.state import initial_state
from app.agents.bug_analysis.graph import impact_score
from app.agents.assignment.graph import pick_best

# ---------------------------------------------------------------------------
# Pydantic models for request/response
# ---------------------------------------------------------------------------

class BugInput(BaseModel):
    """Single bug payload for triage."""
    bug_id: str = Field(..., description="Unique bug identifier")
    severity: str = Field(..., description="e.g. High, Critical, Medium, Low")
    product: str = Field(..., description="Product name")
    description: str = Field(..., description="Bug description")
    required_skills: list[str] = Field(default_factory=list, description="Skills needed")


class BatchTriageRequest(BaseModel):
    """Request body for batch triage: array of bugs."""
    bugs: list[BugInput] = Field(..., description="List of bugs to triage")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bugs": [
                        {
                            "bug_id": "BUG-1001",
                            "severity": "High",
                            "product": "Checkout",
                            "description": "Payment timeout during peak hours",
                            "required_skills": ["Payments", "Java"],
                        },
                        {
                            "bug_id": "BUG-1002",
                            "severity": "Medium",
                            "product": "Orders",
                            "description": "Order status not updating correctly",
                            "required_skills": ["Database"],
                        },
                    ]
                }
            ]
        }
    }


class TriageResponse(BaseModel):
    """Response for a single triage (subset of final_result)."""
    bug: dict
    routes: list = []
    analysis: dict = {}
    assignment: dict = {}
    engineer: dict | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Direct triage pipeline (no Runner; session state not used by current agent)
# ---------------------------------------------------------------------------


def _run_triage_sync(bug: dict) -> dict:
    """
    Run triage pipeline synchronously: supervisor (routes + bug) → analysis → assignment.
    Returns dict with bug, routes, analysis, assignment, engineer (or error).
    """
    agent = SupervisorAgent()
    result, state = agent.run(bug, initial_state())
    if "error" in result:
        return result
    bug_obj = result.get("bug")
    routes = result.get("routes", [])
    if not bug_obj:
        return {"error": "No bug in supervisor result"}
    analysis = {
        "bug_id": bug_obj["bug_id"],
        "impact_score": impact_score(bug_obj.get("severity", "")),
    }
    eng_path = get_data_path(get_engineers_filename())
    if not eng_path.exists():
        return {
            "bug": bug_obj,
            "routes": routes,
            "analysis": analysis,
            "assignment": {},
            "engineer": None,
            "error": "engineer.json not found",
        }
    try:
        engineers = json.loads(eng_path.read_text(encoding="utf-8"))
        chosen = pick_best(engineers, bug_obj)
        assignment = {
            "bug_id": bug_obj["bug_id"],
            "assigned_to": {
                "ldap_id": chosen["ldap_id"],
                "name": chosen["name"],
                "role": chosen["role"],
            },
        }
        return {
            "bug": bug_obj,
            "routes": routes,
            "analysis": analysis,
            "assignment": assignment,
            "engineer": chosen,
        }
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "bug": bug_obj,
            "routes": routes,
            "analysis": analysis,
            "assignment": {},
            "engineer": None,
            "error": str(e),
        }


async def run_triage(bug: dict) -> dict:
    """Run triage in thread pool so sync agent.run() does not block event loop."""
    return await asyncio.to_thread(_run_triage_sync, bug)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Agentic Triage Platform API",
    description="REST API for bug triage: analysis and engineer assignment using ADK agents.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Health check for Vertex / load balancers."""
    return {"status": "ok", "service": "agentic-triage-api"}


@app.post("/predict")
async def predict(request: dict):
    """
    Vertex AI custom prediction: request must have "instances" (array of bug objects).
    Response has "predictions" (array of triage results). Port 8080.
    """
    instances = request.get("instances")
    if not isinstance(instances, list):
        raise HTTPException(status_code=400, detail="Request must include 'instances' array")
    predictions = []
    for inst in instances:
        if not isinstance(inst, dict):
            predictions.append({"error": "Each instance must be a bug object (dict)"})
            continue
        result = await run_triage(inst)
        predictions.append(result or {"error": "No result from triage pipeline"})
    return {"predictions": predictions}


@app.post("/triage", response_model=TriageResponse)
async def triage_one(bug: BugInput):
    """
    Triage a single bug: run analysis and assignment.
    Returns bug, routes, analysis, assignment, and assigned engineer.
    """
    bug_dict = bug.model_dump()
    result = await run_triage(bug_dict)
    if not result:
        raise HTTPException(status_code=500, detail="No result from triage pipeline")
    # Pure error (no bug in result) → 400
    if result.get("error") and not result.get("bug"):
        raise HTTPException(status_code=400, detail=result["error"])
    return TriageResponse(
        bug=result.get("bug", {}),
        routes=result.get("routes", []),
        analysis=result.get("analysis") or {},
        assignment=result.get("assignment") or {},
        engineer=result.get("engineer"),
        error=result.get("error"),
    )


@app.post("/triage/batch")
async def triage_batch(request: BatchTriageRequest):
    """
    Triage multiple bugs. Send a JSON object with key "bugs" (array of bug objects).
    Returns list of triage results in same order.
    """
    results = []
    for b in request.bugs:
        result = await run_triage(b.model_dump())
        if not result:
            results.append({"error": "No result from triage pipeline"})
        elif result.get("error") and not result.get("bug"):
            results.append({"error": result["error"], "bug_id": b.bug_id})
        else:
            results.append({
                "bug": result.get("bug"),
                "routes": result.get("routes", []),
                "analysis": result.get("analysis") or {},
                "assignment": result.get("assignment") or {},
                "engineer": result.get("engineer"),
                "error": result.get("error"),
            })
    return {"results": results, "total": len(results)}


@app.get("/data/bugs")
async def get_data_bugs():
    """Return bugs from data folder (file names from config: BUGS_FILENAMES)."""
    for name in get_bugs_filenames():
        path = get_data_path(name)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "instances" in data:
                    return data["instances"]
                return [data]
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail=f"Invalid JSON in {name}")
    raise HTTPException(status_code=404, detail="No bugs file found in data folder")


@app.get("/data/engineers")
async def get_data_engineers():
    """Return engineers from data folder (file name from config: ENGINEERS_FILENAME)."""
    path = get_data_path(get_engineers_filename())
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{get_engineers_filename()} not found in data folder")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in {get_engineers_filename()}")
