"""Parse Harbor v0.21 jobs and derive fail-closed run summaries."""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

from harbor.models.job.result import JobResult, TrialResult

from .hashing import atomic_write_json, sha256_file
from .judge import EvidenceKind


EVIDENCE_KINDS: dict[str, EvidenceKind] = {
    "workspace": "workspace",
    "mechanical": "oracle",
    "stdout": "telemetry",
    "stderr": "telemetry",
}


def load_job(job_dir: Path) -> JobResult:
    job = JobResult.model_validate_json((job_dir / "result.json").read_text(encoding="utf-8"))
    trials = [TrialResult.model_validate_json(path.read_text(encoding="utf-8")) for path in sorted(job_dir.glob("*/result.json"))]
    return job.model_copy(update={"trial_results": trials})


def validate_job(job_dir: Path, *, expected_trials: int) -> JobResult:
    lock = json.loads((job_dir / "lock.json").read_text(encoding="utf-8"))
    if lock.get("schema_version") != 3 or lock.get("harbor", {}).get("version") != "0.21.0":
        raise ValueError("invalid or unexpected Harbor lock")
    if len(lock.get("trials", [])) != expected_trials:
        raise ValueError("incomplete Harbor lock")
    job = load_job(job_dir)
    if job.n_total_trials != expected_trials or len(job.trial_results) != expected_trials:
        raise ValueError("incomplete Harbor job")
    if job.stats.n_errored_trials or job.stats.n_cancelled_trials or job.finished_at is None:
        raise ValueError("Harbor job contains failed, cancelled, or unfinished trials")
    for trial in job.trial_results:
        if trial.exception_info is not None:
            raise ValueError(f"trial {trial.trial_name} failed")
        if trial.verifier_environment_mode != "separate":
            raise ValueError(f"trial {trial.trial_name} did not use a separate verifier sandbox")
        rewards = trial.verifier_result.rewards if trial.verifier_result else None
        if not rewards or rewards.get("infrastructure") != 1:
            raise ValueError(f"trial {trial.trial_name} failed deterministic verification")
    return job


def _final_response(path: Path) -> str:
    document = json.loads(path.read_text(encoding="utf-8"))
    steps = document.get("steps") if isinstance(document, dict) else None
    if not isinstance(steps, list):
        raise ValueError("trajectory is not a valid ATIF document")
    messages: list[str] = [
        step["message"]
        for step in steps
        if isinstance(step, dict) and step.get("source") == "agent" and isinstance(step.get("message"), str) and step["message"].strip()
    ]
    if not messages:
        raise ValueError("trajectory has no final assistant response")
    return messages[-1]


def trial_evidence(job_dir: Path, trial_name: str) -> list[tuple[EvidenceKind, str]]:
    root = job_dir / trial_name
    trajectory = root / "agent/trajectory.json"
    if not trajectory.is_file():
        raise ValueError(f"trial {trial_name} has no trajectory evidence")
    evidence: list[tuple[EvidenceKind, str]] = [
        ("infrastructure", "Harbor separate verifier returned infrastructure=1"),
        ("response", f"trajectory sha256={sha256_file(trajectory)}\nfinal assistant response:\n{_final_response(trajectory)}"),
    ]
    paths = {
        "workspace": root / "verifier/workspace-manifest.json",
        "mechanical": root / "verifier/mechanical.json",
        "stdout": root / "verifier/test-stdout.txt",
        "stderr": root / "verifier/test-stderr.txt",
    }
    for name, path in paths.items():
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            evidence.append((EVIDENCE_KINDS[name], f"{name} sha256={sha256_file(path)}\n{text[:8000]}"))
    return evidence


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def distribution(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "mean": None, "sd": None, "p05": None, "p25": None, "p50": None, "p75": None, "p95": None}
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "sd": statistics.stdev(values) if len(values) > 1 else None,
        "p05": _percentile(values, 0.05),
        "p25": _percentile(values, 0.25),
        "p50": _percentile(values, 0.50),
        "p75": _percentile(values, 0.75),
        "p95": _percentile(values, 0.95),
    }


def _group_statistics(cells: list[dict]) -> dict[str, object]:
    valid_cells = [cell for cell in cells if cell.get("valid") is True]
    dimension_sets = {frozenset(cell.get("scores", {})) for cell in valid_cells}
    if len(dimension_sets) > 1:
        raise ValueError("valid cells in one cohort have inconsistent score dimensions")
    dimensions = sorted(next(iter(dimension_sets), frozenset()))
    return {
        "scores": {name: distribution([float(cell["scores"][name]) for cell in valid_cells]) for name in dimensions},
        "wall_time_seconds": distribution([float(cell["wall_time_seconds"]) for cell in valid_cells if cell.get("wall_time_seconds") is not None]),
    }


