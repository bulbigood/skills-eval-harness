"""Independent filesystem evidence and scenario-specific oracles."""
from __future__ import annotations

import difflib
import hashlib
import re
from pathlib import Path

import yaml

from .scenarios import Scenario


def payload_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    values = {}
    for path in sorted(root.rglob("*")):
        if (
            not path.is_file()
            or ".git" in path.parts
            or ".agents" in path.parts
            or ".iwe-eval-harness" in path.parts
            or path.name == "AGENTS.md"
            or "__pycache__" in path.parts
            or path.suffix == ".pyc"
        ):
            continue
        rel = str(path.relative_to(root))
        try:
            values[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            values[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def _document_title(text: str, fallback: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            try:
                frontmatter = yaml.safe_load(text[4:end]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            if isinstance(frontmatter, dict) and isinstance(frontmatter.get("title"), str):
                return frontmatter["title"]
    heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return heading.group(1).strip() if heading else fallback


def _source_excerpt(text: str, terms: tuple[str, ...], limit: int = 420) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lowered = compact.casefold()
    positions = [lowered.find(term.casefold()) for term in terms]
    positions = [position for position in positions if position >= 0]
    start = max(0, min(positions, default=0) - 100)
    return compact[start:start + limit]


def _document_links(text: str) -> list[str]:
    links = set(re.findall(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]", text))
    for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
        target = target.strip().split(maxsplit=1)[0].strip("<>")
        if re.match(r"^[a-z][a-z0-9+.-]*://", target, re.IGNORECASE):
            continue
        target = target.split("#", 1)[0].split("?", 1)[0]
        target = re.sub(r"^(?:\./)?(?:graph/)?", "", target)
        target = re.sub(r"\.md$", "", target, flags=re.IGNORECASE)
        if target:
            links.add(target)
    return sorted(links)


def _standalone_document_links(text: str) -> list[str]:
    """Return links whose complete non-blank line is one Markdown/wiki link."""
    links: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not (
            re.fullmatch(r"\[\[[^\]]+\]\]", stripped)
            or re.fullmatch(r"\[[^\]]+\]\([^)]+\)", stripped)
        ):
            continue
        links.update(_document_links(stripped))
    return sorted(links)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    try:
        value = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return {}, text[end + 5:]
    return (value if isinstance(value, dict) else {}), text[end + 5:]


def independent_schema_validation_evidence(
    scenario: Scenario,
    after: dict[str, str],
) -> dict:
    """Validate the authored meeting schema directly from snapshot files, without IWE."""
    schema_path = ".iwe/schemas/meeting.yaml"
    document_paths = sorted(
        path for path in after
        if path.startswith("graph/meetings/") and path.endswith(".md")
    )
    errors: list[str] = []
    schema: dict = {}
    try:
        parsed = yaml.safe_load(after.get(schema_path, "")) or {}
        schema = parsed if isinstance(parsed, dict) else {}
    except yaml.YAMLError as error:
        errors.append(f"schema YAML is invalid: {error}")
    if len(document_paths) != 1:
        errors.append(f"expected exactly one meeting document, found {len(document_paths)}")
    document_path = document_paths[0] if len(document_paths) == 1 else None
    if not schema:
        errors.append("meeting schema is missing or empty")
    if document_path:
        frontmatter, body = _parse_frontmatter(after[document_path])
        frontmatter_schema = schema.get("frontmatter", {})
        for field in frontmatter_schema.get("required", []):
            if field not in frontmatter:
                errors.append(f"missing required frontmatter field: {field}")
        for field, rule in frontmatter_schema.get("properties", {}).items():
            if field not in frontmatter or not isinstance(rule, dict):
                continue
            if "const" in rule and frontmatter[field] != rule["const"]:
                errors.append(f"frontmatter {field} does not equal {rule['const']!r}")
            if rule.get("type") == "boolean" and not isinstance(frontmatter[field], bool):
                errors.append(f"frontmatter {field} is not boolean")
        headings = [
            (len(match.group(1)), match.group(2).strip())
            for match in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", body, re.MULTILINE)
        ]
        level_one = [title for level, title in headings if level == 1]
        root_rules = schema.get("sections", [])
        if len(level_one) != 1:
            errors.append(f"expected exactly one level-1 section, found {len(level_one)}")
        elif root_rules and isinstance(root_rules[0], dict):
            pattern = root_rules[0].get("header", {}).get("pattern")
            if pattern and re.fullmatch(pattern, level_one[0]) is None:
                errors.append("level-1 section does not match schema")
            allowed = {
                child.get("header", {}).get("const")
                for child in root_rules[0].get("sections", [])
                if isinstance(child, dict)
            }
            actual = [title for level, title in headings if level == 2]
            for expected in sorted(value for value in allowed if value):
                if actual.count(expected) != 1:
                    errors.append(f"expected exactly one level-2 section: {expected}")
            if root_rules[0].get("additionalSections") is False:
                for title in actual:
                    if title not in allowed:
                        errors.append(f"unexpected level-2 section: {title}")
    return {
        "applicable": scenario.id == "create-and-validate-a-schema-bound-document",
        "schema_path": schema_path,
        "document_path": document_path,
        "valid": not errors,
        "errors": errors,
        "method": "independent YAML frontmatter and Markdown heading-tree validation",
    }


def _is_english_audit_retention_decision(body: str) -> bool:
    """Recognize the scenario facts without requiring one exact phrasing."""
    lowered = body.casefold()
    return (
        re.search(r"(?m)^#\s+.*\bdecision\b", lowered) is not None
        and re.search(r"\baudit\b", lowered) is not None
        and re.search(r"\b90\s+days?\b", lowered) is not None
        and re.search(r"[А-Яа-яЁё]", body) is None
    )


def independent_oracle_evidence(
    scenario: Scenario,
    before: dict[str, str],
    after: dict[str, str],
    final_response: str,
) -> dict:
    """Build compact ground truth directly from Markdown snapshots, never from IWE."""
    del final_response  # Tested-agent prose must not influence independent evidence selection.
    terms_by_scenario = {
        "discover-and-retrieve-bounded-multi-hop-context": ("marcus", "machiavelli", "nietzsche", "virtue"),
        "query-structured-metadata-without-scanning-files": ("power", "morality"),
        "ambiguous-discovery-with-one-follow-up": ("api",),
        "read-one-known-note": ("implementation", "checklist"),
        "list-and-sort-typed-notes": ("priority",),
        "count-a-typed-cohort": ("project",),
        "show-a-bounded-subtree": ("core",),
        "read-one-note-with-children": ("core",),
        "validate-a-known-schema-scope": ("core",),
        "create-a-quick-note": ("release", "scratchpad"),
        "update-typed-frontmatter": ("reviewed", "temporary"),
        "replace-an-authoritative-body": ("approved", "final"),
        "edit-local-blocks": ("ready", "tail"),
        "rename-a-note-and-its-links": ("core", "renamed"),
        "inline-while-keeping-the-target": ("reusable", "child"),
        "attach-to-a-known-destination": ("core", "source"),
        "preview-one-scoped-deletion": ("deletion", "target"),
        "find-notes-by-body-concept": ("blue-lantern", "handoff"),
        "summarize-one-topic": ("staged", "cutovers", "rollback", "checkpoints"),
        "find-one-exact-note-without-body": ("core alpha",),
        "find-one-partial-note": ("core gamma",),
        "read-one-note-with-parent-context": ("core alpha", "core beta", "implementation", "release"),
        "replace-text-in-one-section": ("regions", "deployment"),
        "replace-one-structured-block": ("rollback", "release"),
        "create-one-complete-document": ("release", "checklist", "backups"),
        "route-listed-runbook-through-iwe": ("payment", "ledger", "zero-drift"),
        "route-unlisted-guide-through-workspace": ("contributor", "python 3.13"),
        "fallback-after-listed-iwe-miss": ("violet harbor", "single-writer"),
        "create-iwe-document-in-declared-language": ("audit", "90 days"),
    }
    authored_keys_by_scenario = {
        "discover-and-retrieve-bounded-multi-hop-context": {
            "virtue-across-centuries",
            "meditations-009-043",
            "meditations-010-001",
            "meditations-010-016",
            "meditations-010-033",
            "meditations-011-017",
            "meditations-011-043",
            "prince-15",
            "prince-16",
            "prince-26",
            "bge-041",
            "bge-227",
            "bge-228",
        },
    }
    terms = terms_by_scenario.get(scenario.id, ())
    authored_keys = authored_keys_by_scenario.get(scenario.id)
    metadata_relationships: dict[str, dict[str, list[str]]] | None = None
    if scenario.id == "query-structured-metadata-without-scanning-files":
        direct_keys = {"power", "morality"}
        outgoing: dict[str, dict[str, set[str]]] = {}
        for path, text in sorted(after.items()):
            if not path.startswith("graph/") or not path.endswith(".md"):
                continue
            key = path.removeprefix("graph/").removesuffix(".md")
            all_links = set(_document_links(text))
            includes = set(_standalone_document_links(text))
            outgoing[key] = {
                "includes": includes,
                "references": all_links - includes,
            }
        # IWE 0.18.0 indexes the configured library root (`graph/` in the pinned
        # fixtures), not arbitrary Markdown elsewhere in the workspace. Keep the
        # independent parser scoped to that same public runtime boundary.
        metadata_relationships = {}
        for key in sorted(direct_keys):
            metadata_relationships[key] = {
                "includes": sorted(outgoing.get(key, {}).get("includes", set())),
                "included_by": sorted(
                    source for source, relations in outgoing.items()
                    if key in relations["includes"]
                ),
                "references": sorted(outgoing.get(key, {}).get("references", set())),
                "referenced_by": sorted(
                    source for source, relations in outgoing.items()
                    if key in relations["references"]
                ),
            }

    documents = []
    for path, text in sorted(after.items()):
        if not path.endswith(".md"):
            continue
        lowered = text.casefold()
        key = path.removeprefix("graph/").removesuffix(".md")
        if authored_keys is not None:
            if key not in authored_keys:
                continue
        elif scenario.id == "query-structured-metadata-without-scanning-files" and key not in {"power", "morality"}:
            continue
        elif terms and not any(term in lowered for term in terms):
            continue
        frontmatter, _ = _parse_frontmatter(text)
        links = _document_links(text)[:12]
        document = {
            "key": key,
            "title": _document_title(text, Path(key).name),
            "frontmatter": frontmatter,
        }
        if scenario.id != "query-structured-metadata-without-scanning-files":
            document.update({
                "links": links,
                "source_excerpt": _source_excerpt(text, terms),
            })
        documents.append(document)

    if scenario.id == "query-structured-metadata-without-scanning-files":
        documents.sort(key=lambda item: item["key"])
    else:
        documents.sort(key=lambda item: item["key"])
        documents = documents[:20]
    authoritative_matches = (
        [
            item for item in documents
            if item["frontmatter"].get("type") == "project"
            and "api" in after[f"graph/{item['key']}.md"].casefold()
        ]
        if scenario.id == "ambiguous-discovery-with-one-follow-up"

        else []
    )
    changed = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    diffs = {}
    for path in changed[:6]:
        diff = "".join(difflib.unified_diff(
            before.get(path, "").splitlines(keepends=True),
            after.get(path, "").splitlines(keepends=True),
            fromfile=f"before/{path}",
            tofile=f"after/{path}",
            n=3,
        ))
        diffs[path] = diff[:8000]

    prepared = {}
    for path in (
        "graph/eval-roadmap.md",
        "graph/eval-plan.md",
        "src/retry.py",
        "tests/test_retry.py",
        "graph/core-alpha.md",
        "graph/core-beta.md",
        "graph/core-gamma.md",
        ".iwe/schemas/core.yaml",
        "graph/core-edit.md",
        "graph/core-body.md",
        "graph/core-blocks.md",
        "graph/core-old.md",
        "graph/core-renamed.md",
        "graph/core-referrer.md",
        "graph/core-child.md",
        "graph/core-parent.md",
        "graph/core-source.md",
        "graph/inbox.md",
        "graph/core-delete.md",
        "graph/core-delete-ref.md",
        "graph/core-local-text.md",
        "graph/core-block-replace.md",
        "graph/projects/release-checklist.md",
        "graph/decisions/queue-backpressure.md",
        "graph/runbooks/payment-ledger-recovery.md",
        "docs/contributor-prerequisites.md",
        "operations/violet-harbor-recovery.md",
    ):
        if path in after:
            prepared[path] = after[path][:8000]
    authoring_language = None
    if scenario.id == "create-iwe-document-in-declared-language":
        created_documents = {
            key: after[key] for key in after.keys() - before.keys()
            if key.startswith("graph/") and key.endswith(".md")
        }
        bodies = list(created_documents.values())
        authoring_language = {
            "expected": "English",
            "created_paths": sorted(created_documents),
            "valid": (
                len(bodies) == 1
                and _is_english_audit_retention_decision(bodies[0])
            ),
        }
    evidence = {
        "source": "direct independent parsing of fixture snapshots; no tested CLI or skill",
        "matching_documents": documents,
        "authoritative_matches": authoritative_matches,
        "changed_files": changed,
        "independent_diffs": diffs,
        "prepared_documents": prepared,
        "authoring_language": authoring_language,
        "schema_validation": (
            independent_schema_validation_evidence(scenario, after)
            if scenario.id == "create-and-validate-a-schema-bound-document"
            else None
        ),
        "workspace_fact": {
            "route-unlisted-guide-through-workspace": {
                "source_path": "docs/contributor-prerequisites.md",
                "fact": "required_python = 3.13",
                "source_text": after.get("docs/contributor-prerequisites.md", ""),
            },
            "fallback-after-listed-iwe-miss": {
                "source_path": "operations/violet-harbor-recovery.md",
                "fact": "recovery_mode = single-writer",
                "source_text": after.get("operations/violet-harbor-recovery.md", ""),
            },
        }.get(scenario.id),
    }
    if metadata_relationships is not None:
        evidence["graph_neighborhoods"] = metadata_relationships
    return evidence
