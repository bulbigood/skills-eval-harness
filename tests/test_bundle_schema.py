from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills_eval_harness.bundle import validate_run_bundle


@pytest.mark.parametrize("schema", [3, 4])
def test_validate_run_bundle_rejects_every_legacy_summary_schema(tmp_path: Path, schema: int) -> None:
    (tmp_path / "summary.json").write_text(json.dumps({"schema_version": schema}))
    with pytest.raises(ValueError, match="only summary schema version 5"):
        validate_run_bundle(tmp_path, require_seal=False)


def test_validate_run_bundle_accepts_schema_v5_at_the_schema_gate(tmp_path: Path) -> None:
    (tmp_path / "summary.json").write_text(json.dumps({"schema_version": 5}))
    with pytest.raises(ValueError, match="device telemetry"):
        validate_run_bundle(tmp_path, require_seal=False)
