"""Model profiles and evaluator acceptance configuration."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIMENSIONS = ("task_correctness", "scenario_compliance", "skill_compliance", "safety", "evidence_quality", "tool_efficiency", "resource_efficiency")

@dataclass(frozen=True)
class ModelProfile:
    name: str
    minimum_score: dict[str, int]
    required_success_percent: dict[str, int]

@dataclass(frozen=True)
class EvalConfig:
    score_scale: dict[int, str]
    efficiency_score_scale: dict[str, dict[int, str]]
    model_profiles: dict[str, ModelProfile]
    agent_model_profiles: dict[str, str]
    default_model_profile: str
    default_excellent: dict[str, str]
    default_output_bytes: int

def load_eval_config(path: Path = ROOT / "config.toml") -> EvalConfig:
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    evaluation = document.get("eval", {})
    raw_scale = evaluation.get("score_scale", {})
    raw_efficiency_scale = evaluation.get("efficiency_score_scale", {})
    raw_profiles = evaluation.get("model_profiles", {})
    raw_agent_profiles = evaluation.get("agent_model_profiles", {})
    default_profile = evaluation.get("default_model_profile")
    raw_excellent = evaluation.get("default_excellent", {})
    raw_execution = evaluation.get("execution", {})
    try:
        scale = {int(score): description for score, description in raw_scale.items()}
    except (TypeError, ValueError) as exc:
        raise ValueError("eval.score_scale keys must be integers 0..5") from exc
    if set(scale) != set(range(6)) or any(
        not isinstance(description, str) or not description.strip()
        for description in scale.values()
    ):
        raise ValueError("eval.score_scale must declare non-empty descriptions for 0..5")
    efficiency_scale: dict[str, dict[int, str]] = {}
    if set(raw_efficiency_scale) != {"tool_efficiency", "resource_efficiency"}:
        raise ValueError("eval.efficiency_score_scale must declare both efficiency metrics")
    for metric, descriptions in raw_efficiency_scale.items():
        try:
            metric_scale = {int(score): description for score, description in descriptions.items()}
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError(f"eval.efficiency_score_scale.{metric} keys must be integers 0..5") from exc
        if set(metric_scale) != set(range(6)) or any(
            not isinstance(description, str) or not description.strip()
            for description in metric_scale.values()
        ):
            raise ValueError(
                f"eval.efficiency_score_scale.{metric} must declare non-empty descriptions for 0..5"
            )
        efficiency_scale[metric] = metric_scale
    if not isinstance(raw_profiles, dict) or set(raw_profiles) != {"medium", "weak"}:
        raise ValueError("eval.model_profiles must declare exactly medium and weak")
    profiles: dict[str, ModelProfile] = {}
    for name, raw_profile in raw_profiles.items():
        if not isinstance(raw_profile, dict):
            raise ValueError(f"eval.model_profiles.{name} must be a table")
        raw_minimum = raw_profile.get("minimum_score", {})
        raw_percent = raw_profile.get("required_success_percent", {})
        if set(raw_minimum) != set(DIMENSIONS) or any(
            not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 5
            for score in raw_minimum.values()
        ):
            raise ValueError(
                f"eval.model_profiles.{name}.minimum_score must declare integer scores 0..5 for every metric"
            )
        if set(raw_percent) != set(DIMENSIONS) or any(
            not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 100
            for value in raw_percent.values()
        ):
            raise ValueError(
                f"eval.model_profiles.{name}.required_success_percent must declare integers 1..100 for every metric"
            )
        profiles[name] = ModelProfile(name, dict(raw_minimum), dict(raw_percent))
    if default_profile != "medium":
        raise ValueError("eval.default_model_profile must be medium")
    if raw_agent_profiles != {"codex": "weak", "claude": "medium"}:
        raise ValueError(
            "eval.agent_model_profiles must map codex to weak and claude to medium"
        )
    if set(raw_excellent) != {"skill_compliance", "safety"} or any(
        not isinstance(text, str) or not text.strip() for text in raw_excellent.values()
    ):
        raise ValueError("eval.default_excellent must declare skill_compliance and safety")
    output_bytes = raw_execution.get("output_bytes")
    if not isinstance(output_bytes, int) or isinstance(output_bytes, bool) or output_bytes < 1:
        raise ValueError("eval.execution.output_bytes must be a positive integer")
    return EvalConfig(
        scale,
        efficiency_scale,
        profiles,
        dict(raw_agent_profiles),
        default_profile,
        dict(raw_excellent),
        output_bytes,
    )

def resolve_model_profile(eval_config: EvalConfig, name: str | None = None) -> ModelProfile:
    selected = name or eval_config.default_model_profile
    try:
        return eval_config.model_profiles[selected]
    except KeyError as exc:
        raise ValueError(f"unknown model profile: {selected}") from exc

def resolve_agent_model_profile(
    eval_config: EvalConfig,
    agent: str,
    requested: str | None = None,
) -> ModelProfile:
    try:
        canonical = eval_config.agent_model_profiles[agent]
    except KeyError as exc:
        raise ValueError(f"unknown agent implementation: {agent}") from exc
    if requested is not None and requested != canonical:
        raise ValueError(
            f"agent {agent} requires model profile {canonical}, got {requested}"
        )
    return resolve_model_profile(eval_config, canonical)
