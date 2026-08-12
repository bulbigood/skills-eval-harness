"""Agent process adapters, output parsing, performance data, and safe retries."""
from __future__ import annotations

import json
import shlex
import statistics
import subprocess
import time
from pathlib import Path

def process_argv(command: str, cwd: Path) -> list[str]:
    """Build the executed argv and pin Codex to the prepared workspace explicitly."""
    argv = shlex.split(command)
    if (
        argv
        and Path(argv[0]).name == "codex"
        and len(argv) > 1
        and argv[1] == "exec"
        and "-C" not in argv
        and "--cd" not in argv
    ):
        argv[2:2] = ["-C", str(cwd.resolve())]
    return argv

def _claude_tool_result_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )
    return ""

def parse_process_output(executable_name: str, stdout: str) -> dict:
    final = ""
    commands: list[dict] = []
    pending_bash: dict[str, str] = {}
    provider_errors: list[str] = []
    tool_activity = False
    token_usage: dict[str, int] = {}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if executable_name == "claude":
            usage = event.get("usage")
            if isinstance(usage, dict):
                token_usage = {
                    "input_tokens": int(usage.get("input_tokens", 0)),
                    "cached_input_tokens": int(
                        usage.get("cache_read_input_tokens", 0)
                        + usage.get("cache_creation_input_tokens", 0)
                    ),
                    "output_tokens": int(usage.get("output_tokens", 0)),
                }
            message = event.get("message", {})
            content = message.get("content", []) if isinstance(message, dict) else []
            if event.get("type") == "assistant" and isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict) or item.get("type") != "tool_use":
                        continue
                    if item.get("name") == "Bash" and isinstance(item.get("input"), dict):
                        tool_activity = True
                        pending_bash[str(item.get("id", ""))] = str(item["input"].get("command", ""))
            if event.get("type") == "user" and isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict) or item.get("type") != "tool_result":
                        continue
                    tool_id = str(item.get("tool_use_id", ""))
                    command = pending_bash.pop(tool_id, None)
                    if command is not None:
                        commands.append({
                            "command": command,
                            "exit_code": 1 if item.get("is_error") else 0,
                            "output": _claude_tool_result_text(item.get("content")),
                        })
            if event.get("type") == "result":
                if event.get("is_error"):
                    provider_errors.append(str(event.get("result", "provider error")))
                if event.get("structured_output") is not None:
                    final = json.dumps(event["structured_output"], ensure_ascii=False)
                elif event.get("result") is not None:
                    final = str(event["result"])
            continue
        usage = event.get("usage")
        if isinstance(usage, dict):
            token_usage = {
                "input_tokens": int(usage.get("input_tokens", 0)),
                "cached_input_tokens": int(usage.get("cached_input_tokens", 0)),
                "output_tokens": int(usage.get("output_tokens", 0)),
            }
        item = event.get("item", {})
        if event.get("type") in {"error", "turn.failed"}:
            error = event.get("error", event.get("message", "provider error"))
            provider_errors.append(str(error.get("message", error)) if isinstance(error, dict) else str(error))
        if event.get("type") == "item.started" and item.get("type") == "command_execution":
            tool_activity = True
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            final = str(item.get("text", ""))
        if event.get("type") == "item.completed" and item.get("type") == "command_execution":
            tool_activity = True
            commands.append({"command": str(item.get("command", "")), "exit_code": int(item.get("exit_code") or 0), "output": str(item.get("aggregated_output", ""))})
    return {
        "final": final or stdout,
        "commands": commands,
        "token_usage": token_usage,
        "provider_errors": provider_errors,
        "tool_activity": tool_activity,
    }

def performance_summary(results: list[dict], target_ids: tuple[str, ...]) -> dict[str, dict]:
    """Return per-target descriptive statistics over every worker sample."""
    summary: dict[str, dict] = {}
    for target_id in target_ids:
        rows = [row for row in results if row.get("target_id") == target_id]
        if not rows:
            raise ValueError(f"no performance samples for target {target_id}")
        fields = {
            "input_tokens": [row["agent"]["token_usage"]["input_tokens"] for row in rows],
            "output_tokens": [row["agent"]["token_usage"]["output_tokens"] for row in rows],
            "tool_calls": [row["agent"]["metrics"]["task_tool_calls"] for row in rows],
            "wall_seconds": [row["agent"]["wall_seconds"] for row in rows],
        }
        summary[target_id] = {
            "samples": len(rows),
            **{f"{name}_median": statistics.median(values) for name, values in fields.items()},
            **{f"{name}_mean": statistics.mean(values) for name, values in fields.items()},
        }
    return summary

TRANSIENT_PROVIDER_MESSAGES = (
    "selected model is at capacity",
    "service temporarily unavailable",
    "server is temporarily overloaded",
)

TRANSIENT_PROCESS_ATTEMPTS = 4

TRANSIENT_RETRY_DELAYS_SECONDS = (2, 4, 8)

def transient_provider_failure(result: dict) -> str | None:
    """Return a recognized transient message only before any tool execution."""
    if result["exit"] == 0 or result.get("tool_activity"):
        return None
    output = f"{result.get('stdout', '')}\n{result.get('stderr', '')}".casefold()
    return next((message for message in TRANSIENT_PROVIDER_MESSAGES if message in output), None)

def run_process(command: str, prompt: str, cwd: Path, timeout: int, env: dict[str, str]) -> dict:
    started = time.monotonic()
    argv = process_argv(command, cwd)
    transient_failures: list[dict[str, object]] = []
    for attempt in range(1, TRANSIENT_PROCESS_ATTEMPTS + 1):
        attempt_started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                input=prompt,
                cwd=cwd,
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            def captured_text(value: str | bytes | None) -> str:
                if isinstance(value, bytes):
                    return value.decode("utf-8", errors="replace")
                return value or ""

            stderr = captured_text(error.stderr)
            timeout_message = f"process timed out after {timeout} seconds"
            completed = subprocess.CompletedProcess(
                argv,
                124,
                stdout=captured_text(error.stdout),
                stderr=f"{stderr}\n{timeout_message}".strip(),
            )
        parsed = parse_process_output(Path(argv[0]).name, completed.stdout)
        result = {
            "exit": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            **parsed,
            "wall_seconds": time.monotonic() - attempt_started,
        }
        transient_message = transient_provider_failure(result)
        if transient_message is None or attempt == TRANSIENT_PROCESS_ATTEMPTS:
            result["wall_seconds"] = time.monotonic() - started
            result["attempts"] = attempt
            result["transient_failures"] = transient_failures
            return result
        transient_failures.append({
            "attempt": attempt,
            "exit": completed.returncode,
            "message": transient_message,
        })
        time.sleep(TRANSIENT_RETRY_DELAYS_SECONDS[attempt - 1])
    raise AssertionError("unreachable transient retry state")
