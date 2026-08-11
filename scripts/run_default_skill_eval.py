#!/usr/bin/env python3
"""Evaluate config.toml's default skill for correctness and efficiency."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from skill_manifest import load_skills, verify_runtime_binary
from eval_suite_membership import DEFAULT_SKILL_SCENARIOS, validate_membership
from upstream_default_skill import (
    DEFAULT_SOURCE_CACHE as SOURCE_CACHE,
    UPSTREAM_REPOSITORY,
    materialize_upstream_checkout,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLES = 10
DEFAULT_JOBS = 10
SCENARIOS_FILE = Path("tests/eval/scenarios/iwe.eval.yaml")
AGENTS_FILE = Path("tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl")
CACHE = Path("tests/eval/.cache/iwe-default-skill-eval")
DEFAULT_RESULTS_FILE = Path("tests/eval/results/iwe-default-skill-eval.md")


@dataclass(frozen=True)
class Target:
    skill_id: str
    skill_path: Path | None
    skill_version: str | None
    iwe_version: str
    contract_file: Path
    runtime_skill_id: str


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate config.toml's default skill for correctness and efficiency."
    )
    parser.add_argument(
        "--samples",
        type=positive_int,
        default=DEFAULT_SAMPLES,
        help=f"paired samples per target (default: {DEFAULT_SAMPLES})",
    )
    parser.add_argument(
        "--jobs",
        type=positive_int,
        default=DEFAULT_JOBS,
        help=f"concurrent evaluation cells (default: {DEFAULT_JOBS})",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=DEFAULT_RESULTS_FILE,
        help=f"generated Markdown report (default: {DEFAULT_RESULTS_FILE})",
    )
    parser.add_argument(
        "--agent",
        choices=("codex", "claude"),
        default="codex",
        help="shared agent implementation for tested runs and judges (default: codex)",
    )
    parser.add_argument(
        "--repository",
        default=UPSTREAM_REPOSITORY,
        help=f"skills repository whose latest HEAD is evaluated (default: {UPSTREAM_REPOSITORY})",
    )
    parser.add_argument("--list", action="store_true", help="list the matrix without model calls")
    return parser.parse_args(argv)


def load_scenario_ids(root: Path = ROOT) -> tuple[str, ...]:
    return validate_membership(root, DEFAULT_SKILL_SCENARIOS)


def load_targets(root: Path = ROOT) -> tuple[Target, ...]:
    default_skill, skills = load_skills(root)
    current = skills[default_skill]
    return (
        Target(
            current.name,
            current.path,
            current.skill_version,
            current.tested_version,
            current.contract_file,
            current.name,
        ),
    )


def write_experiment(
    samples: int,
    root: Path = ROOT,
    jobs: int = DEFAULT_JOBS,
    agent: str = "codex",
    *,
    source_root: Path | None = None,
    source_revision: str | None = None,
    source_repository: str = UPSTREAM_REPOSITORY,
) -> Path:
    if source_root is None:
        checkout = materialize_upstream_checkout(root, source_repository)
        source_root = checkout.root
        source_revision = checkout.revision
    source_root = source_root.resolve()
    if not source_root.is_relative_to(root.resolve()):
        raise ValueError(f"skill source must be inside the evaluation repository: {source_root}")
    default_skill, skills = load_skills(source_root)
    targets = load_targets(source_root)
    scenario_ids = load_scenario_ids(root)
    cache = (root / CACHE).resolve()
    lines = [
        f"# source_repository = {json.dumps(source_repository)}",
        f"# source_revision = {json.dumps(source_revision or 'working-tree')}",
        f"# default_skill = {json.dumps(default_skill)}",
        "schema_version = 1",
        'name = "iwe-default-skill-correctness-efficiency"',
        f"agent_judge_config = {json.dumps(agent)}",
        f"scenarios = {json.dumps(scenario_ids)}",
        'guidance_accounting = "include_activation"',
        f"samples = {samples}",
        f"jobs = {jobs}",
    ]
    for target in targets:
        runtime_spec = skills[target.runtime_skill_id]
        binary = verify_runtime_binary(runtime_spec)
        runtime = cache / "runtimes" / target.skill_id
        runtime.mkdir(parents=True, exist_ok=True)
        link = runtime / runtime_spec.runtime_cli
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(binary)
        lines.extend([
            "",
            "[[targets]]",
            f"id = {json.dumps(target.skill_id)}",
            f"agents_file = {json.dumps(str(AGENTS_FILE))}",
        ])
        if target.skill_path is None:
            lines.append('skill_mode = "none"')
        else:
            lines.extend([
                f"skill_path = {json.dumps(os.path.relpath(target.skill_path, root))}",
                f"skill_version = {json.dumps(target.skill_version)}",
            ])
        lines.extend([
            f"contract_file = {json.dumps(os.path.relpath(target.contract_file, root))}",
            "[targets.runtime]",
            f"cli = {json.dumps(runtime_spec.runtime_cli)}",
            'source = "directory"',
            f"version = {json.dumps(target.iwe_version)}",
            f"directory = {json.dumps(str(runtime.relative_to(root)))}",
        ])
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
    ]
    if list_only:
        command.append("--list")
    else:
        command.extend(["--markdown-report", str(results_file)])
    command.extend(["--agent", agent])
    return command


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    checkout = materialize_upstream_checkout(ROOT, args.repository)
    print(f"Evaluating {args.repository} at {checkout.revision}")
    manifest = write_experiment(
        args.samples,
        jobs=args.jobs,
        agent=args.agent,
        source_root=checkout.root,
        source_revision=checkout.revision,
        source_repository=args.repository,
    )
    return subprocess.call(
        build_command(manifest, args.results_file, args.agent, list_only=args.list),
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
