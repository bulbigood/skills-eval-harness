from __future__ import annotations

from skills_eval_harness.models import AnalysisPlan
from skills_eval_harness.report_models import ReportContext
from skills_eval_harness.reporting import render_report
from skills_eval_harness.results import summarize_cells

from test_harbor_results import valid_cell


def context(kind: str = "absolute") -> ReportContext:
    arms = ("skill",) if kind == "absolute" else ("no-skill", "skill")
    roles = {"skill": None} if kind == "absolute" else {"no-skill": "control", "skill": "treatment"}
    identities = {(arm, "one", sample) for arm in arms for sample in (1, 2)}
    cells = [valid_cell(arm, sample) for arm in arms for sample in (1, 2)]
    summary = summarize_cells(
        cells, identities, expected_families={"one": "read"},
        analysis=AnalysisPlan(kind=kind, arms=arms, roles=roles, scenarios=("one",), families={"one": "read"}, samples=2),
        pipeline_elapsed_seconds=12.0, run_purpose="production", samples_per_identity=2, preregistered_samples=2,
    )
    sha = "a" * 64
    return ReportContext(
        summary=summary, run_id="run", report_revision="v8", suite_id="suite", suite_kind=kind,
        run_purpose="production", arms=tuple({"id": arm, "skill": arm == "skill", "role": roles[arm]} for arm in arms),
        agent_name="codex", agent_version="1.2.3", worker_model="model|unsafe", worker_reasoning="high",
        judge_backend="api-key", judge_model="judge", judge_reasoning="low", runtime_version="0.18.0",
        runtime_sha256=sha, skill_name="demo", skill_version="1.0.0", skill_url="https://example.test/tree/x",
        skill_sha256=sha, source_commit="b" * 40, source_tree_sha256=sha,
        harness_repository="https://example.test/harness", harness_commit="c" * 40, harness_tree_sha256=sha,
        harbor_version="0.21.0", node_version="22.23.2", agent_image_sha256=sha,
        verifier_image_sha256=sha, config_sha256=sha, suite_sha256=sha, catalog_sha256=sha,
        effective_suite_sha256=sha, fixture_registry_sha256=sha, task_checksums={"arm/task": sha},
        checksum_name="report.md.sha256", evidence_link=None,
    )


def test_common_contract_is_shared_by_absolute_and_paired() -> None:
    required = ["## Report identity", "## Status", "## Execution and model configuration", "## Provenance",
                "## Acceptance policy and result", "## Descriptive results", "## Failures and reliability",
                "## Timing", "## Audit appendix"]
    for kind in ("absolute", "paired"):
        report = render_report(context(kind))
        assert [report.index(section) for section in required] == sorted(report.index(section) for section in required)
        assert "skill_compliance" in report
        assert "model\\|unsafe (reasoning: high)" in report
        assert "median" not in report.lower() and '"p50"' not in report


def test_only_paired_report_adds_comparison_semantics() -> None:
    absolute = render_report(context("absolute"))
    paired = render_report(context("paired"))
    assert "Statistical superiority" not in absolute
    assert "treatment-minus-control deltas" not in absolute
    assert "Statistical superiority: **not asserted**" in paired
    assert "treatment-minus-control deltas" in paired
    assert "Excluded pairs" in paired


def test_report_is_deterministic_and_escapes_untrusted_markdown() -> None:
    model = context("absolute")
    assert render_report(model) == render_report(model)
    assert "model\\|unsafe" in render_report(model)