def _arm_groups(cells: list[dict], arms: list[str]) -> dict[str, object]:
    return {arm: _group_statistics([cell for cell in cells if cell["arm"] == arm]) for arm in arms}


def summarize_cells(
    cells: list[dict],
    expected: int,
    *,
    control_arm: str | None = None,
    treatment_arm: str | None = None,
    pipeline_elapsed_seconds: float | None = None,
) -> dict:
    if expected < 1:
        raise ValueError("expected cell count must be positive")
    identities = {(cell["arm"], cell["scenario_id"], cell["sample"]) for cell in cells}
    if len(cells) != expected or len(identities) != expected:
        raise ValueError("missing or duplicate cells")
    arms = sorted({cell["arm"] for cell in cells})
    if len(arms) == 2 and ({control_arm, treatment_arm} != set(arms) or control_arm == treatment_arm):
        raise ValueError("paired summaries require explicit control and treatment arms")
    valid = all(cell.get("valid") is True for cell in cells)
    passed = valid and all(cell.get("required_pass", cell.get("pass")) is True for cell in cells)
    scenarios = sorted({cell["scenario_id"] for cell in cells})
    families = sorted({cell.get("family", "unknown") for cell in cells})
    per_scenario = {key: _arm_groups([cell for cell in cells if cell["scenario_id"] == key], arms) for key in scenarios}
    per_family = {key: _arm_groups([cell for cell in cells if cell.get("family", "unknown") == key], arms) for key in families}
    paired: dict[str, object] = {}
    excluded_pairs: list[dict[str, object]] = []
    if len(arms) == 2:
        control = {(cell["scenario_id"], cell["sample"]): cell for cell in cells if cell["arm"] == control_arm}
        treatment = {(cell["scenario_id"], cell["sample"]): cell for cell in cells if cell["arm"] == treatment_arm}
        planned_keys = sorted(set(control) | set(treatment))
        keys = [key for key in planned_keys if control.get(key, {}).get("valid") is True and treatment.get(key, {}).get("valid") is True]
        for scenario_id, sample in planned_keys:
            reasons = []
            for label, cohort in ((control_arm, control), (treatment_arm, treatment)):
                cell = cohort.get((scenario_id, sample))
                if cell is None:
                    reasons.append(f"{label}:missing")
                elif cell.get("valid") is not True:
                    reasons.append(f"{label}:{cell.get('invalid_reason', 'invalid')}")
            if reasons:
                excluded_pairs.append({"scenario_id": scenario_id, "sample": sample, "reasons": reasons})
        dimensions = sorted(set.intersection(*(set(control[key].get("scores", {})) & set(treatment[key].get("scores", {})) for key in keys)) if keys else set())
        paired = {
            "control_arm": control_arm,
            "treatment_arm": treatment_arm,
            "n": len(keys),
            "pair_ids": [{"scenario_id": key[0], "sample": key[1]} for key in keys],
            "score_delta_treatment_minus_control": {
                name: distribution([float(treatment[key]["scores"][name] - control[key]["scores"][name]) for key in keys])
                for name in dimensions
            },
            "wall_time_delta_treatment_minus_control": distribution([
                float(treatment[key]["wall_time_seconds"] - control[key]["wall_time_seconds"])
                for key in keys
                if treatment[key].get("wall_time_seconds") is not None and control[key].get("wall_time_seconds") is not None
            ]),
        }
    valid_by_arm = {arm: sum(cell.get("valid") is True for cell in cells if cell["arm"] == arm) for arm in arms}
    invalid_by_arm = {arm: sum(cell.get("valid") is not True for cell in cells if cell["arm"] == arm) for arm in arms}
    cell_seconds = sum(float(cell.get("wall_time_seconds") or 0.0) for cell in cells if cell.get("valid") is True)
    return {
        "schema_version": 2,
        "expected_cells": expected,
        "observed_cells": len(cells),
        "valid": valid,
        "pass": passed,
        "reliability": {
            "valid_cells_by_arm": valid_by_arm,
            "invalid_cells_by_arm": invalid_by_arm,
            "excluded_pairs": excluded_pairs,
        },
        "statistics": {
            "overall": _arm_groups(cells, arms),
            "per_scenario": per_scenario,
            "per_family": per_family,
            "paired": paired,
        },
        "timing": {"summed_cell_seconds": cell_seconds, "pipeline_elapsed_seconds": pipeline_elapsed_seconds},
        "cells": cells,
    }


def write_summary(
    path: Path,
    cells: list[dict],
    expected: int,
    *,
    control_arm: str | None = None,
    treatment_arm: str | None = None,
    pipeline_elapsed_seconds: float | None = None,
) -> dict:
    summary = summarize_cells(
        cells,
        expected,
        control_arm=control_arm,
        treatment_arm=treatment_arm,
        pipeline_elapsed_seconds=pipeline_elapsed_seconds,
    )
    atomic_write_json(path, summary)
    return summary
