"""Execution of one evaluation matrix cell."""
from __future__ import annotations

import hashlib
import json
import os
import random
import shlex
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from experiment import Experiment
from skill_manifest import SkillSpec
from .config import DIMENSIONS, EvalConfig, ModelProfile
from .io import atomic_write_json
from .mechanical import classify_mechanical_errors, mechanical_errors
from .oracle import independent_oracle_evidence, payload_hash, snapshot
from .process import TRANSIENT_PROVIDER_MESSAGES, run_process
from .prompts import agent_prompt, judge_prompt
from .scenarios import Scenario
from .scheduling import MatrixCell
from .scoring import efficiency_diagnostics, profile_verdict, verdict
from .telemetry import command_metrics, deterministic_metric_failures, load_iwe_telemetry, procedure_errors
from .workspace import (
    agents_file_provenance,
    assert_workspace_ready,
    create_judge_workspace,
    eval_environment,
    install_agents_file,
    install_command_shims,
    install_skill,
    judge_environment,
    preinjected_guidance_bytes,
    prepare,
    remove_tested_skill_for_judge,
)


ROOT = Path(__file__).resolve().parents[3]
EVAL = Path(__file__).resolve().parents[1]

CELL_PROVIDER_ATTEMPTS = 3
CELL_RETRY_DELAYS_SECONDS = (15, 45)
CELL_RETRY_JITTER = 0.2
CELL_RETRY_MIN_SPACING_SECONDS = 1.0
_PROVIDER_COOLDOWN_LOCK = threading.Lock()
_PROVIDER_COOLDOWN_UNTIL = 0.0


def _wait_for_provider_retry(delay: float) -> None:
    """Reserve a jittered retry time so concurrent cells do not retry in lockstep."""
    global _PROVIDER_COOLDOWN_UNTIL
    jittered = delay * random.uniform(1 - CELL_RETRY_JITTER, 1 + CELL_RETRY_JITTER)
    with _PROVIDER_COOLDOWN_LOCK:
        now = time.monotonic()
        scheduled = max(
            now + jittered,
            _PROVIDER_COOLDOWN_UNTIL + CELL_RETRY_MIN_SPACING_SECONDS,
        )
        _PROVIDER_COOLDOWN_UNTIL = scheduled
    time.sleep(max(scheduled - now, 0.0))


@dataclass(frozen=True)
class RunContext:
    config: dict
    eval_config: EvalConfig
    model_profile: ModelProfile
    experiment: Experiment | None
    skill: SkillSpec | None
    runtime_binaries: Mapping[str, Path]
    fixtures: Mapping[str, Path]
    report_dir: Path
    agent: str
    keep_workspaces: bool = False


@dataclass(frozen=True)
class ResolvedCell:
    scenario: Scenario
    sample: int
    target: object
    skill: SkillSpec | None
    target_id: str
    pair_id: str | None
    iwe_binary: Path


@dataclass(frozen=True)
class WorkspaceLease:
    temporary: Path
    workspace: Path
    temporary_context: object | None

    def cleanup(self) -> None:
        if self.temporary_context is not None:
            self.temporary_context.cleanup()


@dataclass(frozen=True)
class AgentRun:
    workspace: Path
    base_name: str
    installed_agents_file: Path | None
    before: dict[str, str]
    after: dict[str, str]
    host_auth: Path
    agent: dict
    range_diagnostics: list[str]
    integrity_errors: list[str]
    postcondition_failures: dict[str, str]
    procedural_errors: list[str]


@dataclass(frozen=True)
class Evaluation:
    deterministic_failures: dict[str, str]
    judge: dict
    raw_verdict: dict
    profile: dict


def _resolve_cell(context: RunContext, task) -> ResolvedCell:
    skill = context.skill
    runtime_binaries = context.runtime_binaries
    if isinstance(task, MatrixCell):
        scenario, sample = (task.scenario, task.sample_index)
        local_target = task.target
        local_skill = task.target if task.target.has_skill else None
        target_id, pair_id = (task.target_id, task.pair_id)
        local_iwe_binary = runtime_binaries[target_id]
    else:
        scenario, sample = task
        assert skill is not None
        local_target = skill
        local_skill, target_id, pair_id = (skill, 'single', None)
        local_iwe_binary = runtime_binaries[target_id]
    return ResolvedCell(scenario, sample, local_target, local_skill, target_id, pair_id, local_iwe_binary)


