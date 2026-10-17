from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ServiceNode(BaseModel):
    """Microservice node representation in the FalkorDB topology."""
    id: str = Field(..., description="Unique service ID, e.g. 'svc-checkout'")
    name: str = Field(..., description="Display name, e.g. 'Checkout API'")
    tier: Literal["tier-1", "tier-2", "tier-3"] = Field(..., description="Criticality tier")
    team: str = Field(..., description="Owning engineering team")
    language: str = Field(..., description="Runtime or implementation language")
    status: Literal["HEALTHY", "DEGRADED", "CRITICAL"] = Field(
        default="HEALTHY", description="Observed operational status"
    )


class DeploymentNode(BaseModel):
    """Deployment change event in the graph."""
    id: str = Field(..., description="Unique deployment ID, e.g. 'dep-1029'")
    version: str = Field(..., description="Application semantic version or tag")
    commit_sha: str = Field(..., description="Git commit hash")
    timestamp: int = Field(..., description="Deployment completion epoch ms")
    status: Literal["SUCCESS", "FAILED", "ROLLED_BACK"] = Field(..., description="Deployment outcome")
    deployed_by: str = Field(..., description="Actor or CI trigger responsible")


class AlertNode(BaseModel):
    """Telemetry alert instance linked to a service."""
    id: str = Field(..., description="Alert identifier, e.g. 'alt-5501'")
    name: str = Field(..., description="Alert rule title, e.g. 'P99LatencyBreach'")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(..., description="Alert severity")
    timestamp: int = Field(..., description="Trigger epoch ms")
    status: Literal["FIRING", "RESOLVED"] = Field(default="FIRING", description="Firing state")
    metric_name: str = Field(..., description="Breached telemetry metric")
    metric_value: float = Field(..., description="Observed metric value")


class IncidentNode(BaseModel):
    """Incident entity orchestrating the investigation."""
    id: str = Field(..., description="Incident ID, e.g. 'inc-2026-0042'")
    title: str = Field(..., description="Brief title describing the symptom")
    severity: Literal["SEV-1", "SEV-2", "SEV-3"] = Field(..., description="Incident severity level")
    status: Literal["INVESTIGATING", "IDENTIFIED", "MITIGATED", "RESOLVED"] = Field(
        default="INVESTIGATING", description="Incident resolution phase"
    )
    started_at: int = Field(..., description="Start epoch ms")
    resolved_at: Optional[int] = Field(None, description="Resolution epoch ms")
    summary: Optional[str] = Field(None, description="High level investigation summary")


class RelationshipEdge(BaseModel):
    """Graph relationship representation."""
    source_id: str
    target_id: str
    type: Literal[
        "DEPENDS_ON",
        "DEPLOYED_TO",
        "TRIGGERED_ON",
        "CORRELATED_WITH",
        "EMITTED_BY",
        "AFFECTS",
        "ROOT_CAUSE",
    ]
    properties: dict = Field(default_factory=dict)


class EvidenceChain(BaseModel):
    """Root cause evidence path discovered through FalkorDB Cypher traversal."""
    incident_id: str
    candidate_id: str
    candidate_type: Literal["Deployment", "Service", "Alert"]
    score: float = Field(..., ge=0.0, le=1.0, description="Ranking score from 0.0 to 1.0")
    reasoning: str = Field(..., description="Synthesized causal explanation")
    path_nodes: List[str] = Field(default_factory=list, description="Ordered list of node IDs along path")
