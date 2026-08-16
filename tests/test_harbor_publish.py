from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from skills_eval_harness.publish import _skill_metadata, publish
from skills_eval_harness.hashing import sha256_file
from skills_eval_harness.provenance import Provenance, seal_run, verify_run_seal
from skills_eval_harness.telemetry import validate_device_telemetry


SHA = "a" * 64
COMMIT = "b" * 40


@pytest.fixture(autouse=True)
def validate_seal_and_return_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    def validate(run_dir: Path, *, require_seal: bool) -> dict:
        if require_seal:
            verify_run_seal(run_dir)
        return json.loads((run_dir / "summary.json").read_text())
    monkeypatch.setattr("skills_eval_harness.publish.validate_run_bundle", validate)


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def provenance(dirty: bool = False) -> Provenance:
    return Provenance(
        source_url="https://github.com/acme/skills/tree/" + COMMIT + "/skills/demo",
        source_commit=COMMIT,
        source_tree_sha256=SHA,
        selected_skill="demo",
        selected_skill_sha256=SHA,
        selected_skill_harbor_sha256=SHA,
        runtime_version="1.2.3",
        runtime_sha256=SHA,
        harness_commit=COMMIT,
        harness_tree_sha256=SHA,
        harness_dirty=dirty,
        suite_sha256=SHA,
        effective_suite_sha256=SHA,
        scenario_catalog_sha256=SHA,
        config_sha256=SHA,
        fixture_registry_sha256=SHA,
        harbor_version="0.21.0",
        node_version="22.23.2",
        agent_versions={"codex": "0.147.0", "claude": "2.1.233"},
        task_checksums={"task": SHA},
        image_digests={"agent": SHA},
        fixture_sources={"fixture": {"repository": "https://github.com/acme/fixture", "commit": COMMIT, "tree": COMMIT, "payload_sha256": SHA}},
    )


def test_skill_metadata_reads_nested_version(tmp_path: Path) -> None:
    skill = tmp_path / "inputs/selected-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: iwe-v18\nmetadata:\n  version: \"0.9.9\"\n---\nbody\n"
    )
    assert _skill_metadata(tmp_path) == {"name": "iwe-v18", "version": "0.9.9"}


