#!/usr/bin/env python3
"""Publish a reviewed evaluation Markdown report with pinned provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE_KEYS = ("skill_source", "source_revision", "source_payload_sha256", "selected_skill")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="completed raw report directory")
    parser.add_argument("--manifest", type=Path, required=True, help="exact generated experiment manifest used by the run")
    parser.add_argument("--report", type=Path, required=True, help="generated Markdown report for the same run")
    parser.add_argument("--output", type=Path, required=True, help="tracked publication path under docs/evals/results")
    parser.add_argument("--harness-commit", help="exact harness commit used for a historical run; defaults to HEAD")
    parser.add_argument("--replace", action="store_true", help="replace an existing publication")
    return parser.parse_args(argv)


def _inside(path: Path, parent: Path, label: str) -> Path:
    resolved = path if path.is_absolute() else ROOT / path
    resolved = resolved.resolve()
    if not resolved.is_relative_to(parent.resolve()):
        raise ValueError(f"{label} must be under {parent}")
    return resolved


def _manifest_provenance(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for key in PROVENANCE_KEYS:
        match = re.search(rf"^# {key} = (.+)$", text, re.MULTILINE)
        if not match:
            raise ValueError(f"manifest lacks {key} provenance")
        value = json.loads(match.group(1))
        if not isinstance(value, str) or not value:
            raise ValueError(f"manifest has invalid {key} provenance")
        values[key] = value
    revision = values["source_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("source_revision must be a full Git commit")
    source = values["skill_source"]
    if f"/tree/{revision}/" not in source:
        raise ValueError("skill_source must pin source_revision in a GitHub tree URL")
    if not re.fullmatch(r"[0-9a-f]{64}", values["source_payload_sha256"]):
        raise ValueError("source_payload_sha256 must be SHA-256")
    return values


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _validate_run(run: Path, manifest: Path) -> tuple[dict, dict, list[Path]]:
    experiment = _load_json(run / "experiment.json")
    summary = _load_json(run / "summary.json")
    if experiment.get("name") != summary.get("experiment"):
        raise ValueError("run experiment and summary identities differ")
    manifest_text = manifest.read_text(encoding="utf-8")
    name_match = re.search(r'^name = "([^"]+)"$', manifest_text, re.MULTILINE)
    if not name_match or name_match.group(1) != experiment.get("name"):
        raise ValueError("manifest does not describe the selected run")
    targets = [item["id"] for item in experiment["targets"]]
    scenarios = list(experiment["scenarios"])
    samples = int(experiment["samples"])
    expected = {(target, scenario, sample) for target in targets for scenario in scenarios for sample in range(1, samples + 1)}
    files = sorted(run.glob("targets/*/*--*.json"))
    observed: set[tuple[str, str, int]] = set()
    for path in files:
        raw = _load_json(path)
        identity = (str(raw.get("target_id")), str(raw.get("scenario_id")), int(raw.get("sample", 0)))
        if identity in observed:
            raise ValueError(f"duplicate raw sample identity: {identity}")
        observed.add(identity)
        verdict = raw.get("verdict", {})
        if not verdict.get("valid"):
            raise ValueError(f"invalid sample cannot be published: {identity}")
    if observed != expected:
        raise ValueError(f"incomplete run: expected {len(expected)} cells, observed {len(observed)}")
    outcomes = summary.get("scenarios", [])
    if len(outcomes) != len(targets) * len(scenarios):
        raise ValueError("aggregate summary is incomplete")
    failed = [item for item in outcomes if not item.get("pass")]
    if failed:
        raise ValueError(f"aggregate run is not green: {len(failed)} failed rows")
    return experiment, summary, files


def _git_commit(value: str | None) -> str:
    commit = value or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("harness commit must be a full Git commit")
    subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=ROOT, check=True, capture_output=True)
    return commit


def _sanitize_report(text: str, run_id: str) -> str:
    text = re.sub(
        r"- Telemetry: \[raw sample JSON\]\([^\n]+\)",
        f"- Telemetry: raw sample JSON retained locally with run `{run_id}` (not published).",
        text,
    )
    text = re.sub(
        r"\[Machine-readable report directory\]\([^\n]+\)",
        f"The machine-readable report directory is retained locally at `tests/eval/reports/{run_id}` and is intentionally not published because raw reports can contain complete prompts, transcripts, workspace content, and local paths.",
        text,
    )
    if re.search(r"\]\([^)]*tests/eval/reports/|\]\(\.\./reports/", text):
        raise ValueError("published report still links to private raw telemetry")
    if str(ROOT) in text:
        raise ValueError("published report contains the local repository path")
    return text


def _source_repository(source: str) -> str:
    match = re.match(r"(https://github\.com/[^/]+/[^/]+)/tree/[0-9a-f]{40}/", source)
    if not match:
        raise ValueError("skill_source is not a supported pinned GitHub tree URL")
    return match.group(1)


def publish(args: argparse.Namespace) -> Path:
    reports_root = ROOT / "tests/eval/reports"
    run = _inside(args.run, reports_root, "run")
    output = _inside(args.output, ROOT / "docs/evals/results", "output")
    manifest = _inside(args.manifest, ROOT, "manifest")
    report = _inside(args.report, ROOT, "report")
    if output.exists() and not args.replace:
        raise FileExistsError(f"publication already exists: {output}; pass --replace explicitly")
    provenance = _manifest_provenance(manifest)
    source_repository = _source_repository(provenance["skill_source"])
    experiment, _, files = _validate_run(run, manifest)
    harness_commit = _git_commit(args.harness_commit)
    agents = [target.get("agents_file_provenance") for target in experiment["targets"] if target.get("agents_file_provenance")]
    agents_lines = "\n".join(
        f"- AGENTS.md payload: SHA-256 `{item['sha256']}` ({item['bytes']} bytes)"
        for item in {json.dumps(item, sort_keys=True): item for item in agents}.values()
    ) or "- AGENTS.md payload: not part of this suite"
    body = _sanitize_report(report.read_text(encoding="utf-8"), run.name)
    header = f"""<!-- Selected evidence report. Generated body; provenance header verified by scripts/publish_eval_report.py. -->

# Evidence report — {experiment['name']}

## Evaluated source

- Overall suite verdict: **PASS**
- Source: [{provenance['skill_source']}]({provenance['skill_source']})
- Source repository: `{source_repository}`
- Source commit: `{provenance['source_revision']}`
- Selected skill: `{provenance['selected_skill']}`
- Source payload SHA-256: `{provenance['source_payload_sha256']}`
{agents_lines}
- Harness repository: `https://github.com/bulbigood/skills-eval-harness`
- Harness commit: `{harness_commit}`
- Run ID: `{run.name}`
- Matrix: `{len(experiment['targets'])}` target(s) × `{len(experiment['scenarios'])}` scenarios × `{experiment['samples']}` samples = `{len(files)}` worker and `{len(files)}` judge cells
- Raw telemetry: retained locally and intentionally not published

"""
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(header + body, encoding="utf-8")
    temporary.replace(output)
    return output


def main(argv: list[str] | None = None) -> int:
    try:
        output = publish(parse_args(argv))
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"publish failed: {exc}", file=sys.stderr)
        return 1
    print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
