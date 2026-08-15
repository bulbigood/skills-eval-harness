"""Shared fail-closed validation for completed run bundles."""
from __future__ import annotations

import json
from pathlib import Path

from .fixtures import materialized_fixture_path
from .hashing import (
    canonical_json,
    git_object_sha1,
    git_tree_sha1,
    harbor_content_sha256,
    harbor_skill_sha256,
    sha256_bytes,
    sha256_file,
    sha256_tree,
)
from .judge import Evidence, build_evidence, build_judge_messages, derive_cell_outcome, validate_verdict
from .models import load_config, load_suite, scenario_family, validate_run_id
from .provenance import Provenance, verify_harbor_lock, verify_run_seal
from .results import CellRecord, summarize_cells, trial_evidence, trial_mechanical_success, validate_job
from .telemetry import validate_device_telemetry


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return value


def _verify_git_snapshot(
    snapshot: Path,
    commit_object: Path,
    *,
    expected_commit: str,
    expected_sha256: str,
) -> None:
    payload = commit_object.read_bytes()
    if git_object_sha1("commit", payload) != expected_commit:
        raise ValueError("sealed Git commit object does not match provenance")
    first_line = payload.splitlines()[0].decode("ascii", errors="strict")
    if not first_line.startswith("tree ") or git_tree_sha1(snapshot) != first_line.removeprefix("tree "):
        raise ValueError("sealed Git snapshot does not match its commit tree")
    if sha256_tree(snapshot) != expected_sha256:
        raise ValueError("sealed Git snapshot does not match its SHA-256 identity")


def _verify_git_commit_tree(commit_object: Path, *, expected_commit: str, expected_tree: str) -> None:
    payload = commit_object.read_bytes()
    if git_object_sha1("commit", payload) != expected_commit:
        raise ValueError("sealed Git commit object does not match provenance")
    first_line = payload.splitlines()[0].decode("ascii", errors="strict")
    if first_line != f"tree {expected_tree}":
        raise ValueError("sealed Git commit object does not name the claimed tree")


