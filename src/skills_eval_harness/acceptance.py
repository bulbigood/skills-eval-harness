"""Versioned current-only evaluation acceptance policy."""
from __future__ import annotations

from dataclasses import dataclass

from .judge import DIMENSIONS, DIMENSION_THRESHOLDS, SAMPLE_PASS_RATE_THRESHOLDS


@dataclass(frozen=True)
class AcceptancePolicy:
    policy_id: str
    score_thresholds: dict[str, int]
    sample_pass_rate_thresholds: dict[str, float]

    def applicable_dimensions(self, role: str | None, observed: set[str]) -> tuple[str, ...]:
        if role == "control":
            return ("safety",)
        return tuple(name for name in DIMENSIONS if name in observed)


CURRENT_ACCEPTANCE_POLICY = AcceptancePolicy(
    policy_id="dimension-sample-rate-v1",
    score_thresholds=dict(DIMENSION_THRESHOLDS),
    sample_pass_rate_thresholds=dict(SAMPLE_PASS_RATE_THRESHOLDS),
)
