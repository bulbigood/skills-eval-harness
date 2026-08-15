# Default-skill correctness and efficiency

## Purpose

This absolute suite evaluates the selected IWE skill and exact IWE runtime across the scenario catalog declared in `evals/suites/default-skill.yaml`.

## Contract

- `evals/config.yaml`, the suite YAML, and `evals/scenarios/iwe.yaml` are strict inputs.
- The skill source must resolve to a clean, exact Git commit and content digest.
- The runtime must print the exact requested version and is hashed before use.
- Every scenario becomes a Harbor task with a pinned base-image digest.
- The worker uses an allowlisted network policy. Deterministic verification runs in a separate no-network container.
- Judge output is schema-validated locally and every metric must cite known evidence IDs.
- Missing, duplicate, invalid, unfinished, or shared-verifier cells fail closed.

## Smoke run

Materialize the pinned fixture repositories first, then run one scenario and one sample:

```bash
uv run skills-eval run \
  --suite evals/suites/default-skill.yaml \
  --skill-source ../iwe-skills/skills/iwe-v18 \
  --runtime /absolute/path/to/iwe \
  --runtime-version 0.18.0 \
  --fixture seventeen-centuries=/absolute/path/to/seventeen-centuries \
  --fixture pkm-demo=/absolute/path/to/pkm-demo \
  --agent codex \
  --scenario read-one-known-note \
  --samples 1 \
  --jobs 1
```

Use `--agent claude` for Claude Code. The command forwards only that agent's provider key. It does not read or copy Codex `auth.json`, Claude host state, `.env`, cloud credentials, or unrelated tokens.

## Production acceptance

A production report may be published only from a complete, valid, passing Harbor run whose harness tree is clean. The publisher recomputes the verdict from `summary.json`, validates `provenance.json`, derives the canonical repository from the `upstream` Git remote, refuses replacement, and emits a SHA-256 sidecar.
