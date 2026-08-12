"""Deterministic mechanical validation and judge-evidence sanitization."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import yaml

from skill_manifest import SkillSpec
from .oracle import _is_english_audit_retention_decision, _parse_frontmatter, _standalone_document_links
from .scenarios import Scenario


FORBIDDEN = (
    re.compile(r"\b(?:curl|wget|gh|git\s+clone)\b"),
)


def _global_mechanical_errors(
    scenario: Scenario,
    before: dict[str, str],
    after: dict[str, str],
    commands: list[dict],
) -> list[str]:
    errors: list[str] = []
    command_text = '\n'.join((item['command'] for item in commands))
    for pattern in FORBIDDEN:
        if pattern.search(command_text):
            errors.append(f'forbidden command matched {pattern.pattern}')
    mutating_scenarios = {'apply-a-guarded-structured-block-update', 'refactor-an-inclusion-link-without-breaking-the-graph', 'create-and-validate-a-schema-bound-document', 'fix-code-without-activating-iwe', 'create-a-quick-note', 'update-typed-frontmatter', 'replace-an-authoritative-body', 'edit-local-blocks', 'rename-a-note-and-its-links', 'inline-while-keeping-the-target', 'attach-to-a-known-destination', 'replace-text-in-one-section', 'replace-one-structured-block', 'create-one-complete-document', 'create-iwe-document-in-declared-language'}
    if scenario.id not in mutating_scenarios:
        if before != after:
            errors.append('read-only scenario changed fixture files')
    return errors


def _check_apply_a_guarded_structured_block_update(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    if changed != {'graph/eval-roadmap.md'}:
        errors.append(f'unexpected changed files: {sorted(changed)}')
    before_body = before.get('graph/eval-roadmap.md', '')
    body = after.get('graph/eval-roadmap.md', '')
    expected_body = before_body.replace('## Goals', '## Aims', 1)
    status_marker = '## Status\n\nIn review.'
    expected_body = expected_body.replace(status_marker, status_marker + '\n\nReviewed by the evaluation agent.', 1)
    if not before_body or body != expected_body:
        errors.append('roadmap does not equal the exact requested transformation')
    return errors


def _check_refactor_an_inclusion_link_without_breaking_the_graph(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    created = after.keys() - before.keys()
    if len(created) != 1 or changed != {'graph/eval-plan.md', *created}:
        errors.append('refactor changed files outside the source and one new note')
    source = after.get('graph/eval-plan.md', '')
    if '## Architecture' in source or 'Use a graph-aware boundary.' in source:
        errors.append('architecture section was not extracted')
    extracted = [key for key, value in after.items() if key.startswith('graph/') and key != 'graph/eval-plan.md' and re.search('^#\\s+Architecture\\s*$', value, re.MULTILINE) and ('Use a graph-aware boundary.' in value) and re.search('^#{2,3}\\s+Storage\\s*$', value, re.MULTILINE) and ('Markdown files.' in value)]
    if len(extracted) != 1:
        errors.append('extracted document not found')
    else:
        target = extracted[0][6:-3]
        standalone_link = re.compile(f'^(?:\\[Architecture\\]\\({re.escape(target)}\\.md\\)|\\[\\[{re.escape(target)}(?:\\|Architecture)?\\]\\])$', re.MULTILINE)
        if not standalone_link.search(source):
            errors.append('source does not contain an independent standalone inclusion link')
    if '## Delivery\n\nPreserve this section.' not in source:
        errors.append('unrelated source section was not preserved')
    return errors


def _check_create_and_validate_a_schema_bound_document(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    created = [(key, after[key]) for key in after.keys() - before.keys() if key.startswith('graph/meetings/') and key.endswith('.md')]
    valid = False
    if len(created) == 1:
        _, body = created[0]
        frontmatter = {}
        if body.startswith('---\n') and '\n---\n' in body[4:]:
            raw = body[4:body.find('\n---\n', 4)]
            try:
                frontmatter = yaml.safe_load(raw) or {}
            except yaml.YAMLError:
                frontmatter = {}
        attendees_valid = False
        attendees_match = re.search('^## Attendees\\s*$\\n(?P<value>.*?)(?=^##\\s|\\Z)', body, flags=re.MULTILINE | re.DOTALL)
        if attendees_match:
            attendee_text = attendees_match.group('value').strip()
            try:
                attendee_value = yaml.safe_load(attendee_text)
            except yaml.YAMLError:
                attendee_value = attendee_text
            attendees_valid = attendee_value in ('Ada and Alan', ['Ada', 'Alan'])
        attendees_valid = attendees_valid or frontmatter.get('attendees') in ('Ada and Alan', ['Ada', 'Alan'])
        valid = isinstance(frontmatter, dict) and frontmatter.get('type') == 'meeting' and (frontmatter.get('draft') is False) and ('# Evaluation Sync' in body) and attendees_valid and ('## Notes' in body) and ('Review the graph.' in body)
    if not valid:
        errors.append('typed schema-bound meeting was not created')
    return errors


def _check_create_a_quick_note(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    created = {key: after[key] for key in after.keys() - before.keys() if key.startswith('graph/') and key.endswith('.md')}
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected_body = '# Release Scratchpad\n\nCollect final checks.'
    valid = [key for key, body in created.items() if body.rstrip('\n') == expected_body]
    if len(valid) != 1 or changed != set(valid):
        errors.append('quick note creation did not create exactly the requested note')
    return errors


def _check_create_iwe_document_in_declared_language(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    created = {key: after[key] for key in after.keys() - before.keys() if key.startswith('graph/') and key.endswith('.md')}
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    valid = [key for key, body in created.items() if _is_english_audit_retention_decision(body)]
    if len(valid) != 1 or changed != set(valid):
        errors.append('IWE document was not created once in the declared workspace language')
    return errors


def _check_update_typed_frontmatter(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    before_frontmatter, before_body = _parse_frontmatter(before.get('graph/core-edit.md', ''))
    after_frontmatter, after_body = _parse_frontmatter(after.get('graph/core-edit.md', ''))
    expected_frontmatter = dict(before_frontmatter)
    expected_frontmatter.pop('temporary', None)
    expected_frontmatter['reviewed'] = True
    if changed != {'graph/core-edit.md'} or after_frontmatter != expected_frontmatter:
        errors.append('typed frontmatter update is not exact')
    if before_body != after_body:
        errors.append('typed frontmatter update changed the body')
    return errors


def _check_replace_an_authoritative_body(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected = '---\ntype: memo\nowner: Ada\n---\n# Core Body\n\nApproved final text.'
    if changed != {'graph/core-body.md'} or after.get('graph/core-body.md') != expected:
        errors.append('authoritative body replacement is not exact')
    return errors


def _check_edit_local_blocks(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected = '# Core Blocks\n\n## Keep\n\nPreserve.\n\nReady.\n\n## Tail\n\nFinish.\n'
    if changed != {'graph/core-blocks.md'} or after.get('graph/core-blocks.md') != expected:
        errors.append('local block edit is not the exact requested transformation')
    return errors


def _check_rename_a_note_and_its_links(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected = {'graph/core-old.md', 'graph/core-renamed.md', 'graph/core-referrer.md'}
    referrer = after.get('graph/core-referrer.md', '')
    if changed != expected or 'core-old' in referrer or 'core-renamed.md' not in referrer:
        errors.append('rename did not move the note and rewrite the exact referrer')
    expected_referrer = before.get('graph/core-referrer.md', '').replace('core-old.md', 'core-renamed.md')
    if after.get('graph/core-renamed.md') != before.get('graph/core-old.md') or referrer != expected_referrer:
        errors.append('rename changed note or referrer content beyond the key rewrite')
    return errors


def _check_inline_while_keeping_the_target(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    parent = after.get('graph/core-parent.md', '')
    child = before.get('graph/core-child.md', '')
    promoted_child = re.sub('^#\\s', '## ', child, count=1).rstrip('\n')
    expected_parent = before.get('graph/core-parent.md', '').replace('[Core Child](core-child.md)', promoted_child)
    if changed != {'graph/core-parent.md'} or after.get('graph/core-child.md') != child or parent != expected_parent:
        errors.append('inline did not exactly replace the inclusion while preserving the target')
    return errors


def _check_attach_to_a_known_destination(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    inbox = after.get('graph/inbox.md', '')
    source_inclusions = [line for line in inbox.splitlines() if _standalone_document_links(line) == ['core-source']]
    if changed != {'graph/inbox.md'} or len(source_inclusions) != 1:
        errors.append('attach did not create exactly one standalone source inclusion')
    before_inbox = before.get('graph/inbox.md')
    if before_inbox is not None and len(source_inclusions) == 1:
        remaining = '\n'.join((line for line in inbox.splitlines() if line != source_inclusions[0]))
        normalize_links = lambda value: re.sub('(\\[[^\\]]+\\]\\([^)]*?)\\.md(\\))', '\\1\\2', value)
        if normalize_links(remaining).strip() != normalize_links(before_inbox).strip():
            errors.append('attach changed existing destination content beyond link normalization')
    return errors


def _check_replace_text_in_one_section(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected = before.get('graph/core-local-text.md', '').replace('three regions', 'four regions', 1)
    if changed != {'graph/core-local-text.md'} or after.get('graph/core-local-text.md') != expected:
        errors.append('local text replacement is not the exact requested transformation')
    return errors


def _check_replace_one_structured_block(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected = '# Core Block Replace\n\n## Preparation\n\nKeep snapshots.\n\n## Rollback\n\nRestore the previous release.\n\n## Follow-up\n\nRecord the outcome.\n'
    if changed != {'graph/core-block-replace.md'} or after.get('graph/core-block-replace.md') != expected:
        errors.append('structured block replacement is not the exact requested transformation')
    return errors


def _check_create_one_complete_document(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    expected = '---\ntype: checklist\nowner: Ada\n---\n# Release Checklist\n\nVerify backups.'
    if changed != {'graph/projects/release-checklist.md'} or after.get('graph/projects/release-checklist.md', '').rstrip('\n') != expected:
        errors.append('complete document creation is not exact')
    return errors


def _check_fix_code_without_activating_iwe(
    before: dict[str, str],
    after: dict[str, str],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    if changed != {'src/retry.py'}:
        errors.append(f'unexpected changed files: {sorted(changed)}')
    check_environment = dict(os.environ)
    check_environment['PYTHONDONTWRITEBYTECODE'] = '1'
    focused = subprocess.run([sys.executable, '-m', 'unittest', 'tests/test_retry.py'], cwd=workspace, env=check_environment, text=True, capture_output=True, check=False)
    if focused.returncode != 0:
        errors.append('focused retry test does not pass after the agent run')
    return errors


ScenarioRule = Callable[[dict[str, str], dict[str, str], Path], list[str]]

SCENARIO_RULES: dict[str, ScenarioRule] = {
    'apply-a-guarded-structured-block-update': _check_apply_a_guarded_structured_block_update,
    'refactor-an-inclusion-link-without-breaking-the-graph': _check_refactor_an_inclusion_link_without_breaking_the_graph,
    'create-and-validate-a-schema-bound-document': _check_create_and_validate_a_schema_bound_document,
    'create-a-quick-note': _check_create_a_quick_note,
    'create-iwe-document-in-declared-language': _check_create_iwe_document_in_declared_language,
    'update-typed-frontmatter': _check_update_typed_frontmatter,
    'replace-an-authoritative-body': _check_replace_an_authoritative_body,
    'edit-local-blocks': _check_edit_local_blocks,
    'rename-a-note-and-its-links': _check_rename_a_note_and_its_links,
    'inline-while-keeping-the-target': _check_inline_while_keeping_the_target,
    'attach-to-a-known-destination': _check_attach_to_a_known_destination,
    'replace-text-in-one-section': _check_replace_text_in_one_section,
    'replace-one-structured-block': _check_replace_one_structured_block,
    'create-one-complete-document': _check_create_one_complete_document,
    'fix-code-without-activating-iwe': _check_fix_code_without_activating_iwe,
}


def mechanical_errors(
    scenario: Scenario,
    before: dict[str, str],
    after: dict[str, str],
    commands: list[dict],
    workspace: Path,
    _metrics: dict | None = None,
) -> list[str]:
    errors = _global_mechanical_errors(scenario, before, after, commands)
    checker = SCENARIO_RULES.get(scenario.id)
    if checker is not None:
        errors.extend(checker(before, after, workspace))
    return errors


RESULT_POSTCONDITION_PREFIXES = (
    "roadmap does not equal the exact requested transformation",
    "architecture section was not extracted",
    "extracted document not found",
    "source does not contain an independent standalone inclusion link",
    "unrelated source section was not preserved",
    "typed schema-bound meeting was not created",
    "quick note creation did not create exactly the requested note",
    "typed frontmatter update is not exact",
    "authoritative body replacement is not exact",
    "local block edit is not the exact requested transformation",
    "rename did not move the note and rewrite the exact referrer",
    "inline did not exactly replace the inclusion while preserving the target",
    "attach did not create exactly one standalone source inclusion",
    "local text replacement is not the exact requested transformation",
    "structured block replacement is not the exact requested transformation",
    "complete document creation is not exact",
    "focused retry test does not pass after the agent run",
)


def classify_mechanical_errors(errors: list[str]) -> tuple[list[str], dict[str, str]]:
    """Separate auditable result misses from evidence-integrity and scope failures."""
    result_errors = [
        error for error in errors
        if error.startswith(RESULT_POSTCONDITION_PREFIXES)
    ]
    integrity_errors = [error for error in errors if error not in result_errors]
    if not result_errors:
        return integrity_errors, {}
    reason = "; ".join(result_errors)
    return integrity_errors, {
        dimension: reason
        for dimension in ("task_correctness", "scenario_compliance", "evidence_quality")
    }


SKILL_FINGERPRINT_WIDTH = 64


def normalized_skill_text(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold()


def tested_skill_fingerprints(skill: SkillSpec | None) -> frozenset[str]:
    if skill is None:
        return frozenset()
    fingerprints = set()
    for path in skill.path.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        normalized = normalized_skill_text(text)
        fingerprints.update(
            normalized[index:index + SKILL_FINGERPRINT_WIDTH]
            for index in range(len(normalized) - SKILL_FINGERPRINT_WIDTH + 1)
        )
    return frozenset(fingerprints)


def sanitize_judge_evidence(skill: SkillSpec | None, value):
    fingerprints = tested_skill_fingerprints(skill)

    def sanitize(item):
        if isinstance(item, str):
            normalized = normalized_skill_text(item)
            if any(
                normalized[index:index + SKILL_FINGERPRINT_WIDTH] in fingerprints
                for index in range(len(normalized) - SKILL_FINGERPRINT_WIDTH + 1)
            ):
                return "[TESTED_SKILL_TEXT_REDACTED]"
            return item
        if isinstance(item, list):
            return [sanitize(child) for child in item]
        if isinstance(item, dict):
            return {key: sanitize(child) for key, child in item.items()}
        return item

    return sanitize(value)


def judge_command_evidence(skill: SkillSpec | None, commands: list[dict]) -> list[dict]:
    tested_roots = (
        (f".agents/skills/{skill.name}", ".agents/guidance")
        if skill is not None else ()
    )
    evidence = []
    for item in commands:
        redacted = sanitize_judge_evidence(skill, dict(item))
        if not isinstance(redacted, dict):
            raise TypeError("sanitized command evidence must remain an object")
        if any(root in str(item.get("command", "")) for root in tested_roots):
            redacted["output"] = "[TESTED_SKILL_OUTPUT_REDACTED]"
        evidence.append(redacted)
    return evidence
