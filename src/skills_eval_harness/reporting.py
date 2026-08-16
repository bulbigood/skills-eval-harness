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


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _distribution_table(overall: dict[str, Any]) -> str:
    arms = overall["arm_distributions"]
    rows = ["| Metric | Skill mean | No-skill mean | Paired Δ | Δ median | n |",
            "|---|---:|---:|---:|---:|---:|"]
    for key, label in {**_SCORE_LABELS, **_METRIC_LABELS}.items():
        section = "scores" if key in _SCORE_LABELS else None
        treatment_value = arms["treatment"][section][key] if section else arms["treatment"][key]
        control_value = arms["control"][section][key] if section else arms["control"][key]
        deltas = (overall["score_delta_treatment_minus_control"] if section
                  else overall["metric_delta_treatment_minus_control"])[key]
        rows.append(
            f"| {label} | {_fmt(treatment_value['mean'])} | {_fmt(control_value['mean'])} | "
            f"{_fmt(deltas['mean'])} | {_fmt(deltas['p50'])} | {deltas['n']} |"
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
            f"{_fmt(scores['tool_efficiency']['mean'])} | {_fmt(metrics['wall_time_seconds']['mean'])} | "
            f"{_fmt(metrics['cost_usd']['mean'])} |"
        )
    return "\n".join(rows)


def _failure_ledger(cells: list[dict[str, Any]]) -> str:
    failures = [cell for cell in cells if cell.get("scenario_outcome") == "failed"]
    if not failures:
        return "No deterministic scenario failures were observed."
    rows = ["| Arm | Scenario | Sample | Deterministic failure | Judge summary |",
            "|---|---|---:|---|---|"]
    for cell in sorted(failures, key=lambda item: (item["arm"], item["scenario_id"], item["sample"])):
        reasons = "; ".join(cell.get("scenario_failures", []))
        rationale = cell.get("verdict", {}).get("rationale", "")
        rows.append(
            f"| `{_escape(cell['arm'])}` | `{_escape(cell['scenario_id'])}` | {cell['sample']} | "
            f"{_escape(reasons)} | {_escape(rationale)} |"
        )
    return "\n".join(rows)


def render_human_sections(summary: dict[str, Any]) -> str:
    """Render auditable prose and tables from an already validated summary."""
    paired = summary.get("statistics", {}).get("common_valid_paired")
    if not paired:
        verdict = "PASS" if summary.get("pass") is True else "FAIL"
        return (
            "## Executive summary\n\n"
            f"Overall suite verdict: **{verdict}**. Complete cells: "
            f"`{summary.get('observed_cells', 0)}` / `{summary.get('expected_cells', 0)}`.\n\n"
            "## Audit appendix\n\n```json\n"
            + json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n```"
        )
    treatment = paired["treatment_arm"]
    control = paired["control_arm"]
    overall = paired["overall"]
    reliability = summary["reliability"]
    timing = summary["timing"]
    cells = summary["cells"]
    failures = Counter(cell["arm"] for cell in cells if cell.get("scenario_outcome") == "failed")
    verdict = "PASS" if summary.get("pass") is True else "FAIL"
    valid = "valid" if summary.get("valid") is True else "invalid"
    excluded = len(reliability.get("excluded_pairs", []))

    lines = [
        "## Executive summary",
        "",
        f"This is a **{valid}** production evaluation with an overall suite verdict of **{verdict}**. "
        f"All `{summary['observed_cells']}` / `{summary['expected_cells']}` planned cells were observed. "
        f"The paired analysis contains `{reliability['common_valid_pairs']}` common-valid pairs; "
        f"`{excluded}` pairs were excluded.",
        "",
        f"The treatment arm `{treatment}` had `{failures[treatment]}` deterministic scenario failures, "
        f"compared with `{failures[control]}` in `{control}`. A FAIL verdict describes benchmark acceptance; "
        "it does not mean the evidence bundle is invalid.",
        "",
        "All deltas below are **treatment minus control** (`skill − no-skill`). Positive score deltas are "
        "better; negative cost, token, and wall-time deltas are better.",
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
            {"statistics": summary.get("statistics", {}), "timing": timing},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        "```",
        "",
        "</details>",
    ]
    return "\n".join(lines)
