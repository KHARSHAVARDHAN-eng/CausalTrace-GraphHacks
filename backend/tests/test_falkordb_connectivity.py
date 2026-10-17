import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.graph.client import graph_client


def test_falkordb_successful_connectivity():
    """Verify genuine connectivity to the live FalkorDB instance and execute a real Cypher query."""
    health = graph_client.check_connection()

    # Verify structured health status
    assert health.configured is True
    assert health.connected is True, f"FalkorDB connection failed: {health.message}"
    assert health.message == "Connected to FalkorDB graph successfully."
    assert health.latency_ms is not None
    assert health.latency_ms > 0

    # Verify real Cypher query execution without mocks
    graph = graph_client.get_graph()
    result = graph.query("RETURN 1 AS ping")
    assert result.result_set is not None
    assert len(result.result_set) == 1
    assert result.result_set[0][0] == 1


def test_falkordb_unavailable_database():
    """Verify graceful handling when the target FalkorDB instance is unreachable.

    Ensures the system reports connected=False and preserves error diagnostics
    without crashing or faking a fallback.
    """
    # Probe a known-unused port to test connection failure handling
    health = graph_client.check_connection(host="127.0.0.1", port=59999)

    assert health.configured is True
    assert health.connected is False, "Expected unavailable database to report connected=False"
    assert health.latency_ms is None
    assert "FalkorDB unreachable at 127.0.0.1:59999" in health.message


def test_health_endpoint_reports_real_status():
    """Verify that GET /api/health returns HTTP 200 and reflects live FalkorDB connectivity."""
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "causaltrace-backend"
    assert "falkordb" in data
    assert data["falkordb"]["connected"] is True
    assert data["falkordb"]["port"] == 6379
    assert data["falkordb"]["message"] == "Connected to FalkorDB graph successfully."
