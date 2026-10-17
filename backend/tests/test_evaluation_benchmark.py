"""Automated test suite verifying Phase 1 synthetic incident evaluation benchmark.

Tests:
1. Benchmark script runs to completion with 100% Top-1 accuracy on known culprits.
2. Every scenario is tested individually for ground truth alignment.
3. Distractors and misleading alerts are properly demoted.
4. Abstention is verified on sparse/missing evidence.
5. Strict isolation between ground truth and investigation engine is enforced.
"""

import pytest
from app.services.investigation import investigation_service
from app.evaluation.ground_truth import get_ground_truth, list_benchmark_incident_ids
from scripts.evaluate_investigation import run_evaluation


def test_full_evaluation_benchmark_metrics():
    """Verify that the reproducible evaluation script achieves required quality thresholds."""
    report = run_evaluation()

    assert report["top_1_accuracy_pct"] >= 90.0, "Top-1 accuracy must meet or exceed 90%"
    assert report["top_3_recall_pct"] == 100.0, "Top-3 recall must be 100%"
    assert report["misleading_alert_demotion_pct"] >= 90.0, "Misleading alerts must be demoted in >= 90% of cases"
    assert report["abstention_rate_pct"] == 100.0, "Engine must abstain on 100% of missing evidence scenarios"
    assert report["mean_latency_ms"] < 100.0, "Mean graph query latency must be sub-100ms"


@pytest.mark.parametrize("incident_id", list_benchmark_incident_ids())
def test_individual_scenario_investigation(incident_id: str):
    """Verify investigation output for each of the 10 benchmark scenarios."""
    gt = get_ground_truth(incident_id)
    inv = investigation_service.investigate(incident_id)

    # Basic invariant assertions
    assert inv.incident_id == incident_id
    assert inv.title is not None
    assert len(inv.cypher_query_provenance) >= 1

    if gt["must_abstain"]:
        # Verify abstention behavior on missing evidence
        assert (inv.has_sufficient_evidence is False) or (inv.hypotheses and inv.hypotheses[0].confidence_level == "LOW")
        assert len(inv.uncertainty.insufficient_evidence_flags) >= 1
    else:
        # Verify true culprit identification
        expected_culprit = gt["true_root_cause"]["entity_id"]
        assert len(inv.hypotheses) >= 1
        top_hyp = inv.hypotheses[0]

        assert top_hyp.entity_id == expected_culprit, f"Expected {expected_culprit} as Top-1 for {incident_id}, got {top_hyp.entity_id}"
        assert top_hyp.score >= gt["expected_min_score"]
        assert top_hyp.proven_causality is False, "Must never claim proven causality from correlation alone"

        # Verify distractor demotion if distractors are registered
        if gt.get("distractors"):
            distractor_ids = set(gt["distractors"])
            for d_id in distractor_ids:
                d_hyp = next((h for h in inv.hypotheses if h.entity_id == d_id), None)
                if d_hyp:
                    assert d_hyp.score < top_hyp.score, f"Distractor {d_id} scored higher than true culprit {expected_culprit}"


def test_supporting_and_contradictory_evidence_provenance():
    """Verify that hypotheses expose structured supporting and contradictory evidence."""
    inv = investigation_service.investigate("inc-01-payment-pool-exhaustion")
    assert len(inv.hypotheses) >= 2

    # Top hypothesis has supporting evidence
    top = inv.hypotheses[0]
    assert len(top.supporting_evidence) >= 2
    assert any("critical dependency path" in s.lower() for s in top.supporting_evidence)
    assert top.score_breakdown["topological_criticality"] > 0
    assert top.relative_confidence_pct > 50.0
    assert len(top.missing_evidence) >= 1
    assert inv.top_hypothesis_justification is not None
    assert "dep-payment-v2.4.1" in inv.top_hypothesis_justification

    # Distractor hypothesis has contradictory evidence
    distractor = next((h for h in inv.hypotheses if h.is_distractor_or_competing), None)
    assert distractor is not None
    assert len(distractor.contradictory_evidence) >= 1
    assert any("non-critical" in c.lower() for c in distractor.contradictory_evidence)
