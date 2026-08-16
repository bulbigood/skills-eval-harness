from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from harbor.models.job.result import JobResult, TrialResult

from skills_eval_harness.bundle import validate_run_bundle
from skills_eval_harness.hashing import (
    atomic_write_json,
    git_tree_sha1,
    harbor_content_sha256,
    harbor_skill_sha256,
    sha256_file,
    sha256_tree,
)
from skills_eval_harness.judge import JudgeVerdict, build_evidence, build_judge_messages, derive_cell_outcome
from skills_eval_harness.models import AnalysisPlan, Suite
from skills_eval_harness.publish import publish
from skills_eval_harness.provenance import Provenance, seal_run, verify_run_seal
from skills_eval_harness.results import summarize_cells, trial_evidence
from skills_eval_harness.source import materialize_git_identity, write_git_commit_object
from skills_eval_harness.telemetry import validate_device_telemetry


SHA = "a" * 64
COMMIT = "b" * 40


@pytest.fixture
def mocked_validator(monkeypatch: pytest.MonkeyPatch) -> None:
    def validate(run_dir: Path, *, require_seal: bool) -> dict:
        if require_seal:
            verify_run_seal(run_dir)
        return json.loads((run_dir / "summary.json").read_text())
    monkeypatch.setattr("skills_eval_harness.publish.validate_run_bundle", validate)


def git(root: Path, *args: str) -> None:
    environment = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
    }
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, env=environment)


def commit_repository(root: Path, files: dict[str, str], remote: str) -> str:
    root.mkdir()
    git(root, "init", "-q")
    git(root, "remote", "add", "origin", remote)
    for relative, payload in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload)
    git(root, "add", ".")
    git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


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
        image_digests={"agent": SHA, "verifier": SHA},
        fixture_sources={"fixture": {"repository": "https://github.com/acme/fixture", "commit": COMMIT, "tree": COMMIT, "payload_sha256": SHA}},
    )


