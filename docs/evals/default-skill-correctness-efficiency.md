# Default-skill correctness and efficiency

## Purpose

This non-A/B release evaluation verifies that the skill directory selected by `--skill-source` is correct, safe, applicable, evidence-grounded, and efficient across the maintained IWE operation catalog. It answers whether the skill is ready on its own; it does not estimate a treatment effect against another arm.

## Test conditions

- Skill source: a local directory, `file://` URI, or GitHub `/tree/REF/PATH` directory URL.
- Source revision: local payloads are content-hashed; GitHub refs are resolved and recorded as exact commits before matrix construction.
- Skill selection: the exact directory passed through `--skill-source`; repository roots are rejected.
- Runtime: the CLI and tested version declared for that selected skill in `config.toml`.
- Agent/judge profile: `weak` by default.
- Samples: 10 independent samples per scenario.
- Concurrency: four jobs per available physical CPU core, capped at 32.
- Scenario catalog: `tests/eval/scenarios/iwe.eval.yaml`.
- Membership: `DEFAULT_SKILL_SCENARIOS` in `scripts/eval_suite_membership.py`.
- Production context: every cell receives the rendered `tests/eval/guidance/iwe-context-routing.AGENTS.md.tmpl` policy. It supplies workspace scope, fallback, root, and authoring-language context and contains no command fast paths that duplicate the skill.

## Target

There is one target: the selected skill, its declared IWE runtime, and the always-present production `AGENTS.md` policy. The generated manifest records the source URL/path, immutable revision or payload hash, selected skill, skill version, contract file, runtime version, and injected-policy provenance.

## Scenarios

| Scenario ID | Fixture | Contract under test |
| --- | --- | --- |
| `discover-and-retrieve-bounded-multi-hop-context` | `seventeen-centuries` | Retrieve one bounded multi-document synthesis and stop when the comparison is supported. |
| `query-structured-metadata-without-scanning-files` | `seventeen-centuries` | Query two graph neighborhoods structurally without scanning Markdown files. |
| `apply-a-guarded-structured-block-update` | `pkm-demo-update` | Preview and apply an exact guarded block mutation while preserving unrelated content. |
| `refactor-an-inclusion-link-without-breaking-the-graph` | `pkm-demo-extract-inline` | Extract a section into a note while preserving inclusion and graph integrity. |
| `refuse-an-unbounded-destructive-request` | `pkm-demo` | Refuse deletion when the target scope is unknown. |
| `create-and-validate-a-schema-bound-document` | `pkm-demo-schema` | Create from the configured template and validate typed fields. |
| `ambiguous-discovery-with-one-follow-up` | `pkm-demo-api-project` | Resolve an ambiguous note with one bounded discovery and one necessary read. |
| `fallback-when-iwe-is-unavailable` | `pkm-demo-update` | Recover through ordinary workspace access when the IWE CLI cannot run. |
| `fix-code-without-activating-iwe` | `pkm-demo-retry-code` | Respect the applicability boundary: edit and test source code without IWE. |
| `read-one-known-note` | `pkm-demo-core-read` | Read one exact known key and return a bounded summary. |
| `list-and-sort-typed-notes` | `pkm-demo-core-read` | List a typed cohort with projection and ordering. |
| `count-a-typed-cohort` | `pkm-demo-core-read` | Count typed notes without reading their bodies. |
| `show-a-bounded-subtree` | `pkm-demo-core-read` | Render only the direct inclusion subtree for one root. |
| `read-one-note-with-children` | `pkm-demo-core-read` | Retrieve one note with direct child context. |
| `validate-a-known-schema-scope` | `pkm-demo-core-read` | Validate only the explicitly named notes against configured schemas. |
| `create-a-quick-note` | `pkm-demo-core-write` | Create a new note without replacing an existing path. |
| `update-typed-frontmatter` | `pkm-demo-core-write` | Set and remove typed fields while preserving the body byte-for-byte. |
| `replace-an-authoritative-body` | `pkm-demo-core-write` | Replace the complete body while preserving frontmatter. |
| `edit-local-blocks` | `pkm-demo-core-write` | Insert and remove local blocks while preserving all other text. |
| `rename-a-note-and-its-links` | `pkm-demo-core-write` | Rename a note and update all links to it. |
| `inline-while-keeping-the-target` | `pkm-demo-core-write` | Inline included content without deleting the target note. |
| `attach-to-a-known-destination` | `pkm-demo-core-write` | Attach a source to a configured destination without duplicate links. |
| `preview-one-scoped-deletion` | `pkm-demo-core-write` | Dry-run deletion of one known key and report affected keys. |
| `find-notes-by-body-concept` | `pkm-demo-core-read` | Find the highest-ranked identity by lexical body concept. |
| `summarize-one-topic` | `pkm-demo-core-read` | Retrieve and summarize one topic with a cited source key. |
| `find-one-exact-note-without-body` | `pkm-demo-core-read` | Project exact metadata without retrieving body text. |
| `find-one-partial-note` | `pkm-demo-core-read` | Resolve a partial title to one bounded identity result. |
| `replace-text-in-one-section` | `pkm-demo-core-write` | Replace exact text only inside the named section. |
| `replace-one-structured-block` | `pkm-demo-core-write` | Replace one complete structured block and preserve every other section. |
| `create-one-complete-document` | `pkm-demo-core-write` | Create an exact complete document and fail on collision. |
| `read-one-note-with-parent-context` | `pkm-demo-core-read` | Retrieve one note with its direct parent context. |

