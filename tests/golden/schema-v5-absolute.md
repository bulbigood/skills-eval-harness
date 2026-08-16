# Evaluation report

## Report identity

- Run ID: `run`
- Report revision: `v8`
- Suite: `suite` (`absolute`)
- Summary schema: `5`
- Run purpose: `production`
- Report checksum: [`report.md.sha256`](report.md.sha256)
- Sealed evidence: not staged with this report

## Status

- Evidence integrity: **VALID**
- Suite acceptance: **PASS** (`dimension-sample-rate-v1`)

## Execution and model configuration

| Arm | Role | Skill | Worker | Model (reasoning) |
|---|---|---|---|---|
| `skill` | `absolute` | demo v1.0.0 | `codex 1.2.3` | `model\|unsafe (reasoning: medium)` |

### Judge configuration

- Backend: `api-key`
- Model: `judge`
- Reasoning: `low`
- Dimensions: `task_correctness`, `scenario_compliance`, `skill_compliance`, `safety`, `evidence_quality`, `tool_efficiency`, `resource_efficiency`

Runtime: `0.18.0` (`aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`). Worker image: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`. Verifier image: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`. Harbor: `0.21.0`. Node: `22.23.2`.

## Provenance

- Harness: [https://example.test/harness](https://example.test/harness) commit `cccccccccccccccccccccccccccccccccccccccc`, tree `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- Source: [https://example.test/tree/x](https://example.test/tree/x) commit `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, tree `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- Selected skill: `demo` v`1.0.0`, tree `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- Config / suite / catalog: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` / `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` / `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- Effective suite / fixture registry: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` / `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- Task identities: `{&quot;arm/task&quot;: &quot;aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa&quot;}`

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
| `skill` | `one` | `task_correctness` | 2 / 2 | 100% | 90% | PASS |

The suite passes only when evidence is valid and every applicable criterion passes. Control arms are acceptance-blocking only for safety.

## Descriptive results

### Overall

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `overall` | `skill` | `task_correctness` | 5.000 | 2 | higher is better |
| `overall` | `skill` | `wall_time_seconds` | 10.000 | 2 | lower is better |
| `overall` | `skill` | `n_input_tokens` | 100.000 | 2 | lower is better |
| `overall` | `skill` | `n_cache_tokens` | 20.000 | 2 | lower is better |
| `overall` | `skill` | `n_output_tokens` | 10.000 | 2 | lower is better |
| `overall` | `skill` | `cost_usd` | 0.010 | 2 | lower is better |

### Per scenario

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `one` | `skill` | `task_correctness` | 5.000 | 2 | higher is better |
| `one` | `skill` | `wall_time_seconds` | 10.000 | 2 | lower is better |
| `one` | `skill` | `n_input_tokens` | 100.000 | 2 | lower is better |
| `one` | `skill` | `n_cache_tokens` | 20.000 | 2 | lower is better |
| `one` | `skill` | `n_output_tokens` | 10.000 | 2 | lower is better |
| `one` | `skill` | `cost_usd` | 0.010 | 2 | lower is better |

### Per family

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `read` | `skill` | `task_correctness` | 5.000 | 2 | higher is better |
| `read` | `skill` | `wall_time_seconds` | 10.000 | 2 | lower is better |
| `read` | `skill` | `n_input_tokens` | 100.000 | 2 | lower is better |
| `read` | `skill` | `n_cache_tokens` | 20.000 | 2 | lower is better |
| `read` | `skill` | `n_output_tokens` | 10.000 | 2 | lower is better |
| `read` | `skill` | `cost_usd` | 0.010 | 2 | lower is better |

## Failures and reliability

### Deterministic benchmark failures

None.

### Invalid or unavailable evidence

None.

### Reliability and missingness

- Planned / observed / valid cells: `2` / `2` / `2`.
- Deterministic failures by arm: `{"skill": 0}`.
- Missingness by scenario: `{"one": {"invalid": 0, "invalid_reasons": {}, "planned": 2, "valid": 2}}`.
- Missingness by family: `{"read": {"invalid": 0, "invalid_reasons": {}, "planned": 2, "valid": 2}}`.

## Timing

- Available-valid summed cell-seconds: `20.000`.
- Pipeline elapsed seconds: `12.000`.

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
        "arm": "skill",
        "dimension": "task_correctness",
        "observed_pass_rate": 1.0,
        "pass": true,
        "passed_samples": 2,
        "required_pass_rate": 0.9,
        "scenario_id": "one",
        "score_threshold": 5,
        "total_samples": 2
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
    "absolute": {
      "arm": "skill"
    },
    "kind": "absolute",
    "paired": null
  },
  "evaluation_status": {
    "acceptance": {
      "applicable": true,
      "passed": true,
      "policy_id": "dimension-sample-rate-v1"
    },
    "comparison": {
      "kind": "absolute",
      "superiority_verdict": null
    },
    "evidence_integrity": "valid"
  },
  "interpretation": {
    "inferential_status": "production-descriptive",
    "preregistered_samples": 2,
    "run_purpose": "production",
    "samples_per_identity": 2
  },
  "measurement_scope": {
    "cell_wall_time": "Harbor worker trial wall clock; excludes judging",
    "pipeline_elapsed": "end-to-end execution including judging",
    "tokens_and_cost": "Harbor worker totals; excludes judge usage"
  },
  "reliability": {
    "common_valid_pair_rate": null,
    "common_valid_pairs": null,
    "completion_rate_by_arm": {
      "skill": 1.0
    },
    "excluded_pairs": [],
    "invalid_cells_by_arm": {
      "skill": 0
    },
    "invalid_reasons_by_arm": {
      "skill": {}
    },
    "missingness_by_family": {
      "read": {
        "invalid": 0,
        "invalid_reasons": {},
        "planned": 2,
        "valid": 2
      }
    },
    "missingness_by_scenario": {
      "one": {
        "invalid": 0,
        "invalid_reasons": {},
        "planned": 2,
        "valid": 2
      }
    },
    "planned_cells_by_arm": {
      "skill": 2
    },
    "planned_pairs": null,
    "scenario_failures_by_arm": {
      "skill": 0
    },
    "valid_cells_by_arm": {
      "skill": 2
    }
  },
  "schema_version": 5,
  "statistics": {
    "available_valid": {
      "overall": {
        "skill": {
          "cohort": "available-valid",
          "cost_usd": {
            "mean": 0.01,
            "n": 2,
            "p05": 0.01,
            "p25": 0.01,
            "p75": 0.01,
            "p95": 0.01,
            "sd": 0.0
          },
          "n_cache_tokens": {
            "mean": 20.0,
            "n": 2,
            "p05": 20.0,
            "p25": 20.0,
            "p75": 20.0,
            "p95": 20.0,
            "sd": 0.0
          },
          "n_input_tokens": {
            "mean": 100.0,
            "n": 2,
            "p05": 100.0,
            "p25": 100.0,
            "p75": 100.0,
            "p95": 100.0,
            "sd": 0.0
          },
          "n_output_tokens": {
            "mean": 10.0,
            "n": 2,
            "p05": 10.0,
            "p25": 10.0,
            "p75": 10.0,
            "p95": 10.0,
            "sd": 0.0
          },
          "scores": {
            "task_correctness": {
              "mean": 5.0,
              "n": 2,
              "p05": 5.0,
              "p25": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.0
            }
          },
          "wall_time_seconds": {
            "mean": 10.0,
            "n": 2,
            "p05": 10.0,
            "p25": 10.0,
            "p75": 10.0,
            "p95": 10.0,
            "sd": 0.0
          }
        }
      },
      "per_family": {
        "read": {
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.01,
              "n": 2,
              "p05": 0.01,
              "p25": 0.01,
              "p75": 0.01,
              "p95": 0.01,
              "sd": 0.0
            },
            "n_cache_tokens": {
              "mean": 20.0,
              "n": 2,
              "p05": 20.0,
              "p25": 20.0,
              "p75": 20.0,
              "p95": 20.0,
              "sd": 0.0
            },
            "n_input_tokens": {
              "mean": 100.0,
              "n": 2,
              "p05": 100.0,
              "p25": 100.0,
              "p75": 100.0,
              "p95": 100.0,
              "sd": 0.0
            },
            "n_output_tokens": {
              "mean": 10.0,
              "n": 2,
              "p05": 10.0,
              "p25": 10.0,
              "p75": 10.0,
              "p95": 10.0,
              "sd": 0.0
            },
            "scores": {
              "task_correctness": {
                "mean": 5.0,
                "n": 2,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 10.0,
              "n": 2,
              "p05": 10.0,
              "p25": 10.0,
              "p75": 10.0,
              "p95": 10.0,
              "sd": 0.0
            }
          }
        }
      },
      "per_scenario": {
        "one": {
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.01,
              "n": 2,
              "p05": 0.01,
              "p25": 0.01,
              "p75": 0.01,
              "p95": 0.01,
              "sd": 0.0
            },
            "n_cache_tokens": {
              "mean": 20.0,
              "n": 2,
              "p05": 20.0,
              "p25": 20.0,
              "p75": 20.0,
              "p95": 20.0,
              "sd": 0.0
            },
            "n_input_tokens": {
              "mean": 100.0,
              "n": 2,
              "p05": 100.0,
              "p25": 100.0,
              "p75": 100.0,
              "p95": 100.0,
              "sd": 0.0
            },
            "n_output_tokens": {
              "mean": 10.0,
              "n": 2,
              "p05": 10.0,
              "p25": 10.0,
              "p75": 10.0,
              "p95": 10.0,
              "sd": 0.0
            },
            "scores": {
              "task_correctness": {
                "mean": 5.0,
                "n": 2,
                "p05": 5.0,
                "p25": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 10.0,
              "n": 2,
              "p05": 10.0,
              "p25": 10.0,
              "p75": 10.0,
              "p95": 10.0,
              "sd": 0.0
            }
          }
        }
      }
    },
    "common_valid_paired": {}
  },
  "timing": {
    "available_valid_summed_cell_seconds": 20.0,
    "common_valid_summed_cell_seconds": null,
    "pipeline_elapsed_seconds": 12.0
  }
}
```

</details>

## Sanitized device telemetry

<details>
<summary>Complete sanitized device telemetry</summary>

```json
{
  "cpu_percent_max": 0.0,
  "disk_read_bytes_per_second_max": 0.0,
  "disk_read_bytes_total": 0,
  "disk_scope": "physical-block-devices",
  "disk_write_bytes_per_second_max": 0.0,
  "disk_write_bytes_total": 0,
  "docker_oom_events": 0,
  "load1_max": 0.0,
  "logical_cpus": 1,
  "mem_available_bytes_min": 1,
  "network_rx_bytes_per_second_max": 0.0,
  "network_rx_bytes_total": 0,
  "network_scope": "default-route-interfaces",
  "network_tx_bytes_per_second_max": 0.0,
  "network_tx_bytes_total": 0,
  "rootfs_free_bytes_min": 1,
  "rootfs_scope": "root-filesystem",
  "rootfs_used_bytes_max": 0,
  "running_containers_max": 0,
  "sample_count": 1,
  "sampling_errors": 0,
  "schema_version": 2,
  "scope": "whole-host",
  "swap_free_bytes_min": 0,
  "terminal_status": "completed",
  "total_memory_bytes": 1,
  "total_swap_bytes": 0
}
```

</details>

The report is derived from the bundled, sealed machine-readable evidence. Device telemetry is schema-constrained to numeric capacity and load measurements; hostnames, usernames, paths, environment variables, command lines, network identifiers, container names, labels, and credential material are not accepted.
