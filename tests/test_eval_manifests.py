from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.eval_test_support import ROOT, load_eval_module, load_module, load_runner


class ExperimentManifestTests(unittest.TestCase):
    def test_loads_two_target_manifest_with_target_local_runtimes(self) -> None:
        experiment_module = load_eval_module("experiment")
        experiment = experiment_module.load_experiment(
            ROOT / "tests/eval/experiments/example.toml", ROOT
        )
        self.assertEqual(len(experiment.targets), 2)
        self.assertEqual(experiment.samples, 2)
        self.assertEqual(experiment.targets[0].runtime.version, "0.18.0")
        self.assertEqual(experiment.targets[1].runtime.version, "0.18.1")
        self.assertEqual(experiment.targets[0].skill_path, experiment.targets[1].skill_path)
        self.assertTrue(all(target.has_skill for target in experiment.targets))
        self.assertNotEqual(experiment.targets[0].id, experiment.targets[1].id)

    def test_loads_runtime_only_target_without_a_skill_payload(self) -> None:
        experiment_module = load_eval_module("experiment")
        source = (ROOT / "tests/eval/experiments/example.toml").read_text(encoding="utf-8")
        source += """

[[targets]]
id = "iwe-no-skill"
skill_mode = "none"
contract_file = "../iwe-skills/contracts/iwe-v18.json"
[targets.runtime]
cli = "iwe"
source = "directory"
directory = ".runtimes/iwe-0.18.0/bin"
version = "0.18.0"
"""
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "experiment.toml"
            path.write_text(source, encoding="utf-8")
            experiment = experiment_module.load_experiment(path, ROOT)
        target = experiment.targets[-1]
        self.assertEqual(target.id, "iwe-no-skill")
        self.assertFalse(target.has_skill)
        self.assertIsNone(target.skill_path)
        self.assertIsNone(target.skill_version)

    def test_aggregate_exclusions_reject_unknown_target(self) -> None:
        experiment_module = load_eval_module("experiment")
        source = (ROOT / "tests/eval/experiments/example.toml").read_text(encoding="utf-8")
        source = source.replace(
            "[[targets]]",
            'aggregate_metric_exclusions_by_target = { missing = ["tool_efficiency"] }\n\n[[targets]]',
            1,
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "experiment.toml"
            path.write_text(source, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unknown targets.*missing"):
                experiment_module.load_experiment(path, ROOT)

    def test_matrix_is_complete_paired_and_deterministic(self) -> None:
        runner = load_runner()
        experiment = load_eval_module("experiment").load_experiment(
            ROOT / "tests/eval/experiments/example.toml", ROOT
        )
        scenarios = [s for s in runner.load_scenarios() if s.id in experiment.scenario_ids]
        cells = runner.build_matrix(experiment, scenarios)
        self.assertEqual(len(cells), 8)
        self.assertEqual(len({(c.target_id, c.scenario_id, c.sample_index) for c in cells}), 8)
        self.assertEqual(len({c.pair_id for c in cells}), 4)
        for pair_id in {c.pair_id for c in cells}:
            self.assertEqual(sum(c.pair_id == pair_id for c in cells), 2)

    def test_pairwise_comparison_uses_matching_model_profiles(self) -> None:
        compare = load_eval_module("compare")
        rows = []
        for target, accepted_failures in (
            ("a", {}),
            ("b", {"tool_efficiency": {"deterministic": "hard gate"}}),
        ):
            rows.append({
                "target_id": target,
                "scenario_id": "s",
                "sample": 1,
                "pair_id": "pair-1",
                "verdict": {
                    "valid": True,
                    "metric_scores": {"tool_efficiency": 4},
                    "metric_failures": {"tool_efficiency": {"score": 4, "required": 5}},
                },
                "evaluation_profile": {
                    "name": "weak",
                    "minimum_score": {"tool_efficiency": 4},
                    "metric_failures": accepted_failures,
                },
                "agent": {"metrics": {}},
            })
        metric = compare.compare_results(
            rows,
            ("a", "b"),
            ("tool_efficiency",),
        )[0]["metrics"]["tool_efficiency"]
        self.assertEqual((metric["left_wins"], metric["ties"], metric["left_losses"]), (1, 0, 0))

        rows[1]["evaluation_profile"]["name"] = "medium"
        with self.assertRaisesRegex(ValueError, "mismatched model profiles"):
            compare.compare_results(rows, ("a", "b"), ("tool_efficiency",))

    def test_pairwise_comparison_is_threshold_based_and_keeps_invalid_cells(self) -> None:
        compare = load_eval_module("compare")
        def result(target, sample, score, valid=True):
            scores = {name: 5 for name in load_runner().DIMENSIONS}
            scores["tool_efficiency"] = score
            return {"target_id": target, "scenario_id": "s", "sample": sample,
                    "pair_id": f"pair-{sample}",
                    "verdict": {"valid": valid, "metric_scores": scores,
                                "metric_failures": {} if score >= 4 else {"tool_efficiency": {}},
                                "validation_errors": [] if valid else ["bad"]},
                    "agent": {"metrics": {"tool_calls": sample}}}
        comparison = compare.compare_results([
            result("a", 1, 5), result("b", 1, 3),
            result("a", 2, 3, False), result("b", 2, 5),
        ], ("a", "b"), ("tool_efficiency",))[0]
        metric = comparison["metrics"]["tool_efficiency"]
        self.assertEqual((metric["left_wins"], metric["ties"], metric["left_losses"]), (1, 0, 1))
        self.assertEqual(comparison["invalid_cells"], {"a": 1, "b": 0})
        self.assertNotIn("mean", json.dumps(comparison).lower())
        self.assertNotIn("weighted", json.dumps(comparison).lower())

    def test_pairwise_comparison_preserves_worker_time_deltas(self) -> None:
        compare = load_eval_module("compare")

        def result(target: str, seconds: float, *, valid: bool = True) -> dict:
            return {
                "target_id": target,
                "scenario_id": "s",
                "sample": 1,
                "pair_id": "pair-1",
                "verdict": {"valid": valid, "metric_scores": {}, "metric_failures": {}},
                "agent": {
                    "wall_seconds": seconds,
                    "metrics": {"task_tool_calls": 2, "task_tool_output_bytes": 100},
                },
            }

        comparison = compare.compare_results(
            [result("guided", 3.25), result("control", 5.75)],
            ("guided", "control"),
            ("tool_efficiency", "resource_efficiency"),

            {("s", 1): "pair-1"},
        )[0]
        self.assertEqual(comparison["efficiency"]["worker_wall_seconds_deltas"], [-2.5])
        self.assertEqual(
            comparison["efficiency"]["paired_deltas"]["task_tool_output_bytes"],
            [0],
        )
        renderer = load_eval_module("report_markdown")
        markdown = "\n".join(renderer._comparison_tables([comparison]))
        self.assertIn("## Paired efficiency comparison", markdown)
        self.assertIn("guided − control", markdown)
        self.assertIn("Tool-call efficiency | 0 / 1 / 0", markdown)
        self.assertIn("All scenarios | 1 | 1/1 | 2.500 s | 2.500 s", markdown)
        self.assertIn("Worker wall time (seconds) | `-2.500`", markdown)
        self.assertIn("Task tool-output bytes | `0`", markdown)

    def test_performance_summary_uses_all_sample_medians_per_arm(self) -> None:
        rows = []
        for target, values in {
            "guided": [(100, 10, 1, 2.0), (300, 30, 3, 4.0), (200, 20, 2, 3.0)],
            "control": [(900, 90, 9, 8.0), (700, 70, 7, 6.0), (800, 80, 8, 7.0)],
        }.items():
            for sample, (input_tokens, output_tokens, calls, wall) in enumerate(values, 1):
                rows.append({
                    "target_id": target,
                    "sample": sample,
                    "agent": {
                        "token_usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
                        "metrics": {"task_tool_calls": calls},
                        "wall_seconds": wall,
                    },
                })
        summary = load_runner().performance_summary(rows, ("guided", "control"))
        self.assertEqual(summary["guided"], {
            "samples": 3,
            "input_tokens_median": 200,
            "input_tokens_mean": 200,
            "output_tokens_median": 20,
            "output_tokens_mean": 20,
            "tool_calls_median": 2,
            "tool_calls_mean": 2,
            "wall_seconds_median": 3.0,
            "wall_seconds_mean": 3.0,
        })
        renderer = load_eval_module("report_markdown")
        markdown = "\n".join(renderer._performance_table(summary))
        self.assertIn("| Input tokens | Median | 200 | 800 | +300.0% |", markdown)
        self.assertIn("| Output tokens | Median | 20 | 80 | +300.0% |", markdown)
        self.assertIn("| Tool calls | Median | 2 | 8 | +300.0% |", markdown)
        self.assertIn("| Wall time (seconds) | Median | 3.000 | 7.000 | +133.3% |", markdown)
        self.assertIn("| Wall time (seconds) | Mean | 3.000 | 7.000 | +133.3% |", markdown)

        single_arm_markdown = "\n".join(
            renderer._performance_table({"guided": summary["guided"]})
        )
        self.assertIn("| Metric | Statistic | guided |", single_arm_markdown)
        self.assertIn("| Input tokens | Median | 200 |", single_arm_markdown)

        three_arm = {"cli": summary["guided"], "skill": summary["control"], "policy": summary["guided"]}
        three_arm_markdown = "\n".join(renderer._performance_table(three_arm))
        self.assertIn("| Metric | Statistic | cli | skill | policy |", three_arm_markdown)
        self.assertIn("| Input tokens | Median | 200 | 800 | 200 |", three_arm_markdown)
        self.assertIn("| Samples included | Count | 3 | 3 | 3 |", three_arm_markdown)
        self.assertIn("| Samples included | Count | 3 |", single_arm_markdown)
        self.assertNotIn("Change is", single_arm_markdown)

    def test_quality_comparison_reports_all_quality_metrics_as_percentage_points(self) -> None:
        runner = load_runner()
        renderer = load_eval_module("report_markdown")
        outcomes = []
        for target, successes in (("iwe-v18", 9), ("iwe-no-skill", 7)):
            metrics = {}
            for name in runner.DIMENSIONS:
                metrics[name] = {
                    "applicable": not (target == "iwe-no-skill" and name == "skill_compliance"),
                    "successful_samples": successes,
                    "total_samples": 10,
                }
            outcomes.append({"target_id": target, "metrics": metrics})
        markdown = "\n".join(renderer._quality_comparison_table(
            outcomes, ("iwe-v18", "iwe-no-skill")
        ))
        self.assertIn("## Quality and efficiency acceptance", markdown)
        self.assertIn("| Task correctness | 9/10 (90.0%) | 7/10 (70.0%) | -20.0 pp |", markdown)
        self.assertIn("| Skill compliance | 9/10 (90.0%) | N/A | N/A |", markdown)
        for label in renderer.METRIC_LABELS.values():
            self.assertIn(f"| {label} |", markdown)

    def test_pairwise_comparison_marks_excluded_target_metric_not_applicable(self) -> None:
        compare = load_eval_module("compare")
        rows = [{
            "target_id": target,
            "scenario_id": "s",
            "sample": 1,
            "pair_id": "pair-1",
            "verdict": {
                "valid": True,
                "metric_scores": {"skill_compliance": 5 if target == "skill" else 0},
                "metric_failures": {} if target == "skill" else {"skill_compliance": {}},
            },
            "agent": {"metrics": {}},
        } for target in ("skill", "no-skill")]
        result = compare.compare_results(
            rows,
            ("skill", "no-skill"),
            ("skill_compliance",),
            {("s", 1): "pair-1"},
            excluded_dimensions_by_target={"no-skill": {"skill_compliance"}},
        )[0]
        self.assertEqual(result["metrics"]["skill_compliance"], {"applicable": False})

    def test_experiment_list_mode_shows_pairs_without_resolving_binaries(self) -> None:
        completed = subprocess.run([
            sys.executable, str(ROOT / "tests/eval/run.py"),
            "--experiment", "tests/eval/experiments/example.toml", "--list",
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("v18-on-0180", completed.stdout)
        self.assertIn("IWE 0.18.1", completed.stdout)
        self.assertIn("query-structured-metadata-without-scanning-files", completed.stdout)

    def test_target_aggregation_is_independent_complete_and_histogrammed(self) -> None:
        runner = load_runner()
        scores = {name: 5 for name in runner.DIMENSIONS}
        rows = []
        for target in ("a", "b"):
            for sample in (1, 2):
                target_scores = dict(scores)
                if target == "b":
                    target_scores["task_correctness"] = 0
                rows.append({"target_id": target, "scenario": "S", "scenario_id": "s",
                             "sample": sample, "verdict": {"valid": True,
                             "metric_scores": target_scores,
                             "metric_failures": {} if target == "a" else {"task_correctness": {}},
                             "validation_errors": []}})
        outcomes = runner.aggregate_results(rows, runner.load_eval_config(), expected_samples=2)
        self.assertTrue(next(o for o in outcomes if o["target_id"] == "a")["pass"])
        failed = next(o for o in outcomes if o["target_id"] == "b")
        self.assertFalse(failed["pass"])
        self.assertEqual(failed["metrics"]["task_correctness"]["score_histogram"]["0"], 2)

    def test_experiment_rejects_skill_name_mismatch_in_strict_frontmatter(self) -> None:
        experiment_module = load_eval_module("experiment")
        source = (ROOT / "tests/eval/experiments/example.toml").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            (root / "skill").mkdir()
            (root / "skill/SKILL.md").write_text(
                "---\nname: wrong-name\nmetadata:\n  version: 0.2.0\n---\nbody\n",
                encoding="utf-8",
            )
            (root / "contract.json").write_text(
                json.dumps({"schema_version": 1, "cli_line": "0.18", "commands": {"find": {}}}),
                encoding="utf-8",
            )
            manifest = source.replace("../iwe-skills/skills/iwe-v18", str((root / "skill").relative_to(ROOT))).replace(
                "../iwe-skills/contracts/iwe-v18.json", str((root / "contract.json").relative_to(ROOT))
            )
            path = root / "experiment.toml"
            path.write_text(manifest, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "skill name"):
                experiment_module.load_experiment(path, ROOT)

    def test_comparison_rejects_conflicting_pair_ids_and_missing_expected_cells(self) -> None:
        compare = load_eval_module("compare")
        rows = [
            {"target_id": target, "scenario_id": "s", "sample": 1, "pair_id": pair_id,
             "verdict": {"valid": True, "metric_scores": {"safety": 5}, "metric_failures": {}},
             "agent": {"metrics": {}}}
            for target, pair_id in (("a", "pair-a"), ("b", "pair-b"))
        ]
        with self.assertRaisesRegex(ValueError, "pair_id"):
            compare.compare_results(rows, ("a", "b"), ("safety",), {("s", 1): "expected"})
        with self.assertRaisesRegex(ValueError, "missing expected"):
            compare.compare_results([], ("a", "b"), ("safety",), {("s", 1): "expected"})

    def test_single_skill_list_accepts_weak_model_profile_without_running_agents(self) -> None:
        completed = subprocess.run([
            sys.executable,
            str(ROOT / "tests/eval/run.py"),
            "--list",
            "--model-profile",
            "weak",
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("query-structured-metadata-without-scanning-files", completed.stdout)

    def test_single_skill_list_output_exposes_id_and_display_name(self) -> None:
        completed = subprocess.run([
            sys.executable, str(ROOT / "tests/eval/run.py"), "--list",
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        first = completed.stdout.splitlines()[0]
        self.assertRegex(
            first,
            r"^discover-and-retrieve-bounded-multi-hop-context: .+ \[[^]]+\]$",
        )

    def test_cli_scenario_selector_accepts_only_exact_ids(self) -> None:
        command = [sys.executable, str(ROOT / "tests/eval/run.py"), "--list"]
        selected = subprocess.run(
            command + ["--scenario", "query-structured-metadata-without-scanning-files"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertEqual(len(selected.stdout.splitlines()), 1)
        self.assertTrue(selected.stdout.startswith("query-structured-metadata-without-scanning-files:"))
        for invalid in ("Query structured metadata without scanning files", "metadata"):
            rejected = subprocess.run(
                command + ["--scenario", invalid],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("unknown scenario id", rejected.stderr)


class AcceptanceReplayCommandTests(unittest.TestCase):
    def test_replay_command_requires_explicit_source_output_and_profile(self) -> None:
        module = load_module(
            ROOT / "scripts/replay_eval_acceptance.py",
            "replay_eval_acceptance",
        )
        args = module.parse_args([
            "tests/eval/reports/source",
            "--output",
            "tests/eval/.cache/derived.json",
            "--model-profile",
            "weak",
        ])
        self.assertEqual(args.model_profile, "weak")
        self.assertEqual(args.report, Path("tests/eval/reports/source"))
        self.assertEqual(args.output, Path("tests/eval/.cache/derived.json"))


if __name__ == "__main__":
    unittest.main()
