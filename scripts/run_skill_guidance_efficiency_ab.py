#!/usr/bin/env python3
"""Compare the selected skill with a no-skill control."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from skill_manifest import verify_runtime_binary
from skill_source import DEFAULT_SKILL_SOURCE, ResolvedSkillSource, materialize_skill_source
from eval_concurrency import DEFAULT_JOBS
from eval_suite_runner import atomic_write_text, build_eval_command, positive_int, run_eval


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = 10
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare the selected skill with a no-skill control."
    )
    parser.add_argument("--jobs", type=positive_int, default=DEFAULT_JOBS)
    parser.add_argument("--samples", type=positive_int, default=SAMPLES)
    parser.add_argument("--results-file", type=Path, default=DEFAULT_RESULTS_FILE)
    parser.add_argument("--agent", choices=("codex", "claude"), default="codex")
    parser.add_argument("--skill-source", default=DEFAULT_SKILL_SOURCE)
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
    source: ResolvedSkillSource | None = None,
    skill_source: str = DEFAULT_SKILL_SOURCE,
    scenarios: tuple[str, ...] | None = None,
) -> Path:
    source = source or materialize_skill_source(root, skill_source, SOURCE_CACHE)
    current = source.skill
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
        f"# skill_source = {json.dumps(source.source)}",
        f"# source_revision = {json.dumps(source.revision)}",
        f"# source_payload_sha256 = {json.dumps(source.payload_sha256)}",
        f"# selected_skill = {json.dumps(current.name)}",
        'name = "skill-guidance-efficiency-ab"',
        f"agent_judge_config = {json.dumps(agent)}",
        f"scenarios = {json.dumps(scenario_ids)}",
        f"comparison_metrics = {json.dumps(COMPARISON_METRICS)}",
        'aggregate_metric_exclusions_by_target = { iwe-no-skill = ["tool_efficiency", "resource_efficiency"] }',
        'guidance_accounting = "include_activation"',
        'worker_scheduling = "balanced_waves"',
        f"samples = {samples}",
        f"jobs = {jobs}",
        "",
        "[[targets]]",
        f"id = {json.dumps(current.name)}",
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
    source = materialize_skill_source(ROOT, args.skill_source, SOURCE_CACHE)
    print(f"Evaluating {args.skill_source} at {source.revision}")
    manifest = write_experiment(
        jobs=args.jobs,
        samples=args.samples,
        agent=args.agent,
        source=source,
        scenarios=tuple(args.scenarios) if args.scenarios else None,
    )
    return run_eval(
        build_command(
            manifest,
            args.results_file,
            args.agent,
            list_only=args.list,
        ),
        ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
