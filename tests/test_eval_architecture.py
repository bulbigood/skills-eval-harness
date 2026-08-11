from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "tests/eval"
if str(EVAL) not in sys.path:
    sys.path.insert(0, str(EVAL))

from eval_core.agent_config import FIXTURES_FILE, load_agent_config


class EvalArchitectureTests(unittest.TestCase):
    def test_agent_profiles_use_the_shared_fixture_registry(self) -> None:
        expected = FIXTURES_FILE.read_text(encoding="utf-8")
        self.assertIn("seventeen-centuries", expected)
        for path in sorted((EVAL / "configs").glob("*.json")):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn('"fixtures"', source, path.name)
            config = load_agent_config(path)
            self.assertEqual(set(config["fixtures"]), {"seventeen-centuries", "pkm-demo"})

    def test_eval_core_modules_do_not_import_the_cli_facade(self) -> None:
        self.assertTrue((EVAL / "eval_core/oracle.py").is_file())
        self.assertTrue((EVAL / "eval_core/scoring.py").is_file())
        self.assertTrue((EVAL / "eval_core/workspace.py").is_file())
        self.assertTrue((EVAL / "eval_core/execution.py").is_file())
        for path in sorted((EVAL / "eval_core").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imports.update(
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            )
            self.assertFalse({"run", "tests.eval.run"} & imports, path.name)

    def test_cli_facade_stays_below_eight_hundred_lines(self) -> None:
        line_count = len((EVAL / "run.py").read_text(encoding="utf-8").splitlines())
        self.assertLess(line_count, 800)

    def test_test_modules_stay_below_two_thousand_lines(self) -> None:
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            self.assertLess(line_count, 2000, path.name)


if __name__ == "__main__":
    unittest.main()
