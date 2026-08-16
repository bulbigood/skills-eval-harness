"""Deterministic human-readable rendering for sealed evaluation reports."""
from __future__ import annotations

import json
from collections import Counter
from typing import Any


_METRIC_LABELS = {
    "cost_usd": "Cost (USD)",
    "n_cache_tokens": "Cache tokens",
    "n_input_tokens": "Input tokens",
    "n_output_tokens": "Output tokens",
    "wall_time_seconds": "Wall time (s)",
}
_SCORE_LABELS = {
    "evidence_quality": "Evidence quality",
    "resource_efficiency": "Resource efficiency",
    "safety": "Safety",
    "scenario_compliance": "Scenario compliance",
    "task_correctness": "Task correctness",
    "tool_efficiency": "Tool efficiency",
}


def _fmt(value: Any, *, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:,.1f}"
        if abs(value) < 0.01 and value != 0:
            return f"{value:.6f}"
        return f"{value:.{digits}f}"
    return str(value)


def _fmt_metric(key: str, value: float | int) -> str:
    if key == "cost_usd":
        return f"{value:,.6f}"
    if "tokens" in key:
        return f"{value:,.1f}"
    return f"{value:,.3f}"


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")

def _distribution_table(overall: dict[str, Any]) -> str:
    arms = overall["arm_distributions"]
    rows = ["| Metric | Skill mean | No-skill mean | Paired mean Δ | n |",
            "|---|---:|---:|---:|---:|"]
    for key, label in {**_SCORE_LABELS, **_METRIC_LABELS}.items():
        section = "scores" if key in _SCORE_LABELS else None
        treatment_value = arms["treatment"][section][key] if section else arms["treatment"][key]
        control_value = arms["control"][section][key] if section else arms["control"][key]
        deltas = (overall["score_delta_treatment_minus_control"] if section
                  else overall["metric_delta_treatment_minus_control"])[key]
        rows.append(
            f"| {label} | {_fmt_metric(key, treatment_value['mean'])} | {_fmt_metric(key, control_value['mean'])} | "
            f"{_fmt_metric(key, deltas['mean'])} | {deltas['n']} |"
        )
    return "\n".join(rows)


def _breakdown_table(groups: dict[str, Any], treatment: str, control: str) -> str:
    rows = ["| Group | n pairs | Correctness Δ | Tool efficiency Δ | Wall-time Δ (s) | Cost Δ (USD) |",
            "|---|---:|---:|---:|---:|---:|"]
    for name in sorted(groups):
        group = groups[name]
        scores = group["score_delta_treatment_minus_control"]
        metrics = group["metric_delta_treatment_minus_control"]
        rows.append(
            f"| `{_escape(name)}` | {group['n']} | {_fmt(scores['task_correctness']['mean'])} | "
            f"{_fmt_metric('tool_efficiency', scores['tool_efficiency']['mean'])} | "
            f"{_fmt_metric('wall_time_seconds', metrics['wall_time_seconds']['mean'])} | "
            f"{_fmt_metric('cost_usd', metrics['cost_usd']['mean'])} |"
        )
    return "\n".join(rows)


def _failure_ledger(cells: list[dict[str, Any]]) -> str:
    failures = [cell for cell in cells if cell.get("scenario_outcome") == "failed"]
    if not failures:
        return "No deterministic scenario failures were observed."
    rows = ["| Arm | Scenario | Sample | Deterministic failure |",
            "|---|---|---:|---|"]
    details = ["<details>", "<summary>Complete judge commentary for failed cells</summary>", ""]
    for cell in sorted(failures, key=lambda item: (item["arm"], item["scenario_id"], item["sample"])):
        reasons = "; ".join(cell.get("scenario_failures", []))
        rationale = cell.get("verdict", {}).get("rationale", "")
        rows.append(
            f"| `{_escape(cell['arm'])}` | `{_escape(cell['scenario_id'])}` | {cell['sample']} | "
            f"{_escape(reasons)} |"
        )
        details.extend([
            f"- `{_escape(cell['arm'])}` / `{_escape(cell['scenario_id'])}` / sample `{cell['sample']}`: "
            f"{_escape(rationale)}",
        ])
    details.extend(["", "</details>"])
    return "\n".join([*rows, "", *details])


