# Skill-guidance efficiency A/B

## Purpose

This paired A/B suite estimates the causal effect of skill guidance relative to the same installed IWE runtime with no skill. It focuses on retrieval tasks where route selection, bounds, stopping behavior, and context size materially affect cost and latency.

## Test conditions

- Skill source: a local directory, `file://` URI, or GitHub `/tree/REF/PATH` directory URL.
- GitHub refs are resolved and recorded as exact commits; local payloads are content-hashed.
- Both arms use the same IWE CLI binary, version, fixture, request, agent, judge, and sample seed.
- No `AGENTS.md` is installed by default, matching the current IWE runtime.
- Future production policy can be supplied explicitly with `--agents-template-source`; the resolved text/template is installed identically in both arms so it is not conflated with the skill treatment.
- The treatment uses the skill selected by `--skill-source`; the control sets `skill_mode = "none"`.
- Skill activation and reference reads are included in resource accounting. When an optional shared policy is supplied, its rendered cost is included identically in both arms.
- Scheduling uses balanced paired waves to reduce wall-time bias.
- Agent/judge profile: `weak` by default.
- Samples: 10 paired samples per arm and scenario.
- Concurrency: four jobs per available physical CPU core, capped at 32 and rounded down to a complete two-arm group.

## Arms

| Arm | Condition |
| --- | --- |
| Default skill | IWE runtime and the selected skill. |
| No skill | The identical IWE runtime exposed without skill guidance. |

## Scenarios

| Scenario ID | Fixture | Why it is included |
| --- | --- | --- |
| `summarize-one-topic` | `pkm-demo-core-read` | Tests whether a short common request stays one-pass despite skill activation overhead. |
| `read-one-note-with-parent-context` | `pkm-demo-core-read` | Tests one bounded parent expansion instead of relationship discovery plus separate reads. |
| `list-and-sort-typed-notes` | `pkm-demo-core-read` | Tests typed projection and server-side sorting without loading note bodies or scanning files. |
| `discover-and-retrieve-bounded-multi-hop-context` | `seventeen-centuries` | Tests one-pass bounded synthesis instead of discovery followed by repeated reads. |
| `query-structured-metadata-without-scanning-files` | `seventeen-centuries` | Tests direct structured graph querying instead of filesystem scanning. |
| `ambiguous-discovery-with-one-follow-up` | `pkm-demo-api-project` | Tests bounded discovery with exactly one justified follow-up read and a stopping rule. |

## Fixtures and deterministic contracts

The treatment and control receive byte-identical fixture copies. Fixture-derived oracles establish the expected keys, relationships, summaries, and allowed evidence. Deterministic telemetry verifies call count, command family, bounds, fallback behavior, output volume, skill activation, and prohibited documentation or filesystem exploration. Pair IDs bind the two arms to the same scenario and sample index.

## Evaluation method

Correctness, scenario compliance, skill compliance, safety, and evidence quality remain measured for both arms. The treatment must pass those quality gates; the control remains fully reported and may fail them because discovering that the unguided baseline produces a wrong answer is a legitimate treatment effect, not an infrastructure failure. Safety and sample validity remain fail-closed across both arms. The A/B decision compares `tool_efficiency` and `resource_efficiency`, including activation cost. These efficiency dimensions are excluded from standalone arm acceptance because their purpose is paired comparison, not absolute route conformance. Reports include paired pass-rate deltas, tool calls, token/resource usage, worker duration, and bootstrap timing summaries. A speedup is accepted only when treatment quality and safety do not regress; faster wrong answers remain, technically speaking, wrong.

The runner exits successfully only when every cell is valid, every arm passes safety, and the guided treatment passes all applicable non-efficiency quality gates. Control failures remain visible in target aggregates, the problem ledger, and paired comparisons. `skill_compliance` is N/A when no skill is installed.

## Run

### Script parameters

| Parameter | Default | Behavior |
| --- | --- | --- |
| `--agent {codex,claude}` | `codex` | Selects both worker and judge. `codex` uses the `weak` model profile; `claude` uses the `medium` model profile. Both A/B arms use the same selection. |
| `--samples N` | `10` | Sets paired samples per arm and selected scenario. |
| `--jobs N` | `min(physical cores × 4, 32)` | Sets requested concurrency. The runner clamps it to `1..32`, then rounds down to an even value; values below two become one complete two-arm group. The final balanced wave may be smaller. |
| `--scenario ID` | all 6 suite scenarios | Restricts the matrix to an exact scenario ID. Repeat to select multiple scenarios. |
| `--results-file PATH` | `tests/eval/results/skill-guidance-efficiency-ab.md` | Sets the generated Markdown result path. Raw immutable reports remain under `tests/eval/reports/`. |
| `--publish-output PATH` | unset | After a successful complete 120-cell run, invokes the fail-closed publisher and writes a sanitized tracked report under `docs/evals/results/`. Partial and smoke matrices are rejected. |
| `--skill-source SOURCE` | GitHub URL for `iwe-v18` | Selects one skill directory as a local path, `file://` URI, or GitHub `/tree/REF/PATH` URL. Repository roots are rejected. |
| `--agents-template-source SOURCE` | unset | Optionally loads the exact `AGENTS.md` text/template from a local path, `file://` URI, or HTTPS URL and installs it identically in both arms. The response body is the template; HTML page URLs are therefore invalid inputs even if they display the file. |
| `--list` | disabled | Resolves the source and prints the selected matrix without worker or judge calls. |

Examples:

```bash
# Full paired evaluation with Claude workers and judges.
uv run --with-requirements tests/eval/requirements.txt python scripts/run_skill_guidance_efficiency_ab.py --agent claude

# One-sample, one-scenario Codex smoke run; two jobs preserve arm balance.
uv run --with-requirements tests/eval/requirements.txt python scripts/run_skill_guidance_efficiency_ab.py --samples 1 --jobs 2 --scenario ambiguous-discovery-with-one-follow-up
```

```bash
uv run --with-requirements tests/eval/requirements.txt python scripts/run_skill_guidance_efficiency_ab.py --list
uv run --with-requirements tests/eval/requirements.txt python scripts/run_skill_guidance_efficiency_ab.py

# Full production evaluation followed by fail-closed publication.
uv run --with-requirements tests/eval/requirements.txt python scripts/run_skill_guidance_efficiency_ab.py \
  --publish-output docs/evals/results/skill-guidance-efficiency-ab-f571d6f.md
```

Use `--samples 1` for a bounded twelve-cell smoke run; repeat `--scenario` to select a subset when diagnosing one route.

A new Markdown report defaults to `tests/eval/results/skill-guidance-efficiency-ab.md`. Generated results are intentionally untracked.

## Matrix and model cost

- 2 arms × 6 scenarios × 10 samples = **120 cells**.
- **120 worker calls** and **120 judge calls**.
- `--list` makes no model calls.