def setup(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    run = root / "run"
    run.mkdir(parents=True)
    git(root, "init")
    git(root, "remote", "add", "origin", "https://github.com/bulbigood/skills-eval-harness.git")
    (run / "summary.json").write_text(json.dumps({"valid": True, "pass": True, "expected_cells": 1, "observed_cells": 1}))
    (run / "provenance.json").write_text(provenance().model_dump_json())
    (run / "run-manifest.json").write_text(json.dumps({"run_id": "canonical-production-run", "run_purpose": "production", "agent": "codex", "agent_version": "0.147.0", "node_version": "22.23.2", "samples": 10, "suite_default_samples": 10}))
    (run / "jobs/job/trial/agent").mkdir(parents=True)
    (run / "jobs/job/trial/verifier").mkdir(parents=True)
    (run / "jobs/job/lock.json").write_text("{}")
    (run / "jobs/job/result.json").write_text("{}")
    (run / "jobs/job/trial/agent/trajectory.json").write_text("{}")
    (run / "jobs/job/trial/verifier/oracle.json").write_text("{}")
    (run / "jobs/job/trial/verifier/mechanical.json").write_text("{}")
    (run / "jobs/job/trial/verifier/workspace-manifest.json").write_text("{}")
    (run / "jobs/job/trial/verifier/test-stdout.txt").write_text("ok")
    (run / "jobs/job/trial/verifier/test-stderr.txt").write_text("")
    (run / "inputs").mkdir()
    for name in ("config.yaml", "scenario-catalog.yaml", "suite.yaml", "effective-suite.json", "fixture-sources.json"):
        (run / "inputs" / name).write_text("{}")
    for name in ("runtime", "source-commit-object", "harness-commit-object"):
        (run / "inputs" / name).write_bytes(b"fixture")
    (run / "inputs/fixture-commit-objects").mkdir()
    (run / "inputs/fixture-commit-objects/fixture").write_bytes(b"fixture commit")
    (run / "datasets/arm/task/tests").mkdir(parents=True)
    (run / "datasets/arm/task/task.toml").write_text("version = '1.0'")
    (run / "datasets/arm/task/instruction.md").write_text("task")
    (run / "datasets/arm/task/tests/verify.py").write_text("print('ok')")
    (run / "cells").mkdir()
    (run / "cells/arm--scenario--1.json").write_text(json.dumps({
        "evidence": [{"id": "E0001", "kind": "oracle", "text": "fact"}],
        "judge_messages": [{"role": "system", "content": "judge"}, {"role": "user", "content": "evidence"}],
        "verdict": {"dimensions": []},
    }))
    (run / "device-telemetry.json").write_text(json.dumps({
        "schema_version": 2,
        "started_unix_ms": 1000,
        "finished_unix_ms": 2000,
        "host": {
            "logical_cpus": 2, "total_memory_bytes": 4096, "total_swap_bytes": 0,
            "docker_metrics_available": True, "telemetry_scope": "whole-host",
            "network_scope": "default-route-interfaces", "disk_scope": "physical-block-devices",
            "filesystem_scope": "root-filesystem",
        },
        "samples": [{
            "elapsed_ms": 0, "cpu_percent": 25.0, "load1": 0.5,
            "mem_available_bytes": 2048, "swap_free_bytes": 0, "running_containers": 2,
            "network_rx_bytes": 100, "network_tx_bytes": 200,
            "disk_read_bytes": 300, "disk_write_bytes": 400,
            "network_rx_bytes_per_second": 0.0, "network_tx_bytes_per_second": 0.0,
            "disk_read_bytes_per_second": 0.0, "disk_write_bytes_per_second": 0.0,
            "rootfs_used_bytes": 1000, "rootfs_free_bytes": 2000,
        }],
        "peaks": {
            "cpu_percent": 25.0, "load1": 0.5, "running_containers": 2,
            "network_rx_bytes_per_second": 0.0, "network_tx_bytes_per_second": 0.0,
            "disk_read_bytes_per_second": 0.0, "disk_write_bytes_per_second": 0.0,
            "rootfs_used_bytes": 1000,
        },
        "minima": {"mem_available_bytes": 2048, "swap_free_bytes": 0, "rootfs_free_bytes": 2000},
        "totals": {"network_rx_bytes": 0, "network_tx_bytes": 0, "disk_read_bytes": 0, "disk_write_bytes": 0},
        "docker_oom_events": 0, "sampling_errors": 0, "terminal_status": "completed",
    }))
    seal_run(run)
    return root, run


def test_seal_rejects_omitted_required_file(tmp_path: Path) -> None:
    _, run = setup(tmp_path)
    seal = json.loads((run / "run-seal.json").read_text())
    del seal["files"]["inputs/runtime"]
    (run / "run-seal.json").write_text(json.dumps(seal))
    with pytest.raises(ValueError, match="incomplete|exact publication payload"):
        verify_run_seal(run)


def test_publisher_defaults_to_report_without_evidence(tmp_path: Path) -> None:
    root, run = setup(tmp_path)
    renamed = root / "arbitrary-relocated-bundle-name"
    run.rename(renamed)
    output = root / "reports" / "published.md"
    publish(root=root, run_dir=renamed, output=output)
    text = output.read_text()
    assert text.startswith("# Evaluation report\n")
    assert "- Run ID: `canonical-production-run`" in text
    assert "- Report revision: `unversioned`" in text
    assert "Overall suite verdict: **PASS**" in text
    assert "https://github.com/bulbigood/skills-eval-harness" in text
    assert "Sealed evidence" not in text
    assert "<summary>Complete sanitized device telemetry</summary>" in text
    assert '\n  "cpu_percent_max":' in text
    assert '"p50"' not in text
    assert "median" not in text.lower()
    assert output.with_suffix(".md.sha256").is_file()
    assert not output.with_suffix(".evidence").exists()
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    assert set(staged) == {"reports/published.md", "reports/published.md.sha256"}


def test_publisher_can_include_revalidated_evidence(tmp_path: Path) -> None:
    root, run = setup(tmp_path)
    output = root / "published.md"
    publish(root=root, run_dir=run, output=output, include_evidence=True)
    text = output.read_text()
    assert "Sealed evidence" in text
    evidence = root / "published.evidence"
    assert (evidence / "summary.json").is_file()
    assert (evidence / "cells/arm--scenario--1.json").is_file()
    assert (evidence / "jobs/job/lock.json").is_file()
    assert (evidence / "device-telemetry.json").is_file()
    seal = json.loads((run / "run-seal.json").read_text())
    assert all(
        (evidence / relative).is_file() and sha256_file(evidence / relative) == digest
        for relative, digest in seal["files"].items()
    )
    assert (evidence / "run-seal.json").is_file()
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=root, text=True, capture_output=True, check=True).stdout.splitlines()
    assert set(staged) >= {
        "published.md",
        "published.md.sha256",
        "published.evidence/summary.json",
        "published.evidence/device-telemetry.json",
    }


