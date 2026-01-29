# AI assisted development
"""
Run the FastAPI REST API for Agentic Triage Platform.

Usage:
  python run_api.py

  Or with uvicorn directly:
  uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
