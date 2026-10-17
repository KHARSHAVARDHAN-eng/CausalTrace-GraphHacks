from typing import List, Optional
from pydantic import BaseModel, Field


class DependencyHop(BaseModel):
    """Single topological hop in the service dependency graph."""
    source_service_id: str
    target_service_id: str
    protocol: str = "HTTP"
    latency_p99_ms: float = 0.0
    critical: bool = True


class EvidencePath(BaseModel):
    """Traversed dependency chain linking an affected service to an upstream change."""
    path_id: str
    service_chain: List[str] = Field(..., description="Ordered list of service IDs from symptom to root")
    service_names: List[str] = Field(..., description="Ordered list of human-readable service names")
    is_critical_path: bool = Field(..., description="True if every hop along the chain is critical")
    hop_count: int = Field(..., description="Number of network hops between services")
    hops: List[DependencyHop] = Field(default_factory=list)


class CorroboratingAlert(BaseModel):
    """Telemetry alert correlated with an evidence path or candidate service."""
    id: str
    name: str
    severity: str
    timestamp: int
    metric_name: str
    metric_value: float
    service_id: str


class CorroboratingLog(BaseModel):
    """Error or warning log emitted by a service along the causal path."""
    id: str
    level: str
    message: str
    timestamp: int
    trace_id: Optional[str] = None
    service_id: str


class RootCauseHypothesis(BaseModel):
    """Graph-derived candidate root cause with multi-factor scoring and provenance."""
    hypothesis_id: str
    rank: int = Field(..., description="Hypothesis rank (1 = most probable)")
    entity_id: str = Field(..., description="Node ID of the candidate culprit (e.g., deployment ID)")
    entity_type: str = Field(default="Deployment", description="Entity type: Deployment, Service, or Alert")
    service_id: str
    service_name: str
    score: float = Field(..., ge=0.0, le=1.0, description="Composite ranking score (0.0 to 1.0)")
    confidence_level: str = Field(..., description="Confidence: HIGH, MEDIUM, or LOW")
    proven_causality: bool = Field(
        default=False,
        description="Explicit honesty flag: always False when based on graph correlation without controlled experiment",
    )
    time_delta_sec: int = Field(..., description="Seconds between event timestamp and incident start (negative = before)")
    reasoning: str = Field(..., description="Synthesized causal rationale based on graph evidence")
    evidence_path: Optional[EvidencePath] = None
    corroborating_alerts: List[CorroboratingAlert] = Field(default_factory=list)
    corroborating_logs: List[CorroboratingLog] = Field(default_factory=list)
    is_distractor_or_competing: bool = Field(default=False)
    distractor_reasoning: Optional[str] = None
    supporting_evidence: List[str] = Field(default_factory=list, description="Verified facts supporting this hypothesis")
    contradictory_evidence: List[str] = Field(default_factory=list, description="Observed facts weakening this hypothesis")
    missing_evidence: List[str] = Field(default_factory=list, description="Observability gaps or unmonitored telemetry for this candidate")
    score_breakdown: dict = Field(default_factory=dict, description="Component scores: topological, temporal, telemetry")
    relative_confidence_pct: float = Field(
        default=0.0,
        description="Normalized relative confidence percentage across candidates (softmax normalized heuristic score, not empirical Bayesian calibration)",
    )


class UncertaintyCaveats(BaseModel):
    """Structured uncertainty notes acknowledging correlation vs causation limitations."""
    statement: str = Field(
        default="Graph paths and temporal alignment establish strong plausibility, but do not constitute definitive mathematical proof of causality.",
        description="Standard uncertainty disclaimer",
    )
    insufficient_evidence_flags: List[str] = Field(
        default_factory=list,
        description="Specific gaps in evidence (e.g. missing flamegraphs, unmonitored async workers)",
    )
    recommended_verification_steps: List[str] = Field(
        default_factory=list,
        description="Concrete steps an on-call engineer should take to verify before rollback",
    )


class IncidentInvestigationResponse(BaseModel):
    """Full investigation output payload returned by the API."""
    incident_id: str
    title: str
    severity: str
    started_at: int
    affected_services: List[str]
    blast_radius_services: List[str]
    hypotheses: List[RootCauseHypothesis]
    top_hypothesis_justification: Optional[str] = Field(
        default=None,
        description="Decisive comparative explanation of why the top hypothesis outranks competing candidates",
    )
    evidence_paths: List[EvidencePath]
    active_alerts: List[CorroboratingAlert]
    uncertainty: UncertaintyCaveats
    has_sufficient_evidence: bool = Field(default=True, description="False if evidence is too sparse for high confidence")
    cypher_query_provenance: List[str] = Field(
        default_factory=list,
        description="Actual Cypher queries executed to derive this investigation report",
    )
