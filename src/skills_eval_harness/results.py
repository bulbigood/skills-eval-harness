"""Parse Harbor v0.21 jobs and derive fail-closed run summaries."""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

from harbor.models.job.result import JobResult, TrialResult

from .hashing import atomic_write_json, sha256_file
from .judge import EvidenceKind


EVIDENCE_KINDS: dict[str, EvidenceKind] = {"trajectory": "response", "workspace": "workspace", "mechanical": "oracle", "stdout": "telemetry", "stderr": "telemetry"}


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


def trial_evidence(job_dir: Path, trial_name: str) -> list[tuple[EvidenceKind, str]]:
    root = job_dir / trial_name
    paths = {
        "trajectory": root / "agent/trajectory.json",
        "workspace": root / "verifier/workspace-manifest.json",
        "mechanical": root / "verifier/mechanical.json",
        "stdout": root / "verifier/test-stdout.txt",
        "stderr": root / "verifier/test-stderr.txt",
    }
    evidence: list[tuple[EvidenceKind, str]] = [("infrastructure", "Harbor separate verifier returned infrastructure=1")]
    for name, path in paths.items():
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            evidence.append((EVIDENCE_KINDS[name], f"{name} sha256={sha256_file(path)}\n{text[:8000]}"))
    if not any(kind == "response" for kind, _ in evidence):
        raise ValueError(f"trial {trial_name} has no trajectory evidence")
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
        "n": len(values), "mean": statistics.fmean(values), "sd": statistics.stdev(values) if len(values) > 1 else None,
        "p05": _percentile(values, 0.05), "p25": _percentile(values, 0.25), "p50": _percentile(values, 0.50),
        "p75": _percentile(values, 0.75), "p95": _percentile(values, 0.95),
    }


def _group_statistics(cells: list[dict]) -> dict[str, object]:
    dimensions = sorted({name for cell in cells for name in cell.get("scores", {})})
    return {
        "scores": {name: distribution([float(cell["scores"][name]) for cell in cells if name in cell.get("scores", {})]) for name in dimensions},
        "wall_time_seconds": distribution([float(cell["wall_time_seconds"]) for cell in cells if cell.get("wall_time_seconds") is not None]),
    }


def summarize_cells(cells: list[dict], expected: int, *, pipeline_elapsed_seconds: float | None = None) -> dict:
    identities = {(cell["arm"], cell["scenario_id"], cell["sample"]) for cell in cells}
    if len(cells) != expected or len(identities) != expected:
        raise ValueError("missing or duplicate cells")
    valid = all(cell.get("valid") is True for cell in cells)
    passed = valid and all(cell.get("required_pass", cell.get("pass")) is True for cell in cells)
    by_scenario = {key: _group_statistics([cell for cell in cells if cell["scenario_id"] == key]) for key in sorted({cell["scenario_id"] for cell in cells})}
    by_family = {key: _group_statistics([cell for cell in cells if cell.get("family") == key]) for key in sorted({cell.get("family", "unknown") for cell in cells})}
    paired: dict[str, object] = {}
    arms = sorted({cell["arm"] for cell in cells})
    if len(arms) == 2:
        left = {(cell["scenario_id"], cell["sample"]): cell for cell in cells if cell["arm"] == arms[0] and cell.get("valid")}
        right = {(cell["scenario_id"], cell["sample"]): cell for cell in cells if cell["arm"] == arms[1] and cell.get("valid")}
        keys = sorted(set(left) & set(right))
        dimensions = sorted({name for key in keys for name in left[key].get("scores", {}) if name in right[key].get("scores", {})})
        paired = {
            "arms": [arms[0], arms[1]], "n": len(keys),
            "score_delta_right_minus_left": {name: distribution([float(right[key]["scores"][name] - left[key]["scores"][name]) for key in keys]) for name in dimensions},
            "wall_time_delta_right_minus_left": distribution([float(right[key]["wall_time_seconds"] - left[key]["wall_time_seconds"]) for key in keys if right[key].get("wall_time_seconds") is not None and left[key].get("wall_time_seconds") is not None]),
        }
    cell_seconds = sum(float(cell.get("wall_time_seconds") or 0.0) for cell in cells if cell.get("valid"))
    return {
        "schema_version": 1, "expected_cells": expected, "observed_cells": len(cells), "valid": valid, "pass": passed,
        "statistics": {"overall": _group_statistics(cells), "per_scenario": by_scenario, "per_family": by_family, "paired": paired},
        "timing": {"summed_cell_seconds": cell_seconds, "pipeline_elapsed_seconds": pipeline_elapsed_seconds}, "cells": cells,
    }


def write_summary(path: Path, cells: list[dict], expected: int, *, pipeline_elapsed_seconds: float | None = None) -> dict:
    summary = summarize_cells(cells, expected, pipeline_elapsed_seconds=pipeline_elapsed_seconds)
    atomic_write_json(path, summary)
    return summary
