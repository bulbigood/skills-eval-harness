"""Scoring, aggregation, diagnostics, and saved-report replay."""
from __future__ import annotations

import json
import math
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import AbstractSet, Mapping

from .config import DIMENSIONS, EvalConfig, ModelProfile, load_eval_config, resolve_model_profile
from .io import atomic_write_json
from .scenarios import Scenario


RESULT_DIMENSIONS = ("task_correctness", "scenario_compliance", "safety", "evidence_quality")


PROCEDURE_DIMENSIONS = ("skill_compliance", "tool_efficiency", "resource_efficiency")


def efficiency_range_diagnostic(
    observed: int,
    minimum: int,
    maximum: int,
) -> dict:
    """Describe distance from an ideal range without assigning a semantic score."""
    if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (observed, minimum, maximum)):
        raise ValueError("efficiency counts and bounds must be non-negative integers")
    if minimum > maximum:
        raise ValueError("efficiency minimum must not exceed maximum")
    if minimum <= observed <= maximum:
        return {
            "observed": observed,
            "excellent_range": [minimum, maximum],
            "status": "within",
            "distance": 0,
            "deviation_percent": 0.0,
        }
    if observed < minimum:
        distance = minimum - observed
        denominator = minimum
        status = "below"
    else:
        distance = observed - maximum
        denominator = maximum
        status = "above"
    deviation = None if denominator == 0 else round(distance * 100 / denominator, 2)
    return {
        "observed": observed,
        "excellent_range": [minimum, maximum],
        "status": status,
        "distance": distance,
        "deviation_percent": deviation,
    }


def efficiency_diagnostics(
    scenario: Scenario,
    metrics: dict,
) -> dict:
    return {
        "task_tool_calls": efficiency_range_diagnostic(
            metrics.get("task_tool_calls", 0),
            scenario.min_tool_calls,
            scenario.max_tool_calls,
        ),
        "task_tool_output_bytes": efficiency_range_diagnostic(
            metrics.get("task_tool_output_bytes", 0),
            scenario.min_task_tool_output_bytes,
            scenario.max_task_tool_output_bytes,
        ),
        "unbounded_read": bool(metrics.get("unbounded_read_calls", 0)),
    }


def verdict(
    scenario: Scenario,
    critique: dict,
    mechanical: list[str],
    exits_ok: bool,
    procedure_errors: list[str] | None = None,
    deterministic_metric_failures: dict[str, str] | None = None,
) -> dict:
    normalized_critique = critique if isinstance(critique, dict) else {}
    raw_dimensions = normalized_critique.get("dimensions", {})
    dimensions = raw_dimensions if isinstance(raw_dimensions, dict) else {}
    scoring = scenario.scoring or {}
    scores = {}
    malformed_scores = []
    for name in DIMENSIONS:
        raw_dimension = dimensions.get(name, {})
        dimension = raw_dimension if isinstance(raw_dimension, dict) else {}
        raw = dimension.get("score", 0)
        if isinstance(raw, int) and not isinstance(raw, bool) and 0 <= raw <= 5:
            score = raw
        else:
            score = 0
            malformed_scores.append(name)
        scores[name] = score
    failures = {
        name: {"score": scores[name], "required": scoring[name]["minimum_score"]}
        for name in DIMENSIONS
        if scores[name] < scoring[name]["minimum_score"]
    }
    for name, reason in (deterministic_metric_failures or {}).items():
        failure = failures.setdefault(
            name,
            {"score": scores[name], "required": scoring[name]["minimum_score"]},
        )
        failure["deterministic"] = reason
    validation_errors = list(mechanical)
    if not exits_ok:
        validation_errors.append("agent or judge process failed")
    if malformed_scores:
        validation_errors.append(
            "missing or invalid metric scores: " + ", ".join(malformed_scores)
        )
    return {
        "valid": not validation_errors,
        "metric_scores": scores,
        "metric_failures": failures,
        "validation_errors": validation_errors,
        "procedure_errors": list(procedure_errors or []),
        "critique": critique,
    }


def profile_verdict(raw_verdict: dict, profile: ModelProfile) -> dict:
    """Classify immutable judge scores under the selected model profile."""
    scores = raw_verdict.get("metric_scores", {})
    raw_failures = raw_verdict.get("metric_failures", {})
    failures: dict[str, dict] = {}
    for name in DIMENSIONS:
        deterministic = (
            raw_failures.get(name, {}).get("deterministic")
            if isinstance(raw_failures.get(name), dict)
            else None
        )
        score = scores.get(name, 0)
        if score < profile.minimum_score[name] or deterministic:
            failure = {"score": score, "required": profile.minimum_score[name]}
            if deterministic:
                failure["deterministic"] = deterministic
            failures[name] = failure
    return {
        "name": profile.name,
        "minimum_score": dict(profile.minimum_score),
        "required_success_percent": dict(profile.required_success_percent),
        "metric_failures": failures,
    }


