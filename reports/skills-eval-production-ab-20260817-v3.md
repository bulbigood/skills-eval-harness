# Evaluation report

## Report identity

- Run ID: `skills-eval-production-ab-20260817-v3`
- Publication revision: `v3`
- Suite: `skill-guidance-efficiency-ab` (`paired`)
- Summary schema: `5`
- Run purpose: `production`
- Report checksum: [`skills-eval-production-ab-20260817-v3.md.sha256`](skills-eval-production-ab-20260817-v3.md.sha256)
- Sealed evidence: not staged with this report

## Status

- Evidence integrity: **VALID**
- Suite acceptance: **PASS** (`dimension-sample-rate-v1`)
- Statistical superiority: **not asserted**

## Key results

- Valid cells: `120` / `120`.
- Common-valid pairs: `60` / `60`.
- Acceptance blockers: none.
- Selected overall treatment-minus-control deltas:
  - task correctness: `0.383`; scenario compliance: `1.033`; tool efficiency: `3.350`; resource efficiency: `3.233`.
  - wall time seconds: `-10.380`; n input tokens: `-37580.717`; cost usd: `-0.002482`.

## Execution and model configuration

| Arm | Role | Skill | Worker | Model (reasoning) |
|---|---|---|---|---|
| `no-skill` | `control` | none | `codex 0.147.0` | `openai/gpt-5.6-luna (reasoning: medium)` |
| `skill` | `treatment` | iwe-v18 v0.9.9 | `codex 0.147.0` | `openai/gpt-5.6-luna (reasoning: medium)` |

### Judge configuration

- Backend: `chatgpt`
- Model: `gpt-5.6-sol`
- Reasoning: `low`
- Dimensions: `skill_compliance`, `task_correctness`, `scenario_compliance`, `safety`, `evidence_quality`, `tool_efficiency`, `resource_efficiency`

Runtime: `IWE 0.18.0` (`12eb77af823b04472a2b92ceb0d5bacef4e1eda1b38ba0dadfe8f7c33a86ce6c`). Worker image: `778452e0c755ab2d7b5b79ebf3a1ed099cbc9942a7225717e7da108c3a5b3751`. Verifier image: `8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3`. Harbor: `0.21.0`. Node: `22.23.2`.

## Provenance

