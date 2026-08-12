#!/usr/bin/env python3
"""Run behavioral evaluations for a configured IWE skill and agent."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast


ROOT = Path(__file__).resolve().parents[2]
EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(EVAL))

from skill_manifest import load_skill, verify_runtime_binary
from experiment import load_experiment
from eval_concurrency import DEFAULT_JOBS, normalize_jobs  # type: ignore[import-not-found]
from eval_core.config import DIMENSIONS, EvalConfig, ModelProfile, load_eval_config, resolve_agent_model_profile, resolve_model_profile
from eval_core.agent_config import load_agent_config
from eval_core.scenarios import SCENARIOS_FILE, SCENARIO_SCHEMA, Scenario, load_scenarios, select_scenarios
from eval_core.scheduling import (
    MatrixCell,
    balanced_waves,
    build_matrix,
    execute_synchronized_waves,
    worker_waves,
)
from eval_core.process import (
    TRANSIENT_PROCESS_ATTEMPTS, TRANSIENT_PROVIDER_MESSAGES, TRANSIENT_RETRY_DELAYS_SECONDS,
    parse_process_output, performance_summary, process_argv, run_process, transient_provider_failure,
)
from eval_core.telemetry import ESTIMATED_BYTES_PER_TOKEN, command_metrics, deterministic_metric_failures, efficiency_errors, estimate_input_tokens, load_iwe_telemetry, procedure_errors, route_errors
from eval_core.oracle import (
    _document_links, _document_title, _is_english_audit_retention_decision,
    _source_excerpt, independent_oracle_evidence,
    independent_schema_validation_evidence, payload_hash, snapshot,
)
from eval_core.prompts import agent_prompt, judge_prompt
from eval_core.execution import RunContext, execute_cell, retry_summary
from eval_core.io import atomic_write_json
from eval_core.workspace import (
    agents_file_provenance, assert_workspace_ready, create_judge_workspace,
    ensure_fixture, eval_environment, install_agents_file, install_command_shims,
    install_skill, judge_environment, preinjected_guidance_bytes, prepare,
    remove_tested_skill_for_judge, verify_iwe_binary,
)
from eval_core.scoring import (
    agent_metadata, aggregate_results,
    efficiency_diagnostics, efficiency_range_diagnostic, profile_verdict,
    replay_saved_report, required_successes, validate_shared_agent, verdict,
)
from eval_core.mechanical import (
    classify_mechanical_errors, judge_command_evidence, mechanical_errors,
    sanitize_judge_evidence,
)


__all__ = (
    "DIMENSIONS",
    "EvalConfig",
    "ModelProfile",
    "SCENARIOS_FILE",
    "SCENARIO_SCHEMA",
    "Scenario",
    "MatrixCell",
    "balanced_waves",
    "build_matrix",
    "worker_waves",
    "TRANSIENT_PROCESS_ATTEMPTS",
    "TRANSIENT_PROVIDER_MESSAGES",
    "TRANSIENT_RETRY_DELAYS_SECONDS",
    "parse_process_output",
    "process_argv",
    "transient_provider_failure",
    "ESTIMATED_BYTES_PER_TOKEN",
    "command_metrics",
    "efficiency_errors",
    "estimate_input_tokens",
    "route_errors",
    "_document_links",
    "_document_title",
    "_source_excerpt",
    "independent_schema_validation_evidence",
    "_is_english_audit_retention_decision",
    "resolve_model_profile",
    "agent_metadata",
    "efficiency_range_diagnostic",
    "replay_saved_report",
    "required_successes",
    "subprocess",
    "shutil",
    "run_process",
    "deterministic_metric_failures",
    "load_iwe_telemetry",
    "procedure_errors",
    "independent_oracle_evidence",
    "payload_hash",
    "snapshot",
    "agent_prompt",
    "judge_prompt",
    "assert_workspace_ready",
    "create_judge_workspace",
    "eval_environment",
    "install_agents_file",
    "install_command_shims",
    "install_skill",
    "judge_environment",
    "preinjected_guidance_bytes",
    "prepare",
    "remove_tested_skill_for_judge",
    "efficiency_diagnostics",
    "profile_verdict",
    "verdict",
    "classify_mechanical_errors",
    "judge_command_evidence",
    "mechanical_errors",
    "sanitize_judge_evidence",
)


















































































































































def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--skill", help="skill id from the root config.toml")
    mode.add_argument("--experiment", type=Path, help="paired experiment TOML")
    parser.add_argument("--scenario", action="append", metavar="ID", help="exact scenario id (repeatable)")
    parser.add_argument(
        "--scenario-file",
        type=Path,
        default=SCENARIOS_FILE,
        help="scenario YAML (defaults to the production scenario SSOT)",
    )
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--jobs", type=int)
    parser.add_argument("--samples", type=int)
    parser.add_argument(
        "--model-profile",
        choices=("medium", "weak"),
        default=None,
        help="tested-model profile; must match eval.agent_model_profiles for --agent",
    )
    parser.add_argument("--markdown-report", type=Path)
    parser.add_argument("--agent", choices=("codex", "claude"), default="codex")
    parser.add_argument("--keep-workspaces", action="store_true")
    args = parser.parse_args()
    if args.markdown_report and not args.experiment:
        parser.error("--markdown-report requires --experiment")
    scenario_file = args.scenario_file
    if not scenario_file.is_absolute():
        scenario_file = ROOT / scenario_file
    experiment = (
        load_experiment(args.experiment, ROOT, scenario_file)
        if args.experiment
        else None
    )
    skill = None if experiment else load_skill(args.skill)
    config_name = experiment.agent_judge_config if experiment else (args.config or args.agent)
    config_path = EVAL / "configs" / f"{config_name}.json"
    config = load_agent_config(config_path)
    eval_config = load_eval_config()
    try:
        model_profile = resolve_agent_model_profile(eval_config, args.agent, args.model_profile)
    except ValueError as error:
        parser.error(str(error))
    scenarios = load_scenarios(
        scenario_file,
        eval_config=eval_config,
        model_profile=model_profile,
    )
    if experiment:
        scenarios = select_scenarios(scenarios, list(experiment.scenario_ids))
    if args.scenario:
        try:
            scenarios = select_scenarios(scenarios, args.scenario)
        except ValueError as error:
            parser.error(str(error))
    target_count = len(experiment.targets) if experiment else 1
    balanced_scheduling = bool(
        experiment and experiment.worker_scheduling == "balanced_waves"
    )
    requested_jobs = (
        experiment.jobs
        if experiment
        else (args.jobs if args.jobs is not None else DEFAULT_JOBS)
    )
    try:
        jobs = normalize_jobs(
            requested_jobs,
            target_count=target_count,
            balanced=balanced_scheduling,
        )
    except ValueError as error:
        parser.error(str(error))
    if args.list:
        if experiment:
            for target in experiment.targets:
                skill_label = (
                    os.path.relpath(target.skill_path, ROOT)
                    if target.skill_path is not None else "no skill"
                )
                print(
                    f"target {target.id}: {skill_label} @ IWE "
                    f"{target.runtime.version} ({target.runtime.source})"
                )
        for scenario in scenarios:
            print(f"{scenario.id}: {scenario.name} [{scenario.fixture}]")
        return 0
    if not scenarios:
        parser.error("no scenarios selected")
    shared_agent = validate_shared_agent(config, args.agent)
    if experiment and (args.jobs is not None or args.samples is not None):
        parser.error("experiment samples/jobs are authoritative; edit the manifest")
    if experiment:
        runtime_binaries = {
            target.id: verify_runtime_binary(target.runtime) for target in experiment.targets
        }
        canonical = {}
        for target in experiment.targets:
            binary = runtime_binaries[target.id]
            previous = canonical.setdefault(binary, target.runtime.version)
            if previous != target.runtime.version:
                raise RuntimeError(
                    f"targets resolve {binary} with conflicting versions; use distinct directory sources"
                )
        samples = experiment.samples
    else:
        assert skill is not None
        iwe_binary = verify_iwe_binary(skill)
        runtime_binaries = {"single": iwe_binary}
        samples = args.samples or config["samples"]
    cache = EVAL / ".cache"
    cache.mkdir(exist_ok=True)
    fixtures = {name: ensure_fixture(config, name, cache) for name in {s.fixture for s in scenarios}}
    suffix = f"-{experiment.name}" if experiment else ""
    report_dir = EVAL / "reports" / (dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ") + suffix)
    report_dir.mkdir(parents=True)


    run_context = RunContext(
        config=config,
        eval_config=eval_config,
        model_profile=model_profile,
        experiment=experiment,
        skill=skill,
        runtime_binaries=runtime_binaries,
        fixtures=fixtures,
        report_dir=report_dir,
        agent=args.agent,
        keep_workspaces=args.keep_workspaces,
    )
    execute = lambda task, wave_id=None: execute_cell(run_context, task, wave_id)

    tasks = build_matrix(experiment, scenarios) if experiment else [
        (scenario, sample) for scenario in scenarios for sample in range(1, samples + 1)
    ]
    if experiment and experiment.worker_scheduling == "balanced_waves":
        matrix_tasks = cast(list[MatrixCell], tasks)
        waves = worker_waves(matrix_tasks, jobs, len(experiment.targets))
        results = execute_synchronized_waves(waves, execute)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(jobs, len(tasks))) as executor:
            results = list(executor.map(execute, tasks))
    comparison_exclusions_by_target = {
        target.id: ({"skill_compliance"} if not target.has_skill else set())
        for target in experiment.targets
    } if experiment else {}
    aggregate_exclusions_by_target = {
        target.id: set(experiment.aggregate_exclusions_for(target.id))
        for target in experiment.targets
    } if experiment else {}
    outcomes = aggregate_results(
        results,
        eval_config,
        expected_samples=samples,
        excluded_dimensions_by_target=aggregate_exclusions_by_target,
        excluded_dimensions_by_scenario=experiment.metric_exclusions if experiment else None,
        model_profile=model_profile,
    )
    summary = {
        "configuration": config["name"],
        "skill": skill.name if skill else None,
        "experiment": experiment.name if experiment else None,
        "guidance_accounting": (
            experiment.guidance_accounting if experiment else "exclude_activation"
        ),
        "skill_activation": experiment.skill_activation if experiment else "scenario",
        "worker_scheduling": experiment.worker_scheduling if experiment else "streaming",
        "model_profile": model_profile.name,
        "minimum_score": model_profile.minimum_score,
        "required_success_percent": model_profile.required_success_percent,
        "scenarios": outcomes,
        "retry_accounting": retry_summary(results),
        "results": [
            ({"target_id": r["target_id"], "pair_id": r["pair_id"]} if experiment else {})
            | {"scenario_id": r["scenario_id"], "scenario": r["scenario"],
               "sample": r["sample"], "verdict": r["verdict"]}
            for r in results
        ],
    }
    snapshot_document = None
    if experiment:
        from compare import compare_results
        expected_pairs = {
            (cell.scenario_id, cell.sample_index): cell.pair_id
            for cell in tasks
            if isinstance(cell, MatrixCell)
        }
        comparisons = compare_results(
            results,
            tuple(target.id for target in experiment.targets),
            experiment.comparison_metrics or DIMENSIONS,
            expected_pairs,
            excluded_dimensions_by_target=comparison_exclusions_by_target,
            excluded_dimensions_by_scenario=experiment.metric_exclusions,
        )
        summary["comparisons"] = comparisons
        if experiment.comparison_metrics:
            summary["performance"] = performance_summary(
                results, tuple(target.id for target in experiment.targets)
            )
        snapshot_document = {
            "schema_version": 1, "name": experiment.name,
            "scenarios": [scenario.id for scenario in scenarios],
            "samples": samples, "jobs": jobs,
            "comparison_metrics": list(experiment.comparison_metrics or ()),
            "metric_exclusions": {
                scenario: sorted(metrics)
                for scenario, metrics in experiment.metric_exclusions.items()
            },
            "aggregate_metric_exclusions_by_target": {
                target: sorted(metrics)
                for target, metrics in experiment.aggregate_metric_exclusions_by_target.items()
            },
            "guidance_accounting": experiment.guidance_accounting,
            "skill_activation": experiment.skill_activation,
            "worker_scheduling": experiment.worker_scheduling,
            "model_profile": model_profile.name,
            "minimum_score": model_profile.minimum_score,
            "required_success_percent": model_profile.required_success_percent,
            "agent_judge_config": experiment.agent_judge_config,
            "agent": shared_agent["agent"],
            "judge": {
                "model": shared_agent["judge"]["model"],
                "reasoning": shared_agent["judge"]["reasoning"],
            },
            "estimated_agent_calls": len(tasks), "estimated_judge_calls": len(tasks),
            "targets": [
                {"id": target.id,
                 "model_profile": model_profile.name,
                 "minimum_score": model_profile.minimum_score,
                 "required_success_percent": model_profile.required_success_percent,
                 "skill_mode": "installed" if target.has_skill else "none",
                 "skill_path": os.path.relpath(target.path, ROOT) if target.path else None,
                 "skill_version": target.skill_version,
                 "agents_file": os.path.relpath(target.agents_file, ROOT) if target.agents_file else None,
                 "agents_file_provenance": agents_file_provenance(target.agents_file),
                 "contract_file": os.path.relpath(target.contract_file, ROOT),
                 "runtime": {"cli": target.runtime.cli, "source": target.runtime.source,
                             "directory": str(target.runtime.directory), "version": target.runtime.version}}
                for target in experiment.targets
            ],
        }
        atomic_write_json(report_dir / "experiment.json", snapshot_document)
        for target in experiment.targets:
            atomic_write_json(report_dir / "targets" / target.id / "summary.json", {
                "target_id": target.id,
                "model_profile": model_profile.name,
                "minimum_score": model_profile.minimum_score,
                "required_success_percent": model_profile.required_success_percent,
                "scenarios": [outcome for outcome in outcomes if outcome.get("target_id") == target.id],
            })
        grouped_comparisons = {}
        for comparison in comparisons:
            key = f"{comparison['left_target_id']}--vs--{comparison['right_target_id']}"
            grouped_comparisons.setdefault(key, []).append(comparison)
        for key, values in grouped_comparisons.items():
            atomic_write_json(report_dir / "comparisons" / f"{key}.json", values)
    atomic_write_json(report_dir / "summary.json", summary)
    if args.markdown_report:
        from report_markdown import write_markdown

        assert snapshot_document is not None
        markdown_path = args.markdown_report
        if not markdown_path.is_absolute():
            markdown_path = ROOT / markdown_path
        write_markdown(markdown_path, snapshot_document, summary, report_dir)
    for outcome in outcomes:
        failed_metrics = [
            name for name, detail in outcome["metrics"].items() if not detail["pass"]
        ]
        details = []
        if failed_metrics:
            details.append(f"metric_failures={failed_metrics}")
        if outcome["invalid_samples"]:
            details.append(f"invalid_samples={outcome['invalid_samples']}")
        suffix = " " + " ".join(details) if details else ""
        target_prefix = f"{outcome.get('target_id')} / " if outcome.get("target_id") else ""
        print(f"{'PASS' if outcome['pass'] else 'FAIL'} aggregate {target_prefix}{outcome['scenario']}{suffix}")
    print(f"Reports: {report_dir}")
    return 0 if all(outcome["pass"] for outcome in outcomes) else 1

if __name__ == "__main__":
    sys.exit(main())
