#!/usr/bin/env python3
"""Shared concurrency defaults and normalization for evaluation suites."""

from __future__ import annotations

import os
from pathlib import Path


JOBS_PER_PHYSICAL_CORE = 4
MIN_JOBS = 1
MAX_JOBS = 20


def physical_core_count() -> int:
    """Return available physical cores, preferring Linux topology metadata."""
    allowed_cpus = (
        set(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else None
    )
    topology_root = Path("/sys/devices/system/cpu")
    physical_cores: set[tuple[str, str]] = set()
    for cpu_root in topology_root.glob("cpu[0-9]*"):
        try:
            cpu = int(cpu_root.name[3:])
        except ValueError:
            continue
        if allowed_cpus is not None and cpu not in allowed_cpus:
            continue
        topology = cpu_root / "topology"
        try:
            package = (topology / "physical_package_id").read_text(encoding="utf-8").strip()
            core = (topology / "core_id").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        physical_cores.add((package, core))
    if physical_cores:
        return len(physical_cores)
    return max(MIN_JOBS, len(allowed_cpus) if allowed_cpus is not None else (os.cpu_count() or 1))


def default_jobs(physical_cores: int | None = None) -> int:
    """Use four jobs per available physical core within the global cap."""
    cores = physical_core_count() if physical_cores is None else physical_cores
    if cores < 1:
        raise ValueError("physical core count must be at least 1")
    return min(MAX_JOBS, cores * JOBS_PER_PHYSICAL_CORE)


def normalize_jobs(requested: int, *, target_count: int, balanced: bool) -> int:
    """Clamp concurrency and preserve complete target groups for balanced waves."""
    if target_count < 1:
        raise ValueError("target count must be at least 1")
    bounded = min(MAX_JOBS, max(MIN_JOBS, requested))
    if not balanced:
        return bounded
    if target_count > MAX_JOBS:
        raise ValueError(
            f"balanced target count {target_count} exceeds the jobs cap {MAX_JOBS}"
        )
    if bounded < target_count:
        return target_count
    return bounded - (bounded % target_count)


DEFAULT_JOBS = default_jobs()
