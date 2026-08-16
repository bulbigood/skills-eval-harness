"""Fail-closed publication of verified Harbor reports and their sealed evidence."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from .bundle import validate_run_bundle
from .hashing import atomic_write, sha256_bytes
from .models import validate_run_id
from .provenance import Provenance
from .reporting import render_human_sections
from .telemetry import validate_device_telemetry


def canonical_repository(root: Path) -> str:
    completed = subprocess.run(
        ["git", "remote", "get-url", "origin"],
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
        raise ValueError("publication repository must be a GitHub HTTPS or SSH URL")
    return url


def _skill_metadata(run_dir: Path) -> dict[str, str]:
    skill_file = run_dir / "inputs/selected-skill/SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("selected skill must have YAML frontmatter")
    frontmatter = yaml.safe_load(text.split("\n---\n", 1)[0][4:])
    if not isinstance(frontmatter, dict):
        raise ValueError("selected skill frontmatter must be an object")
    name = frontmatter.get("name")
    metadata = frontmatter.get("metadata", {})
    version = metadata.get("version") if isinstance(metadata, dict) else None
    if not isinstance(name, str) or not name or not isinstance(version, str) or not version:
        raise ValueError("selected skill frontmatter requires string name and version")
    return {"name": name, "version": version}


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
    raw_index = subprocess.run(
        ["git", "rev-parse", "--git-path", "index"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    index = (root / raw_index).resolve() if not Path(raw_index).is_absolute() else Path(raw_index)
    initial = index.read_bytes() if index.exists() else None
    temporary_index = index.with_name(f".{index.name}.publication-{os.getpid()}")
    index_lock = index.with_name(f"{index.name}.lock")
    environment = {**os.environ, "GIT_INDEX_FILE": str(temporary_index)}
    try:
        if initial is None:
            head_exists = subprocess.run(
                ["git", "rev-parse", "--verify", "HEAD"],
                cwd=root,
                capture_output=True,
            ).returncode == 0
            subprocess.run(
                ["git", "read-tree", "HEAD"] if head_exists else ["git", "read-tree", "--empty"],
                cwd=root,
                env=environment,
                check=True,
                capture_output=True,
            )
        else:
            temporary_index.write_bytes(initial)
        subprocess.run(
            ["git", "add", "--", *relative],
            cwd=root,
            env=environment,
            check=True,
            capture_output=True,
        )
        lock_fd = os.open(index_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            current = index.read_bytes() if index.exists() else None
            if current != initial:
                raise RuntimeError("Git index changed concurrently during publication")
            os.replace(temporary_index, index)
        finally:
            os.close(lock_fd)
            index_lock.unlink(missing_ok=True)
    finally:
        temporary_index.unlink(missing_ok=True)


def publish(*, root: Path, run_dir: Path, output: Path, include_evidence: bool = False) -> Path:
    summary = validate_run_bundle(run_dir, require_seal=True)
    telemetry = validate_device_telemetry(run_dir / "device-telemetry.json")
    if (
        telemetry.schema_version != 2
        or telemetry.terminal_status != "completed"
        or telemetry.sampling_errors != 0
    ):
        raise ValueError("publication requires complete healthy schema-v2 telemetry")
    manifest = json.loads((run_dir / "run-manifest.json").read_text(encoding="utf-8"))
    run_id = validate_run_id(manifest.get("run_id"))
    provenance = Provenance.model_validate_json(
        (run_dir / "provenance.json").read_text(encoding="utf-8")
    ).validated()
    if provenance.harness_dirty:
        raise ValueError("publication requires a clean harness commit")
    if summary.get("valid") is not True:
        raise ValueError("publication requires complete structurally valid evidence")
    if summary.get("observed_cells") != summary.get("expected_cells"):
        raise ValueError("publication rejects incomplete runs")
    if (
        manifest.get("run_purpose") != "production"
        or manifest.get("samples") != manifest.get("suite_default_samples")
    ):
        raise ValueError("publication requires a production run at the exact preregistered sample count")

    output = output.resolve()
    root = root.resolve()
    evidence_dir = output.with_suffix(".evidence")
    checksum = output.with_suffix(output.suffix + ".sha256")
    if output.exists() or checksum.exists() or (include_evidence and evidence_dir.exists()):
        raise FileExistsError("refusing to replace an existing publication")
    if not output.is_relative_to(root):
        raise ValueError("publication outputs must be inside the Git repository")
    output.parent.mkdir(parents=True, exist_ok=True)

    repository = canonical_repository(root)
    samples = telemetry.samples
    telemetry_summary = {
        "schema_version": telemetry.schema_version,
        "scope": getattr(telemetry.host, "telemetry_scope", "whole-host"),
        "network_scope": telemetry.host.network_scope,
        "disk_scope": telemetry.host.disk_scope,
        "rootfs_scope": telemetry.host.filesystem_scope,
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
    if telemetry.schema_version == 2:
        telemetry_summary.update({
            "terminal_status": telemetry.terminal_status,
            "sampling_errors": telemetry.sampling_errors,
            "network_rx_bytes_per_second_max": telemetry.peaks.network_rx_bytes_per_second,
            "network_tx_bytes_per_second_max": telemetry.peaks.network_tx_bytes_per_second,
            "disk_read_bytes_per_second_max": telemetry.peaks.disk_read_bytes_per_second,
            "disk_write_bytes_per_second_max": telemetry.peaks.disk_write_bytes_per_second,
            "rootfs_used_bytes_max": telemetry.peaks.rootfs_used_bytes,
            "rootfs_free_bytes_min": telemetry.minima.rootfs_free_bytes,
            "network_rx_bytes_total": telemetry.totals.network_rx_bytes,
            "network_tx_bytes_total": telemetry.totals.network_tx_bytes,
            "disk_read_bytes_total": telemetry.totals.disk_read_bytes,
            "disk_write_bytes_total": telemetry.totals.disk_write_bytes,
        })
    telemetry_json = json.dumps(telemetry_summary, ensure_ascii=False, sort_keys=True, indent=2)
    suite_kind = manifest.get("suite", {}).get("kind", "single")
    context: dict[str, object] = {"suite_kind": suite_kind}
    if suite_kind == "paired":
        skill_metadata = _skill_metadata(run_dir)
        frozen_config = yaml.safe_load((run_dir / "inputs/config.yaml").read_text(encoding="utf-8"))
        agent_config = frozen_config.get("agents", {}).get(manifest["agent"], {})
        context.update({
            "skill_name": skill_metadata["name"],
            "skill_version": skill_metadata["version"],
            "skill_url": provenance.source_url,
            "skill_source_commit": provenance.source_commit,
            "skill_sha256": provenance.selected_skill_sha256,
            "agent_name": manifest["agent"],
            "agent_version": manifest["agent_version"],
            "agent_model": agent_config.get("model", "unknown"),
            "worker_reasoning": agent_config.get(
                "reasoning", "unset in sealed configuration; effective value unknown and not independently reproducible"
            ),
            "judge_model": frozen_config.get("judge", {}).get("model", "not recorded"),
            "judge_reasoning": frozen_config.get("judge", {}).get(
                "reasoning", "not recorded"
            ),
            "runtime_name": "IWE",
            "runtime_version": provenance.runtime_version,
            "runtime_sha256": provenance.runtime_sha256,
            "agent_image_sha256": provenance.image_digests["agent"],
        })
    human_sections = render_human_sections(summary, context=context)
    evidence_line = (
        f"- Sealed evidence: [`{evidence_dir.name}`]({evidence_dir.name}/run-seal.json)\n"
        if include_evidence
        else ""
    )
    suite_verdict_line = (
        "" if suite_kind == "paired"
        else f"- Overall suite verdict: **{'PASS' if summary.get('pass') is True else 'FAIL'}**\n"
    )
    revision_match = re.search(r"-v(\d+)$", output.stem)
    report_revision = f"v{revision_match.group(1)}" if revision_match else "unversioned"
    report = f"""# Evaluation report