- Harness: [https://github.com/bulbigood/skills-eval-harness](https://github.com/bulbigood/skills-eval-harness) commit `dc8ea68ff26574892b4f4dc8ce7d3fc3aeb245ee`, tree `dbb571d6ad431e1449b88f7e8d13572996169d081cdcc1c6110b860d10609247`
- Source: [https://github.com/iwe-org/skills/tree/f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18](https://github.com/iwe-org/skills/tree/f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18) commit `f571d6f83dd79407ec64caf7cc3036708062e3c8`, tree `836c4fec4759c0706cb52d21493e2ed981b3cc0a8168226d37ee80e9b265f3e6`
- Selected skill: `iwe-v18` v`0.9.9`, tree `ca4b120faa5374bc16d5a221d3ccc853aa64ded5c3df0be197ef6a38a01281b9`
- Config / suite / catalog: `04bf759618911d675ee1e3f83cce5ea4146bb6f7f15b7d863c5902c17f2b820d` / `7629985983246c00dc8f88f7e8f487c23bd5b13d09bd16048c1b18e2d28c8844` / `2dbeb9b255bc7640293055b341c6d53d23ac78116e29b4cd6a3d90a8d2e74296`
- Effective suite / fixture registry: `4213d01e80dce9ce48534637343ded745e6a97a208e20f595fde63778bbf916c` / `bce1af055f3740a1a0eafa86c743acc9bd73cf4deacb917da7db6159fb58e852`
- Task identities: `120` entries; canonical map SHA-256 `2ff31e5d1b1294d7622da66b23e8022abe2701ee29ea52ba496090a0a2ba59d2`. The complete map remains in the sealed bundle.

## Acceptance policy and result

Policy `dimension-sample-rate-v1` result: **PASS**.

| Dimension | Score threshold | Sample pass-rate threshold |
|---|---:|---:|
| `skill_compliance` | 5 | 90% |
| `task_correctness` | 5 | 90% |
| `scenario_compliance` | 5 | 90% |
| `safety` | 5 | 100% |
| `evidence_quality` | 5 | 90% |
| `tool_efficiency` | 4 | 90% |
| `resource_efficiency` | 4 | 90% |

### Acceptance ledger

| Arm | Scenario | Dimension | Passed | Observed | Required | Result |
|---|---|---|---:|---:|---:|---|
| `no-skill` | `ambiguous-discovery-with-one-follow-up` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `no-skill` | `discover-and-retrieve-bounded-multi-hop-context` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `no-skill` | `list-and-sort-typed-notes` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `no-skill` | `query-structured-metadata-without-scanning-files` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `no-skill` | `read-one-note-with-parent-context` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `no-skill` | `summarize-one-topic` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `skill` | `ambiguous-discovery-with-one-follow-up` | `skill_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `ambiguous-discovery-with-one-follow-up` | `task_correctness` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `ambiguous-discovery-with-one-follow-up` | `scenario_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `ambiguous-discovery-with-one-follow-up` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `skill` | `ambiguous-discovery-with-one-follow-up` | `evidence_quality` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `ambiguous-discovery-with-one-follow-up` | `tool_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `ambiguous-discovery-with-one-follow-up` | `resource_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `discover-and-retrieve-bounded-multi-hop-context` | `skill_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `discover-and-retrieve-bounded-multi-hop-context` | `task_correctness` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `discover-and-retrieve-bounded-multi-hop-context` | `scenario_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `discover-and-retrieve-bounded-multi-hop-context` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `skill` | `discover-and-retrieve-bounded-multi-hop-context` | `evidence_quality` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `discover-and-retrieve-bounded-multi-hop-context` | `tool_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `discover-and-retrieve-bounded-multi-hop-context` | `resource_efficiency` | 9 / 10 | 90% | 90% | PASS |
| `skill` | `list-and-sort-typed-notes` | `skill_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `list-and-sort-typed-notes` | `task_correctness` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `list-and-sort-typed-notes` | `scenario_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `list-and-sort-typed-notes` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `skill` | `list-and-sort-typed-notes` | `evidence_quality` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `list-and-sort-typed-notes` | `tool_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `list-and-sort-typed-notes` | `resource_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `query-structured-metadata-without-scanning-files` | `skill_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `query-structured-metadata-without-scanning-files` | `task_correctness` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `query-structured-metadata-without-scanning-files` | `scenario_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `query-structured-metadata-without-scanning-files` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `skill` | `query-structured-metadata-without-scanning-files` | `evidence_quality` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `query-structured-metadata-without-scanning-files` | `tool_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `query-structured-metadata-without-scanning-files` | `resource_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `read-one-note-with-parent-context` | `skill_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `read-one-note-with-parent-context` | `task_correctness` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `read-one-note-with-parent-context` | `scenario_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `read-one-note-with-parent-context` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `skill` | `read-one-note-with-parent-context` | `evidence_quality` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `read-one-note-with-parent-context` | `tool_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `read-one-note-with-parent-context` | `resource_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `skill_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `task_correctness` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `scenario_compliance` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `safety` | 10 / 10 | 100% | 100% | PASS |
| `skill` | `summarize-one-topic` | `evidence_quality` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `tool_efficiency` | 10 / 10 | 100% | 90% | PASS |
| `skill` | `summarize-one-topic` | `resource_efficiency` | 10 / 10 | 100% | 90% | PASS |

The suite passes only when evidence is valid and every applicable criterion passes. Control arms are acceptance-blocking only for safety.

## Descriptive results

### Overall

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `overall` | `no-skill` | `task_correctness` | 4.617 | 60 | higher is better |
| `overall` | `no-skill` | `scenario_compliance` | 3.967 | 60 | higher is better |
| `overall` | `no-skill` | `safety` | 5.000 | 60 | higher is better |
| `overall` | `no-skill` | `evidence_quality` | 4.817 | 60 | higher is better |
| `overall` | `no-skill` | `tool_efficiency` | 1.633 | 60 | higher is better |
| `overall` | `no-skill` | `resource_efficiency` | 1.700 | 60 | higher is better |
| `overall` | `no-skill` | `wall_time_seconds` | 63.623 | 60 | lower is better |
| `overall` | `no-skill` | `n_input_tokens` | 85414.817 | 60 | lower is better |
| `overall` | `no-skill` | `n_cache_tokens` | 67302.400 | 60 | lower is better |
| `overall` | `no-skill` | `n_output_tokens` | 910.717 | 60 | lower is better |
| `overall` | `no-skill` | `cost_usd` | 0.006061 | 60 | lower is better |
| `overall` | `skill` | `skill_compliance` | 5.000 | 60 | higher is better |
| `overall` | `skill` | `task_correctness` | 5.000 | 60 | higher is better |
| `overall` | `skill` | `scenario_compliance` | 5.000 | 60 | higher is better |
| `overall` | `skill` | `safety` | 5.000 | 60 | higher is better |
| `overall` | `skill` | `evidence_quality` | 5.000 | 60 | higher is better |
| `overall` | `skill` | `tool_efficiency` | 4.983 | 60 | higher is better |
| `overall` | `skill` | `resource_efficiency` | 4.933 | 60 | higher is better |
| `overall` | `skill` | `wall_time_seconds` | 53.244 | 60 | lower is better |
| `overall` | `skill` | `n_input_tokens` | 47834.100 | 60 | lower is better |
| `overall` | `skill` | `n_cache_tokens` | 36420.267 | 60 | lower is better |
| `overall` | `skill` | `n_output_tokens` | 473.233 | 60 | lower is better |
| `overall` | `skill` | `cost_usd` | 0.003579 | 60 | lower is better |

### Per scenario

| Group | Arm | Measure | Mean | n | Direction |
|---|---|---|---:|---:|---|
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `scenario_compliance` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `safety` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `tool_efficiency` | 4.900 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `resource_efficiency` | 4.600 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `wall_time_seconds` | 51.644 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `n_input_tokens` | 41109.200 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `n_cache_tokens` | 34073.600 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `n_output_tokens` | 400.900 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `no-skill` | `cost_usd` | 0.002570 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `skill_compliance` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `scenario_compliance` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `safety` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `tool_efficiency` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `resource_efficiency` | 5.000 | 10 | higher is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `wall_time_seconds` | 53.047 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `n_input_tokens` | 55868.000 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `n_cache_tokens` | 46694.400 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `n_output_tokens` | 429.500 | 10 | lower is better |
| `ambiguous-discovery-with-one-follow-up` | `skill` | `cost_usd` | 0.003284 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `scenario_compliance` | 4.300 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `safety` | 5.000 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `tool_efficiency` | 0.900 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `resource_efficiency` | 0.600 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `wall_time_seconds` | 70.740 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `n_input_tokens` | 91641.500 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `n_cache_tokens` | 65561.600 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `n_output_tokens` | 1328.400 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `no-skill` | `cost_usd` | 0.008121 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `skill_compliance` | 5.000 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `scenario_compliance` | 5.000 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `safety` | 5.000 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `tool_efficiency` | 4.900 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `resource_efficiency` | 4.600 | 10 | higher is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `wall_time_seconds` | 59.430 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `n_input_tokens` | 48577.600 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `n_cache_tokens` | 33331.200 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `n_output_tokens` | 803.700 | 10 | lower is better |
| `discover-and-retrieve-bounded-multi-hop-context` | `skill` | `cost_usd` | 0.004680 | 10 | lower is better |
| `list-and-sort-typed-notes` | `no-skill` | `task_correctness` | 3.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `no-skill` | `scenario_compliance` | 3.500 | 10 | higher is better |
| `list-and-sort-typed-notes` | `no-skill` | `safety` | 5.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `no-skill` | `evidence_quality` | 4.300 | 10 | higher is better |
| `list-and-sort-typed-notes` | `no-skill` | `tool_efficiency` | 0.700 | 10 | higher is better |
| `list-and-sort-typed-notes` | `no-skill` | `resource_efficiency` | 1.100 | 10 | higher is better |
| `list-and-sort-typed-notes` | `no-skill` | `wall_time_seconds` | 60.373 | 10 | lower is better |
| `list-and-sort-typed-notes` | `no-skill` | `n_input_tokens` | 71633.300 | 10 | lower is better |
| `list-and-sort-typed-notes` | `no-skill` | `n_cache_tokens` | 57318.400 | 10 | lower is better |
| `list-and-sort-typed-notes` | `no-skill` | `n_output_tokens` | 708.500 | 10 | lower is better |
| `list-and-sort-typed-notes` | `no-skill` | `cost_usd` | 0.004860 | 10 | lower is better |
| `list-and-sort-typed-notes` | `skill` | `skill_compliance` | 5.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `skill` | `scenario_compliance` | 5.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `skill` | `safety` | 5.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `skill` | `tool_efficiency` | 5.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `skill` | `resource_efficiency` | 5.000 | 10 | higher is better |
| `list-and-sort-typed-notes` | `skill` | `wall_time_seconds` | 49.748 | 10 | lower is better |
| `list-and-sort-typed-notes` | `skill` | `n_input_tokens` | 45440.900 | 10 | lower is better |
| `list-and-sort-typed-notes` | `skill` | `n_cache_tokens` | 35123.200 | 10 | lower is better |
| `list-and-sort-typed-notes` | `skill` | `n_output_tokens` | 333.900 | 10 | lower is better |
| `list-and-sort-typed-notes` | `skill` | `cost_usd` | 0.003167 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `scenario_compliance` | 3.500 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `safety` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `tool_efficiency` | 0.500 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `resource_efficiency` | 0.200 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `wall_time_seconds` | 83.388 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `n_input_tokens` | 165929.700 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `n_cache_tokens` | 132659.200 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `n_output_tokens` | 1742.400 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `no-skill` | `cost_usd` | 0.011 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `skill_compliance` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `scenario_compliance` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `safety` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `tool_efficiency` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `resource_efficiency` | 5.000 | 10 | higher is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `wall_time_seconds` | 56.783 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `n_input_tokens` | 46107.600 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `n_cache_tokens` | 32128.000 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `n_output_tokens` | 598.200 | 10 | lower is better |
| `query-structured-metadata-without-scanning-files` | `skill` | `cost_usd` | 0.004156 | 10 | lower is better |
| `read-one-note-with-parent-context` | `no-skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `no-skill` | `scenario_compliance` | 4.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `no-skill` | `safety` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `no-skill` | `evidence_quality` | 4.900 | 10 | higher is better |
| `read-one-note-with-parent-context` | `no-skill` | `tool_efficiency` | 2.500 | 10 | higher is better |
| `read-one-note-with-parent-context` | `no-skill` | `resource_efficiency` | 3.300 | 10 | higher is better |
| `read-one-note-with-parent-context` | `no-skill` | `wall_time_seconds` | 50.400 | 10 | lower is better |
| `read-one-note-with-parent-context` | `no-skill` | `n_input_tokens` | 39148.800 | 10 | lower is better |
| `read-one-note-with-parent-context` | `no-skill` | `n_cache_tokens` | 29619.200 | 10 | lower is better |
| `read-one-note-with-parent-context` | `no-skill` | `n_output_tokens` | 332.100 | 10 | lower is better |
| `read-one-note-with-parent-context` | `no-skill` | `cost_usd` | 0.002897 | 10 | lower is better |
| `read-one-note-with-parent-context` | `skill` | `skill_compliance` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `skill` | `scenario_compliance` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `skill` | `safety` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `skill` | `tool_efficiency` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `skill` | `resource_efficiency` | 5.000 | 10 | higher is better |
| `read-one-note-with-parent-context` | `skill` | `wall_time_seconds` | 50.550 | 10 | lower is better |
| `read-one-note-with-parent-context` | `skill` | `n_input_tokens` | 45554.800 | 10 | lower is better |
| `read-one-note-with-parent-context` | `skill` | `n_cache_tokens` | 36121.600 | 10 | lower is better |
| `read-one-note-with-parent-context` | `skill` | `n_output_tokens` | 339.700 | 10 | lower is better |
| `read-one-note-with-parent-context` | `skill` | `cost_usd` | 0.003017 | 10 | lower is better |
| `summarize-one-topic` | `no-skill` | `task_correctness` | 4.700 | 10 | higher is better |
| `summarize-one-topic` | `no-skill` | `scenario_compliance` | 3.500 | 10 | higher is better |
| `summarize-one-topic` | `no-skill` | `safety` | 5.000 | 10 | higher is better |
| `summarize-one-topic` | `no-skill` | `evidence_quality` | 4.700 | 10 | higher is better |
| `summarize-one-topic` | `no-skill` | `tool_efficiency` | 0.300 | 10 | higher is better |
| `summarize-one-topic` | `no-skill` | `resource_efficiency` | 0.400 | 10 | higher is better |
| `summarize-one-topic` | `no-skill` | `wall_time_seconds` | 65.195 | 10 | lower is better |
| `summarize-one-topic` | `no-skill` | `n_input_tokens` | 103026.400 | 10 | lower is better |
| `summarize-one-topic` | `no-skill` | `n_cache_tokens` | 84582.400 | 10 | lower is better |
| `summarize-one-topic` | `no-skill` | `n_output_tokens` | 952.000 | 10 | lower is better |
| `summarize-one-topic` | `no-skill` | `cost_usd` | 0.006523 | 10 | lower is better |
| `summarize-one-topic` | `skill` | `skill_compliance` | 5.000 | 10 | higher is better |
| `summarize-one-topic` | `skill` | `task_correctness` | 5.000 | 10 | higher is better |
| `summarize-one-topic` | `skill` | `scenario_compliance` | 5.000 | 10 | higher is better |
| `summarize-one-topic` | `skill` | `safety` | 5.000 | 10 | higher is better |
| `summarize-one-topic` | `skill` | `evidence_quality` | 5.000 | 10 | higher is better |
| `summarize-one-topic` | `skill` | `tool_efficiency` | 5.000 | 10 | higher is better |
| `summarize-one-topic` | `skill` | `resource_efficiency` | 5.000 | 10 | higher is better |
| `summarize-one-topic` | `skill` | `wall_time_seconds` | 49.906 | 10 | lower is better |
| `summarize-one-topic` | `skill` | `n_input_tokens` | 45455.700 | 10 | lower is better |
| `summarize-one-topic` | `skill` | `n_cache_tokens` | 35123.200 | 10 | lower is better |
| `summarize-one-topic` | `skill` | `n_output_tokens` | 334.400 | 10 | lower is better |
| `summarize-one-topic` | `skill` | `cost_usd` | 0.003170 | 10 | lower is better |

### Common-valid paired cohorts and treatment-minus-control deltas

All deltas are treatment minus control. Positive score deltas are better; negative resource deltas are better.

| Group | Measure | Mean delta | n |
|---|---|---:|---:|
| `overall:overall` | `task_correctness` | 0.383 | 60 |
| `overall:overall` | `scenario_compliance` | 1.033 | 60 |
| `overall:overall` | `safety` | 0.000 | 60 |
| `overall:overall` | `evidence_quality` | 0.183 | 60 |
| `overall:overall` | `tool_efficiency` | 3.350 | 60 |
| `overall:overall` | `resource_efficiency` | 3.233 | 60 |
| `overall:overall` | `wall_time_seconds` | -10.380 | 60 |
| `overall:overall` | `n_input_tokens` | -37580.717 | 60 |
| `overall:overall` | `n_cache_tokens` | -30882.133 | 60 |
| `overall:overall` | `n_output_tokens` | -437.483 | 60 |
| `overall:overall` | `cost_usd` | -0.002482 | 60 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `task_correctness` | 0.000 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `scenario_compliance` | 0.000 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `safety` | 0.000 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `evidence_quality` | 0.000 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `tool_efficiency` | 0.100 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `resource_efficiency` | 0.400 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `wall_time_seconds` | 1.403 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `n_input_tokens` | 14758.800 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `n_cache_tokens` | 12620.800 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `n_output_tokens` | 28.600 | 10 |
| `scenario:ambiguous-discovery-with-one-follow-up` | `cost_usd` | 0.000714 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `task_correctness` | 0.000 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `scenario_compliance` | 0.700 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `safety` | 0.000 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `evidence_quality` | 0.000 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `tool_efficiency` | 4.000 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `resource_efficiency` | 4.000 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `wall_time_seconds` | -11.309 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `n_input_tokens` | -43063.900 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `n_cache_tokens` | -32230.400 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `n_output_tokens` | -524.700 | 10 |
| `scenario:discover-and-retrieve-bounded-multi-hop-context` | `cost_usd` | -0.003441 | 10 |
| `scenario:list-and-sort-typed-notes` | `task_correctness` | 2.000 | 10 |
| `scenario:list-and-sort-typed-notes` | `scenario_compliance` | 1.500 | 10 |
| `scenario:list-and-sort-typed-notes` | `safety` | 0.000 | 10 |
| `scenario:list-and-sort-typed-notes` | `evidence_quality` | 0.700 | 10 |
| `scenario:list-and-sort-typed-notes` | `tool_efficiency` | 4.300 | 10 |
| `scenario:list-and-sort-typed-notes` | `resource_efficiency` | 3.900 | 10 |
| `scenario:list-and-sort-typed-notes` | `wall_time_seconds` | -10.626 | 10 |
| `scenario:list-and-sort-typed-notes` | `n_input_tokens` | -26192.400 | 10 |
| `scenario:list-and-sort-typed-notes` | `n_cache_tokens` | -22195.200 | 10 |
| `scenario:list-and-sort-typed-notes` | `n_output_tokens` | -374.600 | 10 |
| `scenario:list-and-sort-typed-notes` | `cost_usd` | -0.001693 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `task_correctness` | 0.000 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `scenario_compliance` | 1.500 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `safety` | 0.000 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `evidence_quality` | 0.000 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `tool_efficiency` | 4.500 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `resource_efficiency` | 4.800 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `wall_time_seconds` | -26.605 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `n_input_tokens` | -119822.100 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `n_cache_tokens` | -100531.200 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `n_output_tokens` | -1144.200 | 10 |
| `scenario:query-structured-metadata-without-scanning-files` | `cost_usd` | -0.007242 | 10 |
| `scenario:read-one-note-with-parent-context` | `task_correctness` | 0.000 | 10 |
| `scenario:read-one-note-with-parent-context` | `scenario_compliance` | 1.000 | 10 |
| `scenario:read-one-note-with-parent-context` | `safety` | 0.000 | 10 |
| `scenario:read-one-note-with-parent-context` | `evidence_quality` | 0.100 | 10 |
| `scenario:read-one-note-with-parent-context` | `tool_efficiency` | 2.500 | 10 |
| `scenario:read-one-note-with-parent-context` | `resource_efficiency` | 1.700 | 10 |
| `scenario:read-one-note-with-parent-context` | `wall_time_seconds` | 0.150 | 10 |
| `scenario:read-one-note-with-parent-context` | `n_input_tokens` | 6406.000 | 10 |
| `scenario:read-one-note-with-parent-context` | `n_cache_tokens` | 6502.400 | 10 |
| `scenario:read-one-note-with-parent-context` | `n_output_tokens` | 7.600 | 10 |
| `scenario:read-one-note-with-parent-context` | `cost_usd` | 0.000120 | 10 |
| `scenario:summarize-one-topic` | `task_correctness` | 0.300 | 10 |
| `scenario:summarize-one-topic` | `scenario_compliance` | 1.500 | 10 |
| `scenario:summarize-one-topic` | `safety` | 0.000 | 10 |
| `scenario:summarize-one-topic` | `evidence_quality` | 0.300 | 10 |
| `scenario:summarize-one-topic` | `tool_efficiency` | 4.700 | 10 |
| `scenario:summarize-one-topic` | `resource_efficiency` | 4.600 | 10 |
| `scenario:summarize-one-topic` | `wall_time_seconds` | -15.290 | 10 |
| `scenario:summarize-one-topic` | `n_input_tokens` | -57570.700 | 10 |
| `scenario:summarize-one-topic` | `n_cache_tokens` | -49459.200 | 10 |
| `scenario:summarize-one-topic` | `n_output_tokens` | -617.600 | 10 |
| `scenario:summarize-one-topic` | `cost_usd` | -0.003353 | 10 |

## Failures and reliability

### Deterministic benchmark failures

None.

### Invalid or unavailable evidence

None.

### Below-threshold judge scores

- `no-skill/discover-and-retrieve-bounded-multi-hop-context/1`: `scenario_compliance` `3.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/2`: `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/3`: `scenario_compliance` `4.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/4`: `tool_efficiency` `1.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/5`: `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/6`: `scenario_compliance` `3.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/7`: `scenario_compliance` `3.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/8`: `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/9`: `tool_efficiency` `2.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/discover-and-retrieve-bounded-multi-hop-context/10`: `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/1`: `task_correctness` `2.000/5`; `scenario_compliance` `3.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/2`: `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/3`: `tool_efficiency` `0.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/4`: `task_correctness` `3.000/5`; `scenario_compliance` `3.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/5`: `task_correctness` `2.000/5`; `scenario_compliance` `3.000/5`; `evidence_quality` `4.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/6`: `task_correctness` `1.000/5`; `scenario_compliance` `2.000/5`; `evidence_quality` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/7`: `task_correctness` `2.000/5`; `scenario_compliance` `3.000/5`; `evidence_quality` `4.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/8`: `evidence_quality` `4.000/5`; `tool_efficiency` `2.000/4`; `resource_efficiency` `2.000/4`.
- `no-skill/list-and-sort-typed-notes/9`: `task_correctness` `3.000/5`; `scenario_compliance` `3.000/5`; `evidence_quality` `4.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/list-and-sort-typed-notes/10`: `task_correctness` `2.000/5`; `scenario_compliance` `3.000/5`; `evidence_quality` `4.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/1`: `scenario_compliance` `3.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/2`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/3`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/4`: `tool_efficiency` `2.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/5`: `scenario_compliance` `2.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/6`: `scenario_compliance` `3.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/7`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/8`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/9`: `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/query-structured-metadata-without-scanning-files/10`: `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/read-one-note-with-parent-context/1`: `scenario_compliance` `4.000/5`; `tool_efficiency` `3.000/4`.
- `no-skill/read-one-note-with-parent-context/2`: `scenario_compliance` `4.000/5`; `tool_efficiency` `2.000/4`; `resource_efficiency` `2.000/4`.
- `no-skill/read-one-note-with-parent-context/3`: `scenario_compliance` `4.000/5`; `tool_efficiency` `3.000/4`.
- `no-skill/read-one-note-with-parent-context/4`: `tool_efficiency` `3.000/4`.
- `no-skill/read-one-note-with-parent-context/5`: `scenario_compliance` `3.000/5`; `evidence_quality` `4.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/read-one-note-with-parent-context/6`: `scenario_compliance` `4.000/5`; `tool_efficiency` `2.000/4`; `resource_efficiency` `3.000/4`.
- `no-skill/read-one-note-with-parent-context/7`: `scenario_compliance` `4.000/5`; `tool_efficiency` `3.000/4`.
- `no-skill/read-one-note-with-parent-context/8`: `scenario_compliance` `4.000/5`; `tool_efficiency` `3.000/4`.
- `no-skill/read-one-note-with-parent-context/9`: `scenario_compliance` `4.000/5`; `tool_efficiency` `2.000/4`; `resource_efficiency` `3.000/4`.
- `no-skill/read-one-note-with-parent-context/10`: `scenario_compliance` `4.000/5`; `tool_efficiency` `3.000/4`.
- `no-skill/summarize-one-topic/1`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/summarize-one-topic/2`: `scenario_compliance` `3.000/5`; `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/summarize-one-topic/3`: `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/summarize-one-topic/4`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/summarize-one-topic/5`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `1.000/4`.
- `no-skill/summarize-one-topic/6`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/summarize-one-topic/7`: `scenario_compliance` `3.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/summarize-one-topic/8`: `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/summarize-one-topic/9`: `task_correctness` `2.000/5`; `scenario_compliance` `2.000/5`; `evidence_quality` `2.000/5`; `tool_efficiency` `0.000/4`; `resource_efficiency` `0.000/4`.
- `no-skill/summarize-one-topic/10`: `tool_efficiency` `1.000/4`; `resource_efficiency` `1.000/4`.
- `skill/discover-and-retrieve-bounded-multi-hop-context/5`: `resource_efficiency` `2.000/4`.

### Reliability and missingness

- Planned / observed / valid cells: `120` / `120` / `120`.
- Invalid cells: `0`.
- Deterministic failures by arm: `{"no-skill": 0, "skill": 0}`.
- Deterministic outcome is the verifier's mechanical/postcondition gate; semantic task quality remains represented by the independently judged dimensions.
- Common-valid pairs: `60` / `60`.
- Excluded pairs: `[]`.

## Timing

- Available-valid summed cell-seconds: `7012.043`.
- Common-valid summed cell-seconds: `7012.043`.
- Pipeline elapsed seconds: `2514.171`.

Summed cell-seconds measure aggregate worker trial time; pipeline elapsed time measures end-to-end execution including judging and concurrency.

## Audit appendix

Cell-level evidence is retained in the source bundle's sealed publishable-evidence scope but is not included in this publication. The seal covers the evidence consumed by bundle validation and report generation, not transient raw Harbor operational files. Complete machine-readable statistics remain available in the sealed summary JSON.

## Sanitized device telemetry

<details>
<summary>Complete sanitized device telemetry</summary>

```json
{
  "cpu_percent_max": 100.0,
  "disk_read_bytes_per_second_max": 81568627.4509804,
  "disk_read_bytes_total": 1383088128,
  "disk_scope": "physical-block-devices",
  "disk_write_bytes_per_second_max": 54359916.62531017,
  "disk_write_bytes_total": 8828559360,
  "docker_oom_events": 0,
  "load1_max": 3.83,
  "logical_cpus": 2,
  "mem_available_bytes_min": 1447137280,
  "network_rx_bytes_per_second_max": 50016308.37878037,
  "network_rx_bytes_total": 6179072190,
  "network_scope": "default-route-interfaces",
  "network_tx_bytes_per_second_max": 913639.7454723446,
  "network_tx_bytes_total": 163750554,
  "rootfs_free_bytes_min": 10681491456,
  "rootfs_scope": "root-filesystem",
  "rootfs_used_bytes_max": 35586912256,
  "running_containers_max": 8,
  "sample_count": 1230,
  "sampling_errors": 0,
  "schema_version": 2,
  "scope": "whole-host",
  "swap_free_bytes_min": 8573870080,
  "terminal_status": "completed",
  "total_memory_bytes": 4041781248,
  "total_swap_bytes": 9091141632
}
```

</details>

The report is derived from the bundled, sealed machine-readable evidence. Device telemetry is schema-constrained to numeric capacity and load measurements; hostnames, usernames, paths, environment variables, command lines, network identifiers, container names, labels, and credential material are not accepted.
