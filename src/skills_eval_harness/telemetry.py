"""Sanitized, schema-constrained device telemetry for evaluation runs."""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .hashing import atomic_write_json


class StrictTelemetryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class HostCapacity(StrictTelemetryModel):
    logical_cpus: int = Field(ge=1)
    total_memory_bytes: int = Field(ge=1)
    total_swap_bytes: int = Field(ge=0)
    docker_metrics_available: bool


class DeviceSample(StrictTelemetryModel):
    elapsed_ms: int = Field(ge=0)
    cpu_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    load1: float = Field(ge=0, allow_inf_nan=False)
    mem_available_bytes: int = Field(ge=0)
    swap_free_bytes: int = Field(ge=0)
    running_containers: int = Field(ge=0)


class DeviceTelemetry(StrictTelemetryModel):
    schema_version: int = Field(ge=1, le=1)
    started_unix_ms: int = Field(ge=0)
    finished_unix_ms: int = Field(ge=0)
    host: HostCapacity
    samples: tuple[DeviceSample, ...] = Field(min_length=1)
    docker_oom_events: int = Field(ge=0)


def validate_device_telemetry(path: Path) -> DeviceTelemetry:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        telemetry = DeviceTelemetry.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"invalid or sensitive device telemetry: {exc}") from exc
    if telemetry.finished_unix_ms < telemetry.started_unix_ms:
        raise ValueError("invalid or sensitive device telemetry: finish precedes start")
    return telemetry


def _meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        name, value = line.split(":", 1)
        values[name] = int(value.strip().split()[0]) * 1024
    return values


def _cpu_totals() -> tuple[int, int]:
    fields = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0].split()[1:]
    values = [int(value) for value in fields]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return sum(values), idle


def _container_count() -> tuple[int, bool]:
    try:
        completed = subprocess.run(
            ["docker", "ps", "-q"], text=True, capture_output=True, check=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return 0, False
    return len([line for line in completed.stdout.splitlines() if line]), True


class TelemetryRecorder:
    """Collect only numeric capacity/load metrics; never names, paths, env, labels, or commands."""

    def __init__(self, output: Path, period_seconds: float = 2.0):
        self.output = output
        self.period_seconds = period_seconds
        self.started_unix_ms = int(time.time() * 1000)
        self.started_monotonic = time.monotonic()
        self.samples: list[DeviceSample] = []
        self.stop_event = threading.Event()
        self.previous_cpu = _cpu_totals()
        self.oom_process: subprocess.Popen[str] | None = None
        self.stopped = False
        self.thread = threading.Thread(target=self._loop, name="sanitized-device-telemetry", daemon=True)

    def start(self) -> None:
        try:
            self.oom_process = subprocess.Popen(
                [
                    "docker", "events", "--since", str(self.started_unix_ms // 1000),
                    "--filter", "event=oom", "--format", "{{json .}}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except OSError:
            self.oom_process = None
        try:
            self._sample()
            self.thread.start()
        except Exception:
            if self.oom_process is not None:
                self.oom_process.terminate()
                try:
                    self.oom_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.oom_process.kill()
                    try:
                        self.oom_process.wait(timeout=10)
                    except subprocess.SubprocessError:
                        pass
                except (OSError, subprocess.SubprocessError):
                    pass
                finally:
                    self.oom_process = None
            raise

    def _sample(self) -> None:
        total, idle = _cpu_totals()
        old_total, old_idle = self.previous_cpu
        delta_total = total - old_total
        cpu = 0.0 if delta_total <= 0 else 100.0 * (1.0 - (idle - old_idle) / delta_total)
        self.previous_cpu = (total, idle)
        memory = _meminfo()
        containers, _ = _container_count()
        self.samples.append(DeviceSample(
            elapsed_ms=max(0, int((time.monotonic() - self.started_monotonic) * 1000)),
            cpu_percent=max(0.0, min(100.0, cpu)),
            load1=max(0.0, float(Path("/proc/loadavg").read_text(encoding="utf-8").split()[0])),
            mem_available_bytes=max(0, memory.get("MemAvailable", 0)),
            swap_free_bytes=max(0, memory.get("SwapFree", 0)),
            running_containers=containers,
        ))

    def _loop(self) -> None:
        while not self.stop_event.wait(self.period_seconds):
            self._sample()

    def stop(self) -> DeviceTelemetry:
        if self.stopped:
            return validate_device_telemetry(self.output)
        self.stopped = True
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(timeout=max(1.0, self.period_seconds * 2))
        oom_events = 0
        try:
            self._sample()
        finally:
            if self.oom_process is not None:
                self.oom_process.terminate()
                try:
                    stdout, _ = self.oom_process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    self.oom_process.kill()
                    stdout, _ = self.oom_process.communicate(timeout=10)
                oom_events = len([line for line in stdout.splitlines() if line.strip()])
        memory = _meminfo()
        _, docker_available = _container_count()
        telemetry = DeviceTelemetry(
            schema_version=1,
            started_unix_ms=self.started_unix_ms,
            finished_unix_ms=int(time.time() * 1000),
            host=HostCapacity(
                logical_cpus=os.cpu_count() or 1,
                total_memory_bytes=memory["MemTotal"],
                total_swap_bytes=memory.get("SwapTotal", 0),
                docker_metrics_available=docker_available,
            ),
            samples=tuple(self.samples),
            docker_oom_events=oom_events,
        )
        atomic_write_json(self.output, telemetry.model_dump(mode="json"))
        validate_device_telemetry(self.output)
        return telemetry
