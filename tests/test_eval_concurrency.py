from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from tests.eval_test_support import load_eval_module, load_runner


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
EVAL = ROOT / "tests/eval"
for path in (SCRIPTS, EVAL):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class EvalConcurrencyTests(unittest.TestCase):
    def test_default_jobs_is_four_per_physical_core_capped_at_twenty(self) -> None:
        concurrency = load_module(SCRIPTS / "eval_concurrency.py", "eval_concurrency_test_defaults")
        self.assertEqual(concurrency.default_jobs(1), 4)
        self.assertEqual(concurrency.default_jobs(2), 8)
        self.assertEqual(concurrency.default_jobs(5), 20)
        self.assertEqual(concurrency.default_jobs(64), 20)

    def test_single_arm_normalization_clamps_to_one_through_twenty(self) -> None:
        concurrency = load_module(SCRIPTS / "eval_concurrency.py", "eval_concurrency_test_single")
        self.assertEqual(concurrency.normalize_jobs(0, target_count=1, balanced=False), 1)
        self.assertEqual(concurrency.normalize_jobs(8, target_count=1, balanced=False), 8)
        self.assertEqual(concurrency.normalize_jobs(99, target_count=1, balanced=False), 20)

    def test_balanced_normalization_uses_complete_arm_groups(self) -> None:
        concurrency = load_module(SCRIPTS / "eval_concurrency.py", "eval_concurrency_test_balanced")
        self.assertEqual(concurrency.normalize_jobs(8, target_count=2, balanced=True), 8)
        self.assertEqual(concurrency.normalize_jobs(8, target_count=3, balanced=True), 6)
        self.assertEqual(concurrency.normalize_jobs(1, target_count=3, balanced=True), 3)
        self.assertEqual(concurrency.normalize_jobs(99, target_count=3, balanced=True), 18)
        with self.assertRaisesRegex(ValueError, "exceeds the jobs cap"):
            concurrency.normalize_jobs(20, target_count=21, balanced=True)

    def test_synchronized_wave_propagates_worker_failure_without_end_barrier(self) -> None:
        from eval_core import scheduling

        completed: list[tuple[int, int]] = []

        def execute(item: int, wave_id: int) -> int:
            if item == 1:
                raise RuntimeError("worker failed")
            completed.append((item, wave_id))
            return item

        with self.assertRaisesRegex(RuntimeError, "worker failed"):
            scheduling.execute_synchronized_waves([[1, 2]], execute)
        self.assertEqual(completed, [(2, 1)])

    def test_all_suite_wrappers_share_the_common_default(self) -> None:
        concurrency = load_module(SCRIPTS / "eval_concurrency.py", "eval_concurrency")
        modules = [
            load_module(SCRIPTS / name, f"concurrency_{index}")
            for index, name in enumerate((
                "run_default_skill_eval.py",
                "run_skill_guidance_efficiency_ab.py",
                "run_iwe_context_routing_ab.py",
            ))
        ]
        self.assertTrue(all(module.DEFAULT_JOBS == concurrency.DEFAULT_JOBS for module in modules))

    def test_balanced_waves_allow_a_smaller_complete_final_wave(self) -> None:
        runner = load_runner()
        experiment_module = load_eval_module("experiment")
        source_module = load_module(SCRIPTS / "skill_source.py", "concurrency_skill_source")
        source_module.materialize_skill_source(
            ROOT, str(ROOT.parent / "iwe-skills/skills/iwe-v18")
        )
        manifest = ROOT / "tests/eval/experiments/example.toml"
        experiment = experiment_module.load_experiment(manifest, ROOT)
        scenarios = runner.select_scenarios(runner.load_scenarios(), list(experiment.scenario_ids))
        cells = runner.build_matrix(experiment, scenarios)

        waves = runner.balanced_waves(cells, 6)

        self.assertEqual([len(wave) for wave in waves], [6, 2])
        self.assertTrue(all(len(wave) % len(experiment.targets) == 0 for wave in waves))


if __name__ == "__main__":
    unittest.main()
