"""Privacy-preserving procedural attestations from private trajectories."""
from __future__ import annotations

import json
import re
import shlex
from typing import Any

_CMD = re.compile(r'cmd:"((?:\\.|[^"\\])*)"')


def _commands(document: dict[str, Any]) -> list[list[str] | None]:
    rows: list[list[str] | None] = []
    for step in document.get("steps", []):
        if not isinstance(step, dict) or step.get("source") != "agent":
            continue
        for call in step.get("tool_calls") or []:
            arguments = call.get("arguments") if isinstance(call, dict) else None
            source = arguments.get("input") if isinstance(arguments, dict) else None
            match = _CMD.search(source) if isinstance(source, str) else None
            if match is None:
                rows.append(None)
                continue
            try:
                rows.append(shlex.split(json.loads(f'"{match.group(1)}"')))
            except (json.JSONDecodeError, ValueError):
                rows.append(None)
    return rows


def _is_targeted_read(argv: list[str], target: str) -> bool:
    if not argv or argv[-1] != target:
        return False
    if argv[0] == "cat":
        return argv == ["cat", target]
    if argv[0] in {"head", "tail"}:
        return all(not value.startswith("-") or value.lstrip("-n").isdigit() for value in argv[1:-1])
    if argv[0] == "sed":
        return len(argv) == 4 and argv[1] == "-n" and argv[2].endswith("p")
    return False


def fallback_attestation(document: dict[str, Any], target: str) -> dict[str, Any]:
    commands = _commands(document)
    iwe_indices = [index for index, argv in enumerate(commands) if argv and argv[0] == "iwe"]
    reads = [index for index, argv in enumerate(commands) if argv and _is_targeted_read(argv, target)]
    after_attempt = bool(iwe_indices and reads and reads[0] > iwe_indices[0])
    unrelated = any(
        index > iwe_indices[0] and index not in reads
        for index in range(len(commands))
    ) if iwe_indices else False
    return {
        "protocol": "fallback-attestation-v1",
        "runtime_attempt_observed": len(iwe_indices) == 1,
        "targeted_fallback_observed": len(reads) == 1 and after_attempt,
        "declared_path": target,
        "unrelated_post_failure_tool_call_observed": unrelated,
    }
