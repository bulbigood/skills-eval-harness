"""Command telemetry normalization and deterministic procedure gates."""
from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

from .scenarios import Scenario


ESTIMATED_BYTES_PER_TOKEN = 4
IWE_CALL = re.compile(r"(?<![\w-])(?:[\w./-]+/)?iwe\s+(?!docs\b)")
SUPPORTED_SHELL_WRAPPERS = {
    "bash", "/bin/bash",
    "sh", "/bin/sh",
    "zsh", "/bin/zsh",
}
FALLBACK_TOOL = re.compile(
    r"(?:^|[;&|]\s*|[\"'])\s*(?:[\w./-]+/)?(?:grep|rg|find)\b"
)
BROAD_WORKSPACE_READ = re.compile(
    r"\b(?:cat|sed|head|tail)\b[^\n;&|]*(?:\bgraph/|\s\.\s*$)"
)


def estimate_input_tokens(byte_count: int) -> int:
    """Approximate input tokens using the repository-wide four-bytes-per-token rule."""
    return (byte_count + ESTIMATED_BYTES_PER_TOKEN - 1) // ESTIMATED_BYTES_PER_TOKEN

def _command_payload(command: str) -> str:
    """Unwrap only the exact shell form emitted by the configured agent."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return command
    if (
        len(tokens) == 3
        and tokens[0] in SUPPORTED_SHELL_WRAPPERS
        and tokens[1] == "-lc"
    ):
        return tokens[2]
    return command

def _decode_ansi_c_escapes(raw: str) -> str:
    """Decode Bash ANSI-C escapes without re-decoding literal Unicode text."""
    escape = re.compile(
        r"\\(?:[abefnrtv\\'\"?]|x[0-9a-fA-F]{1,2}|u[0-9a-fA-F]{4}|"
        r"U[0-9a-fA-F]{8}|[0-7]{1,3})"
    )
    named = {
        "a": "\a", "b": "\b", "e": "\x1b", "f": "\f", "n": "\n",
        "r": "\r", "t": "\t", "v": "\v", "\\": "\\", "'": "'",
        '"': '"', "?": "?",
    }

    def decode_match(match: re.Match[str]) -> str:
        token = match.group(0)[1:]
        if token[0] in named:
            return named[token[0]]
        if token[0] == "x":
            return chr(int(token[1:], 16))
        if token[0] in {"u", "U"}:
            return chr(int(token[1:], 16))
        return chr(int(token, 8))

    return escape.sub(decode_match, raw)


def _normalize_ansi_c_quotes(command: str) -> str:
    """Convert Bash ``$'...'`` words into POSIX-shell-quoted equivalents."""
    normalized: list[str] = []
    index = 0
    while index < len(command):
        if not command.startswith("$'", index):
            normalized.append(command[index])
            index += 1
            continue
        end = index + 2
        escaped = False
        while end < len(command):
            character = command[end]
            if character == "'" and not escaped:
                break
            if character == "\\" and not escaped:
                escaped = True
            else:
                escaped = False
            end += 1
        if end >= len(command):
            return command
        raw = command[index + 2:end]
        try:
            decoded = _decode_ansi_c_escapes(raw)
        except UnicodeDecodeError:
            return command
        normalized.append(shlex.quote(decoded))
        index = end + 1
    return "".join(normalized)

def _observed_iwe_invocations(command: str) -> list[list[str]]:
    try:
        payload = _normalize_ansi_c_quotes(_command_payload(command))
        payload = re.sub(r"(?<!\S)(?:\d*>&\d+|&>\s*\S+|\d*>>?\s*\S+|\d*<<?\s*\S+)", "", payload)
        payload = re.sub(r"\n\s*done\s*$", "; done", payload)
        loop_pattern = re.compile(
            r"for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+([^;\n]+?)\s*;\s*do\s+(.*?)\s*[;\n]?\s*done",
            re.DOTALL,
        )
        while (loop := loop_pattern.search(payload)) is not None:
            variable, raw_values, body = loop.groups()
            expanded_bodies = []
            for value in shlex.split(raw_values):
                expanded_bodies.append(re.sub(
                    rf"\$\{{{re.escape(variable)}\}}|\${re.escape(variable)}\b",
                    shlex.quote(value),
                    body,
                ).replace("\n", "; "))
            payload = payload[:loop.start()] + "; ".join(expanded_bodies) + payload[loop.end():]
        lexer = shlex.shlex(payload, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []
    invocations: list[list[str]] = []
    command_start = True
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {";", "&&", "||", "|"}:
            command_start = True
            index += 1
            continue
        if command_start and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token):
            index += 1
            continue
        if command_start and Path(token).name == "iwe":
            end = index + 1
            while end < len(tokens) and tokens[end] not in {";", "&&", "||", "|"}:
                end += 1
            args = [
                arg for arg in tokens[index + 1:end]
                if not re.fullmatch(r"(?:\d*>>?|\d*<<?|&>>?|&>)\S*", arg)
            ]
            if args and args[0] != "docs":
                invocations.append(args)
            command_start = False
            index = end
            continue
        command_start = False
        index += 1
    return invocations

def _json_list_count(value: str) -> int | None:
    decoder = json.JSONDecoder()
    for index, character in enumerate(value):
        if character != "[":
            continue
        try:
            parsed, _ = decoder.raw_decode(value[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, list):
            return len(parsed)
    return None

def _unbounded_iwe_args(args: list[str]) -> bool:
    if not args or args[0] not in {"find", "retrieve"}:
        return False
    if "--help" in args or "-h" in args:
        return False

    zero_unbounded_flags = {
        "--limit",
        "-l",
        "--max-documents",
        "--max-tokens",
        "--max-document-tokens",
        "--depth",
        "--distance",
    }
    for index, arg in enumerate(args):
        flag, separator, inline_value = arg.partition("=")
        tracks_zero_as_unlimited = flag in zero_unbounded_flags or flag.startswith("--expand-")
        if not tracks_zero_as_unlimited:
            continue
        value = inline_value if separator else (args[index + 1] if index + 1 < len(args) else None)
        if value == "0":
            return True

    has_flag = lambda expected: expected in args or any(
        arg.startswith(f"{expected}=") for arg in args
    )
    missing_limit = not has_flag("--limit") and not has_flag("-l")
    searched_retrieve = args[0] == "retrieve" and any(
        has_flag(flag) for flag in ("--fuzzy", "--lexical", "--filter")
    )
    unbounded_expansion = any(arg.startswith("--expand-") for arg in args) and any(
        not has_flag(flag)
        for flag in ("--max-documents", "--max-tokens", "--max-document-tokens")
    )
    return (args[0] == "find" and missing_limit) or (
        searched_retrieve and missing_limit
    ) or unbounded_expansion

def _is_skill_activation(
    item: dict,
    tested_skill: str | None,
    activation_path: Path | None = None,
) -> bool:
    if not tested_skill or item.get("exit_code") != 0:
        return False
    command = str(item.get("command", ""))
    if (
        not str(item.get("output", "")).strip()
        or re.search(r"&&|\|\||;|\n", command)
        or IWE_CALL.search(command)
    ):
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if not tokens:
        return False
    payload = _command_payload(command)
    if payload != command:
        try:
            tokens = shlex.split(payload)
        except ValueError:
            return False
        if not tokens:
            return False
    skill_paths = {
        f".agents/skills/{tested_skill}/SKILL.md",
        ".agents/guidance/SKILL.md",
    }
    if activation_path is not None:
        skill_paths.add(str(activation_path))

    def is_skill_path(value: str) -> bool:
        return value in skill_paths

    reader = Path(tokens[0]).name
    if reader == "cat":
        return len(tokens) == 2 and is_skill_path(tokens[1])
    if reader == "sed":
        return (
            len(tokens) == 4
            and tokens[1] == "-n"
            and bool(re.fullmatch(r"\d+(?:,(?:\d+|\$))?p", tokens[2]))
            and is_skill_path(tokens[3])
        )
    if reader in {"head", "tail"}:
        return (
            len(tokens) == 2 and is_skill_path(tokens[1])
        ) or (
            len(tokens) == 4
            and tokens[1] == "-n"
            and tokens[2].isdigit()
            and is_skill_path(tokens[3])
        )
    return False

def command_metrics(
    commands: list[dict],
    telemetry: list[dict] | None = None,
    tested_skill: str | None = None,
    exclude_skill_activation: bool = True,
    activation_path: Path | None = None,
) -> dict[str, int]:
    activation_calls = sum(
        _is_skill_activation(item, tested_skill, activation_path) for item in commands
    )
    skill_paths = [
        f".agents/skills/{tested_skill}/SKILL.md",
        ".agents/guidance/SKILL.md",
    ] if tested_skill else []
    if activation_path is not None:
        skill_paths.append(str(activation_path))
    metrics = {
        "raw_tool_calls": len(commands),
        "task_tool_calls": max(
            len(commands) - int(exclude_skill_activation and activation_calls > 0),
            0,
        ),
        "skill_activation_calls": activation_calls,
        "skill_read_calls": sum(
            any(path in str(item.get("command", "")) for path in skill_paths)
            for item in commands
        ),
        "iwe_calls": 0,
        "help_calls": 0,
        "web_calls": 0,
        "docs_calls": 0,
        "forbidden_fallback_calls": 0,
        "broad_workspace_reads": 0,
        "reference_reads": 0,
        "iwe_output_bytes": 0,
        "context_bytes": 0,
        "task_tool_output_bytes": 0,
        "failed_iwe_calls": 0,
        "unbounded_read_calls": 0,
        "max_result_count": 0,
        "result_records": 0,
        "iwe_telemetry_missing": 0,
        "iwe_telemetry_extra": 0,
        "iwe_telemetry_mismatch": 0,
        "iwe_telemetry_invalid": 0,
        "iwe_output_truncated": 0,
    }
    observed_invocations: list[list[str]] = []
    observed_details: list[tuple[str, int | None]] = []
    observed_iwe_task_output_bytes = 0
    for item in commands:
        command = str(item.get("command", ""))
        output = str(item.get("output", ""))
        item_invocations = _observed_iwe_invocations(command)
        observed_invocations.extend(item_invocations)
        observed_details.extend(
            (
                output if len(item_invocations) == 1 else "",
                int(item["exit_code"])
                if item.get("exit_code") is not None and len(item_invocations) == 1
                else None,
            )
            for _ in item_invocations
        )
        iwe_calls = len(item_invocations)
        metrics["iwe_calls"] += iwe_calls
        metrics["help_calls"] += command.count("--help")
        metrics["docs_calls"] += len(re.findall(r"(?<![\w-])iwe\s+docs\b", command))
        metrics["web_calls"] += len(re.findall(r"\b(?:curl|wget|gh)\b|\bgit\s+clone\b", command))
        metrics["forbidden_fallback_calls"] += len(FALLBACK_TOOL.findall(command))
        metrics["broad_workspace_reads"] += len(BROAD_WORKSPACE_READ.findall(command))
        metrics["reference_reads"] += int(
            "/references/" in command
            and (".agents/skills/" in command or ".agents/guidance/" in command)
        )
        metrics["context_bytes"] += len(output.encode("utf-8"))
        if not (
            exclude_skill_activation
            and _is_skill_activation(item, tested_skill, activation_path)
        ):
            output_bytes = len(output.encode("utf-8"))
            metrics["task_tool_output_bytes"] += output_bytes
            if iwe_calls:
                observed_iwe_task_output_bytes += output_bytes
        for read_command, arguments in re.findall(
            r"(?<![\w-])iwe\s+(find|retrieve)\b(.*?)"
            r"(?=(?:\s+&&|\s+\|\||[;\n]|$))",
            command,
            re.DOTALL,
        ):
            try:
                invocation = shlex.split(f"{read_command} {arguments}")
            except ValueError:
                invocation = [read_command, *arguments.split()]
            if _unbounded_iwe_args(invocation):
                metrics["unbounded_read_calls"] += 1
        if iwe_calls:
            metrics["iwe_output_bytes"] += len(output.encode("utf-8"))
            metrics["iwe_output_truncated"] += int("eval shim: stdout exceeded configured budget" in output)
            if int(item.get("exit_code") or 0) != 0:
                metrics["failed_iwe_calls"] += iwe_calls
    if telemetry is not None:
        telemetry_invocations = [
            [str(arg) for arg in item.get("args", [])]
            for item in telemetry
        ]
        metrics["iwe_telemetry_missing"] = max(len(observed_invocations) - len(telemetry), 0)
        metrics["iwe_telemetry_extra"] = max(len(telemetry) - len(observed_invocations), 0)
        metrics["iwe_telemetry_mismatch"] = int(
            sorted(observed_invocations) != sorted(telemetry_invocations)
        )
        telemetry_valid = not metrics["iwe_telemetry_mismatch"]
        if telemetry_valid:
            detail_queues: dict[tuple[str, ...], list[tuple[str, int | None]]] = {}
            for invocation, detail in zip(observed_invocations, observed_details, strict=True):
                detail_queues.setdefault(tuple(invocation), []).append(detail)
            telemetry_details = [
                detail_queues[tuple(invocation)].pop(0)
                for invocation in telemetry_invocations
            ]
            for item, (observed_output, observed_exit) in zip(telemetry, telemetry_details, strict=True):
                stdout = item.get("stdout")
                stderr = item.get("stderr")
                result_count = item.get("result_count")
                emitted_bytes = item.get("emitted_stdout_bytes")
                raw_bytes = item.get("stdout_bytes")
                stderr_bytes = item.get("stderr_bytes")
                exit_code = item.get("exit_code")
                record_valid = (
                    isinstance(stdout, str)
                    and isinstance(stderr, str)
                    and isinstance(emitted_bytes, int) and not isinstance(emitted_bytes, bool)
                    and isinstance(raw_bytes, int) and not isinstance(raw_bytes, bool)
                    and isinstance(stderr_bytes, int) and not isinstance(stderr_bytes, bool)
                    and isinstance(exit_code, int) and not isinstance(exit_code, bool)
                    and emitted_bytes == len(stdout.encode("utf-8"))
                    and stderr_bytes == len(stderr.encode("utf-8"))
                    and raw_bytes >= emitted_bytes
                    and (not observed_output or bool(stdout or stderr))
                    and (
                        not observed_output
                        or observed_output.endswith(stdout + stderr)
                        or observed_output.endswith(stderr + stdout)
                    )
                    and (
                        result_count is None
                        or result_count == _json_list_count(stdout)
                    )
                    and (observed_exit is None or exit_code == observed_exit)
                    and (
                        raw_bytes == emitted_bytes
                        or "eval shim: stdout exceeded configured budget" in observed_output
                    )
                )
                if not record_valid:
                    telemetry_valid = False
                    break
        metrics["iwe_telemetry_invalid"] = int(not telemetry_valid)
        if telemetry_valid:
            metrics["help_calls"] = sum("--help" in item.get("args", []) for item in telemetry)
            metrics["iwe_output_bytes"] = sum(int(item.get("stdout_bytes", 0)) for item in telemetry)
            metrics["failed_iwe_calls"] = sum(int(item.get("exit_code", 0)) != 0 for item in telemetry)
            metrics["unbounded_read_calls"] = sum(
                _unbounded_iwe_args([str(arg) for arg in item.get("args", [])])

                for item in telemetry
            )
            metrics["max_result_count"] = max(
                (int(item["result_count"]) for item in telemetry if item.get("result_count") is not None),
                default=0,
            )
            metrics["result_records"] = sum(
                int(item.get("result_count") or 0) for item in telemetry
            )
            emitted_iwe_bytes = sum(
                int(item.get("emitted_stdout_bytes", 0))
                + int(item.get("stderr_bytes", 0))
                for item in telemetry
            )
            missing_captured_bytes = max(
                emitted_iwe_bytes - observed_iwe_task_output_bytes,
                0,
            )
            metrics["task_tool_output_bytes"] += missing_captured_bytes
            metrics["context_bytes"] += missing_captured_bytes
    metrics["estimated_context_tokens"] = estimate_input_tokens(metrics["context_bytes"])
    metrics["estimated_task_input_tokens"] = estimate_input_tokens(
        metrics["task_tool_output_bytes"]
    )
    return metrics

def load_iwe_telemetry(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

def efficiency_errors(
    scenario: Scenario,
    metrics: dict[str, int],
    *,
    allow_filesystem_fallback: bool = False,
) -> list[str]:
    errors: list[str] = []
    if metrics["unbounded_read_calls"]:
        errors.append("unbounded IWE discovery or retrieval used")
    if metrics.get("iwe_output_truncated", 0):
        errors.append("IWE output exceeded the configured capture budget")
    if metrics["web_calls"] or metrics["docs_calls"]:
        errors.append("web or IWE documentation command used")
    if scenario.max_iwe_calls is not None and metrics["iwe_calls"] > scenario.max_iwe_calls:
        errors.append(f"IWE call limit exceeded: {metrics['iwe_calls']} > {scenario.max_iwe_calls}")
    filesystem_tool_calls = metrics["forbidden_fallback_calls"]
    broad_read_calls = metrics["broad_workspace_reads"]
    if (
        filesystem_tool_calls
        and not (scenario.allow_fallback or allow_filesystem_fallback)
        and scenario.skill_activation != "forbidden"
    ):
        errors.append("forbidden fallback tool used")
    if broad_read_calls and not (scenario.allow_fallback or allow_filesystem_fallback):
        errors.append("forbidden fallback tool used")
    if scenario.iwe_mode == "unavailable":
        if not scenario.allow_fallback:
            errors.append("unavailable scenario must explicitly permit fallback")
    return errors


def telemetry_integrity_errors(metrics: dict[str, int]) -> list[str]:
    """Return capture-integrity failures that make a cell non-evaluable."""
    errors: list[str] = []
    if metrics.get("iwe_telemetry_missing", 0):
        errors.append("IWE telemetry missing for observed command invocation")
    if metrics.get("iwe_telemetry_extra", 0):
        errors.append("IWE telemetry contains records without observed command invocations")
    if metrics.get("iwe_telemetry_mismatch", 0):
        errors.append("IWE telemetry arguments do not match observed command invocations")
    if metrics.get("iwe_telemetry_invalid", 0):
        errors.append("IWE telemetry measurements do not match observed command evidence")
    return errors


def route_errors(
    scenario: Scenario,
    commands: list[dict],
    after_snapshot: dict[str, str] | None = None,
) -> list[str]:
    """Enforce scenario-owned source routing from observable task commands."""
    del after_snapshot  # Reserved for route oracles that need workspace state.
    errors: list[str] = []
    iwe_indexes: list[int] = []
    filesystem_indexes: list[int] = []

    for index, item in enumerate(commands):
        command = str(item.get("command", ""))
        if _observed_iwe_invocations(command):
            iwe_indexes.append(index)
        item_metrics = command_metrics([item])
        if item_metrics["forbidden_fallback_calls"] or item_metrics["broad_workspace_reads"]:
            filesystem_indexes.append(index)

    route = scenario.route
    if route == "iwe-only":
        if not iwe_indexes:
            errors.append("required initial IWE lookup missing")
        elif filesystem_indexes and filesystem_indexes[0] < iwe_indexes[0]:
            errors.append("filesystem search preceded the required IWE lookup")
    elif route == "filesystem-only":
        if iwe_indexes:
            errors.append("IWE invoked for a filesystem-first route")
        if not filesystem_indexes:
            errors.append("required local filesystem lookup was not observed")
    elif route == "iwe-then-filesystem":
        if not iwe_indexes:
            errors.append("required IWE lookup before fallback was not used")
        if not filesystem_indexes:
            errors.append("required filesystem fallback after IWE miss was not used")
        if iwe_indexes and filesystem_indexes and iwe_indexes[0] > filesystem_indexes[0]:
            errors.append("filesystem fallback occurred before the IWE miss")

    command_text = "\n".join(str(item.get("command", "")) for item in commands)
    for path in scenario.forbidden_read_paths:
        if path in command_text:
            errors.append(f"forbidden path read: {path}")
    return errors

def procedure_errors(
    scenario: Scenario,
    commands: list[dict],
    metrics: dict[str, int],
    telemetry: list[dict] | None = None,
    *,
    allow_filesystem_fallback: bool = False,
) -> list[str]:
    errors = efficiency_errors(
        scenario,
        metrics,
        allow_filesystem_fallback=allow_filesystem_fallback,
    )
    errors.extend(route_errors(scenario, commands))
    if scenario.skill_activation == "forbidden":
        if metrics.get("skill_read_calls", 0):
            errors.append("IWE skill guidance read for an out-of-scope task")
        if metrics.get("iwe_calls", 0):
            errors.append("IWE runtime invoked for an out-of-scope task")
    command_text = "\n".join(str(item.get("command", "")) for item in commands)
    if re.search(r"\biwe\s+find\s+(?!-)[^|;&\n]+", command_text):
        errors.append("possible deprecated positional iwe find query")
    return errors

def deterministic_metric_failures(
    scenario: Scenario,
    commands: list[dict],
    oracle: dict,
    metrics: dict | None = None,
) -> dict[str, str]:
    """Return explicit scenario-owned metric gates without rewriting judge scores."""
    failures: dict[str, str] = {}
    routing = route_errors(scenario, commands)
    if routing:
        reason = "; ".join(routing)
        failures["skill_compliance"] = reason
        failures["tool_efficiency"] = reason
    if (
        scenario.hard_max_task_tool_calls is not None
        and (metrics or {}).get("task_tool_calls", 0)
        > scenario.hard_max_task_tool_calls
    ):
        reason = (
            "hard task-tool limit exceeded: "
            f"{(metrics or {}).get('task_tool_calls', 0)} > "
            f"{scenario.hard_max_task_tool_calls}"
        )
        failures["skill_compliance"] = reason
        failures["tool_efficiency"] = reason
    forbidden_keys = set(scenario.forbidden_retrieve_keys)
    retrieved_forbidden: set[str] = set()
    observed_forbidden_candidate = False
    for item in commands:
        invocations = _observed_iwe_invocations(str(item.get("command", "")))
        for args in invocations:
            if not args:
                continue
            if args[0] == "find" and any(
                key in str(item.get("output", "")) for key in forbidden_keys
            ):
                observed_forbidden_candidate = True
                continue
            if args[0] != "retrieve":
                continue
            if observed_forbidden_candidate:
                retrieved_forbidden.update(forbidden_keys)
            for flag in ("--key", "-k"):
                if flag in args and args.index(flag) + 1 < len(args):
                    key = args[args.index(flag) + 1]
                    if key in forbidden_keys:
                        retrieved_forbidden.add(key)
    if retrieved_forbidden:
        keys = ", ".join(sorted(retrieved_forbidden))
        reason = f"configured unrelated IWE candidate retrieved: {keys}"
        failures["skill_compliance"] = reason
        failures["tool_efficiency"] = reason

    fact = oracle.get("workspace_fact") if isinstance(oracle, dict) else None
    if scenario.require_oracle_tool_evidence and isinstance(fact, dict):
        source_path = str(fact.get("source_path", ""))
        value_match = re.search(r"=\s*([^\s]+)\s*$", str(fact.get("fact", "")))
        value = value_match.group(1) if value_match else ""
        command_evidence = "\n".join(str(item.get("command", "")) for item in commands)
        output_evidence = "\n".join(str(item.get("output", "")) for item in commands)
        combined_evidence = f"{command_evidence}\n{output_evidence}"
        if (
            not source_path
            or not value
            or source_path not in combined_evidence
            or value not in output_evidence
        ):
            failures["evidence_quality"] = (
                "independent oracle value/path not present in task tool output evidence"
            )
    language = oracle.get("authoring_language") if isinstance(oracle, dict) else None
    if isinstance(language, dict) and language.get("valid") is False:
        reason = "created IWE document does not use the declared English authoring language"
        failures["task_correctness"] = reason
        failures["scenario_compliance"] = reason
        failures["evidence_quality"] = reason
    return failures
