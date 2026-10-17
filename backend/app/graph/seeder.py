"""Idempotent seed script for CausalTrace FalkorDB graph database.

Seeds 10 distinct, deterministic synthetic incident topologies covering:
1. Multi-hop synchronous failure cascades
2. Authentication token/JWT secret mismatches
3. Database row locking deadlock cascades
4. Container Out-Of-Memory (OOM) heap exhaustion
5. External API rate limit & thread starvation cascades
6. Pure infrastructure DNS failures (zero application releases)
7. Insufficient evidence / missing telemetry scenarios (explicit abstention)
8. Dual simultaneous competing deployments in parallel microservices
9. Deep 4-hop schema migration database locks
10. External cloud provider third-party outages
"""

import logging
from typing import Dict, Any, List
from app.graph.client import graph_client

logger = logging.getLogger(__name__)

# Base reference timestamp: 2026-02-02 00:00:00 UTC
BASE_T = 1770000000000


def seed_incident_graph(graph_name: str = None) -> Dict[str, Any]:
    """Idempotently seed the FalkorDB graph with 10 synthetic incident topologies."""
    graph = graph_client.get_graph(graph_name)

    # 1. Ensure FalkorDB Indexes
    for label, prop in [
        ("Service", "id"),
        ("Incident", "id"),
        ("Deployment", "id"),
        ("Alert", "id"),
        ("LogEvent", "id"),
    ]:
        try:
            graph.query(f"CREATE INDEX FOR (n:{label}) ON (n.{prop})")
        except Exception:
            pass

    # Helper functions for executing batch merges
    def merge_service(sid: str, name: str, tier: str, team: str, lang: str, status: str):
        graph.query(
            """
            MERGE (s:Service {id: $sid})
            SET s.name = $name, s.tier = $tier, s.team = $team, s.language = $lang, s.status = $status
            """,
            {"sid": sid, "name": name, "tier": tier, "team": team, "lang": lang, "status": status},
        )

    def merge_dep(src: str, dst: str, proto: str, latency: float, crit: bool):
        graph.query(
            """
            MATCH (a:Service {id: $src})
            MATCH (b:Service {id: $dst})
            MERGE (a)-[r:DEPENDS_ON]->(b)
            SET r.protocol = $proto, r.latency_p99_ms = $latency, r.critical = $crit
            """,
            {"src": src, "dst": dst, "proto": proto, "latency": latency, "crit": crit},
        )

    def merge_deployment(did: str, ver: str, sha: str, ts: int, st: str, by: str, sid: str):
        graph.query(
            """
            MERGE (d:Deployment {id: $did})
            SET d.version = $ver, d.commit_sha = $sha, d.timestamp = $ts, d.status = $st, d.deployed_by = $by
            WITH d
            MATCH (s:Service {id: $sid})
            MERGE (d)-[:DEPLOYED_TO {environment: 'production'}]->(s)
            """,
            {"did": did, "ver": ver, "sha": sha, "ts": ts, "st": st, "by": by, "sid": sid},
        )

    def merge_alert(aid: str, name: str, sev: str, ts: int, st: str, mname: str, mval: float, sid: str, inc_id: str):
        graph.query(
            """
            MERGE (a:Alert {id: $aid})
            SET a.name = $name, a.severity = $sev, a.timestamp = $ts, a.status = $st,
                a.metric_name = $mname, a.metric_value = $mval
            WITH a
            MATCH (s:Service {id: $sid})
            MERGE (a)-[:TRIGGERED_ON]->(s)
            WITH a
            MATCH (i:Incident {id: $inc_id})
            MERGE (a)-[:CORRELATED_WITH {time_delta_sec: toInteger(($ts - i.started_at) / 1000)}]->(i)
            """,
            {"aid": aid, "name": name, "sev": sev, "ts": ts, "st": st, "mname": mname, "mval": mval, "sid": sid, "inc_id": inc_id},
        )

    def merge_log(lid: str, lvl: str, msg: str, ts: int, trc: str, sid: str):
        graph.query(
            """
            MERGE (l:LogEvent {id: $lid})
            SET l.level = $lvl, l.message = $msg, l.timestamp = $ts, l.trace_id = $trc
            WITH l
            MATCH (s:Service {id: $sid})
            MERGE (l)-[:EMITTED_BY]->(s)
            """,
            {"lid": lid, "lvl": lvl, "msg": msg, "ts": ts, "trc": trc, "sid": sid},
        )

    def merge_incident(iid: str, title: str, sev: str, started_at: int, summary: str, affected_sids: List[str]):
        graph.query(
            """
            MERGE (i:Incident {id: $iid})
            SET i.title = $title, i.severity = $sev, i.status = 'INVESTIGATING',
                i.started_at = $started_at, i.summary = $summary
            """,
            {"iid": iid, "title": title, "sev": sev, "started_at": started_at, "summary": summary},
        )
        for sid in affected_sids:
            graph.query(
                """
                MATCH (i:Incident {id: $iid})
                MATCH (s:Service {id: $sid})
                MERGE (i)-[:AFFECTS]->(s)
                """,
                {"iid": iid, "sid": sid},
            )

    # ==========================================================================
    # SCENARIO 1: inc-01-payment-pool-exhaustion (and inc-2026-checkout-crash)
    # ==========================================================================
    t1 = BASE_T
    merge_service("svc-checkout-web", "Checkout Web Frontend", "tier-1", "checkout-experience", "typescript", "CRITICAL")
    merge_service("svc-order-service", "Order Orchestration API", "tier-1", "order-platform", "go", "DEGRADED")
    merge_service("svc-payment-service", "Payment Processing Service", "tier-1", "payments-core", "python", "DEGRADED")
    merge_service("svc-postgres-payment-db", "Postgres Payment Cluster", "tier-1", "database-infra", "c", "HEALTHY")
    merge_service("svc-inventory-service", "Inventory Allocation Engine", "tier-2", "fulfillment", "java", "HEALTHY")
    merge_service("svc-recommendation-service", "Recommendation Engine", "tier-3", "ml-discovery", "python", "HEALTHY")

    merge_dep("svc-checkout-web", "svc-order-service", "gRPC", 12.5, True)
    merge_dep("svc-order-service", "svc-payment-service", "gRPC", 25.0, True)
    merge_dep("svc-payment-service", "svc-postgres-payment-db", "TCP", 4.2, True)
    merge_dep("svc-order-service", "svc-inventory-service", "HTTP", 45.0, False)
    merge_dep("svc-checkout-web", "svc-recommendation-service", "HTTP", 85.0, False)

    for iid in ["inc-01-payment-pool-exhaustion", "inc-2026-checkout-crash"]:
        merge_incident(iid, "High 5xx error rate and p99 latency surge on checkout", "SEV-1", t1, "Checkout failures due to downstream payment RPC timeout", ["svc-checkout-web"])

    merge_deployment("dep-payment-v2.4.1", "v2.4.1", "8f31bca", t1 - 720000, "SUCCESS", "ci-deployer", "svc-payment-service")
    merge_deployment("dep-rec-v3.0.0", "v3.0.0", "1a49e02", t1 - 300000, "SUCCESS", "argo-cd", "svc-recommendation-service")
    merge_deployment("dep-inventory-v1.8.0", "v1.8.0", "9c8821d", t1 - 2700000, "SUCCESS", "ci-deployer", "svc-inventory-service")

    for iid in ["inc-01-payment-pool-exhaustion", "inc-2026-checkout-crash"]:
        merge_alert("alt-checkout-5xx", "High5xxErrorRate", "CRITICAL", t1, "FIRING", "http_requests_5xx_rate", 18.2, "svc-checkout-web", iid)
        merge_alert("alt-pay-conn-pool", "DbConnectionPoolExhaustion", "CRITICAL", t1 - 480000, "FIRING", "db_pool_exhaustion_pct", 98.5, "svc-payment-service", iid)
        merge_alert("alt-rec-cpu-high", "HighCpuUtilization", "HIGH", t1 - 240000, "FIRING", "cpu_utilization_pct", 94.0, "svc-recommendation-service", iid)

    merge_log("log-pay-fatal-01", "FATAL", "ConnectionPoolTimeoutException: Timeout waiting for connection from pool (max=50, active=50)", t1 - 420000, "trc-checkout-881", "svc-payment-service")
    merge_log("log-order-err-01", "ERROR", "Downstream payment RPC failed with UNAVAILABLE: connection reset by peer", t1 - 360000, "trc-checkout-881", "svc-order-service")
    merge_log("log-rec-info-01", "INFO", "Cache warm-up completed successfully for 10000 user vector embeddings", t1 - 180000, "trc-rec-warm-99", "svc-recommendation-service")

    # ==========================================================================
    # SCENARIO 2: inc-02-auth-jwt-secret-mismatch
    # ==========================================================================
    t2 = BASE_T + 3600000
    merge_service("svc-api-gateway", "API Gateway Ingress", "tier-1", "networking", "go", "CRITICAL")
    merge_service("svc-auth-service", "Authentication Authority", "tier-1", "security-core", "rust", "DEGRADED")
    merge_service("svc-user-db", "User Credentials Store", "tier-1", "security-core", "c", "HEALTHY")
    merge_service("svc-analytics-worker", "Clickstream Analytics Worker", "tier-3", "analytics", "python", "HEALTHY")

    merge_dep("svc-api-gateway", "svc-auth-service", "gRPC", 8.0, True)
    merge_dep("svc-auth-service", "svc-user-db", "TCP", 3.0, True)
    merge_dep("svc-api-gateway", "svc-analytics-worker", "Kafka", 20.0, False)

    merge_incident("inc-02-auth-jwt-secret-mismatch", "Global 401 Unauthorized cascade across API Gateway", "SEV-1", t2, "API Gateway rejecting all valid bearer tokens after auth secret rotation", ["svc-api-gateway"])
    merge_deployment("dep-auth-v1.12.0", "v1.12.0", "3f10a8c", t2 - 600000, "SUCCESS", "ci-deployer", "svc-auth-service")
    merge_deployment("dep-analytics-v0.8.2", "v0.8.2", "4b192e1", t2 - 240000, "SUCCESS", "ci-deployer", "svc-analytics-worker")

    merge_alert("alt-auth-401-spike", "UnauthorizedTokenSpike", "CRITICAL", t2 - 300000, "FIRING", "token_validation_failure_rate", 92.4, "svc-auth-service", "inc-02-auth-jwt-secret-mismatch")
    merge_alert("alt-worker-packet-drop", "WorkerNetworkPacketDrop", "HIGH", t2 - 180000, "FIRING", "packet_drop_pct", 14.2, "svc-analytics-worker", "inc-02-auth-jwt-secret-mismatch")

    merge_log("log-auth-jwt-01", "FATAL", "KeySignatureMismatch: Key ID 'sec-2026-v2' does not match active keystore ring", t2 - 350000, "trc-auth-9901", "svc-auth-service")
    merge_log("log-gw-auth-01", "ERROR", "TokenValidationRPC returned HTTP 401 Invalid Signature for trace trc-auth-9901", t2 - 250000, "trc-auth-9901", "svc-api-gateway")

    # ==========================================================================
    # SCENARIO 3: inc-03-inventory-deadlock-cascade
    # ==========================================================================
    t3 = BASE_T + 7200000
    merge_service("svc-inventory-mysql-db", "Inventory MySQL Cluster", "tier-1", "database-infra", "c", "DEGRADED")
    merge_dep("svc-order-service", "svc-inventory-service", "gRPC", 15.0, True)
    merge_dep("svc-inventory-service", "svc-inventory-mysql-db", "TCP", 5.0, True)

    merge_incident("inc-03-inventory-deadlock-cascade", "Order fulfillment timeouts caused by database row-level locking", "SEV-2", t3, "Deadlocks occurring on inventory reserve transactions", ["svc-order-service"])
    merge_deployment("dep-inv-v3.2.0", "v3.2.0", "a190ef4", t3 - 840000, "SUCCESS", "ci-deployer", "svc-inventory-service")
    merge_deployment("dep-order-v4.0.1", "v4.0.1", "b201fe5", t3 - 2100000, "SUCCESS", "ci-deployer", "svc-order-service")

    merge_alert("alt-inv-deadlock-rate", "DeadlockRateBreach", "CRITICAL", t3 - 420000, "FIRING", "mysql_deadlock_per_sec", 42.0, "svc-inventory-service", "inc-03-inventory-deadlock-cascade")
    merge_log("log-inv-deadlock-01", "FATAL", "DeadlockVictimException: Deadlock found when trying to get lock; try restarting transaction", t3 - 400000, "trc-inv-3301", "svc-inventory-service")
    merge_log("log-order-inv-01", "ERROR", "InventoryReserveRPC timed out after 3000ms for trace trc-inv-3301", t3 - 380000, "trc-inv-3301", "svc-order-service")

    # ==========================================================================
    # SCENARIO 4: inc-04-search-vector-oom
    # ==========================================================================
    t4 = BASE_T + 10800000
    merge_service("svc-product-catalog", "Product Catalog API", "tier-1", "catalog", "typescript", "CRITICAL")
    merge_service("svc-search-service", "Search Vector Engine", "tier-1", "search-team", "java", "CRITICAL")
    merge_service("svc-elasticsearch-cluster", "Elasticsearch Primary", "tier-1", "infra", "java", "HEALTHY")
    merge_service("svc-pricing-service", "Pricing Cache Service", "tier-2", "catalog", "go", "HEALTHY")

    merge_dep("svc-product-catalog", "svc-search-service", "gRPC", 15.0, True)
    merge_dep("svc-search-service", "svc-elasticsearch-cluster", "HTTP", 20.0, True)
    merge_dep("svc-product-catalog", "svc-pricing-service", "HTTP", 5.0, False)

    merge_incident("inc-04-search-vector-oom", "Product catalog search cluster container OOM crash", "SEV-1", t4, "Search engine pods crashing continuously due to vector index memory allocation", ["svc-product-catalog"])
    merge_deployment("dep-search-v5.0.0", "v5.0.0", "cc4810a", t4 - 480000, "SUCCESS", "ci-deployer", "svc-search-service")
    merge_deployment("dep-pricing-v2.1.0", "v2.1.0", "dd1921f", t4 - 360000, "SUCCESS", "ci-deployer", "svc-pricing-service")

    merge_alert("alt-search-oom-restarts", "PodOOMKilledCrashLoop", "CRITICAL", t4 - 240000, "FIRING", "container_restart_count", 14.0, "svc-search-service", "inc-04-search-vector-oom")
    merge_alert("alt-pricing-cache-miss", "PricingCacheMissSpike", "HIGH", t4 - 300000, "FIRING", "cache_miss_rate", 38.5, "svc-pricing-service", "inc-04-search-vector-oom")

    merge_log("log-search-oom-01", "FATAL", "OutOfMemoryError: Java heap space during HNSW vector indexing memory allocation", t4 - 260000, "trc-search-5501", "svc-search-service")
    merge_log("log-catalog-err-01", "ERROR", "ProductSearch gRPC failed with UNAVAILABLE: connection closed by peer", t4 - 220000, "trc-search-5501", "svc-product-catalog")

    # ==========================================================================
    # SCENARIO 5: inc-05-notification-rate-limit-cascade
    # ==========================================================================
    t5 = BASE_T + 14400000
    merge_service("svc-notification-dispatcher", "Notification Dispatcher", "tier-1", "customer-comm", "python", "CRITICAL")
    merge_service("svc-sms-gateway", "SMS Provider Gateway", "tier-1", "external", "unknown", "DEGRADED")
    merge_service("svc-email-renderer", "Async Email Renderer", "tier-3", "customer-comm", "python", "HEALTHY")

    merge_dep("svc-notification-dispatcher", "svc-sms-gateway", "HTTP", 120.0, True)
    merge_dep("svc-notification-dispatcher", "svc-email-renderer", "HTTP", 40.0, False)

    merge_incident("inc-05-notification-rate-limit-cascade", "Order processing worker thread starvation on SMS dispatch", "SEV-2", t5, "Notification dispatcher thread pool saturated by vendor 429 backpressure", ["svc-notification-dispatcher"])
    merge_deployment("dep-notif-v1.4.2", "v1.4.2", "55e9021", t5 - 660000, "SUCCESS", "ci-deployer", "svc-notification-dispatcher")
    merge_deployment("dep-email-template-v1.1", "v1.1", "ee99101", t5 - 900000, "SUCCESS", "ci-deployer", "svc-email-renderer")

    merge_alert("alt-notif-429-exhaustion", "ThreadPoolStarvation", "CRITICAL", t5 - 300000, "FIRING", "active_worker_threads_pct", 100.0, "svc-notification-dispatcher", "inc-05-notification-rate-limit-cascade")
    merge_log("log-notif-429-01", "FATAL", "TooManyRequestsException: HTTP 429 Client Rate Limit exceeded on vendor endpoint", t5 - 320000, "trc-notif-1102", "svc-notification-dispatcher")

    # ==========================================================================
    # SCENARIO 6: inc-06-upstream-dns-misconfig (Infrastructure / Zero Deployments)
    # ==========================================================================
    t6 = BASE_T + 18000000
    merge_service("svc-dns-core", "CoreDNS Cluster Service", "tier-1", "infra-core", "go", "CRITICAL")
    merge_dep("svc-api-gateway", "svc-dns-core", "UDP", 1.5, True)

    merge_incident("inc-06-upstream-dns-misconfig", "Intermittent DNS resolution failures across cluster pods", "SEV-1", t6, "CoreDNS cluster pods reporting high UDP packet drops, failing service discovery", ["svc-api-gateway"])
    merge_alert("alt-dns-core-failure", "CoreDNSResolutionFailure", "CRITICAL", t6 - 120000, "FIRING", "dns_failure_pct", 88.4, "svc-dns-core", "inc-06-upstream-dns-misconfig")
    merge_log("log-dns-err-01", "FATAL", "UnknownHostException: Temporary failure in name resolution for upstream internal domain", t6 - 100000, "trc-dns-7701", "svc-api-gateway")

    # ==========================================================================
    # SCENARIO 7: inc-07-insufficient-evidence-abstain (Missing Telemetry)
    # ==========================================================================
    t7 = BASE_T + 21600000
    merge_service("svc-billing-service", "Billing Ledger API", "tier-1", "billing", "go", "DEGRADED")
    merge_service("svc-billing-storage", "Billing Storage Node", "tier-1", "billing", "c", "HEALTHY")
    merge_dep("svc-billing-service", "svc-billing-storage", "TCP", 2.0, True)

    merge_incident("inc-07-insufficient-evidence-abstain", "Billing service latency spike with missing telemetry and no recent releases", "SEV-2", t7, "Latency breach with dropped telemetry pipeline; no code deployments in 5 days", ["svc-billing-service"])
    # Stale deployment 5 days ago (120 hours prior)
    merge_deployment("dep-billing-v0.9.1-stale", "v0.9.1", "00a11ff", t7 - 432000000, "SUCCESS", "ci-deployer", "svc-billing-service")

    # ==========================================================================
    # SCENARIO 8: inc-08-dual-competing-deployments
    # ==========================================================================
    t8 = BASE_T + 25200000
    merge_service("svc-checkout-aggregator", "Checkout Aggregator", "tier-1", "checkout-experience", "go", "CRITICAL")
    merge_service("svc-fraud-evaluator", "Fraud Risk Evaluator", "tier-1", "risk-platform", "python", "DEGRADED")
    merge_service("svc-tax-calculator", "Realtime Tax Engine", "tier-1", "payments-core", "java", "HEALTHY")

    merge_dep("svc-checkout-aggregator", "svc-fraud-evaluator", "gRPC", 30.0, True)
    merge_dep("svc-checkout-aggregator", "svc-tax-calculator", "gRPC", 25.0, True)

    merge_incident("inc-08-dual-competing-deployments", "Checkout stalls with dual simultaneous fraud and tax deployments", "SEV-1", t8, "Simultaneous fraud and tax deployments; fraud evaluator throwing unhandled null pointer exceptions", ["svc-checkout-aggregator"])
    merge_deployment("dep-fraud-v2.1", "v2.1", "ff8812a", t8 - 480000, "SUCCESS", "ci-deployer", "svc-fraud-evaluator")
    merge_deployment("dep-tax-v1.9", "v1.9", "cc7731b", t8 - 540000, "SUCCESS", "ci-deployer", "svc-tax-calculator")

    merge_alert("alt-fraud-timeout", "FraudEvaluatorNPE", "CRITICAL", t8 - 240000, "FIRING", "unhandled_exception_rate", 65.0, "svc-fraud-evaluator", "inc-08-dual-competing-deployments")
    merge_alert("alt-tax-latency-bump", "TaxEngineLatencyBump", "MEDIUM", t8 - 300000, "FIRING", "latency_p95_ms", 120.0, "svc-tax-calculator", "inc-08-dual-competing-deployments")

    merge_log("log-fraud-01", "FATAL", "NullPointerException in ML decision tree evaluator at RiskEngine.py:104", t8 - 260000, "trc-compete-8801", "svc-fraud-evaluator")
    merge_log("log-aggregator-01", "ERROR", "CheckoutAggregator RPC to FraudEvaluator failed with INTERNAL for trace trc-compete-8801", t8 - 220000, "trc-compete-8801", "svc-checkout-aggregator")

    # ==========================================================================
    # SCENARIO 9: inc-09-deep-chain-database-schema-migration
    # ==========================================================================
    t9 = BASE_T + 28800000
    merge_service("svc-mobile-gateway", "Mobile Edge Gateway", "tier-1", "networking", "go", "CRITICAL")
    merge_service("svc-bff-service", "Mobile Backend-For-Frontend", "tier-1", "mobile", "typescript", "DEGRADED")
    merge_service("svc-account-service", "User Account Service", "tier-1", "account", "go", "DEGRADED")
    merge_service("svc-ledger-service", "Core Ledger Service", "tier-1", "banking", "java", "DEGRADED")
    merge_service("svc-ledger-db", "CockroachDB Ledger Cluster", "tier-1", "infra-db", "c", "DEGRADED")

    # 4-hop chain
    merge_dep("svc-mobile-gateway", "svc-bff-service", "HTTP", 10.0, True)
    merge_dep("svc-bff-service", "svc-account-service", "gRPC", 15.0, True)
    merge_dep("svc-account-service", "svc-ledger-service", "gRPC", 20.0, True)
    merge_dep("svc-ledger-service", "svc-ledger-db", "TCP", 5.0, True)

    merge_incident("inc-09-deep-chain-database-schema-migration", "Ledger balance transaction locks propagating 4 hops upstream", "SEV-1", t9, "Schema migration DDL lock in ledger database causing cascading thread locks 4 hops up to mobile gateway", ["svc-mobile-gateway"])
    merge_deployment("dep-ledger-v1.0.4", "v1.0.4", "7719ab2", t9 - 780000, "SUCCESS", "ci-deployer", "svc-ledger-service")

    merge_alert("alt-bff-latency", "BFFLatencySpike", "HIGH", t9 - 300000, "FIRING", "latency_p99_ms", 950.0, "svc-bff-service", "inc-09-deep-chain-database-schema-migration")
    merge_alert("alt-ledger-lock-timeout", "TableLockTimeout", "CRITICAL", t9 - 420000, "FIRING", "lock_wait_timeout_count", 88.0, "svc-ledger-service", "inc-09-deep-chain-database-schema-migration")

    merge_log("log-ledger-lock-01", "FATAL", "LockWaitTimeoutException: Lock wait timeout exceeded trying to execute schema migration alter table lock", t9 - 450000, "trc-deep-1092", "svc-ledger-service")
    merge_log("log-mobile-gw-01", "ERROR", "MobileGateway upstream timeout 504 on account ledger query for trace trc-deep-1092", t9 - 200000, "trc-deep-1092", "svc-mobile-gateway")

    # ==========================================================================
    # SCENARIO 10: inc-10-external-cloud-dependency-degradation
    # ==========================================================================
    t10 = BASE_T + 32400000
    merge_service("svc-video-transcoder", "Video Transcoder Service", "tier-1", "media", "python", "CRITICAL")
    merge_service("svc-cloud-s3-storage", "External S3 Object Store", "tier-1", "cloud-aws", "external", "CRITICAL")
    merge_dep("svc-video-transcoder", "svc-cloud-s3-storage", "HTTP", 250.0, True)

    merge_incident("inc-10-external-cloud-dependency-degradation", "Transcoder failures attributed to external S3 rate limiting", "SEV-2", t10, "External cloud provider returning 503 SlowDown rate limits; internal code unchanged", ["svc-video-transcoder"])
    merge_deployment("dep-transcoder-v2.0-routine", "v2.0", "9901aa3", t10 - 2100000, "SUCCESS", "ci-deployer", "svc-video-transcoder")

    merge_alert("alt-s3-slowdown", "S3SlowDown503Errors", "CRITICAL", t10 - 300000, "FIRING", "s3_503_rate", 74.2, "svc-cloud-s3-storage", "inc-10-external-cloud-dependency-degradation")
    merge_log("log-transcoder-01", "ERROR", "AmazonS3Exception: 503 Slow Down: Please reduce your request rate. Request ID: AWS-S3-9912", t10 - 280000, "trc-s3-9912", "svc-video-transcoder")

    return {
        "status": "success",
        "incidents_seeded": 10,
        "message": "Successfully seeded 10 diverse production incident topologies into FalkorDB.",
    }


if __name__ == "__main__":
    result = seed_incident_graph()
    print("Seed complete:", result)