def test_publisher_rejects_failed_incomplete_dirty_or_overwrite(tmp_path: Path) -> None:
    root, run = setup(tmp_path)
    output = root / "published.md"
    summary = {"valid": True, "pass": False, "expected_cells": 1, "observed_cells": 1}
    (run / "summary.json").write_text(json.dumps(summary))
    seal_run(run)
    publish(root=root, run_dir=run, output=output)
    assert "Overall suite verdict: **FAIL**" in output.read_text()
    output.unlink()
    output.with_suffix(".md.sha256").unlink()
    subprocess.run(["git", "reset", "-q"], cwd=root, check=True)
    (run / "summary.json").write_text(json.dumps({**summary, "pass": True, "observed_cells": 0}))
    seal_run(run)
    with pytest.raises(ValueError, match="incomplete"):
        publish(root=root, run_dir=run, output=output)
    (run / "summary.json").write_text(json.dumps({**summary, "pass": True}))
    (run / "provenance.json").write_text(provenance(True).model_dump_json())
    seal_run(run)
    with pytest.raises(ValueError, match="clean"):
        publish(root=root, run_dir=run, output=output)


def test_publisher_rejects_tampered_sealed_artifact(tmp_path: Path) -> None:
    root, run = setup(tmp_path)
    (run / "summary.json").write_text(json.dumps({"valid": True, "pass": False, "expected_cells": 1, "observed_cells": 1}))
    with pytest.raises(ValueError, match="sealed artifact mismatch"):
        publish(root=root, run_dir=run, output=root / "published.md")


def test_device_telemetry_rejects_sensitive_or_unexpected_fields(tmp_path: Path) -> None:
    _, run = setup(tmp_path)
    telemetry = run / "device-telemetry.json"
    payload = json.loads(telemetry.read_text())
    validate_device_telemetry(telemetry)
    payload["host"]["hostname"] = "private-runner-01"
    telemetry.write_text(json.dumps(payload))
    seal_run(run)
    with pytest.raises(ValueError, match="device telemetry"):
        validate_device_telemetry(telemetry)


def test_publisher_requires_healthy_current_telemetry_and_releases_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, run = setup(tmp_path)
    output = root / "published.md"
    telemetry = run / "device-telemetry.json"
    payload = json.loads(telemetry.read_text())
    payload["terminal_status"] = "failed"
    telemetry.write_text(json.dumps(payload))
    seal_run(run)
    with pytest.raises(ValueError, match="healthy schema-v2"):
        publish(root=root, run_dir=run, output=output)

    payload["terminal_status"] = "completed"
    telemetry.write_text(json.dumps(payload))
    seal_run(run)
    monkeypatch.setattr("skills_eval_harness.publish.tempfile.mkdtemp", lambda **_: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError, match="disk"):
        publish(root=root, run_dir=run, output=output)
    assert not (root / ".published.md.publish.lock").exists()
