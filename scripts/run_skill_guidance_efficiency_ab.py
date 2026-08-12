#!/usr/bin/env python3
"""Compare the selected skill with a no-skill control."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
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
    "summarize-one-topic",
    "read-one-note-with-parent-context",
    "list-and-sort-typed-notes",
    "discover-and-retrieve-bounded-multi-hop-context",
    "query-structured-metadata-without-scanning-files",
    "ambiguous-discovery-with-one-follow-up",
)
COMPARISON_METRICS = ("tool_efficiency", "resource_efficiency")
SOURCE_CACHE = Path("tests/eval/.cache/skill-guidance-efficiency-source")
CACHE = Path("tests/eval/.cache/skill-guidance-efficiency-ab")
AGENTS_CACHE_FILE = CACHE / "guidance.AGENTS.md.tmpl"
DEFAULT_RESULTS_FILE = Path("tests/eval/results/skill-guidance-efficiency-ab.md")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare the selected skill with a no-skill control."
    )
    parser.add_argument("--jobs", type=positive_int, default=DEFAULT_JOBS)
    parser.add_argument("--samples", type=positive_int, default=SAMPLES)
    parser.add_argument("--results-file", type=Path, default=DEFAULT_RESULTS_FILE)
    parser.add_argument(
        "--publish-output",
        type=Path,
        help=(
            "after a successful complete run, publish a sanitized tracked report "
            "under docs/evals/results"
        ),
    )
    parser.add_argument("--agent", choices=("codex", "claude"), default="codex")
    parser.add_argument("--skill-source", default=DEFAULT_SKILL_SOURCE)
    parser.add_argument(
        "--agents-template-source",
        help=(
            "optional local path, file:// URI, or HTTPS URL whose response body is "
            "the AGENTS.md text/template installed identically in both arms"
        ),
    )
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


def materialize_agents_template(root: Path, source: str | None) -> Path | None:
    """Resolve optional AGENTS.md text to one stable repository-local template."""
    if source is None:
        return None
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme == "https":
        with urllib.request.urlopen(source, timeout=30) as response:  # noqa: S310
            payload = response.read()
    elif parsed.scheme == "file":
        payload = Path(urllib.request.url2pathname(parsed.path)).expanduser().read_bytes()
    elif parsed.scheme:
        raise ValueError("AGENTS template source must be a local path, file:// URI, or HTTPS URL")
    else:
        path = Path(source).expanduser()
        if not path.is_absolute():
            path = root / path
        payload = path.read_bytes()
    if not payload.strip():
        raise ValueError("AGENTS template source is empty")
    destination = (root / AGENTS_CACHE_FILE).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(destination)
    digest = hashlib.sha256(payload).hexdigest()
    print(f"Using shared AGENTS.md template {source} (sha256={digest})")
    return destination


def write_experiment(
    *,
    root: Path = ROOT,
    jobs: int = DEFAULT_JOBS,
    samples: int = SAMPLES,
    agent: str = "codex",
    source: ResolvedSkillSource | None = None,
    skill_source: str = DEFAULT_SKILL_SOURCE,
    agents_template: Path | None = None,
    agents_template_source: str | None = None,
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
        f"contract_file = {json.dumps(os.path.relpath(current.contract_file, root))}",
        "[targets.runtime]",
        f"cli = {json.dumps(current.runtime_cli)}",
        'source = "directory"',
        f"version = {json.dumps(current.tested_version)}",
        f"directory = {json.dumps(str(runtime.relative_to(root)))}",
    ]
    if agents_template is not None:
        shared_runtime.insert(
            0, f"agents_file = {json.dumps(os.path.relpath(agents_template, root))}"
        )
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
        *(
            [f"# agents_template_source = {json.dumps(agents_template_source)}"]
            if agents_template_source is not None
            else []
        ),
        'name = "skill-guidance-efficiency-ab"',
        f"agent_judge_config = {json.dumps(agent)}",
        f"scenarios = {json.dumps(scenario_ids)}",
        f"comparison_metrics = {json.dumps(COMPARISON_METRICS)}",
        'aggregate_metric_exclusions_by_target = { iwe-v18 = ["tool_efficiency", "resource_efficiency"], iwe-no-skill = ["tool_efficiency", "resource_efficiency"] }',
        'required_aggregate_targets = ["iwe-v18"]',
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
    agents_template = materialize_agents_template(ROOT, args.agents_template_source)
    print(f"Evaluating {args.skill_source} at {source.revision}")
    manifest = write_experiment(
        jobs=args.jobs,
        samples=args.samples,
        agent=args.agent,
        source=source,
        agents_template=agents_template,
        agents_template_source=args.agents_template_source,
        scenarios=tuple(args.scenarios) if args.scenarios else None,
    )
    exit_code = run_eval(
        build_command(
            manifest,
            args.results_file,
            args.agent,
            list_only=args.list,
        ),
        ROOT,
    )
    if exit_code or args.publish_output is None:
        return exit_code
    if args.list or args.samples != SAMPLES or args.scenarios:
        raise ValueError("--publish-output requires the complete production matrix")
    report_dirs = sorted(
        (ROOT / "tests/eval/reports").glob("*-skill-guidance-efficiency-ab"),
        key=lambda path: path.stat().st_mtime,
    )
    if not report_dirs:
        raise RuntimeError("successful evaluation did not create a report directory")
    publish_command = [
        sys.executable,
        str(ROOT / "scripts/publish_eval_report.py"),
        "--run", str(report_dirs[-1]),
        "--manifest", str(manifest),
        "--report", str(args.results_file),
        "--output", str(args.publish_output),
    ]
    return run_eval(publish_command, ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
