"""Evaluation matrix construction and balanced-wave scheduling."""
from __future__ import annotations

import concurrent.futures
import hashlib
import threading
from dataclasses import dataclass
from typing import Callable, TypeVar

from experiment import EvalTarget
from .scenarios import Scenario


Task = TypeVar("Task")
Result = TypeVar("Result")

@dataclass(frozen=True)
class MatrixCell:
    target_id: str
    scenario_id: str
    sample_index: int
    pair_id: str
    target: EvalTarget
    scenario: "Scenario"

def build_matrix(experiment, scenarios) -> list[MatrixCell]:
    """Expand a complete matrix in scenario/sample/target order."""
    selected = {scenario.id: scenario for scenario in scenarios}
    scenario_ids = tuple(scenario_id for scenario_id in experiment.scenario_ids if scenario_id in selected)
    if not scenario_ids:
        raise ValueError("no experiment scenarios selected")
    cells = []
    for scenario_id in scenario_ids:
        for sample in range(1, experiment.samples + 1):
            pair_id = hashlib.sha256(
                f"{experiment.name}\0{scenario_id}\0{sample}".encode()
            ).hexdigest()[:16]
            for target in experiment.targets:
                cells.append(MatrixCell(target.id, scenario_id, sample, pair_id, target, selected[scenario_id]))
    expected = len(experiment.targets) * len(scenario_ids) * experiment.samples
    identities = {(c.target_id, c.scenario_id, c.sample_index) for c in cells}
    if len(cells) != expected or len(identities) != expected:
        raise ValueError("incomplete or duplicate evaluation matrix")
    return cells

def balanced_waves(cells: list[MatrixCell], jobs: int) -> list[list[MatrixCell]]:
    """Group complete comparison sets into equal-arm counterbalanced waves."""
    if not cells:
        return []
    first_pair_id = cells[0].pair_id
    target_count = next(
        (index for index, cell in enumerate(cells) if cell.pair_id != first_pair_id),
        len(cells),
    )
    if target_count < 2 or jobs < target_count or jobs % target_count:
        raise ValueError(
            "balanced_waves requires jobs to be a positive multiple of the target count"
        )
    groups: list[list[MatrixCell]] = []
    for offset in range(0, len(cells), target_count):
        group = cells[offset : offset + target_count]
        if len(group) != target_count or len({cell.pair_id for cell in group}) != 1:
            raise ValueError("balanced_waves requires adjacent complete target groups")
        rotation = (group[0].sample_index - 1) % target_count
        groups.append(group[rotation:] + group[:rotation])
    groups_per_wave = jobs // target_count
    waves = [
        [cell for group in groups[offset : offset + groups_per_wave] for cell in group]
        for offset in range(0, len(groups), groups_per_wave)
    ]
    if any(len(wave) > jobs or len(wave) % target_count for wave in waves):
        raise ValueError("balanced_waves requires complete target groups")
    return waves

def worker_waves(
    cells: list[MatrixCell], jobs: int, target_count: int
) -> list[list[MatrixCell]]:
    """Schedule single-arm chunks or preserve counterbalanced comparison waves."""
    if target_count == 1:
        if jobs < 1:
            raise ValueError("single-arm worker waves require at least one job")
        return [cells[offset : offset + jobs] for offset in range(0, len(cells), jobs)]
    if target_count >= 2:
        return balanced_waves(cells, jobs)
    raise ValueError("worker scheduling requires at least one target")


def execute_synchronized_waves(
    waves: list[list[Task]],
    execute: Callable[[Task, int], Result],
) -> list[Result]:
    """Execute complete waves with synchronized starts and fail-fast collection."""
    results: list[Result] = []
    for wave_id, wave in enumerate(waves, start=1):
        start_barrier = threading.Barrier(len(wave))

        def execute_started(task: Task) -> Result:
            start_barrier.wait()
            return execute(task, wave_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(wave)) as executor:
            results.extend(executor.map(execute_started, wave))
    return results
