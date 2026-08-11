#!/usr/bin/env python3
"""Render the scenario-independent IWE AGENTS.md template."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from string import Template

DEFAULT_IWE_ROOT = "."
DEFAULT_IWE_DOCUMENTS = "project documentation"
DEFAULT_IWE_LANGUAGE = "English"


def _single_line(name: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be empty")
    if "\n" in value or "\r" in value:
        raise ValueError(f"{name} must be one line")
    return value


def render(
    template_path: Path,
    *,
    iwe_root: str = DEFAULT_IWE_ROOT,
    iwe_documents: str = DEFAULT_IWE_DOCUMENTS,
    iwe_language: str = DEFAULT_IWE_LANGUAGE,
) -> str:
    values = {
        "IWE_ROOT": _single_line("iwe_root", iwe_root),
        "IWE_DOCUMENTS": _single_line("iwe_documents", iwe_documents),
        "IWE_LANGUAGE": _single_line("iwe_language", iwe_language),
    }
    return Template(template_path.read_text(encoding="utf-8")).substitute(values)


def write_rendered(output: Path, text: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, output)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iwe-root", default=DEFAULT_IWE_ROOT)
    parser.add_argument("--iwe-documents", default=DEFAULT_IWE_DOCUMENTS)
    parser.add_argument("--iwe-language", default=DEFAULT_IWE_LANGUAGE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    write_rendered(
        args.output,
        render(
            args.template,
            iwe_root=args.iwe_root,
            iwe_documents=args.iwe_documents,
            iwe_language=args.iwe_language,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
