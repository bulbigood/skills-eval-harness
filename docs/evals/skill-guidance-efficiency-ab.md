# Skill-guidance efficiency A/B

## Purpose

This paired A/B suite estimates the causal effect of skill guidance relative to the same installed IWE runtime with no skill. It focuses on retrieval tasks where route selection, bounds, stopping behavior, and context size materially affect cost and latency.

## Test conditions

- Source repository: `https://github.com/iwe-org/skills`; the latest `HEAD` is resolved once and recorded by exact commit.
- Skill selection: `default_skill` from the fetched checkout's `config.toml`.
- Both arms use the same IWE CLI binary, version, fixture, request, production `AGENTS.md`, agent, judge, and sample seed.
- The shared `AGENTS.md` is rendered from `tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl`; it is always present and contains no command fast paths that duplicate the skill.
- The treatment uses the current upstream default skill; the control sets `skill_mode = "none"`.
- Shared policy cost, skill activation, and reference reads are included in resource accounting.
- Scheduling uses balanced paired waves to reduce wall-time bias.
- Agent/judge profile: `weak` by default.
- Samples: 10 paired samples per arm and scenario.
- Concurrency: four jobs per available physical CPU core, capped at 20 and rounded down to a complete two-arm group.

## Arms

| Arm | Condition |
| --- | --- |
| Default skill | Production `AGENTS.md`, IWE runtime, and the skill selected by upstream `default_skill`. |
| No skill | The identical production `AGENTS.md` and IWE runtime exposed without skill guidance. |

## Scenarios

| Scenario ID | Fixture | Why it is included |
| --- | --- | --- |
| `discover-and-retrieve-bounded-multi-hop-context` | `seventeen-centuries` | Tests one-pass bounded synthesis instead of discovery followed by repeated reads. |
| `query-structured-metadata-without-scanning-files` | `seventeen-centuries` | Tests direct structured graph querying instead of filesystem scanning. |
| `ambiguous-discovery-with-one-follow-up` | `pkm-demo-api-project` | Tests bounded discovery with exactly one justified follow-up read and a stopping rule. |

## Fixtures and deterministic contracts

The treatment and control receive byte-identical fixture copies. Fixture-derived oracles establish the expected keys, relationships, summaries, and allowed evidence. Deterministic telemetry verifies call count, command family, bounds, fallback behavior, output volume, skill activation, and prohibited documentation or filesystem exploration. Pair IDs bind the two arms to the same scenario and sample index.

## Evaluation method

Correctness, scenario compliance, skill compliance, safety, and evidence quality remain quality gates for both arms. The A/B decision compares `tool_efficiency` and `resource_efficiency`, including activation cost. Reports include paired pass-rate deltas, tool calls, token/resource usage, worker duration, and bootstrap timing summaries. A speedup is accepted only when quality and safety do not regress; faster wrong answers remain, technically speaking, wrong.

## Run

### Script parameters

| Parameter | Default | Behavior |
| --- | --- | --- |
| `--agent {codex,claude}` | `codex` | Selects both worker and judge. `codex` uses the `weak` model profile; `claude` uses the `medium` model profile. Both A/B arms use the same selection. |
| `--samples N` | `10` | Sets paired samples per arm and selected scenario. |
| `--jobs N` | `min(physical cores × 4, 20)` | Sets requested concurrency. The runner clamps it to `1..20`, then rounds down to an even value; values below two become one complete two-arm group. The final balanced wave may be smaller. |
| `--scenario ID` | all 3 suite scenarios | Restricts the matrix to an exact scenario ID. Repeat to select multiple scenarios. |
| `--results-file PATH` | `tests/eval/results/skill-guidance-efficiency-ab.md` | Sets the generated Markdown result path. Raw immutable reports remain under `tests/eval/reports/`. |
| `--repository URL_OR_PATH` | `https://github.com/iwe-org/skills` | Selects the source repository whose exact `HEAD` and configured `default_skill` are tested. |
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
```

Use `--samples 1` for a bounded six-cell smoke run; repeat `--scenario` to select a subset when diagnosing one route.

A new Markdown report defaults to `tests/eval/results/skill-guidance-efficiency-ab.md`. Generated results are intentionally untracked.

## Matrix and model cost

- 2 arms × 3 scenarios × 10 samples = **60 cells**.
- **60 worker calls** and **60 judge calls**.
- `--list` makes no model calls.
