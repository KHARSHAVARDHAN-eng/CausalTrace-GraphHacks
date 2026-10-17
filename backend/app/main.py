from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router

app = FastAPI(
    title="CausalTrace API",
    description="AI-powered incident investigation platform connecting service dependencies, deployments, and telemetry in FalkorDB.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local development and frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")


@app.get("/", tags=["Root"])
def root_info():
    """Root info endpoint pointing to documentation and health check."""
    return {
        "service": "CausalTrace API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
        "description": "Graph Hacks Incident Investigation Engine",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=(settings.APP_ENV == "development"),
    )
