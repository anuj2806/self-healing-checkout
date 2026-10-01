import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models import (
    CheckoutRequest,
    CheckoutResponse,
    IncidentPayload,
    HealthResponse,
)
from app.checkout import process_checkout
from app.incident import list_incidents, get_incident, update_incident_status

APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")

app = FastAPI(
    title="Self-Healing Checkout API",
    description="E-commerce checkout backend with structured incident emission and autonomous healing support",
    version=APP_VERSION,
)

# Enable CORS for frontend Vite dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint verified by CI/CD post-deployment smoke tests."""
    return HealthResponse(
        status="healthy",
        version=os.getenv("APP_VERSION", APP_VERSION),
    )


@app.post("/api/checkout", response_model=CheckoutResponse)
def checkout_endpoint(request: CheckoutRequest):
    """
    Process checkout.
    If tax calculation or business logic encounters an unexpected failure,
    a structured incident is emitted and HTTP 500 returned with the incident_id.
    """
    return process_checkout(request)


@app.get("/api/incidents", response_model=List[IncidentPayload])
def get_all_incidents():
    """Retrieve all emitted incidents."""
    return list_incidents()


@app.get("/api/incidents/{incident_id}", response_model=IncidentPayload)
def get_incident_by_id(incident_id: str):
    """Retrieve details of a specific incident."""
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


class IncidentStatusUpdate(BaseModel):
    status: str


@app.patch("/api/incidents/{incident_id}", response_model=IncidentPayload)
def update_incident(incident_id: str, update: IncidentStatusUpdate):
    """Update status of an incident (e.g., INVESTIGATING, FIXING, RESOLVED)."""
    incident = update_incident_status(incident_id, update.status)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
