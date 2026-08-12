# IWE evaluation suites

## Evaluation runs

- [Default-skill correctness and efficiency](docs/evals/default-skill-correctness-efficiency.md) — verifies the correctness, safety, applicability, evidence quality, and efficiency of the skill directory selected explicitly by each run. [Evidence report](docs/evals/results/default-skill-correctness-efficiency-f571d6f.md).

## A/B test suites

- [Skill-guidance efficiency A/B](docs/evals/skill-guidance-efficiency-ab.md) — measures the causal quality, tool-use, token, and wall-time effect of the default skill against the same IWE runtime without skill guidance; both arms retain the always-present production `AGENTS.md` policy.
- [Context-routing A/B](docs/evals/context-routing-ab.md) — compares IWE CLI only, the skill, and the skill plus the always-present workspace `AGENTS.md` policy on documentation routing, fallback, and authoring-language behavior.
