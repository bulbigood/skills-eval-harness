from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EvalSuiteDocumentationTests(unittest.TestCase):
    def test_only_supported_eval_suite_runners_remain(self) -> None:
        runners = {
            path.name
            for path in (ROOT / "scripts").glob("run_*.py")
        }
        self.assertEqual(
            runners,
            {
                "run_default_skill_eval.py",
                "run_iwe_context_routing_ab.py",
                "run_skill_guidance_efficiency_ab.py",
            },
        )

    def test_retired_agents_fast_path_suites_are_removed(self) -> None:
        retired = (
            "scripts/run_iwe_agents_preinject_ab.py",
            "scripts/run_iwe_agents_inject_optimization_ab.py",
            "tests/eval/guidance/iwe-routes.AGENTS.md",
            "tests/eval/guidance/iwe-routes-optimized.AGENTS.md",
            "tests/eval/results/iwe-agents-preinject-ab.md",
            "tests/eval/results/iwe-agents-inject-optimization-ab.md",
        )
        for relative in retired:
            with self.subTest(path=relative):
                self.assertFalse((ROOT / relative).exists())

    def test_root_readme_is_only_an_eval_suite_index(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        headings = [line for line in text.splitlines() if line.startswith("#")]
        self.assertEqual(
            headings,
            [
                "# IWE evaluation suites",
                "## Evaluation runs",
                "## A/B test suites",
            ],
        )
        expected_links = (
            "docs/evals/default-skill-correctness-efficiency.md",
            "docs/evals/skill-guidance-efficiency-ab.md",
            "docs/evals/context-routing-ab.md",
        )
        for link in expected_links:
            self.assertEqual(text.count(f"]({link})"), 1)
        for retired_term in (
            "preinject",
            "inject optimization",
            "## Install",
            "## Skills",
            "Latest",
        ):
            self.assertNotIn(retired_term, text)

    def test_each_active_suite_has_complete_documentation(self) -> None:
        documents = {
            "docs/evals/default-skill-correctness-efficiency.md": (
                "discover-and-retrieve-bounded-multi-hop-context",
                "fallback-when-iwe-is-unavailable",
                "fix-code-without-activating-iwe",
            ),
            "docs/evals/skill-guidance-efficiency-ab.md": (
                "discover-and-retrieve-bounded-multi-hop-context",
                "query-structured-metadata-without-scanning-files",
                "ambiguous-discovery-with-one-follow-up",
            ),
            "docs/evals/context-routing-ab.md": (
                "route-listed-runbook-through-iwe",
                "route-unlisted-guide-through-workspace",
                "fallback-after-listed-iwe-miss",
                "fallback-when-iwe-is-unavailable",
                "create-iwe-document-in-declared-language",
            ),
        }
        required_sections = (
            "## Purpose",
            "## Test conditions",
            "## Scenarios",
            "## Fixtures and deterministic contracts",
            "## Evaluation method",
            "## Run",
            "## Matrix and model cost",
        )
        for relative, scenario_ids in documents.items():
            with self.subTest(document=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                for section in required_sections:
                    self.assertIn(section, text)
                for parameter in (
                    "--agent {codex,claude}",
                    "--samples N",
                    "--jobs N",
                    "--scenario ID",
                    "--results-file PATH",
                    "--list",
                ):
                    self.assertIn(f"`{parameter}`", text)
                self.assertIn("--agent claude", text)
                self.assertIn("`--skill-source SOURCE`", text)
                self.assertIn("file://", text)
                self.assertIn("/tree/REF/PATH", text)
                self.assertTrue("## Target" in text or "## Arms" in text)
                for scenario_id in scenario_ids:
                    self.assertIn(f"`{scenario_id}`", text)


if __name__ == "__main__":
    unittest.main()
