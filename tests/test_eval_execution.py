from __future__ import annotations

import json
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "tests/eval"
SCRIPTS = ROOT / "scripts"
for path in (SCRIPTS, EVAL):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from eval_core.execution import (
    WorkspaceLease,
    _resolve_cell,
    _wait_for_provider_retry,
    execute_cell,
    retry_summary,
)
from eval_core.process import parse_process_output


class EvalExecutionTests(unittest.TestCase):
    def test_workspace_lease_owns_workspace_and_cleanup(self) -> None:
        cleanup = mock.Mock()
        lease = WorkspaceLease(Path("/tmp/run"), Path("/tmp/run/workspace"), cleanup)

        lease.cleanup()

        cleanup.cleanup.assert_called_once_with()
        with self.assertRaises(FrozenInstanceError):
            lease.workspace = Path("/tmp/other")

    def test_resolve_cell_supports_direct_single_skill_runs(self) -> None:
        scenario = SimpleNamespace(id="scenario")
        skill = SimpleNamespace(name="skill")
        binary = Path("/opt/iwe")
        context = SimpleNamespace(skill=skill, runtime_binaries={"single": binary})

        cell = _resolve_cell(context, (scenario, 3))

        self.assertIs(cell.scenario, scenario)
        self.assertEqual(cell.sample, 3)
        self.assertIs(cell.skill, skill)
        self.assertEqual(cell.target_id, "single")
        self.assertIsNone(cell.pair_id)
        self.assertEqual(cell.iwe_binary, binary)

    def test_shared_provider_cooldown_adds_jitter(self) -> None:
        with (
            mock.patch("eval_core.execution.random.uniform", return_value=1.2),
            mock.patch("eval_core.execution.time.monotonic", return_value=100.0),
            mock.patch("eval_core.execution.time.sleep") as sleep,
            mock.patch("eval_core.execution._PROVIDER_COOLDOWN_UNTIL", 0.0),
        ):
            _wait_for_provider_retry(10)

        sleep.assert_called_once_with(12.0)

    def test_retry_summary_reports_actual_provider_attempts(self) -> None:
        summary = retry_summary([
            {
                "worker_cell_attempts": 1,
                "worker_process_attempts": 2,
                "judge_process_attempts": 1,
                "provider_failure_recovered": False,
            },
            {
                "worker_cell_attempts": 2,
                "worker_process_attempts": 2,
                "judge_process_attempts": 1,
                "provider_failure_recovered": True,
            },
            {
                "worker_cell_attempts": 3,
                "worker_process_attempts": 3,
                "judge_process_attempts": 0,
                "provider_failure_recovered": False,
            },
        ])

        self.assertEqual(summary, {
            "declared_cells": 3,
            "worker_cell_attempts": 6,
            "worker_process_attempts": 7,
            "judge_process_attempts": 2,
            "retried_cells": 2,
            "recovered_cells": 1,
            "exhausted_cells": 1,
        })

    def test_parse_process_output_separates_provider_errors_from_tool_output(self) -> None:
        provider_stdout = "\n".join([
            json.dumps({
                "type": "item.started",
                "item": {"type": "command_execution", "command": "iwe find"},
            }),
            json.dumps({
                "type": "error",
                "message": "Selected model is at capacity. Please try a different model.",
            }),
        ])
        parsed = parse_process_output("codex", provider_stdout)
        self.assertTrue(parsed["tool_activity"])
        self.assertEqual(parsed["provider_errors"], [
            "Selected model is at capacity. Please try a different model."
        ])

        spoofed = parse_process_output("codex", json.dumps({
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": "printf capacity",
                "exit_code": 1,
                "aggregated_output": "Selected model is at capacity.",
            },
        }))
        self.assertTrue(spoofed["tool_activity"])
        self.assertEqual(spoofed["provider_errors"], [])

    def test_execute_cell_retries_capacity_failure_in_a_fresh_workspace(self) -> None:
        context = SimpleNamespace(
            skill=SimpleNamespace(name="skill"),
            runtime_binaries={"single": Path("/opt/iwe")},
            report_dir=Path("/tmp/report"),
            experiment=None,
        )
        scenario = SimpleNamespace(id="scenario", slug="scenario", name="Scenario")
        task = (scenario, 1)
        first_lease = mock.Mock(spec=WorkspaceLease)
        second_lease = mock.Mock(spec=WorkspaceLease)
        failed_run = SimpleNamespace(agent={
            "exit": 1,
            "commands": [{"command": "iwe retrieve --key note"}],
            "stdout": "Selected model is at capacity. Please try a different model.",
            "stderr": "",
            "provider_errors": ["Selected model is at capacity. Please try a different model."],
            "tool_activity": True,
        })
        successful_run = SimpleNamespace(agent={"exit": 0, "commands": []})
        result = {"verdict": {"valid": True}}

        with (
            mock.patch(
                "eval_core.execution._create_workspace_lease",
                side_effect=[first_lease, second_lease],
            ),
            mock.patch(
                "eval_core.execution._execute_agent",
                side_effect=[failed_run, successful_run],
            ),
            mock.patch(
                "eval_core.execution._evaluate_agent",
                return_value=SimpleNamespace(judge={"attempts": 1}),
            ) as evaluate,
            mock.patch(
                "eval_core.execution._record_result",
                side_effect=lambda *_args: result.update(_args[4]) or result,
            ),
            mock.patch("eval_core.execution._record_worker_attempt") as record_attempt,
            mock.patch("eval_core.execution.time.sleep"),
        ):
            actual = execute_cell(context, task)

        self.assertIs(actual, result)
        self.assertEqual(actual["worker_cell_attempts"], 2)
        self.assertEqual(actual["worker_process_attempts"], 2)
        self.assertEqual(actual["prior_retryable_provider_failures"], 1)
        self.assertTrue(actual["provider_failure_recovered"])
        self.assertEqual(actual["judge_process_attempts"], 1)
        self.assertEqual(evaluate.call_count, 1)
        evaluate.assert_called_once_with(mock.ANY, mock.ANY, second_lease, successful_run)
        record_attempt.assert_called_once_with(context, mock.ANY, failed_run, 1)
        first_lease.cleanup.assert_called_once_with()
        second_lease.cleanup.assert_called_once_with()

    def test_execute_cell_bounds_fresh_workspace_retries(self) -> None:
        context = SimpleNamespace(
            skill=SimpleNamespace(name="skill"),
            runtime_binaries={"single": Path("/opt/iwe")},
            report_dir=Path("/tmp/report"),
            experiment=None,
        )
        scenario = SimpleNamespace(id="scenario", slug="scenario", name="Scenario")
        failed_run = SimpleNamespace(agent={
            "exit": 1,
            "commands": [{"command": "iwe retrieve --key note"}],
            "stdout": "",
            "stderr": "Selected model is at capacity. Please try a different model.",
            "provider_errors": ["Selected model is at capacity. Please try a different model."],
            "tool_activity": True,
        })
        leases = [mock.Mock(spec=WorkspaceLease) for _ in range(3)]

        with (
            mock.patch(
                "eval_core.execution._create_workspace_lease", side_effect=leases
            ),
            mock.patch(
                "eval_core.execution._execute_agent",
                side_effect=[failed_run, failed_run, failed_run],
            ),
            mock.patch("eval_core.execution._evaluate_agent") as evaluate,
            mock.patch(
                "eval_core.execution._provider_failure_evaluation",
                return_value=SimpleNamespace(judge={"attempts": 0}),
            ) as provider_evaluation,
            mock.patch(
                "eval_core.execution._record_result",
                side_effect=lambda *_args: {"done": True, **_args[4]},
            ),
            mock.patch("eval_core.execution._record_worker_attempt") as record_attempt,
            mock.patch("eval_core.execution.time.sleep"),
        ):
            actual = execute_cell(context, (scenario, 1))

        self.assertEqual(actual, {
            "done": True,
            "worker_cell_attempts": 3,
            "worker_process_attempts": 3,
            "prior_retryable_provider_failures": 2,
            "provider_failure_recovered": False,
            "judge_process_attempts": 0,
        })
        self.assertEqual(record_attempt.call_count, 3)
        self.assertEqual(evaluate.call_count, 0)
        provider_evaluation.assert_called_once_with(context, scenario, failed_run)
        self.assertTrue(all(lease.cleanup.call_count == 1 for lease in leases))

    def test_execute_cell_does_not_multiply_startup_retries_or_judge_provider_failure(self) -> None:
        context = SimpleNamespace(
            skill=SimpleNamespace(name="skill"),
            runtime_binaries={"single": Path("/opt/iwe")},
            report_dir=Path("/tmp/report"),
            experiment=None,
        )
        scenario = SimpleNamespace(id="scenario", slug="scenario", name="Scenario")
        failed_run = SimpleNamespace(agent={
            "exit": 1,
            "commands": [],
            "stdout": "Selected model is at capacity. Please try a different model.",
            "stderr": "",
            "provider_errors": ["Selected model is at capacity. Please try a different model."],
            "tool_activity": False,
        })
        lease = mock.Mock(spec=WorkspaceLease)

        with (
            mock.patch("eval_core.execution._create_workspace_lease", return_value=lease),
            mock.patch("eval_core.execution._execute_agent", return_value=failed_run) as execute,
            mock.patch("eval_core.execution._evaluate_agent") as evaluate,
            mock.patch(
                "eval_core.execution._provider_failure_evaluation",
                return_value=SimpleNamespace(judge={"attempts": 0}),
            ) as provider_evaluation,
            mock.patch(
                "eval_core.execution._record_result",
                side_effect=lambda *_args: {"done": True, **_args[4]},
            ),
            mock.patch("eval_core.execution._record_worker_attempt") as record_attempt,
            mock.patch("eval_core.execution.time.sleep") as sleep,
        ):
            actual = execute_cell(context, (scenario, 1))

        self.assertEqual(actual, {
            "done": True,
            "worker_cell_attempts": 1,
            "worker_process_attempts": 1,
            "prior_retryable_provider_failures": 0,
            "provider_failure_recovered": False,
            "judge_process_attempts": 0,
        })
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(evaluate.call_count, 0)
        provider_evaluation.assert_called_once_with(context, scenario, failed_run)
        record_attempt.assert_called_once_with(context, mock.ANY, failed_run, 1)
        sleep.assert_not_called()
        lease.cleanup.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