def validate_run_bundle(run_dir: Path, *, require_seal: bool) -> dict:
    if require_seal:
        verify_run_seal(run_dir)
    validate_device_telemetry(run_dir / "device-telemetry.json")
    manifest = _load_json(run_dir / "run-manifest.json")
    validate_run_id(manifest.get("run_id"))
    provenance = Provenance.model_validate_json(
        (run_dir / "provenance.json").read_text(encoding="utf-8")
    ).validated()
    config_path = run_dir / "inputs/config.yaml"
    suite_path = run_dir / "inputs/suite.yaml"
    catalog_path = run_dir / "inputs/scenario-catalog.yaml"
    effective_path = run_dir / "inputs/effective-suite.json"
    fixtures_path = run_dir / "inputs/fixture-sources.json"
    expected_hashes = {
        config_path: provenance.config_sha256,
        suite_path: provenance.suite_sha256,
        catalog_path: provenance.scenario_catalog_sha256,
        effective_path: provenance.effective_suite_sha256,
        fixtures_path: provenance.fixture_registry_sha256,
    }
    if any(not path.is_file() or sha256_file(path) != digest for path, digest in expected_hashes.items()):
        raise ValueError("sealed run inputs do not match provenance")
    config = load_config(config_path)
    expected_images = {
        "agent": config.container.agent_image_id.removeprefix("sha256:"),
        "verifier": config.container.image.rsplit("@sha256:", 1)[1],
    }
    if provenance.image_digests != expected_images:
        raise ValueError("sealed container images do not match provenance")
    if provenance.node_version != config.container.node_version:
        raise ValueError("sealed Node version does not match provenance")
    if provenance.agent_versions != {name: value.version for name, value in config.agents.items()}:
        raise ValueError("sealed agent versions do not match provenance")
    if config.runtimes.get(provenance.runtime_version) != provenance.runtime_sha256:
        raise ValueError("runtime version is not bound to canonical bytes")
    _verify_git_snapshot(
        run_dir / "inputs/source-repository",
        run_dir / "inputs/source-commit-object",
        expected_commit=provenance.source_commit,
        expected_sha256=provenance.source_tree_sha256,
    )
    _verify_git_snapshot(
        run_dir / "inputs/harness-repository",
        run_dir / "inputs/harness-commit-object",
        expected_commit=provenance.harness_commit,
        expected_sha256=provenance.harness_tree_sha256,
    )
    harness_snapshot = run_dir / "inputs/harness-repository"
    canonical_inputs = {
        config_path: harness_snapshot / "evals/config.yaml",
        catalog_path: harness_snapshot / "evals/scenarios/iwe.yaml",
        fixtures_path: harness_snapshot / "evals/fixtures/sources.json",
    }
    if any(
        not canonical.is_file() or sealed.read_bytes() != canonical.read_bytes()
        for sealed, canonical in canonical_inputs.items()
    ):
        raise ValueError("sealed canonical registries do not match the harness commit")
    source_repository = provenance.source_url.split("/tree/", 1)[0].rstrip("/").removesuffix(".git")
    if (
        f"/tree/{provenance.source_commit}/" not in provenance.source_url
        or source_repository not in {value.rstrip("/").removesuffix(".git") for value in config.skill_repositories}
    ):
        raise ValueError("source URL is not bound to the sealed source commit")
    if sha256_file(run_dir / "inputs/runtime") != provenance.runtime_sha256:
        raise ValueError("sealed runtime snapshot does not match provenance")
    skill_snapshot = run_dir / "inputs/selected-skill"
    if (
        sha256_tree(skill_snapshot) != provenance.selected_skill_sha256
        or harbor_skill_sha256(skill_snapshot) != provenance.selected_skill_harbor_sha256
    ):
        raise ValueError("sealed skill snapshot does not match provenance")
    fixture_registry = _load_json(fixtures_path)
    for name, revision in provenance.fixture_sources.items():
        declared = fixture_registry.get(name)
        declared_repository = declared.get("repository", "").removesuffix(".git") if isinstance(declared, dict) else ""
        if (
            not isinstance(declared, dict)
            or set(declared) != {"repository", "commit"}
            or declared_repository != revision.repository.removesuffix(".git")
            or declared.get("commit") != revision.commit
        ):
            raise ValueError("fixture registry does not match provenance")
        if sha256_tree(run_dir / "inputs/fixtures" / name) != revision.payload_sha256:
            raise ValueError("sealed fixture snapshot does not match provenance")
        if git_tree_sha1(run_dir / "inputs/fixtures" / name) != revision.tree:
            raise ValueError("sealed fixture snapshot does not match the claimed Git tree")
        _verify_git_commit_tree(
            run_dir / "inputs/fixture-commit-objects" / name,
            expected_commit=revision.commit,
            expected_tree=revision.tree,
        )
    authored_suite = load_suite(suite_path)
    effective = _load_json(effective_path)
    if manifest.get("schema_version") != 1 or manifest.get("suite") != effective:
        raise ValueError("run manifest does not match the effective suite")
    if manifest.get("suite_default_samples") != authored_suite.default_samples:
        raise ValueError("run manifest default sample count does not match the authored suite")
    if manifest.get("run_purpose") == "production" and (
        effective != authored_suite.model_dump(mode="json")
        or manifest.get("samples") != authored_suite.default_samples
    ):
        raise ValueError("production run does not match the preregistered suite matrix")
    if manifest.get("run_purpose") == "production":
        suite_repository_path = manifest.get("suite_repository_path")
        if (
            not isinstance(suite_repository_path, str)
            or Path(suite_repository_path).parent.as_posix() != "evals/suites"
            or not (run_dir / "inputs/harness-repository" / suite_repository_path).is_file()
            or (run_dir / "inputs/harness-repository" / suite_repository_path).read_bytes() != suite_path.read_bytes()
            or provenance.harness_dirty
        ):
            raise ValueError("production suite is not bound to the sealed canonical harness commit")
    arms = effective.get("arms")
    scenarios = effective.get("scenarios")
    samples = manifest.get("samples")
    if not isinstance(arms, list) or not isinstance(scenarios, list) or not isinstance(samples, int) or samples < 1:
        raise ValueError("invalid run plan identity matrix")
    expected_identities = {
        (arm["id"], scenario_id, sample)
        for arm in arms
        for scenario_id in scenarios
        for sample in range(1, samples + 1)
    }
    expected_evidence: dict[tuple[str, str, int], list[dict]] = {}
    observed_trials: set[tuple[str, str, int]] = set()
    profile = config.agents[manifest["agent"]]
    if manifest.get("agent_version") != profile.version:
        raise ValueError("run manifest agent version does not match the sealed config")
    if manifest.get("node_version") != config.container.node_version:
        raise ValueError("run manifest Node version does not match the sealed config")
    batches = manifest["execution"]["arm_concurrency_batches"]
    for arm in arms:
        arm_id = arm["id"]
        dataset = (run_dir / manifest["datasets"][arm_id]).resolve()
        if not dataset.is_relative_to(run_dir):
            raise ValueError("dataset path escapes the run directory")
        for task in sorted(path for path in dataset.iterdir() if path.is_dir()):
            key = f"{arm_id}/{task.name}"
            if harbor_content_sha256(
                task,
                virtual_files={"environment/payload/usr/local/bin/iwe": run_dir / "inputs/runtime"},
            ) != provenance.task_checksums.get(key):
                raise ValueError(f"materialized task mismatch: {key}")
        matching_jobs = []
        for candidate in sorted((run_dir / "jobs").iterdir()):
            if not candidate.is_dir() or not (candidate / "lock.json").is_file():
                continue
            candidate_lock = _load_json(candidate / "lock.json")
            sources = {
                trial.get("task", {}).get("source")
                for trial in candidate_lock.get("trials", [])
                if isinstance(trial, dict) and isinstance(trial.get("task"), dict)
            }
            if sources == {arm_id}:
                matching_jobs.append((candidate, candidate_lock))
        if len(matching_jobs) != 1:
            raise ValueError(f"expected exactly one sealed Harbor job for arm: {arm_id}")
        job_dir, lock = matching_jobs[0]
        job = validate_job(
            job_dir,
            expected_trials=len(scenarios) * samples,
            require_mechanical_success=False,
            allow_failed_trials=True,
        )
        concurrency = max(batch.get(arm_id, 0) for batch in batches)
        verify_harbor_lock(
            provenance,
            lock,
            arm_id=arm_id,
            n_concurrent=concurrency,
            retries=config.execution.retries,
            agent_name=profile.harbor_name,
            agent_version=profile.version,
            model=profile.model,
            skill_enabled=arm["skill"],
        )
        for trial in job.trial_results:
            task_id = trial.task_name.removeprefix("iwe/")
            scenario_id, sample_text = task_id.rsplit("--sample-", 1)
            identity = (arm_id, scenario_id, int(sample_text))
            if identity in observed_trials or identity not in expected_identities:
                raise ValueError("Harbor results do not match the run identity matrix")
            observed_trials.add(identity)
            if trial.exception_info is not None or not trial_mechanical_success(trial):
                continue
            expected_evidence[identity] = [
                item.model_dump(mode="json")
                for item in build_evidence(trial_evidence(job_dir, trial.trial_name))
            ]
    if observed_trials != expected_identities:
        raise ValueError("Harbor results do not cover the run identity matrix")

    catalog = {item["id"]: item for item in __import__("yaml").safe_load(catalog_path.read_text(encoding="utf-8"))["scenarios"]}
    cells = []
    for path in sorted((run_dir / "cells").glob("*.json")):
        raw = _load_json(path)
        cell = CellRecord.model_validate(raw).model_dump(mode="json", by_alias=True)
        expected_name = f"{cell['arm']}--{cell['scenario_id']}--{cell['sample']}.json"
        if path.name != expected_name:
            raise ValueError("cell filename does not match its identity")
        if cell["family"] != scenario_family(catalog[cell["scenario_id"]]):
            raise ValueError("cell family does not match the sealed scenario")
        if cell["valid"]:
            identity = (cell["arm"], cell["scenario_id"], cell["sample"])
            if cell["evidence"] != expected_evidence[identity]:
                raise ValueError("stored cell evidence does not reproduce from Harbor artifacts")
            evidence = tuple(Evidence.model_validate(item) for item in cell["evidence"])
            oracle_items = [item for item in evidence if item.kind == "oracle"]
            if len(oracle_items) != 1 or "\n" not in oracle_items[0].text:
                raise ValueError("semantic oracle does not match the sealed scenario")
            header, oracle_text = oracle_items[0].text.split("\n", 1)
            oracle = json.loads(oracle_text)
            if header != f"oracle sha256={sha256_bytes(oracle_text.encode())}":
                raise ValueError("semantic oracle evidence digest mismatch")
            scenario = catalog[cell["scenario_id"]]
            if oracle.get("procedure") != scenario["procedure"] or oracle.get("excellent") != scenario["excellent"]:
                raise ValueError("semantic oracle does not match the sealed scenario")
            task_id = f"{cell['scenario_id']}--sample-{cell['sample']:03d}"
            task = run_dir / manifest["datasets"][cell["arm"]] / task_id
            before = {
                item["path"]: item["sha256"]
                for item in json.loads((task / "tests/before-tree.json").read_text(encoding="utf-8"))
            }
            excerpts = oracle.get("source_excerpts")
            if not isinstance(excerpts, list) or not excerpts:
                raise ValueError("semantic oracle has no fixture-derived source evidence")
            for excerpt in excerpts:
                if not isinstance(excerpt, dict) or set(excerpt) != {"path", "sha256", "text"}:
                    raise ValueError("invalid semantic oracle source evidence")
                source_path = materialized_fixture_path(run_dir, scenario["fixture"], excerpt["path"])
                if (
                    before.get(excerpt["path"]) != excerpt["sha256"]
                    or not source_path.is_file()
                    or sha256_file(source_path) != excerpt["sha256"]
                    or excerpt["text"] not in source_path.read_text(encoding="utf-8")
                ):
                    raise ValueError("semantic oracle source evidence does not match the fixture baseline")
            verdict = validate_verdict(canonical_json(cell["verdict"]).decode(), evidence)
            arm = next(item for item in arms if item["id"] == cell["arm"])
            expected_scores, expected_pass, expected_required = derive_cell_outcome(
                verdict,
                role=arm.get("role"),
                agent=manifest["agent"],
            )
            if (
                cell["scores"] != expected_scores
                or cell["pass"] is not expected_pass
                or cell["required_pass"] is not expected_required
            ):
                raise ValueError("cell scores or pass flags do not derive from the sealed verdict")
            expected_messages = build_judge_messages(
                scenario=catalog[cell["scenario_id"]], evidence=evidence, scale={"minimum": 0, "maximum": 5}
            )
            if cell["judge_messages"] != expected_messages:
                raise ValueError("stored judge messages do not match sealed scenario and evidence")
        cells.append(cell)

    control = next((arm["id"] for arm in arms if arm.get("role") == "control"), None)
    treatment = next((arm["id"] for arm in arms if arm.get("role") == "treatment"), None)
    stored_summary = _load_json(run_dir / "summary.json")
    recomputed = summarize_cells(
        cells,
        expected_identities,
        expected_families={
            scenario_id: scenario_family(catalog[scenario_id])
            for scenario_id in manifest["suite"]["scenarios"]
        },
        control_arm=control,
        treatment_arm=treatment,
        pipeline_elapsed_seconds=stored_summary.get("timing", {}).get("pipeline_elapsed_seconds"),
        run_purpose=manifest["run_purpose"],
        samples_per_identity=samples,
        preregistered_samples=manifest["suite"]["default_samples"],
    )
    if canonical_json(recomputed) != canonical_json(stored_summary):
        raise ValueError("summary does not recompute from sealed cells")

    return recomputed
