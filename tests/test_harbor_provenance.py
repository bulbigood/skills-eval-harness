from __future__ import annotations

from pathlib import Path

import pytest

from skills_eval_harness.hashing import sha256_file, sha256_tree
from skills_eval_harness.provenance import Provenance, verify_harbor_lock, verify_materialized


def make_provenance(tmp_path: Path) -> tuple[Provenance, dict[str, Path]]:
    paths = {}
    for name in ("source", "skill"):
        path = tmp_path / name
        path.mkdir()
        (path / "payload").write_text(name, encoding="utf-8")
        paths[name] = path
    for name in ("runtime", "suite", "scenarios", "config"):
        path = tmp_path / name
        path.write_text(name, encoding="utf-8")
        paths[name] = path
    provenance = Provenance(
        source_url="https://github.com/acme/skills",
        source_commit="a" * 40,
        source_tree_sha256=sha256_tree(paths["source"]),
        selected_skill="demo",
        selected_skill_sha256=sha256_tree(paths["skill"]),
        runtime_version="1.2.3",
        runtime_sha256=sha256_file(paths["runtime"]),
        harness_commit="b" * 40,
        harness_dirty=False,
        suite_sha256=sha256_file(paths["suite"]),
        scenario_catalog_sha256=sha256_file(paths["scenarios"]),
        config_sha256=sha256_file(paths["config"]),
        harbor_version="0.21.0",
        task_checksums={"arm/task": "c" * 64},
        image_digests={"agent": "d" * 64},
    )
    return provenance, paths


def test_materialized_bytes_and_harbor_lock_are_bound(tmp_path: Path) -> None:
    provenance, p = make_provenance(tmp_path)
    verify_materialized(provenance, source_root=p["source"], skill_root=p["skill"], runtime=p["runtime"], suite=p["suite"], scenarios=p["scenarios"], config=p["config"])
    verify_harbor_lock(provenance, {"schema_version": 3, "harbor": {"version": "0.21.0"}, "trials": [{"task": {"name": "task", "source": "arm", "digest": "sha256:" + "c" * 64}}]})


def test_tampering_fails_closed(tmp_path: Path) -> None:
    provenance, p = make_provenance(tmp_path)
    p["runtime"].write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="provenance mismatch"):
        verify_materialized(provenance, source_root=p["source"], skill_root=p["skill"], runtime=p["runtime"], suite=p["suite"], scenarios=p["scenarios"], config=p["config"])
    with pytest.raises(ValueError, match="no trials"):
        verify_harbor_lock(provenance, {"schema_version": 3, "harbor": {"version": "0.21.0"}, "trials": []})
