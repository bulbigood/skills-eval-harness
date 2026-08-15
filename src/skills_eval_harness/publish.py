"""Fail-closed publication of verified Harbor summaries."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .hashing import atomic_write, canonical_json, sha256_bytes
from .provenance import Provenance, verify_run_seal


def canonical_repository(root: Path) -> str:
    completed = subprocess.run(["git", "remote", "get-url", "upstream"], cwd=root, text=True, capture_output=True, check=True)
    url = completed.stdout.strip()
    if url.endswith(".git"):
        url = url[:-4]
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url.removeprefix("git@github.com:")
    if not url.startswith("https://github.com/"):
        raise ValueError("canonical upstream must be a GitHub HTTPS or SSH URL")
    return url


def publish(*, root: Path, run_dir: Path, output: Path) -> Path:
    verify_run_seal(run_dir)
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    provenance = Provenance.model_validate_json((run_dir / "provenance.json").read_text(encoding="utf-8")).validated()
    if provenance.harness_dirty:
        raise ValueError("publication requires a clean harness commit")
    if summary.get("valid") is not True or summary.get("pass") is not True:
        raise ValueError("publication requires a complete valid passing run")
    if summary.get("observed_cells") != summary.get("expected_cells"):
        raise ValueError("publication rejects incomplete runs")
    repository = canonical_repository(root)
    statistics_json = canonical_json({"statistics": summary.get("statistics", {}), "timing": summary.get("timing", {})}).decode()
    report = f"""# {run_dir.name}\n\n- Overall suite verdict: **PASS**\n- Harness repository: [{repository}]({repository})\n- Harness commit: `{provenance.harness_commit}`\n- Source: [{provenance.source_url}]({provenance.source_url})\n- Source commit: `{provenance.source_commit}`\n- Selected skill SHA-256: `{provenance.selected_skill_sha256}`\n- Runtime version: `{provenance.runtime_version}`\n- Runtime SHA-256: `{provenance.runtime_sha256}`\n- Harbor version: `{provenance.harbor_version}`\n- Complete cells: `{summary['observed_cells']}` / `{summary['expected_cells']}`\n\n## Verified statistics\n\n```json\n{statistics_json}\n```\n\nThe verdict above is derived from the validated machine-readable summary; it is not supplied by the caller.\n"""
    if output.exists():
        raise FileExistsError("refusing to replace an existing publication")
    atomic_write(output, report.encode())
    digest = sha256_bytes(report.encode())
    atomic_write(output.with_suffix(output.suffix + ".sha256"), f"{digest}  {output.name}\n".encode())
    return output