def setup(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    run = root / "run"
    run.mkdir(parents=True)
    git(root, "init")
    git(root, "remote", "add", "origin", "https://github.com/bulbigood/skills-eval-harness.git")
    summary = {
        "schema_version": 5, "valid": True, "pass": True, "expected_cells": 1, "observed_cells": 1,
        "analysis": {"kind": "absolute", "absolute": {"arm": "arm"}, "paired": None},
        "evaluation_status": {"evidence_integrity": "valid", "acceptance": {"applicable": True, "passed": True, "policy_id": "dimension-sample-rate-v1"}, "comparison": {"kind": "absolute", "superiority_verdict": None}},
        "acceptance": {"policy_id": "dimension-sample-rate-v1", "pass": True, "score_thresholds": {"safety": 5}, "sample_pass_rate_thresholds": {"safety": 1.0}, "criteria": []},
        "reliability": {"planned_cells_by_arm": {"arm": 1}, "valid_cells_by_arm": {"arm": 1}, "invalid_cells_by_arm": {"arm": 0}, "scenario_failures_by_arm": {"arm": 0}, "missingness_by_scenario": {}, "missingness_by_family": {}, "excluded_pairs": [], "common_valid_pairs": None, "planned_pairs": None},
        "statistics": {"available_valid": {"overall": {"arm": {"scores": {}}}, "per_scenario": {}, "per_family": {}}, "common_valid_paired": {}},
        "timing": {"available_valid_summed_cell_seconds": 1.0, "common_valid_summed_cell_seconds": None, "pipeline_elapsed_seconds": 2.0},
        "measurement_scope": {}, "interpretation": {}, "cells": [],
    }
    (run / "summary.json").write_text(json.dumps(summary))
    (run / "provenance.json").write_text(provenance().model_dump_json())
    suite = {"schema_version": 1, "id": "demo-suite", "kind": "absolute", "default_samples": 10, "scenarios": ["scenario"], "arms": [{"id": "arm", "skill": True, "role": None}]}
    (run / "run-manifest.json").write_text(json.dumps({"run_id": "canonical-production-run", "run_purpose": "production", "agent": "codex", "agent_version": "0.147.0", "node_version": "22.23.2", "samples": 10, "suite_default_samples": 10, "suite": suite}))
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
    (run / "inputs/config.yaml").write_text("agents:\n  codex:\n    model: openai/test\n    reasoning: high\njudge:\n  model: judge-test\n  reasoning: low\n")
    (run / "inputs/selected-skill").mkdir()
    (run / "inputs/selected-skill/SKILL.md").write_text("---\nname: demo\nmetadata:\n  version: '1.0.0'\n---\nbody\n")
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


def build_valid_current_bundle(tmp_path: Path) -> tuple[Path, Path]:
    """Build one complete production bundle without invoking Harbor, a worker, or a judge."""
    root = tmp_path / "publication-repository"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "remote", "add", "origin", "https://github.com/acme/evaluation-reports.git")
    run = root / "run"
    inputs = run / "inputs"
    inputs.mkdir(parents=True)

    runtime = inputs / "runtime"
    runtime.write_bytes(b"deterministic offline runtime\n")
    runtime_digest = sha256_file(runtime)
    image_digest = "1" * 64
    verifier_digest = "2" * 64
    suite = {
        "schema_version": 1,
        "id": "offline-suite",
        "kind": "absolute",
        "default_samples": 1,
        "scenarios": ["offline-read"],
        "arms": [{"id": "ordinary", "skill": False, "role": None}],
    }
    config_text = f"""schema_version: 1
harbor_version: 0.21.0
container:
  image: verifier@sha256:{verifier_digest}
  agent_image: agent
  agent_image_id: sha256:{image_digest}
  cpus: 1
  memory_mb: 256
  storage_mb: 1024
  node_version: 22.23.2
  network_mode: allowlist
  agent_hosts: {{codex: []}}
  verifier_network_mode: no-network
agents:
  codex: {{harbor_name: codex, model: offline-model, version: 0.147.0, credential_env: OPENAI_API_KEY, reasoning: low}}
  claude: {{harbor_name: claude-code, model: offline-model, version: 2.1.233, credential_env: ANTHROPIC_API_KEY, reasoning: low}}
judge: {{model: offline-judge, credential_env: OPENAI_API_KEY, reasoning: low, timeout_seconds: 1, concurrency: 1}}
execution: {{timeout_seconds: 1, global_concurrency: 1, retries: 0}}
runtimes: {{0.18.0: {runtime_digest}}}
skill_repositories: [https://github.com/acme/skills]
"""
    catalog_text = """scenarios:
  - id: offline-read
    fixture: demo-fixture
    command_families: [read]
    procedure: Read the fixture fact.
    excellent: Report the fixture fact exactly.
"""
    suite_text = """schema_version: 1
id: offline-suite
kind: absolute
default_samples: 1
scenarios: [offline-read]
arms:
  - {id: ordinary, skill: false, role: null}
"""
    fixture_registry = {"demo": {"repository": "https://github.com/acme/demo-fixture", "commit": ""}}

    source_repository = tmp_path / "source-repository"
    source_commit = commit_repository(
        source_repository,
        {"skills/demo/SKILL.md": "---\nname: demo\nmetadata:\n  version: '1.0.0'\n---\noffline skill\n"},
        "https://github.com/acme/skills.git",
    )
    harness_repository = tmp_path / "harness-repository"
    harness_commit = commit_repository(
        harness_repository,
        {
            "evals/config.yaml": config_text,
            "evals/scenarios/iwe.yaml": catalog_text,
            "evals/fixtures/sources.json": "placeholder\n",
            "evals/suites/offline.yaml": suite_text,
        },
        "https://github.com/acme/harness.git",
    )
    fixture_repository = tmp_path / "fixture-repository"
    fixture_commit = commit_repository(
        fixture_repository,
        {"fact.txt": "the fixture fact\n"},
        "https://github.com/acme/demo-fixture.git",
    )
    fixture_registry["demo"]["commit"] = fixture_commit
    fixture_text = json.dumps(fixture_registry, sort_keys=True) + "\n"
    (harness_repository / "evals/fixtures/sources.json").write_text(fixture_text)
    git(harness_repository, "add", "evals/fixtures/sources.json")
    git(harness_repository, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "registry")
    harness_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=harness_repository, check=True, capture_output=True, text=True
    ).stdout.strip()

    materialize_git_identity(source_repository, inputs / "source-repository", inputs / "source-commit-object")
    materialize_git_identity(harness_repository, inputs / "harness-repository", inputs / "harness-commit-object")
    shutil.copytree(inputs / "source-repository/skills/demo", inputs / "selected-skill")
    shutil.copytree(fixture_repository, inputs / "fixtures/demo", ignore=shutil.ignore_patterns(".git"))
    shutil.copytree(inputs / "fixtures/demo", inputs / "materialized-fixtures/demo-fixture")
    write_git_commit_object(fixture_repository, inputs / "fixture-commit-objects/demo")
    (inputs / "config.yaml").write_text(config_text)
    (inputs / "scenario-catalog.yaml").write_text(catalog_text)
    (inputs / "suite.yaml").write_text(suite_text)
    atomic_write_json(inputs / "effective-suite.json", suite)
    (inputs / "fixture-sources.json").write_text(fixture_text)

    task = run / "datasets/ordinary/offline-read--sample-001"
    (task / "tests").mkdir(parents=True)
    (task / "task.toml").write_text("version = '1.0'\n")
    (task / "instruction.md").write_text("Read the fixture fact.\n")
    (task / "tests/verify.py").write_text("print('offline')\n")
    (task / "tests/before-tree.json").write_text(
        json.dumps([{"path": "fact.txt", "sha256": sha256_file(inputs / "materialized-fixtures/demo-fixture/fact.txt")}])
    )
    task_digest = harbor_content_sha256(
        task, virtual_files={"environment/payload/usr/local/bin/iwe": runtime}
    )

    fixture_tree = git_tree_sha1(inputs / "fixtures/demo")
    provenance = Provenance(
        source_url=f"https://github.com/acme/skills/tree/{source_commit}/skills/demo",
        source_commit=source_commit,
        source_tree_sha256=sha256_tree(inputs / "source-repository"),
        selected_skill="demo",
        selected_skill_sha256=sha256_tree(inputs / "selected-skill"),
        selected_skill_harbor_sha256=harbor_skill_sha256(inputs / "selected-skill"),
        runtime_version="0.18.0",
        runtime_sha256=runtime_digest,
        harness_commit=harness_commit,
        harness_tree_sha256=sha256_tree(inputs / "harness-repository"),
        harness_dirty=False,
        suite_sha256=sha256_file(inputs / "suite.yaml"),
        effective_suite_sha256=sha256_file(inputs / "effective-suite.json"),
        scenario_catalog_sha256=sha256_file(inputs / "scenario-catalog.yaml"),
        config_sha256=sha256_file(inputs / "config.yaml"),
        fixture_registry_sha256=sha256_file(inputs / "fixture-sources.json"),
        harbor_version="0.21.0",
        node_version="22.23.2",
        agent_versions={"codex": "0.147.0", "claude": "2.1.233"},
        task_checksums={"ordinary/offline-read--sample-001": task_digest},
        image_digests={"agent": image_digest, "verifier": verifier_digest},
        fixture_sources={"demo": {
            "repository": "https://github.com/acme/demo-fixture",
            "commit": fixture_commit,
            "tree": fixture_tree,
            "payload_sha256": sha256_tree(inputs / "fixtures/demo"),
        }},
        judge_concurrency=1,
    )
    (run / "provenance.json").write_text(provenance.model_dump_json())

    trial_name = "offline-trial"
    trial_dir = run / "jobs/ordinary" / trial_name
    (trial_dir / "agent").mkdir(parents=True)
    (trial_dir / "verifier").mkdir()
    (trial_dir / "agent/trajectory.json").write_text(
        json.dumps({"steps": [{"source": "agent", "message": "the fixture fact"}]})
    )
    oracle = {
        "procedure": "Read the fixture fact.",
        "excellent": "Report the fixture fact exactly.",
        "source_excerpts": [{
            "path": "fact.txt",
            "sha256": sha256_file(inputs / "materialized-fixtures/demo-fixture/fact.txt"),
            "text": "the fixture fact",
        }],
    }
    (trial_dir / "verifier/oracle.json").write_text(json.dumps(oracle, sort_keys=True))
    (trial_dir / "verifier/mechanical.json").write_text(json.dumps({"failures": []}))
    (trial_dir / "verifier/workspace-manifest.json").write_text("[]")
    (trial_dir / "verifier/test-stdout.txt").write_text("offline verification passed\n")
    (trial_dir / "verifier/test-stderr.txt").write_text("")
    trial = TrialResult.model_validate({
        "id": "00000000-0000-0000-0000-000000000002",
        "task_name": "iwe/offline-read--sample-001",
        "trial_name": trial_name,
        "trial_uri": "file:///offline-trial",
        "task_id": {"path": "/offline-task"},
        "task_checksum": task_digest,
        "config": {"task": {"name": "iwe/offline-read--sample-001"}},
        "agent_info": {"name": "codex", "version": "0.147.0"},
        "agent_result": {"n_input_tokens": 10, "n_cache_tokens": 2, "n_output_tokens": 3, "cost_usd": 0.01},
        "verifier_result": {"rewards": {"infrastructure": 1}},
        "verifier_environment_mode": "separate",
        "started_at": "2026-01-01T00:00:00Z",
        "finished_at": "2026-01-01T00:00:01Z",
    })
    atomic_write_json(trial_dir / "result.json", trial.model_dump(mode="json", exclude_none=True))
    job = JobResult.model_validate({
        "id": "00000000-0000-0000-0000-000000000001",
        "started_at": "2026-01-01T00:00:00Z",
        "finished_at": "2026-01-01T00:00:01Z",
        "n_total_trials": 1,
        "stats": {"n_completed_trials": 1, "evals": {}},
    })
    atomic_write_json(run / "jobs/ordinary/result.json", job.model_dump(mode="json", exclude_none=True))
    lock_trial = {
        "schema_version": 2,
        "install_only": False,
        "timeout_multiplier": 1.0,
        "agent": {"name": "codex", "model_name": "offline-model", "skills": [], "resume_trajectory": False, "extra_allowed_hosts": [], "kwargs": {"version": "0.147.0"}, "mcp_servers": []},
        "skills": [],
        "environment": {"type": "docker", "force_build": False, "delete": True, "cpu_enforcement_policy": "auto", "memory_enforcement_policy": "auto", "extra_docker_compose": [], "kwargs": {}, "extra_allowed_hosts": []},
        "verifier": {"disable": False, "environment_mode": "separate"},
        "task": {"name": "offline-read--sample-001", "source": "ordinary", "digest": f"sha256:{task_digest}"},
    }
    atomic_write_json(run / "jobs/ordinary/lock.json", {
        "schema_version": 3,
        "harbor": {"version": "0.21.0", "is_editable": False},
        "n_concurrent_trials": 1,
        "retry": {"max_retries": 0},
        "trials": [lock_trial],
    })

    scenario = {
        "id": "offline-read", "fixture": "demo-fixture", "command_families": ["read"],
        "procedure": "Read the fixture fact.", "excellent": "Report the fixture fact exactly.",
    }
    evidence = build_evidence(trial_evidence(run / "jobs/ordinary", trial_name))
    verdict = {
        "rationale": "All deterministic offline evidence supports the result.",
        "dimensions": {
            name: {"score": 5, "rationale": "Deterministic evidence supports this score.", "evidence_ids": ["E0003"]}
            for name in ("task_correctness", "scenario_compliance", "skill_compliance", "safety", "evidence_quality", "tool_efficiency", "resource_efficiency")
        },
    }
    scores, passed, required = derive_cell_outcome(
        JudgeVerdict.model_validate(verdict),
        role=None,
        agent="codex",
    )
    cell = {
        "arm": "ordinary", "scenario_id": "offline-read", "family": "read", "sample": 1,
        "valid": True, "pass": passed, "required_pass": required, "scenario_outcome": "passed",
        "scenario_failures": [], "scores": scores, "wall_time_seconds": 1.0,
        "n_input_tokens": 10, "n_cache_tokens": 2, "n_output_tokens": 3, "cost_usd": 0.01,
        "evidence": [item.model_dump(mode="json") for item in evidence],
        "judge_messages": build_judge_messages(scenario=scenario, evidence=evidence, scale={"minimum": 0, "maximum": 5}),
        "verdict": verdict,
    }
    atomic_write_json(run / "cells/ordinary--offline-read--1.json", cell)
    validated_suite = Suite.model_validate(suite)
    summary = summarize_cells(
        [cell], {("ordinary", "offline-read", 1)}, expected_families={"offline-read": "read"},
        analysis=AnalysisPlan.from_suite(validated_suite, families={"offline-read": "read"}, samples=1),
        pipeline_elapsed_seconds=1.5, run_purpose="production", samples_per_identity=1,
        preregistered_samples=1,
    )
    atomic_write_json(run / "summary.json", summary)
    atomic_write_json(run / "run-manifest.json", {
        "schema_version": 1, "run_id": "offline-current-v5", "run_purpose": "production",
        "agent": "codex", "agent_version": "0.147.0", "node_version": "22.23.2",
        "samples": 1, "suite_default_samples": 1, "suite": suite,
        "suite_repository_path": "evals/suites/offline.yaml",
        "datasets": {"ordinary": "datasets/ordinary"},
        "execution": {"judge_concurrency": 1, "arm_concurrency_batches": [{"ordinary": 1}]},
        "judge_backend": "offline-fixture",
    })
    atomic_write_json(run / "device-telemetry.json", {
        "schema_version": 2, "started_unix_ms": 1000, "finished_unix_ms": 2000,
        "host": {"logical_cpus": 1, "total_memory_bytes": 4096, "total_swap_bytes": 0, "docker_metrics_available": False, "telemetry_scope": "whole-host", "network_scope": "default-route-interfaces", "disk_scope": "physical-block-devices", "filesystem_scope": "root-filesystem"},
        "samples": [{"elapsed_ms": 0, "cpu_percent": 0.0, "load1": 0.0, "mem_available_bytes": 2048, "swap_free_bytes": 0, "running_containers": 0, "network_rx_bytes": 0, "network_tx_bytes": 0, "disk_read_bytes": 0, "disk_write_bytes": 0, "rootfs_used_bytes": 1024, "rootfs_free_bytes": 2048, "network_rx_bytes_per_second": 0.0, "network_tx_bytes_per_second": 0.0, "disk_read_bytes_per_second": 0.0, "disk_write_bytes_per_second": 0.0}],
        "peaks": {"cpu_percent": 0.0, "load1": 0.0, "running_containers": 0, "network_rx_bytes_per_second": 0.0, "network_tx_bytes_per_second": 0.0, "disk_read_bytes_per_second": 0.0, "disk_write_bytes_per_second": 0.0, "rootfs_used_bytes": 1024},
        "minima": {"mem_available_bytes": 2048, "swap_free_bytes": 0, "rootfs_free_bytes": 2048},
        "totals": {"network_rx_bytes": 0, "network_tx_bytes": 0, "disk_read_bytes": 0, "disk_write_bytes": 0},
        "docker_oom_events": 0, "sampling_errors": 0, "terminal_status": "completed",
    })
    seal_run(run)
    return root, run


