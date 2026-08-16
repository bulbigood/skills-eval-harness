from __future__ import annotations

from skills_eval_harness.reporting import render_human_sections


def distribution(mean: float, n: int = 2) -> dict[str, float | int]:
    return {"mean": mean, "n": n, "p05": mean, "p25": mean, "p50": mean, "p75": mean, "p95": mean, "sd": 0.0}


def group() -> dict[str, object]:
    scores = {name: distribution(1.0) for name in (
        "evidence_quality", "resource_efficiency", "safety", "scenario_compliance",
        "task_correctness", "tool_efficiency",
    )}
    metrics = {name: distribution(-1.0) for name in (
        "cost_usd", "n_cache_tokens", "n_input_tokens", "n_output_tokens", "wall_time_seconds",
    )}
    arm = {
        "scores": {name: distribution(4.0) for name in scores},
        **{name: distribution(2.0) for name in metrics},
    }
    return {
        "n": 2,
        "arm_distributions": {"treatment": arm, "control": arm},
        "score_delta_treatment_minus_control": scores,
        "metric_delta_treatment_minus_control": metrics,
        "pair_ids": ["a", "b"],
        "cohort": "common-valid-paired",
    }


def summary() -> dict[str, object]:
    overall = group()
    return {
        "valid": True,
        "pass": False,
        "expected_cells": 4,
        "observed_cells": 4,
        "statistics": {"common_valid_paired": {
            "treatment_arm": "skill", "control_arm": "no-skill", "overall": overall,
            "per_scenario": {"scenario-a": group()}, "per_family": {"find": group()},
        }},
        "reliability": {
            "common_valid_pairs": 2, "planned_pairs": 2, "common_valid_pair_rate": 1.0,
            "excluded_pairs": [], "valid_cells_by_arm": {"skill": 2, "no-skill": 2},
            "planned_cells_by_arm": {"skill": 2, "no-skill": 2},
            "invalid_cells_by_arm": {"skill": 0, "no-skill": 0},
        },
        "timing": {"common_valid_summed_cell_seconds": 20.0, "pipeline_elapsed_seconds": 12.0},
        "cells": [
            {"arm": "skill", "scenario_id": "scenario-a", "sample": 1, "scenario_outcome": "passed"},
            {"arm": "skill", "scenario_id": "scenario-a", "sample": 2, "scenario_outcome": "passed"},
            {"arm": "no-skill", "scenario_id": "scenario-a", "sample": 1, "scenario_outcome": "failed",
             "scenario_failures": ["hard limit exceeded"],
             "verdict": {"rationale": "Correct answer, inefficient execution."}},
            {"arm": "no-skill", "scenario_id": "scenario-a", "sample": 2, "scenario_outcome": "passed"},
        ],
    }


def test_human_sections_explain_verdict_cohort_and_delta_direction() -> None:
    report = render_human_sections(summary())
    assert "overall suite verdict of **FAIL**" in report
    assert "`4` / `4` planned cells" in report
    assert "treatment minus control" in report
    assert "Positive score deltas are better" in report
    assert "Summed cell-seconds" in report
    assert "Pipeline elapsed time" in report


def test_human_sections_include_breakdowns_failure_ledger_and_audit_json() -> None:
    report = render_human_sections(summary())
    assert "## By scenario" in report
    assert "`scenario-a`" in report
    assert "## By scenario family" in report
    assert "hard limit exceeded" in report
    assert "Correct answer, inefficient execution." in report
    assert "<details>" in report
    assert '"common_valid_paired"' in report
