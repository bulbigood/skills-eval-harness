from pathlib import Path

from skills_eval_harness.models import load_suite, load_yaml


ROOT = Path(__file__).resolve().parents[1]


def test_smoke_31_suite_covers_the_complete_catalog_once() -> None:
    suite = load_suite(ROOT / "evals/suites/skill-guidance-ab-smoke-31.yaml")
    catalog = load_yaml(ROOT / "evals/scenarios/iwe.yaml")
    assert isinstance(catalog, dict)
    catalog_ids = {item["id"] for item in catalog["scenarios"]}

    assert suite.id == "skill-guidance-efficiency-ab-smoke-31"
    assert suite.kind == "paired"
    assert suite.default_samples == 1
    assert len(suite.scenarios) == 31
    assert len(set(suite.scenarios)) == 31
    assert set(suite.scenarios) == catalog_ids
    assert [(arm.id, arm.role, arm.skill) for arm in suite.arms] == [
        ("skill", "treatment", True),
        ("no-skill", "control", False),
    ]
