from __future__ import annotations

import importlib.util
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_IDS = (
    "route-listed-runbook-through-iwe",
    "route-unlisted-guide-through-workspace",
    "fallback-after-listed-iwe-miss",
    "fallback-when-iwe-is-unavailable",
    "create-iwe-document-in-declared-language",
)
SCENARIO_FILE = ROOT / "tests/eval/scenarios/iwe.eval.yaml"
TEMPLATE = ROOT / "tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl"
RENDERER = ROOT / "scripts/render_iwe_context_agents.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class IweContextRoutingEvalTests(unittest.TestCase):
    def test_single_catalog_and_explicit_suite_memberships(self) -> None:
        document = yaml.safe_load(SCENARIO_FILE.read_text(encoding="utf-8"))
        catalog_ids = tuple(item["id"] for item in document["scenarios"])
        self.assertEqual(len(catalog_ids), 35)
        self.assertEqual(len(set(catalog_ids)), 35)
        self.assertNotIn("find-workspace-information-after-iwe-miss", catalog_ids)
        self.assertNotIn("route-listed-decision-through-iwe", catalog_ids)
        self.assertTrue(set(SCENARIO_IDS) <= set(catalog_ids))

        default_suite = load_module(
            ROOT / "scripts/run_default_skill_eval.py",
            "run_default_skill_eval_membership",
        )
        scenario_ids = default_suite.DEFAULT_SKILL_SCENARIOS
        self.assertEqual(len(scenario_ids), 31)
        self.assertIn("fallback-when-iwe-is-unavailable", scenario_ids)
        for scenario_id in (
            "route-listed-runbook-through-iwe",
            "route-unlisted-guide-through-workspace",
            "fallback-after-listed-iwe-miss",
            "create-iwe-document-in-declared-language",
        ):
            self.assertNotIn(scenario_id, scenario_ids)

    def test_manifest_is_three_arm_five_scenario_ten_sample_experiment(self) -> None:
        module = load_module(
            ROOT / "scripts/run_iwe_context_routing_ab.py",
            "run_iwe_context_routing_ab",
        )
        self.assertEqual(module.SCENARIOS, SCENARIO_IDS)
        self.assertEqual(module.DEFAULT_SAMPLES, 10)
        concurrency = load_module(
            ROOT / "scripts/eval_concurrency.py", "context_eval_concurrency"
        )
        self.assertEqual(module.DEFAULT_JOBS, concurrency.DEFAULT_JOBS)
        source = module.materialize_skill_source(
            ROOT, str(ROOT.parent / "iwe-skills/skills/iwe-v18")
        )
        with mock.patch.object(module, "verify_runtime_binary", return_value=Path("/bin/true")):
            manifest_path = module.write_experiment(root=ROOT, source=source)
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["samples"], 10)
        self.assertEqual(manifest["jobs"], module.DEFAULT_JOBS)
        self.assertEqual(manifest["guidance_accounting"], "include_activation")
        self.assertEqual(manifest["skill_activation"], "optional")
        self.assertEqual(manifest["worker_scheduling"], "balanced_waves")
        self.assertEqual([target["id"] for target in manifest["targets"]], [
            "iwe-cli-only",
            "iwe-v18",
            "iwe-v18-agents",
        ])
        self.assertEqual(manifest["targets"][0]["skill_mode"], "none")
        self.assertNotIn("skill_path", manifest["targets"][0])
        for target in manifest["targets"][1:]:
            self.assertTrue(target["skill_path"].startswith("tests/eval/.cache/"))
            self.assertEqual(target["skill_version"], "0.9.9")
        self.assertNotIn("agents_file", manifest["targets"][1])
        self.assertEqual(
            manifest["targets"][2]["agents_file"],
            str(TEMPLATE.relative_to(ROOT)),
        )
        experiment_module = load_module(ROOT / "tests/eval/experiment.py", "experiment")
        experiment = experiment_module.load_experiment(manifest_path, ROOT)
        runner = load_module(ROOT / "tests/eval/run.py", "run_context_routing_scheduler")
        scenarios = [
            scenario for scenario in runner.load_scenarios()
            if scenario.id in experiment.scenario_ids
        ]
        cells = runner.build_matrix(experiment, scenarios)
        effective_jobs = runner.normalize_jobs(
            experiment.jobs, target_count=len(experiment.targets), balanced=True
        )
        waves = runner.worker_waves(cells, effective_jobs, len(experiment.targets))
        self.assertEqual(len(cells), 150)
        self.assertGreaterEqual(effective_jobs, len(experiment.targets))
        self.assertLessEqual(effective_jobs, 32)
        self.assertEqual(effective_jobs % len(experiment.targets), 0)
        self.assertEqual(sum(map(len, waves)), len(cells))
        for wave in waves:
            self.assertLessEqual(len(wave), effective_jobs)
            per_target = len(wave) // len(experiment.targets)
            self.assertEqual(
                {target: [cell.target_id for cell in wave].count(target) for target in (
                    "iwe-cli-only", "iwe-v18", "iwe-v18-agents",
                )},
                {
                    "iwe-cli-only": per_target,
                    "iwe-v18": per_target,
                    "iwe-v18-agents": per_target,
                },
            )

    def test_smoke_can_select_one_scenario(self) -> None:
        module = load_module(
            ROOT / "scripts/run_iwe_context_routing_ab.py",
            "run_iwe_context_routing_smoke",
        )
        args = module.parse_args([
            "--samples", "1",
            "--scenario", "fallback-when-iwe-is-unavailable",
        ])
        self.assertEqual(args.samples, 1)
        self.assertEqual(args.scenarios, ["fallback-when-iwe-is-unavailable"])
        source = module.materialize_skill_source(
            ROOT, str(ROOT.parent / "iwe-skills/skills/iwe-v18")
        )
        with mock.patch.object(module, "verify_runtime_binary", return_value=Path("/bin/true")):
            manifest_path = module.write_experiment(
                root=ROOT,
                samples=1,
                source=source,
                scenarios=("fallback-when-iwe-is-unavailable",),
            )
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["samples"], 1)
        self.assertEqual(manifest["scenarios"], ["fallback-when-iwe-is-unavailable"])

    def test_agents_template_has_only_declared_placeholders(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.encode("utf-8")), 1200)
        self.assertIn("${IWE_ROOT}", text)
        self.assertIn("${IWE_DOCUMENTS}", text)
        self.assertIn("${IWE_LANGUAGE}", text)
        self.assertNotIn("architecture decisions", text)
        self.assertNotIn("operational runbooks", text)

    def test_renderer_defaults_and_scenario_overrides(self) -> None:
        renderer = load_module(RENDERER, "iwe_context_agents_renderer")
        defaults = renderer.render(TEMPLATE)
        self.assertIn("IWE root is `.`", defaults)
        self.assertIn("project documentation", defaults)
        self.assertIn("written in English", defaults)
        overridden = renderer.render(
            TEMPLATE,
            iwe_root="knowledge",
            iwe_documents="architecture decisions and operational runbooks",
            iwe_language="Spanish",
        )
        self.assertIn("IWE root is `knowledge`", overridden)
        self.assertIn("architecture decisions and operational runbooks", overridden)
        self.assertIn("written in Spanish", overridden)

    def test_routing_contract_survives_rendering(self) -> None:
        renderer = load_module(RENDERER, "iwe_context_agents_renderer_contract")
        text = renderer.render(TEMPLATE)
        lowered = text.casefold()
        self.assertLessEqual(len(text.encode("utf-8")), 1200)
        for required in (
            "iwe is this workspace's markdown knowledge base",
            "iwe root is `.`",
            "iwe stores project documentation",
            "documents created in iwe must be written in english",
            "use iwe first without asking",
            "if iwe returns enough evidence, stop",
            "if iwe has no relevant result, search the workspace",
            "for documentation kinds not listed above, use normal workspace search",
        ):
            self.assertIn(required, lowered)
        for leaked in (
            "atlas",
            "quartz",
            "nightly reconciliation",
            "contributor bootstrap",
            "iwe find",
            "iwe retrieve",
        ):
            self.assertNotIn(leaked, lowered)

    def test_scenarios_encode_hit_miss_unlisted_and_language_routes(self) -> None:
        document = yaml.safe_load(
            SCENARIO_FILE.read_text(encoding="utf-8")
        )
        scenarios = {item["id"]: item for item in document["scenarios"]}
        self.assertTrue(set(SCENARIO_IDS) <= scenarios.keys())
        self.assertEqual(scenarios["route-listed-runbook-through-iwe"]["runtime"]["route"], "iwe-only")
        self.assertEqual(
            scenarios["route-unlisted-guide-through-workspace"]["runtime"]["route"],
            "filesystem-only",
        )
        self.assertEqual(
            scenarios["fallback-after-listed-iwe-miss"]["runtime"]["route"],
            "iwe-then-filesystem",
        )
        language = scenarios["create-iwe-document-in-declared-language"]
        self.assertEqual(language["runtime"]["route"], "iwe-only")
        self.assertEqual(language["runtime"]["forbidden_read_paths"], [".iwe/config.toml"])
        self.assertRegex(language["request"], r"[А-Яа-яЁё]")
        for scenario_id in (
            "route-listed-runbook-through-iwe",
            "route-unlisted-guide-through-workspace",
            "fallback-after-listed-iwe-miss",
        ):
            self.assertEqual(
                scenarios[scenario_id]["agents_context"]["iwe_documents"],
                "architecture decisions and operational runbooks",
            )

    def test_runner_renders_scenario_context_into_agents_file(self) -> None:
        runner = load_module(ROOT / "tests/eval/run.py", "iwe_eval_runner_agents_render")
        scenario = next(
            item for item in runner.load_scenarios(SCENARIO_FILE)
            if item.id == "route-listed-runbook-through-iwe"
        )
        with tempfile.TemporaryDirectory() as directory:
            destination = runner.install_agents_file(
                Path(directory), TEMPLATE, scenario.agents_context
            )
            self.assertIsNotNone(destination)
            text = destination.read_text(encoding="utf-8")
        self.assertIn("architecture decisions and operational runbooks", text)
        self.assertIn("written in English", text)

    def test_route_contracts_are_deterministic(self) -> None:
        runner = load_module(ROOT / "tests/eval/run.py", "iwe_eval_runner_context_routing")
        scenarios = {item.id: item for item in runner.load_scenarios(SCENARIO_FILE)}

        hit = scenarios["route-listed-runbook-through-iwe"]
        errors = runner.procedure_errors(hit, [], runner.command_metrics([]))
        self.assertIn("required initial IWE lookup missing", errors)

        unlisted = scenarios["route-unlisted-guide-through-workspace"]
        commands = [{"command": "iwe find --lexical contributor --limit 5", "output": "[]", "exit_code": 0}]
        errors = runner.procedure_errors(unlisted, commands, runner.command_metrics(commands))
        self.assertIn("IWE invoked for a filesystem-first route", errors)

        fallback = scenarios["fallback-after-listed-iwe-miss"]
        wrong_order = [
            {"command": "rg -n quartz docs", "output": "docs/quartz.md:interval: 19", "exit_code": 0},
            {"command": "iwe find --lexical quartz --limit 5 --format json", "output": "[]", "exit_code": 0},
        ]
        oracle = {"workspace_fact": {"source_path": "docs/quartz.md", "fact": "interval = 19"}}
        failures = runner.deterministic_metric_failures(
            fallback,
            wrong_order,
            oracle,
            runner.command_metrics(wrong_order),
        )
        self.assertIn("skill_compliance", failures)
        self.assertIn("before the IWE miss", failures["skill_compliance"])

    def test_language_route_rejects_config_inspection_and_non_english_output(self) -> None:
        runner = load_module(ROOT / "tests/eval/run.py", "iwe_eval_runner_context_language")
        scenario = next(
            item for item in runner.load_scenarios(SCENARIO_FILE)
            if item.id == "create-iwe-document-in-declared-language"
        )
        commands = [{
            "command": "sed -n '1,120p' .iwe/config.toml",
            "output": "[search]\nlanguage = 'english'",
            "exit_code": 0,
        }]
        errors = runner.procedure_errors(scenario, commands, runner.command_metrics(commands))
        self.assertIn("forbidden path read: .iwe/config.toml", errors)
        failures = runner.deterministic_metric_failures(
            scenario,
            [],
            {"authoring_language": {"expected": "English", "valid": False}},
            runner.command_metrics([]),
        )
        self.assertIn("task_correctness", failures)
        self.assertTrue(runner._is_english_audit_retention_decision(
            "# Audit Log Retention Decision\n\nAudit logs are stored for 90 days.\n"
        ))
        self.assertTrue(runner._is_english_audit_retention_decision(
            "# Audit Retention Decision\n\nRetain audit records for 90 days.\n"
        ))
        self.assertFalse(runner._is_english_audit_retention_decision(
            "# Решение о хранении аудита\n\nЖурналы аудита хранятся 90 дней.\n"
        ))
        self.assertFalse(runner._is_english_audit_retention_decision(
            "# Audit Policy\n\nAudit logs are stored indefinitely.\n"
        ))


if __name__ == "__main__":
    unittest.main()
