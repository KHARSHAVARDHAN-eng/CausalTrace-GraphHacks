"""API routes for incidents and graph-derived investigations."""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path, status
from app.graph.query import graph_query_service
from app.services.investigation import investigation_service
from app.schemas.investigation import IncidentInvestigationResponse
from app.graph.seeder import seed_incident_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["Incidents & Investigations"])


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/scenarios", response_model=List[Dict[str, Any]])
def list_incidents():
    """List all incidents available in the FalkorDB property graph."""
    try:
        incidents, _ = graph_query_service.list_incidents()
        return incidents
    except Exception as exc:
        logger.error("Failed to list incidents from FalkorDB: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"FalkorDB query failed: {type(exc).__name__} ({str(exc)})",
        )


@router.get("/{incident_id}/investigation", response_model=IncidentInvestigationResponse)
def get_incident_investigation(
    incident_id: str = Path(
        ...,
        pattern=r"^[a-zA-Z0-9_\-\.]{3,64}$",
        description="Alphanumeric identifier of the target incident (3-64 chars)",
        examples=["inc-01-payment-pool-exhaustion"],
    ),
    window_ms: int = Query(
        3600000,
        ge=60000,
        le=604800000,
        description="Temporal investigation window in milliseconds (1 min to 7 days, default: 1 hour)",
    ),
):
    """Execute a graph-driven causal investigation for an incident in FalkorDB.

    Traverses service dependencies, temporal changes, and active telemetry
    to synthesize ranked root-cause hypotheses and evidence paths.
    """
    try:
        return investigation_service.investigate(incident_id=incident_id, window_ms=window_ms)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'\""),
        )
    except Exception as exc:
        logger.error("Investigation failed for incident '%s': %s", incident_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Graph investigation failed: {type(exc).__name__} ({str(exc)})",
        )


@router.post("/seed", status_code=status.HTTP_201_CREATED)
def seed_graph_endpoint():
    """Idempotently seed or reset the FalkorDB graph with the synthetic test incident."""
    try:
        result = seed_incident_graph()
        return {"message": "Incident graph seeded successfully", "details": result}
    except Exception as exc:
        logger.error("Failed to seed FalkorDB graph: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"FalkorDB seeding failed: {type(exc).__name__} ({str(exc)})",
        )