def _create_workspace_lease(context: RunContext) -> WorkspaceLease:
    workspace_root = EVAL / '.cache/workspaces'
    workspace_root.mkdir(parents=True, exist_ok=True)
    temporary_context = None
    if context.keep_workspaces:
        temporary = Path(tempfile.mkdtemp(prefix='iwe-agent-eval-', dir=workspace_root))
    else:
        temporary_context = tempfile.TemporaryDirectory(prefix='iwe-agent-eval-', dir=workspace_root)
        temporary = Path(temporary_context.name)
    workspace = temporary / 'workspace'
    return WorkspaceLease(temporary, workspace, temporary_context)


def _execute_agent(
    context: RunContext,
    cell: ResolvedCell,
    lease: WorkspaceLease,
    task,
    worker_wave_id: int | None,
) -> AgentRun:
    config = context.config
    experiment = context.experiment
    fixtures = context.fixtures
    scenario = cell.scenario
    local_target = cell.target
    local_skill = cell.skill
    local_iwe_binary = cell.iwe_binary
    temporary = lease.temporary
    workspace = lease.workspace
    base_name = 'seventeen-centuries' if scenario.fixture.startswith('seventeen') else 'pkm-demo'
    shutil.copytree(fixtures[scenario.fixture], workspace, ignore=shutil.ignore_patterns('.git'))
    prepare(workspace, scenario.fixture)
    install_skill(workspace, local_skill)
    installed_agents_file = install_agents_file(workspace, local_target.agents_file if isinstance(task, MatrixCell) else None, scenario.agents_context)
    activation_path = workspace / '.agents/guidance/SKILL.md' if local_skill is not None else None
    assert_workspace_ready(workspace, activation_path)
    before = snapshot(workspace)
    isolated_home = temporary / 'home'
    codex_home = temporary / 'codex-home'
    isolated_home.mkdir()
    codex_home.mkdir()
    shim_bin = temporary / 'shims'
    install_command_shims(shim_bin, scenario, local_iwe_binary, allow_filesystem_tools=local_skill is None)
    (isolated_home / '.bash_profile').write_text(f'export PATH="{shim_bin}:{local_iwe_binary.parent}:$PATH"\n', encoding='utf-8')
    host_auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if host_auth.exists():
        shutil.copy2(host_auth, codex_home / 'auth.json')
    env = eval_environment(isolated_home, codex_home, shim_bin, local_iwe_binary, temporary, context.agent, workspace=workspace)
    prompt = agent_prompt(scenario, skill_installed=local_skill is not None, activation_path=activation_path, skill_activation=experiment.skill_activation if experiment else 'scenario')
    agent = run_process(config['agent_command'], prompt, workspace, config['timeout_seconds'], env)
    agent['wave_id'] = worker_wave_id
    telemetry = load_iwe_telemetry(Path(env['IWE_EVAL_IWE_LOG']))
    agent['iwe_telemetry'] = telemetry
    agent['metrics'] = command_metrics(agent['commands'], telemetry, tested_skill=local_skill.name if local_skill is not None else None, exclude_skill_activation=scenario.skill_activation == 'required' and (not (experiment and experiment.guidance_accounting == 'include_activation')), activation_path=activation_path)
    range_diagnostics = efficiency_diagnostics(scenario, agent['metrics'])
    after = snapshot(workspace)
    mechanical = mechanical_errors(scenario, before, after, agent['commands'], workspace)
    integrity_errors, postcondition_failures = classify_mechanical_errors(mechanical)
    procedural_errors = procedure_errors(scenario, agent['commands'], agent['metrics'], agent['iwe_telemetry'], allow_filesystem_fallback=bool(isinstance(task, MatrixCell) and local_skill is None and (local_target.agents_file is None)))
    return AgentRun(
        workspace, base_name, installed_agents_file, before, after, host_auth,
        agent, range_diagnostics, integrity_errors, postcondition_failures,
        procedural_errors,
    )


