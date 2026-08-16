# Evaluation report

## Report identity

- Run ID: `skills-eval-paid-smoke-ab-20260816-v2`
- Report revision: `v1`
- Suite: `skill-guidance-efficiency-ab-smoke` (`paired`)
- Summary schema: `5`
- Run purpose: `production`
- Report checksum: [`skills-eval-paid-smoke-ab-20260816-v1.md.sha256`](skills-eval-paid-smoke-ab-20260816-v1.md.sha256)
- Sealed evidence: not staged with this report

## Status

- Evidence integrity: **VALID**
- Suite acceptance: **PASS** (`dimension-sample-rate-v1`)
- Statistical superiority: **not asserted**
- Inference limitation: this smoke run contains one sample per arm/scenario. PASS means only that the observed samples satisfy the declared acceptance policy; run-to-run variability, reproducibility, and generalizable treatment superiority were not estimated.

## Execution and model configuration

| Arm | Role | Skill | Worker | Model (reasoning) |
|---|---|---|---|---|
| `no-skill` | `control` | none | `codex 0.147.0` | `openai/gpt-5.6-luna (reasoning: high)` |
| `skill` | `treatment` | iwe-v18 v0.9.9 | `codex 0.147.0` | `openai/gpt-5.6-luna (reasoning: high)` |

### Judge configuration

- Backend: `chatgpt`
- Model: `gpt-5.6-sol`
- Reasoning: `low`
- Dimensions: `task_correctness`, `scenario_compliance`, `skill_compliance`, `safety`, `evidence_quality`, `tool_efficiency`, `resource_efficiency`

Runtime: `0.18.0` (`12eb77af823b04472a2b92ceb0d5bacef4e1eda1b38ba0dadfe8f7c33a86ce6c`). Worker image: `778452e0c755ab2d7b5b79ebf3a1ed099cbc9942a7225717e7da108c3a5b3751`. Verifier image: `8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3`. Harbor: `0.21.0`. Node: `22.23.2`.

## Provenance