def test_seal_rejects_omitted_required_file(tmp_path: Path) -> None:
    _, run = setup(tmp_path)
    seal = json.loads((run / "run-seal.json").read_text())
    del seal["files"]["inputs/runtime"]
    (run / "run-seal.json").write_text(json.dumps(seal))
    with pytest.raises(ValueError, match="incomplete|exact publication payload"):
        verify_run_seal(run)


def test_publisher_defaults_to_report_without_evidence(tmp_path: Path, mocked_validator: None) -> None:
    root, run = setup(tmp_path)
    renamed = root / "arbitrary-relocated-bundle-name"
    run.rename(renamed)
    output = root / "reports" / "published.md"
    publish(root=root, run_dir=renamed, output=output)
    text = output.read_text()
    assert text.startswith("# Evaluation report\n")
    assert "- Run ID: `canonical-production-run`" in text
    assert "- Report revision: `unversioned`" in text
    assert "Suite acceptance: **PASS**" in text
    assert "https://github.com/bulbigood/skills-eval-harness" in text
    assert "Sealed evidence: not staged with this report" in text
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


def test_publisher_can_include_revalidated_evidence(tmp_path: Path, mocked_validator: None) -> None:
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


def test_publisher_rejects_failed_incomplete_dirty_or_overwrite(tmp_path: Path, mocked_validator: None) -> None:
    root, run = setup(tmp_path)
    output = root / "published.md"
    summary = json.loads((run / "summary.json").read_text())
    summary["pass"] = False
    summary["acceptance"]["pass"] = False
    summary["evaluation_status"]["acceptance"]["passed"] = False
    (run / "summary.json").write_text(json.dumps(summary))
    seal_run(run)
    publish(root=root, run_dir=run, output=output)
    assert "Suite acceptance: **FAIL**" in output.read_text()
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