- Run ID: `{run_id}`
- Report revision: `{report_revision}`
{suite_verdict_line}- Evaluation harness repository: [{repository}]({repository})
- Evaluation harness commit used for this run: [`{provenance.harness_commit}`]({repository}/commit/{provenance.harness_commit})
- Agent image SHA-256: `{provenance.image_digests['agent']}`
- Node version: `{manifest['node_version']}`
- Harbor version: `{provenance.harbor_version}`
- Complete cells: `{summary['observed_cells']}` / `{summary['expected_cells']}`
{evidence_line}

{human_sections}

## Sanitized device telemetry

<details>
<summary>Complete sanitized device telemetry</summary>

```json
{telemetry_json}
```

</details>

The report is derived from the bundled, sealed machine-readable evidence. Device telemetry is schema-constrained to numeric capacity and load measurements; hostnames, usernames, paths, environment variables, command lines, network identifiers, container names, labels, and credential material are not accepted.
"""

    lock_path = output.with_name(f".{output.name}.publish.lock")
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        temporary_root = Path(tempfile.mkdtemp(prefix=".publication-", dir=output.parent))
    except Exception:
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)
        raise
    temporary_evidence = temporary_root / evidence_dir.name
    temporary_output = temporary_root / output.name
    temporary_checksum = temporary_root / checksum.name
    created: list[Path] = []
    try:
        if include_evidence:
            temporary_evidence.mkdir(parents=True)
            for relative in _sealed_paths(run_dir):
                destination = temporary_evidence / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(run_dir / relative, destination)
            shutil.copy2(run_dir / "run-seal.json", temporary_evidence / "run-seal.json")
            validate_run_bundle(temporary_evidence, require_seal=True)
        atomic_write(temporary_output, report.encode())
        digest = sha256_bytes(report.encode())
        atomic_write(temporary_checksum, f"{digest}  {output.name}\n".encode())
        if include_evidence:
            temporary_evidence.rename(evidence_dir)
            created.append(evidence_dir)
        os.link(temporary_checksum, checksum)
        created.append(checksum)
        os.link(temporary_output, output)
        created.append(output)
        _stage(root, (output, checksum, *((evidence_dir,) if include_evidence else ())))
    except Exception:
        for path in reversed(created):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        raise
    finally:
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)
        shutil.rmtree(temporary_root, ignore_errors=True)
    return output
