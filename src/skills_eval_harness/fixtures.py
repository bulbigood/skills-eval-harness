"""Validate canonical immutable fixture repositories before materialization."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class FixtureSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    repository: HttpUrl
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")


def load_fixture_sources(path: Path) -> dict[str, FixtureSource]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not raw:
        raise ValueError("fixture source registry must be a non-empty object")
    return {name: FixtureSource.model_validate(value) for name, value in raw.items()}


def fixture_source_name(fixture_name: str, sources: dict[str, FixtureSource]) -> str:
    matches = [name for name in sources if fixture_name == name or fixture_name.startswith(name + "-")]
    if len(matches) != 1:
        raise ValueError(f"fixture has no unique canonical source: {fixture_name}")
    return matches[0]


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=True
    )
    return completed.stdout.strip()


def _canonical_url(value: str) -> str:
    if value.endswith(".git"):
        value = value[:-4]
    if value.startswith("git@github.com:"):
        value = "https://github.com/" + value.removeprefix("git@github.com:")
    return value


def validate_fixture_roots(
    fixtures: dict[str, str],
    required_fixture_names: set[str],
    registry_path: Path,
) -> dict[str, dict[str, str]]:
    sources = load_fixture_sources(registry_path)
    required_sources = {fixture_source_name(name, sources) for name in required_fixture_names}
    if set(fixtures) != required_sources:
        raise ValueError(f"fixture arguments must exactly match canonical sources: {sorted(required_sources)}")
    result: dict[str, dict[str, str]] = {}
    for name in sorted(required_sources):
        root = Path(fixtures[name]).resolve()
        source = sources[name]
        commit = _git(root, "rev-parse", "HEAD")
        tree = _git(root, "rev-parse", "HEAD^{tree}")
        remote = _canonical_url(_git(root, "remote", "get-url", "origin"))
        dirty = _git(root, "status", "--porcelain")
        if commit != source.commit or remote != _canonical_url(str(source.repository)) or dirty:
            raise ValueError(f"fixture source is not the clean canonical revision: {name}")
        result[name] = {"repository": _canonical_url(str(source.repository)), "commit": commit, "tree": tree}
    return result


def materialize_fixture(source: Path, destination: Path, fixture_name: str) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git"))
    if fixture_name == "pkm-demo-api-project":
        path = destination / "graph/api-integration.md"
        path.write_text(
            "---\ntype: project\n---\n\n" + path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        return
    if fixture_name != "pkm-demo-core-read":
        return
    graph = destination / "graph"
    (graph / "core-alpha.md").write_text(
        "---\ntype: project\npriority: 2\n---\n\n# Core Alpha\n\n"
        "Coordinates the release.\n\n[Core Beta](core-beta.md)\n",
        encoding="utf-8",
    )
    (graph / "core-beta.md").write_text(
        "---\ntype: note\npriority: 1\n---\n\n# Core Beta\n\n"
        "Records the direct implementation checklist.\n",
        encoding="utf-8",
    )
    (graph / "core-gamma.md").write_text(
        "---\ntype: project\npriority: 3\n---\n\n# Core Gamma\n\n"
        "Tracks the higher-priority migration. The rollout uses staged cutovers and rollback "
        "checkpoints under the blue-lantern handoff.\n",
        encoding="utf-8",
    )
    config = destination / ".iwe/config.toml"
    config.write_text(
        config.read_text(encoding="utf-8") + '\n[schemas.core]\nmatch = "core-*"\n',
        encoding="utf-8",
    )
    schemas = destination / ".iwe/schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    (schemas / "core.yaml").write_text(
        "$schema: https://document-schema.org/draft/2026-06/schema\n"
        "frontmatter:\n"
        "  type: object\n"
        "  required: [type, priority]\n"
        "  properties:\n"
        "    type: { type: string }\n"
        "    priority: { type: number }\n",
        encoding="utf-8",
    )


def materialized_fixture_path(run_dir: Path, fixture_name: str, relative_path: str) -> Path:
    root = (run_dir / "inputs/materialized-fixtures").resolve()
    candidate = (root / fixture_name / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("materialized fixture path escapes the sealed fixture root") from exc
    return candidate
