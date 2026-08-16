"""Deterministic composable rendering for schema-v5 evaluation reports."""
from __future__ import annotations

import html
import hashlib
import json
import re
from urllib.parse import quote
from typing import Any

from .acceptance import DIMENSIONS as SCORES, MEASURES, METRICS
from .report_models import ReportContext
from .summary import SummaryV5


PRESENTATION_SCORES = (
    "skill_compliance", "task_correctness", "scenario_compliance", "safety",
    "evidence_quality", "tool_efficiency", "resource_efficiency",
)
PRESENTATION_MEASURES = (*PRESENTATION_SCORES, *METRICS)
PRESENTATION_INDEX = {name: index for index, name in enumerate(PRESENTATION_MEASURES)}


def _escape(value: object) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return html.escape(text, quote=True).replace("\\", "\\\\").replace("|", "\\|").replace("`", "\\`").replace("[", "\\[").replace("]", "\\]")


def _link(value: str) -> str:
    return quote(value, safe="/:#?&=%+~@,;!$'*-._")


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:.6f}" if 0 < abs(value) < .01 else f"{value:.3f}"
    return _escape(value)


def _without_medians(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", by_alias=True)
    if isinstance(value, dict):
        return {k: _without_medians(v) for k, v in value.items() if k != "p50" and "median" not in k.lower()}
    if isinstance(value, list):
        return [_without_medians(v) for v in value]
    return value


def _identity(context: ReportContext) -> str:
    evidence = f"[`run-seal.json`]({_link(context.publication.evidence_link)})" if context.publication.evidence_link else "not staged with this report"
    return "\n".join((
        "## Report identity", "",
        f"- Run ID: `{_escape(context.identity.run_id)}`", f"- Report revision: `{_escape(context.identity.report_revision)}`",
        f"- Suite: `{_escape(context.identity.suite_id)}` (`{context.identity.suite_kind}`)", "- Summary schema: `5`",
        f"- Run purpose: `{_escape(context.identity.run_purpose)}`",
        f"- Report checksum: [`{_escape(context.publication.checksum_name)}`]({_link(context.publication.checksum_name)})",
        f"- Sealed evidence: {evidence}",
    ))


def _status(context: ReportContext) -> str:
    status = context.summary.evaluation_status
    acceptance = status.acceptance
    lines = ["## Status", "", f"- Evidence integrity: **{status.evidence_integrity.upper()}**",
             f"- Suite acceptance: **{'PASS' if acceptance.passed else 'FAIL'}** (`{_escape(acceptance.policy_id)}`)"]
    if context.identity.suite_kind == "paired":
        lines.append("- Statistical superiority: **not asserted**")
    samples = context.summary.interpretation.samples_per_identity
    if samples == 1:
        lines.append(
            "- Inference limitation: this smoke run contains one sample per arm/scenario. "
            "PASS means only that the observed samples satisfy the declared acceptance policy; "
            "run-to-run variability, reproducibility, and generalizable treatment superiority "
            "were not estimated."
        )
    return "\n".join(lines)


def _key_results(context: ReportContext) -> str:
    summary = context.summary
    reliability = summary.reliability
    valid_cells = sum(reliability.valid_cells_by_arm.values())
    lines = ["## Key results", "", f"- Valid cells: `{valid_cells}` / `{summary.expected_cells}`."]
    if context.identity.suite_kind == "paired":
        lines.append(
            f"- Common-valid pairs: `{reliability.common_valid_pairs}` / "
            f"`{reliability.planned_pairs}`."
        )
    blockers = [item for item in summary.acceptance.criteria if not item.pass_]
    if blockers:
        lines.append("- Acceptance blockers:")
        lines.extend(
            f"  - `{_escape(item.arm)} / {_escape(item.scenario_id)} / "
            f"{_escape(item.dimension)}`: `{item.passed_samples}/{item.total_samples}` "
            f"({item.observed_pass_rate:.0%}) < required `{item.required_pass_rate:.0%}`."
            for item in blockers
        )
    else:
        lines.append("- Acceptance blockers: none.")
    if context.identity.suite_kind == "paired":
        paired = summary.statistics.common_valid_paired["overall"]
        scores = paired["score_delta_treatment_minus_control"]
        metrics = paired["metric_delta_treatment_minus_control"]
        lines.append("- Selected overall treatment-minus-control deltas:")
        selected_scores = (
            "task_correctness", "scenario_compliance", "tool_efficiency", "resource_efficiency"
        )
        score_parts = [
            f"{name.replace('_', ' ')}: `{_fmt(scores[name]['mean'])}`"
            for name in selected_scores
            if name in scores
        ]
        if score_parts:
            lines.append("  - " + "; ".join(score_parts) + ".")
        selected_metrics = ("wall_time_seconds", "n_input_tokens", "cost_usd")
        metric_parts = [
            f"{name.replace('_', ' ')}: `{_fmt(metrics[name]['mean'])}`"
            for name in selected_metrics
            if name in metrics
        ]
        if metric_parts:
            lines.append("  - " + "; ".join(metric_parts) + ".")
    return "\n".join(lines)


def _configuration(context: ReportContext) -> str:
    lines = ["## Execution and model configuration", "", "| Arm | Role | Skill | Worker | Model (reasoning) |", "|---|---|---|---|---|"]
    for arm in sorted(context.identity.arms, key=lambda item: item["id"]):
        skill = f"{context.provenance.skill_name} v{context.provenance.skill_version}" if arm["skill"] else "none"
        lines.append(f"| `{_escape(arm['id'])}` | `{_escape(arm['role'] or 'absolute')}` | {_escape(skill)} | `{_escape(context.execution.agent_name)} {_escape(context.execution.agent_version)}` | `{_escape(context.execution.worker_model)} (reasoning: {_escape(context.execution.worker_reasoning)})` |")
    lines += ["", "### Judge configuration", "", f"- Backend: `{_escape(context.execution.judge_backend)}`", f"- Model: `{_escape(context.execution.judge_model)}`", f"- Reasoning: `{_escape(context.execution.judge_reasoning)}`", "- Dimensions: `skill_compliance`, `task_correctness`, `scenario_compliance`, `safety`, `evidence_quality`, `tool_efficiency`, `resource_efficiency`", "", f"Runtime: `{_escape(context.execution.runtime_version)}` (`{context.execution.runtime_sha256}`). Worker image: `{context.execution.agent_image_sha256}`. Verifier image: `{context.execution.verifier_image_sha256}`. Harbor: `{_escape(context.execution.harbor_version)}`. Node: `{_escape(context.execution.node_version)}`."]
    return "\n".join(lines)


def _provenance(context: ReportContext) -> str:
    task_json = json.dumps(context.provenance.task_checksums, sort_keys=True, indent=2)
    task_digest = hashlib.sha256(
        json.dumps(
            context.provenance.task_checksums,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return "\n".join((
        "## Provenance", "",
        f"- Harness: [{_escape(context.provenance.harness_repository)}]({_link(context.provenance.harness_repository)}) commit `{context.provenance.harness_commit}`, tree `{context.provenance.harness_tree_sha256}`",
        f"- Source: [{_escape(context.provenance.skill_url)}]({_link(context.provenance.skill_url)}) commit `{context.provenance.source_commit}`, tree `{context.provenance.source_tree_sha256}`",
        f"- Selected skill: `{_escape(context.provenance.skill_name)}` v`{_escape(context.provenance.skill_version)}`, tree `{context.provenance.skill_sha256}`",
        f"- Config / suite / catalog: `{context.provenance.config_sha256}` / `{context.provenance.suite_sha256}` / `{context.provenance.catalog_sha256}`",
        f"- Effective suite / fixture registry: `{context.provenance.effective_suite_sha256}` / `{context.provenance.fixture_registry_sha256}`",
        f"- Task identities: `{len(context.provenance.task_checksums)}` entries; canonical map SHA-256 `{task_digest}`.",
        "", "<details>", "<summary>Complete task identity map</summary>", "",
        "```json", task_json, "```", "", "</details>",
    ))


def _acceptance(summary: SummaryV5) -> str:
    acceptance = summary.acceptance
    lines = ["## Acceptance policy and result", "", f"Policy `{_escape(acceptance.policy_id)}` result: **{'PASS' if acceptance.pass_ else 'FAIL'}**.", "", "| Dimension | Score threshold | Sample pass-rate threshold |", "|---|---:|---:|"]
    for name in PRESENTATION_SCORES:
        if name not in acceptance.score_thresholds:
            continue
        lines.append(f"| `{name}` | {acceptance.score_thresholds[name]} | {acceptance.sample_pass_rate_thresholds[name]:.0%} |")
    lines += ["", "### Acceptance ledger", "", "| Arm | Scenario | Dimension | Passed | Observed | Required | Result |", "|---|---|---|---:|---:|---:|---|"]
    for row in sorted(acceptance.criteria, key=lambda item: (item.arm, item.scenario_id, PRESENTATION_INDEX[item.dimension])):
        lines.append(f"| `{_escape(row.arm)}` | `{_escape(row.scenario_id)}` | `{_escape(row.dimension)}` | {row.passed_samples} / {row.total_samples} | {row.observed_pass_rate:.0%} | {row.required_pass_rate:.0%} | {'PASS' if row.pass_ else '**FAIL**'} |")
    lines += ["", "The suite passes only when evidence is valid and every applicable criterion passes. Control arms are acceptance-blocking only for safety."]
    return "\n".join(lines)


def _distribution_rows(groups: dict[str, Any], label: str) -> list[str]:
    rows = [f"### {label}", "", "| Group | Arm | Measure | Mean | n | Direction |", "|---|---|---|---:|---:|---|"]
    for group_name, arms in sorted(groups.items()):
        for arm, stats in sorted(arms.items()):
            for name in PRESENTATION_MEASURES:
                dist = stats.get("scores", {}).get(name) if name in SCORES else stats.get(name)
                if dist:
                    direction = next(item.direction for item in MEASURES if item.name == name)
                    rows.append(f"| `{_escape(group_name)}` | `{_escape(arm)}` | `{name}` | {_fmt(dist['mean'])} | {dist['n']} | {direction} |")
    return rows


def _descriptive(context: ReportContext) -> str:
    available = context.summary.statistics.available_valid
    lines = ["## Descriptive results", "", *_distribution_rows({"overall": available["overall"]}, "Overall"), "", *_distribution_rows(available["per_scenario"], "Per scenario"), "", *_distribution_rows(available["per_family"], "Per family")]
    if context.identity.suite_kind == "paired":
        paired = context.summary.statistics.common_valid_paired
        lines += ["", "### Common-valid paired cohorts and treatment-minus-control deltas", "", "All deltas are treatment minus control. Positive score deltas are better; negative resource deltas are better.", "", "| Group | Measure | Mean delta | n |", "|---|---|---:|---:|"]
        for scope, groups in (("overall", {"overall": paired["overall"]}), ("scenario", paired["per_scenario"]), ("family", paired["per_family"])):
            for name, group in sorted(groups.items()):
                deltas = {**group["score_delta_treatment_minus_control"], **group["metric_delta_treatment_minus_control"]}
                for measure in PRESENTATION_MEASURES:
                    if measure not in deltas:
                        continue
                    dist = deltas[measure]
                    lines.append(f"| `{scope}:{_escape(name)}` | `{measure}` | {_fmt(dist['mean'])} | {dist['n']} |")
    return "\n".join(lines)


def _failures(context: ReportContext) -> str:
    summary = context.summary
    cells = summary.cells
    deterministic = sorted((c for c in cells if c.scenario_outcome == "failed"), key=lambda c: (c.arm, c.scenario_id, c.sample))
    invalid = sorted((c for c in cells if not c.valid), key=lambda c: (c.arm, c.scenario_id, c.sample))
    lines = ["## Failures and reliability", "", "### Deterministic benchmark failures", ""]
    lines.append("None." if not deterministic else "\n".join(f"- `{_escape(c.arm)}/{_escape(c.scenario_id)}/{c.sample}`: {_escape('; '.join(c.scenario_failures))}" for c in deterministic))
    lines += ["", "### Invalid or unavailable evidence", "", "None." if not invalid else "\n".join(f"- `{_escape(c.arm)}/{_escape(c.scenario_id)}/{c.sample}`: `{_escape(c.invalid_reason)}`" for c in invalid)]
    reliability = summary.reliability
    lines += ["", "### Reliability and missingness", "", f"- Planned / observed / valid cells: `{summary.expected_cells}` / `{summary.observed_cells}` / `{sum(reliability.valid_cells_by_arm.values())}`.", f"- Deterministic failures by arm: `{json.dumps(reliability.scenario_failures_by_arm, sort_keys=True)}`.", f"- Missingness by scenario: `{json.dumps(reliability.missingness_by_scenario, sort_keys=True)}`.", f"- Missingness by family: `{json.dumps(reliability.missingness_by_family, sort_keys=True)}`."]
    if context.identity.suite_kind == "paired":
        lines += [f"- Common-valid pairs: `{reliability.common_valid_pairs}` / `{reliability.planned_pairs}`.", f"- Excluded pairs: `{json.dumps(reliability.excluded_pairs, sort_keys=True)}`."]
    return "\n".join(lines)


def _timing(summary: SummaryV5) -> str:
    timing = summary.timing
    lines = ["## Timing", "", f"- Available-valid summed cell-seconds: `{_fmt(timing.available_valid_summed_cell_seconds)}`."]
    if timing.common_valid_summed_cell_seconds is not None:
        lines.append(f"- Common-valid summed cell-seconds: `{_fmt(timing.common_valid_summed_cell_seconds)}`.")
    lines += [f"- Pipeline elapsed seconds: `{_fmt(timing.pipeline_elapsed_seconds)}`.", "", "Summed cell-seconds measure aggregate worker trial time; pipeline elapsed time measures end-to-end execution including judging and concurrency."]
    return "\n".join(lines)


def _audit(context: ReportContext) -> str:
    summary = context.summary.model_dump(mode="json", by_alias=True)
    payload = {key: summary[key] for key in ("schema_version", "analysis", "evaluation_status", "acceptance", "reliability", "statistics", "timing", "measurement_scope", "interpretation")}
    encoded = json.dumps(_without_medians(payload), ensure_ascii=False, sort_keys=True, indent=2)
    fence = "`" * (max((len(run) for run in re.findall(r"`+", encoded)), default=2) + 1)
    return "\n".join((
        "## Audit appendix", "",
        "Cell-level evidence is retained in the source bundle's sealed publishable-evidence scope "
        "but is not included in this publication. The seal covers the evidence consumed by bundle "
        "validation and report generation, not transient raw Harbor operational files.", "",
        "<details>", "<summary>Complete sanitized summary JSON</summary>", "",
        f"{fence}json", encoded, fence, "", "</details>",
    ))


def _telemetry(context: ReportContext) -> str:
    encoded = json.dumps(context.telemetry.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=2)
    return "\n".join(("## Sanitized device telemetry", "", "<details>",
        "<summary>Complete sanitized device telemetry</summary>", "", "```json", encoded, "```", "", "</details>", "",
        "The report is derived from the bundled, sealed machine-readable evidence. Device telemetry is schema-constrained to numeric capacity and load measurements; hostnames, usernames, paths, environment variables, command lines, network identifiers, container names, labels, and credential material are not accepted."))


def render_report(context: ReportContext) -> str:
    """Render the complete report through one common section pipeline."""
    sections = (_identity(context), _status(context), _key_results(context), _configuration(context), _provenance(context), _acceptance(context.summary), _descriptive(context), _failures(context), _timing(context.summary), _audit(context), _telemetry(context))
    return "# Evaluation report\n\n" + "\n\n".join(sections) + "\n"
