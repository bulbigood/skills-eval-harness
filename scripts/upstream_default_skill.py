"""Materialize an exact latest upstream skills checkout for evaluation."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


UPSTREAM_REPOSITORY = "https://github.com/iwe-org/skills"
DEFAULT_SOURCE_CACHE = Path("tests/eval/.cache/iwe-default-skill-source")


@dataclass(frozen=True)
class SourceCheckout:
    root: Path
    revision: str


def materialize_upstream_checkout(
    root: Path,
    repository: str = UPSTREAM_REPOSITORY,
    source_cache: Path = DEFAULT_SOURCE_CACHE,
) -> SourceCheckout:
    """Fetch repository HEAD and detach an isolated cache at that exact commit."""
    destination = (root / source_cache).resolve()
    git_dir = destination / ".git"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not git_dir.is_dir():
        raise RuntimeError(f"upstream cache exists but is not a Git checkout: {destination}")
    if not destination.exists():
        temporary_parent = Path(
            tempfile.mkdtemp(prefix="iwe-skills-clone-", dir=destination.parent)
        )
        temporary_checkout = temporary_parent / "source"
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--quiet",
                    "--no-checkout",
                    "--filter=blob:none",
                    repository,
                    str(temporary_checkout),
                ],
                check=True,
            )
            temporary_checkout.replace(destination)
        finally:
            shutil.rmtree(temporary_parent, ignore_errors=True)
    subprocess.run(
        ["git", "-C", str(destination), "remote", "set-url", "origin", repository],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(destination), "fetch", "--quiet", "--depth=1", "origin", "HEAD"],
        check=True,
    )
    revision = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "FETCH_HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "-C", str(destination), "checkout", "--quiet", "--detach", "--force", revision],
        check=True,
    )
    return SourceCheckout(root=destination, revision=revision)
