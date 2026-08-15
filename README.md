# IWE skills evaluation harness

This repository evaluates IWE agent skills with [Harbor](https://github.com/harbor-framework/harbor). Both Codex and Claude Code execute as Harbor-installed agents inside Docker-compatible containers. Deterministic verification runs in a separate, no-network verifier container.

## Security model

- Worker output is untrusted evidence, never prompt instructions.
- Judge responses are validated locally with a strict Pydantic/JSON schema.
- Every metric requires a rationale and one or more valid evidence IDs.
- Worker and verifier sandboxes use explicit network policies.
- Only the selected agent provider credential is forwarded. Host credential files are never copied.
- Published reports are derived from complete machine-readable summaries and content-bound provenance.

## Installation

```bash
uv sync --all-groups
uv run skills-eval validate
```

The dependency lock pins Harbor `0.21.0`. Rollouts require Docker Engine with Compose and Buildx support. Podman is deliberately rejected because Harbor's Docker backend depends on Docker-specific Compose, Buildx, and copy semantics.

### Codex authentication

API-key authentication remains the default. It requires `OPENAI_API_KEY`:

```bash
uv run skills-eval run ... --agent codex --codex-auth api-key
```

To use included ChatGPT subscription access, first create a dedicated file-backed Codex login:

```bash
install -d -m 700 "$HOME/.codex-harbor"
printf '%s\n' 'cli_auth_credentials_store = "file"' 'forced_login_method = "chatgpt"' > "$HOME/.codex-harbor/config.toml"
CODEX_HOME="$HOME/.codex-harbor" codex login
chmod 600 "$HOME/.codex-harbor/auth.json"
```

Then select it explicitly:

```bash
uv run skills-eval run ... \
  --agent codex \
  --codex-auth chatgpt \
  --judge-auth chatgpt \
  --codex-auth-json "$HOME/.codex-harbor/auth.json"
```

The source file must be owned by the current user, regular JSON, non-symlinked, no larger than 1 MiB, and mode `0600` or stricter. The harness copies it to a private generic temporary path, and Harbor uploads it to `/tmp/codex-secrets`. Both layers clean up in `finally`; Harbor also uses a disposable environment. A hard process or daemon crash can still leave an orphaned container, so subscription-auth runs belong only on a trusted private runner. The source path, credential bytes, and credential digest are never added to datasets, provenance, reports, or run seals.

`--judge-auth chatgpt` runs the structured judge through an ephemeral, read-only Codex CLI sandbox using a separate temporary copy of the same explicitly selected login. `--judge-auth api-key` preserves the Responses API backend and requires `OPENAI_API_KEY`. Both backends feed the same strict local schema and evidence-reference validator. Claude workers continue to require `ANTHROPIC_API_KEY`.

### Global concurrency

`execution.global_concurrency` defaults to `2`. `--jobs N` overrides it for one run. The value is a global Harbor trial ceiling, not a per-arm allowance: paired arms run concurrently with an equal static share (`1 + 1` at the default). An odd spare slot remains unused rather than biasing one arm. If the limit is smaller than the arm count, arms run in deterministic one-slot batches. The resolved allocation is recorded in `run-manifest.json`.

Every completed run records a terminal cell for every planned identity and produces schema-constrained `device-telemetry.json` containing numeric capacity and load measurements only. A failing suite is sealed for diagnosis and exits nonzero. `--run-purpose diagnostic` is the default and can never be published. Publication accepts only a passing `production` run with at least the suite's preregistered `default_samples`, revalidates and recomputes the sealed bundle, then stages the report, checksum, telemetry, cells, Harbor locks/results, trajectories, semantic oracle, verifier evidence, immutable inputs, manifests, and seal. Unexpected telemetry fields such as hostnames, paths, commands, labels, network identifiers, or credential material fail closed.

## Suites

- [Default-skill correctness and efficiency](docs/evals/default-skill-correctness-efficiency.md)
- [Skill-guidance efficiency A/B](docs/evals/skill-guidance-efficiency-ab.md)

Published historical evidence remains available under [`docs/evals/results`](docs/evals/results). Those reports are static records from the previous harness and are not accepted as inputs by the Harbor pipeline.

## Commands

```bash
uv run skills-eval validate
uv run skills-eval prepare --help
uv run skills-eval run --help
uv run skills-eval publish --help
```

Start with one scenario, one sample, and the default diagnostic purpose. A full production matrix performs paid worker and judge calls and should only follow a successful smoke run; explicitly pass `--run-purpose production` only for the preregistered matrix intended for publication.