def test_publisher_rejects_tampered_sealed_artifact(tmp_path: Path, mocked_validator: None) -> None:
    root, run = setup(tmp_path)
    summary = json.loads((run / "summary.json").read_text())
    summary["pass"] = False
    (run / "summary.json").write_text(json.dumps(summary))
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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocked_validator: None
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


def test_publish_uses_real_bundle_validator_and_rejects_legacy_schema(tmp_path: Path) -> None:
    root, run = setup(tmp_path)
    summary = json.loads((run / "summary.json").read_text())
    summary["schema_version"] = 4
    (run / "summary.json").write_text(json.dumps(summary))
    seal_run(run)
    with pytest.raises(ValueError, match="only summary schema version 5"):
        publish(root=root, run_dir=run, output=root / "report.md")


def test_publish_validates_sealed_current_bundle_and_writes_markdown_checksum(tmp_path: Path) -> None:
    root, run = build_valid_current_bundle(tmp_path)
    output = root / "reports/current.md"

    assert validate_run_bundle(run, require_seal=True)["schema_version"] == 5
    publish(root=root, run_dir=run, output=output)

    report = output.read_text()
    assert report.startswith("# Evaluation report\n")
    assert str(tmp_path) not in report
    checksum = output.with_suffix(".md.sha256")
    assert checksum.read_text() == f"{sha256_file(output)}  current.md\n"
