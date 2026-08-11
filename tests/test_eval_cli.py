from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from tests.eval_test_support import ROOT, load_eval_module, load_module, load_runner


class PairedSkillEvalCommandTests(unittest.TestCase):

    def test_agents_file_is_target_local_and_records_exact_payload(self) -> None:
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            treatment = root / "route.AGENTS.md"
            treatment.write_text("# Routes\nUse one bounded IWE call.\n", encoding="utf-8")
            workspace = root / "workspace"
            workspace.mkdir()
            installed = runner.install_agents_file(workspace, treatment)
            self.assertEqual(installed, workspace / "AGENTS.md")
            self.assertEqual(installed.read_bytes(), treatment.read_bytes())
            provenance = runner.agents_file_provenance(treatment)
            self.assertEqual(provenance["bytes"], len(treatment.read_bytes()))
            self.assertRegex(provenance["sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(runner.preinjected_guidance_bytes(treatment), provenance["bytes"])
            control = root / "control"
            control.mkdir()
            self.assertIsNone(runner.install_agents_file(control, None))
            self.assertEqual(runner.preinjected_guidance_bytes(None), 0)
            self.assertFalse((control / "AGENTS.md").exists())
            judge_temporary = root / "judge"
            judge_temporary.mkdir()
            judge = runner.create_judge_workspace(judge_temporary)
            self.assertFalse((judge / "AGENTS.md").exists())
            with self.assertRaisesRegex(RuntimeError, "already contains AGENTS.md"):
                runner.install_agents_file(workspace, treatment)

    def test_agents_file_installation_occurs_before_worker_timer(self) -> None:
        source = (ROOT / "tests/eval/eval_core/execution.py").read_text(encoding="utf-8")
        calls = {
            node.func.id: node.lineno
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in {"install_agents_file", "run_process"}
        }
        self.assertLess(calls["install_agents_file"], calls["run_process"])

    def test_installed_agents_file_is_hidden_from_oracle_and_judge_snapshots(self) -> None:
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "AGENTS.md").write_text("treatment-only policy", encoding="utf-8")
            (workspace / "note.md").write_text("evidence", encoding="utf-8")
            self.assertEqual(runner.snapshot(workspace), {"note.md": "evidence"})

    def test_targets_with_and_without_agents_keep_identical_filesystem_tools(self) -> None:
        runner = load_runner()
        scenario = next(
            item for item in runner.load_scenarios()
            if item.id == "ambiguous-discovery-with-one-follow-up"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for arm in ("treatment", "control"):
                bin_dir = root / arm
                runner.install_command_shims(
                    bin_dir, scenario, Path("/bin/false"),
                    allow_filesystem_tools=True,
                )
                for name in ("grep", "rg", "find"):
                    self.assertFalse((bin_dir / name).exists())

    def test_control_filesystem_route_is_not_a_procedure_error(self) -> None:
        runner = load_runner()
        scenario = next(
            item for item in runner.load_scenarios()
            if item.id == "ambiguous-discovery-with-one-follow-up"
        )
        metrics = {
            "unbounded_read_calls": 0,
            "iwe_telemetry_missing": 0,
            "iwe_telemetry_extra": 0,
            "iwe_telemetry_mismatch": 0,
            "iwe_telemetry_invalid": 0,
            "iwe_output_truncated": 0,
            "web_calls": 0,
            "docs_calls": 0,
            "iwe_calls": 0,
            "forbidden_fallback_calls": 2,
            "broad_workspace_reads": 0,
            "skill_read_calls": 0,
        }
        self.assertIn("forbidden fallback tool used", runner.procedure_errors(scenario, [], metrics))
        self.assertNotIn(
            "forbidden fallback tool used",
            runner.procedure_errors(
                scenario, [], metrics, allow_filesystem_fallback=True,
            ),
        )

    def test_guidance_efficiency_ab_profile_is_two_arm_three_scenario_ten_sample(self) -> None:
        module = load_module(
            ROOT / "scripts/run_skill_guidance_efficiency_ab.py",
            "run_skill_guidance_efficiency_ab",
        )
        concurrency = load_module(
            ROOT / "scripts/eval_concurrency.py", "guidance_eval_concurrency"
        )
        self.assertEqual(module.DEFAULT_JOBS, concurrency.DEFAULT_JOBS)
        self.assertEqual(module.SAMPLES, 10)
        self.assertEqual(module.SCENARIOS, (
            "discover-and-retrieve-bounded-multi-hop-context",
            "query-structured-metadata-without-scanning-files",
            "ambiguous-discovery-with-one-follow-up",
        ))
        self.assertEqual(module.COMPARISON_METRICS, (
            "tool_efficiency", "resource_efficiency",
        ))
        with mock.patch.object(module, "verify_runtime_binary", return_value=Path("/bin/true")):
            manifest_path = module.write_experiment(
                root=ROOT,
                jobs=module.DEFAULT_JOBS,
                agent="codex",
                source_root=ROOT,
            )
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["samples"], 10)
        self.assertEqual(manifest["jobs"], module.DEFAULT_JOBS)
        self.assertEqual(manifest["name"], "skill-guidance-efficiency-ab")
        self.assertEqual(tuple(manifest["scenarios"]), module.SCENARIOS)
        self.assertEqual(tuple(manifest["comparison_metrics"]), module.COMPARISON_METRICS)
        self.assertEqual(manifest["guidance_accounting"], "include_activation")
        self.assertEqual(manifest["worker_scheduling"], "balanced_waves")
        self.assertEqual([target["id"] for target in manifest["targets"]], [
            "iwe-v18", "iwe-no-skill",
        ])
        self.assertEqual(
            {target["agents_file"] for target in manifest["targets"]},
            {"tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl"},
        )
        self.assertNotIn("skill_mode", manifest["targets"][0])
        self.assertEqual(manifest["targets"][1]["skill_mode"], "none")
        self.assertNotIn("skill_path", manifest["targets"][1])
        self.assertNotIn("skill_version", manifest["targets"][1])
        self.assertEqual(
            manifest["targets"][0]["runtime"], manifest["targets"][1]["runtime"]
        )
        experiment = load_eval_module("experiment").load_experiment(manifest_path, ROOT)
        self.assertEqual(experiment.guidance_accounting, "include_activation")
        self.assertEqual(experiment.worker_scheduling, "balanced_waves")
        scenarios = [
            scenario for scenario in load_runner().load_scenarios()
            if scenario.id in experiment.scenario_ids
        ]
        cells = load_runner().build_matrix(experiment, scenarios)
        self.assertEqual(len(cells), 60)
        self.assertEqual(len({cell.pair_id for cell in cells}), 30)
        waves = load_runner().balanced_waves(cells, experiment.jobs)
        self.assertEqual(sum(map(len, waves)), len(cells))
        self.assertTrue(all(0 < len(wave) <= experiment.jobs for wave in waves))
        for wave in waves:
            pairs_per_wave = len(wave) // 2
            self.assertEqual(
                [cell.target_id for cell in wave].count("iwe-v18"), pairs_per_wave
            )
            self.assertEqual(
                [cell.target_id for cell in wave].count("iwe-no-skill"), pairs_per_wave
            )
            for pair_index in range(pairs_per_wave):
                pair = wave[pair_index * 2 : pair_index * 2 + 2]
                self.assertEqual(pair[0].pair_id, pair[1].pair_id)
                expected = ["iwe-v18", "iwe-no-skill"] if pair[0].sample_index % 2 else ["iwe-no-skill", "iwe-v18"]
                self.assertEqual([cell.target_id for cell in pair], expected)
        command = module.build_command(manifest_path, Path("result.md"), "codex", list_only=True)
        self.assertIn("--list", command)

    def test_default_skill_eval_uses_the_explicit_correctness_efficiency_suite(self) -> None:
        module = load_module(ROOT / "scripts/run_default_skill_eval.py", "run_iwe_all_scenarios")
        expected = module.DEFAULT_SKILL_SCENARIOS
        self.assertEqual(len(expected), 31)
        self.assertEqual(module.load_scenario_ids(ROOT), expected)
        cache_parent = ROOT / "tests/eval/.cache"
        cache_parent.mkdir(parents=True, exist_ok=True)
        temporary_cache = tempfile.TemporaryDirectory(dir=cache_parent)
        self.addCleanup(temporary_cache.cleanup)
        with mock.patch.object(
            module, "CACHE", Path(temporary_cache.name).relative_to(ROOT)
        ):
            manifest_path = module.write_experiment(1, ROOT, source_root=ROOT)
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = tomllib.loads(manifest_text)
        self.assertIn('# source_repository = "https://github.com/iwe-org/skills"', manifest_text)
        self.assertIn('# default_skill = "iwe-v18"', manifest_text)
        self.assertEqual(tuple(manifest["scenarios"]), expected)
        self.assertEqual(manifest["name"], "iwe-default-skill-correctness-efficiency")
        self.assertEqual(manifest["jobs"], module.DEFAULT_JOBS)
        self.assertEqual(
            manifest["targets"][0]["agents_file"],
            "tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl",
        )
        experiment = load_eval_module("experiment").load_experiment(manifest_path, ROOT)
        self.assertEqual(experiment.guidance_accounting, "include_activation")
        self.assertEqual(experiment.worker_scheduling, "streaming")
        self.assertEqual(len(manifest["targets"]), 1)
        self.assertEqual(manifest["targets"][0]["id"], "iwe-v18")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tests/eval/run.py"),
             "--experiment", str(manifest_path.relative_to(ROOT)), "--list"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("target iwe-v18: ../iwe-skills/skills/iwe-v18 @ IWE 0.18.0 (directory)", completed.stdout)
        self.assertNotIn("iwe-memory-system", completed.stdout)
        self.assertNotIn("iwe-no-skill", completed.stdout)


    def test_default_skill_eval_uses_configured_iwe_v18(self) -> None:
        module = load_module(ROOT / "scripts/run_default_skill_eval.py", "run_iwe_skill_ab_eval")
        targets = module.load_targets(ROOT)
        self.assertEqual(targets[0].skill_id, "iwe-v18")
        self.assertEqual(targets[0].skill_version, "0.9.9")
        self.assertEqual(targets[0].iwe_version, "0.18.0")
        self.assertEqual(targets[0].runtime_skill_id, "iwe-v18")
        self.assertEqual(len(targets), 1)

    def test_default_skill_eval_follows_default_skill_from_config(self) -> None:
        module = load_module(ROOT / "scripts/run_default_skill_eval.py", "run_default_skill_dynamic")
        configured = mock.Mock()
        configured.name = "future-default"
        configured.path = Path("skills/future-default")
        configured.skill_version = "2.0.0"
        configured.tested_version = "0.19.0"
        configured.contract_file = Path("contracts/future-default.json")
        with mock.patch.object(
            module,
            "load_skills",
            return_value=("future-default", {"future-default": configured}),
        ):
            targets = module.load_targets(ROOT)
        self.assertEqual(targets[0].skill_id, "future-default")
        self.assertEqual(targets[0].runtime_skill_id, "future-default")

    def test_default_skill_eval_materializes_latest_upstream_head(self) -> None:
        module = load_module(
            ROOT / "scripts/run_default_skill_eval.py",
            "run_default_skill_upstream",
        )
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            upstream = base / "upstream"
            subprocess.run(
                ["git", "init", "-q", "-b", "main", str(upstream)], check=True
            )
            subprocess.run(
                ["git", "-C", str(upstream), "config", "user.email", "eval@example.test"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(upstream), "config", "user.name", "Eval Test"],
                check=True,
            )
            (upstream / "marker.txt").write_text("latest\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(upstream), "add", "marker.txt"], check=True
            )
            subprocess.run(
                ["git", "-C", str(upstream), "commit", "-q", "-m", "latest"],
                check=True,
            )
            expected = subprocess.check_output(
                ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True
            ).strip()
            checkout = module.materialize_upstream_checkout(base / "cache", str(upstream))
            self.assertEqual(checkout.revision, expected)
            self.assertEqual((checkout.root / "marker.txt").read_text(), "latest\n")

    def test_default_skill_eval_generates_the_linked_markdown_results(self) -> None:
        module = load_module(ROOT / "scripts/run_default_skill_eval.py", "run_default_skill_eval_report")
        args = module.parse_args([])
        self.assertEqual(args.agent, "codex")

        self.assertEqual(args.repository, "https://github.com/iwe-org/skills")
        self.assertEqual(module.parse_args(["--agent", "claude"]).agent, "claude")
        cache_parent = ROOT / "tests/eval/.cache"
        cache_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache_parent) as directory:
            cache_path = Path(directory).relative_to(ROOT)
            with (
                mock.patch.object(module, "CACHE", cache_path),
                mock.patch.object(module, "verify_runtime_binary", return_value=Path("/bin/true")),
            ):
                manifest = module.write_experiment(
                    1, root=ROOT, jobs=1, agent="claude", source_root=ROOT
                )
            self.assertIn(
                'agent_judge_config = "claude"',
                manifest.read_text(encoding="utf-8"),
            )
        command = module.build_command(Path("manifest.toml"), args.results_file, args.agent)
        self.assertEqual(
            args.results_file,
            Path("tests/eval/results/iwe-default-skill-eval.md"),
        )
        self.assertEqual(
            command[command.index("--markdown-report") + 1],
            str(args.results_file),
        )
        self.assertEqual(command[command.index("--agent") + 1], "codex")
        self.assertEqual(command[command.index("--model-profile") + 1], "weak")
        claude_command = module.build_command(
            Path("manifest.toml"), args.results_file, "claude"
        )
        self.assertEqual(
            claude_command[claude_command.index("--model-profile") + 1],
            "medium",
        )

        renderer = load_eval_module("report_markdown")
        self.assertEqual(
            renderer._skill_metadata_line({"skill_mode": "none", "skill_version": None}),
            "- Skill guidance: `none` (control)",
        )
        self.assertEqual(
            renderer._skill_metadata_line({
                "skill_mode": "none",
                "skill_version": None,
                "agents_file": "tests/eval/guidance/iwe-routes.AGENTS.md",
                "agents_file_provenance": {"bytes": 859, "sha256": "a" * 64},
            }),
            "- Pre-injected `AGENTS.md`: `859` bytes, SHA-256 `" + "a" * 64 + "`",
        )
        self.assertEqual(renderer._cell({"applicable": False}), "—")
        no_skill_raw = {
            "scenario": "S",
            "sample": 1,
            "verdict": {
                "valid": True,
                "validation_errors": [],
                "procedure_errors": [],
                "metric_failures": {"skill_compliance": {"score": 0, "required": 4}},
            },
        }
        problem_lines = renderer._problem_lines(
            [(Path("raw.json"), no_skill_raw)], None, {"skill_compliance"}
        )
        self.assertIn("No sample-level problems detected.", problem_lines)
        self.assertNotIn("Skill compliance", "\n".join(problem_lines))
        runner = load_runner()
        command_config = json.loads(
            (ROOT / "tests/eval/configs/codex.json").read_text(encoding="utf-8")
        )
        with mock.patch.object(runner.shutil, "which", return_value="/usr/bin/codex"), \
             mock.patch.object(runner.subprocess, "run") as version_run:
            version_run.return_value.stdout = "codex-cli 0.test\n"
            metadata = runner.agent_metadata(command_config["agent_command"])
            shared_agent = runner.validate_shared_agent(command_config, "codex")
        self.assertEqual(metadata, {
            "name": "Codex CLI",
            "version": "0.test",
            "model": "gpt-5.6-luna",
            "reasoning": "medium",
        })
        self.assertEqual(shared_agent["agent"]["model"], "gpt-5.6-luna")
        self.assertEqual(shared_agent["judge"]["model"], "gpt-5.6-sol")
        with self.assertRaisesRegex(ValueError, "same configured agent"):
            runner.validate_shared_agent({
                **command_config,
                "judge_command": command_config["judge_command"].replace(
                    "codex exec", "claude exec"
                ),
            }, "codex")

        claude_stream = "\n".join((
            json.dumps({"type": "assistant", "message": {"content": [{
                "type": "tool_use", "id": "tool-1", "name": "Bash",
                "input": {"command": "iwe count --filter '{ type: project }'"},
            }]}}),
            json.dumps({"type": "user", "message": {"content": [{
                "type": "tool_result", "tool_use_id": "tool-1",
                "content": "3\n", "is_error": False,
            }]}}),
            json.dumps({"type": "result", "subtype": "success", "result": "There are 3."}),
        ))
        parsed = runner.parse_process_output("claude", claude_stream)
        self.assertEqual(parsed["final"], "There are 3.")
        self.assertEqual(parsed["commands"], [{
            "command": "iwe count --filter '{ type: project }'",
            "exit_code": 0,
            "output": "3\n",
        }])
        structured = runner.parse_process_output("claude", json.dumps({
            "type": "result", "subtype": "success",
            "structured_output": {"rationale": "bounded", "dimensions": {}},
        }))
        self.assertEqual(
            json.loads(structured["final"]),
            {"rationale": "bounded", "dimensions": {}},
        )
        with mock.patch.object(runner.shutil, "which", return_value="/usr/bin/claude"), \
             mock.patch.object(runner.subprocess, "run") as version_run:
            version_run.return_value.stdout = "2.1.200 (Claude Code)\n"
            metadata = runner.agent_metadata(
                "claude --bare -p --model sonnet --effort low"
            )
        self.assertEqual(metadata, {
            "name": "Claude Code", "version": "2.1.200 (Claude Code)",
            "model": "sonnet", "reasoning": "low",
        })
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-only"}, clear=False):
            claude_env = runner.eval_environment(
                Path("/tmp/home"), Path("/tmp/codex"), Path("/tmp/shims"),
                Path("/tmp/iwe"), Path("/tmp/eval"), "claude",
            )
            codex_env = runner.eval_environment(
                Path("/tmp/home"), Path("/tmp/codex"), Path("/tmp/shims"),
                Path("/tmp/iwe"), Path("/tmp/eval"), "codex",
            )
        self.assertEqual(claude_env["ANTHROPIC_API_KEY"], "test-only")
        self.assertEqual(claude_env["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"], "1")
        self.assertNotIn("ANTHROPIC_API_KEY", codex_env)
        weak_profile = load_runner().load_eval_config().model_profiles["weak"]
        experiment = {
            "name": "ab",
            "scenarios": ["scenario"],
            "samples": 1,
            "estimated_agent_calls": 2,
            "estimated_judge_calls": 2,
            "agent_judge_config": "codex",
            "agent": {
                "name": "Codex CLI", "version": "0.146.0",
                "model": "gpt-5.6-terra", "reasoning": "medium",
            },
            "judge": {"model": "gpt-5.6-sol", "reasoning": "low"},
            "targets": [
                {
                    "id": "a",
                    "model_profile": "weak",
                    "minimum_score": weak_profile.minimum_score,
                    "required_success_percent": weak_profile.required_success_percent,
                    "skill_version": "1.0.0",
                    "runtime": {"version": "0.18.0"},
                },
                {
                    "id": "b",
                    "model_profile": "weak",
                    "minimum_score": weak_profile.minimum_score,
                    "required_success_percent": weak_profile.required_success_percent,
                    "skill_mode": "none",
                    "skill_version": None,
                    "runtime": {"version": "0.18.0"},
                },
            ],
        }
        metrics = {
            name: {
                "successful_samples": 0 if name == "tool_efficiency" else 1,
                "total_samples": 1,
                "required_successes": 1,
                "required_success_percent": weak_profile.required_success_percent[name],
                "pass": name != "tool_efficiency",
                "score_histogram": {"0": 1} if name == "tool_efficiency" else {"5": 1},
            }
            for name in load_runner().DIMENSIONS
        }
        outcome = {
            "target_id": "a", "scenario": "Scenario", "scenario_id": "scenario",
            "samples": 1, "invalid_samples": 0, "procedure_failure_samples": 1,
            "procedure_error_counts": {"unbounded": 1}, "metrics": metrics, "pass": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_dir = root / "reports/run"
            telemetry = report_dir / "targets/a/scenario--1.json"
            telemetry.parent.mkdir(parents=True)
            telemetry.write_text(json.dumps({
                "target_id": "a", "scenario_id": "scenario", "sample": 1,
                "verdict": {
                    "valid": True,
                    "validation_errors": [],
                    "procedure_errors": ["unbounded"],
                    "metric_failures": {"tool_efficiency": {
                        "score": 2,
                        "required": 5,
                        "deterministic": "configured unrelated IWE candidate retrieved: d8w3r",
                    }},
                    "critique": {
                        "rationale": "The answer was correct but retrieval was unbounded.",
                        "dimensions": {"tool_efficiency": {
                            "score": 2,
                            "rationale": "Avoidable calls exceeded the bounded procedure.",
                            "evidence": ["Three calls were observed; one was expected."],
                        }},
                    },
                },
            }), encoding="utf-8")
            report_path = root / "results/report.md"
            markdown = renderer.render_markdown(
                experiment,
                {"scenarios": [outcome]},
                report_dir,
                report_path=report_path,
            )
            self.assertIn("Generated by tests/eval/report_markdown.py", markdown)
            self.assertIn("Scenarios tested: `scenario`", markdown)
            self.assertIn("Paired samples per target: `1`", markdown)
            self.assertIn("Agent: Codex CLI `0.146.0`", markdown)
            self.assertIn("AI model: `gpt-5.6-terra`; reasoning: `medium`", markdown)
            self.assertIn("Judge AI model: `gpt-5.6-sol`; reasoning: `low`", markdown)
            self.assertIn(
                "[Metric and score definitions](../../../docs/evaluation-metrics.md)", markdown
            )
            self.assertIn("## Evaluation profile — `a`", markdown)
            self.assertIn("## Evaluation profile — `b`", markdown)
            self.assertEqual(markdown.count("| Metric | Minimum PASS score |"), 2)
            self.assertEqual(markdown.count("| Metric | Required success percent |"), 2)
            self.assertIn("Model profile: **`weak`**", markdown)
            self.assertIn("| Metric | Minimum PASS score |", markdown)
            self.assertIn("| Tool-call efficiency (`tool_efficiency`) | 4/5 |", markdown)
            self.assertIn("| Task correctness (`task_correctness`) | 5/5 |", markdown)
            self.assertIn("| Metric | Required success percent |", markdown)
            self.assertIn("| Token/resource efficiency (`resource_efficiency`) | 90% |", markdown)
            self.assertIn("## Aggregate metrics", markdown)
            self.assertIn(
                "| Metric | Passing samples | Minimum sample score | "
                "Required passing samples per scenario | Verdict |",
                markdown,
            )
            self.assertIn(
                "| Tool-call efficiency | 0/1 | 4/5 | 1/1 (90%) | **FAIL** |",
                markdown,
            )
            self.assertIn("0/1 **(FAIL)**", markdown)
            self.assertIn("| Procedure-clean | 0/1 | — | Informational | — |", markdown)
            self.assertIn("### Problem ledger", markdown)
            self.assertIn("Analysis: The answer was correct but retrieval was unbounded.", markdown)
            self.assertIn("**Tool-call efficiency: 2/5 (required 5/5).**", markdown)
            self.assertIn(
                "Deterministic gate: configured unrelated IWE candidate retrieved: d8w3r",
                markdown,
            )
            self.assertIn("Three calls were observed; one was expected.", markdown)
            self.assertIn(
                "[raw sample JSON](../reports/run/targets/a/scenario--1.json)", markdown
            )
            self.assertIn(
                "[Machine-readable report directory](../reports/run)", markdown
            )
            telemetry.unlink()
            with self.assertRaisesRegex(FileNotFoundError, "expected sample telemetry"):
                renderer.render_markdown(
                    experiment,
                    {"scenarios": [outcome]},
                    report_dir,
                    report_path=report_path,
                )

        definitions = (ROOT / "docs/evaluation-metrics.md").read_text(encoding="utf-8")
        for label in (
            "Overall", "Valid samples", "Procedure-clean", "Task correctness",
            "Scenario compliance", "Skill compliance", "Safety", "Evidence quality",
            "Tool efficiency", "Resource efficiency",
        ):
            self.assertIn(f"### {label}", definitions)
        for source in (
            "../config.toml",
            "../tests/eval/scenarios/iwe.eval.yaml",
            "../tests/eval/run.py",
        ):
            self.assertIn(source, definitions)
        self.assertIn(
            "`weak` requires `90%` success for task correctness, scenario compliance, "
            "skill compliance, evidence quality, and tool/resource efficiency",
            definitions,
        )

    def test_markdown_problem_ledger_honors_model_profile(self) -> None:
        renderer = load_eval_module("report_markdown")
        raw = {
            "scenario": "S",
            "sample": 1,
            "verdict": {
                "valid": True,
                "validation_errors": [],
                "procedure_errors": [],
                "metric_failures": {
                    "tool_efficiency": {"score": 4, "required": 5}
                },
            },
            "evaluation_profile": {
                "name": "weak",
                "minimum_score": {"tool_efficiency": 4},
                "required_success_percent": {"tool_efficiency": 80},
                "metric_failures": {},
            },
        }
        problem_lines = renderer._problem_lines([(Path("raw.json"), raw)], None)
        self.assertIn("No sample-level problems detected.", problem_lines)

    def test_default_skill_eval_defaults_to_ten_samples_and_allows_override(self) -> None:
        module = load_module(ROOT / "scripts/run_default_skill_eval.py", "run_default_skill_eval_args")
        self.assertEqual(module.parse_args([]).samples, 10)
        self.assertEqual(module.parse_args([]).jobs, module.DEFAULT_JOBS)
        self.assertEqual(module.parse_args(["--samples", "2"]).samples, 2)
        self.assertEqual(module.parse_args(["--jobs", "4"]).jobs, 4)
        self.assertEqual(
            module.parse_args(["--scenario", "read-one-known-note", "--scenario", "count-a-typed-cohort"]).scenarios,
            ["read-one-known-note", "count-a-typed-cohort"],
        )
        self.assertTrue(module.parse_args(["--list"]).list)
        self.assertIn(
            "--list",
            module.build_command(Path("experiment.toml"), Path("result.md"), list_only=True),
        )
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            module.parse_args(["--samples", "0"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            module.parse_args(["--jobs", "0"])

    def test_guidance_smoke_can_bound_samples_and_scenarios(self) -> None:
        module = load_module(
            ROOT / "scripts/run_skill_guidance_efficiency_ab.py",
            "run_skill_guidance_smoke_args",
        )
        args = module.parse_args([
            "--samples", "1",
            "--scenario", "ambiguous-discovery-with-one-follow-up",
        ])
        self.assertEqual(args.samples, 1)
        self.assertEqual(args.scenarios, ["ambiguous-discovery-with-one-follow-up"])
        with mock.patch.object(module, "verify_runtime_binary", return_value=Path("/bin/true")):
            manifest_path = module.write_experiment(
                root=ROOT,
                samples=1,
                source_root=ROOT,
                scenarios=("ambiguous-discovery-with-one-follow-up",),
            )
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["samples"], 1)
        self.assertEqual(manifest["scenarios"], ["ambiguous-discovery-with-one-follow-up"])

    def test_single_skill_evals_use_common_jobs_default_and_one_sample(self) -> None:
        config = json.loads(
            (ROOT / "tests/eval/configs/codex.json").read_text(encoding="utf-8")
        )
        runner = load_runner()
        concurrency = load_module(
            ROOT / "scripts/eval_concurrency.py", "single_eval_concurrency"
        )
        self.assertNotIn("jobs", config)
        self.assertEqual(runner.DEFAULT_JOBS, concurrency.DEFAULT_JOBS)
        self.assertEqual(config["samples"], 1)


if __name__ == "__main__":
    unittest.main()
