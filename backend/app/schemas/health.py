from typing import Optional
from pydantic import BaseModel, Field


class FalkorDBHealth(BaseModel):
    """Health status representation for FalkorDB graph database."""
    configured: bool = Field(..., description="Whether FalkorDB host and parameters are specified")
    connected: bool = Field(..., description="Whether a live connection to FalkorDB succeeded")
    host: str = Field(..., description="FalkorDB host endpoint")
    port: int = Field(..., description="FalkorDB connection port")
    graph: str = Field(..., description="Target FalkorDB graph identifier")
    message: str = Field(..., description="Diagnostic connection message or error details")
    latency_ms: Optional[float] = Field(None, description="Round-trip latency in milliseconds for ping query")


class LLMHealth(BaseModel):
    """Health and readiness status for the modular LLM provider."""
    provider: str = Field(..., description="Configured LLM provider name (e.g., openai, anthropic, stub)")
    model: str = Field(..., description="Configured model identifier")
    has_api_key: bool = Field(..., description="Whether an API key is detected in the environment")
    status: str = Field(..., description="Operational status: ready, unconfigured, or stub")
    message: str = Field(..., description="Explanation of LLM readiness")


class HealthResponse(BaseModel):
    """Overall system health and connectivity payload."""
    status: str = Field(..., description="System status: healthy, degraded, or initializing")
    service: str = Field(default="causaltrace-backend", description="Backend service identifier")
    version: str = Field(default="0.1.0", description="API version")
    environment: str = Field(..., description="Running environment")
    timestamp_ms: int = Field(..., description="Current timestamp in epoch milliseconds")
    falkordb: FalkorDBHealth = Field(..., description="FalkorDB connectivity details")
    llm: LLMHealth = Field(..., description="AI/LLM provider readiness details")
