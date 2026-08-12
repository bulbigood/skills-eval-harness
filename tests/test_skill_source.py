from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.eval_test_support import load_module

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class SkillSourceTests(unittest.TestCase):
    def test_production_default_pins_latest_main_iwe_v18_commit(self) -> None:
        module = load_module(ROOT / "scripts/skill_source.py", "skill_source_default_test")
        self.assertEqual(
            module.DEFAULT_SKILL_SOURCE,
            "https://github.com/iwe-org/skills/tree/"
            "f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18",
        )

    def setUp(self) -> None:
        self.module = load_module(ROOT / "scripts/skill_source.py", "skill_source_test")

    def _source_tree(self, root: Path) -> Path:
        skill = root / "skills/example"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: example\ncompatibility: Requires IWE CLI >=0.18.0.\nmetadata:\n  version: '1.2.3'\n---\n# Example\n",
            encoding="utf-8",
        )
        contract = root / "contracts/example.json"
        contract.parent.mkdir()
        contract.write_text(json.dumps({
            "schema_version": 1,
            "cli_line": "0.18",
            "default_limit": 20,
            "commands": {
                name: {} for name in (
                    "find", "retrieve", "update", "create", "extract", "delete",
                    "schema.validate",
                )
            },
        }), encoding="utf-8")
        (root / "config.toml").write_text(
            """schema_version = 1
default_skill = "example"
[skills.example]
path = "skills/example"
skill_version = "1.2.3"
[skills.example.runtime]
cli = "iwe"
source = "homebrew"
supported = ">=0.18.0"
tested = "0.18.0"
[skills.example.contract]
file = "contracts/example.json"
upstream_revision = "iwe-cli-0.18.0"
[skills.example.execution]
normal_tool_calls = 1
maximum_search_results = 20
maximum_output_bytes = 65536
network_allowed = false
forbidden_fallbacks = ["grep", "rg", "find"]
""",
            encoding="utf-8",
        )
        return skill

    def test_local_directory_and_file_uri_resolve_the_declared_skill(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/eval/.cache") as directory:
            base = Path(directory)
            skill = self._source_tree(base / "source")
            for source in (str(skill), skill.as_uri()):
                resolved = self.module.materialize_skill_source(
                    ROOT, source, Path(base.name) / "materialized"
                )
                self.assertEqual(resolved.skill.name, "example")
                self.assertEqual(resolved.skill.path.name, "example")
                self.assertEqual(resolved.revision, resolved.payload_sha256)
                self.assertTrue(resolved.skill.path.is_relative_to(ROOT))
                self.assertEqual(resolved.source, source)

    def test_local_directory_must_be_declared_by_an_enclosing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "example"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nname: example\n---\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "enclosing skill manifest"):
                self.module.materialize_skill_source(ROOT, str(skill))

    def test_source_symlink_must_not_escape_manifest_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/eval/.cache") as directory:
            source_root = Path(directory) / "source"
            skill = self._source_tree(source_root)
            (skill / "outside").symlink_to(Path(directory).parent)
            with self.assertRaisesRegex(ValueError, "symlink escapes"):
                self.module.materialize_skill_source(ROOT, str(skill))

    def test_github_directory_url_is_parsed_without_accepting_repository_url(self) -> None:
        parsed = self.module.parse_github_skill_url(
            "https://github.com/iwe-org/skills/tree/main/skills/iwe-v18"
        )
        self.assertEqual(parsed.repository, "https://github.com/iwe-org/skills.git")
        self.assertEqual(parsed.ref, "main")
        self.assertEqual(parsed.directory, "skills/iwe-v18")
        with self.assertRaisesRegex(ValueError, "directory URL"):
            self.module.parse_github_skill_url("https://github.com/iwe-org/skills")

    def test_github_materialization_pins_commit_and_selected_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/eval/.cache") as directory:
            base = Path(directory)
            repository = base / "repository"
            self._source_tree(repository)
            subprocess.run(["git", "init", "-q", "-b", "main", repository], check=True)
            subprocess.run(["git", "-C", repository, "add", "."], check=True)
            subprocess.run(
                ["git", "-C", repository, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "fixture"],
                check=True,
            )
            revision = subprocess.check_output(
                ["git", "-C", repository, "rev-parse", "HEAD"], text=True
            ).strip()
            parsed = self.module.GitHubSkillURL(
                repository=str(repository), ref=revision, directory="skills/example"
            )
            with mock.patch.object(self.module, "parse_github_skill_url", return_value=parsed):
                resolved = self.module.materialize_skill_source(
                    ROOT,
                    "https://github.com/acme/repo/tree/main/skills/example",
                    base.relative_to(ROOT) / "github-materialized",
                )
            self.assertEqual(resolved.revision, revision)
            self.assertEqual(resolved.skill.name, "example")
            self.assertEqual(resolved.directory, "skills/example")

    def test_wrappers_expose_only_skill_source(self) -> None:
        for relative in (
            "scripts/run_default_skill_eval.py",
            "scripts/run_skill_guidance_efficiency_ab.py",
            "scripts/run_iwe_context_routing_ab.py",
        ):
            module = load_module(ROOT / relative, f"source_cli_{Path(relative).stem}")
            defaults = module.parse_args(["--list"])
            self.assertEqual(defaults.skill_source, self.module.DEFAULT_SKILL_SOURCE)
            args = module.parse_args(["--skill-source", "/tmp/example", "--list"])
            self.assertEqual(args.skill_source, "/tmp/example")
            with self.assertRaises(SystemExit):
                module.parse_args(["--repository", "/tmp/repository", "--list"])


if __name__ == "__main__":
    unittest.main()
