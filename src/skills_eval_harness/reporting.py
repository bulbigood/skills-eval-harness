"""Deterministic composable rendering for schema-v5 evaluation reports."""
from __future__ import annotations

import html
import json
from typing import Any

from .report_models import ReportContext

SCORES = ("task_correctness", "scenario_compliance", "skill_compliance", "safety", "evidence_quality", "tool_efficiency", "resource_efficiency")
METRICS = ("wall_time_seconds", "n_input_tokens", "n_cache_tokens", "n_output_tokens", "cost_usd")


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True).replace("|", "\\|").replace("\n", " ")


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:.6f}" if 0 < abs(value) < .01 else f"{value:.3f}"
    return _escape(value)


def _without_medians(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _without_medians(v) for k, v in value.items() if k != "p50" and "median" not in k.lower()}
    if isinstance(value, list):
        return [_without_medians(v) for v in value]
    return value


def _identity(context: ReportContext) -> str:
    evidence = f"[`run-seal.json`]({context.evidence_link})" if context.evidence_link else "not staged with this report"
    return "\n".join((
        "## Report identity", "",
        f"- Run ID: `{_escape(context.run_id)}`", f"- Report revision: `{_escape(context.report_revision)}`",
        f"- Suite: `{_escape(context.suite_id)}` (`{context.suite_kind}`)", "- Summary schema: `5`",
        f"- Run purpose: `{_escape(context.run_purpose)}`",
        f"- Report checksum: [`{_escape(context.checksum_name)}`]({_escape(context.checksum_name)})",
        f"- Sealed evidence: {evidence}",
    ))


def _status(context: ReportContext) -> str:
    status = context.summary["evaluation_status"]
    acceptance = status["acceptance"]
    lines = ["## Status", "", f"- Evidence integrity: **{status['evidence_integrity'].upper()}**",
             f"- Suite acceptance: **{'PASS' if acceptance['passed'] else 'FAIL'}** (`{_escape(acceptance['policy_id'])}`)"]
    if context.suite_kind == "paired":
        lines.append("- Statistical superiority: **not asserted**")
    return "\n".join(lines)


def _configuration(context: ReportContext) -> str:
    lines = ["## Execution and model configuration", "", "| Arm | Role | Skill | Worker | Model (reasoning) |", "|---|---|---|---|---|"]
    for arm in sorted(context.arms, key=lambda item: item["id"]):
        skill = f"{context.skill_name} v{context.skill_version}" if arm["skill"] else "none"
        lines.append(f"| `{_escape(arm['id'])}` | `{_escape(arm['role'] or 'absolute')}` | {_escape(skill)} | `{_escape(context.agent_name)} {_escape(context.agent_version)}` | `{_escape(context.worker_model)} (reasoning: {_escape(context.worker_reasoning)})` |")
    lines += ["", "### Judge configuration", "", f"- Backend: `{_escape(context.judge_backend)}`", f"- Model: `{_escape(context.judge_model)}`", f"- Reasoning: `{_escape(context.judge_reasoning)}`", "- Dimensions: `task_correctness`, `scenario_compliance`, `skill_compliance`, `safety`, `evidence_quality`, `tool_efficiency`, `resource_efficiency`", "", f"Runtime: `{_escape(context.runtime_version)}` (`{context.runtime_sha256}`). Worker image: `{context.agent_image_sha256}`. Verifier image: `{context.verifier_image_sha256}`. Harbor: `{_escape(context.harbor_version)}`. Node: `{_escape(context.node_version)}`."]
    return "\n".join(lines)


def _provenance(context: ReportContext) -> str:
    return "\n".join(("## Provenance", "", f"- Harness: [{_escape(context.harness_repository)}]({_escape(context.harness_repository)}) commit `{context.harness_commit}`, tree `{context.harness_tree_sha256}`", f"- Source: [{_escape(context.skill_url)}]({_escape(context.skill_url)}) commit `{context.source_commit}`, tree `{context.source_tree_sha256}`", f"- Selected skill: `{_escape(context.skill_name)}` v`{_escape(context.skill_version)}`, tree `{context.skill_sha256}`", f"- Config / suite / catalog: `{context.config_sha256}` / `{context.suite_sha256}` / `{context.catalog_sha256}`", f"- Effective suite / fixture registry: `{context.effective_suite_sha256}` / `{context.fixture_registry_sha256}`", f"- Task identities: `{_escape(json.dumps(context.task_checksums, sort_keys=True))}`"))


def _acceptance(summary: dict[str, Any]) -> str:
    acceptance = summary["acceptance"]
    lines = ["## Acceptance policy and result", "", f"Policy `{_escape(acceptance['policy_id'])}` result: **{'PASS' if acceptance['pass'] else 'FAIL'}**.", "", "| Dimension | Score threshold | Sample pass-rate threshold |", "|---|---:|---:|"]
    for name in sorted(acceptance["score_thresholds"]):
        lines.append(f"| `{name}` | {acceptance['score_thresholds'][name]} | {acceptance['sample_pass_rate_thresholds'][name]:.0%} |")
    lines += ["", "### Acceptance ledger", "", "| Arm | Scenario | Dimension | Passed | Observed | Required | Result |", "|---|---|---|---:|---:|---:|---|"]
    for row in sorted(acceptance["criteria"], key=lambda item: (item["arm"], item["scenario_id"], item["dimension"])):
        lines.append(f"| `{_escape(row['arm'])}` | `{_escape(row['scenario_id'])}` | `{_escape(row['dimension'])}` | {row['passed_samples']} / {row['total_samples']} | {row['observed_pass_rate']:.0%} | {row['required_pass_rate']:.0%} | {'PASS' if row['pass'] else '**FAIL**'} |")
    lines += ["", "The suite passes only when evidence is valid and every applicable criterion passes. Control arms are acceptance-blocking only for safety."]
    return "\n".join(lines)