def _evaluate_agent(
    context: RunContext,
    cell: ResolvedCell,
    lease: WorkspaceLease,
    run: AgentRun,
) -> Evaluation:
    config = context.config
    eval_config = context.eval_config
    model_profile = context.model_profile
    experiment = context.experiment
    scenario = cell.scenario
    local_skill = cell.skill
    temporary = lease.temporary
    workspace = run.workspace
    before = run.before
    after = run.after
    host_auth = run.host_auth
    agent = run.agent
    integrity_errors = run.integrity_errors
    postcondition_failures = run.postcondition_failures
    procedural_errors = run.procedural_errors
    judge_schema = EVAL / 'judge.schema.json'
    judge_command = config['judge_command'].format(judge_schema=shlex.quote(str(judge_schema)), judge_schema_json=shlex.quote(json.dumps(json.loads(judge_schema.read_text(encoding='utf-8')), separators=(',', ':'))))
    oracle = independent_oracle_evidence(scenario, before, after, agent['final'])
    deterministic_failures = deterministic_metric_failures(scenario, agent['commands'], oracle, metrics=agent['metrics'])
    for dimension, reason in postcondition_failures.items():
        prior = deterministic_failures.get(dimension)
        deterministic_failures[dimension] = f'{prior}; {reason}' if prior else reason
    judge_prompt_text = judge_prompt(local_skill, scenario, agent, before, after, integrity_errors + procedural_errors + list(deterministic_failures.values()), eval_config, oracle, include_guidance_activation=bool(experiment and experiment.guidance_accounting == 'include_activation'))
    remove_tested_skill_for_judge(workspace)
    judge_workspace = create_judge_workspace(temporary)
    judge_home = temporary / 'judge-home'
    judge_codex_home = temporary / 'judge-codex-home'
    judge_home.mkdir()
    judge_codex_home.mkdir()
    if host_auth.exists():
        shutil.copy2(host_auth, judge_codex_home / 'auth.json')
    judge_tools = temporary / 'judge-tools'
    judge_tools.mkdir()
    judge_executable = shutil.which(shlex.split(judge_command)[0])
    node_executable = shutil.which('node')
    if not judge_executable or not node_executable:
        raise RuntimeError('configured judge executable or its node runtime is unavailable')
    (judge_tools / Path(judge_executable).name).symlink_to(judge_executable)
    (judge_tools / 'node').symlink_to(node_executable)
    judge_env = judge_environment(judge_home, judge_codex_home, judge_tools, context.agent)
    judge = run_process(judge_command, judge_prompt_text, judge_workspace, config['timeout_seconds'], judge_env)
    try:
        critique = json.loads(judge['final'])
    except json.JSONDecodeError:
        critique = {'rationale': 'invalid judge JSON', 'evidence': [judge['final']], 'dimensions': {}}
    judge_errors = list(integrity_errors)
    if judge['commands']:
        judge_errors.append('judge executed commands instead of inspecting supplied evidence only')
    raw_sample_verdict = verdict(scenario, critique, judge_errors, agent['exit'] == 0 and judge['exit'] == 0, procedure_errors=procedural_errors, deterministic_metric_failures=deterministic_failures)
    sample_profile = profile_verdict(raw_sample_verdict, model_profile)
    return Evaluation(deterministic_failures, judge, raw_sample_verdict, sample_profile)


