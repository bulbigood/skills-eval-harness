"""Validated view model shared by absolute and paired reports."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict

from .models import Suite
from .provenance import Provenance


class ReportContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    summary: dict[str, Any]
    run_id: str
    report_revision: str
    suite_id: str
    suite_kind: Literal["absolute", "paired"]
    run_purpose: str
    arms: tuple[dict[str, Any], ...]
    agent_name: str
    agent_version: str
    worker_model: str
    worker_reasoning: str
    judge_backend: str
    judge_model: str
    judge_reasoning: str
    runtime_version: str
    runtime_sha256: str
    skill_name: str
    skill_version: str
    skill_url: str
    skill_sha256: str
    source_commit: str
    source_tree_sha256: str
    harness_repository: str
    harness_commit: str
    harness_tree_sha256: str
    harbor_version: str
    node_version: str
    agent_image_sha256: str
    verifier_image_sha256: str
    config_sha256: str
    suite_sha256: str
    catalog_sha256: str
    effective_suite_sha256: str
    fixture_registry_sha256: str
    task_checksums: dict[str, str]
    checksum_name: str
    evidence_link: str | None

    @classmethod
    def from_validated_bundle(
        cls,
        run_dir: Path,
        *,
        summary: dict[str, Any],
        output: Path,
        repository: str,
        include_evidence: bool,
    ) -> "ReportContext":
        if summary.get("schema_version") != 5:
            raise ValueError("only summary schema version 5 is supported for reports")
        manifest = json.loads((run_dir / "run-manifest.json").read_text(encoding="utf-8"))
        suite = Suite.model_validate(manifest["suite"])
        if summary.get("analysis", {}).get("kind") != suite.kind:
            raise ValueError("summary analysis kind does not match the validated effective suite")
        provenance = Provenance.model_validate_json(
            (run_dir / "provenance.json").read_text(encoding="utf-8")
        ).validated()
        config = yaml.safe_load((run_dir / "inputs/config.yaml").read_text(encoding="utf-8"))
        agent = config["agents"][manifest["agent"]]
        judge = config["judge"]
        skill_text = (run_dir / "inputs/selected-skill/SKILL.md").read_text(encoding="utf-8")
        if not skill_text.startswith("---\n") or "\n---\n" not in skill_text[4:]:
            raise ValueError("selected skill must have YAML frontmatter")
        metadata = yaml.safe_load(skill_text.split("\n---\n", 1)[0][4:])
        version = metadata.get("metadata", {}).get("version") if isinstance(metadata, dict) else None
        if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str) or not isinstance(version, str):
            raise ValueError("selected skill frontmatter requires string name and version")
        match = re.search(r"-v(\d+)$", output.stem)
        evidence_dir = output.with_suffix(".evidence")
        return cls(
            summary=summary,
            run_id=manifest["run_id"],
            report_revision=f"v{match.group(1)}" if match else "unversioned",
            suite_id=suite.id,
            suite_kind=suite.kind,
            run_purpose=manifest["run_purpose"],
            arms=tuple(arm.model_dump(mode="json") for arm in suite.arms),
            agent_name=manifest["agent"], agent_version=manifest["agent_version"],
            worker_model=agent["model"], worker_reasoning=agent["reasoning"],
            judge_backend=manifest.get("judge_backend", "api-key"),
            judge_model=judge["model"], judge_reasoning=judge["reasoning"],
            runtime_version=provenance.runtime_version, runtime_sha256=provenance.runtime_sha256,
            skill_name=metadata["name"], skill_version=version, skill_url=provenance.source_url,
            skill_sha256=provenance.selected_skill_sha256, source_commit=provenance.source_commit,
            source_tree_sha256=provenance.source_tree_sha256, harness_repository=repository,
            harness_commit=provenance.harness_commit, harness_tree_sha256=provenance.harness_tree_sha256,
            harbor_version=provenance.harbor_version, node_version=provenance.node_version,
            agent_image_sha256=provenance.image_digests["agent"],
            verifier_image_sha256=provenance.image_digests["verifier"],
            config_sha256=provenance.config_sha256, suite_sha256=provenance.suite_sha256,
            catalog_sha256=provenance.scenario_catalog_sha256,
            effective_suite_sha256=provenance.effective_suite_sha256,
            fixture_registry_sha256=provenance.fixture_registry_sha256,
            task_checksums=provenance.task_checksums,
            checksum_name=output.name + ".sha256",
            evidence_link=f"{evidence_dir.name}/run-seal.json" if include_evidence else None,
        )
