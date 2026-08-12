"""Resolve and freeze one skill selected by its directory URL or local path."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

from skill_manifest import SkillSpec, load_skills


DEFAULT_SKILL_SOURCE = (
    "https://github.com/iwe-org/skills/tree/"
    "f571d6f83dd79407ec64caf7cc3036708062e3c8/skills/iwe-v18"
)
DEFAULT_SOURCE_CACHE = Path("tests/eval/.cache/skill-source")


@dataclass(frozen=True)
class GitHubSkillURL:
    repository: str
    ref: str
    directory: str


@dataclass(frozen=True)
class ResolvedSkillSource:
    root: Path
    skill: SkillSpec
    source: str
    revision: str
    payload_sha256: str
    directory: str


def parse_github_skill_url(source: str) -> GitHubSkillURL:
    parsed = urlparse(source)
    if parsed.scheme != "https" or parsed.netloc.casefold() != "github.com":
        raise ValueError(f"unsupported web skill source; expected GitHub directory URL: {source}")
    parts = [unquote(part) for part in PurePosixPath(parsed.path).parts if part != "/"]
    if len(parts) < 5 or parts[2] != "tree":
        raise ValueError(
            "GitHub skill source must be a directory URL of the form "
            "https://github.com/OWNER/REPOSITORY/tree/REF/PATH"
        )
    owner, repository, _, ref, *directory = parts
    if not owner or not repository or not ref or not directory:
        raise ValueError("GitHub skill source must include a ref and skill directory URL")
    return GitHubSkillURL(
        repository=f"https://github.com/{owner}/{repository.removesuffix('.git')}.git",
        ref=ref,
        directory=str(PurePosixPath(*directory)),
    )


def _local_directory(source: str, root: Path) -> Path:
    parsed = urlparse(source)
    if parsed.scheme == "file":
        if parsed.netloc not in {"", "localhost"}:
            raise ValueError(f"file skill source must be local: {source}")
        candidate = Path(unquote(parsed.path))
    elif parsed.scheme:
        raise ValueError(f"unsupported skill source scheme {parsed.scheme!r}")
    else:
        candidate = Path(source).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
    candidate = candidate.resolve()
    if not candidate.is_dir() or not (candidate / "SKILL.md").is_file():
        raise ValueError(f"skill source is not a skill directory: {candidate}")
    return candidate


def _manifest_root(skill_directory: Path) -> Path:
    for parent in (skill_directory.parent, *skill_directory.parents):
        manifest = parent / "config.toml"
        if manifest.is_file():
            _, skills = load_skills(parent)
            if any(spec.path == skill_directory for spec in skills.values()):
                return parent
    raise ValueError(
        f"skill directory is not declared by an enclosing skill manifest: {skill_directory}"
    )


def _validate_source_links(source_root: Path) -> None:
    resolved_root = source_root.resolve()
    for item in source_root.rglob("*"):
        if item.is_symlink() and not item.resolve().is_relative_to(resolved_root):
            raise ValueError(f"skill source symlink escapes manifest root: {item}")


def _payload_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(
        (item for item in path.rglob("*") if item.is_file() and ".git" not in item.parts),
        key=lambda item: item.relative_to(path).as_posix(),
    ):
        relative = item.relative_to(path).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        content = item.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _replace_destination(destination: Path, populate) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f"{destination.name}-", dir=destination.parent))
    staged = temporary / "source"
    try:
        populate(staged)
        if destination.exists():
            shutil.rmtree(destination)
        staged.replace(destination)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def _selected_skill(root: Path, directory: str) -> SkillSpec:
    selected = (root / directory).resolve()
    if not selected.is_relative_to(root.resolve()):
        raise ValueError(f"skill directory escapes source root: {directory}")
    _, skills = load_skills(root)
    matches = [skill for skill in skills.values() if skill.path == selected]
    if len(matches) != 1:
        raise ValueError(f"skill directory is not declared exactly once by source manifest: {directory}")
    return matches[0]


def materialize_skill_source(
    root: Path,
    source: str = DEFAULT_SKILL_SOURCE,
    source_cache: Path = DEFAULT_SOURCE_CACHE,
) -> ResolvedSkillSource:
    """Freeze one selected skill and its manifest-owned evaluation metadata."""
    root = root.resolve()
    destination = (root / source_cache).resolve()
    if not destination.is_relative_to(root):
        raise ValueError(f"skill source cache must stay inside evaluation repository: {destination}")

    if source.startswith("https://"):
        github = parse_github_skill_url(source)

        def clone(staged: Path) -> None:
            staged.mkdir(parents=True)
            subprocess.run(["git", "-C", str(staged), "init", "--quiet"], check=True)
            subprocess.run(
                ["git", "-C", str(staged), "remote", "add", "origin", github.repository],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(staged), "config", "extensions.partialClone", "origin"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(staged), "config", "remote.origin.promisor", "true"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(staged), "config", "remote.origin.partialCloneFilter", "blob:none"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(staged), "sparse-checkout", "init", "--no-cone"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(staged),
                    "sparse-checkout",
                    "set",
                    "--no-cone",
                    "/config.toml",
                    "/skills/",
                    "/contracts/",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(staged),
                    "fetch",
                    "--quiet",
                    "--depth=1",
                    "--filter=blob:none",
                    "origin",
                    github.ref,
                ],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(staged), "checkout", "--quiet", "--detach", "FETCH_HEAD"],
                check=True,
            )

            _validate_source_links(staged)

        _replace_destination(destination, clone)
        revision = subprocess.check_output(
            ["git", "-C", str(destination), "rev-parse", "HEAD"], text=True
        ).strip()
        if len(github.ref) == 40 and all(character in "0123456789abcdefABCDEF" for character in github.ref):
            if revision.casefold() != github.ref.casefold():
                raise RuntimeError(
                    f"pinned skill source resolved to {revision}, expected {github.ref}"
                )
        directory = github.directory
    else:
        local_skill = _local_directory(source, root)
        source_root = _manifest_root(local_skill)
        for payload_directory in (source_root / "skills", source_root / "contracts"):
            if payload_directory.is_dir():
                _validate_source_links(payload_directory)
        directory = local_skill.relative_to(source_root).as_posix()

        def copy_source(staged: Path) -> None:
            staged.mkdir(parents=True)
            shutil.copy2(source_root / "config.toml", staged / "config.toml")
            for payload_directory in ("skills", "contracts"):
                source_directory = source_root / payload_directory
                if source_directory.is_dir():
                    shutil.copytree(source_directory, staged / payload_directory, symlinks=True)

        _replace_destination(destination, copy_source)
        revision = _payload_sha256(destination)

    skill = _selected_skill(destination, directory)
    payload = _payload_sha256(destination)
    return ResolvedSkillSource(
        root=destination,
        skill=skill,
        source=source,
        revision=revision,
        payload_sha256=payload,
        directory=directory,
    )