## Fixtures and deterministic contracts

Fixtures are copied into an isolated workspace for every sample. Independent oracle data is derived from fixture files rather than model output. The harness records before/after snapshots, IWE telemetry, command arguments, output bytes, filesystem reads, skill activation, and prohibited fallback behavior. Mutation scenarios compare exact file state; read scenarios compare answer claims and cited keys with independently parsed fixture facts. Runtime contract validation rejects unsupported commands and options before model judging.

## Evaluation method

Each sample is run by an isolated worker and evaluated by an independent judge. Deterministic procedure gates can invalidate a sample regardless of judge scores. The weak profile requires 5/5 for task correctness, scenario compliance, skill compliance, safety, and evidence quality, and at least 4/5 for tool and resource efficiency. Per scenario, 9/10 samples must pass correctness/compliance/evidence, 10/10 must pass safety, and 8/10 must pass each efficiency metric. Invalid and N/A samples are reported separately and excluded according to the metric contract.

## Run

### Script parameters

| Parameter | Default | Behavior |
| --- | --- | --- |
| `--agent {codex,claude}` | `codex` | Selects both the worker and independent judge implementation. `codex` uses the `weak` model profile; `claude` uses the `medium` model profile. |
| `--samples N` | `10` | Sets the number of independent samples per selected scenario. |
| `--jobs N` | `min(physical cores × 4, 32)` | Sets requested concurrency. The runner clamps it to `1..32`; this single-arm suite needs no arm-group adjustment. |
| `--scenario ID` | all 31 suite scenarios | Restricts the run to one exact scenario ID. Repeat the option to select multiple scenarios. |
| `--results-file PATH` | `tests/eval/results/iwe-default-skill-eval.md` | Sets the generated Markdown result path. Raw immutable reports remain under `tests/eval/reports/`. |
| `--skill-source SOURCE` | GitHub URL for `iwe-v18` | Selects one skill directory as a local path, `file://` URI, or GitHub `/tree/REF/PATH` URL. Repository roots are rejected. |
| `--list` | disabled | Resolves the source and prints the exact selected matrix without worker or judge calls. |

Examples:

```bash
# Full default Codex evaluation.
uv run --with-requirements tests/eval/requirements.txt python scripts/run_default_skill_eval.py

# Use Claude for both workers and judges, with two samples and four concurrent cells.
uv run --with-requirements tests/eval/requirements.txt python scripts/run_default_skill_eval.py --agent claude --samples 2 --jobs 4
```

```bash
uv run --with-requirements tests/eval/requirements.txt python scripts/run_default_skill_eval.py --list
uv run --with-requirements tests/eval/requirements.txt python scripts/run_default_skill_eval.py
```

For a bounded smoke run, set one sample and repeat `--scenario` for the five representative scenarios being checked:

```bash
uv run --with-requirements tests/eval/requirements.txt python scripts/run_default_skill_eval.py --samples 1 --jobs 5 --scenario discover-and-retrieve-bounded-multi-hop-context --scenario apply-a-guarded-structured-block-update --scenario refuse-an-unbounded-destructive-request --scenario fallback-when-iwe-is-unavailable --scenario fix-code-without-activating-iwe
```

The generated manifest is stored under `tests/eval/.cache/iwe-default-skill-eval/`; a new Markdown result defaults to `tests/eval/results/iwe-default-skill-eval.md`. Generated results and raw telemetry are intentionally untracked. A reviewed result may be copied to `docs/evals/results/` as a selected, immutable evidence report whose header pins the tested source repository, source commit, payload hashes, and harness commit. The root README links only such selected reports.

### Publish a selected report

Publication is a separate deterministic step after a complete green production run. Do not publish smoke, partial, invalid, or aggregate-failing runs. Pass the exact generated manifest and Markdown report from the same run:

```bash
uv run --with-requirements tests/eval/requirements.txt python scripts/publish_eval_report.py \
  --run tests/eval/reports/RUN_ID-iwe-default-skill-correctness-efficiency \
  --manifest tests/eval/.cache/iwe-default-skill-eval/experiment.toml \
  --report tests/eval/results/iwe-default-skill-eval.md \
  --output docs/evals/results/default-skill-correctness-efficiency-SOURCE_SHA_PREFIX.md
```

The publisher fails closed unless the raw matrix is complete and unique, every sample is valid, every aggregate row passes, the source URL pins the full source commit, and source payload provenance is present. It records the harness `HEAD`, source identity, payload and `AGENTS.md` hashes, run ID, and matrix cardinality. Private raw-telemetry links are replaced with retention notes rather than publishing prompts, transcripts, workspace data, or local paths.

For a historical run made by another harness commit, pass its exact existing commit with `--harness-commit COMMIT`. Existing publications are immutable by default; `--replace` is required to overwrite one. The command writes the selected report only. Review its diff, then update the root README and this document's **Published evidence** link in the same commit. Git commit and push remain explicit operator actions.

## Published evidence

- [IWE v18 at `f571d6f83dd79407ec64caf7cc3036708062e3c8`](results/default-skill-correctness-efficiency-f571d6f.md) — 31 scenarios × 10 samples, PASS.

## Matrix and model cost

- 1 target × 31 scenarios × 10 samples = **310 cells**.
- **310 worker calls** and **310 judge calls**.
- Listing and deterministic unit tests make no model calls.
