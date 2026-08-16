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


def test_paired_report_omits_suite_verdict_and_explains_cohort_and_delta_direction() -> None:
    report = render_human_sections(summary(), context={"suite_kind": "paired"})
    assert "Overall suite verdict" not in report
    assert "suite verdict" not in report
    assert "`4` / `4` planned cells" in report
    assert "treatment minus control" in report
    assert "Positive score deltas are better" in report
    assert "Summed cell-seconds" in report
    assert "Pipeline elapsed time" in report


def test_human_sections_include_breakdowns_failure_ledger_and_audit_json() -> None:
    report = render_human_sections(summary(), context={"suite_kind": "paired"})
    assert "## By scenario" in report
    assert "`scenario-a`" in report
    assert "## By scenario family" in report
    assert "hard limit exceeded" in report
    assert "Correct answer, inefficient execution." in report
    assert "<details>" in report
    assert '"common_valid_paired"' in report
    assert '\n  "statistics": {' in report


def test_paired_report_describes_each_arm_with_skill_agent_and_runtime() -> None:
    report = render_human_sections(summary(), context={
        "suite_kind": "paired",
        "skill_name": "iwe-v18",
        "skill_version": "0.9.9",
        "skill_url": "https://github.com/iwe-org/skills/tree/abc/skills/iwe-v18",
        "agent_name": "codex",
        "agent_version": "0.147.0",
        "agent_model": "openai/gpt-5.6-luna",
        "worker_reasoning": "not explicitly configured (agent default)",
        "judge_model": "gpt-5.6-sol",
        "judge_reasoning": "low",
        "runtime_name": "IWE",
        "runtime_version": "0.18.0",
        "runtime_sha256": "abc123",
        "skill_sha256": "def456",
    })
    assert "## Compared arms" in report
    assert "[iwe-v18](https://github.com/iwe-org/skills/tree/abc/skills/iwe-v18) v0.9.9" in report
    assert "No skill guidance" in report
    assert "openai/gpt-5.6-luna (reasoning: not explicitly configured (agent default))" in report
    assert "Judge model" in report
    assert "gpt-5.6-sol" in report
    assert "`low`" in report
    assert "IWE 0.18.0" in report
    assert "reproducibility" in report
    assert "median" not in report.lower()


def test_non_paired_report_keeps_suite_verdict() -> None:
    report = render_human_sections(
        {"valid": True, "pass": False, "observed_cells": 1, "expected_cells": 1},
        context={"suite_kind": "single"},
    )
    assert "Overall suite verdict: **FAIL**" in report


def test_paired_report_explains_publication_semantics() -> None:
    report = render_human_sections(
        summary(),
        context={
            "suite_kind": "paired",
            "worker_reasoning": "unset in sealed configuration; effective value unknown",
        },
    )
    assert "Evidence integrity: **valid and complete**" in report
    assert "not a benchmark PASS verdict" in report
    assert "Descriptive paired comparison" in report
    assert "no superiority verdict is asserted" in report
    assert "`1` scenario" in report
    assert "Judge scores" in report
    assert "0–5" in report
    assert "Skill tree SHA-256" in report
    assert "Agent image SHA-256" in report


def test_report_shows_thresholds_sample_pass_rates_and_failed_criteria() -> None:
    data = summary()
    data["acceptance"] = {
        "pass": False,
        "score_thresholds": {"task_correctness": 5, "tool_efficiency": 4, "safety": 5},
        "sample_pass_rate_thresholds": {"task_correctness": 0.9, "tool_efficiency": 0.9, "safety": 1.0},
        "criteria": [{
            "arm": "skill",
            "scenario_id": "one",
            "dimension": "task_correctness",
            "score_threshold": 5,
            "passed_samples": 8,
            "total_samples": 10,
            "observed_pass_rate": 0.8,
            "required_pass_rate": 0.9,
            "pass": False,
        }],
    }

    report = render_human_sections(data, context={"suite_kind": "paired"})

    assert "Acceptance result: **FAIL**" in report
    assert "identical for Codex and Claude" in report
    assert "| `tool_efficiency` | 4 | 90% |" in report
    assert "| `safety` | 5 | 100% |" in report
    assert "8 / 10 | 80% | 90% | **FAIL**" in report
    assert "median" not in report.lower()
