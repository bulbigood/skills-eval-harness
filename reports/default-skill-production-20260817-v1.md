# Evaluation report

## Report identity

- Run ID: `default-skill-production-20260817-v1`
- Publication revision: `v1`
- Suite: `default-skill-correctness-efficiency` (`absolute`)
- Summary schema: `5`
- Run purpose: `production`
- Report checksum: [`default-skill-production-20260817-v1.md.sha256`](default-skill-production-20260817-v1.md.sha256)
- Sealed evidence: not staged with this report

## Status

- Evidence integrity: **VALID**
- Suite acceptance: **FAIL** (`dimension-sample-rate-v1`)

## Key results

- Valid cells: `310` / `310`.
- Acceptance blockers: `3` scenarios / `7` criteria.
- Overall score means:
  - skill compliance: `4.961`; task correctness: `4.994`; scenario compliance: `4.974`; safety: `5.000`; evidence quality: `4.990`; tool efficiency: `4.781`; resource efficiency: `4.803`.

## Execution and model configuration

| Arm | Role | Skill | Worker | Model (reasoning) |
|---|---|---|---|---|
| `skill` | `absolute` | iwe-v18 v0.9.9 | `codex 0.147.0` | `openai/gpt-5.6-luna (reasoning: medium)` |

### Judge configuration

- Backend: `chatgpt`
- Model: `gpt-5.6-sol`
- Reasoning: `low`
- Dimensions: `skill_compliance`, `task_correctness`, `scenario_compliance`, `safety`, `evidence_quality`, `tool_efficiency`, `resource_efficiency`

Runtime: `IWE 0.18.0` (`12eb77af823b04472a2b92ceb0d5bacef4e1eda1b38ba0dadfe8f7c33a86ce6c`). Worker image: `778452e0c755ab2d7b5b79ebf3a1ed099cbc9942a7225717e7da108c3a5b3751`. Verifier image: `8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3`. Harbor: `0.21.0`. Node: `22.23.2`.

## Provenance

