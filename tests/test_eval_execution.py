from __future__ import annotations

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

from eval_core.execution import WorkspaceLease, _resolve_cell


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


if __name__ == "__main__":
    unittest.main()
