"""Reproducible Evaluation Benchmark for CausalTrace Investigation Engine.

Evaluates:
1. Top-1 Root-Cause Accuracy
2. Top-3 Root-Cause Recall
3. Misleading-Alert Demotion Rate (Robustness)
4. Abstention Behavior on Insufficient Evidence
5. Cypher Traversal Latency
"""

import os
import sys
import time
from typing import List, Dict, Any

# Ensure backend directory is in sys.path when running script directly
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.investigation import investigation_service
from app.evaluation.ground_truth import GROUND_TRUTH_DATASET, list_benchmark_incident_ids, get_ground_truth


def run_evaluation() -> Dict[str, Any]:
    """Execute evaluation benchmark across all synthetic incident scenarios."""
    incident_ids = list_benchmark_incident_ids()

    total_scenarios = len(incident_ids)
    culprit_scenarios = 0
    top_1_correct = 0
    top_3_correct = 0

    distractor_scenarios = 0
    distractor_success = 0

    abstention_scenarios = 0
    abstention_success = 0

    results_table = []
    latencies_ms = []

    print("\n" + "=" * 90)
    print(" CAUSALTRACE INVESTIGATION ENGINE — REPRODUCIBLE EVALUATION BENCHMARK")
    print("=" * 90)
    print(f"Total Scenarios Evaluated: {total_scenarios}\n")

    for idx, inc_id in enumerate(incident_ids, start=1):
        gt = get_ground_truth(inc_id)
        expected_behavior = gt["expected_behavior"]
        must_abstain = gt.get("must_abstain", False)

        t0 = time.perf_counter()
        inv = investigation_service.investigate(inc_id)
        latency = (time.perf_counter() - t0) * 1000
        latencies_ms.append(latency)

        top_hyp = inv.hypotheses[0] if inv.hypotheses else None
        top_entity = top_hyp.entity_id if top_hyp else "NONE"
        top_score = top_hyp.score if top_hyp else 0.0
        confidence = top_hyp.confidence_level if top_hyp else "NONE"

        is_top1 = False
        is_top3 = False

        if not must_abstain and gt.get("true_root_cause"):
            culprit_scenarios += 1
            expected_entity = gt["true_root_cause"]["entity_id"]

            if top_entity == expected_entity:
                top_1_correct += 1
                is_top1 = True

            hyp_ids = [h.entity_id for h in inv.hypotheses[:3]]
            if expected_entity in hyp_ids:
                top_3_correct += 1
                is_top3 = True

            # Distractor check
            if gt.get("distractors"):
                distractor_scenarios += 1
                distractor_entities = set(gt["distractors"])
                # True culprit must score strictly higher than any distractor
                culprit_score = next((h.score for h in inv.hypotheses if h.entity_id == expected_entity), 0.0)
                max_distractor_score = max((h.score for h in inv.hypotheses if h.entity_id in distractor_entities), default=0.0)

                if culprit_score > max_distractor_score:
                    distractor_success += 1

            status_str = "PASS (Top-1)" if is_top1 else ("PASS (Top-3)" if is_top3 else "FAIL")
        else:
            # Abstention / Insufficient Evidence Scenario
            abstention_scenarios += 1
            expected_entity = "ABSTAIN"
            has_abstained = (inv.has_sufficient_evidence is False) or (confidence == "LOW")
            if has_abstained:
                abstention_success += 1
                status_str = "PASS (Abstained)"
            else:
                status_str = "FAIL (False Positive)"

        results_table.append({
            "idx": idx,
            "id": inc_id,
            "expected": expected_entity,
            "found": top_entity,
            "score": top_score,
            "confidence": confidence,
            "status": status_str,
            "latency_ms": round(latency, 2),
        })

    # Print Table
    header = f"{'#':<3} | {'Incident ID':<42} | {'Expected':<22} | {'Top-1 Found':<22} | {'Score':<6} | {'Status':<16} | {'Latency':<8}"
    print(header)
    print("-" * len(header))
    for r in results_table:
        print(f"{r['idx']:<3} | {r['id']:<42} | {r['expected']:<22} | {r['found']:<22} | {r['score']:<6.3f} | {r['status']:<16} | {r['latency_ms']:<6.1f}ms")

    # Metrics computation
    top1_acc = (top_1_correct / culprit_scenarios * 100) if culprit_scenarios else 0.0
    top3_rec = (top_3_correct / culprit_scenarios * 100) if culprit_scenarios else 0.0
    distractor_acc = (distractor_success / distractor_scenarios * 100) if distractor_scenarios else 0.0
    abstention_rate = (abstention_success / abstention_scenarios * 100) if abstention_scenarios else 0.0
    mean_latency = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0

    cold_start_ms = latencies_ms[0] if latencies_ms else 0.0
    warm_latencies = latencies_ms[1:] if len(latencies_ms) > 1 else latencies_ms
    mean_warm_latency = sum(warm_latencies) / len(warm_latencies) if warm_latencies else 0.0
    min_warm = min(warm_latencies) if warm_latencies else 0.0
    max_warm = max(warm_latencies) if warm_latencies else 0.0

    print("\n" + "=" * 90)
    print(" SUMMARY BENCHMARK METRICS (Synthetic Suite: 10 Curated Scenarios)")
    print("=" * 90)
    print(f"Top-1 Root-Cause Accuracy:           {top1_acc:6.1f}%  ({top_1_correct}/{culprit_scenarios} scenarios)")
    print(f"Top-3 Root-Cause Recall:             {top3_rec:6.1f}%  ({top_3_correct}/{culprit_scenarios} scenarios)")
    print(f"Misleading-Alert Demotion Rate:      {distractor_acc:6.1f}%  ({distractor_success}/{distractor_scenarios} distractor scenarios)")
    print(f"Insufficient Evidence Abstention:    {abstention_rate:6.1f}%  ({abstention_success}/{abstention_scenarios} ambiguous/gap scenarios)")
    print(f"Scenario 1 Measured Latency:         {cold_start_ms:6.1f} ms  (First scenario execution)")
    print(f"Warm Traversal Latency (Scenarios 2-10): {mean_warm_latency:4.1f} ms mean ({min_warm:.1f}–{max_warm:.1f} ms range)")
    print(f"Overall Mean Traversal Latency:      {mean_latency:6.1f} ms  (All 10 scenarios)")
    print("=" * 90 + "\n")

    return {
        "total_scenarios": total_scenarios,
        "top_1_accuracy_pct": top1_acc,
        "top_3_recall_pct": top3_rec,
        "misleading_alert_demotion_pct": distractor_acc,
        "abstention_rate_pct": abstention_rate,
        "mean_latency_ms": mean_latency,
        "cold_start_latency_ms": cold_start_ms,
        "mean_warm_latency_ms": mean_warm_latency,
        "min_warm_latency_ms": min_warm,
        "max_warm_latency_ms": max_warm,
        "results": results_table,
    }


if __name__ == "__main__":
    report = run_evaluation()
    # Check assertions for automated execution
    if report["top_1_accuracy_pct"] < 90.0 or report["abstention_rate_pct"] < 100.0:
        print("ERROR: Benchmark did not meet quality thresholds.")
        sys.exit(1)
    print("All benchmark quality assertions PASSED.")
    sys.exit(0)
