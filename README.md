# IWE skills evaluation harness

This repository evaluates IWE agent skills with [Harbor](https://github.com/harbor-framework/harbor). Both Codex and Claude Code execute as Harbor-installed agents inside Docker-compatible containers. Deterministic verification runs in a separate, no-network verifier container.

## Security model

- Worker output is untrusted evidence, never prompt instructions.
- Judge responses are validated locally with a strict Pydantic/JSON schema.
- Every metric requires a non-whitespace rationale and one or more unique, valid evidence IDs.
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

`--judge-auth chatgpt` runs the structured judge through an ephemeral, read-only Codex CLI sandbox using a separate temporary copy of the same explicitly selected login. The credential home is mounted outside the judge-visible `/work` directory, and the harness rejects every unknown JSONL lifecycle event or item type as well as any tool-use item before accepting a verdict. `--judge-auth api-key` preserves the Responses API backend and requires `OPENAI_API_KEY`. Both backends feed the same strict local schema and evidence-reference validator. Claude workers continue to require `ANTHROPIC_API_KEY`.

### Concurrency

`execution.global_concurrency` defaults to `2`; `--jobs N` overrides the global Harbor worker ceiling. Paired arms receive an equal static share (`1 + 1` by default). Odd spare slots remain unused rather than biasing one arm.

`judge.concurrency` defaults to `4`; `--judge-jobs N` overrides judge concurrency independently. Judged cells execute concurrently but are written in canonical input order. Both resolved concurrency values are bound in the manifest and provenance.

Completed trials with deterministic task failures remain valid, judged experimental outcomes. Exceptions, malformed verifier evidence, judge failures, missing cells, or telemetry failures remain invalid. `summary.valid` represents evidence integrity; `summary.pass` describes the benchmark result. A structurally valid failing production benchmark may therefore be sealed and published with an explicit **FAIL** verdict.

`device-telemetry.json` persists CPU, memory, default-route network, physical-device disk I/O, root-filesystem usage, OOM, and sampling-failure measurements. Publication always revalidates the sealed production bundle and stages the report plus checksum. The evidence bundle is omitted by default; pass `--include-evidence` to additionally copy, revalidate, and stage telemetry, cells, Harbor artifacts, immutable inputs, manifests, and seal. Sensitive or unexpected telemetry fields fail closed.

## Suites

- [Default-skill correctness and efficiency](docs/evals/default-skill-correctness-efficiency.md)
- [Skill-guidance efficiency A/B](docs/evals/skill-guidance-efficiency-ab.md)

## Commands

```bash
uv run skills-eval validate
uv run skills-eval prepare --help
uv run skills-eval run --help
uv run skills-eval publish --help
```

Start with one scenario, one sample, and the default diagnostic purpose. A full production matrix performs paid worker and judge calls and should only follow a successful smoke run; explicitly pass `--run-purpose production` only for the preregistered matrix intended for publication.