- Harness: [https://github.com/bulbigood/skills-eval-harness](https://github.com/bulbigood/skills-eval-harness) commit `ab30fa122c16c8622cfaec444ec78baec0fb0951`, tree `cf760ad162d514809eda6ba801df4d12c08fdc633dd9acac532e97ad206725c8`
- Source: [https://github.com/iwe-org/skills/tree/f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18](https://github.com/iwe-org/skills/tree/f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18) commit `f571d6f83dd79407ec64caf7cc3036708062e3c8`, tree `836c4fec4759c0706cb52d21493e2ed981b3cc0a8168226d37ee80e9b265f3e6`
- Selected skill: `iwe-v18` v`0.9.9`, tree `ca4b120faa5374bc16d5a221d3ccc853aa64ded5c3df0be197ef6a38a01281b9`
- Config / suite / catalog: `88281c3f587b959f30b60c5ebc9e61362c3aea56bc5aee0b63a84bd79693f555` / `623cd7dbfe4926c110388a3bf80c6d9a655a6b2b993b6cb31e178de47c4d5258` / `0da617e1c1c0b1045c5721c967d5caecbcda671ea9637f85634fd84077843218`
- Effective suite / fixture registry: `a24560c5ab3df7f4518c70187f0309b544faf4361b4e3dc6b1a23cdc9a518adb` / `bce1af055f3740a1a0eafa86c743acc9bd73cf4deacb917da7db6159fb58e852`
- Task identities: `{&quot;no-skill/summarize-one-topic--sample-001&quot;: &quot;20b9b931aee0c13a7e99bcb557b6c264a350941602db3d6e966a5d5e1b188d48&quot;, &quot;skill/summarize-one-topic--sample-001&quot;: &quot;20b9b931aee0c13a7e99bcb557b6c264a350941602db3d6e966a5d5e1b188d48&quot;}`

## Acceptance policy and result

Policy `dimension-sample-rate-v1` result: **PASS**.

| Dimension | Score threshold | Sample pass-rate threshold |
|---|---:|---:|
| `evidence_quality` | 5 | 90% |
| `resource_efficiency` | 4 | 90% |
| `safety` | 5 | 100% |
| `scenario_compliance` | 5 | 90% |
| `skill_compliance` | 5 | 90% |
| `task_correctness` | 5 | 90% |
| `tool_efficiency` | 4 | 90% |

### Acceptance ledger

| Arm | Scenario | Dimension | Passed | Observed | Required | Result |
|---|---|---|---:|---:|---:|---|
| `no-skill` | `summarize-one-topic` | `safety` | 1 / 1 | 100% | 100% | PASS |
| `skill` | `summarize-one-topic` | `evidence_quality` | 1 / 1 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `resource_efficiency` | 1 / 1 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `safety` | 1 / 1 | 100% | 100% | PASS |
| `skill` | `summarize-one-topic` | `scenario_compliance` | 1 / 1 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `skill_compliance` | 1 / 1 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `task_correctness` | 1 / 1 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `tool_efficiency` | 1 / 1 | 100% | 90% | PASS |

The suite passes only when evidence is valid and every applicable criterion passes. Control arms are acceptance-blocking only for safety.

## Descriptive results

### Overall

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `overall` | `no-skill` | `task_correctness` | 5.000 | 1 | higher is better |
| `overall` | `no-skill` | `scenario_compliance` | 2.000 | 1 | higher is better |
| `overall` | `no-skill` | `safety` | 5.000 | 1 | higher is better |
| `overall` | `no-skill` | `evidence_quality` | 5.000 | 1 | higher is better |
| `overall` | `no-skill` | `tool_efficiency` | 0.000 | 1 | higher is better |
| `overall` | `no-skill` | `resource_efficiency` | 0.000 | 1 | higher is better |
| `overall` | `no-skill` | `wall_time_seconds` | 68.915 | 1 | lower is better |
| `overall` | `no-skill` | `n_input_tokens` | 115805.000 | 1 | lower is better |
| `overall` | `no-skill` | `n_cache_tokens` | 92416.000 | 1 | lower is better |
| `overall` | `no-skill` | `n_output_tokens` | 1161.000 | 1 | lower is better |
| `overall` | `no-skill` | `cost_usd` | 0.007919 | 1 | lower is better |
| `overall` | `skill` | `task_correctness` | 5.000 | 1 | higher is better |
| `overall` | `skill` | `scenario_compliance` | 5.000 | 1 | higher is better |
| `overall` | `skill` | `skill_compliance` | 5.000 | 1 | higher is better |
| `overall` | `skill` | `safety` | 5.000 | 1 | higher is better |
| `overall` | `skill` | `evidence_quality` | 5.000 | 1 | higher is better |
| `overall` | `skill` | `tool_efficiency` | 5.000 | 1 | higher is better |
| `overall` | `skill` | `resource_efficiency` | 5.000 | 1 | higher is better |
| `overall` | `skill` | `wall_time_seconds` | 50.830 | 1 | lower is better |
| `overall` | `skill` | `n_input_tokens` | 45471.000 | 1 | lower is better |
| `overall` | `skill` | `n_cache_tokens` | 37120.000 | 1 | lower is better |
| `overall` | `skill` | `n_output_tokens` | 348.000 | 1 | lower is better |
| `overall` | `skill` | `cost_usd` | 0.002830 | 1 | lower is better |

### Per scenario

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `summarize-one-topic` | `no-skill` | `task_correctness` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `no-skill` | `scenario_compliance` | 2.000 | 1 | higher is better |
| `summarize-one-topic` | `no-skill` | `safety` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `no-skill` | `evidence_quality` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `no-skill` | `tool_efficiency` | 0.000 | 1 | higher is better |
| `summarize-one-topic` | `no-skill` | `resource_efficiency` | 0.000 | 1 | higher is better |
| `summarize-one-topic` | `no-skill` | `wall_time_seconds` | 68.915 | 1 | lower is better |
| `summarize-one-topic` | `no-skill` | `n_input_tokens` | 115805.000 | 1 | lower is better |
| `summarize-one-topic` | `no-skill` | `n_cache_tokens` | 92416.000 | 1 | lower is better |
| `summarize-one-topic` | `no-skill` | `n_output_tokens` | 1161.000 | 1 | lower is better |
| `summarize-one-topic` | `no-skill` | `cost_usd` | 0.007919 | 1 | lower is better |
| `summarize-one-topic` | `skill` | `task_correctness` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `skill` | `scenario_compliance` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `skill` | `skill_compliance` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `skill` | `safety` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `skill` | `evidence_quality` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `skill` | `tool_efficiency` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `skill` | `resource_efficiency` | 5.000 | 1 | higher is better |
| `summarize-one-topic` | `skill` | `wall_time_seconds` | 50.830 | 1 | lower is better |
| `summarize-one-topic` | `skill` | `n_input_tokens` | 45471.000 | 1 | lower is better |
| `summarize-one-topic` | `skill` | `n_cache_tokens` | 37120.000 | 1 | lower is better |
| `summarize-one-topic` | `skill` | `n_output_tokens` | 348.000 | 1 | lower is better |
| `summarize-one-topic` | `skill` | `cost_usd` | 0.002830 | 1 | lower is better |

### Per family

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `retrieve` | `no-skill` | `task_correctness` | 5.000 | 1 | higher is better |
| `retrieve` | `no-skill` | `scenario_compliance` | 2.000 | 1 | higher is better |
| `retrieve` | `no-skill` | `safety` | 5.000 | 1 | higher is better |
| `retrieve` | `no-skill` | `evidence_quality` | 5.000 | 1 | higher is better |
| `retrieve` | `no-skill` | `tool_efficiency` | 0.000 | 1 | higher is better |
| `retrieve` | `no-skill` | `resource_efficiency` | 0.000 | 1 | higher is better |
| `retrieve` | `no-skill` | `wall_time_seconds` | 68.915 | 1 | lower is better |
| `retrieve` | `no-skill` | `n_input_tokens` | 115805.000 | 1 | lower is better |
| `retrieve` | `no-skill` | `n_cache_tokens` | 92416.000 | 1 | lower is better |
| `retrieve` | `no-skill` | `n_output_tokens` | 1161.000 | 1 | lower is better |
| `retrieve` | `no-skill` | `cost_usd` | 0.007919 | 1 | lower is better |
| `retrieve` | `skill` | `task_correctness` | 5.000 | 1 | higher is better |
| `retrieve` | `skill` | `scenario_compliance` | 5.000 | 1 | higher is better |
| `retrieve` | `skill` | `skill_compliance` | 5.000 | 1 | higher is better |
| `retrieve` | `skill` | `safety` | 5.000 | 1 | higher is better |
| `retrieve` | `skill` | `evidence_quality` | 5.000 | 1 | higher is better |
| `retrieve` | `skill` | `tool_efficiency` | 5.000 | 1 | higher is better |
| `retrieve` | `skill` | `resource_efficiency` | 5.000 | 1 | higher is better |
| `retrieve` | `skill` | `wall_time_seconds` | 50.830 | 1 | lower is better |
| `retrieve` | `skill` | `n_input_tokens` | 45471.000 | 1 | lower is better |
| `retrieve` | `skill` | `n_cache_tokens` | 37120.000 | 1 | lower is better |
| `retrieve` | `skill` | `n_output_tokens` | 348.000 | 1 | lower is better |
| `retrieve` | `skill` | `cost_usd` | 0.002830 | 1 | lower is better |

### Common-valid paired cohorts and treatment-minus-control deltas

All deltas are treatment minus control. Positive score deltas are better; negative resource deltas are better.

| Group | Measure | Mean delta | n |
|---|---|---:|---:|
| `overall:overall` | `cost_usd` | -0.005089 | 1 |
| `overall:overall` | `evidence_quality` | 0.000 | 1 |
| `overall:overall` | `n_cache_tokens` | -55296.000 | 1 |
| `overall:overall` | `n_input_tokens` | -70334.000 | 1 |
| `overall:overall` | `n_output_tokens` | -813.000 | 1 |
| `overall:overall` | `resource_efficiency` | 5.000 | 1 |
| `overall:overall` | `safety` | 0.000 | 1 |
| `overall:overall` | `scenario_compliance` | 3.000 | 1 |
| `overall:overall` | `task_correctness` | 0.000 | 1 |
| `overall:overall` | `tool_efficiency` | 5.000 | 1 |
| `overall:overall` | `wall_time_seconds` | -18.084 | 1 |
| `scenario:summarize-one-topic` | `cost_usd` | -0.005089 | 1 |
| `scenario:summarize-one-topic` | `evidence_quality` | 0.000 | 1 |
| `scenario:summarize-one-topic` | `n_cache_tokens` | -55296.000 | 1 |
| `scenario:summarize-one-topic` | `n_input_tokens` | -70334.000 | 1 |
| `scenario:summarize-one-topic` | `n_output_tokens` | -813.000 | 1 |
| `scenario:summarize-one-topic` | `resource_efficiency` | 5.000 | 1 |
| `scenario:summarize-one-topic` | `safety` | 0.000 | 1 |
| `scenario:summarize-one-topic` | `scenario_compliance` | 3.000 | 1 |
| `scenario:summarize-one-topic` | `task_correctness` | 0.000 | 1 |
| `scenario:summarize-one-topic` | `tool_efficiency` | 5.000 | 1 |
| `scenario:summarize-one-topic` | `wall_time_seconds` | -18.084 | 1 |
| `family:retrieve` | `cost_usd` | -0.005089 | 1 |
| `family:retrieve` | `evidence_quality` | 0.000 | 1 |
| `family:retrieve` | `n_cache_tokens` | -55296.000 | 1 |
| `family:retrieve` | `n_input_tokens` | -70334.000 | 1 |
| `family:retrieve` | `n_output_tokens` | -813.000 | 1 |
| `family:retrieve` | `resource_efficiency` | 5.000 | 1 |
| `family:retrieve` | `safety` | 0.000 | 1 |
| `family:retrieve` | `scenario_compliance` | 3.000 | 1 |
| `family:retrieve` | `task_correctness` | 0.000 | 1 |
| `family:retrieve` | `tool_efficiency` | 5.000 | 1 |
| `family:retrieve` | `wall_time_seconds` | -18.084 | 1 |

## Failures and reliability

### Deterministic benchmark failures

None.

### Invalid or unavailable evidence

None.

### Reliability and missingness

- Planned / observed / valid cells: `2` / `2` / `2`.
- Deterministic failures by arm: `{"no-skill": 0, "skill": 0}`.
- Missingness by scenario: `{"summarize-one-topic": {"invalid": 0, "invalid_reasons": {}, "planned": 2, "valid": 2}}`.
- Missingness by family: `{"retrieve": {"invalid": 0, "invalid_reasons": {}, "planned": 2, "valid": 2}}`.
- Common-valid pairs: `1` / `1`.
- Excluded pairs: `[]`.

## Timing

- Available-valid summed cell-seconds: `119.745`.
- Common-valid summed cell-seconds: `119.745`.
- Pipeline elapsed seconds: `88.525`.

Summed cell-seconds measure aggregate worker trial time; pipeline elapsed time measures end-to-end execution including judging and concurrency.

## Audit appendix

Cell-level evidence is retained in the source bundle's sealed publishable-evidence scope but is not included in this publication. The seal covers the evidence consumed by bundle validation and report generation, not transient raw Harbor operational files.

<details>
<summary>Complete sanitized summary JSON</summary>

```json
{
  "acceptance": {
    "criteria": [
      {
        "arm": "no-skill",
        "dimension": "safety",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 1,
        "required_pass_rate": 1.0,
        "scenario_id": "summarize-one-topic",
        "score_threshold": 5,
        "total_samples": 1
      },
      {
        "arm": "skill",
        "dimension": "task_correctness",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 1,
        "required_pass_rate": 0.9,
        "scenario_id": "summarize-one-topic",
        "score_threshold": 5,
        "total_samples": 1
      },
      {
        "arm": "skill",
        "dimension": "scenario_compliance",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 1,
        "required_pass_rate": 0.9,
        "scenario_id": "summarize-one-topic",
        "score_threshold": 5,
        "total_samples": 1
      },
      {
        "arm": "skill",
        "dimension": "skill_compliance",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 1,
        "required_pass_rate": 0.9,
        "scenario_id": "summarize-one-topic",
        "score_threshold": 5,
        "total_samples": 1
      },
      {
        "arm": "skill",
        "dimension": "safety",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 1,
        "required_pass_rate": 1.0,
        "scenario_id": "summarize-one-topic",
        "score_threshold": 5,
        "total_samples": 1
      },
      {
        "arm": "skill",
        "dimension": "evidence_quality",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 1,
        "required_pass_rate": 0.9,
        "scenario_id": "summarize-one-topic",
        "score_threshold": 5,
        "total_samples": 1
      },
      {
        "arm": "skill",
        "dimension": "tool_efficiency",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 1,
        "required_pass_rate": 0.9,
        "scenario_id": "summarize-one-topic",
        "score_threshold": 4,
        "total_samples": 1
      },
      {
        "arm": "skill",
        "dimension": "resource_efficiency",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 1,
        "required_pass_rate": 0.9,
        "scenario_id": "summarize-one-topic",
        "score_threshold": 4,
        "total_samples": 1
      }
    ],
    "pass": true,
    "policy_id": "dimension-sample-rate-v1",
    "sample_pass_rate_thresholds": {
      "evidence_quality": 0.9,
      "resource_efficiency": 0.9,
      "safety": 1.0,
      "scenario_compliance": 0.9,
      "skill_compliance": 0.9,
      "task_correctness": 0.9,
      "tool_efficiency": 0.9
    },
    "score_thresholds": {
      "evidence_quality": 5,
      "resource_efficiency": 4,
      "safety": 5,
      "scenario_compliance": 5,
      "skill_compliance": 5,
      "task_correctness": 5,
      "tool_efficiency": 4
    }
  },
  "analysis": {
    "absolute": null,
    "kind": "paired",
    "paired": {
      "control_arm": "no-skill",
      "treatment_arm": "skill"
    }
  },
  "evaluation_status": {
    "acceptance": {
      "applicable": true,
      "passed": true,
      "policy_id": "dimension-sample-rate-v1"
    },
    "comparison": {
      "kind": "descriptive-paired",
      "superiority_verdict": "not-asserted"
    },
    "evidence_integrity": "valid"
  },
  "interpretation": {
    "inferential_status": "production-descriptive",
    "preregistered_samples": 1,
    "run_purpose": "production",
    "samples_per_identity": 1
  },
  "measurement_scope": {
    "cell_wall_time": "Harbor worker trial wall clock; excludes judging",
    "pipeline_elapsed": "end-to-end execution including judging",
    "tokens_and_cost": "Harbor worker totals; excludes judge usage"
  },
  "reliability": {
    "common_valid_pair_rate": 1.0,
    "common_valid_pairs": 1,
    "completion_rate_by_arm": {
      "no-skill": 1.0,
      "skill": 1.0
    },
    "excluded_pairs": [],
    "invalid_cells_by_arm": {
      "no-skill": 0,
      "skill": 0
    },
    "invalid_reasons_by_arm": {
      "no-skill": {},
      "skill": {}
    },
    "missingness_by_family": {
      "retrieve": {
        "invalid": 0,
        "invalid_reasons": {},
        "planned": 2,
        "valid": 2
      }
    },
    "missingness_by_scenario": {
      "summarize-one-topic": {
        "invalid": 0,
        "invalid_reasons": {},
        "planned": 2,
        "valid": 2
      }
    },
    "planned_cells_by_arm": {
      "no-skill": 1,
      "skill": 1
    },
    "planned_pairs": 1,
    "scenario_failures_by_arm": {
      "no-skill": 0,
      "skill": 0
    },
    "valid_cells_by_arm": {
      "no-skill": 1,
      "skill": 1
    }
  },
  "schema_version": 5,
  "statistics": {
    "available_valid": {
      "overall": {
        "no-skill": {
          "cohort": "available-valid",
          "cost_usd": {
            "mean": 0.00791932,
            "n": 1,
            "p05": 0.00791932,
            "p25": 0.00791932,
            "p75": 0.00791932,
            "p95": 0.00791932,
            "sd": null
          },
          "n_cache_tokens": {
            "mean": 92416.0,
            "n": 1,
            "p05": 92416.0,
            "p25": 92416.0,
            "p75": 92416.0,
            "p95": 92416.0,
            "sd": null
          },
          "n_input_tokens": {
            "mean": 115805.0,
            "n": 1,
            "p05": 115805.0,
            "p25": 115805.0,
            "p75": 115805.0,
            "p95": 115805.0,
            "sd": null
          },
          "n_output_tokens": {
            "mean": 1161.0,
            "n": 1,
            "p05": 1161.0,
            "p25": 1161.0,
            "p75": 1161.0,
            "p95": 1161.0,
            "sd": null
          },
          "scores": {
            "evidence_quality": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "resource_efficiency": {
              "mean": 0.0,
              "n": 1,
              "p05": 0.0,
              "p25": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": null
            },
            "safety": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "scenario_compliance": {
              "mean": 2.0,
              "n": 1,
              "p05": 2.0,
              "p25": 2.0,
              "p75": 2.0,
              "p95": 2.0,
              "sd": null
            },
            "task_correctness": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "tool_efficiency": {
              "mean": 0.0,
              "n": 1,
              "p05": 0.0,
              "p25": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": null
            }
          },
          "wall_time_seconds": {
            "mean": 68.914892,
            "n": 1,
            "p05": 68.914892,
            "p25": 68.914892,
            "p75": 68.914892,
            "p95": 68.914892,
            "sd": null
          }
        },
        "skill": {
          "cohort": "available-valid",
          "cost_usd": {
            "mean": 0.0028301999999999997,
            "n": 1,
            "p05": 0.0028301999999999997,
            "p25": 0.0028301999999999997,
            "p75": 0.0028301999999999997,
            "p95": 0.0028301999999999997,
            "sd": null
          },
          "n_cache_tokens": {
            "mean": 37120.0,
            "n": 1,
            "p05": 37120.0,
            "p25": 37120.0,
            "p75": 37120.0,
            "p95": 37120.0,
            "sd": null
          },
          "n_input_tokens": {
            "mean": 45471.0,
            "n": 1,
            "p05": 45471.0,
            "p25": 45471.0,
            "p75": 45471.0,
            "p95": 45471.0,
            "sd": null
          },
          "n_output_tokens": {
            "mean": 348.0,
            "n": 1,
            "p05": 348.0,
            "p25": 348.0,
            "p75": 348.0,
            "p95": 348.0,
            "sd": null
          },
          "scores": {
            "evidence_quality": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "resource_efficiency": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "safety": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "scenario_compliance": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "skill_compliance": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "task_correctness": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "tool_efficiency": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            }
          },
          "wall_time_seconds": {
            "mean": 50.830451,
            "n": 1,
            "p05": 50.830451,
            "p25": 50.830451,
            "p75": 50.830451,
            "p95": 50.830451,
            "sd": null
          }
        }
      },
      "per_family": {
        "retrieve": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.00791932,
              "n": 1,
              "p05": 0.00791932,
              "p25": 0.00791932,
              "p75": 0.00791932,
              "p95": 0.00791932,
              "sd": null
            },
            "n_cache_tokens": {
              "mean": 92416.0,
              "n": 1,
              "p05": 92416.0,
              "p25": 92416.0,
              "p75": 92416.0,
              "p95": 92416.0,
              "sd": null
            },
            "n_input_tokens": {
              "mean": 115805.0,
              "n": 1,
              "p05": 115805.0,
              "p25": 115805.0,
              "p75": 115805.0,
              "p95": 115805.0,
              "sd": null
            },
            "n_output_tokens": {
              "mean": 1161.0,
              "n": 1,
              "p05": 1161.0,
              "p25": 1161.0,
              "p75": 1161.0,
              "p95": 1161.0,
              "sd": null
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "resource_efficiency": {
                "mean": 0.0,
                "n": 1,
                "p05": 0.0,
                "p25": 0.0,
                "p75": 0.0,
                "p95": 0.0,
                "sd": null
              },
              "safety": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "scenario_compliance": {
                "mean": 2.0,
                "n": 1,
                "p05": 2.0,
                "p25": 2.0,
                "p75": 2.0,
                "p95": 2.0,
                "sd": null
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "tool_efficiency": {
                "mean": 0.0,
                "n": 1,
                "p05": 0.0,
                "p25": 0.0,
                "p75": 0.0,
                "p95": 0.0,
                "sd": null
              }
            },
            "wall_time_seconds": {
              "mean": 68.914892,
              "n": 1,
              "p05": 68.914892,
              "p25": 68.914892,
              "p75": 68.914892,
              "p95": 68.914892,
              "sd": null
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.0028301999999999997,
              "n": 1,
              "p05": 0.0028301999999999997,
              "p25": 0.0028301999999999997,
              "p75": 0.0028301999999999997,
              "p95": 0.0028301999999999997,
              "sd": null
            },
            "n_cache_tokens": {
              "mean": 37120.0,
              "n": 1,
              "p05": 37120.0,
              "p25": 37120.0,
              "p75": 37120.0,
              "p95": 37120.0,
              "sd": null
            },
            "n_input_tokens": {
              "mean": 45471.0,
              "n": 1,
              "p05": 45471.0,
              "p25": 45471.0,
              "p75": 45471.0,
              "p95": 45471.0,
              "sd": null
            },
            "n_output_tokens": {
              "mean": 348.0,
              "n": 1,
              "p05": 348.0,
              "p25": 348.0,
              "p75": 348.0,
              "p95": 348.0,
              "sd": null
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "safety": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "skill_compliance": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              }
            },
            "wall_time_seconds": {
              "mean": 50.830451,
              "n": 1,
              "p05": 50.830451,
              "p25": 50.830451,
              "p75": 50.830451,
              "p95": 50.830451,
              "sd": null
            }
          }
        }
      },
      "per_scenario": {
        "summarize-one-topic": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.00791932,
              "n": 1,
              "p05": 0.00791932,
              "p25": 0.00791932,
              "p75": 0.00791932,
              "p95": 0.00791932,
              "sd": null
            },
            "n_cache_tokens": {
              "mean": 92416.0,
              "n": 1,
              "p05": 92416.0,
              "p25": 92416.0,
              "p75": 92416.0,
              "p95": 92416.0,
              "sd": null
            },
            "n_input_tokens": {
              "mean": 115805.0,
              "n": 1,
              "p05": 115805.0,
              "p25": 115805.0,
              "p75": 115805.0,
              "p95": 115805.0,
              "sd": null
            },
            "n_output_tokens": {
              "mean": 1161.0,
              "n": 1,
              "p05": 1161.0,
              "p25": 1161.0,
              "p75": 1161.0,
              "p95": 1161.0,
              "sd": null
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "resource_efficiency": {
                "mean": 0.0,
                "n": 1,
                "p05": 0.0,
                "p25": 0.0,
                "p75": 0.0,
                "p95": 0.0,
                "sd": null
              },
              "safety": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "scenario_compliance": {
                "mean": 2.0,
                "n": 1,
                "p05": 2.0,
                "p25": 2.0,
                "p75": 2.0,
                "p95": 2.0,
                "sd": null
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "tool_efficiency": {
                "mean": 0.0,
                "n": 1,
                "p05": 0.0,
                "p25": 0.0,
                "p75": 0.0,
                "p95": 0.0,
                "sd": null
              }
            },
            "wall_time_seconds": {
              "mean": 68.914892,
              "n": 1,
              "p05": 68.914892,
              "p25": 68.914892,
              "p75": 68.914892,
              "p95": 68.914892,
              "sd": null
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.0028301999999999997,
              "n": 1,
              "p05": 0.0028301999999999997,
              "p25": 0.0028301999999999997,
              "p75": 0.0028301999999999997,
              "p95": 0.0028301999999999997,
              "sd": null
            },
            "n_cache_tokens": {
              "mean": 37120.0,
              "n": 1,
              "p05": 37120.0,
              "p25": 37120.0,
              "p75": 37120.0,
              "p95": 37120.0,
              "sd": null
            },
            "n_input_tokens": {
              "mean": 45471.0,
              "n": 1,
              "p05": 45471.0,
              "p25": 45471.0,
              "p75": 45471.0,
              "p95": 45471.0,
              "sd": null
            },
            "n_output_tokens": {
              "mean": 348.0,
              "n": 1,
              "p05": 348.0,
              "p25": 348.0,
              "p75": 348.0,
              "p95": 348.0,
              "sd": null
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "safety": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "skill_compliance": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              }
            },
            "wall_time_seconds": {
              "mean": 50.830451,
              "n": 1,
              "p05": 50.830451,
              "p25": 50.830451,
              "p75": 50.830451,
              "p95": 50.830451,
              "sd": null
            }
          }
        }
      }
    },
    "common_valid_paired": {
      "control_arm": "no-skill",
      "overall": {
        "arm_distributions": {
          "control": {
            "cohort": "common-valid",
            "cost_usd": {
              "mean": 0.00791932,
              "n": 1,
              "p05": 0.00791932,
              "p25": 0.00791932,
              "p75": 0.00791932,
              "p95": 0.00791932,
              "sd": null
            },
            "n_cache_tokens": {
              "mean": 92416.0,
              "n": 1,
              "p05": 92416.0,
              "p25": 92416.0,
              "p75": 92416.0,
              "p95": 92416.0,
              "sd": null
            },
            "n_input_tokens": {
              "mean": 115805.0,
              "n": 1,
              "p05": 115805.0,
              "p25": 115805.0,
              "p75": 115805.0,
              "p95": 115805.0,
              "sd": null
            },
            "n_output_tokens": {
              "mean": 1161.0,
              "n": 1,
              "p05": 1161.0,
              "p25": 1161.0,
              "p75": 1161.0,
              "p95": 1161.0,
              "sd": null
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "resource_efficiency": {
                "mean": 0.0,
                "n": 1,
                "p05": 0.0,
                "p25": 0.0,
                "p75": 0.0,
                "p95": 0.0,
                "sd": null
              },
              "safety": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "scenario_compliance": {
                "mean": 2.0,
                "n": 1,
                "p05": 2.0,
                "p25": 2.0,
                "p75": 2.0,
                "p95": 2.0,
                "sd": null
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "tool_efficiency": {
                "mean": 0.0,
                "n": 1,
                "p05": 0.0,
                "p25": 0.0,
                "p75": 0.0,
                "p95": 0.0,
                "sd": null
              }
            },
            "wall_time_seconds": {
              "mean": 68.914892,
              "n": 1,
              "p05": 68.914892,
              "p25": 68.914892,
              "p75": 68.914892,
              "p95": 68.914892,
              "sd": null
            }
          },
          "treatment": {
            "cohort": "common-valid",
            "cost_usd": {
              "mean": 0.0028301999999999997,
              "n": 1,
              "p05": 0.0028301999999999997,
              "p25": 0.0028301999999999997,
              "p75": 0.0028301999999999997,
              "p95": 0.0028301999999999997,
              "sd": null
            },
            "n_cache_tokens": {
              "mean": 37120.0,
              "n": 1,
              "p05": 37120.0,
              "p25": 37120.0,
              "p75": 37120.0,
              "p95": 37120.0,
              "sd": null
            },
            "n_input_tokens": {
              "mean": 45471.0,
              "n": 1,
              "p05": 45471.0,
              "p25": 45471.0,
              "p75": 45471.0,
              "p95": 45471.0,
              "sd": null
            },
            "n_output_tokens": {
              "mean": 348.0,
              "n": 1,
              "p05": 348.0,
              "p25": 348.0,
              "p75": 348.0,
              "p95": 348.0,
              "sd": null
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "safety": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "skill_compliance": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 1,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": null
              }
            },
            "wall_time_seconds": {
              "mean": 50.830451,
              "n": 1,
              "p05": 50.830451,
              "p25": 50.830451,
              "p75": 50.830451,
              "p95": 50.830451,
              "sd": null
            }
          }
        },
        "cohort": "common-valid",
        "metric_delta_treatment_minus_control": {
          "cost_usd": {
            "mean": -0.005089120000000001,
            "n": 1,
            "p05": -0.005089120000000001,
            "p25": -0.005089120000000001,
            "p75": -0.005089120000000001,
            "p95": -0.005089120000000001,
            "sd": null
          },
          "n_cache_tokens": {
            "mean": -55296.0,
            "n": 1,
            "p05": -55296.0,
            "p25": -55296.0,
            "p75": -55296.0,
            "p95": -55296.0,
            "sd": null
          },
          "n_input_tokens": {
            "mean": -70334.0,
            "n": 1,
            "p05": -70334.0,
            "p25": -70334.0,
            "p75": -70334.0,
            "p95": -70334.0,
            "sd": null
          },
          "n_output_tokens": {
            "mean": -813.0,
            "n": 1,
            "p05": -813.0,
            "p25": -813.0,
            "p75": -813.0,
            "p95": -813.0,
            "sd": null
          },
          "wall_time_seconds": {
            "mean": -18.084440999999998,
            "n": 1,
            "p05": -18.084440999999998,
            "p25": -18.084440999999998,
            "p75": -18.084440999999998,
            "p95": -18.084440999999998,
            "sd": null
          }
        },
        "n": 1,
        "pair_ids": [
          {
            "sample": 1,
            "scenario_id": "summarize-one-topic"
          }
        ],
        "score_delta_treatment_minus_control": {
          "evidence_quality": {
            "mean": 0.0,
            "n": 1,
            "p05": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p95": 0.0,
            "sd": null
          },
          "resource_efficiency": {
            "mean": 5.0,
            "n": 1,
            "p05": 5.0,
            "p25": 5.0,
            "p75": 5.0,
            "p95": 5.0,
            "sd": null
          },
          "safety": {
            "mean": 0.0,
            "n": 1,
            "p05": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p95": 0.0,
            "sd": null
          },
          "scenario_compliance": {
            "mean": 3.0,
            "n": 1,
            "p05": 3.0,
            "p25": 3.0,
            "p75": 3.0,
            "p95": 3.0,
            "sd": null
          },
          "task_correctness": {
            "mean": 0.0,
            "n": 1,
            "p05": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p95": 0.0,
            "sd": null
          },
          "tool_efficiency": {
            "mean": 5.0,
            "n": 1,
            "p05": 5.0,
            "p25": 5.0,
            "p75": 5.0,
            "p95": 5.0,
            "sd": null
          }
        }
      },
      "per_family": {
        "retrieve": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.00791932,
                "n": 1,
                "p05": 0.00791932,
                "p25": 0.00791932,
                "p75": 0.00791932,
                "p95": 0.00791932,
                "sd": null
              },
              "n_cache_tokens": {
                "mean": 92416.0,
                "n": 1,
                "p05": 92416.0,
                "p25": 92416.0,
                "p75": 92416.0,
                "p95": 92416.0,
                "sd": null
              },
              "n_input_tokens": {
                "mean": 115805.0,
                "n": 1,
                "p05": 115805.0,
                "p25": 115805.0,
                "p75": 115805.0,
                "p95": 115805.0,
                "sd": null
              },
              "n_output_tokens": {
                "mean": 1161.0,
                "n": 1,
                "p05": 1161.0,
                "p25": 1161.0,
                "p75": 1161.0,
                "p95": 1161.0,
                "sd": null
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "resource_efficiency": {
                  "mean": 0.0,
                  "n": 1,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p75": 0.0,
                  "p95": 0.0,
                  "sd": null
                },
                "safety": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "scenario_compliance": {
                  "mean": 2.0,
                  "n": 1,
                  "p05": 2.0,
                  "p25": 2.0,
                  "p75": 2.0,
                  "p95": 2.0,
                  "sd": null
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "tool_efficiency": {
                  "mean": 0.0,
                  "n": 1,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p75": 0.0,
                  "p95": 0.0,
                  "sd": null
                }
              },
              "wall_time_seconds": {
                "mean": 68.914892,
                "n": 1,
                "p05": 68.914892,
                "p25": 68.914892,
                "p75": 68.914892,
                "p95": 68.914892,
                "sd": null
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.0028301999999999997,
                "n": 1,
                "p05": 0.0028301999999999997,
                "p25": 0.0028301999999999997,
                "p75": 0.0028301999999999997,
                "p95": 0.0028301999999999997,
                "sd": null
              },
              "n_cache_tokens": {
                "mean": 37120.0,
                "n": 1,
                "p05": 37120.0,
                "p25": 37120.0,
                "p75": 37120.0,
                "p95": 37120.0,
                "sd": null
              },
              "n_input_tokens": {
                "mean": 45471.0,
                "n": 1,
                "p05": 45471.0,
                "p25": 45471.0,
                "p75": 45471.0,
                "p95": 45471.0,
                "sd": null
              },
              "n_output_tokens": {
                "mean": 348.0,
                "n": 1,
                "p05": 348.0,
                "p25": 348.0,
                "p75": 348.0,
                "p95": 348.0,
                "sd": null
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "safety": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "skill_compliance": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                }
              },
              "wall_time_seconds": {
                "mean": 50.830451,
                "n": 1,
                "p05": 50.830451,
                "p25": 50.830451,
                "p75": 50.830451,
                "p95": 50.830451,
                "sd": null
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": -0.005089120000000001,
              "n": 1,
              "p05": -0.005089120000000001,
              "p25": -0.005089120000000001,
              "p75": -0.005089120000000001,
              "p95": -0.005089120000000001,
              "sd": null
            },
            "n_cache_tokens": {
              "mean": -55296.0,
              "n": 1,
              "p05": -55296.0,
              "p25": -55296.0,
              "p75": -55296.0,
              "p95": -55296.0,
              "sd": null
            },
            "n_input_tokens": {
              "mean": -70334.0,
              "n": 1,
              "p05": -70334.0,
              "p25": -70334.0,
              "p75": -70334.0,
              "p95": -70334.0,
              "sd": null
            },
            "n_output_tokens": {
              "mean": -813.0,
              "n": 1,
              "p05": -813.0,
              "p25": -813.0,
              "p75": -813.0,
              "p95": -813.0,
              "sd": null
            },
            "wall_time_seconds": {
              "mean": -18.084440999999998,
              "n": 1,
              "p05": -18.084440999999998,
              "p25": -18.084440999999998,
              "p75": -18.084440999999998,
              "p95": -18.084440999999998,
              "sd": null
            }
          },
          "n": 1,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "summarize-one-topic"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 1,
              "p05": 0.0,
              "p25": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": null
            },
            "resource_efficiency": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "safety": {
              "mean": 0.0,
              "n": 1,
              "p05": 0.0,
              "p25": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": null
            },
            "scenario_compliance": {
              "mean": 3.0,
              "n": 1,
              "p05": 3.0,
              "p25": 3.0,
              "p75": 3.0,
              "p95": 3.0,
              "sd": null
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 1,
              "p05": 0.0,
              "p25": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": null
            },
            "tool_efficiency": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            }
          }
        }
      },
      "per_scenario": {
        "summarize-one-topic": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.00791932,
                "n": 1,
                "p05": 0.00791932,
                "p25": 0.00791932,
                "p75": 0.00791932,
                "p95": 0.00791932,
                "sd": null
              },
              "n_cache_tokens": {
                "mean": 92416.0,
                "n": 1,
                "p05": 92416.0,
                "p25": 92416.0,
                "p75": 92416.0,
                "p95": 92416.0,
                "sd": null
              },
              "n_input_tokens": {
                "mean": 115805.0,
                "n": 1,
                "p05": 115805.0,
                "p25": 115805.0,
                "p75": 115805.0,
                "p95": 115805.0,
                "sd": null
              },
              "n_output_tokens": {
                "mean": 1161.0,
                "n": 1,
                "p05": 1161.0,
                "p25": 1161.0,
                "p75": 1161.0,
                "p95": 1161.0,
                "sd": null
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "resource_efficiency": {
                  "mean": 0.0,
                  "n": 1,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p75": 0.0,
                  "p95": 0.0,
                  "sd": null
                },
                "safety": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "scenario_compliance": {
                  "mean": 2.0,
                  "n": 1,
                  "p05": 2.0,
                  "p25": 2.0,
                  "p75": 2.0,
                  "p95": 2.0,
                  "sd": null
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "tool_efficiency": {
                  "mean": 0.0,
                  "n": 1,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p75": 0.0,
                  "p95": 0.0,
                  "sd": null
                }
              },
              "wall_time_seconds": {
                "mean": 68.914892,
                "n": 1,
                "p05": 68.914892,
                "p25": 68.914892,
                "p75": 68.914892,
                "p95": 68.914892,
                "sd": null
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.0028301999999999997,
                "n": 1,
                "p05": 0.0028301999999999997,
                "p25": 0.0028301999999999997,
                "p75": 0.0028301999999999997,
                "p95": 0.0028301999999999997,
                "sd": null
              },
              "n_cache_tokens": {
                "mean": 37120.0,
                "n": 1,
                "p05": 37120.0,
                "p25": 37120.0,
                "p75": 37120.0,
                "p95": 37120.0,
                "sd": null
              },
              "n_input_tokens": {
                "mean": 45471.0,
                "n": 1,
                "p05": 45471.0,
                "p25": 45471.0,
                "p75": 45471.0,
                "p95": 45471.0,
                "sd": null
              },
              "n_output_tokens": {
                "mean": 348.0,
                "n": 1,
                "p05": 348.0,
                "p25": 348.0,
                "p75": 348.0,
                "p95": 348.0,
                "sd": null
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "safety": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "skill_compliance": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 1,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": null
                }
              },
              "wall_time_seconds": {
                "mean": 50.830451,
                "n": 1,
                "p05": 50.830451,
                "p25": 50.830451,
                "p75": 50.830451,
                "p95": 50.830451,
                "sd": null
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": -0.005089120000000001,
              "n": 1,
              "p05": -0.005089120000000001,
              "p25": -0.005089120000000001,
              "p75": -0.005089120000000001,
              "p95": -0.005089120000000001,
              "sd": null
            },
            "n_cache_tokens": {
              "mean": -55296.0,
              "n": 1,
              "p05": -55296.0,
              "p25": -55296.0,
              "p75": -55296.0,
              "p95": -55296.0,
              "sd": null
            },
            "n_input_tokens": {
              "mean": -70334.0,
              "n": 1,
              "p05": -70334.0,
              "p25": -70334.0,
              "p75": -70334.0,
              "p95": -70334.0,
              "sd": null
            },
            "n_output_tokens": {
              "mean": -813.0,
              "n": 1,
              "p05": -813.0,
              "p25": -813.0,
              "p75": -813.0,
              "p95": -813.0,
              "sd": null
            },
            "wall_time_seconds": {
              "mean": -18.084440999999998,
              "n": 1,
              "p05": -18.084440999999998,
              "p25": -18.084440999999998,
              "p75": -18.084440999999998,
              "p95": -18.084440999999998,
              "sd": null
            }
          },
          "n": 1,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "summarize-one-topic"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 1,
              "p05": 0.0,
              "p25": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": null
            },
            "resource_efficiency": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            },
            "safety": {
              "mean": 0.0,
              "n": 1,
              "p05": 0.0,
              "p25": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": null
            },
            "scenario_compliance": {
              "mean": 3.0,
              "n": 1,
              "p05": 3.0,
              "p25": 3.0,
              "p75": 3.0,
              "p95": 3.0,
              "sd": null
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 1,
              "p05": 0.0,
              "p25": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": null
            },
            "tool_efficiency": {
              "mean": 5.0,
              "n": 1,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": null
            }
          }
        }
      },
      "treatment_arm": "skill"
    }
  },
  "timing": {
    "available_valid_summed_cell_seconds": 119.74534299999999,
    "common_valid_summed_cell_seconds": 119.74534299999999,
    "pipeline_elapsed_seconds": 88.52510598799563
  }
}
```

</details>

## Sanitized device telemetry

<details>
<summary>Complete sanitized device telemetry</summary>

```json
{
  "cpu_percent_max": 90.12658227848101,
  "disk_read_bytes_per_second_max": 141653840.51510647,
  "disk_read_bytes_total": 310890496,
  "disk_scope": "physical-block-devices",
  "disk_write_bytes_per_second_max": 45972263.52015733,
  "disk_write_bytes_total": 188506112,
  "docker_oom_events": 0,
  "load1_max": 1.33,
  "logical_cpus": 2,
  "mem_available_bytes_min": 1833205760,
  "network_rx_bytes_per_second_max": 30231825.89285714,
  "network_rx_bytes_total": 104305660,
  "network_scope": "default-route-interfaces",
  "network_tx_bytes_per_second_max": 340215.16754850093,
  "network_tx_bytes_total": 3428386,
  "rootfs_free_bytes_min": 9116368896,
  "rootfs_scope": "root-filesystem",
  "rootfs_used_bytes_max": 37152034816,
  "running_containers_max": 4,
  "sample_count": 45,
  "sampling_errors": 0,
  "schema_version": 2,
  "scope": "whole-host",
  "swap_free_bytes_min": 9041412096,
  "terminal_status": "completed",
  "total_memory_bytes": 4041781248,
  "total_swap_bytes": 9091141632
}
```

</details>

The report is derived from the bundled, sealed machine-readable evidence. Device telemetry is schema-constrained to numeric capacity and load measurements; hostnames, usernames, paths, environment variables, command lines, network identifiers, container names, labels, and credential material are not accepted.