def required_successes(total: int, percent: int) -> int:
    if total < 1:
        raise ValueError("sample total must be positive")
    if not 1 <= percent <= 100:
        raise ValueError("required success percent must be in 1..100")
    return math.ceil(total * percent / 100)


def agent_metadata(command: str) -> dict[str, str]:
    tokens = shlex.split(command)
    executable = shutil.which(tokens[0])
    if not executable:
        raise RuntimeError(f"configured agent executable is unavailable: {tokens[0]}")
    version = subprocess.run(
        [executable, "--version"], text=True, capture_output=True, check=True
    ).stdout.strip()
    model_flag = "-m" if "-m" in tokens else "--model" if "--model" in tokens else None
    model = tokens[tokens.index(model_flag) + 1] if model_flag else "unknown"
    reasoning = "unknown"
    if "--effort" in tokens:
        reasoning = tokens[tokens.index("--effort") + 1]
    for index, token in enumerate(tokens[:-1]):
        if token == "-c" and tokens[index + 1].startswith("model_reasoning_effort="):
            reasoning = tokens[index + 1].split("=", 1)[1].strip('"')
            break
    return {
        "name": {"codex": "Codex CLI", "claude": "Claude Code"}.get(
            Path(executable).name, Path(executable).name
        ),
        "version": version.removeprefix("codex-cli "),
        "model": model,
        "reasoning": reasoning,
    }


def validate_shared_agent(config: dict, expected_agent: str) -> dict[str, dict[str, str]]:
    agent_name = Path(shlex.split(config["agent_command"])[0]).name
    judge_name = Path(shlex.split(config["judge_command"])[0]).name
    if agent_name != expected_agent or judge_name != expected_agent:
        raise ValueError(
            "tested runs and judges must use the same configured agent "
            f"{expected_agent!r}; got agent={agent_name!r}, judge={judge_name!r}"
        )
    return {
        "agent": agent_metadata(config["agent_command"]),
        "judge": agent_metadata(config["judge_command"]),
    }


def aggregate_results(
    results: list[dict],
    eval_config: EvalConfig | None = None,
    expected_samples: int | None = None,
    excluded_dimensions_by_target: dict[str, set[str]] | None = None,
    excluded_dimensions_by_scenario: Mapping[str, AbstractSet[str]] | None = None,
    model_profile: ModelProfile | None = None,
) -> list[dict]:
    eval_config = eval_config or load_eval_config()
    model_profile = model_profile or resolve_model_profile(eval_config)
    excluded_dimensions_by_target = excluded_dimensions_by_target or {}
    excluded_dimensions_by_scenario = excluded_dimensions_by_scenario or {}
    grouped: dict[tuple[str | None, str], list[dict]] = {}
    for result in results:
        scenario = result["scenario"]
        scenario_id = result.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise ValueError(f"scenario_id missing from result: {scenario}")
        grouped.setdefault((result.get("target_id"), scenario_id), []).append(result)
    outcomes = []
    for (target_id, scenario_id), samples in grouped.items():
        scenario = samples[0]["scenario"]
        total = len(samples)
        sample_ids = [sample["sample"] for sample in samples]
        if len(sample_ids) != len(set(sample_ids)):
            raise ValueError(f"duplicate samples for {target_id or 'single'} / {scenario}")
        if expected_samples is not None and set(sample_ids) != set(range(1, expected_samples + 1)):
            raise ValueError(f"incomplete samples for {target_id or 'single'} / {scenario}")
        metrics = {}
        for dimension in DIMENSIONS:
            if (
                dimension in excluded_dimensions_by_target.get(target_id or "", set())
                or dimension in excluded_dimensions_by_scenario.get(scenario_id, set())
            ):
                metrics[dimension] = {
                    "applicable": False,
                    "minimum_score": None,
                    "successful_samples": None,
                    "total_samples": total,
                    "success_percent": None,
                    "required_success_percent": None,
                    "required_successes": None,
                    "score_histogram": None,
                    "pass": True,
                }
                continue
            successful = sum(
                sample["verdict"].get("valid", False)
                and dimension
                not in profile_verdict(
                    sample["verdict"], model_profile
                )["metric_failures"]
                for sample in samples
            )
            percent = model_profile.required_success_percent[dimension]
            required = required_successes(total, percent)
            metrics[dimension] = {
                "applicable": True,
                "minimum_score": model_profile.minimum_score[dimension],
                "successful_samples": successful,
                "total_samples": total,
                "success_percent": successful * 100 / total,
                "required_success_percent": percent,
                "required_successes": required,
                "score_histogram": {
                    str(score): sum(
                        sample["verdict"].get("metric_scores", {}).get(dimension, 0) == score
                        for sample in samples
                    )
                    for score in range(6)
                },
                "pass": successful >= required,
            }
        invalid_samples = sum(not sample["verdict"].get("valid", False) for sample in samples)
        procedure_failure_samples = sum(
            bool(sample["verdict"].get("procedure_errors", [])) for sample in samples
        )
        procedure_error_counts: dict[str, int] = {}
        for sample in samples:
            for error in set(sample["verdict"].get("procedure_errors", [])):
                procedure_error_counts[error] = procedure_error_counts.get(error, 0) + 1
        outcome = {
            "scenario": scenario,
            "scenario_id": scenario_id,
            "model_profile": model_profile.name,
            "samples": total,
            "invalid_samples": invalid_samples,
            "procedure_failure_samples": procedure_failure_samples,
            "procedure_error_counts": dict(sorted(procedure_error_counts.items())),
            "metrics": metrics,
            "result_pass": invalid_samples == 0 and all(
                metrics[name]["pass"] for name in RESULT_DIMENSIONS
            ),
            "procedure_pass": all(metrics[name]["pass"] for name in PROCEDURE_DIMENSIONS),
            "pass": invalid_samples == 0 and all(item["pass"] for item in metrics.values()),
        }
        if target_id is not None:
            outcome["target_id"] = target_id
        outcomes.append(outcome)
    return outcomes


