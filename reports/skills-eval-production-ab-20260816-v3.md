# skills-eval-production-ab-20260816-v1

- Evaluation harness repository: [https://github.com/bulbigood/skills-eval-harness](https://github.com/bulbigood/skills-eval-harness)
- Evaluation harness commit used for this run: [`6d44cfa25f32908dee88eae60eef4b6646d7398f`](https://github.com/bulbigood/skills-eval-harness/commit/6d44cfa25f32908dee88eae60eef4b6646d7398f)
- Agent image SHA-256: `778452e0c755ab2d7b5b79ebf3a1ed099cbc9942a7225717e7da108c3a5b3751`
- Node version: `22.23.2`
- Harbor version: `0.21.0`
- Complete cells: `120` / `120`


## Executive summary

This is a **valid** production A/B evaluation. All `120` / `120` planned cells were observed. The paired analysis contains `60` common-valid pairs; `0` pairs were excluded.

The treatment arm `skill` had `0` deterministic scenario failures, compared with `8` in `no-skill`.

All deltas below are **treatment minus control** (`skill − no-skill`). Positive score deltas are better; negative cost, token, and wall-time deltas are better.

## Compared arms

| Arm | Role | Skill guidance | Worker agent | Model | Runtime |
|---|---|---|---|---|---|
| `skill` | Treatment | [iwe-v18](https://github.com/iwe-org/skills/tree/f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18) v0.9.9 | `codex 0.147.0` | `openai/gpt-5.6-luna` | `IWE 0.18.0` |
| `no-skill` | Control | No skill guidance | `codex 0.147.0` | `openai/gpt-5.6-luna` | `IWE 0.18.0` |

The treatment skill comes from skill-repository commit `f571d6f83dd79407ec64caf7cc3036708062e3c8`. Its content SHA-256 is `ca4b120faa5374bc16d5a221d3ccc853aa64ded5c3df0be197ef6a38a01281b9`; this immutable content identity is recorded for reproducibility. The IWE runtime binary SHA-256 is `12eb77af823b04472a2b92ceb0d5bacef4e1eda1b38ba0dadfe8f7c33a86ce6c` and verifies the exact executable shared by both arms.

## Overall paired comparison

| Metric | Skill mean | No-skill mean | Paired Δ | Δ median | n |
|---|---:|---:|---:|---:|---:|
| Evidence quality | 5.000 | 4.833 | 0.167 | 0.000 | 60 |
| Resource efficiency | 4.867 | 1.633 | 3.233 | 4.000 | 60 |
| Safety | 5.000 | 5.000 | 0.000 | 0.000 | 60 |
| Scenario compliance | 4.967 | 3.650 | 1.317 | 1.000 | 60 |
| Task correctness | 5.000 | 4.750 | 0.250 | 0.000 | 60 |
| Tool efficiency | 4.883 | 1.383 | 3.500 | 4.000 | 60 |
| Cost (USD) | 0.003541 | 0.007789 | -0.004247 | -0.001467 | 60 |
| Cache tokens | 37,132.8 | 108,044.8 | -70,912.0 | -28,928.0 | 60 |
| Input tokens | 47,574.3 | 127,315.9 | -79,741.5 | -37,833.0 | 60 |
| Output tokens | 592.017 | 1,478.0 | -886.000 | -465.000 | 60 |
| Wall time (s) | 52.066 | 70.945 | -18.878 | -11.205 | 60 |

Means use the common-valid paired cohort. The paired Δ columns summarize within-pair differences, not differences between independently rounded arm means.

## By scenario

| Group | n pairs | Correctness Δ | Tool efficiency Δ | Wall-time Δ (s) | Cost Δ (USD) |
|---|---:|---:|---:|---:|---:|
| `ambiguous-discovery-with-one-follow-up` | 10 | 0.000 | 0.700 | 1.502 | 0.000794 |
| `discover-and-retrieve-bounded-multi-hop-context` | 10 | 0.000 | 3.800 | -16.710 | -0.005085 |
| `list-and-sort-typed-notes` | 10 | 1.500 | 4.200 | -11.059 | -0.001165 |
| `query-structured-metadata-without-scanning-files` | 10 | 0.000 | 4.900 | -77.496 | -0.019 |
| `read-one-note-with-parent-context` | 10 | 0.000 | 3.200 | 0.858 | 0.000358 |
| `summarize-one-topic` | 10 | 0.000 | 4.200 | -10.364 | -0.001307 |

## By scenario family

| Group | n pairs | Correctness Δ | Tool efficiency Δ | Wall-time Δ (s) | Cost Δ (USD) |
|---|---:|---:|---:|---:|---:|
| `find` | 20 | 0.750 | 4.550 | -44.277 | -0.010 |
| `find+retrieve` | 10 | 0.000 | 0.700 | 1.502 | 0.000794 |
| `retrieve` | 30 | 0.000 | 3.733 | -8.739 | -0.002011 |

## Deterministic failure ledger

| Arm | Scenario | Sample | Deterministic failure | Judge summary |
|---|---|---:|---|---|
| `no-skill` | `query-structured-metadata-without-scanning-files` | 1 | hard tool-call maximum exceeded | The delivered answer was accurate, complete, safe, and compliant, but the execution was highly inefficient: it exceeded both the hard tool-call maximum and the observed tool-output budget by a large margin. |
| `no-skill` | `query-structured-metadata-without-scanning-files` | 2 | hard tool-call maximum exceeded | The delivered answer is substantively correct, concise, and safe, but the trajectory is severely inefficient and violates the scenario's one-query, no-scanning procedure. |
| `no-skill` | `query-structured-metadata-without-scanning-files` | 5 | hard tool-call maximum exceeded | The answer itself was accurate, complete, safe, and well-supported, but the trajectory was severely inefficient and violated the scenario's explicit one-call constraint. |
| `no-skill` | `query-structured-metadata-without-scanning-files` | 6 | hard tool-call maximum exceeded | The final answer was fully correct, well-supported, safe, and compliant in form, but the execution was drastically inefficient: it exceeded both the hard tool-call limit and the tool-output byte budget. |
| `no-skill` | `query-structured-metadata-without-scanning-files` | 7 | hard tool-call maximum exceeded | The delivered answer was accurate, well-supported, scoped correctly, and safe, but the execution was drastically inefficient: it used 11 calls and 211,515 bytes of tool output for a scenario designed to require one bounded structured query. |
| `no-skill` | `query-structured-metadata-without-scanning-files` | 8 | hard tool-call maximum exceeded | The final answer was substantively correct, safe, and compliant in form, but execution efficiency was severely deficient: it exceeded both the one-call target and the observed tool-output budget by a large margin. |
| `no-skill` | `query-structured-metadata-without-scanning-files` | 9 | hard tool-call maximum exceeded | The answer itself was accurate, compact, and safe, but the trajectory was highly inefficient and failed the scenario's central requirement to obtain the structured metadata with one bounded query. |
| `no-skill` | `query-structured-metadata-without-scanning-files` | 10 | hard tool-call maximum exceeded | The delivered answer was accurate, complete, concise, and safe, but the execution was severely inefficient: it used 13 calls and roughly 194 KB of tool output for a task designed to require one bounded query. |

## Reliability and timing

- Common-valid pair rate: `1.000` (`60` / `60`).
- Valid cells: `120` / `120`.
- Invalid cells: `0`.
- Summed common-valid cell time: `7,380.7` seconds.
- Pipeline elapsed time: `4,814.2` seconds.

Summed cell-seconds measure aggregate work across cells. Pipeline elapsed time measures end-to-end wall-clock duration under concurrency; they are intentionally not interchangeable.

## Audit appendix

<details>
<summary>Complete machine-readable statistics and timing</summary>

```json
{
  "statistics": {
    "available_valid": {
      "overall": {
        "no-skill": {
          "cohort": "available-valid",
          "cost_usd": {
            "mean": 0.007788729333333333,
            "n": 60,
            "p05": 0.00221725,
            "p25": 0.0029647799999999998,
            "p50": 0.0044109200000000005,
            "p75": 0.00859679,
            "p95": 0.02646665,
            "sd": 0.007694568781522406
          },
          "n_cache_tokens": {
            "mean": 108044.8,
            "n": 60,
            "p05": 32524.800000000003,
            "p25": 35072.0,
            "p50": 64896.0,
            "p75": 78016.0,
            "p95": 427135.9999999998,
            "sd": 130219.56215936325
          },
          "n_input_tokens": {
            "mean": 127315.86666666667,
            "n": 60,
            "p05": 38196.05,
            "p25": 41949.5,
            "p50": 83818.5,
            "p75": 102230.0,
            "p95": 489602.64999999985,
            "sd": 145632.1452006549
          },
          "n_output_tokens": {
            "mean": 1478.0166666666667,
            "n": 60,
            "p05": 369.8,
            "p25": 468.75,
            "p50": 883.5,
            "p75": 1640.75,
            "p95": 5175.35,
            "sd": 1551.162937071613
          },
          "scores": {
            "evidence_quality": {
              "mean": 4.833333333333333,
              "n": 60,
              "p05": 3.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.5261522196019802
            },
            "resource_efficiency": {
              "mean": 1.6333333333333333,
              "n": 60,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 1.0,
              "p75": 3.0,
              "p95": 5.0,
              "sd": 1.726823935424455
            },
            "safety": {
              "mean": 5.0,
              "n": 60,
              "p05": 5.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 3.65,
              "n": 60,
              "p05": 2.0,
              "p25": 3.0,
              "p50": 4.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 1.0865120683067773
            },
            "task_correctness": {
              "mean": 4.75,
              "n": 60,
              "p05": 2.95,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.7729538324626148
            },
            "tool_efficiency": {
              "mean": 1.3833333333333333,
              "n": 60,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 1.0,
              "p75": 2.0,
              "p95": 5.0,
              "sd": 1.5303889686874466
            }
          },
          "wall_time_seconds": {
            "mean": 70.94472801666667,
            "n": 60,
            "p05": 46.8677561,
            "p25": 49.622942,
            "p50": 60.036891499999996,
            "p75": 73.15607875,
            "p95": 146.57354565,
            "sd": 32.751760231942654
          }
        },
        "skill": {
          "cohort": "available-valid",
          "cost_usd": {
            "mean": 0.003541386,
            "n": 60,
            "p05": 0.00285715,
            "p25": 0.0029344499999999995,
            "p50": 0.003228,
            "p75": 0.00411275,
            "p95": 0.004754739999999999,
            "sd": 0.0007594016590180206
          },
          "n_cache_tokens": {
            "mean": 37132.8,
            "n": 60,
            "p05": 27136.0,
            "p25": 37120.0,
            "p50": 37120.0,
            "p75": 37120.0,
            "p95": 53248.0,
            "sd": 5505.019062144678
          },
          "n_input_tokens": {
            "mean": 47574.35,
            "n": 60,
            "p05": 45498.4,
            "p25": 45554.75,
            "p50": 45713.5,
            "p75": 46748.25,
            "p95": 62699.45,
            "sd": 4722.595579870983
          },
          "n_output_tokens": {
            "mean": 592.0166666666667,
            "n": 60,
            "p05": 371.85,
            "p25": 410.25,
            "p50": 469.0,
            "p75": 758.0,
            "p95": 1058.9499999999998,
            "sd": 240.9608936319066
          },
          "scores": {
            "evidence_quality": {
              "mean": 5.0,
              "n": 60,
              "p05": 5.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.0
            },
            "resource_efficiency": {
              "mean": 4.866666666666666,
              "n": 60,
              "p05": 5.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.7240813388775701
            },
            "safety": {
              "mean": 5.0,
              "n": 60,
              "p05": 5.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 4.966666666666667,
              "n": 60,
              "p05": 5.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.25819888974716115
            },
            "skill_compliance": {
              "mean": 4.933333333333334,
              "n": 60,
              "p05": 5.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.40616714713579355
            },
            "task_correctness": {
              "mean": 5.0,
              "n": 60,
              "p05": 5.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.0
            },
            "tool_efficiency": {
              "mean": 4.883333333333334,
              "n": 60,
              "p05": 5.0,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.6402241838994506
            }
          },
          "wall_time_seconds": {
            "mean": 52.06647366666667,
            "n": 60,
            "p05": 47.360844650000004,
            "p25": 48.08570974999999,
            "p50": 49.783041,
            "p75": 56.052922499999994,
            "p95": 60.87846905,
            "sd": 4.843649737215941
          }
        }
      },
      "per_family": {
        "find": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.013685974,
              "n": 20,
              "p05": 0.003496216,
              "p25": 0.00433321,
              "p50": 0.0088858,
              "p75": 0.02182532,
              "p95": 0.030637465999999995,
              "sd": 0.010521916334927026
            },
            "n_cache_tokens": {
              "mean": 217075.2,
              "n": 20,
              "p05": 49100.799999999996,
              "p25": 64000.0,
              "p50": 125440.0,
              "p75": 305792.0,
              "p95": 547507.2,
              "sd": 181408.08107619509
            },
            "n_input_tokens": {
              "mean": 248144.75,
              "n": 20,
              "p05": 58003.1,
              "p25": 73545.25,
              "p50": 148940.0,
              "p75": 358097.5,
              "p95": 615028.7500000001,
              "sd": 202697.82903983092
            },
            "n_output_tokens": {
              "mean": 2608.8,
              "n": 20,
              "p05": 637.5500000000001,
              "p25": 879.25,
              "p50": 1397.5,
              "p75": 4302.75,
              "p95": 6537.700000000001,
              "sd": 2130.2270103886754
            },
            "scores": {
              "evidence_quality": {
                "mean": 4.5,
                "n": 20,
                "p05": 3.0,
                "p25": 4.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.8271701918685112
              },
              "resource_efficiency": {
                "mean": 0.5,
                "n": 20,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 0.0,
                "p75": 1.0,
                "p95": 1.0500000000000007,
                "sd": 0.606976978666884
              },
              "safety": {
                "mean": 5.0,
                "n": 20,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 3.65,
                "n": 20,
                "p05": 2.0,
                "p25": 2.75,
                "p50": 3.5,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.268027892769755
              },
              "task_correctness": {
                "mean": 4.25,
                "n": 20,
                "p05": 2.0,
                "p25": 3.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.2085223687584246
              },
              "tool_efficiency": {
                "mean": 0.45,
                "n": 20,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 0.0,
                "p75": 1.0,
                "p95": 1.0,
                "sd": 0.5104177855340404
              }
            },
            "wall_time_seconds": {
              "mean": 96.1436,
              "n": 20,
              "p05": 52.61406675,
              "p25": 60.442060500000004,
              "p50": 74.036553,
              "p75": 130.6223245,
              "p95": 177.8414978,
              "sd": 44.58939212462357
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.00356403,
              "n": 20,
              "p05": 0.00285715,
              "p25": 0.00293875,
              "p50": 0.0034343,
              "p75": 0.0035687,
              "p95": 0.0052441960000000004,
              "sd": 0.0008039857920582795
            },
            "n_cache_tokens": {
              "mean": 35072.0,
              "n": 20,
              "p05": 27084.8,
              "p25": 37120.0,
              "p50": 37120.0,
              "p75": 37120.0,
              "p95": 37120.0,
              "sd": 4207.3291440432595
            },
            "n_input_tokens": {
              "mean": 45860.25,
              "n": 20,
              "p05": 45485.75,
              "p25": 45521.0,
              "p50": 45873.5,
              "p75": 46182.0,
              "p95": 46230.799999999996,
              "sd": 340.9071296594302
            },
            "n_output_tokens": {
              "mean": 587.45,
              "n": 20,
              "p05": 368.0,
              "p25": 419.0,
              "p50": 563.5,
              "p75": 758.0,
              "p95": 831.5500000000001,
              "sd": 186.8271013249247
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 20,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 20,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "safety": {
                "mean": 5.0,
                "n": 20,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 20,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "skill_compliance": {
                "mean": 4.95,
                "n": 20,
                "p05": 4.949999999999999,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.22360679774997896
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 20,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 20,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 51.86614505,
              "n": 20,
              "p05": 47.4653228,
              "p25": 47.70112075,
              "p50": 51.266481,
              "p75": 56.052922499999994,
              "p95": 56.5186035,
              "sd": 4.069891378679178
            }
          }
        },
        "find+retrieve": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.002756888,
              "n": 10,
              "p05": 0.00242858,
              "p25": 0.00246464,
              "p50": 0.0025185399999999997,
              "p75": 0.00305375,
              "p95": 0.0034682439999999992,
              "sd": 0.00044053771781514653
            },
            "n_cache_tokens": {
              "mean": 40294.4,
              "n": 10,
              "p05": 34508.8,
              "p25": 35072.0,
              "p50": 35072.0,
              "p75": 44096.0,
              "p95": 56435.19999999998,
              "sd": 9640.9296370561
            },
            "n_input_tokens": {
              "mean": 47019.4,
              "n": 10,
              "p05": 40946.350000000006,
              "p25": 41098.25,
              "p50": 41163.0,
              "p75": 51039.5,
              "p95": 64889.59999999999,
              "sd": 10553.945014911616
            },
            "n_output_tokens": {
              "mean": 505.0,
              "n": 10,
              "p05": 451.25,
              "p25": 459.0,
              "p50": 478.5,
              "p75": 516.25,
              "p95": 630.55,
              "sd": 70.4493513888603
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 4.3,
                "n": 10,
                "p05": 3.0,
                "p25": 4.0,
                "p50": 4.5,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.8232726023485646
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 4.8,
                "n": 10,
                "p05": 4.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.4216370213557839
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 4.3,
                "n": 10,
                "p05": 2.45,
                "p25": 4.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.0593499054713802
              }
            },
            "wall_time_seconds": {
              "mean": 50.1627205,
              "n": 10,
              "p05": 47.74209365,
              "p25": 48.402347,
              "p50": 48.999271,
              "p75": 51.91409275,
              "p95": 54.36802734999999,
              "sd": 2.6311753132478546
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.003550624,
              "n": 10,
              "p05": 0.00299475,
              "p25": 0.0030786500000000005,
              "p50": 0.00332168,
              "p75": 0.0035918100000000004,
              "p95": 0.004868181999999998,
              "sd": 0.0008179822590197852
            },
            "n_cache_tokens": {
              "mean": 44083.2,
              "n": 10,
              "p05": 37120.0,
              "p25": 37120.0,
              "p50": 39680.0,
              "p75": 53248.0,
              "p95": 53248.0,
              "sd": 8040.193430508995
            },
            "n_input_tokens": {
              "mean": 54281.0,
              "n": 10,
              "p05": 45751.350000000006,
              "p25": 45807.0,
              "p50": 54235.5,
              "p75": 62733.75,
              "p95": 62878.350000000006,
              "sd": 8944.117495749806
            },
            "n_output_tokens": {
              "mean": 524.5,
              "n": 10,
              "p05": 428.5,
              "p25": 475.5,
              "p50": 508.0,
              "p75": 543.5,
              "p95": 662.25,
              "sd": 84.01487963450283
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "skill_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 51.6646571,
              "n": 10,
              "p05": 49.13503465,
              "p25": 50.1381375,
              "p50": 51.1384025,
              "p75": 53.34091275,
              "p95": 55.0726765,
              "sd": 2.254667427945735
            }
          }
        },
        "retrieve": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.005534513333333334,
              "n": 30,
              "p05": 0.00216273,
              "p25": 0.00292858,
              "p50": 0.004447059999999999,
              "p75": 0.008156459999999999,
              "p95": 0.009405972,
              "sd": 0.003144440478051571
            },
            "n_cache_tokens": {
              "mean": 57941.333333333336,
              "n": 30,
              "p05": 23040.0,
              "p25": 33024.0,
              "p50": 66048.0,
              "p75": 75264.0,
              "p95": 78694.4,
              "sd": 23044.93638050687
            },
            "n_input_tokens": {
              "mean": 73528.76666666666,
              "n": 30,
              "p05": 38175.25,
              "p25": 40919.25,
              "p50": 84460.5,
              "p75": 92672.5,
              "p95": 103385.45,
              "sd": 30178.292634325564
            },
            "n_output_tokens": {
              "mean": 1048.5,
              "n": 30,
              "p05": 355.0,
              "p25": 404.0,
              "p50": 888.5,
              "p75": 1591.5,
              "p95": 2026.2999999999995,
              "sd": 722.0795519264791
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 30,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 1.5,
                "n": 30,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 1.0,
                "p75": 2.75,
                "p95": 4.0,
                "sd": 1.5028708160235105
              },
              "safety": {
                "mean": 5.0,
                "n": 30,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 3.2666666666666666,
                "n": 30,
                "p05": 2.0,
                "p25": 3.0,
                "p50": 3.0,
                "p75": 4.0,
                "p95": 4.549999999999997,
                "sd": 0.8276819867946673
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 30,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 1.0333333333333334,
                "n": 30,
                "p05": 0.0,
                "p25": 0.25,
                "p50": 1.0,
                "p75": 2.0,
                "p95": 2.0,
                "sd": 0.7648904962570576
              }
            },
            "wall_time_seconds": {
              "mean": 61.072815866666666,
              "n": 30,
              "p05": 46.55108565,
              "p25": 48.04565275,
              "p50": 59.9634525,
              "p75": 70.72577375,
              "p95": 80.84143999999999,
              "sd": 13.780793234221134
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.0035232106666666665,
              "n": 30,
              "p05": 0.0027834440000000004,
              "p25": 0.0029181,
              "p50": 0.0029977,
              "p75": 0.00418855,
              "p95": 0.0047183799999999994,
              "sd": 0.0007357946324373929
            },
            "n_cache_tokens": {
              "mean": 36189.86666666667,
              "n": 30,
              "p05": 27136.0,
              "p25": 37120.0,
              "p50": 37120.0,
              "p75": 37120.0,
              "p95": 37683.2,
              "sd": 3080.43592675624
            },
            "n_input_tokens": {
              "mean": 46481.53333333333,
              "n": 30,
              "p05": 45508.8,
              "p25": 45552.25,
              "p50": 45614.5,
              "p75": 48264.75,
              "p95": 48324.3,
              "sd": 1303.9276141674834
            },
            "n_output_tokens": {
              "mean": 617.5666666666667,
              "n": 30,
              "p05": 380.1,
              "p25": 404.5,
              "p50": 434.5,
              "p75": 933.5,
              "p95": 1131.7499999999998,
              "sd": 301.3401884837173
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 30,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 4.733333333333333,
                "n": 30,
                "p05": 2.8000000000000007,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.0148325268098497
              },
              "safety": {
                "mean": 5.0,
                "n": 30,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 4.933333333333334,
                "n": 30,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.3651483716701107
              },
              "skill_compliance": {
                "mean": 4.9,
                "n": 30,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.5477225575051661
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 30,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 4.766666666666667,
                "n": 30,
                "p05": 3.3500000000000005,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.8976341829703132
              }
            },
            "wall_time_seconds": {
              "mean": 52.33396493333333,
              "n": 30,
              "p05": 47.31734485,
              "p25": 47.778209000000004,
              "p50": 48.9528515,
              "p75": 58.62651825,
              "p95": 62.68905304999999,
              "sd": 5.928202181765431
            }
          }
        }
      },
      "per_scenario": {
        "ambiguous-discovery-with-one-follow-up": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.002756888,
              "n": 10,
              "p05": 0.00242858,
              "p25": 0.00246464,
              "p50": 0.0025185399999999997,
              "p75": 0.00305375,
              "p95": 0.0034682439999999992,
              "sd": 0.00044053771781514653
            },
            "n_cache_tokens": {
              "mean": 40294.4,
              "n": 10,
              "p05": 34508.8,
              "p25": 35072.0,
              "p50": 35072.0,
              "p75": 44096.0,
              "p95": 56435.19999999998,
              "sd": 9640.9296370561
            },
            "n_input_tokens": {
              "mean": 47019.4,
              "n": 10,
              "p05": 40946.350000000006,
              "p25": 41098.25,
              "p50": 41163.0,
              "p75": 51039.5,
              "p95": 64889.59999999999,
              "sd": 10553.945014911616
            },
            "n_output_tokens": {
              "mean": 505.0,
              "n": 10,
              "p05": 451.25,
              "p25": 459.0,
              "p50": 478.5,
              "p75": 516.25,
              "p95": 630.55,
              "sd": 70.4493513888603
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 4.3,
                "n": 10,
                "p05": 3.0,
                "p25": 4.0,
                "p50": 4.5,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.8232726023485646
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 4.8,
                "n": 10,
                "p05": 4.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.4216370213557839
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 4.3,
                "n": 10,
                "p05": 2.45,
                "p25": 4.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.0593499054713802
              }
            },
            "wall_time_seconds": {
              "mean": 50.1627205,
              "n": 10,
              "p05": 47.74209365,
              "p25": 48.402347,
              "p50": 48.999271,
              "p75": 51.91409275,
              "p95": 54.36802734999999,
              "sd": 2.6311753132478546
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.003550624,
              "n": 10,
              "p05": 0.00299475,
              "p25": 0.0030786500000000005,
              "p50": 0.00332168,
              "p75": 0.0035918100000000004,
              "p95": 0.004868181999999998,
              "sd": 0.0008179822590197852
            },
            "n_cache_tokens": {
              "mean": 44083.2,
              "n": 10,
              "p05": 37120.0,
              "p25": 37120.0,
              "p50": 39680.0,
              "p75": 53248.0,
              "p95": 53248.0,
              "sd": 8040.193430508995
            },
            "n_input_tokens": {
              "mean": 54281.0,
              "n": 10,
              "p05": 45751.350000000006,
              "p25": 45807.0,
              "p50": 54235.5,
              "p75": 62733.75,
              "p95": 62878.350000000006,
              "sd": 8944.117495749806
            },
            "n_output_tokens": {
              "mean": 524.5,
              "n": 10,
              "p05": 428.5,
              "p25": 475.5,
              "p50": 508.0,
              "p75": 543.5,
              "p95": 662.25,
              "sd": 84.01487963450283
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "skill_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 51.6646571,
              "n": 10,
              "p05": 49.13503465,
              "p25": 50.1381375,
              "p50": 51.1384025,
              "p75": 53.34091275,
              "p95": 55.0726765,
              "sd": 2.254667427945735
            }
          }
        },
        "discover-and-retrieve-bounded-multi-hop-context": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.009290276,
              "n": 10,
              "p05": 0.007798004000000001,
              "p25": 0.008237119999999999,
              "p50": 0.00873778,
              "p75": 0.00933049,
              "p95": 0.012622053999999994,
              "sd": 0.002172029891298306
            },
            "n_cache_tokens": {
              "mean": 74956.8,
              "n": 10,
              "p05": 64409.600000000006,
              "p25": 67072.0,
              "p50": 70528.0,
              "p75": 76096.0,
              "p95": 99327.99999999997,
              "sd": 15097.39365880379
            },
            "n_input_tokens": {
              "mean": 102509.5,
              "n": 10,
              "p05": 87953.5,
              "p25": 92107.5,
              "p50": 97710.5,
              "p75": 102832.0,
              "p95": 134532.79999999993,
              "sd": 20985.121630177255
            },
            "n_output_tokens": {
              "mean": 1900.5,
              "n": 10,
              "p05": 1486.9,
              "p25": 1606.25,
              "p50": 1741.5,
              "p75": 1933.0,
              "p95": 2791.2499999999986,
              "sd": 552.6102202778696
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 0.4,
                "n": 10,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 0.0,
                "p75": 1.0,
                "p95": 1.0,
                "sd": 0.5163977794943223
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 2.8,
                "n": 10,
                "p05": 2.0,
                "p25": 2.0,
                "p50": 3.0,
                "p75": 3.0,
                "p95": 4.099999999999998,
                "sd": 0.9189365834726815
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 0.5,
                "n": 10,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 0.5,
                "p75": 1.0,
                "p95": 1.0,
                "sd": 0.5270462766947299
              }
            },
            "wall_time_seconds": {
              "mean": 77.0383508,
              "n": 10,
              "p05": 69.26558370000001,
              "p25": 71.24475025,
              "p50": 74.0152265,
              "p75": 78.17748625,
              "p95": 93.93282534999997,
              "sd": 10.15701567494898
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.0042051,
              "n": 10,
              "p05": 0.00401623,
              "p25": 0.00411275,
              "p50": 0.0041791,
              "p75": 0.0042738,
              "p95": 0.00443916,
              "sd": 0.00015305145830369897
            },
            "n_cache_tokens": {
              "mean": 37120.0,
              "n": 10,
              "p05": 37120.0,
              "p25": 37120.0,
              "p50": 37120.0,
              "p75": 37120.0,
              "p95": 37120.0,
              "sd": 0.0
            },
            "n_input_tokens": {
              "mean": 48293.1,
              "n": 10,
              "p05": 48257.700000000004,
              "p25": 48270.5,
              "p50": 48286.0,
              "p75": 48317.0,
              "p95": 48334.15,
              "sd": 29.194558092600445
            },
            "n_output_tokens": {
              "mean": 1023.4,
              "n": 10,
              "p05": 866.5500000000001,
              "p25": 944.5,
              "p50": 1004.5,
              "p75": 1086.25,
              "p95": 1213.25,
              "sd": 126.32603321036669
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 4.2,
                "n": 10,
                "p05": 1.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.6865480854231356
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 4.8,
                "n": 10,
                "p05": 3.9000000000000004,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.6324555320336759
              },
              "skill_compliance": {
                "mean": 4.7,
                "n": 10,
                "p05": 3.35,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.9486832980505138
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 4.3,
                "n": 10,
                "p05": 1.4500000000000002,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.4944341180973262
              }
            },
            "wall_time_seconds": {
              "mean": 60.328277,
              "n": 10,
              "p05": 57.6455878,
              "p25": 58.846126999999996,
              "p50": 59.979383999999996,
              "p75": 61.13863175,
              "p95": 63.89202065,
              "sd": 2.2533788014121763
            }
          }
        },
        "list-and-sort-typed-notes": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.004443776,
              "n": 10,
              "p05": 0.0033799760000000002,
              "p25": 0.004039880000000001,
              "p50": 0.00430398,
              "p75": 0.00479371,
              "p95": 0.005793875999999998,
              "sd": 0.0008511475335125187
            },
            "n_cache_tokens": {
              "mean": 70476.8,
              "n": 10,
              "p05": 48588.8,
              "p25": 62464.0,
              "p50": 63744.0,
              "p75": 78848.0,
              "p95": 99596.79999999999,
              "sd": 18250.982736402017
            },
            "n_input_tokens": {
              "mean": 80458.0,
              "n": 10,
              "p05": 56874.100000000006,
              "p25": 71440.0,
              "p50": 73366.5,
              "p75": 89521.25,
              "p95": 112134.59999999998,
              "sd": 19789.914395413078
            },
            "n_output_tokens": {
              "mean": 865.0,
              "n": 10,
              "p05": 623.05,
              "p25": 810.5,
              "p50": 869.5,
              "p75": 943.75,
              "p95": 1078.6499999999999,
              "sd": 157.32627102793595
            },
            "scores": {
              "evidence_quality": {
                "mean": 4.0,
                "n": 10,
                "p05": 3.0,
                "p25": 3.0,
                "p50": 4.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.9428090415820634
              },
              "resource_efficiency": {
                "mean": 0.9,
                "n": 10,
                "p05": 0.0,
                "p25": 1.0,
                "p50": 1.0,
                "p75": 1.0,
                "p95": 1.549999999999999,
                "sd": 0.5676462121975467
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 4.0,
                "n": 10,
                "p05": 3.0,
                "p25": 3.0,
                "p50": 4.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.9428090415820634
              },
              "task_correctness": {
                "mean": 3.5,
                "n": 10,
                "p05": 2.0,
                "p25": 2.25,
                "p50": 3.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.35400640077266
              },
              "tool_efficiency": {
                "mean": 0.8,
                "n": 10,
                "p05": 0.0,
                "p25": 1.0,
                "p50": 1.0,
                "p75": 1.0,
                "p95": 1.0,
                "sd": 0.4216370213557839
              }
            },
            "wall_time_seconds": {
              "mean": 59.112096799999996,
              "n": 10,
              "p05": 52.05671425,
              "p25": 56.93359475,
              "p50": 60.252210000000005,
              "p75": 60.97439,
              "p95": 64.6503179,
              "sd": 4.439501782901841
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.003278924,
              "n": 10,
              "p05": 0.0028426500000000004,
              "p25": 0.00289825,
              "p50": 0.0029375,
              "p75": 0.00301835,
              "p95": 0.004698010000000001,
              "sd": 0.0007491632401137806
            },
            "n_cache_tokens": {
              "mean": 35123.2,
              "n": 10,
              "p05": 27136.0,
              "p25": 37120.0,
              "p50": 37120.0,
              "p75": 37120.0,
              "p95": 37120.0,
              "sd": 4209.6240212161465
            },
            "n_input_tokens": {
              "mean": 45530.5,
              "n": 10,
              "p05": 45473.25,
              "p25": 45501.5,
              "p50": 45518.0,
              "p75": 45551.25,
              "p95": 45610.55,
              "sd": 49.37216939846892
            },
            "n_output_tokens": {
              "mean": 412.5,
              "n": 10,
              "p05": 358.0,
              "p25": 385.5,
              "p50": 417.0,
              "p75": 427.25,
              "p95": 475.5,
              "sd": 41.7565696760535
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "skill_compliance": {
                "mean": 4.9,
                "n": 10,
                "p05": 4.45,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.31622776601683794
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 48.0527809,
              "n": 10,
              "p05": 47.3837008,
              "p25": 47.590977499999994,
              "p50": 47.6862645,
              "p75": 48.11368350000001,
              "p95": 49.5441619,
              "sd": 0.8441557175731478
            }
          }
        },
        "query-structured-metadata-without-scanning-files": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.022928172,
              "n": 10,
              "p05": 0.014084138,
              "p25": 0.018679,
              "p50": 0.022792479999999997,
              "p75": 0.02707047,
              "p95": 0.031797326,
              "sd": 0.006571142275861768
            },
            "n_cache_tokens": {
              "mean": 363673.6,
              "n": 10,
              "p05": 186304.0,
              "p25": 268736.0,
              "p50": 333568.0,
              "p75": 471936.0,
              "p95": 569779.2,
              "sd": 146230.12409152303
            },
            "n_input_tokens": {
              "mean": 415831.5,
              "n": 10,
              "p05": 225452.95,
              "p25": 315036.5,
              "p50": 386333.0,
              "p75": 530897.75,
              "p95": 630456.25,
              "sd": 154466.86057191828
            },
            "n_output_tokens": {
              "mean": 4352.6,
              "n": 10,
              "p05": 2033.6000000000001,
              "p25": 3304.5,
              "p50": 4336.5,
              "p75": 5208.25,
              "p95": 6734.699999999999,
              "sd": 1672.6539922463874
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 0.1,
                "n": 10,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 0.0,
                "p75": 0.0,
                "p95": 0.5499999999999989,
                "sd": 0.31622776601683794
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 3.3,
                "n": 10,
                "p05": 2.0,
                "p25": 2.0,
                "p50": 2.5,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.4944341180973262
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 0.1,
                "n": 10,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 0.0,
                "p75": 0.0,
                "p95": 0.5499999999999989,
                "sd": 0.31622776601683794
              }
            },
            "wall_time_seconds": {
              "mean": 133.1751032,
              "n": 10,
              "p05": 87.97025005,
              "p25": 111.94184999999999,
              "p50": 131.959354,
              "p75": 147.13389074999998,
              "p95": 183.4298858,
              "sd": 33.618838536798094
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.0038491360000000004,
              "n": 10,
              "p05": 0.00336453,
              "p25": 0.0034541,
              "p50": 0.0035069,
              "p75": 0.0035788999999999994,
              "p95": 0.005346956,
              "sd": 0.0007891311153583205
            },
            "n_cache_tokens": {
              "mean": 35020.8,
              "n": 10,
              "p05": 26572.800000000003,
              "p25": 37120.0,
              "p50": 37120.0,
              "p75": 37120.0,
              "p95": 37120.0,
              "sd": 4432.078940331877
            },
            "n_input_tokens": {
              "mean": 46190.0,
              "n": 10,
              "p05": 46145.0,
              "p25": 46164.25,
              "p50": 46185.0,
              "p75": 46219.75,
              "p95": 46238.8,
              "sd": 35.739800409813895
            },
            "n_output_tokens": {
              "mean": 762.4,
              "n": 10,
              "p05": 678.0500000000001,
              "p25": 732.0,
              "p50": 759.0,
              "p75": 802.0,
              "p95": 847.05,
              "sd": 62.663475096032705
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "skill_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 55.6795092,
              "n": 10,
              "p05": 53.41812395,
              "p25": 55.18524725,
              "p50": 56.06618,
              "p75": 56.4019735,
              "p95": 57.03170849999999,
              "sd": 1.393157411580997
            }
          }
        },
        "read-one-note-with-parent-context": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.002954904,
              "n": 10,
              "p05": 0.00216273,
              "p25": 0.0022253299999999998,
              "p50": 0.00263062,
              "p75": 0.00367617,
              "p95": 0.004365319999999999,
              "sd": 0.0009180435876749596
            },
            "n_cache_tokens": {
              "mean": 31539.2,
              "n": 10,
              "p05": 23040.0,
              "p25": 25536.0,
              "p50": 33024.0,
              "p75": 33024.0,
              "p95": 41228.79999999999,
              "sd": 7274.685434970902
            },
            "n_input_tokens": {
              "mean": 40845.0,
              "n": 10,
              "p05": 38175.25,
              "p25": 38252.5,
              "p50": 38427.5,
              "p75": 41771.75,
              "p95": 48545.44999999999,
              "sd": 4817.280883559844
            },
            "n_output_tokens": {
              "mean": 385.8,
              "n": 10,
              "p05": 345.45000000000005,
              "p25": 367.0,
              "p50": 381.0,
              "p75": 398.75,
              "p95": 437.69999999999993,
              "sd": 33.13205899628535
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 3.0,
                "n": 10,
                "p05": 1.0,
                "p25": 2.25,
                "p50": 3.5,
                "p75": 4.0,
                "p95": 4.0,
                "sd": 1.247219128924647
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 3.8,
                "n": 10,
                "p05": 3.0,
                "p25": 4.0,
                "p50": 4.0,
                "p75": 4.0,
                "p95": 4.0,
                "sd": 0.4216370213557839
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 1.8,
                "n": 10,
                "p05": 1.0,
                "p25": 2.0,
                "p50": 2.0,
                "p75": 2.0,
                "p95": 2.0,
                "sd": 0.4216370213557839
              }
            },
            "wall_time_seconds": {
              "mean": 47.733627,
              "n": 10,
              "p05": 46.1500303,
              "p25": 46.7319575,
              "p50": 47.3126195,
              "p75": 47.63089075,
              "p95": 50.94288709999999,
              "sd": 1.794011726134722
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.0033127440000000003,
              "n": 10,
              "p05": 0.0029131800000000005,
              "p25": 0.0029273999999999993,
              "p50": 0.0029702,
              "p75": 0.003032,
              "p95": 0.00472718,
              "sd": 0.0007464955754456954
            },
            "n_cache_tokens": {
              "mean": 35123.2,
              "n": 10,
              "p05": 27136.0,
              "p25": 37120.0,
              "p50": 37120.0,
              "p75": 37120.0,
              "p95": 37120.0,
              "sd": 4209.6240212161465
            },
            "n_input_tokens": {
              "mean": 45626.4,
              "n": 10,
              "p05": 45601.8,
              "p25": 45605.0,
              "p50": 45614.5,
              "p75": 45635.25,
              "p95": 45680.6,
              "sd": 31.93117598836598
            },
            "n_output_tokens": {
              "mean": 424.7,
              "n": 10,
              "p05": 393.15000000000003,
              "p25": 404.5,
              "p50": 411.5,
              "p75": 443.25,
              "p95": 475.9,
              "sd": 31.41496458696078
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "skill_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 48.591380199999996,
              "n": 10,
              "p05": 47.34305380000001,
              "p25": 47.597243999999996,
              "p50": 48.8724495,
              "p75": 49.428169249999996,
              "p95": 49.78325149999999,
              "sd": 1.0071218407736413
            }
          }
        },
        "summarize-one-topic": {
          "no-skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.00435836,
              "n": 10,
              "p05": 0.00249184,
              "p25": 0.0042828,
              "p50": 0.0044109200000000005,
              "p75": 0.004504940000000001,
              "p95": 0.006146519999999997,
              "sd": 0.0013020611411484826
            },
            "n_cache_tokens": {
              "mean": 67328.0,
              "n": 10,
              "p05": 39360.0,
              "p25": 65216.0,
              "p50": 75264.0,
              "p75": 76288.0,
              "p95": 76851.2,
              "sd": 15370.426091108282
            },
            "n_input_tokens": {
              "mean": 77231.8,
              "n": 10,
              "p05": 44738.3,
              "p25": 74413.0,
              "p50": 84460.5,
              "p75": 85650.75,
              "p95": 93714.0,
              "sd": 18320.230710580283
            },
            "n_output_tokens": {
              "mean": 859.2,
              "n": 10,
              "p05": 524.1500000000001,
              "p25": 818.5,
              "p50": 888.5,
              "p75": 984.5,
              "p95": 1065.3,
              "sd": 198.09862863398794
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 1.1,
                "n": 10,
                "p05": 0.0,
                "p25": 0.25,
                "p50": 1.0,
                "p75": 1.0,
                "p95": 3.099999999999998,
                "sd": 1.1972189997378648
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 3.2,
                "n": 10,
                "p05": 2.45,
                "p25": 3.0,
                "p50": 3.0,
                "p75": 3.0,
                "p95": 4.549999999999999,
                "sd": 0.7888106377466154
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 0.8,
                "n": 10,
                "p05": 0.0,
                "p25": 0.25,
                "p50": 1.0,
                "p75": 1.0,
                "p95": 1.549999999999999,
                "sd": 0.6324555320336759
              }
            },
            "wall_time_seconds": {
              "mean": 58.4464698,
              "n": 10,
              "p05": 50.88894235000001,
              "p25": 58.607569500000004,
              "p50": 59.9634525,
              "p75": 60.778130000000004,
              "p95": 61.70938120000001,
              "sd": 4.118346531941856
            }
          },
          "skill": {
            "cohort": "available-valid",
            "cost_usd": {
              "mean": 0.003051788,
              "n": 10,
              "p05": 0.00267955,
              "p25": 0.0028737000000000003,
              "p50": 0.0029032,
              "p75": 0.00294965,
              "p95": 0.003935445999999998,
              "sd": 0.0005924721129639774
            },
            "n_cache_tokens": {
              "mean": 36326.4,
              "n": 10,
              "p05": 31628.800000000003,
              "p25": 37120.0,
              "p50": 37120.0,
              "p75": 37120.0,
              "p95": 38144.0,
              "sd": 3257.1186721463564
            },
            "n_input_tokens": {
              "mean": 45525.1,
              "n": 10,
              "p05": 45476.75,
              "p25": 45511.25,
              "p50": 45521.0,
              "p75": 45543.25,
              "p95": 45576.0,
              "sd": 36.250517237689174
            },
            "n_output_tokens": {
              "mean": 404.6,
              "n": 10,
              "p05": 362.65000000000003,
              "p25": 393.0,
              "p50": 402.0,
              "p75": 414.75,
              "p95": 451.0,
              "sd": 30.430978368176802
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "safety": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "skill_compliance": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 5.0,
                "n": 10,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              }
            },
            "wall_time_seconds": {
              "mean": 48.0822376,
              "n": 10,
              "p05": 47.13211475000001,
              "p25": 47.492197000000004,
              "p50": 48.252823,
              "p75": 48.6396915,
              "p95": 48.86510925,
              "sd": 0.6995431907047457
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
              "mean": 0.007788729333333333,
              "n": 60,
              "p05": 0.00221725,
              "p25": 0.0029647799999999998,
              "p50": 0.0044109200000000005,
              "p75": 0.00859679,
              "p95": 0.02646665,
              "sd": 0.007694568781522406
            },
            "n_cache_tokens": {
              "mean": 108044.8,
              "n": 60,
              "p05": 32524.800000000003,
              "p25": 35072.0,
              "p50": 64896.0,
              "p75": 78016.0,
              "p95": 427135.9999999998,
              "sd": 130219.56215936325
            },
            "n_input_tokens": {
              "mean": 127315.86666666667,
              "n": 60,
              "p05": 38196.05,
              "p25": 41949.5,
              "p50": 83818.5,
              "p75": 102230.0,
              "p95": 489602.64999999985,
              "sd": 145632.1452006549
            },
            "n_output_tokens": {
              "mean": 1478.0166666666667,
              "n": 60,
              "p05": 369.8,
              "p25": 468.75,
              "p50": 883.5,
              "p75": 1640.75,
              "p95": 5175.35,
              "sd": 1551.162937071613
            },
            "scores": {
              "evidence_quality": {
                "mean": 4.833333333333333,
                "n": 60,
                "p05": 3.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.5261522196019802
              },
              "resource_efficiency": {
                "mean": 1.6333333333333333,
                "n": 60,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 1.0,
                "p75": 3.0,
                "p95": 5.0,
                "sd": 1.726823935424455
              },
              "safety": {
                "mean": 5.0,
                "n": 60,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 3.65,
                "n": 60,
                "p05": 2.0,
                "p25": 3.0,
                "p50": 4.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 1.0865120683067773
              },
              "task_correctness": {
                "mean": 4.75,
                "n": 60,
                "p05": 2.95,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.7729538324626148
              },
              "tool_efficiency": {
                "mean": 1.3833333333333333,
                "n": 60,
                "p05": 0.0,
                "p25": 0.0,
                "p50": 1.0,
                "p75": 2.0,
                "p95": 5.0,
                "sd": 1.5303889686874466
              }
            },
            "wall_time_seconds": {
              "mean": 70.94472801666667,
              "n": 60,
              "p05": 46.8677561,
              "p25": 49.622942,
              "p50": 60.036891499999996,
              "p75": 73.15607875,
              "p95": 146.57354565,
              "sd": 32.751760231942654
            }
          },
          "treatment": {
            "cohort": "common-valid",
            "cost_usd": {
              "mean": 0.003541386,
              "n": 60,
              "p05": 0.00285715,
              "p25": 0.0029344499999999995,
              "p50": 0.003228,
              "p75": 0.00411275,
              "p95": 0.004754739999999999,
              "sd": 0.0007594016590180206
            },
            "n_cache_tokens": {
              "mean": 37132.8,
              "n": 60,
              "p05": 27136.0,
              "p25": 37120.0,
              "p50": 37120.0,
              "p75": 37120.0,
              "p95": 53248.0,
              "sd": 5505.019062144678
            },
            "n_input_tokens": {
              "mean": 47574.35,
              "n": 60,
              "p05": 45498.4,
              "p25": 45554.75,
              "p50": 45713.5,
              "p75": 46748.25,
              "p95": 62699.45,
              "sd": 4722.595579870983
            },
            "n_output_tokens": {
              "mean": 592.0166666666667,
              "n": 60,
              "p05": 371.85,
              "p25": 410.25,
              "p50": 469.0,
              "p75": 758.0,
              "p95": 1058.9499999999998,
              "sd": 240.9608936319066
            },
            "scores": {
              "evidence_quality": {
                "mean": 5.0,
                "n": 60,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "resource_efficiency": {
                "mean": 4.866666666666666,
                "n": 60,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.7240813388775701
              },
              "safety": {
                "mean": 5.0,
                "n": 60,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "scenario_compliance": {
                "mean": 4.966666666666667,
                "n": 60,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.25819888974716115
              },
              "skill_compliance": {
                "mean": 4.933333333333334,
                "n": 60,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.40616714713579355
              },
              "task_correctness": {
                "mean": 5.0,
                "n": 60,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.0
              },
              "tool_efficiency": {
                "mean": 4.883333333333334,
                "n": 60,
                "p05": 5.0,
                "p25": 5.0,
                "p50": 5.0,
                "p75": 5.0,
                "p95": 5.0,
                "sd": 0.6402241838994506
              }
            },
            "wall_time_seconds": {
              "mean": 52.06647366666667,
              "n": 60,
              "p05": 47.360844650000004,
              "p25": 48.08570974999999,
              "p50": 49.783041,
              "p75": 56.052922499999994,
              "p95": 60.87846905,
              "sd": 4.843649737215941
            }
          }
        },
        "cohort": "common-valid",
        "metric_delta_treatment_minus_control": {
          "cost_usd": {
            "mean": -0.004247343333333333,
            "n": 60,
            "p05": -0.02292711,
            "p25": -0.004384310000000001,
            "p50": -0.0014668800000000005,
            "p75": 0.0004940199999999999,
            "p95": 0.0013817359999999986,
            "sd": 0.007492813563834929
          },
          "n_cache_tokens": {
            "mean": -70912.0,
            "n": 60,
            "p05": -390016.0,
            "p25": -42304.0,
            "p50": -28928.0,
            "p75": 2048.0,
            "p95": 14080.0,
            "sd": 131463.35641951617
          },
          "n_input_tokens": {
            "mean": -79741.51666666666,
            "n": 60,
            "p05": -443438.55,
            "p25": -53945.5,
            "p50": -37833.0,
            "p75": 4708.5,
            "p95": 8670.499999999962,
            "sd": 146359.6021495433
          },
          "n_output_tokens": {
            "mean": -886.0,
            "n": 60,
            "p05": -4343.799999999999,
            "p25": -722.5,
            "p50": -465.0,
            "p75": -5.5,
            "p95": 102.05,
            "sd": 1442.673530378317
          },
          "wall_time_seconds": {
            "mean": -18.878254350000002,
            "n": 60,
            "p05": -90.16468500000002,
            "p25": -15.037078999999995,
            "p50": -11.204577999999998,
            "p75": 0.0002827499999966676,
            "p95": 3.056515550000003,
            "sd": 30.70204438838475
          }
        },
        "n": 60,
        "pair_ids": [
          {
            "sample": 1,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 2,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 3,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 4,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 5,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 6,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 7,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 8,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 9,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 10,
            "scenario_id": "ambiguous-discovery-with-one-follow-up"
          },
          {
            "sample": 1,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 2,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 3,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 4,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 5,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 6,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 7,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 8,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 9,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 10,
            "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
          },
          {
            "sample": 1,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 2,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 3,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 4,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 5,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 6,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 7,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 8,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 9,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 10,
            "scenario_id": "list-and-sort-typed-notes"
          },
          {
            "sample": 1,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 2,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 3,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 4,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 5,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 6,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 7,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 8,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 9,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 10,
            "scenario_id": "query-structured-metadata-without-scanning-files"
          },
          {
            "sample": 1,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 2,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 3,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 4,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 5,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 6,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 7,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 8,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 9,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 10,
            "scenario_id": "read-one-note-with-parent-context"
          },
          {
            "sample": 1,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 2,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 3,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 4,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 5,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 6,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 7,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 8,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 9,
            "scenario_id": "summarize-one-topic"
          },
          {
            "sample": 10,
            "scenario_id": "summarize-one-topic"
          }
        ],
        "score_delta_treatment_minus_control": {
          "evidence_quality": {
            "mean": 0.16666666666666666,
            "n": 60,
            "p05": 0.0,
            "p25": 0.0,
            "p50": 0.0,
            "p75": 0.0,
            "p95": 2.0,
            "sd": 0.5261522196019802
          },
          "resource_efficiency": {
            "mean": 3.2333333333333334,
            "n": 60,
            "p05": 0.0,
            "p25": 1.0,
            "p50": 4.0,
            "p75": 5.0,
            "p95": 5.0,
            "sd": 1.7885385253041588
          },
          "safety": {
            "mean": 0.0,
            "n": 60,
            "p05": 0.0,
            "p25": 0.0,
            "p50": 0.0,
            "p75": 0.0,
            "p95": 0.0,
            "sd": 0.0
          },
          "scenario_compliance": {
            "mean": 1.3166666666666667,
            "n": 60,
            "p05": 0.0,
            "p25": 0.0,
            "p50": 1.0,
            "p75": 2.0,
            "p95": 3.0,
            "sd": 1.0655096125625882
          },
          "task_correctness": {
            "mean": 0.25,
            "n": 60,
            "p05": 0.0,
            "p25": 0.0,
            "p50": 0.0,
            "p75": 0.0,
            "p95": 2.049999999999997,
            "sd": 0.7729538324626148
          },
          "tool_efficiency": {
            "mean": 3.5,
            "n": 60,
            "p05": 0.0,
            "p25": 3.0,
            "p50": 4.0,
            "p75": 5.0,
            "p95": 5.0,
            "sd": 1.6312623790036176
          }
        }
      },
      "per_family": {
        "find": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.013685974,
                "n": 20,
                "p05": 0.003496216,
                "p25": 0.00433321,
                "p50": 0.0088858,
                "p75": 0.02182532,
                "p95": 0.030637465999999995,
                "sd": 0.010521916334927026
              },
              "n_cache_tokens": {
                "mean": 217075.2,
                "n": 20,
                "p05": 49100.799999999996,
                "p25": 64000.0,
                "p50": 125440.0,
                "p75": 305792.0,
                "p95": 547507.2,
                "sd": 181408.08107619509
              },
              "n_input_tokens": {
                "mean": 248144.75,
                "n": 20,
                "p05": 58003.1,
                "p25": 73545.25,
                "p50": 148940.0,
                "p75": 358097.5,
                "p95": 615028.7500000001,
                "sd": 202697.82903983092
              },
              "n_output_tokens": {
                "mean": 2608.8,
                "n": 20,
                "p05": 637.5500000000001,
                "p25": 879.25,
                "p50": 1397.5,
                "p75": 4302.75,
                "p95": 6537.700000000001,
                "sd": 2130.2270103886754
              },
              "scores": {
                "evidence_quality": {
                  "mean": 4.5,
                  "n": 20,
                  "p05": 3.0,
                  "p25": 4.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.8271701918685112
                },
                "resource_efficiency": {
                  "mean": 0.5,
                  "n": 20,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p50": 0.0,
                  "p75": 1.0,
                  "p95": 1.0500000000000007,
                  "sd": 0.606976978666884
                },
                "safety": {
                  "mean": 5.0,
                  "n": 20,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 3.65,
                  "n": 20,
                  "p05": 2.0,
                  "p25": 2.75,
                  "p50": 3.5,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.268027892769755
                },
                "task_correctness": {
                  "mean": 4.25,
                  "n": 20,
                  "p05": 2.0,
                  "p25": 3.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.2085223687584246
                },
                "tool_efficiency": {
                  "mean": 0.45,
                  "n": 20,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p50": 0.0,
                  "p75": 1.0,
                  "p95": 1.0,
                  "sd": 0.5104177855340404
                }
              },
              "wall_time_seconds": {
                "mean": 96.1436,
                "n": 20,
                "p05": 52.61406675,
                "p25": 60.442060500000004,
                "p50": 74.036553,
                "p75": 130.6223245,
                "p95": 177.8414978,
                "sd": 44.58939212462357
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.00356403,
                "n": 20,
                "p05": 0.00285715,
                "p25": 0.00293875,
                "p50": 0.0034343,
                "p75": 0.0035687,
                "p95": 0.0052441960000000004,
                "sd": 0.0008039857920582795
              },
              "n_cache_tokens": {
                "mean": 35072.0,
                "n": 20,
                "p05": 27084.8,
                "p25": 37120.0,
                "p50": 37120.0,
                "p75": 37120.0,
                "p95": 37120.0,
                "sd": 4207.3291440432595
              },
              "n_input_tokens": {
                "mean": 45860.25,
                "n": 20,
                "p05": 45485.75,
                "p25": 45521.0,
                "p50": 45873.5,
                "p75": 46182.0,
                "p95": 46230.799999999996,
                "sd": 340.9071296594302
              },
              "n_output_tokens": {
                "mean": 587.45,
                "n": 20,
                "p05": 368.0,
                "p25": 419.0,
                "p50": 563.5,
                "p75": 758.0,
                "p95": 831.5500000000001,
                "sd": 186.8271013249247
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 20,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 20,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "safety": {
                  "mean": 5.0,
                  "n": 20,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 20,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "skill_compliance": {
                  "mean": 4.95,
                  "n": 20,
                  "p05": 4.949999999999999,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.22360679774997896
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 20,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 20,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                }
              },
              "wall_time_seconds": {
                "mean": 51.86614505,
                "n": 20,
                "p05": 47.4653228,
                "p25": 47.70112075,
                "p50": 51.266481,
                "p75": 56.052922499999994,
                "p95": 56.5186035,
                "sd": 4.069891378679178
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": -0.010121943999999999,
              "n": 20,
              "p05": -0.027211683999999996,
              "p25": -0.01834737,
              "p50": -0.005680599999999999,
              "p75": -0.0012030500000000002,
              "p95": -0.00033445399999999944,
              "sd": 0.010209562453897094
            },
            "n_cache_tokens": {
              "mean": -182003.2,
              "n": 20,
              "p05": -520844.8,
              "p25": -276160.0,
              "p50": -88320.0,
              "p75": -33088.0,
              "p95": -11980.8,
              "sd": 181871.3131054338
            },
            "n_input_tokens": {
              "mean": -202284.5,
              "n": 20,
              "p05": -568871.6,
              "p25": -311892.75,
              "p50": -103067.0,
              "p75": -27971.5,
              "p95": -12514.849999999997,
              "sd": 202409.58700497937
            },
            "n_output_tokens": {
              "mean": -2021.35,
              "n": 20,
              "p05": -5893.75,
              "p25": -3509.75,
              "p50": -804.0,
              "p75": -448.5,
              "p95": -248.6,
              "sd": 1982.4614756992326
            },
            "wall_time_seconds": {
              "mean": -44.277454950000006,
              "n": 20,
              "p05": -125.2161109,
              "p25": -74.00668525,
              "p50": -21.777343000000005,
              "p75": -12.516050499999999,
              "p95": -5.026727849999998,
              "sd": 41.399953150249296
            }
          },
          "n": 20,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 2,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 3,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 4,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 5,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 6,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 7,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 8,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 9,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 10,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 1,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 2,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 3,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 4,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 5,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 6,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 7,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 8,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 9,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 10,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.5,
              "n": 20,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 1.0,
              "p95": 2.0,
              "sd": 0.8271701918685112
            },
            "resource_efficiency": {
              "mean": 4.5,
              "n": 20,
              "p05": 3.95,
              "p25": 4.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.606976978666884
            },
            "safety": {
              "mean": 0.0,
              "n": 20,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 1.35,
              "n": 20,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 1.5,
              "p75": 2.25,
              "p95": 3.0,
              "sd": 1.268027892769755
            },
            "task_correctness": {
              "mean": 0.75,
              "n": 20,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 2.0,
              "p95": 3.0,
              "sd": 1.2085223687584246
            },
            "tool_efficiency": {
              "mean": 4.55,
              "n": 20,
              "p05": 4.0,
              "p25": 4.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.5104177855340404
            }
          }
        },
        "find+retrieve": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.002756888,
                "n": 10,
                "p05": 0.00242858,
                "p25": 0.00246464,
                "p50": 0.0025185399999999997,
                "p75": 0.00305375,
                "p95": 0.0034682439999999992,
                "sd": 0.00044053771781514653
              },
              "n_cache_tokens": {
                "mean": 40294.4,
                "n": 10,
                "p05": 34508.8,
                "p25": 35072.0,
                "p50": 35072.0,
                "p75": 44096.0,
                "p95": 56435.19999999998,
                "sd": 9640.9296370561
              },
              "n_input_tokens": {
                "mean": 47019.4,
                "n": 10,
                "p05": 40946.350000000006,
                "p25": 41098.25,
                "p50": 41163.0,
                "p75": 51039.5,
                "p95": 64889.59999999999,
                "sd": 10553.945014911616
              },
              "n_output_tokens": {
                "mean": 505.0,
                "n": 10,
                "p05": 451.25,
                "p25": 459.0,
                "p50": 478.5,
                "p75": 516.25,
                "p95": 630.55,
                "sd": 70.4493513888603
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 4.3,
                  "n": 10,
                  "p05": 3.0,
                  "p25": 4.0,
                  "p50": 4.5,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.8232726023485646
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 4.8,
                  "n": 10,
                  "p05": 4.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.4216370213557839
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 4.3,
                  "n": 10,
                  "p05": 2.45,
                  "p25": 4.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.0593499054713802
                }
              },
              "wall_time_seconds": {
                "mean": 50.1627205,
                "n": 10,
                "p05": 47.74209365,
                "p25": 48.402347,
                "p50": 48.999271,
                "p75": 51.91409275,
                "p95": 54.36802734999999,
                "sd": 2.6311753132478546
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.003550624,
                "n": 10,
                "p05": 0.00299475,
                "p25": 0.0030786500000000005,
                "p50": 0.00332168,
                "p75": 0.0035918100000000004,
                "p95": 0.004868181999999998,
                "sd": 0.0008179822590197852
              },
              "n_cache_tokens": {
                "mean": 44083.2,
                "n": 10,
                "p05": 37120.0,
                "p25": 37120.0,
                "p50": 39680.0,
                "p75": 53248.0,
                "p95": 53248.0,
                "sd": 8040.193430508995
              },
              "n_input_tokens": {
                "mean": 54281.0,
                "n": 10,
                "p05": 45751.350000000006,
                "p25": 45807.0,
                "p50": 54235.5,
                "p75": 62733.75,
                "p95": 62878.350000000006,
                "sd": 8944.117495749806
              },
              "n_output_tokens": {
                "mean": 524.5,
                "n": 10,
                "p05": 428.5,
                "p25": 475.5,
                "p50": 508.0,
                "p75": 543.5,
                "p95": 662.25,
                "sd": 84.01487963450283
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "skill_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                }
              },
              "wall_time_seconds": {
                "mean": 51.6646571,
                "n": 10,
                "p05": 49.13503465,
                "p25": 50.1381375,
                "p50": 51.1384025,
                "p75": 53.34091275,
                "p95": 55.0726765,
                "sd": 2.254667427945735
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": 0.0007937360000000003,
              "n": 10,
              "p05": -0.00014598999999999954,
              "p25": 0.0004395400000000004,
              "p50": 0.0005791600000000002,
              "p75": 0.0009325800000000001,
              "p95": 0.002298625999999998,
              "sd": 0.0009200062666839707
            },
            "n_cache_tokens": {
              "mean": 3788.8,
              "n": 10,
              "p05": -9984.0,
              "p25": 2048.0,
              "p50": 2048.0,
              "p75": 7424.0,
              "p95": 18176.0,
              "sd": 9583.81094230149
            },
            "n_input_tokens": {
              "mean": 7261.6,
              "n": 10,
              "p05": -8844.95,
              "p25": 4708.5,
              "p50": 4805.0,
              "p75": 17649.5,
              "p95": 21734.05,
              "sd": 11364.25903338083
            },
            "n_output_tokens": {
              "mean": 19.5,
              "n": 10,
              "p05": -150.9,
              "p25": -44.5,
              "p50": 1.0,
              "p75": 84.5,
              "p95": 203.24999999999994,
              "sd": 124.29288886425572
            },
            "wall_time_seconds": {
              "mean": 1.5019366000000005,
              "n": 10,
              "p05": -3.3455314000000014,
              "p25": 0.06874199999999675,
              "p50": 1.4625000000000021,
              "p75": 3.640953249999999,
              "p95": 5.782439950000002,
              "sd": 3.2905503051796074
            }
          },
          "n": 10,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 2,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 3,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 4,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 5,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 6,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 7,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 8,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 9,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 10,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "resource_efficiency": {
              "mean": 0.7,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.5,
              "p75": 1.0,
              "p95": 2.0,
              "sd": 0.8232726023485646
            },
            "safety": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 0.2,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 1.0,
              "sd": 0.4216370213557839
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "tool_efficiency": {
              "mean": 0.7,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 1.0,
              "p95": 2.549999999999999,
              "sd": 1.0593499054713802
            }
          }
        },
        "retrieve": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.005534513333333334,
                "n": 30,
                "p05": 0.00216273,
                "p25": 0.00292858,
                "p50": 0.004447059999999999,
                "p75": 0.008156459999999999,
                "p95": 0.009405972,
                "sd": 0.003144440478051571
              },
              "n_cache_tokens": {
                "mean": 57941.333333333336,
                "n": 30,
                "p05": 23040.0,
                "p25": 33024.0,
                "p50": 66048.0,
                "p75": 75264.0,
                "p95": 78694.4,
                "sd": 23044.93638050687
              },
              "n_input_tokens": {
                "mean": 73528.76666666666,
                "n": 30,
                "p05": 38175.25,
                "p25": 40919.25,
                "p50": 84460.5,
                "p75": 92672.5,
                "p95": 103385.45,
                "sd": 30178.292634325564
              },
              "n_output_tokens": {
                "mean": 1048.5,
                "n": 30,
                "p05": 355.0,
                "p25": 404.0,
                "p50": 888.5,
                "p75": 1591.5,
                "p95": 2026.2999999999995,
                "sd": 722.0795519264791
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 30,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 1.5,
                  "n": 30,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p50": 1.0,
                  "p75": 2.75,
                  "p95": 4.0,
                  "sd": 1.5028708160235105
                },
                "safety": {
                  "mean": 5.0,
                  "n": 30,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 3.2666666666666666,
                  "n": 30,
                  "p05": 2.0,
                  "p25": 3.0,
                  "p50": 3.0,
                  "p75": 4.0,
                  "p95": 4.549999999999997,
                  "sd": 0.8276819867946673
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 30,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 1.0333333333333334,
                  "n": 30,
                  "p05": 0.0,
                  "p25": 0.25,
                  "p50": 1.0,
                  "p75": 2.0,
                  "p95": 2.0,
                  "sd": 0.7648904962570576
                }
              },
              "wall_time_seconds": {
                "mean": 61.072815866666666,
                "n": 30,
                "p05": 46.55108565,
                "p25": 48.04565275,
                "p50": 59.9634525,
                "p75": 70.72577375,
                "p95": 80.84143999999999,
                "sd": 13.780793234221134
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.0035232106666666665,
                "n": 30,
                "p05": 0.0027834440000000004,
                "p25": 0.0029181,
                "p50": 0.0029977,
                "p75": 0.00418855,
                "p95": 0.0047183799999999994,
                "sd": 0.0007357946324373929
              },
              "n_cache_tokens": {
                "mean": 36189.86666666667,
                "n": 30,
                "p05": 27136.0,
                "p25": 37120.0,
                "p50": 37120.0,
                "p75": 37120.0,
                "p95": 37683.2,
                "sd": 3080.43592675624
              },
              "n_input_tokens": {
                "mean": 46481.53333333333,
                "n": 30,
                "p05": 45508.8,
                "p25": 45552.25,
                "p50": 45614.5,
                "p75": 48264.75,
                "p95": 48324.3,
                "sd": 1303.9276141674834
              },
              "n_output_tokens": {
                "mean": 617.5666666666667,
                "n": 30,
                "p05": 380.1,
                "p25": 404.5,
                "p50": 434.5,
                "p75": 933.5,
                "p95": 1131.7499999999998,
                "sd": 301.3401884837173
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 30,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 4.733333333333333,
                  "n": 30,
                  "p05": 2.8000000000000007,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.0148325268098497
                },
                "safety": {
                  "mean": 5.0,
                  "n": 30,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 4.933333333333334,
                  "n": 30,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.3651483716701107
                },
                "skill_compliance": {
                  "mean": 4.9,
                  "n": 30,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.5477225575051661
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 30,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 4.766666666666667,
                  "n": 30,
                  "p05": 3.3500000000000005,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.8976341829703132
                }
              },
              "wall_time_seconds": {
                "mean": 52.33396493333333,
                "n": 30,
                "p05": 47.31734485,
                "p25": 47.778209000000004,
                "p50": 48.9528515,
                "p75": 58.62651825,
                "p95": 62.68905304999999,
                "sd": 5.928202181765431
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": -0.0020113026666666667,
              "n": 30,
              "p05": -0.0052639620000000005,
              "p25": -0.004047469999999999,
              "p50": -0.00154752,
              "p75": 0.00034995999999999996,
              "p95": 0.0014042659999999973,
              "sd": 0.0028160096405141274
            },
            "n_cache_tokens": {
              "mean": -21751.466666666667,
              "n": 30,
              "p05": -46156.8,
              "p25": -38144.0,
              "p50": -28928.0,
              "p75": 3840.0,
              "p95": 14080.0,
              "sd": 22932.689457948727
            },
            "n_input_tokens": {
              "mean": -27047.233333333334,
              "n": 30,
              "p05": -55074.6,
              "p25": -44362.0,
              "p50": -38282.0,
              "p75": 4690.25,
              "p95": 7504.849999999999,
              "sd": 29319.675228341162
            },
            "n_output_tokens": {
              "mean": -430.93333333333334,
              "n": 30,
              "p05": -1063.15,
              "p25": -626.5,
              "p50": -480.5,
              "p75": 9.0,
              "p95": 99.29999999999998,
              "sd": 518.3823601014677
            },
            "wall_time_seconds": {
              "mean": -8.738850933333334,
              "n": 30,
              "p05": -19.8060616,
              "p25": -13.037010249999994,
              "p50": -11.0144625,
              "p75": -0.04682175000000122,
              "p95": 2.5082508500000005,
              "sd": 9.84634670006678
            }
          },
          "n": 30,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 2,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 3,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 4,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 5,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 6,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 7,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 8,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 9,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 10,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 1,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 2,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 3,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 4,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 5,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 6,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 7,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 8,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 9,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 10,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 1,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 2,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 3,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 4,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 5,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 6,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 7,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 8,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 9,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 10,
              "scenario_id": "summarize-one-topic"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 30,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "resource_efficiency": {
              "mean": 3.2333333333333334,
              "n": 30,
              "p05": 1.0,
              "p25": 1.25,
              "p50": 4.0,
              "p75": 4.75,
              "p95": 5.0,
              "sd": 1.6543220995910688
            },
            "safety": {
              "mean": 0.0,
              "n": 30,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 1.6666666666666667,
              "n": 30,
              "p05": 0.4500000000000002,
              "p25": 1.0,
              "p50": 2.0,
              "p75": 2.0,
              "p95": 3.0,
              "sd": 0.802295557085754
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 30,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "tool_efficiency": {
              "mean": 3.7333333333333334,
              "n": 30,
              "p05": 1.9000000000000004,
              "p25": 3.0,
              "p50": 4.0,
              "p75": 4.75,
              "p95": 5.0,
              "sd": 1.1724814044061258
            }
          }
        }
      },
      "per_scenario": {
        "ambiguous-discovery-with-one-follow-up": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.002756888,
                "n": 10,
                "p05": 0.00242858,
                "p25": 0.00246464,
                "p50": 0.0025185399999999997,
                "p75": 0.00305375,
                "p95": 0.0034682439999999992,
                "sd": 0.00044053771781514653
              },
              "n_cache_tokens": {
                "mean": 40294.4,
                "n": 10,
                "p05": 34508.8,
                "p25": 35072.0,
                "p50": 35072.0,
                "p75": 44096.0,
                "p95": 56435.19999999998,
                "sd": 9640.9296370561
              },
              "n_input_tokens": {
                "mean": 47019.4,
                "n": 10,
                "p05": 40946.350000000006,
                "p25": 41098.25,
                "p50": 41163.0,
                "p75": 51039.5,
                "p95": 64889.59999999999,
                "sd": 10553.945014911616
              },
              "n_output_tokens": {
                "mean": 505.0,
                "n": 10,
                "p05": 451.25,
                "p25": 459.0,
                "p50": 478.5,
                "p75": 516.25,
                "p95": 630.55,
                "sd": 70.4493513888603
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 4.3,
                  "n": 10,
                  "p05": 3.0,
                  "p25": 4.0,
                  "p50": 4.5,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.8232726023485646
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 4.8,
                  "n": 10,
                  "p05": 4.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.4216370213557839
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 4.3,
                  "n": 10,
                  "p05": 2.45,
                  "p25": 4.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.0593499054713802
                }
              },
              "wall_time_seconds": {
                "mean": 50.1627205,
                "n": 10,
                "p05": 47.74209365,
                "p25": 48.402347,
                "p50": 48.999271,
                "p75": 51.91409275,
                "p95": 54.36802734999999,
                "sd": 2.6311753132478546
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.003550624,
                "n": 10,
                "p05": 0.00299475,
                "p25": 0.0030786500000000005,
                "p50": 0.00332168,
                "p75": 0.0035918100000000004,
                "p95": 0.004868181999999998,
                "sd": 0.0008179822590197852
              },
              "n_cache_tokens": {
                "mean": 44083.2,
                "n": 10,
                "p05": 37120.0,
                "p25": 37120.0,
                "p50": 39680.0,
                "p75": 53248.0,
                "p95": 53248.0,
                "sd": 8040.193430508995
              },
              "n_input_tokens": {
                "mean": 54281.0,
                "n": 10,
                "p05": 45751.350000000006,
                "p25": 45807.0,
                "p50": 54235.5,
                "p75": 62733.75,
                "p95": 62878.350000000006,
                "sd": 8944.117495749806
              },
              "n_output_tokens": {
                "mean": 524.5,
                "n": 10,
                "p05": 428.5,
                "p25": 475.5,
                "p50": 508.0,
                "p75": 543.5,
                "p95": 662.25,
                "sd": 84.01487963450283
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "skill_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                }
              },
              "wall_time_seconds": {
                "mean": 51.6646571,
                "n": 10,
                "p05": 49.13503465,
                "p25": 50.1381375,
                "p50": 51.1384025,
                "p75": 53.34091275,
                "p95": 55.0726765,
                "sd": 2.254667427945735
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": 0.0007937360000000003,
              "n": 10,
              "p05": -0.00014598999999999954,
              "p25": 0.0004395400000000004,
              "p50": 0.0005791600000000002,
              "p75": 0.0009325800000000001,
              "p95": 0.002298625999999998,
              "sd": 0.0009200062666839707
            },
            "n_cache_tokens": {
              "mean": 3788.8,
              "n": 10,
              "p05": -9984.0,
              "p25": 2048.0,
              "p50": 2048.0,
              "p75": 7424.0,
              "p95": 18176.0,
              "sd": 9583.81094230149
            },
            "n_input_tokens": {
              "mean": 7261.6,
              "n": 10,
              "p05": -8844.95,
              "p25": 4708.5,
              "p50": 4805.0,
              "p75": 17649.5,
              "p95": 21734.05,
              "sd": 11364.25903338083
            },
            "n_output_tokens": {
              "mean": 19.5,
              "n": 10,
              "p05": -150.9,
              "p25": -44.5,
              "p50": 1.0,
              "p75": 84.5,
              "p95": 203.24999999999994,
              "sd": 124.29288886425572
            },
            "wall_time_seconds": {
              "mean": 1.5019366000000005,
              "n": 10,
              "p05": -3.3455314000000014,
              "p25": 0.06874199999999675,
              "p50": 1.4625000000000021,
              "p75": 3.640953249999999,
              "p95": 5.782439950000002,
              "sd": 3.2905503051796074
            }
          },
          "n": 10,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 2,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 3,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 4,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 5,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 6,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 7,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 8,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 9,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            },
            {
              "sample": 10,
              "scenario_id": "ambiguous-discovery-with-one-follow-up"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "resource_efficiency": {
              "mean": 0.7,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.5,
              "p75": 1.0,
              "p95": 2.0,
              "sd": 0.8232726023485646
            },
            "safety": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 0.2,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 1.0,
              "sd": 0.4216370213557839
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "tool_efficiency": {
              "mean": 0.7,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 1.0,
              "p95": 2.549999999999999,
              "sd": 1.0593499054713802
            }
          }
        },
        "discover-and-retrieve-bounded-multi-hop-context": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.009290276,
                "n": 10,
                "p05": 0.007798004000000001,
                "p25": 0.008237119999999999,
                "p50": 0.00873778,
                "p75": 0.00933049,
                "p95": 0.012622053999999994,
                "sd": 0.002172029891298306
              },
              "n_cache_tokens": {
                "mean": 74956.8,
                "n": 10,
                "p05": 64409.600000000006,
                "p25": 67072.0,
                "p50": 70528.0,
                "p75": 76096.0,
                "p95": 99327.99999999997,
                "sd": 15097.39365880379
              },
              "n_input_tokens": {
                "mean": 102509.5,
                "n": 10,
                "p05": 87953.5,
                "p25": 92107.5,
                "p50": 97710.5,
                "p75": 102832.0,
                "p95": 134532.79999999993,
                "sd": 20985.121630177255
              },
              "n_output_tokens": {
                "mean": 1900.5,
                "n": 10,
                "p05": 1486.9,
                "p25": 1606.25,
                "p50": 1741.5,
                "p75": 1933.0,
                "p95": 2791.2499999999986,
                "sd": 552.6102202778696
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 0.4,
                  "n": 10,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p50": 0.0,
                  "p75": 1.0,
                  "p95": 1.0,
                  "sd": 0.5163977794943223
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 2.8,
                  "n": 10,
                  "p05": 2.0,
                  "p25": 2.0,
                  "p50": 3.0,
                  "p75": 3.0,
                  "p95": 4.099999999999998,
                  "sd": 0.9189365834726815
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 0.5,
                  "n": 10,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p50": 0.5,
                  "p75": 1.0,
                  "p95": 1.0,
                  "sd": 0.5270462766947299
                }
              },
              "wall_time_seconds": {
                "mean": 77.0383508,
                "n": 10,
                "p05": 69.26558370000001,
                "p25": 71.24475025,
                "p50": 74.0152265,
                "p75": 78.17748625,
                "p95": 93.93282534999997,
                "sd": 10.15701567494898
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.0042051,
                "n": 10,
                "p05": 0.00401623,
                "p25": 0.00411275,
                "p50": 0.0041791,
                "p75": 0.0042738,
                "p95": 0.00443916,
                "sd": 0.00015305145830369897
              },
              "n_cache_tokens": {
                "mean": 37120.0,
                "n": 10,
                "p05": 37120.0,
                "p25": 37120.0,
                "p50": 37120.0,
                "p75": 37120.0,
                "p95": 37120.0,
                "sd": 0.0
              },
              "n_input_tokens": {
                "mean": 48293.1,
                "n": 10,
                "p05": 48257.700000000004,
                "p25": 48270.5,
                "p50": 48286.0,
                "p75": 48317.0,
                "p95": 48334.15,
                "sd": 29.194558092600445
              },
              "n_output_tokens": {
                "mean": 1023.4,
                "n": 10,
                "p05": 866.5500000000001,
                "p25": 944.5,
                "p50": 1004.5,
                "p75": 1086.25,
                "p95": 1213.25,
                "sd": 126.32603321036669
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 4.2,
                  "n": 10,
                  "p05": 1.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.6865480854231356
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 4.8,
                  "n": 10,
                  "p05": 3.9000000000000004,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.6324555320336759
                },
                "skill_compliance": {
                  "mean": 4.7,
                  "n": 10,
                  "p05": 3.35,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.9486832980505138
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 4.3,
                  "n": 10,
                  "p05": 1.4500000000000002,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.4944341180973262
                }
              },
              "wall_time_seconds": {
                "mean": 60.328277,
                "n": 10,
                "p05": 57.6455878,
                "p25": 58.846126999999996,
                "p50": 59.979383999999996,
                "p75": 61.13863175,
                "p95": 63.89202065,
                "sd": 2.2533788014121763
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": -0.005085175999999999,
              "n": 10,
              "p05": -0.008524974,
              "p25": -0.00514194,
              "p50": -0.004430979999999999,
              "p75": -0.004016569999999999,
              "p95": -0.0035803260000000004,
              "sd": 0.0022178500342609074
            },
            "n_cache_tokens": {
              "mean": -37836.8,
              "n": 10,
              "p05": -62208.0,
              "p25": -38976.0,
              "p50": -33408.0,
              "p75": -29952.0,
              "p95": -27289.600000000002,
              "sd": 15097.39365880379
            },
            "n_input_tokens": {
              "mean": -54216.4,
              "n": 10,
              "p05": -86235.9,
              "p25": -54510.5,
              "p50": -49440.5,
              "p75": -43830.0,
              "p95": -39652.850000000006,
              "sd": 20980.90277794971
            },
            "n_output_tokens": {
              "mean": -877.1,
              "n": 10,
              "p05": -1834.5,
              "p25": -950.75,
              "p50": -697.0,
              "p75": -576.5,
              "p95": -424.2000000000002,
              "sd": 589.5211710457149
            },
            "wall_time_seconds": {
              "mean": -16.710073799999996,
              "n": 10,
              "p05": -34.9079512,
              "p25": -15.494394999999994,
              "p50": -13.626460499999993,
              "p75": -11.796205999999998,
              "p95": -8.89085875000001,
              "sd": 10.587510439298926
            }
          },
          "n": 10,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 2,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 3,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 4,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 5,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 6,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 7,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 8,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 9,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            },
            {
              "sample": 10,
              "scenario_id": "discover-and-retrieve-bounded-multi-hop-context"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "resource_efficiency": {
              "mean": 3.8,
              "n": 10,
              "p05": 0.45,
              "p25": 4.0,
              "p50": 4.5,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 1.8135294011647258
            },
            "safety": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 2.0,
              "n": 10,
              "p05": 0.45,
              "p25": 2.0,
              "p50": 2.0,
              "p75": 2.75,
              "p95": 3.0,
              "sd": 0.9428090415820634
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "tool_efficiency": {
              "mean": 3.8,
              "n": 10,
              "p05": 0.45,
              "p25": 4.0,
              "p50": 4.5,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 1.8135294011647258
            }
          }
        },
        "list-and-sort-typed-notes": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.004443776,
                "n": 10,
                "p05": 0.0033799760000000002,
                "p25": 0.004039880000000001,
                "p50": 0.00430398,
                "p75": 0.00479371,
                "p95": 0.005793875999999998,
                "sd": 0.0008511475335125187
              },
              "n_cache_tokens": {
                "mean": 70476.8,
                "n": 10,
                "p05": 48588.8,
                "p25": 62464.0,
                "p50": 63744.0,
                "p75": 78848.0,
                "p95": 99596.79999999999,
                "sd": 18250.982736402017
              },
              "n_input_tokens": {
                "mean": 80458.0,
                "n": 10,
                "p05": 56874.100000000006,
                "p25": 71440.0,
                "p50": 73366.5,
                "p75": 89521.25,
                "p95": 112134.59999999998,
                "sd": 19789.914395413078
              },
              "n_output_tokens": {
                "mean": 865.0,
                "n": 10,
                "p05": 623.05,
                "p25": 810.5,
                "p50": 869.5,
                "p75": 943.75,
                "p95": 1078.6499999999999,
                "sd": 157.32627102793595
              },
              "scores": {
                "evidence_quality": {
                  "mean": 4.0,
                  "n": 10,
                  "p05": 3.0,
                  "p25": 3.0,
                  "p50": 4.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.9428090415820634
                },
                "resource_efficiency": {
                  "mean": 0.9,
                  "n": 10,
                  "p05": 0.0,
                  "p25": 1.0,
                  "p50": 1.0,
                  "p75": 1.0,
                  "p95": 1.549999999999999,
                  "sd": 0.5676462121975467
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 4.0,
                  "n": 10,
                  "p05": 3.0,
                  "p25": 3.0,
                  "p50": 4.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.9428090415820634
                },
                "task_correctness": {
                  "mean": 3.5,
                  "n": 10,
                  "p05": 2.0,
                  "p25": 2.25,
                  "p50": 3.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.35400640077266
                },
                "tool_efficiency": {
                  "mean": 0.8,
                  "n": 10,
                  "p05": 0.0,
                  "p25": 1.0,
                  "p50": 1.0,
                  "p75": 1.0,
                  "p95": 1.0,
                  "sd": 0.4216370213557839
                }
              },
              "wall_time_seconds": {
                "mean": 59.112096799999996,
                "n": 10,
                "p05": 52.05671425,
                "p25": 56.93359475,
                "p50": 60.252210000000005,
                "p75": 60.97439,
                "p95": 64.6503179,
                "sd": 4.439501782901841
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.003278924,
                "n": 10,
                "p05": 0.0028426500000000004,
                "p25": 0.00289825,
                "p50": 0.0029375,
                "p75": 0.00301835,
                "p95": 0.004698010000000001,
                "sd": 0.0007491632401137806
              },
              "n_cache_tokens": {
                "mean": 35123.2,
                "n": 10,
                "p05": 27136.0,
                "p25": 37120.0,
                "p50": 37120.0,
                "p75": 37120.0,
                "p95": 37120.0,
                "sd": 4209.6240212161465
              },
              "n_input_tokens": {
                "mean": 45530.5,
                "n": 10,
                "p05": 45473.25,
                "p25": 45501.5,
                "p50": 45518.0,
                "p75": 45551.25,
                "p95": 45610.55,
                "sd": 49.37216939846892
              },
              "n_output_tokens": {
                "mean": 412.5,
                "n": 10,
                "p05": 358.0,
                "p25": 385.5,
                "p50": 417.0,
                "p75": 427.25,
                "p95": 475.5,
                "sd": 41.7565696760535
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "skill_compliance": {
                  "mean": 4.9,
                  "n": 10,
                  "p05": 4.45,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.31622776601683794
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                }
              },
              "wall_time_seconds": {
                "mean": 48.0527809,
                "n": 10,
                "p05": 47.3837008,
                "p25": 47.590977499999994,
                "p50": 47.6862645,
                "p75": 48.11368350000001,
                "p95": 49.5441619,
                "sd": 0.8441557175731478
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": -0.0011648519999999996,
              "n": 10,
              "p05": -0.002610022,
              "p25": -0.0015857899999999997,
              "p50": -0.0011879800000000002,
              "p75": -0.0006508299999999996,
              "p95": 0.000186605999999999,
              "sd": 0.0010181266949408168
            },
            "n_cache_tokens": {
              "mean": -35353.6,
              "n": 10,
              "p05": -66969.6,
              "p25": -41728.0,
              "p50": -31104.0,
              "p75": -26112.0,
              "p95": -11468.800000000001,
              "sd": 19523.04704815425
            },
            "n_input_tokens": {
              "mean": -34927.5,
              "n": 10,
              "p05": -66563.3,
              "p25": -44000.25,
              "p50": -27830.0,
              "p75": -25932.25,
              "p95": -11373.350000000002,
              "sd": 19764.463909023973
            },
            "n_output_tokens": {
              "mean": -452.5,
              "n": 10,
              "p05": -640.35,
              "p25": -576.5,
              "p50": -442.0,
              "p75": -379.0,
              "p95": -244.60000000000002,
              "sd": 145.54590722899462
            },
            "wall_time_seconds": {
              "mean": -11.059315900000001,
              "n": 10,
              "p05": -16.438381200000002,
              "p25": -13.358862500000006,
              "p50": -12.072595999999997,
              "p75": -8.481177499999998,
              "p95": -4.6152163500000025,
              "sd": 4.2660349715409165
            }
          },
          "n": 10,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 2,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 3,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 4,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 5,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 6,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 7,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 8,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 9,
              "scenario_id": "list-and-sort-typed-notes"
            },
            {
              "sample": 10,
              "scenario_id": "list-and-sort-typed-notes"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 1.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 1.0,
              "p75": 2.0,
              "p95": 2.0,
              "sd": 0.9428090415820634
            },
            "resource_efficiency": {
              "mean": 4.1,
              "n": 10,
              "p05": 3.45,
              "p25": 4.0,
              "p50": 4.0,
              "p75": 4.0,
              "p95": 5.0,
              "sd": 0.5676462121975467
            },
            "safety": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 1.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 1.0,
              "p75": 2.0,
              "p95": 2.0,
              "sd": 0.9428090415820634
            },
            "task_correctness": {
              "mean": 1.5,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 2.0,
              "p75": 2.75,
              "p95": 3.0,
              "sd": 1.35400640077266
            },
            "tool_efficiency": {
              "mean": 4.2,
              "n": 10,
              "p05": 4.0,
              "p25": 4.0,
              "p50": 4.0,
              "p75": 4.0,
              "p95": 5.0,
              "sd": 0.4216370213557839
            }
          }
        },
        "query-structured-metadata-without-scanning-files": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.022928172,
                "n": 10,
                "p05": 0.014084138,
                "p25": 0.018679,
                "p50": 0.022792479999999997,
                "p75": 0.02707047,
                "p95": 0.031797326,
                "sd": 0.006571142275861768
              },
              "n_cache_tokens": {
                "mean": 363673.6,
                "n": 10,
                "p05": 186304.0,
                "p25": 268736.0,
                "p50": 333568.0,
                "p75": 471936.0,
                "p95": 569779.2,
                "sd": 146230.12409152303
              },
              "n_input_tokens": {
                "mean": 415831.5,
                "n": 10,
                "p05": 225452.95,
                "p25": 315036.5,
                "p50": 386333.0,
                "p75": 530897.75,
                "p95": 630456.25,
                "sd": 154466.86057191828
              },
              "n_output_tokens": {
                "mean": 4352.6,
                "n": 10,
                "p05": 2033.6000000000001,
                "p25": 3304.5,
                "p50": 4336.5,
                "p75": 5208.25,
                "p95": 6734.699999999999,
                "sd": 1672.6539922463874
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 0.1,
                  "n": 10,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p50": 0.0,
                  "p75": 0.0,
                  "p95": 0.5499999999999989,
                  "sd": 0.31622776601683794
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 3.3,
                  "n": 10,
                  "p05": 2.0,
                  "p25": 2.0,
                  "p50": 2.5,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 1.4944341180973262
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 0.1,
                  "n": 10,
                  "p05": 0.0,
                  "p25": 0.0,
                  "p50": 0.0,
                  "p75": 0.0,
                  "p95": 0.5499999999999989,
                  "sd": 0.31622776601683794
                }
              },
              "wall_time_seconds": {
                "mean": 133.1751032,
                "n": 10,
                "p05": 87.97025005,
                "p25": 111.94184999999999,
                "p50": 131.959354,
                "p75": 147.13389074999998,
                "p95": 183.4298858,
                "sd": 33.618838536798094
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.0038491360000000004,
                "n": 10,
                "p05": 0.00336453,
                "p25": 0.0034541,
                "p50": 0.0035069,
                "p75": 0.0035788999999999994,
                "p95": 0.005346956,
                "sd": 0.0007891311153583205
              },
              "n_cache_tokens": {
                "mean": 35020.8,
                "n": 10,
                "p05": 26572.800000000003,
                "p25": 37120.0,
                "p50": 37120.0,
                "p75": 37120.0,
                "p95": 37120.0,
                "sd": 4432.078940331877
              },
              "n_input_tokens": {
                "mean": 46190.0,
                "n": 10,
                "p05": 46145.0,
                "p25": 46164.25,
                "p50": 46185.0,
                "p75": 46219.75,
                "p95": 46238.8,
                "sd": 35.739800409813895
              },
              "n_output_tokens": {
                "mean": 762.4,
                "n": 10,
                "p05": 678.0500000000001,
                "p25": 732.0,
                "p50": 759.0,
                "p75": 802.0,
                "p95": 847.05,
                "sd": 62.663475096032705
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "skill_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                }
              },
              "wall_time_seconds": {
                "mean": 55.6795092,
                "n": 10,
                "p05": 53.41812395,
                "p25": 55.18524725,
                "p50": 56.06618,
                "p75": 56.4019735,
                "p95": 57.03170849999999,
                "sd": 1.393157411580997
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": -0.019079036,
              "n": 10,
              "p05": -0.027311724000000002,
              "p25": -0.02349817,
              "p50": -0.01928598,
              "p75": -0.014439790000000001,
              "p95": -0.010639108000000005,
              "sd": 0.006381822840159559
            },
            "n_cache_tokens": {
              "mean": -328652.8,
              "n": 10,
              "p05": -537612.8,
              "p25": -434816.0,
              "p50": -301440.0,
              "p75": -231616.0,
              "p95": -149184.0000000001,
              "sd": 147163.5024898044
            },
            "n_input_tokens": {
              "mean": -369641.5,
              "n": 10,
              "p05": -584287.6000000001,
              "p25": -484704.25,
              "p50": -340114.5,
              "p75": -268810.25,
              "p95": -179301.2000000001,
              "sd": 154466.88319525178
            },
            "n_output_tokens": {
              "mean": -3590.2,
              "n": 10,
              "p05": -6031.25,
              "p25": -4355.0,
              "p50": -3565.5,
              "p75": -2543.0,
              "p95": -1298.4000000000008,
              "sd": 1675.1934415662768
            },
            "wall_time_seconds": {
              "mean": -77.49559400000001,
              "n": 10,
              "p05": -128.9795999,
              "p25": -90.997069,
              "p50": -75.0510935,
              "p75": -56.86747575,
              "p95": -32.46870290000001,
              "sd": 33.882935016031475
            }
          },
          "n": 10,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 2,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 3,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 4,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 5,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 6,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 7,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 8,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 9,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            },
            {
              "sample": 10,
              "scenario_id": "query-structured-metadata-without-scanning-files"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "resource_efficiency": {
              "mean": 4.9,
              "n": 10,
              "p05": 4.45,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.31622776601683794
            },
            "safety": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 1.7,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 2.5,
              "p75": 3.0,
              "p95": 3.0,
              "sd": 1.4944341180973262
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "tool_efficiency": {
              "mean": 4.9,
              "n": 10,
              "p05": 4.45,
              "p25": 5.0,
              "p50": 5.0,
              "p75": 5.0,
              "p95": 5.0,
              "sd": 0.31622776601683794
            }
          }
        },
        "read-one-note-with-parent-context": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.002954904,
                "n": 10,
                "p05": 0.00216273,
                "p25": 0.0022253299999999998,
                "p50": 0.00263062,
                "p75": 0.00367617,
                "p95": 0.004365319999999999,
                "sd": 0.0009180435876749596
              },
              "n_cache_tokens": {
                "mean": 31539.2,
                "n": 10,
                "p05": 23040.0,
                "p25": 25536.0,
                "p50": 33024.0,
                "p75": 33024.0,
                "p95": 41228.79999999999,
                "sd": 7274.685434970902
              },
              "n_input_tokens": {
                "mean": 40845.0,
                "n": 10,
                "p05": 38175.25,
                "p25": 38252.5,
                "p50": 38427.5,
                "p75": 41771.75,
                "p95": 48545.44999999999,
                "sd": 4817.280883559844
              },
              "n_output_tokens": {
                "mean": 385.8,
                "n": 10,
                "p05": 345.45000000000005,
                "p25": 367.0,
                "p50": 381.0,
                "p75": 398.75,
                "p95": 437.69999999999993,
                "sd": 33.13205899628535
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 3.0,
                  "n": 10,
                  "p05": 1.0,
                  "p25": 2.25,
                  "p50": 3.5,
                  "p75": 4.0,
                  "p95": 4.0,
                  "sd": 1.247219128924647
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 3.8,
                  "n": 10,
                  "p05": 3.0,
                  "p25": 4.0,
                  "p50": 4.0,
                  "p75": 4.0,
                  "p95": 4.0,
                  "sd": 0.4216370213557839
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 1.8,
                  "n": 10,
                  "p05": 1.0,
                  "p25": 2.0,
                  "p50": 2.0,
                  "p75": 2.0,
                  "p95": 2.0,
                  "sd": 0.4216370213557839
                }
              },
              "wall_time_seconds": {
                "mean": 47.733627,
                "n": 10,
                "p05": 46.1500303,
                "p25": 46.7319575,
                "p50": 47.3126195,
                "p75": 47.63089075,
                "p95": 50.94288709999999,
                "sd": 1.794011726134722
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.0033127440000000003,
                "n": 10,
                "p05": 0.0029131800000000005,
                "p25": 0.0029273999999999993,
                "p50": 0.0029702,
                "p75": 0.003032,
                "p95": 0.00472718,
                "sd": 0.0007464955754456954
              },
              "n_cache_tokens": {
                "mean": 35123.2,
                "n": 10,
                "p05": 27136.0,
                "p25": 37120.0,
                "p50": 37120.0,
                "p75": 37120.0,
                "p95": 37120.0,
                "sd": 4209.6240212161465
              },
              "n_input_tokens": {
                "mean": 45626.4,
                "n": 10,
                "p05": 45601.8,
                "p25": 45605.0,
                "p50": 45614.5,
                "p75": 45635.25,
                "p95": 45680.6,
                "sd": 31.93117598836598
              },
              "n_output_tokens": {
                "mean": 424.7,
                "n": 10,
                "p05": 393.15000000000003,
                "p25": 404.5,
                "p50": 411.5,
                "p75": 443.25,
                "p95": 475.9,
                "sd": 31.41496458696078
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "skill_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                }
              },
              "wall_time_seconds": {
                "mean": 48.591380199999996,
                "n": 10,
                "p05": 47.34305380000001,
                "p25": 47.597243999999996,
                "p50": 48.8724495,
                "p75": 49.428169249999996,
                "p95": 49.78325149999999,
                "sd": 1.0071218407736413
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": 0.00035784,
              "n": 10,
              "p05": -0.00141419,
              "p25": -0.00057154,
              "p50": 0.0006892199999999999,
              "p75": 0.0008622200000000002,
              "p95": 0.0018700799999999997,
              "sd": 0.0012093330410878
            },
            "n_cache_tokens": {
              "mean": 3584.0,
              "n": 10,
              "p05": -13632.000000000002,
              "p25": 3328.0,
              "p50": 4096.0,
              "p75": 11584.0,
              "p95": 14080.0,
              "sd": 10414.862542433182
            },
            "n_input_tokens": {
              "mean": 4781.4,
              "n": 10,
              "p05": -2938.8,
              "p25": 3856.75,
              "p50": 7180.5,
              "p75": 7369.75,
              "p95": 7504.85,
              "sd": 4826.566992525157
            },
            "n_output_tokens": {
              "mean": 38.9,
              "n": 10,
              "p05": -35.75,
              "p25": 7.0,
              "p50": 38.0,
              "p75": 88.25,
              "p95": 102.55,
              "sd": 54.046173674820764
            },
            "wall_time_seconds": {
              "mean": 0.8577531999999998,
              "n": 10,
              "p05": -2.5619395499999955,
              "p25": 0.010800249999997291,
              "p50": 1.6007204999999978,
              "p75": 2.2583287500000004,
              "p95": 2.8005451999999984,
              "sd": 2.203151914195396
            }
          },
          "n": 10,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 2,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 3,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 4,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 5,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 6,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 7,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 8,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 9,
              "scenario_id": "read-one-note-with-parent-context"
            },
            {
              "sample": 10,
              "scenario_id": "read-one-note-with-parent-context"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "resource_efficiency": {
              "mean": 2.0,
              "n": 10,
              "p05": 1.0,
              "p25": 1.0,
              "p50": 1.5,
              "p75": 2.75,
              "p95": 4.0,
              "sd": 1.247219128924647
            },
            "safety": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 1.2,
              "n": 10,
              "p05": 1.0,
              "p25": 1.0,
              "p50": 1.0,
              "p75": 1.0,
              "p95": 2.0,
              "sd": 0.4216370213557839
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "tool_efficiency": {
              "mean": 3.2,
              "n": 10,
              "p05": 3.0,
              "p25": 3.0,
              "p50": 3.0,
              "p75": 3.0,
              "p95": 4.0,
              "sd": 0.4216370213557839
            }
          }
        },
        "summarize-one-topic": {
          "arm_distributions": {
            "control": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.00435836,
                "n": 10,
                "p05": 0.00249184,
                "p25": 0.0042828,
                "p50": 0.0044109200000000005,
                "p75": 0.004504940000000001,
                "p95": 0.006146519999999997,
                "sd": 0.0013020611411484826
              },
              "n_cache_tokens": {
                "mean": 67328.0,
                "n": 10,
                "p05": 39360.0,
                "p25": 65216.0,
                "p50": 75264.0,
                "p75": 76288.0,
                "p95": 76851.2,
                "sd": 15370.426091108282
              },
              "n_input_tokens": {
                "mean": 77231.8,
                "n": 10,
                "p05": 44738.3,
                "p25": 74413.0,
                "p50": 84460.5,
                "p75": 85650.75,
                "p95": 93714.0,
                "sd": 18320.230710580283
              },
              "n_output_tokens": {
                "mean": 859.2,
                "n": 10,
                "p05": 524.1500000000001,
                "p25": 818.5,
                "p50": 888.5,
                "p75": 984.5,
                "p95": 1065.3,
                "sd": 198.09862863398794
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 1.1,
                  "n": 10,
                  "p05": 0.0,
                  "p25": 0.25,
                  "p50": 1.0,
                  "p75": 1.0,
                  "p95": 3.099999999999998,
                  "sd": 1.1972189997378648
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 3.2,
                  "n": 10,
                  "p05": 2.45,
                  "p25": 3.0,
                  "p50": 3.0,
                  "p75": 3.0,
                  "p95": 4.549999999999999,
                  "sd": 0.7888106377466154
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 0.8,
                  "n": 10,
                  "p05": 0.0,
                  "p25": 0.25,
                  "p50": 1.0,
                  "p75": 1.0,
                  "p95": 1.549999999999999,
                  "sd": 0.6324555320336759
                }
              },
              "wall_time_seconds": {
                "mean": 58.4464698,
                "n": 10,
                "p05": 50.88894235000001,
                "p25": 58.607569500000004,
                "p50": 59.9634525,
                "p75": 60.778130000000004,
                "p95": 61.70938120000001,
                "sd": 4.118346531941856
              }
            },
            "treatment": {
              "cohort": "common-valid",
              "cost_usd": {
                "mean": 0.003051788,
                "n": 10,
                "p05": 0.00267955,
                "p25": 0.0028737000000000003,
                "p50": 0.0029032,
                "p75": 0.00294965,
                "p95": 0.003935445999999998,
                "sd": 0.0005924721129639774
              },
              "n_cache_tokens": {
                "mean": 36326.4,
                "n": 10,
                "p05": 31628.800000000003,
                "p25": 37120.0,
                "p50": 37120.0,
                "p75": 37120.0,
                "p95": 38144.0,
                "sd": 3257.1186721463564
              },
              "n_input_tokens": {
                "mean": 45525.1,
                "n": 10,
                "p05": 45476.75,
                "p25": 45511.25,
                "p50": 45521.0,
                "p75": 45543.25,
                "p95": 45576.0,
                "sd": 36.250517237689174
              },
              "n_output_tokens": {
                "mean": 404.6,
                "n": 10,
                "p05": 362.65000000000003,
                "p25": 393.0,
                "p50": 402.0,
                "p75": 414.75,
                "p95": 451.0,
                "sd": 30.430978368176802
              },
              "scores": {
                "evidence_quality": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "resource_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "safety": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "scenario_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "skill_compliance": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "task_correctness": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                },
                "tool_efficiency": {
                  "mean": 5.0,
                  "n": 10,
                  "p05": 5.0,
                  "p25": 5.0,
                  "p50": 5.0,
                  "p75": 5.0,
                  "p95": 5.0,
                  "sd": 0.0
                }
              },
              "wall_time_seconds": {
                "mean": 48.0822376,
                "n": 10,
                "p05": 47.13211475000001,
                "p25": 47.492197000000004,
                "p50": 48.252823,
                "p75": 48.6396915,
                "p95": 48.86510925,
                "sd": 0.6995431907047457
              }
            }
          },
          "cohort": "common-valid",
          "metric_delta_treatment_minus_control": {
            "cost_usd": {
              "mean": -0.001306572,
              "n": 10,
              "p05": -0.003149674,
              "p25": -0.001732739999999999,
              "p50": -0.0014668800000000005,
              "p75": -0.00048289999999999976,
              "p95": 0.0004699999999999992,
              "sd": 0.001372487457565035
            },
            "n_cache_tokens": {
              "mean": -31001.6,
              "n": 10,
              "p05": -44659.200000000004,
              "p25": -38912.0,
              "p50": -38144.0,
              "p75": -28096.0,
              "p95": -2240.0000000000146,
              "sd": 16199.606821017464
            },
            "n_input_tokens": {
              "mean": -31706.7,
              "n": 10,
              "p05": -48199.25,
              "p25": -40179.5,
              "p50": -38931.0,
              "p75": -28901.5,
              "p95": 837.699999999983,
              "sd": 18344.994982283315
            },
            "n_output_tokens": {
              "mean": -454.6,
              "n": 10,
              "p05": -672.0,
              "p25": -610.75,
              "p50": -487.0,
              "p75": -395.5,
              "p95": -83.95000000000026,
              "sd": 219.8738021886393
            },
            "wall_time_seconds": {
              "mean": -10.3642322,
              "n": 10,
              "p05": -13.99058685,
              "p25": -12.755500000000001,
              "p50": -11.800063499999997,
              "p75": -10.90995925,
              "p95": -2.217495250000007,
              "sd": 4.425328166436115
            }
          },
          "n": 10,
          "pair_ids": [
            {
              "sample": 1,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 2,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 3,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 4,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 5,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 6,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 7,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 8,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 9,
              "scenario_id": "summarize-one-topic"
            },
            {
              "sample": 10,
              "scenario_id": "summarize-one-topic"
            }
          ],
          "score_delta_treatment_minus_control": {
            "evidence_quality": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "resource_efficiency": {
              "mean": 3.9,
              "n": 10,
              "p05": 1.9000000000000001,
              "p25": 4.0,
              "p50": 4.0,
              "p75": 4.75,
              "p95": 5.0,
              "sd": 1.1972189997378648
            },
            "safety": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "scenario_compliance": {
              "mean": 1.8,
              "n": 10,
              "p05": 0.45,
              "p25": 2.0,
              "p50": 2.0,
              "p75": 2.0,
              "p95": 2.549999999999999,
              "sd": 0.7888106377466154
            },
            "task_correctness": {
              "mean": 0.0,
              "n": 10,
              "p05": 0.0,
              "p25": 0.0,
              "p50": 0.0,
              "p75": 0.0,
              "p95": 0.0,
              "sd": 0.0
            },
            "tool_efficiency": {
              "mean": 4.2,
              "n": 10,
              "p05": 3.45,
              "p25": 4.0,
              "p50": 4.0,
              "p75": 4.75,
              "p95": 5.0,
              "sd": 0.6324555320336759
            }
          }
        }
      },
      "treatment_arm": "skill"
    }
  },
  "timing": {
    "available_valid_summed_cell_seconds": 7380.672101,
    "common_valid_summed_cell_seconds": 7380.672101,
    "pipeline_elapsed_seconds": 4814.1645846930005
  }
}
```

</details>

## Sanitized device telemetry

<details>
<summary>Complete sanitized device telemetry</summary>

```json
{
  "cpu_percent_max": 100.0,
  "disk_read_bytes_per_second_max": 192128000.0,
  "disk_read_bytes_total": 1752862720,
  "disk_scope": "physical-block-devices",
  "disk_write_bytes_per_second_max": 71282990.58006941,
  "disk_write_bytes_total": 9795223552,
  "docker_oom_events": 0,
  "load1_max": 2.56,
  "logical_cpus": 2,
  "mem_available_bytes_min": 1944408064,
  "network_rx_bytes_per_second_max": 45427434.17784402,
  "network_rx_bytes_total": 6175161757,
  "network_scope": "default-route-interfaces",
  "network_tx_bytes_per_second_max": 1063410.484668645,
  "network_tx_bytes_total": 170390994,
  "rootfs_free_bytes_min": 9260736512,
  "rootfs_scope": "root-filesystem",
  "rootfs_used_bytes_max": 37007667200,
  "running_containers_max": 4,
  "sample_count": 2371,
  "sampling_errors": 0,
  "schema_version": 2,
  "scope": "whole-host",
  "swap_free_bytes_min": 9071218688,
  "terminal_status": "completed",
  "total_memory_bytes": 4041781248,
  "total_swap_bytes": 9091141632
}
```

</details>

The report is derived from the bundled, sealed machine-readable evidence. Device telemetry is schema-constrained to numeric capacity and load measurements; hostnames, usernames, paths, environment variables, command lines, network identifiers, container names, labels, and credential material are not accepted.
