import inspect
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.graph.query import graph_query_service
from app.services.investigation import investigation_service
from app.evaluation.ground_truth import get_ground_truth


@pytest.fixture(scope="module")
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


def test_graph_traversal_paths():
    """Verify that graph_query_service correctly traverses upstream topologies in FalkorDB."""
    paths, cypher = graph_query_service.traverse_upstream_paths("svc-checkout-web", max_depth=3)

    assert len(paths) >= 3, "Expected at least 3 distinct upstream dependency paths"
    assert "MATCH path = " in cypher

    # Verify critical payment path exists and is flagged critical
    payment_path = next(
        (p for p in paths if p.service_chain[-1] == "svc-payment-service"),
        None,
    )
    assert payment_path is not None, "Critical path to svc-payment-service missing"
    assert payment_path.is_critical_path is True
    assert payment_path.hop_count == 2
    assert payment_path.service_chain == [
        "svc-checkout-web",
        "svc-order-service",
        "svc-payment-service",
    ]

    # Verify recommendation path exists and is marked non-critical
    rec_path = next(
        (p for p in paths if p.service_chain[-1] == "svc-recommendation-service"),
        None,
    )
    assert rec_path is not None, "Path to svc-recommendation-service missing"
    assert rec_path.is_critical_path is False
    assert rec_path.hop_count == 1


def test_root_cause_ranking_against_ground_truth():
    """Verify that the investigation ranking correctly identifies the true culprit without prior knowledge."""
    # Retrieve evaluation benchmark
    gt = get_ground_truth("inc-2026-checkout-crash")

    investigation = investigation_service.investigate("inc-2026-checkout-crash")
    assert len(investigation.hypotheses) >= 2, "Expected at least 2 ranked hypotheses"

    top_hypothesis = investigation.hypotheses[0]

    # Evaluate against ground truth
    assert top_hypothesis.rank == 1
    assert top_hypothesis.entity_id == gt["true_root_cause"]["entity_id"]
    assert top_hypothesis.service_id == gt["true_root_cause"]["service_id"]
    assert top_hypothesis.score >= 0.85, f"Expected high confidence score >= 0.85, got {top_hypothesis.score}"
    assert top_hypothesis.confidence_level == "HIGH"

    # Explicit uncertainty assertion (Requirement 8)
    assert top_hypothesis.proven_causality is False, "Must not claim proven causality from correlation alone"


def test_distractor_and_competing_hypothesis_handling():
    """Verify that the engine properly demotes the misleading alert and non-critical distractor."""
    gt = get_ground_truth("inc-2026-checkout-crash")
    distractor_id = gt["distractors"][0] if isinstance(gt["distractors"][0], str) else gt["distractors"][0]["entity_id"]

    investigation = investigation_service.investigate("inc-2026-checkout-crash")

    distractor_hyp = next(
        (h for h in investigation.hypotheses if h.entity_id == distractor_id),
        None,
    )
    assert distractor_hyp is not None, f"Distractor {distractor_id} not found in hypotheses"

    top_hyp = investigation.hypotheses[0]

    # Distractor must be ranked strictly lower than the true root cause
    assert distractor_hyp.rank > top_hyp.rank
    assert distractor_hyp.score < top_hyp.score

    # Distractor must be flagged as a competing/misleading candidate
    assert distractor_hyp.is_distractor_or_competing is True
    assert distractor_hyp.distractor_reasoning is not None
    assert "non-critical" in distractor_hyp.distractor_reasoning.lower()


def test_evidence_provenance_and_corroboration():
    """Verify that hypotheses trace back to real Cypher queries, alerts, and log traces."""
    investigation = investigation_service.investigate("inc-2026-checkout-crash")

    # Assert Cypher audit trail is present
    assert len(investigation.cypher_query_provenance) >= 4
    for q in investigation.cypher_query_provenance:
        assert "MATCH" in q, f"Query provenance does not contain Cypher MATCH: {q}"

    top_hyp = investigation.hypotheses[0]
    # Check corroborating alerts
    assert len(top_hyp.corroborating_alerts) >= 1
    assert any(a.name == "DbConnectionPoolExhaustion" for a in top_hyp.corroborating_alerts)

    # Check corroborating logs with distributed trace ID
    assert len(top_hyp.corroborating_logs) >= 1
    fatal_log = next((l for l in top_hyp.corroborating_logs if l.level == "FATAL"), None)
    assert fatal_log is not None
    assert fatal_log.trace_id == "trc-checkout-881"


def test_ground_truth_isolation():
    """Verify architectural isolation: investigation service must NOT import or reference ground truth."""
    import app.services.investigation as inv_mod
    import app.graph.query as query_mod

    inv_source = inspect.getsource(inv_mod)
    query_source = inspect.getsource(query_mod)

    assert "ground_truth" not in inv_source, "Leak detected: investigation.py references ground_truth"
    assert "ground_truth" not in query_source, "Leak detected: query.py references ground_truth"
    assert "GROUND_TRUTH_DATASET" not in inv_source
    assert "GROUND_TRUTH_DATASET" not in query_source


def test_investigation_api_endpoints(client):
    """Verify the HTTP endpoints for listing and investigating incidents."""
    # 1. List incidents
    list_res = client.get("/api/incidents")
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert len(incidents) >= 1
    assert any(i["id"] == "inc-2026-checkout-crash" for i in incidents)

    # 2. Get incident investigation
    inv_res = client.get("/api/incidents/inc-2026-checkout-crash/investigation")
    assert inv_res.status_code == 200
    data = inv_res.json()

    assert data["incident_id"] == "inc-2026-checkout-crash"
    assert len(data["hypotheses"]) >= 2
    top = data["hypotheses"][0]
    assert top["entity_id"] == "dep-payment-v2.4.1"
    assert "relative_confidence_pct" in top
    assert top["relative_confidence_pct"] > 50.0
    assert "missing_evidence" in top
    assert isinstance(top["missing_evidence"], list)
    assert data["top_hypothesis_justification"] is not None
    assert "dep-payment-v2.4.1" in data["top_hypothesis_justification"]
    assert data["uncertainty"]["statement"] is not None


def test_invalid_incident_id_returns_422(client):
    """Verify 422 Unprocessable Entity when incident_id contains illegal characters or wrong length."""
    # Too short (< 3 chars)
    res_short = client.get("/api/incidents/a/investigation")
    assert res_short.status_code == 422

    # Illegal characters (spaces, special punctuation)
    res_bad_chars = client.get("/api/incidents/inc;DROP%20TABLE/investigation")
    assert res_bad_chars.status_code == 422


def test_out_of_bounds_window_ms_returns_422(client):
    """Verify 422 when window_ms is negative, zero, or exceeds 7 days."""
    # Negative or too small (< 60,000 ms)
    res_small = client.get("/api/incidents/inc-2026-checkout-crash/investigation?window_ms=500")
    assert res_small.status_code == 422

    # Excessively large (> 604,800,000 ms = 7 days)
    res_huge = client.get("/api/incidents/inc-2026-checkout-crash/investigation?window_ms=9999999999")
    assert res_huge.status_code == 422


def test_nonexistent_incident_returns_404(client):
    """Verify 404 response when querying an unknown incident."""
    res = client.get("/api/incidents/inc-unknown-9999/investigation")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_unavailable_database_handling():
    """Verify graceful handling when FalkorDB is unreachable."""
    from app.graph.client import FalkorDBClientManager

    # Create manager configured to unreachable port
    broken_manager = FalkorDBClientManager()
    status = broken_manager.check_connection(host="127.0.0.1", port=59999)

    assert status.connected is False
    assert "FalkorDB unreachable" in status.message
