#!/usr/bin/env python3
"""Run the three-arm IWE context-routing evaluation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from skill_manifest import load_skills, verify_runtime_binary
from eval_suite_membership import CONTEXT_ROUTING_SCENARIOS

ROOT = Path(__file__).resolve().parents[1]
CURRENT_SKILL = "iwe-v18"
DEFAULT_SAMPLES = 10
DEFAULT_JOBS = 15
SCENARIOS = CONTEXT_ROUTING_SCENARIOS
COMPARISON_METRICS = (
    "task_correctness",
    "scenario_compliance",
    "skill_compliance",
    "tool_efficiency",
    "resource_efficiency",
)
AGENTS_FILE = Path("tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl")
SCENARIO_FILE = Path("tests/eval/scenarios/iwe.eval.yaml")
CACHE = Path("tests/eval/.cache/iwe-context-routing-ab")
DEFAULT_RESULTS_FILE = Path("tests/eval/results/iwe-context-routing-ab.md")


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=positive_int, default=DEFAULT_JOBS)
    parser.add_argument("--samples", type=positive_int, default=DEFAULT_SAMPLES)
    parser.add_argument("--results-file", type=Path, default=DEFAULT_RESULTS_FILE)
    parser.add_argument("--agent", choices=("codex", "claude"), default="codex")
    parser.add_argument("--list", action="store_true")
    return parser.parse_args(argv)


def write_experiment(
    *,
    root: Path = ROOT,
    jobs: int = DEFAULT_JOBS,
    samples: int = DEFAULT_SAMPLES,
    agent: str = "codex",
) -> Path:
    _, skills = load_skills(root)
    current = skills[CURRENT_SKILL]
    binary = verify_runtime_binary(current)
    cache = (root / CACHE).resolve()
    runtime = cache / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    link = runtime / current.runtime_cli
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(binary)

    shared_runtime = [
        f"contract_file = {json.dumps(os.path.relpath(current.contract_file, root))}",
        "[targets.runtime]",
        f"cli = {json.dumps(current.runtime_cli)}",
        'source = "directory"',
        f"version = {json.dumps(current.tested_version)}",
        f"directory = {json.dumps(str(runtime.relative_to(root)))}",
    ]
    skill = [
        f"skill_path = {json.dumps(os.path.relpath(current.path, root))}",
        f"skill_version = {json.dumps(current.skill_version)}",
    ]
    lines = [
        "schema_version = 1",
        'name = "iwe-context-routing-ab"',
        f"agent_judge_config = {json.dumps(agent)}",
        f"scenarios = {json.dumps(SCENARIOS)}",
        f"comparison_metrics = {json.dumps(COMPARISON_METRICS)}",
        'guidance_accounting = "include_activation"',
        'skill_activation = "optional"',
        'worker_scheduling = "balanced_waves"',
        f"samples = {samples}",
        f"jobs = {jobs}",
        "",
        "[[targets]]",
        'id = "iwe-cli-only"',
        'skill_mode = "none"',
        *shared_runtime,
        "",
        "[[targets]]",
        'id = "iwe-v18"',
        *skill,
        *shared_runtime,
        "",
        "[[targets]]",
        'id = "iwe-v18-agents"',
        f"agents_file = {json.dumps(str(AGENTS_FILE))}",
        *skill,
        *shared_runtime,
    ]
    path = cache / "experiment.toml"
    temporary = path.with_suffix(".toml.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path


def build_command(
    manifest: Path,
    results_file: Path,
    agent: str = "codex",
    *,
    list_only: bool = False,
) -> list[str]:
    model_profile = {"codex": "weak", "claude": "medium"}[agent]
    command = [
        sys.executable,
        str(ROOT / "tests/eval/run.py"),
        "--experiment", str(manifest),
        "--scenario-file", str(SCENARIO_FILE),
        "--model-profile", model_profile,
        "--agent", agent,
    ]
    if list_only:
        command.append("--list")
    else:
        command.extend(["--markdown-report", str(results_file)])
    return command


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = write_experiment(
        jobs=args.jobs,
        samples=args.samples,
        agent=args.agent,
    )
    return subprocess.call(
        build_command(manifest, args.results_file, args.agent, list_only=args.list),
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
