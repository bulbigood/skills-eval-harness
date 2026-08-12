from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "scripts/publish_eval_report.py"
    spec = importlib.util.spec_from_file_location("publish_eval_report_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublishEvalReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / "tests/eval/.cache")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "tests/eval/reports/run/targets/skill").mkdir(parents=True)
        (self.root / "tests/eval/results").mkdir(parents=True)
        (self.root / "docs/evals/results").mkdir(parents=True)
        (self.root / "manifest.toml").write_text(
            '# skill_source = "https://github.com/acme/skills/tree/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/skills/demo"\n'
            '# source_revision = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\n'
            '# source_payload_sha256 = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"\n'
            '# selected_skill = "demo"\n'
            'name = "demo-suite"\n',
            encoding="utf-8",
        )
        experiment = {
            "name": "demo-suite",
            "scenarios": ["scenario"],
            "samples": 1,
            "targets": [{
                "id": "skill",
                "agents_file_provenance": {"bytes": 7, "sha256": "c" * 64},
            }],
        }
        summary = {
            "experiment": "demo-suite",
            "scenarios": [{
                "target_id": "skill",
                "scenario_id": "scenario",
                "pass": True,
                "metrics": {"safety": {"pass": True}},
            }],
        }
        raw = {
            "target_id": "skill",
            "scenario_id": "scenario",
            "sample": 1,
            "verdict": {"valid": True},
        }
        (self.root / "tests/eval/reports/run/experiment.json").write_text(json.dumps(experiment), encoding="utf-8")
        (self.root / "tests/eval/reports/run/summary.json").write_text(json.dumps(summary), encoding="utf-8")
        (self.root / "tests/eval/reports/run/targets/skill/scenario--1.json").write_text(json.dumps(raw), encoding="utf-8")
        (self.root / "tests/eval/results/report.md").write_text(
            "# Generated report\n\n- Telemetry: [raw sample JSON](../reports/run/targets/skill/scenario--1.json)\n\n"
            "## Artifacts\n\n[Machine-readable report directory](../reports/run)\n",
            encoding="utf-8",
        )

    def args(self, *, replace: bool = False):
        return self.module.parse_args([
            "--run", "tests/eval/reports/run",
            "--manifest", "manifest.toml",
            "--report", "tests/eval/results/report.md",
            "--output", "docs/evals/results/demo-aaaaaaaa.md",
            "--harness-commit", "d" * 40,
            *( ["--replace"] if replace else [] ),
        ])

    def test_publish_pins_provenance_and_removes_private_links(self) -> None:
        with (
            mock.patch.object(self.module, "ROOT", self.root),
            mock.patch.object(self.module.subprocess, "run"),
        ):
            output = self.module.publish(self.args())
        text = output.read_text(encoding="utf-8")
        self.assertIn("Overall suite verdict: **PASS**", text)
        self.assertIn("Source commit: `" + "a" * 40 + "`", text)
        self.assertIn("Harness commit: `" + "d" * 40 + "`", text)
        self.assertIn("Matrix: `1` target(s) × `1` scenarios × `1` samples", text)
        self.assertNotIn("](../reports/", text)
        self.assertIn("not published", text)

    def test_publish_fails_closed_for_incomplete_run(self) -> None:
        (self.root / "tests/eval/reports/run/targets/skill/scenario--1.json").unlink()
        with (
            mock.patch.object(self.module, "ROOT", self.root),
            mock.patch.object(self.module.subprocess, "run"),
            self.assertRaisesRegex(ValueError, "incomplete run"),
        ):
            self.module.publish(self.args())

    def test_publish_requires_explicit_replace(self) -> None:
        output = self.root / "docs/evals/results/demo-aaaaaaaa.md"
        output.write_text("existing", encoding="utf-8")
        with (
            mock.patch.object(self.module, "ROOT", self.root),
            mock.patch.object(self.module.subprocess, "run"),
            self.assertRaisesRegex(FileExistsError, "--replace"),
        ):
            self.module.publish(self.args())


if __name__ == "__main__":
    unittest.main()
