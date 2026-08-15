from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from skills_eval_harness.publish import publish
from skills_eval_harness.provenance import Provenance, seal_run


SHA = "a" * 64
COMMIT = "b" * 40


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def provenance(dirty: bool = False) -> Provenance:
    return Provenance(
        source_url="https://github.com/acme/skills/tree/" + COMMIT + "/skills/demo",
        source_commit=COMMIT,
        source_tree_sha256=SHA,
        selected_skill="demo",
        selected_skill_sha256=SHA,
        runtime_version="1.2.3",
        runtime_sha256=SHA,
        harness_commit=COMMIT,
        harness_dirty=dirty,
        suite_sha256=SHA,
        scenario_catalog_sha256=SHA,
        config_sha256=SHA,
        harbor_version="0.21.0",
        task_checksums={"task": SHA},
        image_digests={"agent": SHA},
    )


def setup(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    run = root / "run"
    run.mkdir(parents=True)
    git(root, "init")
    git(root, "remote", "add", "upstream", "https://github.com/iwe-org/skills-eval-harness.git")
    (run / "summary.json").write_text(json.dumps({"valid": True, "pass": True, "expected_cells": 1, "observed_cells": 1}))
    (run / "provenance.json").write_text(provenance().model_dump_json())
    (run / "jobs/job").mkdir(parents=True)
    (run / "jobs/job/lock.json").write_text("{}")
    seal_run(run)
    return root, run


def test_publisher_derives_pass_and_canonical_repository(tmp_path: Path) -> None:
    root, run = setup(tmp_path)
    output = root / "published.md"
    publish(root=root, run_dir=run, output=output)
    text = output.read_text()
    assert "Overall suite verdict: **PASS**" in text
    assert "https://github.com/iwe-org/skills-eval-harness" in text
    assert "bulbigood" not in text
    assert output.with_suffix(".md.sha256").is_file()


def test_publisher_rejects_failed_incomplete_dirty_or_overwrite(tmp_path: Path) -> None:
    root, run = setup(tmp_path)
    output = root / "published.md"
    summary = {"valid": True, "pass": False, "expected_cells": 1, "observed_cells": 1}
    (run / "summary.json").write_text(json.dumps(summary))
    seal_run(run)
    with pytest.raises(ValueError, match="passing"):
        publish(root=root, run_dir=run, output=output)
    (run / "summary.json").write_text(json.dumps({**summary, "pass": True, "observed_cells": 0}))
    seal_run(run)
    with pytest.raises(ValueError, match="incomplete"):
        publish(root=root, run_dir=run, output=output)
    (run / "summary.json").write_text(json.dumps({**summary, "pass": True}))
    (run / "provenance.json").write_text(provenance(True).model_dump_json())
    seal_run(run)
    with pytest.raises(ValueError, match="clean"):
        publish(root=root, run_dir=run, output=output)


def test_publisher_rejects_tampered_sealed_artifact(tmp_path: Path) -> None:
    root, run = setup(tmp_path)
    (run / "summary.json").write_text(json.dumps({"valid": True, "pass": False, "expected_cells": 1, "observed_cells": 1}))
    with pytest.raises(ValueError, match="sealed artifact mismatch"):
        publish(root=root, run_dir=run, output=root / "published.md")
