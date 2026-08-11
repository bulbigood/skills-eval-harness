"""Agent/judge profile loading with shared fixture provenance."""
from __future__ import annotations

import json
from pathlib import Path


EVAL = Path(__file__).resolve().parent.parent
FIXTURES_FILE = EVAL / "fixtures.json"
REQUIRED_PROFILE_KEYS = {
    "name",
    "agent_command",
    "judge_command",
    "timeout_seconds",
    "samples",
}


def load_agent_config(
    path: Path,
    fixtures_path: Path = FIXTURES_FILE,
) -> dict:
    """Load one explicit model profile and attach the canonical fixture registry."""
    profile = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_PROFILE_KEYS - profile.keys())
    if missing:
        raise ValueError(f"agent config missing required keys: {', '.join(missing)}")
    if "fixtures" in profile:
        raise ValueError("agent config must not duplicate the shared fixture registry")
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    if not fixtures:
        raise ValueError("fixture registry must not be empty")
    return {**profile, "fixtures": fixtures}
