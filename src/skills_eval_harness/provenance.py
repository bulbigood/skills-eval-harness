"""Content-bound provenance records and fail-closed reconciliation."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .hashing import atomic_write_json, sha256_file, sha256_tree

SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_url: str
    source_commit: str
    source_tree_sha256: str
    selected_skill: str
    selected_skill_sha256: str
    runtime_version: str
    runtime_sha256: str
    harness_commit: str
    harness_dirty: bool
    suite_sha256: str
    effective_suite_sha256: str
    scenario_catalog_sha256: str
    config_sha256: str
    harbor_version: Literal["0.21.0"]
    task_checksums: dict[str, str]
    image_digests: dict[str, str]
    agents_template_sha256: str | None = None
    worker_auth_mode: Literal["api-key", "chatgpt"] = "api-key"
    judge_auth_mode: Literal["api-key", "chatgpt"] = "api-key"

    def validated(self) -> "Provenance":
        if not COMMIT.fullmatch(self.source_commit) or not COMMIT.fullmatch(self.harness_commit):
            raise ValueError("source and harness revisions must be full Git commits")
        hashes = (
            self.source_tree_sha256,
            self.selected_skill_sha256,
            self.runtime_sha256,
            self.suite_sha256,
            self.effective_suite_sha256,
            self.scenario_catalog_sha256,
            self.config_sha256,
            *self.task_checksums.values(),
            *self.image_digests.values(),
        )
        if self.agents_template_sha256 is not None and not SHA256.fullmatch(self.agents_template_sha256):
            raise ValueError("AGENTS template digest must be lowercase SHA-256")

        if not hashes or any(not SHA256.fullmatch(value) for value in hashes):
            raise ValueError("all provenance digests must be lowercase SHA-256")
        return self


def verify_materialized(
    provenance: Provenance,
    *,
    source_root: Path,
    skill_root: Path,
    runtime: Path,
    suite: Path,
    scenarios: Path,
    config: Path,
) -> None:
    provenance.validated()
    actual = {
        "source_tree_sha256": sha256_tree(source_root),
        "selected_skill_sha256": sha256_tree(skill_root),
        "runtime_sha256": sha256_file(runtime),
        "suite_sha256": sha256_file(suite),
        "scenario_catalog_sha256": sha256_file(scenarios),
        "config_sha256": sha256_file(config),
    }
    expected = {key: getattr(provenance, key) for key in actual}
    mismatches = [
        f"{key}: expected {expected[key]}, got {actual[key]}"
        for key in actual
        if actual[key] != expected[key]
    ]
    if mismatches:
        raise ValueError("provenance mismatch: " + "; ".join(mismatches))


def verify_harbor_lock(provenance: Provenance, lock: dict) -> None:
    harbor = lock.get("harbor") or {}
    version = harbor.get("version") or lock.get("harbor_version") or lock.get("version")
    if lock.get("schema_version") != 3 or version != provenance.harbor_version:
        raise ValueError("unexpected Harbor lock schema or version")
    trials = lock.get("trials")
    if not isinstance(trials, list) or not trials:
        raise ValueError("Harbor lock has no trials")
    seen: set[str] = set()
    for trial in trials:
        task = trial.get("task") or {}
        name = task.get("name")
        source = task.get("source")
        digest = task.get("digest", "")
        key = f"{source}/{name}"
        if key in seen or key not in provenance.task_checksums:
            raise ValueError(f"unexpected or duplicate locked task: {key}")
        if not isinstance(digest, str) or not digest.startswith("sha256:") or not SHA256.fullmatch(digest.removeprefix("sha256:")):
            raise ValueError(f"invalid locked task digest: {key}")
        if digest.removeprefix("sha256:") != provenance.task_checksums[key]:
            raise ValueError(f"locked task digest mismatch: {key}")
        seen.add(key)
    locked_sources = {key.split("/", 1)[0] for key in seen}
    expected = {key for key in provenance.task_checksums if key.split("/", 1)[0] in locked_sources}
    if seen != expected:
        raise ValueError("Harbor lock is missing expected tasks")


def seal_run(run_dir: Path) -> dict[str, object]:
    """Hash every publishable result and Harbor lock; the seal excludes itself."""
    roots = [run_dir / "provenance.json", run_dir / "run-manifest.json", run_dir / "summary.json"]
    roots.extend(sorted((run_dir / "cells").glob("*.json")))
    roots.extend(sorted((run_dir / "jobs").glob("**/lock.json")))
    roots.extend(sorted((run_dir / "jobs").glob("**/result.json")))
    roots.extend(sorted((run_dir / "jobs").glob("**/trajectory.json")))
    roots.extend(sorted((run_dir / "jobs").glob("**/workspace-manifest.json")))
    roots.extend(sorted((run_dir / "jobs").glob("**/mechanical.json")))
    files = {str(path.relative_to(run_dir)): sha256_file(path) for path in roots if path.is_file()}
    if "provenance.json" not in files or "run-manifest.json" not in files or "summary.json" not in files or not any(name.endswith("/lock.json") for name in files):
        raise ValueError("cannot seal incomplete run")
    seal: dict[str, object] = {"schema_version": 1, "files": files}
    atomic_write_json(run_dir / "run-seal.json", seal)
    return seal


def verify_run_seal(run_dir: Path) -> None:
    seal = json.loads((run_dir / "run-seal.json").read_text(encoding="utf-8"))
    files = seal.get("files")
    if seal.get("schema_version") != 1 or not isinstance(files, dict):
        raise ValueError("invalid run seal")
    for relative, expected in files.items():
        path = run_dir / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"sealed artifact mismatch: {relative}")
