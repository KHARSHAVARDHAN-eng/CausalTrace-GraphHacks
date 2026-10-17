from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router

__all__ = ["health_router", "incidents_router"]
