"""Ground-Truth Incident Benchmark Dataset for CausalTrace.

IMPORTANT ARCHITECTURAL CONSTRAINT:
This file contains the ground truth for evaluating CausalTrace investigation accuracy.
It MUST NEVER be imported by or exposed to the graph query service, investigation logic,
LLM reasoning provider, or API endpoints. It is consumed solely by evaluation benchmarks
and test suites.
"""

from typing import Dict, Any, List

GROUND_TRUTH_DATASET: Dict[str, Dict[str, Any]] = {
    # --------------------------------------------------------------------------
    # Scenario 1: Multi-Hop Synchronous Connection Pool Exhaustion (Baseline)
    # --------------------------------------------------------------------------
    "inc-01-payment-pool-exhaustion": {
        "incident_id": "inc-01-payment-pool-exhaustion",
        "title": "Cascading 500 error spike during checkout completion",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "dep-payment-v2.4.1",
            "entity_type": "Deployment",
            "service_id": "svc-payment-service",
            "service_name": "Payment Processing Service",
        },
        "distractors": ["dep-rec-v3.0.0"],
        "expected_min_score": 0.85,
        "expected_confidence": "HIGH",
    },

    # Also keep alias inc-2026-checkout-crash pointing to Scenario 1 for backward compatibility
    "inc-2026-checkout-crash": {
        "incident_id": "inc-2026-checkout-crash",
        "title": "Cascading 5xx surge and checkout outage",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "dep-payment-v2.4.1",
            "entity_type": "Deployment",
            "service_id": "svc-payment-service",
            "service_name": "Payment Processing Service",
        },
        "distractors": ["dep-rec-v3.0.0"],
        "expected_min_score": 0.85,
        "expected_confidence": "HIGH",
    },

    # --------------------------------------------------------------------------
    # Scenario 2: Auth JWT Secret Mismatch Across Gateway
    # --------------------------------------------------------------------------
    "inc-02-auth-jwt-secret-mismatch": {
        "incident_id": "inc-02-auth-jwt-secret-mismatch",
        "title": "Global 401 Unauthorized cascade across API Gateway",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "dep-auth-v1.12.0",
            "entity_type": "Deployment",
            "service_id": "svc-auth-service",
            "service_name": "Authentication Authority",
        },
        "distractors": ["dep-analytics-v0.8.2"],
        "expected_min_score": 0.80,
        "expected_confidence": "HIGH",
    },

    # --------------------------------------------------------------------------
    # Scenario 3: Inventory Database Row Locking Deadlock Cascade
    # --------------------------------------------------------------------------
    "inc-03-inventory-deadlock-cascade": {
        "incident_id": "inc-03-inventory-deadlock-cascade",
        "title": "Order fulfillment timeouts caused by database row-level locking",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "dep-inv-v3.2.0",
            "entity_type": "Deployment",
            "service_id": "svc-inventory-service",
            "service_name": "Inventory Allocation Engine",
        },
        "distractors": ["dep-order-v4.0.1"],
        "expected_min_score": 0.80,
        "expected_confidence": "HIGH",
    },

    # --------------------------------------------------------------------------
    # Scenario 4: Vector Search Out-Of-Memory (OOMKilled)
    # --------------------------------------------------------------------------
    "inc-04-search-vector-oom": {
        "incident_id": "inc-04-search-vector-oom",
        "title": "Product catalog search cluster container OOM crash",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "dep-search-v5.0.0",
            "entity_type": "Deployment",
            "service_id": "svc-search-service",
            "service_name": "Search Vector Engine",
        },
        "distractors": ["dep-pricing-v2.1.0"],
        "expected_min_score": 0.80,
        "expected_confidence": "HIGH",
    },

    # --------------------------------------------------------------------------
    # Scenario 5: External Notification Rate Limiting & Thread Starvation
    # --------------------------------------------------------------------------
    "inc-05-notification-rate-limit-cascade": {
        "incident_id": "inc-05-notification-rate-limit-cascade",
        "title": "Order processing worker thread starvation on SMS dispatch",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "dep-notif-v1.4.2",
            "entity_type": "Deployment",
            "service_id": "svc-notification-dispatcher",
            "service_name": "Notification Dispatcher",
        },
        "distractors": ["dep-email-template-v1.1"],
        "expected_min_score": 0.75,
        "expected_confidence": "HIGH",
    },

    # --------------------------------------------------------------------------
    # Scenario 6: Upstream Infrastructure DNS Outage (No App Deployment)
    # --------------------------------------------------------------------------
    "inc-06-upstream-dns-misconfig": {
        "incident_id": "inc-06-upstream-dns-misconfig",
        "title": "Intermittent DNS resolution failures across cluster pods",
        "expected_behavior": "IDENTIFY_INFRA_OR_ALERT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "alt-dns-core-failure",
            "entity_type": "Alert",
            "service_id": "svc-dns-core",
            "service_name": "CoreDNS Cluster Service",
        },
        "distractors": [],
        "expected_min_score": 0.50,
        "expected_confidence": "MEDIUM",
    },

    # --------------------------------------------------------------------------
    # Scenario 7: Insufficient Evidence / Dropped Telemetry (Explicit Abstention)
    # --------------------------------------------------------------------------
    "inc-07-insufficient-evidence-abstain": {
        "incident_id": "inc-07-insufficient-evidence-abstain",
        "title": "Billing service latency spike with missing telemetry and no recent releases",
        "expected_behavior": "ABSTAIN",
        "must_abstain": True,
        "true_root_cause": None,
        "distractors": ["dep-billing-v0.9.1-stale"],
        "expected_max_score": 0.45,
        "expected_confidence": "LOW",
    },

    # --------------------------------------------------------------------------
    # Scenario 8: Dual Competing Deployments in Aggregator
    # --------------------------------------------------------------------------
    "inc-08-dual-competing-deployments": {
        "incident_id": "inc-08-dual-competing-deployments",
        "title": "Checkout stalls with dual simultaneous fraud and tax deployments",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "dep-fraud-v2.1",
            "entity_type": "Deployment",
            "service_id": "svc-fraud-evaluator",
            "service_name": "Fraud Risk Evaluator",
        },
        "distractors": ["dep-tax-v1.9"],
        "expected_min_score": 0.70,
        "expected_confidence": "HIGH",
    },

    # --------------------------------------------------------------------------
    # Scenario 9: 4-Hop Deep Chain Database Schema Migration Lock
    # --------------------------------------------------------------------------
    "inc-09-deep-chain-database-schema-migration": {
        "incident_id": "inc-09-deep-chain-database-schema-migration",
        "title": "Ledger balance transaction locks propagating 4 hops upstream",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "dep-ledger-v1.0.4",
            "entity_type": "Deployment",
            "service_id": "svc-ledger-service",
            "service_name": "Core Ledger Service",
        },
        "distractors": ["alt-bff-latency"],
        "expected_min_score": 0.65,
        "expected_confidence": "MEDIUM",
    },

    # --------------------------------------------------------------------------
    # Scenario 10: External Cloud Provider Outage (S3 SlowDown / 503)
    # --------------------------------------------------------------------------
    "inc-10-external-cloud-dependency-degradation": {
        "incident_id": "inc-10-external-cloud-dependency-degradation",
        "title": "Transcoder failures attributed to external S3 rate limiting",
        "expected_behavior": "IDENTIFY_CULPRIT",
        "must_abstain": False,
        "true_root_cause": {
            "entity_id": "alt-s3-slowdown",
            "entity_type": "Alert",
            "service_id": "svc-cloud-s3-storage",
            "service_name": "External S3 Object Store",
        },
        "distractors": ["dep-transcoder-v2.0-routine"],
        "expected_min_score": 0.70,
        "expected_confidence": "HIGH",
    },
}


def get_ground_truth(incident_id: str) -> Dict[str, Any]:
    """Retrieve ground truth for an incident strictly for evaluation assertions."""
    if incident_id not in GROUND_TRUTH_DATASET:
        raise KeyError(f"No ground truth registered for incident '{incident_id}'.")
    return GROUND_TRUTH_DATASET[incident_id]


def list_benchmark_incident_ids() -> List[str]:
    """Return all unique benchmark incident IDs (excluding alias duplicates)."""
    return [k for k in GROUND_TRUTH_DATASET if k != "inc-2026-checkout-crash"]
