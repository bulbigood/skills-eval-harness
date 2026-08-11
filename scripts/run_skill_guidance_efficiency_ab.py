#!/usr/bin/env python3
"""Compare the latest upstream default skill with a no-skill control."""

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
from upstream_default_skill import UPSTREAM_REPOSITORY, materialize_upstream_checkout


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = 10
DEFAULT_JOBS = 10
SCENARIOS = (
    "discover-and-retrieve-bounded-multi-hop-context",
    "query-structured-metadata-without-scanning-files",
    "ambiguous-discovery-with-one-follow-up",
)
COMPARISON_METRICS = ("tool_efficiency", "resource_efficiency")
AGENTS_FILE = Path("tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl")
SOURCE_CACHE = Path("tests/eval/.cache/skill-guidance-efficiency-source")
CACHE = Path("tests/eval/.cache/skill-guidance-efficiency-ab")
DEFAULT_RESULTS_FILE = Path("tests/eval/results/skill-guidance-efficiency-ab.md")


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("jobs must be at least 1")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare the latest upstream default skill with a no-skill control."
    )
    parser.add_argument("--jobs", type=positive_int, default=DEFAULT_JOBS)
    parser.add_argument("--samples", type=positive_int, default=SAMPLES)
    parser.add_argument("--results-file", type=Path, default=DEFAULT_RESULTS_FILE)
    parser.add_argument("--agent", choices=("codex", "claude"), default="codex")
    parser.add_argument("--repository", default=UPSTREAM_REPOSITORY)
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="scenario ID to run; repeat to select multiple scenarios",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="regenerate and list the selected matrix without model calls",
    )
    return parser.parse_args(argv)


def write_experiment(
    *,
    root: Path = ROOT,
    jobs: int = DEFAULT_JOBS,
    samples: int = SAMPLES,
    agent: str = "codex",
    source_root: Path | None = None,
    source_revision: str | None = None,
    source_repository: str = UPSTREAM_REPOSITORY,
    scenarios: tuple[str, ...] | None = None,
) -> Path:
    if source_root is None:
        checkout = materialize_upstream_checkout(root, source_repository, SOURCE_CACHE)
        source_root = checkout.root
        source_revision = checkout.revision
    source_root = source_root.resolve()
    if not source_root.is_relative_to(root.resolve()):
        raise ValueError(f"skill source must be inside the evaluation repository: {source_root}")
    default_skill, skills = load_skills(source_root)
    current = skills[default_skill]
    binary = verify_runtime_binary(current)
    cache = (root / CACHE).resolve()
    runtime = cache / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    link = runtime / current.runtime_cli
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(binary)

    shared_runtime = [
        f"agents_file = {json.dumps(str(AGENTS_FILE))}",
        f"contract_file = {json.dumps(os.path.relpath(current.contract_file, root))}",
        "[targets.runtime]",
        f"cli = {json.dumps(current.runtime_cli)}",
        'source = "directory"',
        f"version = {json.dumps(current.tested_version)}",
        f"directory = {json.dumps(str(runtime.relative_to(root)))}",
    ]
    scenario_ids = scenarios or SCENARIOS
    unknown = set(scenario_ids) - set(SCENARIOS)
    if unknown:
        raise ValueError(f"unknown skill-guidance scenarios: {sorted(unknown)}")
    lines = [
        "schema_version = 1",
        f"# source_repository = {json.dumps(source_repository)}",
        f"# source_revision = {json.dumps(source_revision or 'working-tree')}",
        f"# default_skill = {json.dumps(default_skill)}",
        'name = "skill-guidance-efficiency-ab"',
        f"agent_judge_config = {json.dumps(agent)}",
        f"scenarios = {json.dumps(scenario_ids)}",
        f"comparison_metrics = {json.dumps(COMPARISON_METRICS)}",
        'guidance_accounting = "include_activation"',
        'worker_scheduling = "balanced_waves"',
        f"samples = {samples}",
        f"jobs = {jobs}",
        "",
        "[[targets]]",
        f"id = {json.dumps(default_skill)}",
        f"skill_path = {json.dumps(os.path.relpath(current.path, root))}",
        f"skill_version = {json.dumps(current.skill_version)}",
        *shared_runtime,
        "",
        "[[targets]]",
        'id = "iwe-no-skill"',
        'skill_mode = "none"',
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
        "--experiment",
        str(manifest),
        "--model-profile",
        model_profile,
        "--agent",
        agent,
    ]
    if list_only:
        command.append("--list")
    else:
        command.extend(["--markdown-report", str(results_file)])
    return command


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    checkout = materialize_upstream_checkout(ROOT, args.repository, SOURCE_CACHE)
    print(f"Evaluating {args.repository} at {checkout.revision}")
    manifest = write_experiment(
        jobs=args.jobs,
        samples=args.samples,
        agent=args.agent,
        source_root=checkout.root,
        source_revision=checkout.revision,
        source_repository=args.repository,
        scenarios=tuple(args.scenarios) if args.scenarios else None,
    )
    return subprocess.call(
        build_command(
            manifest,
            args.results_file,
            args.agent,
            list_only=args.list,
        ),
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
