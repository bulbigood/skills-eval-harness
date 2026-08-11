"""Explicit scenario memberships for evaluation suites."""

from __future__ import annotations

from pathlib import Path

import yaml

SCENARIO_CATALOG = Path("tests/eval/scenarios/iwe.eval.yaml")

DEFAULT_SKILL_SCENARIOS = (
    "discover-and-retrieve-bounded-multi-hop-context",
    "query-structured-metadata-without-scanning-files",
    "apply-a-guarded-structured-block-update",
    "refactor-an-inclusion-link-without-breaking-the-graph",
    "refuse-an-unbounded-destructive-request",
    "create-and-validate-a-schema-bound-document",
    "ambiguous-discovery-with-one-follow-up",
    "fallback-when-iwe-is-unavailable",
    "fix-code-without-activating-iwe",
    "read-one-known-note",
    "list-and-sort-typed-notes",
    "count-a-typed-cohort",
    "show-a-bounded-subtree",
    "read-one-note-with-children",
    "validate-a-known-schema-scope",
    "create-a-quick-note",
    "update-typed-frontmatter",
    "replace-an-authoritative-body",
    "edit-local-blocks",
    "rename-a-note-and-its-links",
    "inline-while-keeping-the-target",
    "attach-to-a-known-destination",
    "preview-one-scoped-deletion",
    "find-notes-by-body-concept",
    "summarize-one-topic",
    "find-one-exact-note-without-body",
    "find-one-partial-note",
    "replace-text-in-one-section",
    "replace-one-structured-block",
    "create-one-complete-document",
    "read-one-note-with-parent-context",
)

CONTEXT_ROUTING_SCENARIOS = (
    "route-listed-runbook-through-iwe",
    "route-unlisted-guide-through-workspace",
    "fallback-after-listed-iwe-miss",
    "fallback-when-iwe-is-unavailable",
    "create-iwe-document-in-declared-language",
)


def validate_membership(root: Path, scenario_ids: tuple[str, ...]) -> tuple[str, ...]:
    document = yaml.safe_load((root / SCENARIO_CATALOG).read_text(encoding="utf-8"))
    available = tuple(item["id"] for item in document["scenarios"])
    if len(available) != len(set(available)):
        raise ValueError("scenario catalog contains duplicate IDs")
    unknown = sorted(set(scenario_ids) - set(available))
    if unknown:
        raise ValueError(f"suite references unknown scenarios: {unknown}")
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("suite membership contains duplicate IDs")
    return scenario_ids