def _record_result(
    context: RunContext,
    cell: ResolvedCell,
    run: AgentRun,
    evaluation: Evaluation,
    accounting: dict[str, int | bool] | None = None,
) -> dict:
    config = context.config
    eval_config = context.eval_config
    experiment = context.experiment
    report_dir = context.report_dir
    scenario = cell.scenario
    sample = cell.sample
    local_target = cell.target
    local_skill = cell.skill
    local_iwe_binary = cell.iwe_binary
    target_id = cell.target_id
    pair_id = cell.pair_id
    base_name = run.base_name
    installed_agents_file = run.installed_agents_file
    workspace = run.workspace
    agent = run.agent
    range_diagnostics = run.range_diagnostics
    judge = evaluation.judge
    raw_sample_verdict = evaluation.raw_verdict
    sample_profile = evaluation.profile
    result = {'scenario': scenario.name, 'scenario_id': scenario.id, 'sample': sample, 'fixture': {'name': scenario.fixture, 'commit': config['fixtures'][base_name]['commit']}, 'agent_judge_config': {'name': config['name'], 'agent_command_sha256': hashlib.sha256(config['agent_command'].encode()).hexdigest(), 'judge_command_sha256': hashlib.sha256(config['judge_command'].encode()).hexdigest()}, 'scoring_contract': {'scale': eval_config.score_scale, 'dimensions': scenario.scoring}, 'evaluation_profile': sample_profile, 'efficiency_expectations': {'task_tool_calls': [scenario.min_tool_calls, scenario.max_tool_calls], 'task_tool_output_bytes': [scenario.min_task_tool_output_bytes, scenario.max_task_tool_output_bytes], 'max_iwe_calls': scenario.max_iwe_calls, 'hard_max_task_tool_calls': scenario.hard_max_task_tool_calls}, 'agent': agent, 'preinjected_guidance_bytes': preinjected_guidance_bytes(installed_agents_file), 'efficiency_diagnostics': range_diagnostics, 'judge': judge, 'verdict': raw_sample_verdict, 'workspace': str(workspace) if context.keep_workspaces else None}
    if accounting:
        result.update(accounting)
    if experiment:
        result['target_id'] = target_id
        result['pair_id'] = pair_id
        target_dir = report_dir / 'targets' / target_id
        target_dir.mkdir(parents=True, exist_ok=True)
        local_skill_path = local_skill.path if local_skill is not None else None
        result['target_provenance'] = {'skill_mode': 'installed' if local_skill is not None else 'none', 'skill_path': os.path.relpath(local_skill_path, ROOT) if local_skill_path is not None else None, 'skill_version': local_skill.skill_version if local_skill is not None else None, 'skill_sha256': payload_hash(local_skill_path) if local_skill_path is not None else None, 'agents_file': os.path.relpath(local_target.agents_file, ROOT) if local_target.agents_file is not None else None, 'agents_file_provenance': agents_file_provenance(installed_agents_file), 'agents_context': scenario.agents_context, 'contract_file': os.path.relpath(local_target.contract_file, ROOT), 'contract_sha256': hashlib.sha256(local_target.contract_file.read_bytes()).hexdigest(), 'runtime_source': local_target.runtime.source, 'runtime_binary': str(local_iwe_binary), 'declared_runtime_version': local_target.runtime.version, 'observed_runtime_version': local_target.runtime.version}
        raw_path = target_dir / f'{scenario.slug}--{sample}.json'
    else:
        raw_path = report_dir / f'{scenario.slug}--{sample}.json'
    atomic_write_json(raw_path, result)
    failures = sorted(result['evaluation_profile']['metric_failures'])
    status = 'VALID' if result['verdict']['valid'] else 'INVALID'
    suffix = f' metric_failures={failures}' if failures else ''
    print(f'{status} sample {sample} {scenario.name}{suffix}', flush=True)
    return result


def _retryable_worker_provider_failure(run: AgentRun) -> str | None:
    agent = run.agent
    if agent.get('exit') == 0:
        return None
    provider_errors = [str(error).casefold() for error in agent.get('provider_errors', [])]
    return next(
        (
            message
            for message in TRANSIENT_PROVIDER_MESSAGES
            if any(message in error for error in provider_errors)
        ),
        None,
    )


def _attempt_path(context: RunContext, cell: ResolvedCell, attempt: int) -> Path:
    target = cell.target_id if context.experiment else 'single'
    return (
        context.report_dir
        / 'attempts'
        / target
        / f'{cell.scenario.slug}--{cell.sample}--attempt-{attempt}.json'
    )


