// ==============================================================================
// CausalTrace - Proposed FalkorDB Graph Schema
// Hackathon: Graph Hacks
// Engine: FalkorDB (Cypher)
// ==============================================================================

// ------------------------------------------------------------------------------
// 1. INDEXES & CONSTRAINTS (FalkorDB Syntax)
// ------------------------------------------------------------------------------
CREATE INDEX FOR (s:Service) ON (s.id);
CREATE INDEX FOR (s:Service) ON (s.name);
CREATE INDEX FOR (d:Deployment) ON (d.id);
CREATE INDEX FOR (d:Deployment) ON (d.timestamp);
CREATE INDEX FOR (a:Alert) ON (a.id);
CREATE INDEX FOR (a:Alert) ON (a.timestamp);
CREATE INDEX FOR (i:Incident) ON (i.id);
CREATE INDEX FOR (l:LogEvent) ON (l.id);

// ------------------------------------------------------------------------------
// 2. NODE LABELS & PROPERTIES SPECIFICATION
// ------------------------------------------------------------------------------
// (:Service {
//     id: STRING,            // Unique service identifier (e.g., "svc-payments-api")
//     name: STRING,          // Human-readable service name (e.g., "Payments API")
//     tier: STRING,          // "tier-1", "tier-2", "tier-3"
//     team: STRING,          // Owning team (e.g., "checkout-platform")
//     language: STRING,      // Runtime (e.g., "go", "python", "typescript")
//     status: STRING         // "HEALTHY", "DEGRADED", "CRITICAL"
// })
//
// (:Deployment {
//     id: STRING,            // Unique deployment ID (e.g., "dep-84920")
//     version: STRING,       // Semantic version / tag (e.g., "v2.14.1")
//     commit_sha: STRING,    // Git commit hash
//     timestamp: INTEGER,    // Epoch milliseconds of deployment completion
//     status: STRING,        // "SUCCESS", "FAILED", "ROLLED_BACK"
//     deployed_by: STRING    // User or CI/CD actor
// })
//
// (:Alert {
//     id: STRING,            // Alert instance identifier (e.g., "alt-9012")
//     name: STRING,          // Alert rule name (e.g., "High5xxErrorRate")
//     severity: STRING,      // "CRITICAL", "HIGH", "MEDIUM", "LOW"
//     timestamp: INTEGER,    // Epoch milliseconds when alert fired
//     status: STRING,        // "FIRING", "RESOLVED"
//     metric_name: STRING,   // Metric monitored (e.g., "http_requests_5xx_rate")
//     metric_value: FLOAT    // Value that breached threshold
// })
//
// (:Incident {
//     id: STRING,            // Incident identifier (e.g., "inc-2026-0042")
//     title: STRING,         // Incident summary (e.g., "Checkout latency spike")
//     severity: STRING,      // "SEV-1", "SEV-2", "SEV-3"
//     status: STRING,        // "INVESTIGATING", "IDENTIFIED", "MITIGATED", "RESOLVED"
//     started_at: INTEGER,   // Epoch milliseconds
//     resolved_at: INTEGER,  // Epoch milliseconds or null
//     summary: STRING        // Investigation summary or notes
// })
//
// (:LogEvent {
//     id: STRING,            // Unique log entry ID
//     level: STRING,         // "ERROR", "FATAL", "WARN"
//     message: STRING,       // Log message content
//     timestamp: INTEGER,    // Epoch milliseconds
//     trace_id: STRING       // Distributed trace ID
// })

// ------------------------------------------------------------------------------
// 3. RELATIONSHIPS SPECIFICATION
// ------------------------------------------------------------------------------
// (:Service)-[:DEPENDS_ON {
//     protocol: STRING,          // "gRPC", "HTTP/REST", "Kafka", etc.
//     latency_p99_ms: FLOAT,     // Baseline p99 latency
//     critical: BOOLEAN          // Whether failure cascades hard
// }]->(:Service)
//
// (:Deployment)-[:DEPLOYED_TO {
//     environment: STRING        // "production", "staging"
// }]->(:Service)
//
// (:Alert)-[:TRIGGERED_ON]->(:Service)
//
// (:Alert)-[:CORRELATED_WITH {
//     confidence: FLOAT,         // Statistical or heuristic correlation score
//     time_delta_sec: INTEGER    // Difference between alert fire and incident start
// }]->(:Incident)
//
// (:LogEvent)-[:EMITTED_BY]->(:Service)
//
// (:Incident)-[:AFFECTS]->(:Service)
//
// (:Incident)-[:ROOT_CAUSE {
//     score: FLOAT,              // Ranked confidence score (0.0 to 1.0)
//     reasoning: STRING,         // LLM + Cypher synthesized justification
//     evidence_chain: STRING     // Path identifiers (JSON or serialized path)
// }]->(:Deployment|:Service|:Alert)

// ------------------------------------------------------------------------------
// 4. REPRESENTATIVE CYPHER INVESTIGATION PATTERNS
// ------------------------------------------------------------------------------

// Pattern A: Trace all upstream dependencies within 2 hops of an affected service
// MATCH path = (start:Service {id: $service_id})<-[:DEPENDS_ON*1..2]-(upstream:Service)
// RETURN path;

// Pattern B: Find recent deployments across the dependency tree within 30 minutes of incident start
// MATCH (inc:Incident {id: $incident_id})-[:AFFECTS]->(target:Service)
// MATCH (target)-[:DEPENDS_ON*0..3]->(dep_svc:Service)
// MATCH (dep:Deployment)-[:DEPLOYED_TO]->(dep_svc)
// WHERE dep.timestamp <= inc.started_at
//   AND dep.timestamp >= (inc.started_at - 1800000)
// RETURN dep_svc.name AS service, dep.version AS version, dep.timestamp AS deployed_at
// ORDER BY dep.timestamp DESC;

// Pattern C: Correlate active alerts with services in the blast radius
// MATCH (inc:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)
// MATCH (blast_radius:Service)-[:DEPENDS_ON*0..2]->(s)
// MATCH (alt:Alert {status: 'FIRING'})-[:TRIGGERED_ON]->(blast_radius)
// RETURN blast_radius.name, alt.name, alt.severity, alt.timestamp;
