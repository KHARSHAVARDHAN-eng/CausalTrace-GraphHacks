import time
from fastapi import APIRouter
from app.core.config import settings
from app.graph.client import graph_client
from app.ai.provider import get_llm_provider
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """System health check probe.

    Queries real FalkorDB connectivity and reports LLM provider readiness.
    Accurately reflects unconfigured or unreachable states without faking success.
    """
    falkor_health = graph_client.check_connection()
    llm_health = get_llm_provider().check_health()

    # Determine aggregated status
    if falkor_health.connected and (llm_health.status == "ready" or llm_health.status == "stub"):
        system_status = "healthy"
    else:
        system_status = "degraded"

    return HealthResponse(
        status=system_status,
        service="causaltrace-backend",
        version="0.1.0",
        environment=settings.APP_ENV,
        timestamp_ms=int(time.time() * 1000),
        falkordb=falkor_health,
        llm=llm_health,
    )