def _record_worker_attempt(
    context: RunContext,
    cell: ResolvedCell,
    run: AgentRun,
    attempt: int,
) -> None:
    agent = run.agent
    atomic_write_json(_attempt_path(context, cell, attempt), {
        'target_id': cell.target_id,
        'scenario_id': cell.scenario.id,
        'sample': cell.sample,
        'attempt': attempt,
        'classification': 'retryable_provider_failure',
        'provider_error': _retryable_worker_provider_failure(run),
        'agent': agent,
        'workspace_changed': run.before != run.after,
        'workspace': str(run.workspace) if context.keep_workspaces else None,
    })


def _provider_failure_evaluation(
    context: RunContext,
    scenario: Scenario,
    run: AgentRun,
) -> Evaluation:
    error = _retryable_worker_provider_failure(run) or 'provider process failed'
    rationale = f'Worker did not complete because of a transient provider failure: {error}.'
    critique = {
        'rationale': rationale,
        'evidence': [error],
        'dimensions': {
            name: {'score': 0, 'rationale': rationale, 'evidence': [error]}
            for name in DIMENSIONS
        },
    }
    raw_verdict = verdict(
        scenario,
        critique,
        ['worker provider retries exhausted'],
        exits_ok=False,
    )
    judge = {
        'exit': None,
        'final': json.dumps(critique, ensure_ascii=False),
        'commands': [],
        'attempts': 0,
        'transient_failures': [],
        'skipped': 'worker provider retries exhausted',
    }
    return Evaluation(
        {},
        judge,
        raw_verdict,
        profile_verdict(raw_verdict, context.model_profile),
    )


def retry_summary(results: list[dict]) -> dict[str, int]:
    return {
        'declared_cells': len(results),
        'worker_cell_attempts': sum(int(result.get('worker_cell_attempts', 1)) for result in results),
        'worker_process_attempts': sum(int(result.get('worker_process_attempts', 1)) for result in results),
        'judge_process_attempts': sum(int(result.get('judge_process_attempts', 1)) for result in results),
        'retried_cells': sum(int(result.get('worker_cell_attempts', 1)) > 1 for result in results),
        'recovered_cells': sum(bool(result.get('provider_failure_recovered')) for result in results),
        'exhausted_cells': sum(
            int(result.get('worker_cell_attempts', 1)) > 1
            and not bool(result.get('provider_failure_recovered'))
            for result in results
        ),
    }


def execute_cell(context: RunContext, task, worker_wave_id: int | None = None) -> dict:
    cell = _resolve_cell(context, task)
    prior_worker_process_attempts = 0
    for attempt in range(1, CELL_PROVIDER_ATTEMPTS + 1):
        lease = _create_workspace_lease(context)
        try:
            run = _execute_agent(context, cell, lease, task, worker_wave_id)
            retryable = _retryable_worker_provider_failure(run)
            clean_retry = retryable is not None and bool(run.agent.get('tool_activity'))
            if clean_retry and attempt < CELL_PROVIDER_ATTEMPTS:
                prior_worker_process_attempts += int(run.agent.get('attempts', 1))
                _record_worker_attempt(context, cell, run, attempt)
            else:
                if retryable is not None:
                    _record_worker_attempt(context, cell, run, attempt)
                evaluation = (
                    _provider_failure_evaluation(context, cell.scenario, run)
                    if retryable is not None
                    else _evaluate_agent(context, cell, lease, run)
                )
                accounting = {
                    'worker_cell_attempts': attempt,
                    'worker_process_attempts': (
                        prior_worker_process_attempts + int(run.agent.get('attempts', 1))
                    ),
                    'prior_retryable_provider_failures': attempt - 1,
                    'provider_failure_recovered': (
                        attempt > 1 and run.agent.get('exit') == 0
                    ),
                    'judge_process_attempts': int(evaluation.judge.get('attempts', 0)),
                }
                return _record_result(
                    context,
                    cell,
                    run,
                    evaluation,
                    accounting,
                )
        finally:
            lease.cleanup()
        _wait_for_provider_retry(CELL_RETRY_DELAYS_SECONDS[attempt - 1])
    raise AssertionError('unreachable cell retry state')