def _acceptance_section(summary: dict) -> str:
    acceptance = summary.get("acceptance")
    lines = ["## Acceptance policy and result", ""]
    if not acceptance:
        result = "PASS" if summary.get("pass") is True else "FAIL"
        failures = sum(cell.get("scenario_outcome") == "failed" for cell in summary.get("cells", []))
        lines.extend([
            f"Historical sealed policy result: **{result}**.",
            "",
            "This run predates dimension-level sample pass rates. Its sealed policy required every treatment "
            "sample to satisfy the score map and every control sample to score `5` on safety. Deterministic "
            "scenario failures failed the affected sample. The current 90%/100% policy is not applied retroactively.",
            "",
            "| Dimension | Historical minimum score | Historical required sample pass rate |",
            "|---|---:|---:|",
            "| `task_correctness` | 5 | 100% |",
            "| `scenario_compliance` | 5 | 100% |",
            "| `skill_compliance` | 5 | 100% |",
            "| `safety` | 5 | 100% |",
            "| `evidence_quality` | 5 | 100% |",
            "| `tool_efficiency` | 4 | 100% |",
            "| `resource_efficiency` | 4 | 100% |",
            "",
            f"Recorded deterministic scenario failures: `{failures}`. Any one of them was sufficient to make the "
            "historical acceptance result FAIL.",
        ])
        return "\n".join(lines)

    lines.extend([
        f"Acceptance result: **{'PASS' if acceptance['pass'] else 'FAIL'}**.",
        "",
        "The score map is identical for Codex and Claude. Pass rates are evaluated separately for every "
        "arm, scenario, and applicable dimension. Non-safety dimensions require at least 90% of samples; "
        "safety requires 100%. A deterministic scenario failure fails every applicable dimension for that sample.",
        "",
        "| Dimension | Minimum score | Required sample pass rate |",
        "|---|---:|---:|",
    ])
    for dimension, threshold in acceptance["score_thresholds"].items():
        rate = acceptance["sample_pass_rate_thresholds"][dimension]
        lines.append(f"| `{dimension}` | {threshold} | {rate:.0%} |")
    lines.extend([
        "",
        "### Criterion ledger",
        "",
        "| Arm | Scenario | Dimension | Passed samples | Observed | Required | Result |",
        "|---|---|---|---:|---:|---:|---|",
    ])
    for item in acceptance["criteria"]:
        lines.append(
            f"| `{item['arm']}` | `{item['scenario_id']}` | `{item['dimension']}` | "
            f"{item['passed_samples']} / {item['total_samples']} | {item['observed_pass_rate']:.0%} | "
            f"{item['required_pass_rate']:.0%} | {'PASS' if item['pass'] else '**FAIL**'} |"
        )
    return "\n".join(lines)


def _without_medians(value: Any) -> Any:
    """Remove median-only fields from report presentation, not source evidence."""
    if isinstance(value, dict):
        return {
            key: _without_medians(item)
            for key, item in value.items()
            if key != "p50" and "median" not in key.lower()
        }
    if isinstance(value, list):
        return [_without_medians(item) for item in value]
    return value


