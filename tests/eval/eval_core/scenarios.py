"""Scenario schema loading and exact scenario selection."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

from .config import DIMENSIONS, EvalConfig, ModelProfile, load_eval_config, resolve_model_profile

EVAL = Path(__file__).resolve().parents[1]
SCENARIOS_FILE = EVAL / "scenarios/iwe.eval.yaml"
SCENARIO_SCHEMA = EVAL / "scenario.schema.json"

class StrictSafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""

def _construct_unique_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping

StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)

def select_scenarios(scenarios: list["Scenario"], requested_ids: list[str] | None) -> list["Scenario"]:
    """Select scenarios by exact stable ID, preserving declaration order."""
    if not requested_ids:
        return scenarios
    available = {scenario.id for scenario in scenarios}
    unknown = sorted(set(requested_ids) - available)
    if unknown:
        raise ValueError(f"unknown scenario id(s): {', '.join(unknown)}")
    requested = set(requested_ids)
    return [scenario for scenario in scenarios if scenario.id in requested]

@dataclass(frozen=True)
class Scenario:
    name: str
    fixture: str
    request: str
    rubric: str
    max_output_bytes: int
    allow_fallback: bool
    iwe_mode: str
    id: str = ""

    min_tool_calls: int = 0
    max_tool_calls: int = 0
    min_task_tool_output_bytes: int = 0
    max_task_tool_output_bytes: int = 0
    scoring: dict[str, dict] | None = None
    procedure: dict[str, list[str]] | None = None
    skill_activation: str = "required"
    max_iwe_calls: int | None = None
    hard_max_task_tool_calls: int | None = None
    allow_broad_fallback: bool = False
    forbidden_retrieve_keys: tuple[str, ...] = ()
    require_oracle_tool_evidence: bool = False
    route: str | None = None
    forbidden_read_paths: tuple[str, ...] = ()
    agents_context: dict[str, str] | None = None
    capabilities: tuple[str, ...] = ()
    command_families: tuple[str, ...] = ()

    @property
    def slug(self) -> str:
        return self.id or re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")

def load_scenarios(
    path: Path = SCENARIOS_FILE,
    eval_config: EvalConfig | None = None,
    model_profile: ModelProfile | None = None,
) -> list[Scenario]:
    eval_config = eval_config or load_eval_config()
    model_profile = model_profile or resolve_model_profile(eval_config)
    schema = json.loads(SCENARIO_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)
    except yaml.YAMLError as exc:
        problem = getattr(exc, "problem", None) or type(exc).__name__
        raise ValueError(f"invalid eval scenario YAML: {problem}") from exc
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise ValueError(f"invalid eval scenario document at {location}: {error.message}")

    result: list[Scenario] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for item in document["scenarios"]:
        for field in ("name", "fixture", "request"):
            if not item[field].strip():
                raise ValueError(f"{field} must contain non-whitespace text in scenario {item['id']}")
        if item["id"] in seen_ids or item["name"] in seen_names:
            raise ValueError(f"duplicate eval scenario id or name: {item['id']}")
        seen_ids.add(item["id"])
        seen_names.add(item["name"])
        runtime = item.get("runtime", {})
        budgets = item["efficiency"]
        for name, bounds in budgets.items():
            if bounds[0] > bounds[1]:
                raise ValueError(f"invalid {name} range in scenario {item['id']}")
        excellent = item["excellent"]
        mode = runtime.get("mode", "real")
        scoring = {
            name: {
                "minimum_score": model_profile.minimum_score[name],
                "excellent": (
                    excellent.get(name)
                    or eval_config.default_excellent.get(name)
                    or (
                        "Follows the ideal semantic procedure or an equivalent bounded strategy, "
                        "completes the task, stops when sufficient evidence is available, and makes no avoidable call."
                        if name == "tool_efficiency"
                        else "Retrieves only relevant, non-duplicate evidence needed by the semantic procedure "
                        "and obtains no unnecessary context."
                    )
                ),
            }
            for name in DIMENSIONS
        }
        result.append(Scenario(
            id=item["id"],
            name=item["name"],
            fixture=item["fixture"],
            request=item["request"].strip(),
            rubric=json.dumps(scoring, indent=2, ensure_ascii=False),
            max_output_bytes=runtime.get("output_bytes", eval_config.default_output_bytes),
            allow_fallback=(
                mode == "unavailable" or runtime.get("allow_filesystem_fallback", False)
            ),
            iwe_mode=mode,
            min_tool_calls=budgets["task_tool_calls"][0],
            max_tool_calls=budgets["task_tool_calls"][1],
            min_task_tool_output_bytes=budgets["task_tool_output_bytes"][0],
            max_task_tool_output_bytes=budgets["task_tool_output_bytes"][1],
            scoring=scoring,
            procedure={
                name: [step.strip() for step in item["procedure"].get(name, [])]
                for name in ("ideal", "acceptable_variations", "stop_when", "avoid")
            },
            skill_activation=item.get("skill_activation", "required"),
            max_iwe_calls=runtime.get("max_iwe_calls"),
            hard_max_task_tool_calls=runtime.get("hard_max_task_tool_calls"),
            allow_broad_fallback=runtime.get("allow_filesystem_fallback", False),
            forbidden_retrieve_keys=tuple(runtime.get("forbidden_retrieve_keys", [])),
            require_oracle_tool_evidence=runtime.get("require_oracle_tool_evidence", False),
            route=runtime.get("route"),
            forbidden_read_paths=tuple(runtime.get("forbidden_read_paths", [])),
            agents_context=dict(item.get("agents_context", {})),
            capabilities=tuple(item["capabilities"]),
            command_families=tuple(item["command_families"]),
        ))
    return result
