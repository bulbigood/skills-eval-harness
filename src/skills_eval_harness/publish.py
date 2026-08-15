"""Fail-closed publication of verified Harbor reports and their sealed evidence."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .hashing import atomic_write, canonical_json, sha256_bytes
from .provenance import Provenance, verify_run_seal
from .telemetry import validate_device_telemetry


def canonical_repository(root: Path) -> str:
    completed = subprocess.run(
        ["git", "remote", "get-url", "upstream"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    url = completed.stdout.strip()
    if url.endswith(".git"):
        url = url[:-4]
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url.removeprefix("git@github.com:")
    if not url.startswith("https://github.com/"):
        raise ValueError("canonical upstream must be a GitHub HTTPS or SSH URL")
    return url


def _sealed_paths(run_dir: Path) -> tuple[Path, ...]:
    seal = json.loads((run_dir / "run-seal.json").read_text(encoding="utf-8"))
    files = seal.get("files")
    if not isinstance(files, dict):
        raise ValueError("invalid run seal")
    relative_paths: list[Path] = []
    for raw in sorted(files):
        relative = Path(raw)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe sealed artifact path: {raw}")
        relative_paths.append(relative)
    return tuple(relative_paths)


def _stage(root: Path, paths: tuple[Path, ...]) -> None:
    relative: list[str] = []
    resolved_root = root.resolve()
    for path in paths:
        resolved = path.resolve()
        if not resolved.is_relative_to(resolved_root):
            raise ValueError("publication outputs must be inside the Git repository")
        relative.append(str(resolved.relative_to(resolved_root)))
    subprocess.run(["git", "add", "--", *relative], cwd=root, check=True, capture_output=True)


def _validate_evidence_cells(run_dir: Path, expected: int) -> None:
    paths = sorted((run_dir / "cells").glob("*.json"))
    if len(paths) != expected:
        raise ValueError("sealed evidence cell count does not match summary")
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        evidence = document.get("evidence") if isinstance(document, dict) else None
        messages = document.get("judge_messages") if isinstance(document, dict) else None
        verdict = document.get("verdict") if isinstance(document, dict) else None
        if not isinstance(evidence, list) or not evidence or not isinstance(messages, list) or len(messages) != 2 or not isinstance(verdict, dict):
            raise ValueError("sealed evidence cell omits judge inputs or output")


def publish(*, root: Path, run_dir: Path, output: Path) -> Path:
    verify_run_seal(run_dir)
    telemetry = validate_device_telemetry(run_dir / "device-telemetry.json")
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    provenance = Provenance.model_validate_json(
        (run_dir / "provenance.json").read_text(encoding="utf-8")
    ).validated()
    if provenance.harness_dirty:
        raise ValueError("publication requires a clean harness commit")
    if summary.get("valid") is not True or summary.get("pass") is not True:
        raise ValueError("publication requires a complete valid passing run")
    if summary.get("observed_cells") != summary.get("expected_cells"):
        raise ValueError("publication rejects incomplete runs")
    _validate_evidence_cells(run_dir, int(summary["expected_cells"]))

    output = output.resolve()
    root = root.resolve()
    evidence_dir = output.with_suffix(".evidence")
    checksum = output.with_suffix(output.suffix + ".sha256")
    if output.exists() or checksum.exists() or evidence_dir.exists():
        raise FileExistsError("refusing to replace an existing publication")
    if not output.is_relative_to(root):
        raise ValueError("publication outputs must be inside the Git repository")

    repository = canonical_repository(root)
    statistics_json = canonical_json(
        {"statistics": summary.get("statistics", {}), "timing": summary.get("timing", {})}
    ).decode()
    samples = telemetry.samples
    telemetry_summary = {
        "logical_cpus": telemetry.host.logical_cpus,
        "total_memory_bytes": telemetry.host.total_memory_bytes,
        "total_swap_bytes": telemetry.host.total_swap_bytes,
        "sample_count": len(samples),
        "cpu_percent_max": max(sample.cpu_percent for sample in samples),
        "load1_max": max(sample.load1 for sample in samples),
        "mem_available_bytes_min": min(sample.mem_available_bytes for sample in samples),
        "swap_free_bytes_min": min(sample.swap_free_bytes for sample in samples),
        "running_containers_max": max(sample.running_containers for sample in samples),
        "docker_oom_events": telemetry.docker_oom_events,
    }
    telemetry_json = canonical_json(telemetry_summary).decode()
    evidence_link = evidence_dir.name
    report = f"""# {run_dir.name}

- Overall suite verdict: **PASS**
- Harness repository: [{repository}]({repository})
- Harness commit: `{provenance.harness_commit}`
- Source: [{provenance.source_url}]({provenance.source_url})
- Source commit: `{provenance.source_commit}`
- Selected skill SHA-256: `{provenance.selected_skill_sha256}`
- Runtime version: `{provenance.runtime_version}`
- Runtime SHA-256: `{provenance.runtime_sha256}`
- Harbor version: `{provenance.harbor_version}`
- Complete cells: `{summary['observed_cells']}` / `{summary['expected_cells']}`
- Sealed evidence: [`{evidence_link}`]({evidence_link}/run-seal.json)

## Verified statistics

```json
{statistics_json}
```

## Sanitized device telemetry

```json
{telemetry_json}
```

The report is derived from the bundled, sealed machine-readable evidence. Device telemetry is schema-constrained to numeric capacity and load measurements; hostnames, usernames, paths, environment variables, command lines, network identifiers, container names, labels, and credential material are not accepted.
"""

    evidence_dir.mkdir(parents=True)
    for relative in _sealed_paths(run_dir):
        destination = evidence_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(run_dir / relative, destination)
    shutil.copy2(run_dir / "run-seal.json", evidence_dir / "run-seal.json")
    atomic_write(output, report.encode())
    digest = sha256_bytes(report.encode())
    atomic_write(checksum, f"{digest}  {output.name}\n".encode())
    _stage(root, (output, checksum, evidence_dir))
    return output
