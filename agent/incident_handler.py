"""
Incident Handler Service / Webhook Listener.

Receives structured incident events from the checkout backend,
validates them, deduplicates by signature, and hands them off
to the Agent Orchestrator.
"""

import sys
import os
import argparse
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn
import httpx

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models import IncidentPayload
from agent.orchestrator import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [IncidentHandler] %(message)s",
)
logger = logging.getLogger("incident_handler")

app = FastAPI(title="Agent Incident Webhook Handler")
orchestrator = Orchestrator()

# In-memory tracking of active incident signatures to prevent duplicate concurrent runs
ACTIVE_INCIDENTS: Dict[str, str] = {}


def _run_healing_pipeline(incident: IncidentPayload, sig: str):
    """Executes orchestrator healing loop and guarantees signature lock is released."""
    try:
        orchestrator.handle_incident(incident)
    except Exception as e:
        logger.exception(f"Unexpected error in orchestrator: {e}")
    finally:
        logger.info(f"Releasing active lock for signature: {sig}")
        ACTIVE_INCIDENTS.pop(sig, None)


@app.post("/webhook/incident")
async def receive_incident_webhook(incident: IncidentPayload, background_tasks: BackgroundTasks):
    """
    Webhook endpoint called by backend when an unhandled 500 error occurs.
    Spawns the autonomous healing loop in the background.
    """
    sig = f"{incident.error_type}:{incident.error_message}:{incident.endpoint}"
    logger.info(f"Received incident notification: {incident.incident_id} | Signature: {sig}")

    if sig in ACTIVE_INCIDENTS and ACTIVE_INCIDENTS[sig] in ["INVESTIGATING", "FIXING"]:
        logger.warning(f"Incident with signature '{sig}' is already being processed. Skipping duplicate.")
        return {"status": "SKIPPED_DUPLICATE", "incident_id": incident.incident_id}

    ACTIVE_INCIDENTS[sig] = "INVESTIGATING"

    # Run orchestrator healing pipeline in background and ensure lock cleanup
    background_tasks.add_task(_run_healing_pipeline, incident, sig)

    return {
        "status": "ACCEPTED",
        "incident_id": incident.incident_id,
        "message": "Orchestrator dispatched to isolated git worktree",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "agent-incident-handler"}


def process_single_incident_by_id(backend_url: str, incident_id: str):
    """Utility function to trigger incident handling directly via CLI."""
    logger.info(f"Fetching incident {incident_id} from {backend_url}...")
    with httpx.Client() as client:
        resp = client.get(f"{backend_url}/api/incidents/{incident_id}")
        if resp.status_code != 200:
            logger.error(f"Failed to fetch incident: {resp.text}")
            return False
        incident_data = resp.json()

    incident = IncidentPayload(**incident_data)
    result = orchestrator.handle_incident(incident)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Incident Webhook Handler & Agent Launcher")
    parser.add_argument("--listen", action="store_true", help="Start FastAPI webhook listener")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    parser.add_argument("--incident-id", type=str, help="Process a specific incident ID directly")
    parser.add_argument("--backend-url", type=str, default="http://127.0.0.1:8000", help="Backend API base URL")

    args = parser.parse_args()

    if args.incident_id:
        process_single_incident_by_id(args.backend_url, args.incident_id)
    else:
        logger.info(f"Starting Incident Handler Webhook listener on port {args.port}...")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