def replay_saved_report(
    report_dir: Path,
    output_path: Path,
    model_profile: ModelProfile,
    eval_config: EvalConfig | None = None,
) -> dict:
    """Reaggregate immutable raw samples under a selected model profile."""
    eval_config = eval_config or load_eval_config()
    source = report_dir.resolve()
    destination = output_path.resolve()
    if not source.is_dir():
        raise ValueError(f"saved report directory not found: {report_dir}")
    if source == destination or source in destination.parents:
        raise ValueError("replay output must be outside the immutable source report")

    results = []
    for path in sorted(source.rglob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON in saved report: {path}") from exc
        if not isinstance(document, dict):
            continue
        if not {"scenario", "scenario_id", "sample", "verdict"} <= set(document):
            continue
        results.append(document)
    if not results:
        raise ValueError("saved report contains no raw samples")

    experiment_path = source / "experiment.json"
    experiment_document = (
        json.loads(experiment_path.read_text(encoding="utf-8"))
        if experiment_path.is_file()
        else {}
    )
    excluded_dimensions_by_scenario = {
        scenario: frozenset(metrics)
        for scenario, metrics in experiment_document.get("metric_exclusions", {}).items()
    }

    identities = [
        (result.get("target_id"), result["scenario_id"], result["sample"])
        for result in results
    ]
    if len(identities) != len(set(identities)):
        raise ValueError("saved report contains duplicate raw sample identities")
    grouped_samples: dict[tuple[str | None, str], set[int]] = {}
    for result in results:
        grouped_samples.setdefault(
            (result.get("target_id"), result["scenario_id"]), set()
        ).add(result["sample"])
    sample_sets = list(grouped_samples.values())
    expected = set(range(1, max(max(values) for values in sample_sets) + 1))
    if any(values != expected for values in sample_sets):
        raise ValueError("saved report has incomplete or inconsistent sample cardinality")

    excluded_dimensions_by_target = {
        result["target_id"]: {"skill_compliance"}
        for result in results
        if result.get("target_id")
        and result.get("target_provenance", {}).get("skill_mode") == "none"
    }
    outcomes = aggregate_results(
        results,
        eval_config,
        expected_samples=len(expected),
        excluded_dimensions_by_target=excluded_dimensions_by_target,
        excluded_dimensions_by_scenario=excluded_dimensions_by_scenario,
        model_profile=model_profile,
    )
    replay = {
        "schema_version": 1,

        "source_report": str(source),
        "model_profile": model_profile.name,
        "minimum_score": model_profile.minimum_score,
        "required_success_percent": model_profile.required_success_percent,
        "raw_samples": len(results),
        "scenarios": outcomes,
    }
    atomic_write_json(output_path, replay)
    return replay