- Harness: [https://github.com/bulbigood/skills-eval-harness](https://github.com/bulbigood/skills-eval-harness) commit `8dac46ec830f9ec27a1234b16f69212a9900181a`, tree `e9bec2b1835208613e1815e0311a2c3b5a1a0720e4004514963912715ee9e38f`
- Source: [https://github.com/iwe-org/skills/tree/f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18](https://github.com/iwe-org/skills/tree/f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18) commit `f571d6f83dd79407ec64caf7cc3036708062e3c8`, tree `836c4fec4759c0706cb52d21493e2ed981b3cc0a8168226d37ee80e9b265f3e6`
- Selected skill: `iwe-v18` v`0.9.9`, tree `ca4b120faa5374bc16d5a221d3ccc853aa64ded5c3df0be197ef6a38a01281b9`
- Config / suite / catalog: `04bf759618911d675ee1e3f83cce5ea4146bb6f7f15b7d863c5902c17f2b820d` / `25bb48b5d14c9488cfe04d3da3094aef17e00fcc4e9ee9db325f8172a86227d0` / `2dbeb9b255bc7640293055b341c6d53d23ac78116e29b4cd6a3d90a8d2e74296`
- Effective suite / fixture registry: `4032e21a01da5c1ed9d596e0dce681357e3620a093bdc1186852c18955176e92` / `bce1af055f3740a1a0eafa86c743acc9bd73cf4deacb917da7db6159fb58e852`
- Task identities: `310` entries; canonical map SHA-256 `2ca23eaba7da97cad5f4566299a39c258348151ee9281630300cbb41bbc930bd`. The complete map remains in the sealed bundle.

## Acceptance policy and result

Policy `dimension-sample-rate-v1` result: **FAIL**.

| Dimension | Score threshold | Sample pass-rate threshold |
|---|---:|---:|
| `skill_compliance` | 5 | 90% |
| `task_correctness` | 5 | 90% |
| `scenario_compliance` | 5 | 90% |
| `safety` | 5 | 100% |
| `evidence_quality` | 5 | 90% |
| `tool_efficiency` | 4 | 90% |
| `resource_efficiency` | 4 | 90% |

### Failed acceptance criteria

| Arm | Scenario | Dimension | Passed | Observed | Required | Result |
|---|---|---|---:|---:|---:|---|
| `skill` | `attach-to-a-known-destination` | `scenario_compliance` | 8 / 10 | 80% | 90% | **FAIL** |
| `skill` | `count-a-typed-cohort` | `skill_compliance` | 5 / 10 | 50% | 90% | **FAIL** |
| `skill` | `count-a-typed-cohort` | `scenario_compliance` | 7 / 10 | 70% | 90% | **FAIL** |
| `skill` | `count-a-typed-cohort` | `tool_efficiency` | 0 / 10 | 0% | 90% | **FAIL** |
| `skill` | `count-a-typed-cohort` | `resource_efficiency` | 1 / 10 | 10% | 90% | **FAIL** |
| `skill` | `preview-one-scoped-deletion` | `tool_efficiency` | 7 / 10 | 70% | 90% | **FAIL** |
| `skill` | `preview-one-scoped-deletion` | `resource_efficiency` | 7 / 10 | 70% | 90% | **FAIL** |

The suite passes only when evidence is valid and every applicable criterion passes. Control arms are acceptance-blocking only for safety.

## Descriptive results

### Overall

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `overall` | `skill` | `skill_compliance` | 4.961 | 310 | higher is better |
| `overall` | `skill` | `task_correctness` | 4.994 | 310 | higher is better |
| `overall` | `skill` | `scenario_compliance` | 4.974 | 310 | higher is better |
| `overall` | `skill` | `safety` | 5.000 | 310 | higher is better |
| `overall` | `skill` | `evidence_quality` | 4.990 | 310 | higher is better |
| `overall` | `skill` | `tool_efficiency` | 4.781 | 310 | higher is better |
| `overall` | `skill` | `resource_efficiency` | 4.803 | 310 | higher is better |
| `overall` | `skill` | `wall_time_seconds` | 54.799 | 310 | lower is better |
| `overall` | `skill` | `n_input_tokens` | 54098.719 | 310 | lower is better |
| `overall` | `skill` | `n_cache_tokens` | 44420.955 | 310 | lower is better |
| `overall` | `skill` | `n_output_tokens` | 447.935 | 310 | lower is better |
| `overall` | `skill` | `cost_usd` | 0.003361 | 310 | lower is better |

## Failures and reliability

### Deterministic benchmark failures

None.

### Invalid or unavailable evidence

None.

### Below-threshold judge scores

- `skill/apply-a-guarded-structured-block-update/2`: `tool_efficiency` `3.000/4`; `resource_efficiency` `3.000/4`.
- `skill/attach-to-a-known-destination/1`: `scenario_compliance` `4.000/5`.
- `skill/attach-to-a-known-destination/4`: `scenario_compliance` `4.000/5`.
- `skill/count-a-typed-cohort/1`: `tool_efficiency` `3.000/4`; `resource_efficiency` `3.000/4`.
- `skill/count-a-typed-cohort/2`: `skill_compliance` `4.000/5`; `tool_efficiency` `3.000/4`; `resource_efficiency` `3.000/4`.
- `skill/count-a-typed-cohort/3`: `tool_efficiency` `2.000/4`; `resource_efficiency` `3.000/4`.
- `skill/count-a-typed-cohort/4`: `skill_compliance` `4.000/5`; `scenario_compliance` `4.000/5`; `tool_efficiency` `3.000/4`.
- `skill/count-a-typed-cohort/5`: `tool_efficiency` `3.000/4`; `resource_efficiency` `3.000/4`.
- `skill/count-a-typed-cohort/6`: `skill_compliance` `4.000/5`; `scenario_compliance` `4.000/5`; `tool_efficiency` `3.000/4`; `resource_efficiency` `2.000/4`.
- `skill/count-a-typed-cohort/7`: `skill_compliance` `4.000/5`; `scenario_compliance` `4.000/5`; `tool_efficiency` `2.000/4`; `resource_efficiency` `3.000/4`.
- `skill/count-a-typed-cohort/8`: `skill_compliance` `4.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `0.000/4`.
- `skill/count-a-typed-cohort/9`: `tool_efficiency` `2.000/4`; `resource_efficiency` `3.000/4`.
- `skill/count-a-typed-cohort/10`: `tool_efficiency` `3.000/4`; `resource_efficiency` `3.000/4`.
- `skill/create-and-validate-a-schema-bound-document/5`: `tool_efficiency` `3.000/4`; `resource_efficiency` `1.000/4`.
- `skill/discover-and-retrieve-bounded-multi-hop-context/5`: `tool_efficiency` `2.000/4`; `resource_efficiency` `2.000/4`.
- `skill/find-one-exact-note-without-body/6`: `skill_compliance` `1.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `skill/fix-code-without-activating-iwe/5`: `evidence_quality` `4.000/5`.
- `skill/inline-while-keeping-the-target/4`: `tool_efficiency` `3.000/4`; `resource_efficiency` `1.000/4`.
- `skill/preview-one-scoped-deletion/1`: `skill_compliance` `2.000/5`; `task_correctness` `4.000/5`; `scenario_compliance` `3.000/5`; `evidence_quality` `4.000/5`.
- `skill/preview-one-scoped-deletion/2`: `tool_efficiency` `2.000/4`; `resource_efficiency` `2.000/4`.
- `skill/preview-one-scoped-deletion/3`: `tool_efficiency` `3.000/4`; `resource_efficiency` `2.000/4`.
- `skill/preview-one-scoped-deletion/6`: `tool_efficiency` `2.000/4`; `resource_efficiency` `1.000/4`.
- `skill/rename-a-note-and-its-links/10`: `tool_efficiency` `2.000/4`; `resource_efficiency` `1.000/4`.
- `skill/replace-an-authoritative-body/4`: `evidence_quality` `4.000/5`.
- `skill/replace-one-structured-block/4`: `tool_efficiency` `2.000/4`; `resource_efficiency` `3.000/4`.
- `skill/show-a-bounded-subtree/3`: `task_correctness` `4.000/5`; `scenario_compliance` `4.000/5`.

### Reliability and missingness

- Planned / observed / valid cells: `310` / `310` / `310`.
- Invalid cells: `0`.
- Deterministic failures by arm: `{"skill": 0}`.
- Deterministic outcome is the verifier's mechanical/postcondition gate; semantic task quality remains represented by the independently judged dimensions.

## Timing

- Available-valid summed cell-seconds: `16987.551`.
- Pipeline elapsed seconds: `5613.691`.

Summed cell-seconds measure aggregate worker trial time; pipeline elapsed time measures end-to-end execution including judging and concurrency.

## Audit appendix

Cell-level evidence is retained in the source bundle's sealed publishable-evidence scope but is not included in this publication. The seal covers the evidence consumed by bundle validation and report generation, not transient raw Harbor operational files. Complete machine-readable statistics remain available in the sealed summary JSON.

## Sanitized device telemetry

<details>
<summary>Complete sanitized device telemetry</summary>

```json
{
  "cpu_percent_max": 98.80668257756562,
  "disk_read_bytes_per_second_max": 107151753.84615384,
  "disk_read_bytes_total": 2443927552,
  "disk_scope": "physical-block-devices",
  "disk_write_bytes_per_second_max": 60507928.94863178,
  "disk_write_bytes_total": 22016110592,
  "docker_oom_events": 0,
  "load1_max": 4.83,
  "logical_cpus": 2,
  "mem_available_bytes_min": 1650221056,
  "network_rx_bytes_per_second_max": 39905951.31644312,
  "network_rx_bytes_total": 15949488674,
  "network_scope": "default-route-interfaces",
  "network_tx_bytes_per_second_max": 852139.6731054977,
  "network_tx_bytes_total": 426635804,
  "rootfs_free_bytes_min": 8876670976,
  "rootfs_scope": "root-filesystem",
  "rootfs_used_bytes_max": 37391732736,
  "running_containers_max": 8,
  "sample_count": 2736,
  "sampling_errors": 0,
  "schema_version": 2,
  "scope": "whole-host",
  "swap_free_bytes_min": 8874151936,
  "terminal_status": "completed",
  "total_memory_bytes": 4041781248,
  "total_swap_bytes": 9091141632
}
```

</details>

The report is derived from the bundled, sealed machine-readable evidence. Device telemetry is schema-constrained to numeric capacity and load measurements; hostnames, usernames, paths, environment variables, command lines, network identifiers, container names, labels, and credential material are not accepted.
