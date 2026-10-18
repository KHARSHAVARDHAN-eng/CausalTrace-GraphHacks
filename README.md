# CausalTrace

Incident investigation platform connecting microservice dependencies, deployments, alerts, and logs in FalkorDB.

Built for the **Graph Hacks** hackathon (**Track:** Agents That Act on Connected Data).

- **Demo Video:** [https://youtu.be/cTQS2JAvlS4](https://youtu.be/cTQS2JAvlS4)
- **Repository:** [https://github.com/KHARSHAVARDHAN-eng/CausalTrace-GraphHacks](https://github.com/KHARSHAVARDHAN-eng/CausalTrace-GraphHacks)
- **Submission Package:** [SUBMISSION.md](SUBMISSION.md)
- **Demo Walkthrough Script:** [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
- **Graph Schema DDL:** [docs/schema.cypher](docs/schema.cypher)

---

## Overview

During high-severity incidents in microservice architectures, symptoms typically appear on edge services (for example, HTTP 500 spikes or latency increases on an API gateway) while the root cause sits two to four hops upstream (such as a database connection pool exhaustion or a bad configuration release).

Investigating these cascades manually is slow:
- Relational tables struggle to query variable-depth call graphs without recursive queries or repeated joins.
- Distributed tracing tracks individual requests but usually lacks deployment change context.
- Metric dashboards show what is failing, but not which upstream change initiated the failure.

CausalTrace stores service dependencies, code deployments, alerts, and trace logs as a property graph in FalkorDB. When an incident is investigated, CausalTrace uses native Cypher queries to compute the blast radius, correlate events across time, demote irrelevant distractor alerts, and rank candidate root causes using deterministic graph evidence.

---

## Demo

A 2.5-minute video demonstrating CausalTrace is available at:
**[https://youtu.be/cTQS2JAvlS4](https://youtu.be/cTQS2JAvlS4)**

The walkthrough demonstrates:
1. **Normal Investigation (`inc-01-payment-pool-exhaustion`):** Traversing a two-hop dependency chain (`checkout-web` to `order-service` to `payment-service`), identifying deployment `dep-payment-v2.4.1` as the primary cause, corroborating it with active pool exhaustion alerts and trace logs, and generating an evidence-guided diagnostic check.
2. **Competing Hypotheses (`inc-08-dual-competing-deployments`):** Evaluating two deployments shipped simultaneously by different teams, ranking the critical-path fraud evaluator deployment higher than an asynchronous tax deployment, and explaining why.
3. **Safe Abstention (`inc-07-insufficient-evidence-abstain`):** Handling an incident with dropped telemetry and no recent releases by producing zero candidate hypotheses, flagging the observability gaps, and recommending targeted read-only audit steps instead of guessing.

The exact narration and click-through instructions are documented in [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

---

## Key Capabilities

### Deterministic Evidence Scoring
Rather than relying on a generative model to guess potential causes, CausalTrace calculates candidate scores using structured graph evidence:
- **Topology Distance and Criticality:** Direct synchronous upstream dependencies carry higher weight than asynchronous or distant nodes.
- **Temporal Alignment:** Deployments completed immediately prior to incident onset receive higher priority than older or unrelated changes.
- **Alert Corroboration:** Active firing alerts on candidate services increase the candidate confidence.
- **Distributed Trace Matching:** Error logs whose trace IDs match downstream errors directly corroborate the causal link.

### Distractor Demotion and Competing Hypotheses
In complex microservice systems, unrelated alerts and routine deployments frequently coincide with real outages. CausalTrace evaluates all candidate entities within the blast radius. Candidates that sit off the critical call path or lack corroborating telemetry are demoted, while competing candidates are presented alongside an explanation of the discriminating factors.

### Safe Abstention Under Observability Gaps
When telemetry is incomplete or candidate scores fall below a confidence threshold (0.60), the engine abstains. It returns zero candidate hypotheses, explicitly flags the missing data (for example, missing error logs or absent deployment records), and informs the engineer that correlation is insufficient to claim a root cause.

### Evidence-Guided Diagnostic Recommendations
For every investigated incident, CausalTrace synthesizes an actionable, read-only diagnostic recommendation labeled `RECOMMENDED (NOT EXECUTED)`. Recommendations are grounded in the observed graph evidence and explicitly state their discriminating value—for example, comparing p99 latency between canary and baseline releases, or auditing local log files when central telemetry is unavailable.

---

## Architecture

```
+-------------------------------------------------------------+
|                     CausalTrace Frontend                    |
|          (React 18, Vite, TypeScript, Tailwind CSS)         |
|  - Incident workbench and scenario selector                 |
|  - Dependency graph visualizer and blast radius map         |
|  - Evidence timeline, ranked hypotheses, diagnostic cards   |
+------------------------------+------------------------------+
                               |
                               | HTTP / JSON API
                               v
+-------------------------------------------------------------+
|                       FastAPI Backend                       |
|  - Native FalkorDB Cypher query engine                      |
|  - Multi-hop blast radius isolation (1 to 4 hops)           |
|  - Deterministic candidate ranking and distractor demotion  |
|  - Epistemic uncertainty detection and safe abstention      |
|  - Read-only diagnostic recommendation engine               |
+---------------+-----------------------------+---------------+
                |                             |
  Cypher (Redis)|                             | Provider API
                v                             v
+-------------------------------+ +---------------------------+
|         FalkorDB Graph        | |    Modular AI Provider    |
|     (Primary Graph Store)     | |   (OpenAI / Claude / Stub)|
| Service topologies, releases, | | Environment health probes |
| alerts, logs, and trace links | | (Not in critical scoring) |
+-------------------------------+ +---------------------------+
```

### AI Architecture Note
Root-cause candidate extraction, scoring, and abstention run entirely deterministically via Cypher queries and Python scoring heuristics in FalkorDB. A modular AI provider interface (`backend/app/ai/provider.py`) supports OpenAI, Anthropic, and stub modes, used for health probes and ready for optional narrative generation. It is excluded from the critical ranking path so that the engine never hallucinates nonexistent services, releases, or causal connections.

---

## Graph Schema and Cypher Queries

The FalkorDB property graph models microservice dependencies and incident telemetry. The complete schema, constraints, and indexes are in [docs/schema.cypher](docs/schema.cypher).

### Node Labels

| Label | Properties | Role |
| :--- | :--- | :--- |
| `:Incident` | `id`, `title`, `severity`, `status`, `started_at`, `summary` | Root incident record |
| `:Service` | `id`, `name`, `tier`, `team`, `language`, `status` | System component |
| `:Deployment` | `id`, `version`, `commit_sha`, `timestamp`, `status`, `deployed_by` | Code or configuration release |
| `:Alert` | `id`, `name`, `severity`, `timestamp`, `status`, `metric_name`, `metric_value` | Firing metric threshold |
| `:LogEvent` | `id`, `level`, `message`, `timestamp`, `trace_id` | Log entry with distributed trace ID |

### Relationship Types

| Relationship | Source | Target | Key Properties | Description |
| :--- | :--- | :--- | :--- | :--- |
| `[:DEPENDS_ON]` | `:Service` | `:Service` | `protocol`, `latency_p99_ms`, `critical` | Multi-hop dependency call graph |
| `[:DEPLOYED_TO]` | `:Deployment` | `:Service` | `environment` | Links releases to target service |
| `[:TRIGGERED_ON]` | `:Alert` | `:Service` | - | Links active alerts to failing service |
| `[:EMITTED_BY]` | `:LogEvent` | `:Service` | - | Links logs to emitting service |
| `[:AFFECTS]` | `:Incident` | `:Service` | - | Identifies symptom services |
| `[:ROOT_CAUSE]` | `:Incident` | `:Deployment` \| `:Service` \| `:Alert` | `score`, `reasoning` | Causal hypothesis linkage |

### Representative Cypher Queries

#### 1. Multi-Hop Dependency Blast Radius (1 to 4 Hops)
```cypher
MATCH path = (s:Service {id: $service_id})-[:DEPENDS_ON*1..4]->(target:Service)
RETURN [node IN nodes(path) | node.id] AS chain,
       [rel IN relationships(path) | rel.critical] AS criticals,
       [rel IN relationships(path) | rel.protocol] AS protos,
       [rel IN relationships(path) | rel.latency_p99_ms] AS latencies;
```

#### 2. Temporal Candidate Deployment Correlation
```cypher
MATCH (d:Deployment)-[:DEPLOYED_TO]->(s:Service)
WHERE s.id IN $service_ids
  AND d.timestamp <= $max_ts
  AND d.timestamp >= ($max_ts - $window_ms)
RETURN d.id AS id, d.version AS version, d.commit_sha AS commit_sha,
       d.timestamp AS timestamp, d.status AS status, d.deployed_by AS deployed_by,
       s.id AS service_id, s.name AS service_name
ORDER BY d.timestamp DESC;
```

#### 3. Active Firing Alerts Across Topology
```cypher
MATCH (a:Alert)-[:TRIGGERED_ON]->(s:Service)
WHERE s.id IN $service_ids
  AND (a.timestamp <= ($max_ts + 300000) AND a.timestamp >= ($max_ts - $window_ms))
RETURN a.id AS id, a.name AS name, a.severity AS severity,
       a.timestamp AS timestamp, a.metric_name AS metric_name,
       a.metric_value AS metric_value, s.id AS service_id
ORDER BY a.timestamp ASC;
```

#### 4. Corroborating Anomaly Logs with Trace Identifiers
```cypher
MATCH (l:LogEvent)-[:EMITTED_BY]->(s:Service)
WHERE s.id IN $service_ids
  AND l.timestamp <= ($max_ts + 300000)
  AND l.timestamp >= ($max_ts - $window_ms)
RETURN l.id AS id, l.level AS level, l.message AS message,
       l.timestamp AS timestamp, l.trace_id AS trace_id, s.id AS service_id
ORDER BY l.timestamp DESC;
```

---

## Synthetic Evaluation Benchmark

The repository includes a suite of 10 curated synthetic failure scenarios seeded directly into FalkorDB. These evaluate the engine's deterministic ranking, distractor demotion, and abstention behavior across varied microservice topologies.

### The 10 Scenarios

1. `inc-01-payment-pool-exhaustion`: Two-hop database connection pool exhaustion during checkout, with a routine distractor release on an unrelated service.
2. `inc-02-auth-jwt-secret-mismatch`: Global 401 Unauthorized cascade caused by an auth secret rotation deployment.
3. `inc-03-inventory-deadlock-cascade`: Database row-level lock timeouts during inventory allocation.
4. `inc-04-search-vector-oom`: Product search container crash following a vector index update.
5. `inc-05-notification-rate-limit-cascade`: Third-party SMS vendor 429 rate limits causing worker thread pool starvation.
6. `inc-06-upstream-dns-misconfig`: Cluster CoreDNS packet drop alert without any code deployment events.
7. `inc-07-insufficient-evidence-abstain`: Latency breach accompanied by dropped telemetry; tests safe abstention.
8. `inc-08-dual-competing-deployments`: Two simultaneous deployments; fraud evaluator isolated via trace matches, tax release demoted.
9. `inc-09-deep-chain-database-schema-migration`: Four-hop ledger DDL lock propagating upstream to a mobile gateway.
10. `inc-10-external-cloud-dependency-degradation`: S3 503 SlowDown rate limits causing video transcoder pipeline backpressure.

### Benchmark Results

Run the benchmark with:
```bash
python backend/scripts/evaluate_investigation.py
```

Results across all 10 scenarios:

| # | Incident ID | Expected Cause | Top-1 Found | Score | Status | Latency |
| :-: | :--- | :--- | :--- | :-: | :-: | :-: |
| 1 | `inc-01-payment-pool-exhaustion` | `dep-payment-v2.4.1` | `dep-payment-v2.4.1` | 0.955 | PASS | 60.2 ms |
| 2 | `inc-02-auth-jwt-secret-mismatch` | `dep-auth-v1.12.0` | `dep-auth-v1.12.0` | 1.000 | PASS | 4.8 ms |
| 3 | `inc-03-inventory-deadlock-cascade` | `dep-inv-v3.2.0` | `dep-inv-v3.2.0` | 1.000 | PASS | 3.8 ms |
| 4 | `inc-04-search-vector-oom` | `dep-search-v5.0.0` | `dep-search-v5.0.0` | 1.000 | PASS | 4.3 ms |
| 5 | `inc-05-notification-rate-limit-cascade` | `dep-notif-v1.4.2` | `dep-notif-v1.4.2` | 1.000 | PASS | 4.5 ms |
| 6 | `inc-06-upstream-dns-misconfig` | `alt-dns-core-failure` | `alt-dns-core-failure` | 0.812 | PASS | 3.9 ms |
| 7 | `inc-07-insufficient-evidence-abstain` | `ABSTAIN` | `NONE` | 0.000 | PASS | 3.5 ms |
| 8 | `inc-08-dual-competing-deployments` | `dep-fraud-v2.1` | `dep-fraud-v2.1` | 1.000 | PASS | 3.5 ms |
| 9 | `inc-09-deep-chain-database-schema-migration` | `dep-ledger-v1.0.4` | `dep-ledger-v1.0.4` | 0.915 | PASS | 4.2 ms |
| 10 | `inc-10-external-cloud-dependency-degradation` | `alt-s3-slowdown` | `alt-s3-slowdown` | 0.812 | PASS | 4.2 ms |

**Summary Metrics:**
- **Top-1 Root-Cause Accuracy:** 100.0% (9/9 culprit scenarios)
- **Top-3 Root-Cause Recall:** 100.0% (9/9 culprit scenarios)
- **Misleading-Alert Demotion Rate:** 100.0% (8/8 distractor scenarios)
- **Insufficient Evidence Abstention:** 100.0% (1/1 gap scenarios)
- **Warm Graph Traversal Latency:** 4.1 ms mean (3.5–4.8 ms range across Scenarios 2–10)
- **Overall Mean Traversal Latency:** 9.7 ms (including Scenario 1 cold start at 60.2 ms)

**Evaluation Disclosure:**
These benchmarks evaluate deterministic graph ranking across 10 curated synthetic topologies. They demonstrate reproducibility and algorithmic correctness, but they do not represent real-world production outages or mathematical proof of causality. Confidence scores reflect heuristic evidence alignment rather than formal probabilities.

---

## Local Setup

### Prerequisites
- Docker (for running FalkorDB)
- Python 3.10+
- Node.js 18+ (tested on Node 20 and 22)

---

### 1. Start FalkorDB
Run the official FalkorDB Docker container:
```bash
docker run -d --name causaltrace-falkordb -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
```
- Port `6379`: Redis/Cypher query interface
- Port `3000`: Built-in FalkorDB web visualizer

---

### 2. Configure and Start the Backend
From the repository root:
```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify backend health:
```bash
curl -s http://localhost:8000/api/health
```

---

### 3. Seed the Graph
With FalkorDB and the backend running, seed all 10 synthetic topologies and incident records:
```bash
curl -X POST http://localhost:8000/api/incidents/seed
```
You can also reset the graph at any time using the "Reset Graph" button in the frontend workbench.

---

### 4. Configure and Start the Frontend
In a separate terminal:
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

### 5. Run Tests and Verification

#### Backend Unit and Integration Tests (29 Tests)
```bash
cd backend
pytest -v
```

#### Synthetic Evaluation Benchmark
```bash
cd backend
python scripts/evaluate_investigation.py
```

#### Frontend Production Build
```bash
cd frontend
npm run build
```

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service status, FalkorDB ping latency, and AI provider state |
| `GET` | `/api/incidents` | List all incidents stored in the graph |
| `GET` | `/api/incidents/{id}/investigation` | Execute graph investigation for an incident |
| `POST` | `/api/incidents/seed` | Seed or reset the 10 benchmark incident topologies |

### Example Investigation Request
```bash
curl -s http://localhost:8000/api/incidents/inc-01-payment-pool-exhaustion/investigation | python3 -m json.tool
```

---

## Limitations

- **Heuristic Ranking:** Candidate scores reflect topological distance, temporal proximity, and corroborating telemetry. They do not constitute formal do-calculus causal inference.
- **Topology Size:** The current benchmark topologies contain up to 10 services and 4 hops. Larger topologies with hundreds of services will be evaluated in future work.
- **Batch Seeding:** Topologies and telemetry are currently ingested via Cypher batches. Real-time streaming ingestion via OpenTelemetry or Kafka collectors is planned.

---

## AI-Assisted Development Disclosure

In accordance with hackathon guidelines:
- **Development Tools:** AI coding assistants were used during development for boilerplate scaffolding, TypeScript typing, and test authoring.
- **Runtime System:** The incident investigation engine does not use a generative LLM for candidate generation, graph traversal, or scoring. All ranking, demotion, and abstention decisions are executed deterministically via FalkorDB Cypher queries and graph algorithms. The modular LLM adapter (`backend/app/ai/provider.py`) is used exclusively for health probes and optional future summarization, ensuring no generative hallucinations can affect root-cause identification.

---

## License

MIT License. Built for the **Graph Hacks** hackathon.
