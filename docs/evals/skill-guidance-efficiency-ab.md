# Skill-guidance efficiency A/B

## Purpose

This paired suite measures the effect of the selected skill relative to the same runtime without skill guidance. `evals/suites/skill-guidance-ab.yaml` is the suite SSOT.

## Pairing and containment

Each `(scenario, sample)` pair is run as two separate Harbor jobs:

- `skill`: Harbor injects the resolved skill.
- `no-skill`: no skill is injected.

The generated task bytes, pinned image, runtime, fixture, instruction, resource limits, agent implementation, network allowlist, timeout, verifier image, and verifier policy are identical. Only Harbor's skill injection option differs. A preflight rejects structural drift.

Both Codex and Claude Code use the same Harbor Docker environment implementation. Only explicitly selected credentials are staged. Deterministic verification runs in a separate no-network container.

## Judge safety

The worker trajectory, command telemetry, workspace manifest, and oracle data are serialized as an untrusted JSON evidence envelope. They are never concatenated into the judge's system instruction. Judge output must match the strict schema, contain all seven dimensions, include substantive rationales, and cite only known evidence IDs. Bare scores and unknown citations are invalid cells.

## Smoke run

```bash
uv run skills-eval run \
  --suite evals/suites/skill-guidance-ab.yaml \
  --skill-source ../iwe-skills/skills/iwe-v18 \
  --runtime /absolute/path/to/iwe \
  --runtime-version 0.18.0 \
  --fixture seventeen-centuries=/absolute/path/to/seventeen-centuries \
  --fixture pkm-demo=/absolute/path/to/pkm-demo \
  --agent codex \
  --codex-auth chatgpt \
  --judge-auth chatgpt \
  --codex-auth-json "$HOME/.codex-harbor/auth.json" \
  --scenario ambiguous-discovery-with-one-follow-up \
  --samples 1
```

The smoke uses the configured global concurrency limit of `2`, split evenly as `1 + 1` across the paired arms. `--jobs N` overrides that global ceiling; it is never multiplied by the arm count.

Run the same bounded smoke with `--agent claude` before expanding the matrix. Full runs are paid and should follow smoke repair cycles.

## Provenance and publication

The run records exact source and harness commits, tree hashes for the source and selected skill, runtime identity, suite, scenario catalog and frozen config, Harbor task checksums, image digests, Harbor version, and sanitized numeric device telemetry. Publication rejects dirty, incomplete, structurally invalid, mismatched, sensitive-telemetry, or already-published inputs. A structurally valid benchmark failure remains publishable as an observed outcome. Publication stages the report and checksum by default; `--include-evidence` additionally stages the complete sealed evidence bundle. There is no compatibility path for old TOML manifests or old host-process reports.

The schema-v5 report uses the common identity/status, arm/model, judge, provenance, acceptance, overall/per-scenario/per-family results, failures/reliability, timing, and audit contract. It additionally reports common-valid cohorts, treatment-minus-control deltas, excluded pairs, and explicitly distinguishes threshold acceptance from an unasserted statistical-superiority verdict. Summary schemas v3 and v4 are unsupported and fail closed.
