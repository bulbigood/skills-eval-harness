# Default-skill correctness and efficiency — 2026-08-11

## Result

**FAIL (fail-closed; provider capacity degraded the run).**

This is the published summary of the full run. Interpret it with the [suite methodology](../default-skill-correctness-efficiency.md). The raw machine reports remain generated artifacts and are not committed because they contain large per-sample traces and local runtime metadata.

| Field | Value |
| --- | --- |
| Run ID | `20260811T170027Z-iwe-default-skill-correctness-efficiency` |
| Skills repository | `https://github.com/iwe-org/skills` |
| Skills revision | `f571d6f83dd79407ec64caf7cc3036708062e3c8` |
| Default skill | `iwe-v18` (`0.9.9`) |
| Tested IWE runtime | `0.18.0` |
| Agent | Codex, `weak` worker profile |
| Samples | 10 per scenario |
| Jobs | 10 |
| Matrix | 31 scenarios × 10 samples = 310 cells |

## Validity and acceptance

| Measure | Result |
| --- | ---: |
| Valid samples | 247 / 310 (79.7%) |
| Invalid samples | 63 / 310 (20.3%) |
| Worker provider-capacity failures | 62 |
| Judge process failures | 1 |
| Strictly passing scenario aggregates | 7 / 31 (22.6%) |
| IWE calls observed | 363 |
| Missing, invalid, extra, or mismatched IWE telemetry | 0 |

The 62 worker failures reported `Selected model is at capacity`. The suite is fail-closed, so these samples remain invalid and their scenario aggregates are not repaired or excluded after the fact. Consequently, **7/31 is the strict release result, not a clean estimate of skill quality**.

The passing aggregates were:

- query structured metadata without scanning files;
- create and validate a schema-bound document;
- ambiguous discovery with one follow-up;
- fix code without activating IWE;
- show a bounded subtree;
- rename a note and its links;
- inline while keeping the target.

## Metric observations

Sample-level metric failures, including invalid provider-failed samples:

| Metric | Failed samples |
| --- | ---: |
| Resource efficiency | 93 |
| Tool efficiency | 63 |
| Skill compliance | 60 |
| Task correctness | 58 |
| Scenario compliance | 58 |
| Evidence quality | 56 |
| Safety | 1 |

Resource use across all 310 cells:

| Measure | Total | Mean | Median | Maximum |
| --- | ---: | ---: | ---: | ---: |
| Task tool calls | 671 | 2.16 | 2 | 5 |
| Task tool-output bytes | 5,723,770 | 18,463.77 | 19,843 | 32,372 |
| Estimated task input tokens | 1,431,025 | 4,616.21 | 4,961 | 8,093 |

## Analysis

1. **The harness telemetry path is now sound.** An earlier diagnostic run placed telemetry outside the worker's writable sandbox and was rejected. This run used the corrected workspace-local telemetry path. All 363 observed IWE calls matched command evidence, with zero telemetry defects.
2. **Provider capacity is the dominant validity problem.** Sixty-two of 63 invalid cells were worker capacity failures. At 20.3% invalidity, this run cannot serve as a stable quality baseline even though its strict acceptance outcome is valid under fail-closed rules.
3. **Efficiency is the strongest recurring product concern among completed cells.** Resource efficiency failed in 93 samples, more often than any correctness or compliance dimension. The median task context was 19,843 bytes (about 4,961 estimated input tokens), and the median task used two tool calls.
4. **Safety was robust.** Only one sample failed the safety threshold. The broad failures are not primarily unsafe behavior; they are provider invalidity plus correctness, compliance, and context-volume issues.
5. **The successful scenarios show that the skill can be both correct and bounded.** Structured metadata queries, schema-bound creation, bounded subtree reads, rename/inline mutations, ambiguity handling, and the non-IWE applicability boundary all passed their ten-sample aggregate gates.

## Conclusion

The release gate fails. The result identifies two separate next steps:

- add bounded retry/resume support for transient worker capacity errors, then rerun the same frozen matrix;
- independently reduce guidance/retrieval context and tool overhead before treating efficiency as acceptable.

Until a rerun reaches the suite's validity requirements without provider-capacity contamination, this report should be treated as a diagnostic fail-closed run rather than the canonical quality baseline.

### Follow-up

Bounded process retry was implemented after this run. It retries recognized transient provider-capacity failures only before any tool execution, makes at most four attempts with bounded backoff, and preserves fail-closed behavior after tool execution. A five-sample parallel smoke run then completed with 5/5 valid samples and a passing aggregate. This historical 310-cell result is intentionally unchanged; a new full frozen-matrix run is still required before replacing it as the quality baseline.