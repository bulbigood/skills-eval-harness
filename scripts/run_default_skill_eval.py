#!/usr/bin/env python3
"""Evaluate config.toml's default skill for correctness and efficiency."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from skill_manifest import verify_runtime_binary
from skill_source import DEFAULT_SKILL_SOURCE, ResolvedSkillSource, materialize_skill_source
from eval_suite_membership import DEFAULT_SKILL_SCENARIOS, validate_membership
from eval_concurrency import DEFAULT_JOBS
from eval_suite_runner import atomic_write_text, build_eval_command, positive_int, run_eval


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLES = 10
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
        "--skill-source",
        default=DEFAULT_SKILL_SOURCE,
        help=(
            "skill directory: local path, file:// URI, or GitHub "
            f"directory URL (default: {DEFAULT_SKILL_SOURCE})"
        ),
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="scenario ID to run; repeat to select multiple scenarios",
    )
    parser.add_argument("--list", action="store_true", help="list the matrix without model calls")
    return parser.parse_args(argv)


def load_scenario_ids(root: Path = ROOT) -> tuple[str, ...]:
    return validate_membership(root, DEFAULT_SKILL_SCENARIOS)


def load_targets(source: ResolvedSkillSource) -> tuple[Target, ...]:
    current = source.skill
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
    source: ResolvedSkillSource | None = None,
    skill_source: str = DEFAULT_SKILL_SOURCE,
    scenarios: tuple[str, ...] | None = None,
) -> Path:
    source = source or materialize_skill_source(root, skill_source)
    current = source.skill
    targets = load_targets(source)
    available_scenarios = load_scenario_ids(root)
    scenario_ids = scenarios or available_scenarios
    unknown = set(scenario_ids) - set(available_scenarios)
    if unknown:
        raise ValueError(f"unknown default-skill scenarios: {sorted(unknown)}")
    cache = (root / CACHE).resolve()
    lines = [
        f"# skill_source = {json.dumps(source.source)}",
        f"# source_revision = {json.dumps(source.revision)}",
        f"# source_payload_sha256 = {json.dumps(source.payload_sha256)}",
        f"# selected_skill = {json.dumps(current.name)}",
        "schema_version = 1",
        'name = "iwe-default-skill-correctness-efficiency"',
        f"agent_judge_config = {json.dumps(agent)}",
        f"scenarios = {json.dumps(scenario_ids)}",
        'guidance_accounting = "exclude_activation"',
        f"samples = {samples}",
        f"jobs = {jobs}",
    ]
    for target in targets:
        runtime_spec = current
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
    atomic_write_text(path, "\n".join(lines) + "\n")
    return path


def build_command(
    manifest: Path,
    results_file: Path,
    agent: str = "codex",
    *,
    list_only: bool = False,
) -> list[str]:
    return build_eval_command(
        root=ROOT,
        manifest=manifest,
        results_file=results_file,
        agent=agent,
        list_only=list_only,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = materialize_skill_source(ROOT, args.skill_source)
    print(f"Evaluating {args.skill_source} at {source.revision}")
    manifest = write_experiment(
        args.samples,
        jobs=args.jobs,
        agent=args.agent,
        source=source,
        scenarios=tuple(args.scenarios) if args.scenarios else None,
    )
    return run_eval(
        build_command(manifest, args.results_file, args.agent, list_only=args.list), ROOT
    )


if __name__ == "__main__":
    raise SystemExit(main())