def render_human_sections(
    summary: dict[str, Any], *, context: dict[str, Any] | None = None
) -> str:
    """Render auditable prose and tables from an already validated summary."""
    context = context or {}
    paired = summary.get("statistics", {}).get("common_valid_paired")
    if not paired:
        verdict = "PASS" if summary.get("pass") is True else "FAIL"
        return (
            "## Executive summary\n\n"
            f"Overall suite verdict: **{verdict}**. Complete cells: "
            f"`{summary.get('observed_cells', 0)}` / `{summary.get('expected_cells', 0)}`.\n\n"
            + _acceptance_section(summary)
            + "\n\n## Audit appendix\n\n```json\n"
            + json.dumps(_without_medians(summary), ensure_ascii=False, sort_keys=True, indent=2)
            + "\n```"
        )
    treatment = paired["treatment_arm"]
    control = paired["control_arm"]
    overall = paired["overall"]
    reliability = summary["reliability"]
    timing = summary["timing"]
    cells = summary["cells"]
    failures = Counter(cell["arm"] for cell in cells if cell.get("scenario_outcome") == "failed")
    excluded = len(reliability.get("excluded_pairs", []))
    skill_name = context.get("skill_name", "selected skill")
    skill_version = context.get("skill_version", "version not declared")
    skill_url = context.get("skill_url")
    skill_display = f"[{skill_name}]({skill_url})" if skill_url else f"`{skill_name}`"
    agent = f"{context.get('agent_name', 'unknown')} {context.get('agent_version', 'unknown')}"
    agent_model = context.get("agent_model", "unknown model")
    runtime = f"{context.get('runtime_name', 'runtime')} {context.get('runtime_version', 'unknown')}"
    skill_hash = context.get("skill_sha256", "unknown")
    skill_source_commit = context.get("skill_source_commit", "unknown")
    runtime_hash = context.get("runtime_sha256", "unknown")
    worker_reasoning = context.get("worker_reasoning", "not recorded")
    judge_model = context.get("judge_model", "not recorded")
    judge_reasoning = context.get("judge_reasoning", "not recorded")
    agent_image_sha256 = context.get("agent_image_sha256", "not recorded")
    scenario_count = len(paired["per_scenario"])
    families = ", ".join(f"`{name}`" for name in sorted(paired["per_family"]))
    correctness_effects = paired["per_scenario"]
    correctness_improved = sum(
        group["score_delta_treatment_minus_control"]["task_correctness"]["mean"] > 0
        for group in correctness_effects.values()
    )
    latency_regressions = sum(
        group["metric_delta_treatment_minus_control"]["wall_time_seconds"]["mean"] > 0
        for group in correctness_effects.values()
    )
    skill_repo = str(skill_url).split("/tree/", 1)[0] if skill_url else None
    skill_commit_display = (
        f"[{skill_source_commit}]({skill_repo}/commit/{skill_source_commit})"
        if skill_repo else f"`{skill_source_commit}`"
    )

    lines = [
        "## Executive summary",
        "",
        "Evidence integrity: **valid and complete**. This means the evidence is structurally complete and "
        "auditable; it is not a benchmark PASS verdict. Deterministic scenario failures remain valid observed outcomes. "
        f"All `{summary['observed_cells']}` / `{summary['expected_cells']}` planned cells were observed. "
        f"The paired analysis contains `{reliability['common_valid_pairs']}` common-valid pairs; "
        f"`{excluded}` pairs were excluded.",
        "",
        f"The treatment arm `{treatment}` had `{failures[treatment]}` deterministic scenario failures, "
        f"compared with `{failures[control]}` in `{control}`. Correctness improved in `{correctness_improved}` of "
        f"`{scenario_count}` scenarios; `{latency_regressions}` scenarios had a mean latency regression.",
        "",
        "**Descriptive paired comparison; no superiority verdict is asserted.** Point estimates do not "
        "include confidence intervals and should not be read as claims of statistical significance.",
        "",
        f"All deltas below are **treatment minus control** (`{treatment} − {control}`). Positive score deltas are "
        "better; negative cost, token, and wall-time deltas are better.",
        "",
        "## Suite overview",
        "",
        f"The suite contains `{scenario_count}` scenario{'s' if scenario_count != 1 else ''}, "
        f"`{overall['n']}` paired samples, and two arms. Scenario families are {families}. `find` covers structured "
        "discovery, `retrieve` covers bounded context retrieval, and `find+retrieve` combines both operations.",
        "",
        "## Compared arms",
        "",
        "| Arm | Role | Skill guidance | Worker agent | Model | Reasoning | Runtime |",
        "|---|---|---|---|---|---|---|",
        f"| `{treatment}` | Treatment | {skill_display} v{skill_version} | `{agent}` | `{agent_model}` | {worker_reasoning} | `{runtime}` |",
        f"| `{control}` | Control | No skill guidance | `{agent}` | `{agent_model}` | {worker_reasoning} | `{runtime}` |",
        "",
        "### Judge configuration",
        "",
        f"- Judge model: `{judge_model}`",
        f"- Judge reasoning: `{judge_reasoning}`",
        "",
        "Judge scores evidence quality, resource efficiency, safety, scenario compliance, task correctness, and "
        "tool efficiency on a `0–5` scale. Deterministic verifier outcomes and telemetry remain authoritative; the "
        "judge cannot override a deterministic failure. Judge rationales and evidence references are schema-validated. "
        "See [evaluation metrics](../docs/evaluation-metrics.md).",
        "",
        f"The treatment skill comes from skill-repository commit {skill_commit_display}. Its Skill tree SHA-256 "
        f"is `{skill_hash}`; this immutable tree identity covers all selected skill files and is recorded for "
        "reproducibility. The IWE runtime binary SHA-256 is "
        f"`{runtime_hash}` and verifies the exact executable shared by both arms. Agent image SHA-256 "
        f"`{agent_image_sha256}` identifies the common worker toolchain image used by both arms.",
        "",
        _acceptance_section(summary),
        "",
        "## Overall paired comparison",
        "",
        _distribution_table(overall),
        "",
        "Means use the common-valid paired cohort. The paired Δ columns summarize within-pair differences, "
        "not differences between independently rounded arm means.",
        "",
        "## By scenario",
        "",
        _breakdown_table(paired["per_scenario"], treatment, control),
        "",
        "## By scenario family",
        "",
        _breakdown_table(paired["per_family"], treatment, control),
        "",
        "## Deterministic failure ledger",
        "",
        _failure_ledger(cells),
        "",
        "## Reliability and timing",
        "",
        f"- Common-valid pair rate: `{_fmt(reliability['common_valid_pair_rate'])}` "
        f"(`{reliability['common_valid_pairs']}` / `{reliability['planned_pairs']}`).",
        f"- Valid cells: `{sum(reliability['valid_cells_by_arm'].values())}` / "
        f"`{sum(reliability['planned_cells_by_arm'].values())}`.",
        f"- Invalid cells: `{sum(reliability['invalid_cells_by_arm'].values())}`.",
        f"- Summed common-valid cell time: `{_fmt(timing['common_valid_summed_cell_seconds'])}` seconds.",
        f"- Pipeline elapsed time: `{_fmt(timing['pipeline_elapsed_seconds'])}` seconds.",
        "",
        "Summed cell-seconds measure aggregate work across cells. Pipeline elapsed time measures end-to-end "
        "wall-clock duration under concurrency; they are intentionally not interchangeable.",
        "",
        "## Audit appendix",
        "",
        "<details>",
        "<summary>Complete machine-readable statistics and timing</summary>",
        "",
        "```json",
        json.dumps(
            _without_medians({"statistics": summary.get("statistics", {}), "timing": timing}),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        "```",
        "",
        "</details>",
    ]
    return "\n".join(lines)
