"""Parse Harbor v0.21 jobs and derive fail-closed run summaries."""
from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Literal

from harbor.models.job.result import JobResult, TrialResult
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .hashing import atomic_write_json, sha256_file
from .judge import DIMENSIONS, Evidence, EvidenceKind, JudgeVerdict


EVIDENCE_KINDS: dict[str, EvidenceKind] = {
    "oracle": "oracle",
    "workspace": "workspace",
    "mechanical": "telemetry",
    "stdout": "telemetry",
    "stderr": "telemetry",
}
INVALID_REASONS = {
    "harbor_process_failed",
    "secret_exposure_redacted",
    "harbor_or_verifier_validation_failed",
    "trial_exception",
    "deterministic_verifier_failed",
    "judge_validation_failed",
}


class JudgeMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    role: Literal["system", "user"]
    content: str = Field(min_length=1)


class CellRecord(BaseModel):
    """Strict terminal record for one planned arm/scenario/sample identity."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, strict=True)
    arm: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    family: str = Field(min_length=1)
    sample: int = Field(ge=1)
    valid: bool
    pass_: bool = Field(alias="pass")
    required_pass: bool
    invalid_reason: str | None = None
    scores: dict[str, float] = Field(default_factory=dict)
    wall_time_seconds: float | None = Field(default=None, ge=0)
    n_input_tokens: int | None = Field(default=None, ge=0)
    n_cache_tokens: int | None = Field(default=None, ge=0)
    n_output_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    evidence: list[Evidence] = Field(default_factory=list)
    judge_messages: list[JudgeMessage] = Field(default_factory=list)
    verdict: JudgeVerdict | None = None

    @field_validator("scores")
    @classmethod
    def validate_scores(cls, scores: dict[str, float]) -> dict[str, float]:
        if any(not math.isfinite(value) or not 0 <= value <= 5 for value in scores.values()):
            raise ValueError("scores must be finite values in [0, 5]")
        return scores

    @model_validator(mode="after")
    def terminal_contract(self) -> "CellRecord":
        if not set(self.scores).issubset(DIMENSIONS):
            raise ValueError("cell contains unknown score dimensions")
        if self.valid:
            required = (
                bool(self.scores)
                and self.invalid_reason is None
                and self.wall_time_seconds is not None
                and self.n_input_tokens is not None
                and self.n_cache_tokens is not None
                and self.n_output_tokens is not None
                and self.cost_usd is not None
                and bool(self.evidence)
                and len(self.judge_messages) == 2
                and self.verdict is not None
            )
            if not required:
                raise ValueError("valid cell omits scores, metrics, judge inputs, or verdict")
        elif self.pass_ or self.required_pass or self.invalid_reason not in INVALID_REASONS or self.scores:
            raise ValueError("invalid cell must be terminal, failing, reasoned, and unscored")
        return self


def load_job(job_dir: Path) -> JobResult:
    job = JobResult.model_validate_json((job_dir / "result.json").read_text(encoding="utf-8"))
    trials = [TrialResult.model_validate_json(path.read_text(encoding="utf-8")) for path in sorted(job_dir.glob("*/result.json"))]
    return job.model_copy(update={"trial_results": trials})


def validate_job(
    job_dir: Path,
    *,
    expected_trials: int,
    require_mechanical_success: bool = True,
    allow_failed_trials: bool = False,
) -> JobResult:
    lock = json.loads((job_dir / "lock.json").read_text(encoding="utf-8"))
    if lock.get("schema_version") != 3 or lock.get("harbor") != {"version": "0.21.0", "is_editable": False}:
        raise ValueError("invalid or unexpected Harbor lock")
    if len(lock.get("trials", [])) != expected_trials:
        raise ValueError("incomplete Harbor lock")
    job = load_job(job_dir)
    if job.n_total_trials != expected_trials or len(job.trial_results) != expected_trials:
        raise ValueError("incomplete Harbor job")
    if job.finished_at is None or (
        not allow_failed_trials and (job.stats.n_errored_trials or job.stats.n_cancelled_trials)
    ):
        raise ValueError("Harbor job contains failed, cancelled, or unfinished trials")
    for trial in job.trial_results:
        if trial.exception_info is not None:
            if allow_failed_trials:
                continue
            raise ValueError(f"trial {trial.trial_name} failed")
        if trial.verifier_environment_mode != "separate":
            raise ValueError(f"trial {trial.trial_name} did not use a separate verifier sandbox")
        rewards = trial.verifier_result.rewards if trial.verifier_result else None
        if require_mechanical_success and (not rewards or rewards.get("infrastructure") != 1):
            raise ValueError(f"trial {trial.trial_name} failed deterministic verification")
    return job


def trial_mechanical_success(trial: TrialResult) -> bool:
    rewards = trial.verifier_result.rewards if trial.verifier_result else None
    return bool(rewards and rewards.get("infrastructure") == 1)


def _final_response(path: Path) -> str:
    document = json.loads(path.read_text(encoding="utf-8"))
    steps = document.get("steps") if isinstance(document, dict) else None
    if not isinstance(steps, list):
        raise ValueError("trajectory is not a valid ATIF document")
    messages = [
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
        "oracle": root / "verifier/oracle.json",
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
    if any(not math.isfinite(value) for value in values):
        raise ValueError("statistics require finite observations")
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


def _group_statistics(cells: list[dict], *, cohort: str = "available-valid") -> dict[str, object]:
    valid = [cell for cell in cells if cell["valid"]]
    dimension_sets = {frozenset(cell["scores"]) for cell in valid}
    if len(dimension_sets) > 1:
        raise ValueError("valid cells in one arm cohort have inconsistent score dimensions")
    dimensions = sorted(next(iter(dimension_sets), frozenset()))
    return {
        "cohort": cohort,
        "scores": {name: distribution([cell["scores"][name] for cell in valid]) for name in dimensions},
        "wall_time_seconds": distribution([cell["wall_time_seconds"] for cell in valid]),
        "n_input_tokens": distribution([float(cell["n_input_tokens"]) for cell in valid]),
        "n_cache_tokens": distribution([float(cell["n_cache_tokens"]) for cell in valid]),
        "n_output_tokens": distribution([float(cell["n_output_tokens"]) for cell in valid]),
        "cost_usd": distribution([cell["cost_usd"] for cell in valid]),
    }


def _arm_groups(cells: list[dict], arms: list[str]) -> dict[str, object]:
    return {arm: _group_statistics([cell for cell in cells if cell["arm"] == arm]) for arm in arms}


def _paired_statistics(
    control: dict[tuple[str, int], dict],
    treatment: dict[tuple[str, int], dict],
    keys: list[tuple[str, int]],
) -> dict[str, object]:
    common = [key for key in keys if control[key]["valid"] and treatment[key]["valid"]]
    dimensions = sorted(
        set.intersection(*(set(control[key]["scores"]) & set(treatment[key]["scores"]) for key in common))
        if common else set()
    )
    result: dict[str, object] = {
        "cohort": "common-valid",
        "n": len(common),
        "pair_ids": [{"scenario_id": scenario, "sample": sample} for scenario, sample in common],
        "arm_distributions": {
            "control": _group_statistics([control[key] for key in common], cohort="common-valid"),
            "treatment": _group_statistics([treatment[key] for key in common], cohort="common-valid"),
        },
        "score_delta_treatment_minus_control": {
            name: distribution([treatment[key]["scores"][name] - control[key]["scores"][name] for key in common])
            for name in dimensions
        },
    }
    result["metric_delta_treatment_minus_control"] = {
        field: distribution([float(treatment[key][field] - control[key][field]) for key in common])
        for field in ("wall_time_seconds", "n_input_tokens", "n_cache_tokens", "n_output_tokens", "cost_usd")
    }
    return result


def summarize_cells(
    cells: list[dict],
    expected_identities: set[tuple[str, str, int]],
    *,
    expected_families: dict[str, str],
    control_arm: str | None = None,
    treatment_arm: str | None = None,
    pipeline_elapsed_seconds: float | None = None,
    run_purpose: str = "diagnostic",
    samples_per_identity: int | None = None,
    preregistered_samples: int | None = None,
) -> dict:
    if not expected_identities:
        raise ValueError("expected identity matrix must not be empty")
    if pipeline_elapsed_seconds is not None and (
        not math.isfinite(pipeline_elapsed_seconds) or pipeline_elapsed_seconds < 0
    ):
        raise ValueError("pipeline elapsed seconds must be finite and non-negative")
    normalized = sorted(
        (CellRecord.model_validate(cell).model_dump(mode="json", by_alias=True) for cell in cells),
        key=lambda cell: (cell["scenario_id"], cell["sample"], cell["arm"]),
    )
    identities = {(cell["arm"], cell["scenario_id"], cell["sample"]) for cell in normalized}
    if len(normalized) != len(identities):
        raise ValueError("cell identity matrix contains duplicates")
    if identities != expected_identities:
        missing = sorted(expected_identities - identities)
        unexpected = sorted(identities - expected_identities)
        raise ValueError(f"cell identity matrix mismatch: missing={missing}, unexpected={unexpected}")
    for cell in normalized:
        if cell["family"] != expected_families.get(cell["scenario_id"]):
            raise ValueError("cell family does not match the sealed scenario catalog")
    arms = sorted({identity[0] for identity in expected_identities})
    paired_run = len(arms) == 2
    if paired_run and ({control_arm, treatment_arm} != set(arms) or control_arm == treatment_arm):
        raise ValueError("paired summaries require explicit control and treatment arms")
    if not paired_run and (control_arm is not None or treatment_arm is not None):
        raise ValueError("single-arm summaries must not declare paired roles")

    valid = all(cell["valid"] for cell in normalized)
    passed = valid and all(cell["required_pass"] for cell in normalized)
    scenarios = sorted({identity[1] for identity in expected_identities})
    families = sorted({cell["family"] for cell in normalized})
    per_scenario = {key: _arm_groups([cell for cell in normalized if cell["scenario_id"] == key], arms) for key in scenarios}
    per_family = {key: _arm_groups([cell for cell in normalized if cell["family"] == key], arms) for key in families}

    valid_by_arm = {arm: sum(cell["valid"] for cell in normalized if cell["arm"] == arm) for arm in arms}
    invalid_by_arm = {arm: sum(not cell["valid"] for cell in normalized if cell["arm"] == arm) for arm in arms}
    reasons_by_arm = {
        arm: dict(sorted(Counter(
            cell["invalid_reason"] for cell in normalized if cell["arm"] == arm and not cell["valid"]
        ).items()))
        for arm in arms
    }
    planned_by_arm = {arm: sum(identity[0] == arm for identity in expected_identities) for arm in arms}
    paired: dict[str, object] = {}
    excluded_pairs: list[dict[str, object]] = []
    common_valid_keys: list[tuple[str, int]] = []
    if paired_run:
        control = {(cell["scenario_id"], cell["sample"]): cell for cell in normalized if cell["arm"] == control_arm}
        treatment = {(cell["scenario_id"], cell["sample"]): cell for cell in normalized if cell["arm"] == treatment_arm}
        planned_keys = sorted({(scenario, sample) for _, scenario, sample in expected_identities})
        common_valid_keys = [key for key in planned_keys if control[key]["valid"] and treatment[key]["valid"]]
        for scenario_id, sample in planned_keys:
            reasons = []
            for label, cohort in ((control_arm, control), (treatment_arm, treatment)):
                cell = cohort[(scenario_id, sample)]
                if not cell["valid"]:
                    reasons.append(f"{label}:{cell['invalid_reason']}")
            if reasons:
                excluded_pairs.append({"scenario_id": scenario_id, "sample": sample, "reasons": reasons})
        paired = {
            "control_arm": control_arm,
            "treatment_arm": treatment_arm,
            "overall": _paired_statistics(control, treatment, planned_keys),
            "per_scenario": {
                scenario: _paired_statistics(control, treatment, [key for key in planned_keys if key[0] == scenario])
                for scenario in scenarios
            },
            "per_family": {
                family: _paired_statistics(
                    control,
                    treatment,
                    [key for key in planned_keys if control[key]["family"] == family and treatment[key]["family"] == family],
                )
                for family in families
            },
        }

    available_seconds = sum(cell["wall_time_seconds"] or 0.0 for cell in normalized if cell["valid"])
    common_seconds = 0.0
    if paired_run:
        by_identity = {(cell["arm"], cell["scenario_id"], cell["sample"]): cell for cell in normalized}
        common_seconds = sum(
            (by_identity[(control_arm, scenario, sample)]["wall_time_seconds"] or 0.0)
            + (by_identity[(treatment_arm, scenario, sample)]["wall_time_seconds"] or 0.0)
            for scenario, sample in common_valid_keys
        )
    def grouped_missingness(field: str) -> dict[str, dict[str, object]]:
        groups: dict[str, list[dict]] = {}
        for cell in normalized:
            groups.setdefault(str(cell[field]), []).append(cell)
        return {
            name: {
                "planned": len(rows),
                "valid": sum(1 for row in rows if row["valid"]),
                "invalid": sum(1 for row in rows if not row["valid"]),
                "invalid_reasons": dict(sorted(Counter(
                    row["invalid_reason"] for row in rows if not row["valid"]
                ).items())),
            }
            for name, rows in sorted(groups.items())
        }
    return {
        "schema_version": 3,
        "expected_cells": len(expected_identities),
        "observed_cells": len(normalized),
        "valid": valid,
        "pass": passed,
        "reliability": {
            "planned_cells_by_arm": planned_by_arm,
            "valid_cells_by_arm": valid_by_arm,
            "invalid_cells_by_arm": invalid_by_arm,
            "completion_rate_by_arm": {arm: valid_by_arm[arm] / planned_by_arm[arm] for arm in arms},
            "invalid_reasons_by_arm": reasons_by_arm,
            "missingness_by_scenario": grouped_missingness("scenario_id"),
            "missingness_by_family": grouped_missingness("family"),
            "common_valid_pairs": len(common_valid_keys) if paired_run else None,
            "planned_pairs": len(expected_identities) // 2 if paired_run else None,
            "common_valid_pair_rate": (
                len(common_valid_keys) / (len(expected_identities) // 2) if paired_run else None
            ),
            "excluded_pairs": excluded_pairs,
        },
        "statistics": {
            "available_valid": {
                "overall": _arm_groups(normalized, arms),
                "per_scenario": per_scenario,
                "per_family": per_family,
            },
            "common_valid_paired": paired,
        },
        "timing": {
            "available_valid_summed_cell_seconds": available_seconds,
            "common_valid_summed_cell_seconds": common_seconds if paired_run else None,
            "pipeline_elapsed_seconds": pipeline_elapsed_seconds,
        },
        "measurement_scope": {
            "cell_wall_time": "Harbor worker trial wall clock; excludes judging",
            "tokens_and_cost": "Harbor worker totals; excludes judge usage",
            "pipeline_elapsed": "end-to-end execution including judging",
        },
        "interpretation": {
            "run_purpose": run_purpose,
            "samples_per_identity": samples_per_identity,
            "preregistered_samples": preregistered_samples,
            "inferential_status": (
                "diagnostic-only"
                if run_purpose != "production"
                or samples_per_identity is None
                or preregistered_samples is None
                or samples_per_identity < preregistered_samples
                else "production-descriptive"
            ),
        },
        "cells": normalized,
    }


def write_summary(
    path: Path,
    cells: list[dict],
    expected_identities: set[tuple[str, str, int]],
    *,
    expected_families: dict[str, str],
    control_arm: str | None = None,
    treatment_arm: str | None = None,
    pipeline_elapsed_seconds: float | None = None,
    run_purpose: str = "diagnostic",
    samples_per_identity: int | None = None,
    preregistered_samples: int | None = None,
) -> dict:
    summary = summarize_cells(
        cells,
        expected_identities,
        expected_families=expected_families,
        control_arm=control_arm,
        treatment_arm=treatment_arm,
        pipeline_elapsed_seconds=pipeline_elapsed_seconds,
        run_purpose=run_purpose,
        samples_per_identity=samples_per_identity,
        preregistered_samples=preregistered_samples,
    )
    atomic_write_json(path, summary)
    return summary
