export interface FalkorDBHealth {
  configured: boolean;
  connected: boolean;
  host: string;
  port: number;
  graph: string;
  message: string;
  latency_ms?: number;
}

export interface LLMHealth {
  provider: string;
  model: string;
  has_api_key: boolean;
  status: 'ready' | 'unconfigured' | 'stub';
  message: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'initializing';
  service: string;
  version: string;
  environment: string;
  timestamp_ms: number;
  falkordb: FalkorDBHealth;
  llm: LLMHealth;
}

export interface NodeSchemaDefinition {
  label: string;
  iconName: string;
  color: string;
  description: string;
  properties: { name: string; type: string; example: string }[];
}

export interface EdgeSchemaDefinition {
  type: string;
  source: string;
  target: string;
  description: string;
  properties?: { name: string; type: string }[];
}

export interface IncidentSummary {
  id: string;
  title: string;
  severity: string;
  status: string;
  started_at: number;
  summary: string;
}

export interface DependencyHop {
  source_service_id: string;
  target_service_id: string;
  protocol: string;
  latency_p99_ms: number;
  critical: boolean;
}

export interface EvidencePath {
  path_id: string;
  service_chain: string[];
  service_names: string[];
  is_critical_path: boolean;
  hop_count: number;
  hops: DependencyHop[];
}

export interface CorroboratingAlert {
  id: string;
  name: string;
  severity: string;
  timestamp: number;
  metric_name: string;
  metric_value: number;
  service_id: string;
}

export interface CorroboratingLog {
  id: string;
  level: string;
  message: string;
  timestamp: number;
  trace_id?: string;
  service_id: string;
}

export interface RootCauseHypothesis {
  hypothesis_id: string;
  rank: number;
  entity_id: string;
  entity_type: string;
  service_id: string;
  service_name: string;
  score: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  proven_causality: boolean;
  time_delta_sec: number;
  reasoning: string;
  evidence_path?: EvidencePath;
  corroborating_alerts: CorroboratingAlert[];
  corroborating_logs: CorroboratingLog[];
  is_distractor_or_competing: boolean;
  distractor_reasoning?: string;
  supporting_evidence: string[];
  contradictory_evidence: string[];
  missing_evidence: string[];
  score_breakdown?: {
    topological_criticality?: number;
    temporal_proximity?: number;
    telemetry_corroboration?: number;
  };
  relative_confidence_pct: number;
}

export interface UncertaintyCaveats {
  statement: string;
  insufficient_evidence_flags: string[];
  recommended_verification_steps: string[];
}

export interface IncidentInvestigationResponse {
  incident_id: string;
  title: string;
  severity: string;
  started_at: number;
  affected_services: string[];
  blast_radius_services: string[];
  hypotheses: RootCauseHypothesis[];
  top_hypothesis_justification?: string;
  evidence_paths: EvidencePath[];
  active_alerts: CorroboratingAlert[];
  uncertainty: UncertaintyCaveats;
  has_sufficient_evidence: boolean;
  cypher_query_provenance: string[];
}
