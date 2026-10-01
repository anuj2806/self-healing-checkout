import os
import uuid
import json
import logging
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import httpx

from app.models import IncidentPayload

logger = logging.getLogger("incident_monitor")
logger.setLevel(logging.INFO)

# In-memory incident store
INCIDENTS: Dict[str, IncidentPayload] = {}

# Incident log file path
INCIDENT_LOG_DIR = os.getenv("INCIDENT_LOG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "agent_runs"))
os.makedirs(INCIDENT_LOG_DIR, exist_ok=True)
INCIDENT_LOG_FILE = os.path.join(INCIDENT_LOG_DIR, "incidents.jsonl")

# Webhook URL for agent orchestrator
AGENT_WEBHOOK_URL = os.getenv("AGENT_WEBHOOK_URL", "http://127.0.0.1:8001/webhook/incident")


def emit_incident(
    error: Exception,
    request_payload: Dict[str, Any],
    endpoint: str = "/api/checkout",
    deployment_version: str = "v1.0.0",
) -> IncidentPayload:
    """
    Creates a structured incident from an unexpected failure, persists it,
    and emits a notification to the Agent Orchestrator.
    """
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    tb_str = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    incident = IncidentPayload(
        incident_id=incident_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        service="checkout-backend",
        deployment_version=deployment_version,
        environment=os.getenv("APP_ENV", "production"),
        error_type=type(error).__name__,
        error_message=str(error),
        stack_trace=tb_str,
        endpoint=endpoint,
        request_payload=request_payload,
        status="TRIGGERED",
    )

    INCIDENTS[incident_id] = incident

    # Persist to JSONL file
    try:
        with open(INCIDENT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(incident.model_dump_json() + "\n")
    except Exception as e:
        logger.error(f"Failed to append incident to file: {e}")

    logger.error(
        f"[INCIDENT EMITTED] {incident.incident_id} | Type: {incident.error_type} | Message: {incident.error_message}"
    )

    # Attempt to dispatch to orchestrator webhook (non-blocking)
    try:
        with httpx.Client(timeout=2.0) as client:
            client.post(AGENT_WEBHOOK_URL, json=incident.model_dump())
            logger.info(f"Dispatched incident {incident_id} to orchestrator at {AGENT_WEBHOOK_URL}")
    except Exception as dispatch_err:
        logger.warning(
            f"Could not reach orchestrator webhook at {AGENT_WEBHOOK_URL} ({dispatch_err}). "
            "Incident remains logged in store and JSONL."
        )

    return incident


def get_incident(incident_id: str) -> Optional[IncidentPayload]:
    return INCIDENTS.get(incident_id)


def list_incidents() -> List[IncidentPayload]:
    return list(INCIDENTS.values())


def update_incident_status(incident_id: str, status: str) -> Optional[IncidentPayload]:
    if incident_id in INCIDENTS:
        incident = INCIDENTS[incident_id]
        incident.status = status
        return incident
    return None
