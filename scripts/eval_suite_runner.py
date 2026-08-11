#!/usr/bin/env python3
"""Shared CLI and runner primitives for maintained evaluation suites."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


AGENT_MODEL_PROFILES = {"codex": "weak", "claude": "medium"}


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def build_eval_command(
    *,
    root: Path,
    manifest: Path,
    results_file: Path,
    agent: str,
    list_only: bool,
    extra_arguments: Iterable[str] = (),
) -> list[str]:
    command = [
        sys.executable,
        str(root / "tests/eval/run.py"),
        "--experiment",
        str(manifest),
        *extra_arguments,
        "--model-profile",
        AGENT_MODEL_PROFILES[agent],
        "--agent",
        agent,
    ]
    if list_only:
        command.append("--list")
    else:
        command.extend(["--markdown-report", str(results_file)])
    return command


def run_eval(command: list[str], root: Path) -> int:
    return subprocess.call(command, cwd=root)
