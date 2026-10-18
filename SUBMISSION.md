# CausalTrace — Official Hackathon Submission Package

**Hackathon:** Graph Hacks: Context for AI Agents (WeMakeDevs × FalkorDB)  
**Track:** Agents That Act on Connected Data  
**Submission Portal:** [https://www.wemakedevs.org/hackathons/falkordb](https://www.wemakedevs.org/hackathons/falkordb)  
**Submission Deadline:** October 18, 2026, 11:59 PM IST  
**Public Repository:** [https://github.com/KHARSHAVARDHAN-eng/CausalTrace-GraphHacks](https://github.com/KHARSHAVARDHAN-eng/CausalTrace-GraphHacks)  
**Demo Video URL:** *[Insert Your YouTube / Loom Link Here]*  

---

## 1. Portal Form Fields (Ready to Copy-Paste)

### Project Name
```text
CausalTrace
```

### Tagline / One-Liner (100 characters max)
```text
Evidence-first incident investigation platform connecting service dependencies and telemetry in FalkorDB.
```

### Selected Track
```text
Agents That Act on Connected Data
```

### GitHub Repository URL
```text
https://github.com/KHARSHAVARDHAN-eng/CausalTrace-GraphHacks
```

### Demo Video URL
```text
[INSERT VERIFIED DEMO VIDEO URL — e.g. https://youtu.be/YOUR_VIDEO_ID or https://www.loom.com/share/YOUR_VIDEO_ID]
```

### Short Description (200 words max)
```text
When high-severity incidents strike microservice systems, Site Reliability Engineers are overwhelmed by fragmented telemetry—symptom alerts on edge gateways while true root causes sit 2 to 4 hops upstream. Relational schemas and isolated log aggregators struggle to traverse multi-hop causal graphs during mission-critical triage.

CausalTrace models the production ecosystem—services, synchronous/asynchronous dependencies, code deployments, alerts, and distributed trace logs—as a connected property graph in FalkorDB. When an incident triggers, CausalTrace executes parameterized native Cypher queries to compute blast radiuses, correlate temporal events, demote misleading distractor alerts, and synthesize ranked root-cause hypotheses with warm traversal latencies averaging ~4.1 milliseconds.

Unlike black-box generative bots, CausalTrace uses deterministic graph scoring to prevent hallucinatory culprits, detects telemetry gaps to safely enter Abstention Mode rather than guessing, and generates evidence-guided next diagnostic checks marked as RECOMMENDED (NOT EXECUTED) to help on-call engineers safely verify root causes.
```

---

## 2. Full Project Description / Markdown Overview

### The Problem
During production outages, mean time to resolution (MTTR) is dominated by mean time to understand (MTTU). Incident responders juggle disparate dashboards:
1. **Static dependency architecture diagrams** that lag behind reality.
2. **Recent deployment registries** distributed across CI/CD pipelines.
3. **Active metric alerts** that fire downstream on symptom services without indicating upstream triggers.
4. **Scattered log streams and distributed traces** lacking causal deployment context.

In distributed topologies, a database pool exhaustion 3 hops away often causes the edge checkout web service to fail. Querying variable-depth dependency graphs in relational databases requires recursive CTEs or repeated self-joins, while LLMs without strict graph grounding routinely fabricate plausible-sounding root causes.

---

### The Solution: CausalTrace
**CausalTrace** unifies topologies, deployments, alerts, and traces in **FalkorDB**. It provides on-call engineers with:
- **Instant Graph Traversal:** 1-to-4 hop blast radius mapping using native Cypher in 3.5–5 ms.
- **Deterministic Evidence-First Ranking:** Multi-factor heuristic scoring weighing call path criticality, temporal deployment proximity, alert corroboration, and distributed trace matching.
- **Competing Hypothesis Discrimination:** Evaluates simultaneous changes (e.g., dual releases) and explains why one candidate ranks higher.
- **Safe Epistemic Abstention:** Explicitly abstains when telemetry is missing or candidate scores are below threshold (< 0.60), providing 0 candidate hypotheses and flagging specific observability gaps.
- **Evidence-Guided Diagnostic Recommendations:** Synthesizes read-only verification actions labeled `RECOMMENDED (NOT EXECUTED)` to guide on-call engineers before taking invasive mitigation actions.

---

### Technical Architecture & How FalkorDB is Used

```
[ Frontend: React 18 / Vite / TypeScript / Tailwind CSS ]
                       │  HTTP API
                       ▼
[ Backend: FastAPI (Python 3.10) / Pydantic v2 ]
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[ FalkorDB Native Cypher ]    [ Modular AI Provider ]
  • Graph Topologies            • Health readiness probes
  • Multi-Hop Traversal         • Extensible provider interface
  • Temporal Correlation        • (Not in critical scoring path)
  • Blast Radius Queries
```

#### FalkorDB Graph Schema:
- **Nodes:**
  - `:Incident` (id, title, severity, status, started_at, summary)
  - `:Service` (id, name, tier, team, language, status)
  - `:Deployment` (id, version, commit_sha, timestamp, status, deployed_by)
  - `:Alert` (id, name, severity, timestamp, status, metric_name, metric_value)
  - `:LogEvent` (id, level, message, timestamp, trace_id)
- **Relationships:**
  - `[:DEPENDS_ON]` (`protocol`, `latency_p99_ms`, `critical`)
  - `[:DEPLOYED_TO]` (`environment`)
  - `[:TRIGGERED_ON]` (telemetry alert linkage)
  - `[:EMITTED_BY]` (log and span linkage)
  - `[:AFFECTS]` (incident symptom linkage)
  - `[:ROOT_CAUSE]` (synthesized causal hypothesis link)

#### Representative Native Cypher Traversal:
```cypher
MATCH path = (s:Service {id: $service_id})-[:DEPENDS_ON*1..4]->(target:Service)
RETURN [node IN nodes(path) | node.id] AS chain,
       [rel IN relationships(path) | rel.critical] AS criticals,
       [rel IN relationships(path) | rel.protocol] AS protos,
       [rel IN relationships(path) | rel.latency_p99_ms] AS latencies;
```

---

### Reproducible Synthetic Evaluation Benchmark

To demonstrate reproducibility, CausalTrace includes an automated benchmark evaluating **10 curated synthetic failure topologies** seeded in FalkorDB (`python backend/scripts/evaluate_investigation.py`):

| Metric | Result | Scope |
| :--- | :---: | :--- |
| **Top-1 Root-Cause Accuracy** | **100.0%** | 9/9 culprit scenarios |
| **Top-3 Root-Cause Recall** | **100.0%** | 9/9 culprit scenarios |
| **Misleading-Alert Demotion Rate** | **100.0%** | 8/8 distractor scenarios |
| **Insufficient Evidence Abstention** | **100.0%** | 1/1 telemetry gap scenarios |
| **Warm Graph Traversal Latency** | **4.1 ms mean** | Scenarios 2–10 (3.5–4.8 ms range) |
| **Overall Traversal Latency** | **9.7 ms mean** | All 10 scenarios (including cold start) |

*Evaluation Disclosure: This benchmark evaluates deterministic graph ranking across 10 curated synthetic topologies. It does not represent real-world production outages or formal Pearlian do-calculus causality proofs.*

---

### Technology Stack
- **Graph Database:** FalkorDB (native Redis protocol, Cypher query engine)
- **Backend:** FastAPI, Python 3.10, FalkorDB Python Client, Pydantic v2, pytest
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons
- **Infrastructure:** Docker container (`falkordb/falkordb:latest`)

---

### AI-Assistance Disclosure
- **Development Tooling:** AI coding assistants were utilized for TypeScript interface authoring, boilerplate scaffolding, and test harness authoring.
- **Runtime AI Architecture:** All graph traversals, blast radius isolation, evidence corroboration, candidate scoring, and abstention are executed deterministically via FalkorDB Cypher and graph heuristics. The repository includes an extensible modular LLM provider interface (`backend/app/ai/provider.py`) which powers environment health probes. Generative LLMs are deliberately excluded from the candidate generation and scoring path to avoid generative entity fabrication during production incidents.
