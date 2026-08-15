"""Resolve skill and runtime inputs to exact bytes before any rollout."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .hashing import sha256_file, sha256_tree


@dataclass(frozen=True)
class ResolvedSkill:
    source_url: str
    commit: str
    repository_root: Path
    skill_root: Path
    repository_sha256: str
    skill_sha256: str


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def resolve_skill(source: str, cache: Path) -> ResolvedSkill:
    path = Path(source).expanduser()
    if path.is_dir():
        root_text = _git("rev-parse", "--show-toplevel", cwd=path)
        root = Path(root_text).resolve()
        if _git("status", "--porcelain", cwd=root):
            raise ValueError("local skill repository must be clean")
        commit = _git("rev-parse", "HEAD", cwd=root)
        if not (path / "SKILL.md").is_file():
            raise ValueError("selected skill directory must contain SKILL.md")
        try:
            url = _git("remote", "get-url", "upstream", cwd=root)
        except subprocess.CalledProcessError:
            url = _git("remote", "get-url", "origin", cwd=root)
        if url.endswith(".git"):
            url = url[:-4]
        if url.startswith("git@github.com:"):
            url = "https://github.com/" + url.removeprefix("git@github.com:")
        skill = path.resolve()
        relative = skill.relative_to(root).as_posix()
        canonical = f"{url}/tree/{commit}/{relative}"
        return ResolvedSkill(canonical, commit, root, skill, sha256_tree(root), sha256_tree(skill))

    parsed = urlparse(source)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc != "github.com" or len(parts) < 5 or parts[2] != "tree":
        raise ValueError("skill source must be a local Git directory or GitHub /tree/REF/PATH URL")
    owner, repository, _, ref, *subdirectory = parts
    clone_url = f"https://github.com/{owner}/{repository}.git"
    checkout = cache / owner / repository / ref.replace("/", "-")
    if checkout.exists():
        shutil.rmtree(checkout)
    checkout.parent.mkdir(parents=True, exist_ok=True)
    _git("clone", "--filter=blob:none", "--no-checkout", clone_url, str(checkout))
    _git("fetch", "--depth=1", "origin", ref, cwd=checkout)
    commit = _git("rev-parse", "FETCH_HEAD", cwd=checkout)
    _git("checkout", "--detach", commit, cwd=checkout)
    skill = checkout.joinpath(*subdirectory).resolve()
    if not skill.is_dir() or not (skill / "SKILL.md").is_file():
        raise ValueError("selected skill directory must contain SKILL.md")
    canonical = f"https://github.com/{owner}/{repository}/tree/{commit}/{'/'.join(subdirectory)}"
    return ResolvedSkill(canonical, commit, checkout, skill, sha256_tree(checkout), sha256_tree(skill))


def verify_runtime(binary: Path, expected_version: str) -> tuple[Path, str]:
    binary = binary.expanduser().resolve()
    if not binary.is_file():
        raise ValueError(f"runtime binary does not exist: {binary}")
    result = subprocess.run([str(binary), "--version"], text=True, capture_output=True, check=True)
    output = result.stdout.strip()
    if output != f"iwe {expected_version}":
        raise ValueError(f"runtime version mismatch: expected iwe {expected_version}, got {output!r}")
    return binary, sha256_file(binary)
