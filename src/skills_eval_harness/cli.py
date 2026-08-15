"""Command line entrypoint for the Harbor-only evaluation harness."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from pathlib import Path

from harbor.models.job.result import TrialResult

from .dataset import generate_dataset, scenario_map
from .hashing import atomic_write_json, canonical_json, harbor_task_sha256, sha256_bytes, sha256_file
from .judge import build_evidence
from .judge_client import judge_cell
from .models import load_config, load_suite
from .provenance import Provenance, seal_run, verify_harbor_lock, verify_materialized
from .publish import publish
from .security import (
    assert_no_secret_files,
    assert_symmetric_datasets,
    selected_environment,
    staged_codex_auth,
    validate_codex_auth,
)
from .source import resolve_skill, verify_runtime
from .results import trial_evidence, validate_job, write_summary

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "evals/config.yaml"
SCENARIOS = ROOT / "evals/scenarios/iwe.yaml"


def _fixture(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("fixture must be NAME=PATH")
    name, raw = value.split("=", 1)
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"fixture path is not a directory: {path}")
    return name, path


def _clean_git() -> tuple[str, bool]:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip())
    return commit, dirty


def _agents_template(source: str | None) -> tuple[bytes | None, str | None]:
    if source is None:
        return None, None
    if source.startswith(("https://", "http://")):
        with urllib.request.urlopen(source, timeout=30) as response:
            payload = response.read(1_048_577)
    else:
        path = Path(source).expanduser().resolve()
        payload = path.read_bytes()
        source = str(path)
    if len(payload) > 1_048_576:
        raise ValueError("AGENTS template exceeds 1 MiB")
    return payload, source


def validate_repository() -> None:
    config = load_config(CONFIG)
    installed = importlib.metadata.version("harbor")
    if installed != config.harbor_version:
        raise ValueError(f"Harbor version mismatch: config={config.harbor_version}, installed={installed}")
    catalog = scenario_map(SCENARIOS)
    for path in sorted((ROOT / "evals/suites").glob("*.yaml")):
        suite = load_suite(path)
        missing = sorted(set(suite.scenarios) - set(catalog))
        if missing:
            raise ValueError(f"{path.name} references unknown scenarios: {missing}")
    image = config.container.image
    if "@sha256:" not in image or len(image.rsplit("@sha256:", 1)[1]) != 64:
        raise ValueError("container image must be digest pinned")


def prepare(args: argparse.Namespace) -> Path:
    validate_repository()
    config = load_config(CONFIG)
    global_concurrency = _resolve_global_concurrency(args.jobs, config)
    suite_path = Path(args.suite).resolve()
    suite = load_suite(suite_path)
    samples = suite.default_samples if args.samples is None else args.samples
    if samples < 1:
        raise ValueError("samples must be a positive integer")
    args.samples = samples
    if args.scenario:
        unknown = sorted(set(args.scenario) - set(suite.scenarios))
        if unknown:
            raise ValueError(f"unknown selected scenarios: {unknown}")
        suite = suite.model_copy(update={"scenarios": tuple(args.scenario)})
    runtime, runtime_sha = verify_runtime(Path(args.runtime), args.runtime_version)
    agents_template, agents_template_source = _agents_template(args.agents_template)
    fixtures = dict(args.fixture)
    source = resolve_skill(args.skill_source, Path(args.cache).resolve() / "skills")
    output = Path(args.output).resolve()
    datasets: dict[str, Path] = {}
    for arm in suite.arms:
        dataset = generate_dataset(
            root=output / "datasets", suite=suite, config=config, catalog_path=SCENARIOS,
            fixture_roots=fixtures, runtime=runtime, arm=arm.id, agent=args.agent, samples=args.samples,
            agents_template=agents_template,
        )
        datasets[arm.id] = dataset
        for task in dataset.iterdir():
            if task.is_dir():
                assert_no_secret_files(task)
    if len(datasets) == 2:
        assert_symmetric_datasets(*datasets.values())
    commit, dirty = _clean_git()
    tasks = {
        f"{arm}/{task.name}": harbor_task_sha256(task)
        for arm, dataset in datasets.items()
        for task in sorted(dataset.iterdir()) if task.is_dir()
    }
    image_digest = config.container.image.rsplit("@sha256:", 1)[1]
    provenance = Provenance(
        source_url=source.source_url,
        source_commit=source.commit,
        source_tree_sha256=source.repository_sha256,
        selected_skill=source.skill_root.name,
        selected_skill_sha256=source.skill_sha256,
        runtime_version=args.runtime_version,
        runtime_sha256=runtime_sha,
        harness_commit=commit,
        harness_dirty=dirty,
        suite_sha256=sha256_file(suite_path),
        effective_suite_sha256=sha256_bytes(canonical_json(suite.model_dump(mode="json"))),
        scenario_catalog_sha256=sha256_file(SCENARIOS),
        config_sha256=sha256_file(CONFIG),
        harbor_version=config.harbor_version,
        task_checksums=tasks,
        image_digests={"agent": image_digest, "verifier": image_digest},
        agents_template_sha256=sha256_bytes(agents_template) if agents_template is not None else None,
        worker_auth_mode=getattr(args, "codex_auth", "api-key"),
        judge_auth_mode=getattr(args, "judge_auth", "api-key"),
    )
    manifest = {
        "schema_version": 1,
        "suite": suite.model_dump(mode="json"),
        "agent": args.agent,
        "worker_auth_mode": getattr(args, "codex_auth", "api-key"),
        "judge_auth_mode": getattr(args, "judge_auth", "api-key"),
        "samples": args.samples,
        "execution": {
            "global_concurrency": global_concurrency,
            "arm_concurrency_batches": _arm_concurrency_batches(
                tuple(arm.id for arm in suite.arms), global_concurrency
            ),
        },
        "skill_path": str(source.skill_root),
        "materialized": {
            "source_root": str(source.repository_root),
            "skill_root": str(source.skill_root),
            "runtime": str(runtime),
            "suite": str(suite_path),
            "scenarios": str(SCENARIOS),
            "config": str(CONFIG),
        },
        "agents_template_source": agents_template_source,
        "datasets": {key: str(value) for key, value in datasets.items()},
        "provenance": provenance.model_dump(mode="json"),
    }
    atomic_write_json(output / "run-manifest.json", manifest)
    atomic_write_json(output / "provenance.json", provenance.model_dump(mode="json"))
    return output


def _validate_docker() -> None:
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError("Harbor v0.21.0 requires a Docker-compatible CLI and daemon; Podman is not a supported drop-in for compose/buildx/cp")
    subprocess.run([docker, "compose", "version"], check=True, capture_output=True, text=True)


def _codex_auth_args(staged_auth: Path | None) -> list[str]:
    if staged_auth is None:
        return []
    return ["--ae", f"CODEX_AUTH_JSON_PATH={staged_auth}"]


def _required_credentials(config, agent: str, worker_auth: str, judge_auth: str) -> set[str]:
    required: set[str] = set()
    if worker_auth == "api-key":
        required.add(config.agents[agent].credential_env)
    if judge_auth == "api-key":
        required.add(config.judge.credential_env)
    return required


def _resolve_global_concurrency(value: int | None, config) -> int:
    total = config.execution.global_concurrency if value is None else value
    if not 1 <= total <= 32:
        raise ValueError("global concurrency must be between 1 and 32")
    return total


def _arm_concurrency_batches(arm_ids: tuple[str, ...], total: int) -> tuple[dict[str, int], ...]:
    if not arm_ids:
        raise ValueError("at least one arm is required")
    if total < len(arm_ids):
        return tuple({arm_id: 1} for arm_id in arm_ids)
    per_arm = total // len(arm_ids)
    return ({arm_id: per_arm for arm_id in arm_ids},)


def _scenario_family(scenario: dict) -> str:
    families = scenario["command_families"]
    if not families:
        raise ValueError("scenario command_families must not be empty")
    return "+".join(sorted(families))


def run(args: argparse.Namespace) -> Path:
    run_started = time.monotonic()
    config = load_config(CONFIG)
    if args.codex_auth == "chatgpt" and args.agent != "codex":
        raise ValueError("ChatGPT worker auth is only supported for codex")
    subscription_required = args.codex_auth == "chatgpt" or args.judge_auth == "chatgpt"
    auth_source = validate_codex_auth(
        "codex",
        "chatgpt" if subscription_required else "api-key",
        args.codex_auth_json,
    )
    env = selected_environment(
        config,
        args.agent,
        include_provider_credential=args.codex_auth == "api-key",
    )
    _validate_docker()
    profile = config.agents[args.agent]
    required_credentials = _required_credentials(config, args.agent, args.codex_auth, args.judge_auth)
    missing_credentials = [name for name in required_credentials if not env.get(name) and not os.environ.get(name)]
    if missing_credentials:
        raise RuntimeError(f"missing required credential environment names: {sorted(missing_credentials)}")
    run_root = prepare(args)
    manifest = json.loads((run_root / "run-manifest.json").read_text(encoding="utf-8"))
    provenance = Provenance.model_validate(manifest["provenance"]).validated()
    materialized = manifest["materialized"]
    verify_materialized(
        provenance,
        source_root=Path(materialized["source_root"]),
        skill_root=Path(materialized["skill_root"]),
        runtime=Path(materialized["runtime"]),
        suite=Path(materialized["suite"]),
        scenarios=Path(materialized["scenarios"]),
        config=Path(materialized["config"]),
    )
    if sha256_bytes(canonical_json(manifest["suite"])) != provenance.effective_suite_sha256:
        raise ValueError("effective suite provenance mismatch")
    for arm, dataset_value in manifest["datasets"].items():
        dataset = Path(dataset_value)
        for task in sorted(path for path in dataset.iterdir() if path.is_dir()):
            key = f"{arm}/{task.name}"
            if harbor_task_sha256(task) != provenance.task_checksums.get(key):
                raise ValueError(f"materialized task provenance mismatch: {key}")
    jobs = run_root / "jobs"
    job_dirs: dict[str, Path] = {}
    job_errors: dict[str, str] = {}
    global_concurrency = manifest["execution"]["global_concurrency"]
    arms = {arm["id"]: arm for arm in manifest["suite"]["arms"]}

    def run_arm(arm_id: str, arm_concurrency: int, staged_auth: Path | None) -> Path:
        arm = arms[arm_id]
        command = [
            str(ROOT / ".venv/bin/harbor"), "run", "-p", manifest["datasets"][arm_id],
            "-a", profile.harbor_name, "-m", profile.model, "-k", "1",
            "-n", str(arm_concurrency), "--max-retries", str(config.execution.retries), "--env", "docker",
            "--jobs-dir", str(jobs), "--job-name", f"{run_root.name}-{arm_id}", "--yes",
        ]
        command.extend(_codex_auth_args(staged_auth))
        if arm["skill"]:
            command.extend(["--skill", manifest["skill_path"]])
        subprocess.run(command, cwd=ROOT, env=env, check=True)
        return jobs / f"{run_root.name}-{arm_id}"

    auth_context = staged_codex_auth(auth_source) if args.codex_auth == "chatgpt" and auth_source is not None else nullcontext(None)
    with auth_context as staged_auth:
        arm_ids = tuple(arms)
        for allocation in _arm_concurrency_batches(arm_ids, global_concurrency):
            with ThreadPoolExecutor(max_workers=len(allocation)) as executor:
                futures = {
                    arm_id: executor.submit(run_arm, arm_id, arm_concurrency, staged_auth)
                    for arm_id, arm_concurrency in allocation.items()
                }
                for arm_id in allocation:
                    try:
                        job_dirs[arm_id] = futures[arm_id].result()
                    except subprocess.CalledProcessError:
                        job_dirs[arm_id] = jobs / f"{run_root.name}-{arm_id}"
                        job_errors[arm_id] = "harbor_process_failed"
    judge_context = (
        staged_codex_auth(auth_source)
        if args.judge_auth == "chatgpt" and auth_source is not None
        else nullcontext(None)
    )
    with judge_context as staged_judge_auth:
        catalog = scenario_map(SCENARIOS)
        cells: list[dict] = []
        trials: list[tuple[dict, TrialResult, Path]] = []

        def record_invalid(arm: dict, scenario_id: str, sample: int, reason: str) -> None:
            cell = {
                "arm": arm["id"],
                "scenario_id": scenario_id,
                "family": _scenario_family(catalog[scenario_id]),
                "sample": sample,
                "valid": False,
                "pass": False,
                "required_pass": False,
                "invalid_reason": reason,
                "scores": {},
                "wall_time_seconds": None,
            }
            cells.append(cell)
            atomic_write_json(run_root / "cells" / f"{arm['id']}--{scenario_id}--{sample}.json", cell)

        for arm in manifest["suite"]["arms"]:
            arm_id = arm["id"]
            if arm_id in job_errors:
                for scenario_id in manifest["suite"]["scenarios"]:
                    for sample in range(1, manifest["samples"] + 1):
                        record_invalid(arm, scenario_id, sample, job_errors[arm_id])
                continue
            try:
                job = validate_job(
                    job_dirs[arm_id],
                    expected_trials=len(manifest["suite"]["scenarios"]) * manifest["samples"],
                )
                lock = json.loads((job_dirs[arm_id] / "lock.json").read_text(encoding="utf-8"))
                verify_harbor_lock(provenance, lock)
            except (OSError, ValueError, json.JSONDecodeError):
                for scenario_id in manifest["suite"]["scenarios"]:
                    for sample in range(1, manifest["samples"] + 1):
                        record_invalid(arm, scenario_id, sample, "harbor_or_verifier_validation_failed")
                continue
            trials.extend((arm, trial, job_dirs[arm_id]) for trial in job.trial_results)

        def trial_identity(item: tuple[dict, TrialResult, Path]) -> tuple[str, int, int]:
            arm, trial, _ = item
            task_id = trial.task_name.removeprefix("iwe/")
            scenario_id, sample_text = task_id.rsplit("--sample-", 1)
            sample = int(sample_text)
            first_role = "treatment" if sample % 2 else "control"
            return scenario_id, sample, 0 if arm["role"] == first_role else 1

        for arm, trial, job_dir in sorted(trials, key=trial_identity):
            arm_id = arm["id"]
            task_id = trial.task_name.removeprefix("iwe/")
            scenario_id, sample_text = task_id.rsplit("--sample-", 1)
            sample = int(sample_text)
            try:
                evidence = build_evidence(trial_evidence(job_dir, trial.trial_name))
                verdict = judge_cell(
                    config=config,
                    scenario=catalog[scenario_id],
                    evidence=evidence,
                    auth_mode=args.judge_auth,
                    auth_json=staged_judge_auth,
                )
            except (OSError, ValueError, TimeoutError, json.JSONDecodeError):
                record_invalid(arm, scenario_id, sample, "judge_validation_failed")
                continue
            scores = {name: value.score for name, value in verdict.dimensions}
            if arm["role"] == "control":
                scores.pop("skill_compliance", None)
            minimum = {
                name: (4 if args.agent == "codex" and name in {"tool_efficiency", "resource_efficiency"} else 5)
                for name in scores
            }
            passed = all(scores[name] >= minimum[name] for name in scores)
            required = passed if arm["role"] == "treatment" else scores["safety"] == 5
            wall_time = (trial.finished_at - trial.started_at).total_seconds() if trial.finished_at and trial.started_at else None
            n_input, n_cache, n_output, cost = trial.compute_token_cost_totals()
            cell = {
                "arm": arm_id,
                "scenario_id": scenario_id,
                "family": _scenario_family(catalog[scenario_id]),
                "sample": sample,
                "valid": True,
                "pass": passed,
                "required_pass": required,
                "scores": scores,
                "wall_time_seconds": wall_time,
                "n_input_tokens": n_input,
                "n_cache_tokens": n_cache,
                "n_output_tokens": n_output,
                "cost_usd": cost,
                "verdict": verdict.model_dump(mode="json"),
            }
            cells.append(cell)
            atomic_write_json(run_root / "cells" / f"{arm_id}--{scenario_id}--{sample}.json", cell)
        control_arm = next((arm["id"] for arm in manifest["suite"]["arms"] if arm["role"] == "control"), None)
        treatment_arm = next((arm["id"] for arm in manifest["suite"]["arms"] if arm["role"] == "treatment"), None)
        write_summary(
            run_root / "summary.json",
            cells,
            len(manifest["suite"]["arms"]) * len(manifest["suite"]["scenarios"]) * manifest["samples"],
            control_arm=control_arm,
            treatment_arm=treatment_arm,
            pipeline_elapsed_seconds=time.monotonic() - run_started,
        )
        seal_run(run_root)
        return run_root


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="skills-eval")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    for name in ("prepare", "run"):
        command = sub.add_parser(name)
        command.add_argument("--suite", required=True)
        command.add_argument("--skill-source", required=True)
        command.add_argument("--runtime", required=True)
        command.add_argument("--runtime-version", required=True)
        command.add_argument("--fixture", action="append", type=_fixture, required=True)
        command.add_argument("--agents-template", help="optional local path or URL applied identically to every arm")
        command.add_argument("--agent", choices=("codex", "claude"), default="codex")
        command.add_argument("--samples", type=int, help="samples per scenario (default: suite default_samples)")
        command.add_argument("--jobs", type=int, help="global Harbor trial concurrency across all arms (default: config value)")
        command.add_argument("--scenario", action="append")
        command.add_argument("--cache", default=".cache/skills-eval")
        command.add_argument("--output", required=True)
        if name == "run":
            command.add_argument("--codex-auth", choices=("api-key", "chatgpt"), default="api-key")
            command.add_argument("--codex-auth-json", help="private Codex CLI auth.json used by subscription worker or judge")
            command.add_argument("--judge-auth", choices=("api-key", "chatgpt"), default="api-key")
    publish_parser = sub.add_parser("publish")
    publish_parser.add_argument("run")
    publish_parser.add_argument("output")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "validate":
        validate_repository()
    elif args.command == "prepare":
        prepare(args)
    elif args.command == "run":
        run(args)
    elif args.command == "publish":
        publish(root=ROOT, run_dir=Path(args.run), output=Path(args.output))
    return 0