def _distribution_rows(groups: dict[str, Any], label: str) -> list[str]:
    rows = [f"### {label}", "", "| Group | Arm | Measure | Mean | n | Direction |", "|---|---|---|---:|---:|---|"]
    for group_name, arms in sorted(groups.items()):
        for arm, stats in sorted(arms.items()):
            for name in (*SCORES, *METRICS):
                dist = stats.get("scores", {}).get(name) if name in SCORES else stats.get(name)
                if dist:
                    direction = "higher is better" if name in SCORES else "lower is better"
                    rows.append(f"| `{_escape(group_name)}` | `{_escape(arm)}` | `{name}` | {_fmt(dist['mean'])} | {dist['n']} | {direction} |")
    return rows


def _descriptive(context: ReportContext) -> str:
    available = context.summary["statistics"]["available_valid"]
    lines = ["## Descriptive results", "", *_distribution_rows({"overall": available["overall"]}, "Overall"), "", *_distribution_rows(available["per_scenario"], "Per scenario"), "", *_distribution_rows(available["per_family"], "Per family")]
    if context.suite_kind == "paired":
        paired = context.summary["statistics"]["common_valid_paired"]
        lines += ["", "### Common-valid paired cohorts and treatment-minus-control deltas", "", "All deltas are treatment minus control. Positive score deltas are better; negative resource deltas are better.", "", "| Group | Measure | Mean delta | n |", "|---|---|---:|---:|"]
        for scope, groups in (("overall", {"overall": paired["overall"]}), ("scenario", paired["per_scenario"]), ("family", paired["per_family"])):
            for name, group in sorted(groups.items()):
                for measure, dist in sorted({**group["score_delta_treatment_minus_control"], **group["metric_delta_treatment_minus_control"]}.items()):
                    lines.append(f"| `{scope}:{_escape(name)}` | `{measure}` | {_fmt(dist['mean'])} | {dist['n']} |")
    return "\n".join(lines)


def _failures(context: ReportContext) -> str:
    summary = context.summary
    cells = summary["cells"]
    deterministic = sorted((c for c in cells if c.get("scenario_outcome") == "failed"), key=lambda c: (c["arm"], c["scenario_id"], c["sample"]))
    invalid = sorted((c for c in cells if not c["valid"]), key=lambda c: (c["arm"], c["scenario_id"], c["sample"]))
    lines = ["## Failures and reliability", "", "### Deterministic benchmark failures", ""]
    lines.append("None." if not deterministic else "\n".join(f"- `{_escape(c['arm'])}/{_escape(c['scenario_id'])}/{c['sample']}`: {_escape('; '.join(c['scenario_failures']))}" for c in deterministic))
    lines += ["", "### Invalid or unavailable evidence", "", "None." if not invalid else "\n".join(f"- `{_escape(c['arm'])}/{_escape(c['scenario_id'])}/{c['sample']}`: `{_escape(c['invalid_reason'])}`" for c in invalid)]
    reliability = summary["reliability"]
    lines += ["", "### Reliability and missingness", "", f"- Planned / observed / valid cells: `{summary['expected_cells']}` / `{summary['observed_cells']}` / `{sum(reliability['valid_cells_by_arm'].values())}`.", f"- Deterministic failures by arm: `{json.dumps(reliability['scenario_failures_by_arm'], sort_keys=True)}`.", f"- Missingness by scenario: `{json.dumps(reliability['missingness_by_scenario'], sort_keys=True)}`.", f"- Missingness by family: `{json.dumps(reliability['missingness_by_family'], sort_keys=True)}`."]
    if context.suite_kind == "paired":
        lines += [f"- Common-valid pairs: `{reliability['common_valid_pairs']}` / `{reliability['planned_pairs']}`.", f"- Excluded pairs: `{json.dumps(reliability['excluded_pairs'], sort_keys=True)}`."]
    return "\n".join(lines)


def _timing(summary: dict[str, Any]) -> str:
    timing = summary["timing"]
    lines = ["## Timing", "", f"- Available-valid summed cell-seconds: `{_fmt(timing['available_valid_summed_cell_seconds'])}`."]
    if timing["common_valid_summed_cell_seconds"] is not None:
        lines.append(f"- Common-valid summed cell-seconds: `{_fmt(timing['common_valid_summed_cell_seconds'])}`.")
    lines += [f"- Pipeline elapsed seconds: `{_fmt(timing['pipeline_elapsed_seconds'])}`.", "", "Summed cell-seconds measure aggregate worker trial time; pipeline elapsed time measures end-to-end execution including judging and concurrency."]
    return "\n".join(lines)


def _audit(context: ReportContext) -> str:
    summary = context.summary
    payload = {key: summary[key] for key in ("schema_version", "analysis", "evaluation_status", "acceptance", "reliability", "statistics", "timing", "measurement_scope", "interpretation")}
    return "\n".join(("## Audit appendix", "", "Cells, judge inputs, and verdicts remain in the sealed evidence bundle and are not duplicated here.", "", "```json", json.dumps(_without_medians(payload), ensure_ascii=False, sort_keys=True, indent=2), "```"))


def render_report(context: ReportContext) -> str:
    """Render the complete report through one common section pipeline."""
    sections = (_identity(context), _status(context), _configuration(context), _provenance(context), _acceptance(context.summary), _descriptive(context), _failures(context), _timing(context.summary), _audit(context))
    return "# Evaluation report\n\n" + "\n\n".join(sections) + "\n"
