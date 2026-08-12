from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator
import yaml


from tests.eval_test_support import ROOT, load_runner


class EvalScoringContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()
        cls.config = cls.runner.load_eval_config()
        cls.scenario = next(
            item
            for item in cls.runner.load_scenarios()
            if item.id == "query-structured-metadata-without-scanning-files"
        )

    def test_run_process_pins_codex_to_absolute_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            argv = self.runner.process_argv(
                "codex exec --json -",
                workspace,
            )
        self.assertEqual(argv[:4], ["codex", "exec", "-C", str(workspace.resolve())])
        self.assertEqual(argv[-2:], ["--json", "-"])

    def test_workspace_readiness_requires_prepared_workspace_and_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            guidance = workspace / ".agents/guidance/SKILL.md"
            guidance.parent.mkdir(parents=True)
            guidance.write_text("guidance", encoding="utf-8")

            self.runner.assert_workspace_ready(workspace, guidance)

            guidance.unlink()
            with self.assertRaisesRegex(RuntimeError, "guidance is not readable"):
                self.runner.assert_workspace_ready(workspace, guidance)

    def test_run_process_converts_timeout_to_fail_closed_result(self) -> None:
        timeout = subprocess.TimeoutExpired(
            cmd=["agent"],
            timeout=30,
            output='{"type":"turn.started"}\n',
            stderr="remote process stalled",
        )
        with mock.patch.object(self.runner.subprocess, "run", side_effect=timeout):
            result = self.runner.run_process("agent", "prompt", ROOT, 30, {})

        self.assertEqual(result["exit"], 124)
        self.assertIn("turn.started", result["stdout"])
        self.assertIn("timed out", result["stderr"])

    def test_run_process_retries_capacity_failure_before_any_tool_call(self) -> None:
        capacity = subprocess.CompletedProcess(
            ["agent"],
            1,
            stdout="\n".join([
                json.dumps({
                    "type": "error",
                    "message": "Selected model is at capacity. Please try a different model.",
                }),
                json.dumps({
                    "type": "turn.failed",
                    "error": {"message": "Selected model is at capacity. Please try a different model."},
                }),
            ]),
            stderr="",
        )
        success = subprocess.CompletedProcess(
            ["agent"],
            0,
            stdout=json.dumps({
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "done"},
            }),
            stderr="",
        )
        with (
            mock.patch.object(self.runner.subprocess, "run", side_effect=[capacity, success]) as run,
            mock.patch.object(sys.modules[self.runner.run_process.__module__].time, "sleep") as sleep,
        ):
            result = self.runner.run_process("agent", "prompt", ROOT, 30, {})

        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once()
        self.assertEqual(result["exit"], 0)
        self.assertEqual(result["final"], "done")
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(len(result["transient_failures"]), 1)
        self.assertEqual(result["commands"], [])

    def test_run_process_does_not_retry_capacity_failure_after_tool_execution(self) -> None:
        capacity_after_tool = subprocess.CompletedProcess(
            ["agent"],
            1,
            stdout="\n".join([
                json.dumps({
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "iwe retrieve --key note --limit 1",
                        "exit_code": 0,
                        "aggregated_output": "body",
                    },
                }),
                json.dumps({
                    "type": "turn.failed",
                    "error": {"message": "Selected model is at capacity. Please try a different model."},
                }),
            ]),
            stderr="",
        )
        with mock.patch.object(
            self.runner.subprocess, "run", return_value=capacity_after_tool,
        ) as run:
            result = self.runner.run_process("agent", "prompt", ROOT, 30, {})

        self.assertEqual(run.call_count, 1)
        self.assertEqual(result["exit"], 1)
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["transient_failures"], [])
        self.assertEqual(len(result["commands"]), 1)

    def test_run_process_bounds_repeated_capacity_failures(self) -> None:
        capacity = subprocess.CompletedProcess(
            ["agent"],
            1,
            stdout=json.dumps({
                "type": "turn.failed",
                "error": {"message": "Selected model is at capacity. Please try a different model."},
            }),
            stderr="",
        )
        with (
            mock.patch.object(self.runner.subprocess, "run", return_value=capacity) as run,
            mock.patch.object(sys.modules[self.runner.run_process.__module__].time, "sleep") as sleep,
        ):
            result = self.runner.run_process("agent", "prompt", ROOT, 30, {})

        self.assertEqual(run.call_count, 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2, 4, 8])
        self.assertEqual(result["exit"], 1)
        self.assertEqual(result["attempts"], 4)
        self.assertEqual(len(result["transient_failures"]), 3)

    def test_agent_event_parsing_captures_provider_token_usage(self) -> None:
        codex = self.runner.parse_process_output(
            "codex",
            "\n".join([
                json.dumps({"type": "turn.completed", "usage": {
                    "input_tokens": 1200, "cached_input_tokens": 300, "output_tokens": 80,
                }}),
                json.dumps({"type": "item.completed", "item": {
                    "type": "agent_message", "text": "done",
                }}),
            ]),
        )
        self.assertEqual(codex["token_usage"], {
            "input_tokens": 1200,
            "cached_input_tokens": 300,
            "output_tokens": 80,
        })
        claude = self.runner.parse_process_output(
            "claude",
            json.dumps({
                "type": "result",
                "result": "done",
                "usage": {"input_tokens": 900, "cache_read_input_tokens": 200, "output_tokens": 70},
            }),
        )
        self.assertEqual(claude["token_usage"]["input_tokens"], 900)
        self.assertEqual(claude["token_usage"]["cached_input_tokens"], 200)
        self.assertEqual(claude["token_usage"]["output_tokens"], 70)

    def test_global_config_declares_complete_medium_and_weak_profiles(self) -> None:
        self.assertEqual(set(self.config.score_scale), set(range(6)))
        self.assertTrue(all(self.config.score_scale[score].strip() for score in range(6)))
        self.assertEqual(self.config.default_model_profile, "medium")
        self.assertEqual(set(self.config.model_profiles), {"medium", "weak"})
        self.assertEqual(
            self.config.agent_model_profiles,
            {"codex": "weak", "claude": "medium"},
        )

        medium_required = {
            "task_correctness": 100,
            "scenario_compliance": 100,
            "skill_compliance": 100,
            "safety": 100,
            "evidence_quality": 100,
            "tool_efficiency": 80,
            "resource_efficiency": 80,
        }
        weak_required = {
            **{name: 90 for name in self.runner.DIMENSIONS},
            "safety": 100,
        }
        medium = self.config.model_profiles["medium"]
        weak = self.config.model_profiles["weak"]
        self.assertEqual(medium.required_success_percent, medium_required)
        self.assertEqual(weak.required_success_percent, weak_required)
        self.assertEqual(medium.minimum_score, {name: 5 for name in self.runner.DIMENSIONS})
        self.assertEqual(
            weak.minimum_score,
            {
                **{name: 5 for name in self.runner.DIMENSIONS},
                "tool_efficiency": 4,
                "resource_efficiency": 4,
            },
        )
        self.assertEqual(self.runner.resolve_model_profile(self.config).name, "medium")
        self.assertEqual(
            self.runner.resolve_agent_model_profile(self.config, "codex").name,
            "weak",
        )
        self.assertEqual(
            self.runner.resolve_agent_model_profile(self.config, "claude").name,
            "medium",
        )
        with self.assertRaisesRegex(ValueError, "requires model profile medium"):
            self.runner.resolve_agent_model_profile(self.config, "claude", "weak")
        with self.assertRaisesRegex(ValueError, "requires model profile weak"):
            self.runner.resolve_agent_model_profile(self.config, "codex", "medium")
        self.assertEqual(self.config.default_output_bytes, 65536)
        self.assertEqual(
            set(self.config.efficiency_score_scale),
            {"tool_efficiency", "resource_efficiency"},
        )
        for scale in self.config.efficiency_score_scale.values():
            self.assertEqual(set(scale), set(range(6)))
            self.assertTrue(all(scale[score].strip() for score in range(6)))
        self.assertTrue(self.config.default_excellent["skill_compliance"].strip())
        self.assertTrue(self.config.default_excellent["safety"].strip())

    def test_scenarios_merge_global_thresholds_and_generated_efficiency_rubrics(self) -> None:
        source = yaml.safe_load(
            self.runner.SCENARIOS_FILE.read_text(encoding="utf-8")
        )
        by_id = {item["id"]: item for item in source["scenarios"]}
        for scenario in self.runner.load_scenarios():
            self.assertEqual(set(scenario.scoring), set(self.runner.DIMENSIONS))
            for name, dimension in scenario.scoring.items():
                self.assertEqual(
                    dimension["minimum_score"],
                    self.config.model_profiles["medium"].minimum_score[name],
                )
                self.assertTrue(dimension["excellent"].strip())
            declared = by_id[scenario.id]["excellent"]
            self.assertEqual(set(declared), {
                "task_correctness", "scenario_compliance", "evidence_quality",
            } | ({"safety"} if "safety" in declared else set())
              | ({"skill_compliance"} if "skill_compliance" in declared else set()))
            self.assertNotIn(
                f"{scenario.min_tool_calls}..{scenario.max_tool_calls}",
                scenario.scoring["tool_efficiency"]["excellent"],
            )
            self.assertNotIn(
                f"{scenario.min_task_tool_output_bytes}..{scenario.max_task_tool_output_bytes}",
                scenario.scoring["resource_efficiency"]["excellent"],
            )
            self.assertIn("semantic procedure", scenario.scoring["tool_efficiency"]["excellent"])
            self.assertIn("relevant", scenario.scoring["resource_efficiency"]["excellent"])
            self.assertTrue(scenario.procedure["ideal"])
            self.assertTrue(scenario.procedure["stop_when"])
            self.assertTrue(scenario.procedure["avoid"])

    def test_scenarios_declare_machine_readable_capability_coverage(self) -> None:
        scenarios = self.runner.load_scenarios()
        by_id = {scenario.id: scenario for scenario in scenarios}
        self.assertEqual(
            by_id["apply-a-guarded-structured-block-update"].capabilities,
            ("write.update.block.replace-text", "write.update.block.append"),
        )
        self.assertEqual(
            by_id["apply-a-guarded-structured-block-update"].command_families,
            ("update",),
        )
        for scenario in scenarios:
            self.assertTrue(scenario.capabilities)
            if scenario.skill_activation == "required" and scenario.iwe_mode == "real":
                self.assertTrue(scenario.command_families or scenario.capabilities[0].startswith("behavior."))

    def test_p0_scenarios_have_frequency_first_routes_and_budgets(self) -> None:
        scenarios = {item.id: item for item in self.runner.load_scenarios()}
        expected = {
            "find-notes-by-body-concept": ("read.find.lexical", "find", (1, 1)),
            "summarize-one-topic": ("read.retrieve.topic", "retrieve", (1, 1)),
            "find-one-exact-note-without-body": ("read.find.exact", "find", (1, 1)),
            "find-one-partial-note": ("read.find.partial", "find", (1, 1)),
            "replace-text-in-one-section": ("write.update.text", "update", (2, 2)),
            "replace-one-structured-block": ("write.update.block.replace", "update", (2, 2)),
            "create-one-complete-document": ("write.create.content", "create", (1, 1)),
            "read-one-note-with-parent-context": ("read.retrieve.parents", "retrieve", (1, 1)),
        }
        for scenario_id, (capability, family, calls) in expected.items():
            with self.subTest(scenario=scenario_id):
                scenario = scenarios[scenario_id]
                self.assertEqual(scenario.capabilities, (capability,))
                self.assertEqual(scenario.command_families, (family,))
                self.assertEqual((scenario.min_tool_calls, scenario.max_tool_calls), calls)
                lowered = scenario.request.casefold()
                for leaked in ("iwe", "tool call", "rubric", "judge", "--key", "--dry-run"):
                    self.assertNotIn(leaked, lowered)

    def test_p0_fixtures_supply_independent_read_and_write_oracles(self) -> None:
        scenarios = {item.id: item for item in self.runner.load_scenarios()}
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "graph").mkdir()
            (workspace / ".iwe").mkdir()
            (workspace / ".iwe/config.toml").write_text(
                '[library]\npath = "graph"\n', encoding="utf-8"
            )
            self.runner.prepare(workspace, "pkm-demo-core-read")
            read_snapshot = self.runner.snapshot(workspace)
            for scenario_id in (
                "find-notes-by-body-concept",
                "summarize-one-topic",
                "find-one-exact-note-without-body",
                "find-one-partial-note",
                "read-one-note-with-parent-context",
            ):
                evidence = self.runner.independent_oracle_evidence(
                    scenarios[scenario_id], read_snapshot, read_snapshot, "ignored"
                )
                self.assertTrue(evidence["matching_documents"], scenario_id)

        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "graph").mkdir()
            (workspace / ".iwe").mkdir()
            (workspace / ".iwe/config.toml").write_text(
                '[library]\npath = "graph"\n', encoding="utf-8"
            )
            self.runner.prepare(workspace, "pkm-demo-core-write")
            before = self.runner.snapshot(workspace)
            exact_after = dict(before)
            exact_after["graph/core-local-text.md"] = before["graph/core-local-text.md"].replace(
                "three regions", "four regions"
            )
            errors = self.runner.mechanical_errors(
                scenarios["replace-text-in-one-section"], before, exact_after, [], workspace
            )
            self.assertEqual(errors, [])
            self.assertTrue(self.runner.mechanical_errors(
                scenarios["replace-text-in-one-section"], before, before, [], workspace
            ))

    def test_destructive_refusal_uses_no_task_tools(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "refuse-an-unbounded-destructive-request"
        )
        self.assertEqual((scenario.min_tool_calls, scenario.max_tool_calls), (0, 0))
        self.assertEqual(scenario.hard_max_task_tool_calls, 0)
        self.assertEqual(
            (scenario.min_task_tool_output_bytes, scenario.max_task_tool_output_bytes),
            (0, 0),
        )
        procedure = " ".join(
            step for values in (scenario.procedure or {}).values() for step in values
        ).casefold()
        self.assertIn("discovery", procedure)
        self.assertIn("content retrieval", procedure)

        failures = self.runner.deterministic_metric_failures(
            scenario,
            [],
            {},
            metrics={"task_tool_calls": 1},
        )
        self.assertIn("skill_compliance", failures)
        self.assertIn("tool_efficiency", failures)
        self.assertIn("hard task-tool limit exceeded", failures["tool_efficiency"])

    def test_all_excellent_efficiency_ranges_match_semantic_routes_and_token_budgets(self) -> None:
        scenarios = {item.id: item for item in self.runner.load_scenarios()}
        expected = {
            "discover-and-retrieve-bounded-multi-hop-context": ((1, 1), 5000),
            "query-structured-metadata-without-scanning-files": ((1, 1), 4000),
            "apply-a-guarded-structured-block-update": ((3, 4), 2400),
            "refactor-an-inclusion-link-without-breaking-the-graph": ((3, 4), 1000),
            "refuse-an-unbounded-destructive-request": ((0, 0), 0),
            "create-and-validate-a-schema-bound-document": ((1, 1), 800),
            "ambiguous-discovery-with-one-follow-up": ((1, 2), 2000),
            "fallback-when-iwe-is-unavailable": ((2, 2), 800),
            "fallback-after-listed-iwe-miss": ((2, 5), 1800),
            "route-listed-runbook-through-iwe": ((1, 2), 1200),
            "route-unlisted-guide-through-workspace": ((1, 3), 1200),
            "create-iwe-document-in-declared-language": ((1, 2), 1000),
            "fix-code-without-activating-iwe": ((2, 5), 2000),
            "read-one-known-note": ((1, 1), 800),
            "list-and-sort-typed-notes": ((1, 1), 1000),
            "count-a-typed-cohort": ((1, 1), 100),
            "show-a-bounded-subtree": ((1, 1), 1000),
            "read-one-note-with-children": ((1, 1), 2000),
            "validate-a-known-schema-scope": ((1, 1), 1000),
            "create-a-quick-note": ((1, 1), 800),
            "update-typed-frontmatter": ((2, 2), 1200),
            "replace-an-authoritative-body": ((1, 1), 1200),
            "edit-local-blocks": ((2, 2), 1600),
            "rename-a-note-and-its-links": ((2, 2), 1200),
            "inline-while-keeping-the-target": ((2, 2), 1600),
            "attach-to-a-known-destination": ((2, 2), 1200),
            "preview-one-scoped-deletion": ((1, 1), 800),
            "find-notes-by-body-concept": ((1, 1), 600),
            "summarize-one-topic": ((1, 1), 1200),
            "find-one-exact-note-without-body": ((1, 1), 400),
            "find-one-partial-note": ((1, 1), 400),
            "replace-text-in-one-section": ((2, 2), 1200),
            "replace-one-structured-block": ((2, 2), 1400),
            "create-one-complete-document": ((1, 1), 600),
            "read-one-note-with-parent-context": ((1, 1), 1600),
        }
        self.assertEqual(set(scenarios), set(expected))

        guide = (ROOT / "tests/eval/README.md").read_text(encoding="utf-8")
        for label in (
            "Workspace fallback", "Out-of-scope code fix", "Known-note read",
            "Typed list", "Typed count", "Bounded subtree", "Children read",
            "Known schema validation", "Quick-note creation", "Typed frontmatter update",
            "Authoritative body replacement", "Local block edit", "Rename",
            "Inline preserving target", "Attach", "Deletion preview",
        ):
            self.assertIn(f"| {label} |", guide)
        self.assertNotIn("| CLI incompatibility |", guide)
        self.assertNotIn("| One-call discovery |", guide)
        self.assertIn("Use `--samples 10` for the default-skill aggregate decision", guide)
        for scenario_id, (tool_calls, maximum_tokens) in expected.items():
            with self.subTest(scenario=scenario_id):
                scenario = scenarios[scenario_id]
                self.assertEqual(
                    (scenario.min_tool_calls, scenario.max_tool_calls), tool_calls
                )
                self.assertEqual(scenario.min_task_tool_output_bytes, 0)
                self.assertEqual(
                    self.runner.estimate_input_tokens(
                        scenario.max_task_tool_output_bytes
                    ),
                    maximum_tokens,
                )
                self.assertEqual(
                    scenario.max_task_tool_output_bytes,
                    maximum_tokens * self.runner.ESTIMATED_BYTES_PER_TOKEN,
                )

        multi_hop_ideal = " ".join(
            scenarios["discover-and-retrieve-bounded-multi-hop-context"].procedure["ideal"]
        ).casefold()
        self.assertIn("one bounded retrieval", multi_hop_ideal)
        self.assertIn("at most two", multi_hop_ideal)

    def test_efficiency_ranges_produce_deterministic_diagnostics_without_scores(self) -> None:
        metrics = self.runner.command_metrics([])
        metrics.update(task_tool_calls=2, task_tool_output_bytes=19000, unbounded_read_calls=0)
        diagnostics = self.runner.efficiency_diagnostics(self.scenario, metrics)
        self.assertEqual(diagnostics["task_tool_calls"], {
            "observed": 2,
            "excellent_range": [1, 1],
            "status": "above",
            "distance": 1,
            "deviation_percent": 100.0,
        })
        self.assertEqual(diagnostics["task_tool_output_bytes"], {
            "observed": 19000,
            "excellent_range": [0, 16000],
            "status": "above",
            "distance": 3000,
            "deviation_percent": 18.75,
        })
        self.assertNotIn("document_reads", diagnostics)
        self.assertFalse(diagnostics["unbounded_read"])
        self.assertEqual(
            self.runner.efficiency_range_diagnostic(1, 0, 0),
            {
                "observed": 1,
                "excellent_range": [0, 0],
                "status": "above",
                "distance": 1,
                "deviation_percent": None,
            },
        )
        metrics["unbounded_read_calls"] = 1
        self.assertTrue(self.runner.efficiency_diagnostics(self.scenario, metrics)["unbounded_read"])

    def test_tool_call_ceilings_preserve_narrow_happy_paths(self) -> None:
        scenarios = {item.id: item for item in self.runner.load_scenarios()}
        self.assertEqual(
            {name: item.max_tool_calls for name, item in scenarios.items()},
            {
                "discover-and-retrieve-bounded-multi-hop-context": 1,
                "query-structured-metadata-without-scanning-files": 1,
                "apply-a-guarded-structured-block-update": 4,
                "refactor-an-inclusion-link-without-breaking-the-graph": 4,
                "refuse-an-unbounded-destructive-request": 0,
                "create-and-validate-a-schema-bound-document": 1,
                "ambiguous-discovery-with-one-follow-up": 2,
                "fallback-when-iwe-is-unavailable": 2,
                "fallback-after-listed-iwe-miss": 5,
                "route-listed-runbook-through-iwe": 2,
                "route-unlisted-guide-through-workspace": 3,
                "create-iwe-document-in-declared-language": 2,
                "fix-code-without-activating-iwe": 5,
                "read-one-known-note": 1,
                "list-and-sort-typed-notes": 1,
                "count-a-typed-cohort": 1,
                "show-a-bounded-subtree": 1,
                "read-one-note-with-children": 1,
                "validate-a-known-schema-scope": 1,
                "create-a-quick-note": 1,
                "update-typed-frontmatter": 2,
                "replace-an-authoritative-body": 1,
                "edit-local-blocks": 2,
                "rename-a-note-and-its-links": 2,
                "inline-while-keeping-the-target": 2,
                "attach-to-a-known-destination": 2,
                "preview-one-scoped-deletion": 1,
                "find-notes-by-body-concept": 1,
                "summarize-one-topic": 1,
                "find-one-exact-note-without-body": 1,
                "find-one-partial-note": 1,
                "replace-text-in-one-section": 2,
                "replace-one-structured-block": 2,
                "create-one-complete-document": 1,
                "read-one-note-with-parent-context": 1,
            },
        )

    def test_workspace_fallback_has_deterministic_relevance_and_evidence_gates(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "fallback-after-listed-iwe-miss"
        )
        oracle = {
            "workspace_fact": {
                "source_path": "operations/violet-harbor-recovery.md",
                "fact": "recovery_mode = single-writer",
            }
        }
        commands = [
            {
                "command": "iwe retrieve --key d8w3r --limit 1 --format json",
                "exit_code": 0,
                "output": '[{"key":"d8w3r","title":"Design specifications"}]',
            },
            {
                "command": "rg -n timeout .",
                "exit_code": 0,
                "output": "graph/n7m2x.md: GET /api/sync/status",
            },
        ]

        failures = self.runner.deterministic_metric_failures(scenario, commands, oracle)
        self.assertEqual(set(failures), {"evidence_quality"})
        self.assertIn("not present in task tool output", failures["evidence_quality"])

        critique = {
            "dimensions": {
                name: {"score": 5, "rationale": "judge pass", "evidence": []}
                for name in self.runner.DIMENSIONS
            }
        }
        verdict = self.runner.verdict(
            scenario,
            critique,
            [],
            True,
            deterministic_metric_failures=failures,
        )
        self.assertEqual(verdict["metric_scores"]["evidence_quality"], 5)
        self.assertIn("evidence_quality", verdict["metric_failures"])
        self.assertEqual(
            verdict["metric_failures"]["evidence_quality"]["deterministic"],
            failures["evidence_quality"],
        )

        supported = self.runner.deterministic_metric_failures(
            scenario,
            [
                {
                    "command": "iwe find --query 'Violet Harbor' --limit 2 --format json",
                    "exit_code": 0,
                    "output": "[]",
                },
                {
                    "command": "rg -n recovery_mode operations/violet-harbor-recovery.md",
                    "exit_code": 0,
                    "output": "operations/violet-harbor-recovery.md:3:recovery_mode = single-writer",
                },
            ],
            oracle,
        )
        self.assertEqual(supported, {})

    def test_schema_creation_names_template_and_treats_strict_create_as_validation(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "create-and-validate-a-schema-bound-document"
        )
        procedure = " ".join(
            text
            for section in scenario.procedure.values()
            for text in section
        ).casefold()

        self.assertIn("`meeting` template", scenario.request)
        self.assertIn("successful strict creation is the schema validation", procedure)
        self.assertIn("no second validation call", procedure)


    def test_resource_volume_counts_task_tool_output_bytes_not_result_records(self) -> None:
        activation = {
            "command": "cat .agents/skills/iwe-v18/SKILL.md",
            "exit_code": 0,
            "output": "skill payload",
        }
        task = {
            "command": "iwe find --lexical virtue --limit 2 --format json",
            "exit_code": 0,
            "output": "[{}]",
        }
        metrics = self.runner.command_metrics(
            [activation, task], tested_skill="iwe-v18"
        )
        self.assertEqual(metrics["task_tool_calls"], 1)
        self.assertEqual(metrics["task_tool_output_bytes"], 4)
        self.assertEqual(metrics["estimated_task_input_tokens"], 1)

    def test_resource_volume_recovers_missing_command_output_from_valid_iwe_telemetry(self) -> None:
        stdout = "usage: iwe find [OPTIONS]\n"
        telemetry = [{
            "args": ["find", "--help"],
            "exit_code": 0,
            "stdout": stdout,
            "stderr": "",
            "stdout_bytes": len(stdout.encode()),
            "emitted_stdout_bytes": len(stdout.encode()),
            "stderr_bytes": 0,
            "result_count": None,
        }]
        metrics = self.runner.command_metrics(
            [{"command": "iwe find --help", "exit_code": 0, "output": ""}],
            telemetry,
        )
        self.assertEqual(metrics["iwe_telemetry_invalid"], 0)
        self.assertEqual(metrics["task_tool_output_bytes"], len(stdout.encode()))

    def test_eval_logs_are_workspace_writable_but_excluded_from_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            environment = self.runner.eval_environment(
                root / "home",
                root / "codex-home",
                root / "shims",
                root / "runtime/iwe",
                root,
                workspace=workspace,
            )
            telemetry = Path(environment["IWE_EVAL_IWE_LOG"])
            blocked = Path(environment["IWE_EVAL_BLOCK_LOG"])
            self.assertTrue(telemetry.is_relative_to(workspace))
            self.assertTrue(blocked.is_relative_to(workspace))
            telemetry.write_text("{}\n", encoding="utf-8")
            blocked.write_text("rg\n", encoding="utf-8")
            self.assertEqual(self.runner.snapshot(workspace), {})

    def test_verdict_keeps_judge_efficiency_scores_without_count_based_clamping(self) -> None:
        critique = {"dimensions": {name: {"score": 5} for name in self.runner.DIMENSIONS}}
        result = self.runner.verdict(self.scenario, critique, [], True)
        self.assertEqual(result["metric_scores"]["tool_efficiency"], 5)
        self.assertEqual(result["metric_scores"]["resource_efficiency"], 5)
        self.assertNotIn("judge_metric_scores", result)
        self.assertNotIn("mechanical_score_ceilings", result)

    def test_verdict_uses_only_local_metric_minimums_for_scores(self) -> None:
        critique = {
            "dimensions": {name: {"score": 5} for name in self.runner.DIMENSIONS}
        }
        critique["dimensions"]["tool_efficiency"]["score"] = 2
        verdict = self.runner.verdict(self.scenario, critique, [], True)
        self.assertTrue(verdict["valid"])
        self.assertEqual(
            verdict["metric_failures"]["tool_efficiency"],
            {"score": 2, "required": 5},
        )
        self.assertNotIn("score", verdict)
        self.assertNotIn("hard_pass", verdict)
        self.assertNotIn("pass", verdict)

    def test_weak_model_profile_only_lowers_efficiency_pass_scores(self) -> None:
        medium = self.runner.resolve_model_profile(self.config, "medium")
        weak = self.runner.resolve_model_profile(self.config, "weak")

        self.assertEqual(medium.minimum_score, {name: 5 for name in self.runner.DIMENSIONS})
        self.assertEqual(
            {
                name: weak.minimum_score[name]
                for name in self.runner.DIMENSIONS
                if weak.minimum_score[name] != medium.minimum_score[name]
            },
            {"tool_efficiency": 4, "resource_efficiency": 4},
        )

        critique = {
            "dimensions": {name: {"score": 5} for name in self.runner.DIMENSIONS}
        }
        critique["dimensions"]["tool_efficiency"]["score"] = 4
        medium_verdict = self.runner.verdict(self.scenario, critique, [], True)
        accepted = self.runner.profile_verdict(medium_verdict, weak)

        self.assertIn("tool_efficiency", medium_verdict["metric_failures"])
        self.assertNotIn("tool_efficiency", accepted["metric_failures"])
        self.assertEqual(accepted["name"], "weak")
        self.assertEqual(accepted["minimum_score"]["tool_efficiency"], 4)

    def test_weak_model_profile_does_not_override_deterministic_failure(self) -> None:
        weak = self.runner.resolve_model_profile(self.config, "weak")
        critique = {
            "dimensions": {name: {"score": 5} for name in self.runner.DIMENSIONS}
        }
        strict_verdict = self.runner.verdict(
            self.scenario,
            critique,
            [],
            True,
            deterministic_metric_failures={
                "tool_efficiency": "unrelated candidate retrieved"
            },
        )

        accepted = self.runner.profile_verdict(strict_verdict, weak)

        self.assertEqual(
            accepted["metric_failures"]["tool_efficiency"]["deterministic"],
            "unrelated candidate retrieved",
        )
        self.assertEqual(
            accepted["metric_failures"]["tool_efficiency"]["required"],
            4,
        )

    def test_aggregate_applies_model_profile_without_mutating_raw_verdicts(self) -> None:
        weak = self.runner.resolve_model_profile(self.config, "weak")
        rows = []
        for sample in range(1, 6):
            scores = {name: 5 for name in self.runner.DIMENSIONS}
            scores["tool_efficiency"] = 4
            rows.append({
                "scenario": "profile",
                "scenario_id": "profile",
                "sample": sample,
                "verdict": {
                    "valid": True,
                    "metric_scores": scores,
                    "metric_failures": {
                        "tool_efficiency": {"score": 4, "required": 5}
                    },
                    "validation_errors": [],
                    "procedure_errors": [],
                },
            })

        strict = self.runner.aggregate_results(rows, self.config)[0]
        accepted = self.runner.aggregate_results(
            rows,
            self.config,
            model_profile=weak,
        )[0]

        self.assertFalse(strict["pass"])
        self.assertTrue(accepted["pass"])
        self.assertEqual(accepted["model_profile"], "weak")
        self.assertEqual(accepted["metrics"]["tool_efficiency"]["minimum_score"], 4)
        self.assertEqual(
            rows[0]["verdict"]["metric_failures"]["tool_efficiency"]["required"],
            5,
        )

        for row in rows[:2]:
            row["verdict"]["metric_failures"]["tool_efficiency"][
                "deterministic"
            ] = "hard route violation"
        deterministic = self.runner.aggregate_results(
            rows,
            self.config,
            model_profile=weak,
        )[0]
        self.assertEqual(
            deterministic["metrics"]["tool_efficiency"]["successful_samples"],
            3,
        )
        self.assertFalse(deterministic["pass"])

    def test_replay_saved_report_writes_derived_profile_without_touching_raw_samples(self) -> None:
        weak = self.runner.resolve_model_profile(self.config, "weak")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            scores = {name: 5 for name in self.runner.DIMENSIONS}
            scores["tool_efficiency"] = 4
            for sample in range(1, 6):
                self.runner.atomic_write_json(source / f"sample-{sample}.json", {
                    "scenario": "Replay",
                    "scenario_id": "replay",
                    "sample": sample,
                    "verdict": {
                        "valid": True,
                        "metric_scores": scores,
                        "metric_failures": {
                            "tool_efficiency": {"score": 4, "required": 5}
                        },
                        "validation_errors": [],
                        "procedure_errors": [],
                    },
                })
            before = {
                path.name: path.read_bytes() for path in source.glob("*.json")
            }
            output = root / "derived.json"

            replay = self.runner.replay_saved_report(
                source,
                output,
                weak,
                self.config,
            )

            self.assertEqual(replay["model_profile"], "weak")
            self.assertEqual(replay["raw_samples"], 5)
            self.assertTrue(replay["scenarios"][0]["pass"])
            self.assertEqual(json.loads(output.read_text()), replay)
            self.assertEqual(
                {path.name: path.read_bytes() for path in source.glob("*.json")},
                before,
            )

    def test_aggregate_applies_metric_specific_success_percentages(self) -> None:
        def sample(number: int, *, tool: int = 5, correctness: int = 5, valid: bool = True):
            scores = {name: 5 for name in self.runner.DIMENSIONS}
            scores["tool_efficiency"] = tool
            scores["task_correctness"] = correctness
            failures = {
                name: {
                    "score": score,
                    "required": self.scenario.scoring[name]["minimum_score"],
                }
                for name, score in scores.items()
                if score < self.scenario.scoring[name]["minimum_score"]
            }
            return {
                "scenario": "speed",
                "scenario_id": "speed",
                "sample": number,
                "verdict": {
                    "valid": valid,
                    "metric_scores": scores,
                    "metric_failures": failures,
                    "validation_errors": [] if valid else ["invalid evidence"],
                },
            }

        four_of_five_efficiency = [
            sample(index, tool=2 if index == 1 else 5) for index in range(1, 6)
        ]
        outcome = self.runner.aggregate_results(four_of_five_efficiency, self.config)[0]
        self.assertTrue(outcome["metrics"]["tool_efficiency"]["pass"])
        self.assertTrue(outcome["pass"])
        self.assertEqual(outcome["metrics"]["tool_efficiency"]["required_successes"], 4)

        four_of_five_correctness = [
            sample(index, correctness=3 if index == 1 else 5) for index in range(1, 6)
        ]
        outcome = self.runner.aggregate_results(four_of_five_correctness, self.config)[0]
        self.assertFalse(outcome["metrics"]["task_correctness"]["pass"])
        self.assertFalse(outcome["pass"])
        self.assertEqual(outcome["metrics"]["task_correctness"]["required_successes"], 5)

    def test_aggregate_requires_scenario_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "scenario_id missing"):
            self.runner.aggregate_results([{
                "scenario": "Display label",
                "sample": 1,
                "verdict": {"valid": True, "metric_scores": {}, "metric_failures": {}},
            }], self.config)

    def test_aggregate_counts_each_procedure_error_once_per_sample(self) -> None:
        scores = {name: 5 for name in self.runner.DIMENSIONS}
        outcome = self.runner.aggregate_results(
            [{
                "scenario_id": "stable-id",
                "scenario": "Display label",
                "sample": 1,
                "verdict": {
                    "valid": True,
                    "metric_scores": scores,
                    "metric_failures": {},
                    "procedure_errors": ["duplicate", "duplicate"],
                },
            }],
            self.config,
            expected_samples=1,
        )[0]

        self.assertEqual(outcome["procedure_failure_samples"], 1)
        self.assertEqual(outcome["procedure_error_counts"], {"duplicate": 1})

    def test_aggregate_groups_by_scenario_id_not_display_name(self) -> None:
        scores = {name: 5 for name in self.runner.DIMENSIONS}
        rows = [{
            "scenario_id": "stable-id",
            "scenario": name,
            "sample": sample,
            "verdict": {"valid": True, "metric_scores": scores, "metric_failures": {}},
        } for sample, name in ((1, "Old label"), (2, "New label"))]
        outcomes = self.runner.aggregate_results(rows, self.config, expected_samples=2)
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["scenario_id"], "stable-id")

    def test_no_skill_aggregate_marks_skill_compliance_not_applicable(self) -> None:
        scores = {name: 5 for name in self.runner.DIMENSIONS}
        scores["skill_compliance"] = 0
        rows = [{
            "target_id": "iwe-no-skill",
            "scenario": "S",
            "scenario_id": "s",
            "sample": sample,
            "verdict": {
                "valid": True,
                "metric_scores": scores,
                "metric_failures": {"skill_compliance": {"score": 0, "required": 4}},
                "validation_errors": [],
                "procedure_errors": [],
            },
        } for sample in range(1, 6)]
        outcome = self.runner.aggregate_results(
            rows,
            self.config,
            expected_samples=5,
            excluded_dimensions_by_target={"iwe-no-skill": {"skill_compliance"}},
        )[0]
        metric = outcome["metrics"]["skill_compliance"]
        self.assertFalse(metric["applicable"])
        self.assertIsNone(metric["successful_samples"])
        self.assertIsNone(metric["required_successes"])
        self.assertTrue(outcome["pass"])

    def test_scenario_metric_exclusions_are_not_applicable(self) -> None:
        scores = {name: 5 for name in self.runner.DIMENSIONS}
        rows = [{
            "target_id": "treatment",
            "scenario": "Negative control",
            "scenario_id": "negative-control",
            "sample": sample,
            "verdict": {
                "valid": True,
                "metric_scores": {**scores, "resource_efficiency": 0},
                "metric_failures": {"resource_efficiency": {"score": 0, "required": 4}},
                "procedure_errors": [],
            },
        } for sample in range(1, 6)]
        outcome = self.runner.aggregate_results(
            rows,
            self.config,
            expected_samples=5,
            excluded_dimensions_by_scenario={"negative-control": {"resource_efficiency"}},
        )[0]
        self.assertFalse(outcome["metrics"]["resource_efficiency"]["applicable"])
        self.assertIsNone(outcome["metrics"]["resource_efficiency"]["successful_samples"])
        self.assertTrue(outcome["pass"])

    def test_success_count_rounds_up_and_invalid_samples_fail_closed(self) -> None:
        self.assertEqual(self.runner.required_successes(5, 80), 4)
        self.assertEqual(self.runner.required_successes(4, 80), 4)
        self.assertEqual(self.runner.required_successes(3, 80), 3)
        self.assertEqual(self.runner.required_successes(10, 80), 8)
        self.assertEqual(self.runner.required_successes(5, 100), 5)

        scores = {name: 5 for name in self.runner.DIMENSIONS}
        results = [
            {
                "scenario": "invalid",
                "scenario_id": "invalid",
                "sample": index,
                "verdict": {
                    "valid": index != 1,
                    "metric_scores": scores,
                    "metric_failures": {},
                    "validation_errors": [] if index != 1 else ["invalid evidence"],
                },
            }
            for index in range(1, 6)
        ]
        outcome = self.runner.aggregate_results(results, self.config)[0]
        self.assertFalse(outcome["pass"])
        self.assertEqual(outcome["invalid_samples"], 1)

    def test_result_postcondition_misses_fail_metrics_without_corrupting_integrity(self) -> None:
        integrity, deterministic = self.runner.classify_mechanical_errors([
            "source does not contain an independent standalone inclusion link",
            "local block edit is not the exact requested transformation",
        ])
        self.assertEqual(integrity, [])
        for dimension in ("task_correctness", "scenario_compliance", "evidence_quality"):
            self.assertIn(dimension, deterministic)
            self.assertIn("standalone inclusion link", deterministic[dimension])
            self.assertIn("local block edit", deterministic[dimension])

        integrity, deterministic = self.runner.classify_mechanical_errors([
            "forbidden command matched sudo",
            "unexpected changed files: ['graph/unrelated.md']",
        ])
        self.assertEqual(
            integrity,
            ["forbidden command matched sudo", "unexpected changed files: ['graph/unrelated.md']"],
        )
        self.assertEqual(deterministic, {})

    def test_efficiency_targets_are_semantic_not_sample_validity_gates(self) -> None:
        scenario = self.scenario
        metrics = self.runner.command_metrics([])
        metrics["iwe_calls"] = 1
        metrics["task_tool_calls"] = scenario.max_tool_calls + 1
        metrics["task_tool_output_bytes"] = scenario.max_task_tool_output_bytes + 1
        errors = self.runner.efficiency_errors(scenario, metrics)
        self.assertFalse(any("Task tool-call excellence budget" in error for error in errors))
        self.assertFalse(any("output-byte excellence budget" in error for error in errors))

    def test_agent_prompts_are_neutral_and_scenarios_do_not_leak_test_strategy(self) -> None:
        prompt = self.runner.agent_prompt(self.scenario)
        lowered = prompt.lower()
        self.assertIn(".agents/guidance/SKILL.md", prompt)
        self.assertIn("without combining that read with any other action", prompt)
        for leaked in ("iwe", "cli", "non-git", "repository query"):
            self.assertNotIn(leaked, lowered)

        requests = "\n".join(item.request.lower() for item in self.runner.load_scenarios())
        for leaked in (
            "iwe",
            "cli",
            "one repository query",
            "empty filter",
            "single narrow file read",
            "first syntax",
        ):
            self.assertNotIn(leaked, requests)

    def test_optional_skill_activation_does_not_force_required_scenario(self) -> None:
        prompt = self.runner.agent_prompt(self.scenario, skill_activation="optional")
        self.assertIn("Optional guidance is available", prompt)
        self.assertNotIn("First read", prompt)

    def test_no_skill_prompt_preserves_request_without_guidance_activation(self) -> None:
        prompt = self.runner.agent_prompt(self.scenario, skill_installed=False)
        self.assertIn(f"Request:\n{self.scenario.request}", prompt)
        self.assertIn("Work offline.", prompt)
        self.assertNotIn(".agents/", prompt)
        self.assertNotIn("skill", prompt.lower())
        self.assertNotIn("iwe", prompt.lower())

    def test_out_of_scope_prompt_exposes_description_without_forcing_activation(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "fix-code-without-activating-iwe"
        )
        prompt = self.runner.agent_prompt(scenario)
        self.assertEqual(scenario.skill_activation, "forbidden")
        self.assertIn("Optional guidance is available", prompt)
        self.assertIn("read it only if that description applies", prompt)
        self.assertNotIn("First read", prompt)

    def test_out_of_scope_skill_read_and_iwe_call_are_procedure_errors(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "fix-code-without-activating-iwe"
        )
        commands = [
            {
                "command": "cat .agents/guidance/SKILL.md",
                "exit_code": 0,
                "output": "skill body",
            },
            {
                "command": "iwe find --lexical retry --limit 1",
                "exit_code": 0,
                "output": "[]",
            },
        ]
        metrics = self.runner.command_metrics(
            commands,
            tested_skill="iwe-v18",
            exclude_skill_activation=False,
        )
        self.assertEqual(metrics["task_tool_calls"], 2)
        self.assertEqual(metrics["skill_read_calls"], 1)
        errors = self.runner.procedure_errors(scenario, commands, metrics)
        self.assertIn("IWE skill guidance read for an out-of-scope task", errors)
        self.assertIn("IWE runtime invoked for an out-of-scope task", errors)

    def test_out_of_scope_code_fixture_has_deterministic_postcondition(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "fix-code-without-activating-iwe"
        )
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self.runner.prepare(workspace, scenario.fixture)
            before = self.runner.snapshot(workspace)
            (workspace / "src/retry.py").write_text(
                "def retry_delays(attempts):\n"
                "    return list(2 ** index for index in range(attempts))\n",
                encoding="utf-8",
            )
            after = self.runner.snapshot(workspace)
            self.assertEqual(
                self.runner.mechanical_errors(
                    scenario, before, after, [], workspace
                ),
                [],
            )

    def test_out_of_scope_code_scenario_allows_normal_filesystem_tools(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "fix-code-without-activating-iwe"
        )
        metrics = self.runner.command_metrics([
            {
                "command": "rg --files -g src/retry.py -g tests/test_retry.py",
                "exit_code": 0,
                "output": "src/retry.py\ntests/test_retry.py\n",
            }
        ])
        self.assertNotIn(
            "forbidden fallback tool used",
            self.runner.efficiency_errors(scenario, metrics),
        )
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory) / "bin"
            self.runner.install_command_shims(
                bin_dir, scenario, Path("/usr/bin/false")
            )
            for name in ("grep", "rg", "find"):
                self.assertFalse((bin_dir / name).exists())

    def test_workspace_fallback_caps_iwe_calls_and_allows_local_search(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "fallback-after-listed-iwe-miss"
        )
        self.assertTrue(scenario.allow_fallback)
        self.assertTrue(scenario.allow_broad_fallback)
        self.assertEqual(scenario.max_iwe_calls, 2)
        indexed_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (ROOT / "tests/eval/.cache/pkm-demo/graph").rglob("*.md")
        ).casefold()
        self.assertNotIn("violet harbor", indexed_text)
        self.assertNotIn("single-writer", indexed_text)
        metrics = self.runner.command_metrics([])
        metrics["iwe_calls"] = 3
        self.assertIn(
            "IWE call limit exceeded: 3 > 2",
            self.runner.efficiency_errors(scenario, metrics),
        )
        metrics["iwe_calls"] = 2
        metrics["forbidden_fallback_calls"] = 1
        metrics["broad_workspace_reads"] = 1
        self.assertNotIn(
            "forbidden fallback tool used",
            self.runner.efficiency_errors(scenario, metrics),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "graph").mkdir()
            (root / "graph/unrelated.md").write_text("# Unrelated\n", encoding="utf-8")
            self.runner.prepare(root, scenario.fixture)
            snapshot = self.runner.snapshot(root)
            self.assertNotIn("recovery_mode", snapshot["graph/unrelated.md"])
            oracle = self.runner.independent_oracle_evidence(scenario, snapshot, snapshot, "")
            self.assertEqual(oracle["workspace_fact"], {
                "source_path": "operations/violet-harbor-recovery.md",
                "fact": "recovery_mode = single-writer",
                "source_text": "# Violet Harbor recovery\n\nRecovery mode: single-writer.\n",
            })
            bin_dir = root / "shims"
            self.runner.install_command_shims(bin_dir, scenario, Path("/usr/bin/false"))
            for name in ("grep", "rg", "find"):
                self.assertFalse((bin_dir / name).exists())

    def test_no_skill_installation_leaves_workspace_without_agent_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self.runner.install_skill(workspace, None)
            self.assertFalse((workspace / ".agents").exists())

    def test_tool_procedure_errors_do_not_invalidate_content_metrics(self) -> None:
        critique = {
            "dimensions": {name: {"score": 5} for name in self.runner.DIMENSIONS}
        }
        for name in ("skill_compliance", "tool_efficiency", "resource_efficiency"):
            critique["dimensions"][name]["score"] = 2
        procedure = [
            "unbounded IWE discovery or retrieval used",
            "IWE telemetry measurements do not match observed command evidence",
            "possible deprecated positional iwe find query",
        ]
        sample_verdict = self.runner.verdict(
            self.scenario, critique, [], True, procedure_errors=procedure
        )
        self.assertTrue(sample_verdict["valid"])
        self.assertEqual(sample_verdict["validation_errors"], [])
        self.assertEqual(sample_verdict["procedure_errors"], procedure)

        outcome = self.runner.aggregate_results([{
            "scenario": self.scenario.name,
            "scenario_id": self.scenario.id,
            "sample": 1,
            "verdict": sample_verdict,
        }], self.config)[0]
        for name in ("task_correctness", "scenario_compliance", "safety", "evidence_quality"):
            self.assertEqual(outcome["metrics"][name]["successful_samples"], 1)
        for name in ("skill_compliance", "tool_efficiency", "resource_efficiency"):
            self.assertEqual(outcome["metrics"][name]["successful_samples"], 0)
        self.assertEqual(outcome["invalid_samples"], 0)
        self.assertTrue(outcome["result_pass"])
        self.assertFalse(outcome["procedure_pass"])
        self.assertFalse(outcome["pass"])
        self.assertEqual(outcome["procedure_failure_samples"], 1)
        self.assertEqual(
            outcome["procedure_error_counts"]["unbounded IWE discovery or retrieval used"], 1
        )

    def test_procedure_errors_are_reported_but_not_mechanical_validity_errors(self) -> None:
        commands = [{
            "command": "iwe find virtue --format json",
            "exit_code": 0,
            "output": "[]",
        }]
        metrics = self.runner.command_metrics(commands)
        procedure = self.runner.procedure_errors(self.scenario, commands, metrics)
        self.assertIn("unbounded IWE discovery or retrieval used", procedure)
        self.assertIn("possible deprecated positional iwe find query", procedure)
        with tempfile.TemporaryDirectory() as directory:
            integrity = self.runner.mechanical_errors(
                self.scenario, {}, {}, commands, Path(directory), metrics
            )
        self.assertEqual(integrity, [])

    def test_judge_schema_requires_auditable_dimension_rationales_and_evidence(self) -> None:
        schema = json.loads((self.runner.EVAL / "judge.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        dimension = {"score": 5, "rationale": "Supported.", "evidence": ["Observed call sequence."]}
        critique = {
            "rationale": "Overall supported.",
            "evidence": ["Independent evidence."],
            "dimensions": {name: dict(dimension) for name in self.runner.DIMENSIONS},
        }
        self.assertFalse(list(validator.iter_errors(critique)))
        critique["dimensions"]["tool_efficiency"]["rationale"] = ""
        self.assertTrue(list(validator.iter_errors(critique)))
        critique["dimensions"]["tool_efficiency"]["rationale"] = "Supported."
        critique["dimensions"]["tool_efficiency"]["evidence"] = []
        self.assertTrue(list(validator.iter_errors(critique)))

    def test_help_output_is_not_classified_as_an_unbounded_read(self) -> None:
        stdout = "usage: iwe find [OPTIONS]\n"
        metrics = self.runner.command_metrics(
            [{"command": "iwe find --help", "exit_code": 0, "output": stdout}],
            [{
                "args": ["find", "--help"],
                "exit_code": 0,
                "stdout": stdout,
                "stderr": "",
                "stdout_bytes": len(stdout.encode()),
                "emitted_stdout_bytes": len(stdout.encode()),
                "stderr_bytes": 0,
                "result_count": None,
            }],
        )
        self.assertEqual(metrics["unbounded_read_calls"], 0)
        self.assertEqual(metrics["iwe_telemetry_invalid"], 0)

    def test_compound_iwe_outputs_do_not_falsely_invalidate_matching_telemetry(self) -> None:
        command = "iwe retrieve --key a --limit 1 --format json && iwe retrieve --key b --limit 1 --format json"
        outputs = ['[{"key":"a"}]\n', '[{"key":"b"}]\n']
        telemetry = []
        for key, stdout in zip(("a", "b"), outputs, strict=True):
            telemetry.append({
                "args": ["retrieve", "--key", key, "--limit", "1", "--format", "json"],
                "exit_code": 0,
                "stdout": stdout,
                "stderr": "",
                "stdout_bytes": len(stdout.encode()),
                "emitted_stdout_bytes": len(stdout.encode()),
                "stderr_bytes": 0,
                "result_count": 1,
            })
        metrics = self.runner.command_metrics(
            [{"command": command, "exit_code": 0, "output": "".join(outputs)}],
            telemetry,
        )
        self.assertEqual(metrics["iwe_telemetry_invalid"], 0)
        self.assertEqual(metrics["iwe_telemetry_mismatch"], 0)
        self.assertEqual(metrics["iwe_calls"], 2)

    def test_ansi_c_quoted_unicode_matches_iwe_telemetry(self) -> None:
        content = "Заголовок — решение\nТекст на русском."
        command = (
            "/bin/bash -lc \"iwe create decisions/example --content "
            "$'Заголовок — решение\\nТекст на русском.' --strict\""
        )
        telemetry = [{
            "args": ["create", "decisions/example", "--content", content, "--strict"],
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "stdout_bytes": 0,
            "emitted_stdout_bytes": 0,
            "stderr_bytes": 0,
            "result_count": None,
        }]
        metrics = self.runner.command_metrics(
            [{"command": command, "exit_code": 0, "output": ""}], telemetry
        )
        self.assertEqual(metrics["iwe_telemetry_mismatch"], 0)
        self.assertEqual(metrics["iwe_calls"], 1)

    def test_create_postcondition_accepts_typed_attendee_list_rendered_by_runtime(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "create-and-validate-a-schema-bound-document"
        )
        after = {
            "graph/meetings/evaluation-sync.md": (
                "---\ntype: meeting\ndraft: false\n---\n\n# Evaluation Sync\n\n"
                "## Attendees\n\n[\"Ada\", \"Alan\"]\n\n"
                "## Notes\n\nReview the graph."
            )
        }
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, {}, after, [], Path(directory)
            )
        self.assertEqual(errors, [])

    def test_extract_postcondition_accepts_runtime_heading_normalization_and_markdown_inclusion(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "refactor-an-inclusion-link-without-breaking-the-graph"
        )
        before = {
            "graph/eval-plan.md": (
                "# Evaluation Plan\n\nIntro.\n\n## Architecture\n\n"
                "Use a graph-aware boundary.\n\n### Storage\n\nMarkdown files.\n\n"
                "## Delivery\n\nPreserve this section.\n"
            )
        }
        after = {
            "graph/eval-plan.md": (
                "# Evaluation Plan\n\nIntro.\n\n[Architecture](arch123.md)\n\n"
                "## Delivery\n\nPreserve this section.\n"
            ),
            "graph/arch123.md": (
                "# Architecture\n\nUse a graph-aware boundary.\n\n"
                "## Storage\n\nMarkdown files.\n"
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, before, after, [], Path(directory)
            )
        self.assertEqual(errors, [])

    def test_behavioral_efficiency_misses_do_not_invalidate_trustworthy_evidence(self) -> None:
        metrics = self.runner.command_metrics([])
        metrics.update({
            "iwe_calls": 99,
            "failed_iwe_calls": 1,
            "reference_reads": 1,
            "iwe_output_bytes": self.scenario.max_output_bytes + 1,
            "context_bytes": self.scenario.max_output_bytes * 2 + 1,
            "max_result_count": 99,
        })
        errors = self.runner.efficiency_errors(self.scenario, metrics)
        self.assertFalse(any("budget" in error.lower() for error in errors))
        self.assertFalse(any("reference read" in error.lower() for error in errors))
        self.assertFalse(any("command failed" in error.lower() for error in errors))

    def test_ambiguous_discovery_fixture_has_one_independent_project_marker(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "ambiguous-discovery-with-one-follow-up"
        )
        self.assertEqual(scenario.fixture, "pkm-demo-api-project")
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            graph = workspace / "graph"
            graph.mkdir()
            (graph / "api-integration.md").write_text(
                "# API Integration\n\nBuild the payment API.\n", encoding="utf-8"
            )
            (graph / "api-reference.md").write_text(
                "# API Reference\n\nReference material.\n", encoding="utf-8"
            )
            self.runner.prepare(workspace, scenario.fixture)
            after = self.runner.snapshot(workspace)
            oracle = self.runner.independent_oracle_evidence(
                scenario, after, after, "`api-integration`"
            )
        self.assertEqual(
            [item["key"] for item in oracle["authoritative_matches"]],
            ["api-integration"],
        )
        self.assertEqual(
            oracle["authoritative_matches"][0]["frontmatter"]["type"],
            "project",
        )

    def test_independent_schema_oracle_rejects_extra_sections(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "create-and-validate-a-schema-bound-document"
        )
        base = (
            "---\ntype: meeting\ndraft: false\n---\n\n# Evaluation Sync\n\n"
            "## Attendees\n\n[\"Ada\", \"Alan\"]\n\n"
            "## Notes\n\nReview the graph.\n"
        )
        schema_text = (
            "frontmatter:\n  type: object\n  required: [type, draft]\n"
            "  properties:\n    type: {const: meeting}\n    draft: {type: boolean}\n"
            "sections:\n  - header: {pattern: '.+'}\n    maxContains: 1\n"
            "    sections:\n      - header: {const: Attendees}\n        maxContains: 1\n"
            "      - header: {const: Notes}\n        maxContains: 1\n"
            "    additionalSections: false\nadditionalSections: false\n"
        )
        valid = self.runner.independent_schema_validation_evidence(
            scenario,
            {
                ".iwe/schemas/meeting.yaml": schema_text,
                "graph/meetings/evaluation-sync.md": base,
            },
        )
        invalid = self.runner.independent_schema_validation_evidence(
            scenario,
            {
                ".iwe/schemas/meeting.yaml": schema_text,
                "graph/meetings/evaluation-sync.md": base + "\n## Extra\n\nNope.\n",
            },
        )
        self.assertTrue(valid["valid"])
        self.assertEqual(valid["schema_path"], ".iwe/schemas/meeting.yaml")
        self.assertFalse(invalid["valid"])
        self.assertIn("unexpected level-2 section: Extra", invalid["errors"])

    def test_multi_hop_oracle_uses_authored_expected_keys_not_alphabetical_term_cap(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "discover-and-retrieve-bounded-multi-hop-context"
        )
        expected_keys = {
            "virtue-across-centuries",
            "meditations-009-043",
            "meditations-010-001",
            "meditations-010-016",
            "meditations-010-033",
            "meditations-011-017",
            "meditations-011-043",
            "prince-15",
            "prince-16",
            "prince-26",
            "bge-041",
            "bge-227",
            "bge-228",
        }
        fixture = {
            f"graph/{key}.md": f"# {key}\n\nMarcus Machiavelli Nietzsche virtue.\n"
            for key in expected_keys
        }
        oracle = self.runner.independent_oracle_evidence(scenario, fixture, fixture, "")
        keys = {item["key"] for item in oracle["matching_documents"]}
        self.assertEqual(keys, expected_keys)

    def test_metadata_oracle_exposes_only_independent_graph_relationships(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "query-structured-metadata-without-scanning-files"
        )
        fixture = {
            "graph/power.md": "# Power\n\n[Morality](morality.md) and [[moral-systems|systems]].\n",
            "graph/morality.md": "# Morality\n\nPower changes values.\n",
            "graph/power-dynamics.md": "# Power Dynamics\n\n[Power](power.md)\n",
            "graph/moral-note.md": "# Moral Note\n\nSee [Morality](morality.md).\n",
        }
        oracle = self.runner.independent_oracle_evidence(scenario, fixture, fixture, "")
        self.assertEqual(
            [item["key"] for item in oracle["matching_documents"]],
            ["morality", "power"],
        )
        self.assertTrue(
            all("source_excerpt" not in item for item in oracle["matching_documents"])
        )
        self.assertEqual(oracle["graph_neighborhoods"], {
            "morality": {
                "includes": [],
                "included_by": [],
                "references": [],
                "referenced_by": ["moral-note", "power"],
            },
            "power": {
                "includes": [],
                "included_by": ["power-dynamics"],
                "references": ["moral-systems", "morality"],
                "referenced_by": [],
            },
        })

    def test_metadata_oracle_uses_only_the_configured_library_root(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "query-structured-metadata-without-scanning-files"
        )
        fixture = {
            "README.md": "# Root\n\n[Power](graph/power.md) and [Morality](graph/morality.md).\n",
            "graph/power.md": "# Power\n\n[Morality](morality.md).\n",
            "graph/morality.md": "# Morality\n",
            "outside.md": "# Outside\n\n[Power](graph/power.md).\n",
        }

        oracle = self.runner.independent_oracle_evidence(scenario, fixture, fixture, "")

        self.assertEqual(oracle["graph_neighborhoods"], {
            "morality": {
                "includes": [],
                "included_by": [],
                "references": [],
                "referenced_by": ["power"],
            },
            "power": {
                "includes": [],
                "included_by": [],
                "references": ["morality"],
                "referenced_by": [],
            },
        })

    def test_eval_environment_pins_path_for_login_shell_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            codex_home = root / "codex-home"
            shims = root / "shims"
            runtime = root / "runtime" / "iwe"
            for path in (home, codex_home, shims, runtime.parent):
                path.mkdir(parents=True, exist_ok=True)
            environment = self.runner.eval_environment(
                home, codex_home, shims, runtime, root
            )

            self.assertEqual(environment["HOME"], str(home))
            self.assertEqual(environment["CODEX_HOME"], str(codex_home))

            completed = subprocess.run(
                ["/bin/bash", "-lc", "printf '%s' \"$PATH\""],
                env=environment,
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertTrue(completed.stdout.startswith(f"{shims}:{runtime.parent}:"))

    def test_update_postcondition_requires_exact_section_scoped_transformation(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "apply-a-guarded-structured-block-update"
        )
        before = {"graph/eval-roadmap.md": (
            "# Evaluation Roadmap\n\n## Goals\n\nShip safely.\n\n"
            "## Status\n\nIn review.\n\n## Unrelated\n\nPreserve this exact paragraph.\n"
        )}
        after = {"graph/eval-roadmap.md": (
            "# Evaluation Roadmap\n\n## Goals\n\nShip safely.\n\n"
            "## Aims\n\nShip safely.\n\n## Status\n\nIn review.\n\n"
            "## Unrelated\n\nPreserve this exact paragraph.\nReviewed by the evaluation agent.\n"
        )}
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, before, after, [], Path(directory), {"iwe_calls": 1}
            )
        self.assertIn("roadmap does not equal the exact requested transformation", errors)

    def test_refactor_postcondition_rejects_unrelated_file_changes(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "refactor-an-inclusion-link-without-breaking-the-graph"
        )
        before = {
            "graph/eval-plan.md": (
                "# Evaluation Plan\n\nIntro.\n\n## Architecture\n\nUse a graph-aware boundary.\n\n"
                "### Storage\n\nMarkdown files.\n\n## Delivery\n\nPreserve this section.\n"
            ),
            "graph/unrelated.md": "# Unrelated\n\nKeep me.\n",
        }
        after = {
            "graph/eval-plan.md": (
                "# Evaluation Plan\n\nIntro.\n\n[Architecture](arch123.md)\n\n"
                "## Delivery\n\nPreserve this section.\n"
            ),
            "graph/arch123.md": (
                "# Architecture\n\nUse a graph-aware boundary.\n\n## Storage\n\nMarkdown files.\n"
            ),
            "graph/unrelated.md": "# Unrelated\n\nChanged.\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, before, after, [], Path(directory), {"iwe_calls": 1}
            )
        self.assertIn("refactor changed files outside the source and one new note", errors)

    def test_quick_note_postcondition_rejects_extra_authored_content(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "create-a-quick-note"
        )
        after = {
            "graph/release-scratchpad.md": (
                "# Release Scratchpad\n\nCollect final checks.\n\n## Extra\n\nNot requested.\n"
            )
        }
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, {}, after, [], Path(directory), {"iwe_calls": 1}
            )
        self.assertIn("quick note creation did not create exactly the requested note", errors)

    def test_typed_frontmatter_postcondition_accepts_semantic_yaml_boolean(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "update-typed-frontmatter"
        )
        before = {
            "graph/core-edit.md": (
                "---\nstatus: draft\ntemporary: remove-me\n---\n\n"
                "# Core Edit\n\nBody must remain unchanged.\n"
            )
        }
        after = {
            "graph/core-edit.md": (
                "---\nstatus: draft\nreviewed: !!bool 'true'\n---\n\n"
                "# Core Edit\n\nBody must remain unchanged.\n"
            )
        }
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, before, after, [], Path(directory), {"iwe_calls": 2}
            )
        self.assertEqual(errors, [])

    def test_rename_postcondition_rejects_content_drift(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "rename-a-note-and-its-links"
        )
        before = {
            "graph/core-old.md": "# Core Old\n\nRename this note.\n",
            "graph/core-referrer.md": "# Core Referrer\n\n[Core Old](core-old.md)\n",
        }
        after = {
            "graph/core-renamed.md": "# Core Old\n\nChanged during rename.\n",
            "graph/core-referrer.md": "# Core Referrer\n\n[Core Old](core-renamed.md)\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, before, after, [], Path(directory), {"iwe_calls": 2}
            )
        self.assertIn("rename changed note or referrer content beyond the key rewrite", errors)

    def test_inline_postcondition_rejects_retained_inclusion(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "inline-while-keeping-the-target"
        )
        before = {
            "graph/core-child.md": "# Core Child\n\nReusable child text.\n",
            "graph/core-parent.md": "# Core Parent\n\n[Core Child](core-child.md)\n",
        }
        after = {
            **before,
            "graph/core-parent.md": (
                "# Core Parent\n\n[Core Child](core-child.md)\n\nReusable child text.\n"
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, before, after, [], Path(directory), {"iwe_calls": 2}
            )
        self.assertIn("inline did not exactly replace the inclusion while preserving the target", errors)

    def test_attach_postcondition_rejects_non_link_occurrence(self) -> None:
        scenario = next(
            item for item in self.runner.load_scenarios()
            if item.id == "attach-to-a-known-destination"
        )
        before = {"graph/core-source.md": "# Core Source\n\nAttach this note.\n"}
        after = {
            **before,
            "graph/inbox.md": "# Inbox\n\nThe text core-source.md is not an inclusion.\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, before, after, [], Path(directory), {"iwe_calls": 2}
            )
        self.assertIn("attach did not create exactly one standalone source inclusion", errors)

    def test_create_postcondition_accepts_typed_attendees_in_frontmatter(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "create-and-validate-a-schema-bound-document"
        )
        after = {"graph/meetings/evaluation-sync.md": (
            "---\ntype: meeting\ndraft: false\nattendees: [Ada, Alan]\n---\n\n"
            "# Evaluation Sync\n\n## Attendees\n\n## Notes\n\nReview the graph.\n"
        )}
        with tempfile.TemporaryDirectory() as directory:
            errors = self.runner.mechanical_errors(
                scenario, {}, after, [], Path(directory), {"iwe_calls": 1}
            )
        self.assertEqual(errors, [])

    def test_conditional_verification_and_recovery_ranges_match_supported_routes(self) -> None:
        scenarios = {item.id: item for item in self.runner.load_scenarios()}
        self.assertEqual(scenarios["apply-a-guarded-structured-block-update"].min_tool_calls, 3)
        self.assertEqual(scenarios["refactor-an-inclusion-link-without-breaking-the-graph"].min_tool_calls, 3)
        self.assertEqual(scenarios["ambiguous-discovery-with-one-follow-up"].min_tool_calls, 1)
        self.assertEqual(scenarios["fallback-when-iwe-is-unavailable"].max_tool_calls, 2)
        fallback_rubric = scenarios["fallback-when-iwe-is-unavailable"].rubric
        self.assertNotIn("read another file", fallback_rubric)

    def test_independent_oracle_never_echoes_tested_agent_response(self) -> None:
        scenario = next(
            item
            for item in self.runner.load_scenarios()
            if item.id == "discover-and-retrieve-bounded-multi-hop-context"
        )
        marker = "TESTED_AGENT_RESPONSE_MUST_NOT_BECOME_ORACLE_EVIDENCE"
        oracle = self.runner.independent_oracle_evidence(
            scenario,
            {},
            {"graph/virtue.md": "# Virtue\nMarcus Machiavelli Nietzsche virtue"},
            marker,
        )
        self.assertNotIn("response_for_comparison", oracle)
        self.assertNotIn(marker, json.dumps(oracle))

    def test_independent_oracle_reads_fixture_without_iwe_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            graph = root / "graph"
            graph.mkdir()
            (graph / "virtue-note.md").write_text(
                "---\ntitle: Virtue Note\n---\n\nVirtue requires patience.\n",
                encoding="utf-8",
            )
            scenario = next(
                item for item in self.runner.load_scenarios()
                if item.id == "refuse-an-unbounded-destructive-request"
            )
            evidence = self.runner.independent_oracle_evidence(
                scenario, {}, self.runner.snapshot(root), ""
            )
        serialized = json.dumps(evidence)
        self.assertIn("virtue-note", serialized)
        self.assertIn("Virtue Note", serialized)
        self.assertNotIn("iwe_telemetry", evidence)
        self.assertNotIn("graph_neighborhoods", evidence)

    def test_judge_is_forbidden_from_using_iwe_as_correctness_oracle(self) -> None:
        prompt = self.runner.judge_prompt(
            self.runner.materialize_skill_source(
                ROOT, str(ROOT.parent / "iwe-skills/skills/iwe-v18")
            ).skill,
            self.scenario,
            {"metrics": {}, "iwe_telemetry": [], "commands": [], "final": "[]"},
            {},
            {},
            [],
        )
        self.assertIn("Do not invoke IWE", prompt)

    def test_judge_prompt_declares_included_guidance_accounting(self) -> None:
        prompt = self.runner.judge_prompt(
            self.runner.materialize_skill_source(
                ROOT, str(ROOT.parent / "iwe-skills/skills/iwe-v18")
            ).skill,
            self.scenario,
            {"metrics": {}, "iwe_telemetry": [], "commands": [], "final": "[]"},
            {},
            {},
            [],
            include_guidance_activation=True,
        )
        self.assertIn("includes the skill activation read and its returned bytes", prompt)
        self.assertIn("Reference reads are included", prompt)
        self.assertIn("not independent proof", prompt)
        self.assertIn("Independent oracle evidence", prompt)
        self.assertIn("Ideal semantic procedure", prompt)
        self.assertIn(self.scenario.procedure["ideal"][0], prompt)
        self.assertIn("Equivalent bounded strategies", prompt)
        self.assertIn("Efficiency range diagnostics", prompt)
        self.assertIn("Metric-specific efficiency scales", prompt)
        self.assertIn(self.config.efficiency_score_scale["tool_efficiency"][4], prompt)
        self.assertIn(self.config.efficiency_score_scale["resource_efficiency"][3], prompt)
        self.assertNotIn("score ceiling", prompt.lower())
        with tempfile.TemporaryDirectory() as directory:
            env = self.runner.judge_environment(Path(directory), Path(directory), Path(directory))
            self.assertFalse(
                any((Path(entry) / "iwe").exists() for entry in env["PATH"].split(os.pathsep))
            )

    def test_no_skill_judge_uses_same_oracle_and_rubric_without_skill_redaction(self) -> None:
        run = {
            "metrics": {},
            "iwe_telemetry": [{"argv": ["find", "virtue"]}],
            "commands": [{"command": "iwe find virtue", "output": "result"}],
            "final": "answer",
        }
        prompt = self.runner.judge_prompt(None, self.scenario, run, {}, {}, [])
        self.assertIn("no skill guidance was installed", prompt)
        self.assertIn("skill_compliance is not applicable", prompt)
        self.assertIn("must not affect any other dimension", prompt)
        self.assertIn("Independent oracle evidence", prompt)
        self.assertIn("Ideal semantic procedure", prompt)
        self.assertIn("iwe find virtue", prompt)
        self.assertEqual(
            self.runner.sanitize_judge_evidence(None, {"value": "unchanged"}),
            {"value": "unchanged"},
        )









if __name__ == "__main__":
    unittest.main()
