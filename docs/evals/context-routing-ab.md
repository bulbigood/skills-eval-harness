# Context-routing A/B

## Purpose

This three-arm comparative suite verifies how an agent routes documentation work when IWE's production workspace `AGENTS.md` policy is always present. The policy contains applicability, document-scope, fallback, IWE-root, and authoring-language context; it deliberately contains no command fast paths that duplicate the skill.

## Test conditions

- All arms use the same pinned IWE runtime, fixture, request, agent, judge, and sample index.
- The skill arms use `iwe-v18`; the policy arm adds a rendered workspace `AGENTS.md`.
- The policy is rendered from `tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl` by `scripts/render_iwe_context_agents.py`.
- Defaults: IWE root `.`, IWE document scope `project documentation`, authoring language `English`.
- Scenarios may override `iwe_root`, `iwe_documents`, and `iwe_language` through `agents_context`.
- Guidance bytes and activation are included in resource accounting.
- Samples: 10 per arm and scenario.
- Concurrency: 15 jobs in balanced waves.

## Arms

| Arm | Condition |
| --- | --- |
| `iwe-cli-only` | IWE runtime is available, but no skill or workspace policy is installed. |
| `iwe-v18` | IWE runtime plus the skill, without the rendered workspace policy. |
| `iwe-v18-agents` | The same runtime and skill plus the always-present rendered `AGENTS.md` policy. |

## Scenarios

| Scenario ID | Fixture | Routing contract |
| --- | --- | --- |
| `route-listed-runbook-through-iwe` | `pkm-demo-context-routing` | A declared operational runbook must use IWE immediately; after a hit, ordinary filesystem search is forbidden. |
| `route-unlisted-guide-through-workspace` | `pkm-demo-context-routing` | An undeclared contributor guide must use ordinary workspace search without invoking IWE. |
| `fallback-after-listed-iwe-miss` | `pkm-demo-context-routing` | A declared document must try IWE first and use filesystem fallback only after the recorded miss. |
| `fallback-when-iwe-is-unavailable` | `pkm-demo-update` | If the IWE CLI cannot run, ordinary workspace fallback must still return the correct fact. |
| `create-iwe-document-in-declared-language` | `pkm-demo-context-routing` | A new IWE document must use the policy's authoring language regardless of request language, without reading `.iwe/config.toml`. |

## Fixtures and deterministic contracts

The routing fixture separates graph documents from ordinary workspace documentation so route choice is independently observable. `required_route` selects one of `iwe-only`, `filesystem-only`, or `iwe-then-filesystem`. The harness rejects missing IWE calls, IWE use for undeclared document kinds, fallback before a miss, fallback after a hit, and forbidden configuration reads. Creation is checked from the before/after snapshot and an independent authoring-language oracle. Rendered policy context, byte size, and SHA-256 are recorded for every treated sample.

## Evaluation method

An independent judge scores task correctness, scenario compliance, skill compliance, safety, evidence quality, tool efficiency, and resource efficiency. Deterministic routing and filesystem gates apply before aggregate scoring and cannot be overridden by a plausible final answer. Comparisons include activation cost and use balanced waves. The suite evaluates both absolute per-arm acceptance and differences between CLI-only, skill-only, and production-policy behavior.

## Run

```bash
uv run --with-requirements tests/eval/requirements.txt python scripts/run_iwe_context_routing_ab.py --list
uv run --with-requirements tests/eval/requirements.txt python scripts/run_iwe_context_routing_ab.py
```

The Markdown report defaults to `tests/eval/results/iwe-context-routing-ab.md`.

## Matrix and model cost

- 3 arms × 5 scenarios × 10 samples = **150 cells**.
- **150 worker calls** and **150 judge calls**.
- `--list` makes no model calls.
