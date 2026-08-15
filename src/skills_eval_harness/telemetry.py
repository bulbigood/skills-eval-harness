"""Sanitized, schema-constrained whole-host telemetry for evaluation runs."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from .hashing import atomic_write_json


class StrictTelemetryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LegacyHostCapacity(StrictTelemetryModel):
    logical_cpus: int = Field(ge=1)
    total_memory_bytes: int = Field(ge=1)
    total_swap_bytes: int = Field(ge=0)
    docker_metrics_available: bool


class HostCapacity(LegacyHostCapacity):
    telemetry_scope: Literal["whole-host"]
    network_scope: Literal["default-route-interfaces"]
    disk_scope: Literal["whole-block-devices"]
    filesystem_scope: Literal["root-filesystem"]


class LegacyDeviceSample(StrictTelemetryModel):
    elapsed_ms: int = Field(ge=0)
    cpu_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    load1: float = Field(ge=0, allow_inf_nan=False)
    mem_available_bytes: int = Field(ge=0)
    swap_free_bytes: int = Field(ge=0)
    running_containers: int = Field(ge=0)


class DeviceSample(LegacyDeviceSample):
    network_rx_bytes: int = Field(ge=0)
    network_tx_bytes: int = Field(ge=0)
    disk_read_bytes: int = Field(ge=0)
    disk_write_bytes: int = Field(ge=0)
    rootfs_used_bytes: int = Field(ge=0)
    rootfs_free_bytes: int = Field(ge=0)
    network_rx_bytes_per_second: float = Field(ge=0, allow_inf_nan=False)
    network_tx_bytes_per_second: float = Field(ge=0, allow_inf_nan=False)
    disk_read_bytes_per_second: float = Field(ge=0, allow_inf_nan=False)
    disk_write_bytes_per_second: float = Field(ge=0, allow_inf_nan=False)


class Peaks(StrictTelemetryModel):
    cpu_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    load1: float = Field(ge=0, allow_inf_nan=False)
    running_containers: int = Field(ge=0)
    network_rx_bytes_per_second: float = Field(ge=0, allow_inf_nan=False)
    network_tx_bytes_per_second: float = Field(ge=0, allow_inf_nan=False)
    disk_read_bytes_per_second: float = Field(ge=0, allow_inf_nan=False)
    disk_write_bytes_per_second: float = Field(ge=0, allow_inf_nan=False)
    rootfs_used_bytes: int = Field(ge=0)


class Minima(StrictTelemetryModel):
    mem_available_bytes: int = Field(ge=0)
    swap_free_bytes: int = Field(ge=0)
    rootfs_free_bytes: int = Field(ge=0)


class IoTotals(StrictTelemetryModel):
    network_rx_bytes: int = Field(ge=0)
    network_tx_bytes: int = Field(ge=0)
    disk_read_bytes: int = Field(ge=0)
    disk_write_bytes: int = Field(ge=0)


class LegacyDeviceTelemetry(StrictTelemetryModel):
    schema_version: Literal[1]
    started_unix_ms: int = Field(ge=0)
    finished_unix_ms: int = Field(ge=0)
    host: LegacyHostCapacity
    samples: tuple[LegacyDeviceSample, ...] = Field(min_length=1)
    docker_oom_events: int = Field(ge=0)


class DeviceTelemetry(StrictTelemetryModel):
    schema_version: Literal[2]
    started_unix_ms: int = Field(ge=0)
    finished_unix_ms: int = Field(ge=0)
    host: HostCapacity
    samples: tuple[DeviceSample, ...] = Field(min_length=1)
    peaks: Peaks
    minima: Minima
    totals: IoTotals
    docker_oom_events: int = Field(ge=0)
    sampling_errors: int = Field(ge=0)
    terminal_status: Literal["completed", "failed"]


_TELEMETRY_ADAPTER = TypeAdapter(LegacyDeviceTelemetry | DeviceTelemetry)
_COUNTERS = ("network_rx_bytes", "network_tx_bytes", "disk_read_bytes", "disk_write_bytes")


def validate_device_telemetry(path: Path) -> LegacyDeviceTelemetry | DeviceTelemetry:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        telemetry = _TELEMETRY_ADAPTER.validate_python(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"invalid or sensitive device telemetry: {exc}") from exc
    if telemetry.finished_unix_ms < telemetry.started_unix_ms:
        raise ValueError("invalid or sensitive device telemetry: finish precedes start")
    return telemetry


def set_terminal_status(path: Path, status: Literal["completed", "failed"]) -> DeviceTelemetry:
    """Atomically update a schema-v2 terminal status before sealing."""
    telemetry = validate_device_telemetry(path)
    if not isinstance(telemetry, DeviceTelemetry):
        raise ValueError("legacy telemetry terminal status cannot be updated")
    updated = telemetry.model_copy(update={"terminal_status": status})
    atomic_write_json(path, updated.model_dump(mode="json"))
    return updated


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


def _network_totals() -> tuple[int, int]:
    route_lines = Path("/proc/net/route").read_text(encoding="utf-8").splitlines()[1:]
    interfaces = {
        fields[0]
        for line in route_lines
        if len(fields := line.split()) >= 4
        and fields[1] == "00000000"
        and int(fields[3], 16) & 0x1
    }
    if not interfaces:
        raise ValueError("host telemetry requires an active default-route interface")
    received = transmitted = 0
    for line in Path("/proc/net/dev").read_text(encoding="utf-8").splitlines()[2:]:
        interface, values = line.split(":", 1)
        if interface.strip() not in interfaces:
            continue
        fields = values.split()
        received += int(fields[0])
        transmitted += int(fields[8])
    return received, transmitted


def _disk_totals() -> tuple[int, int]:
    read_sectors = write_sectors = 0
    for line in Path("/proc/diskstats").read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) < 14:
            continue
        device = fields[2]
        if not (Path("/sys/block") / device).exists():
            continue
        read_sectors += int(fields[5])
        write_sectors += int(fields[9])
    return read_sectors * 512, write_sectors * 512


def _rootfs_usage() -> tuple[int, int]:
    usage = shutil.disk_usage("/")
    return usage.used, usage.free


def _container_count() -> tuple[int, bool]:
    try:
        completed = subprocess.run(
            ["docker", "ps", "-q"], text=True, capture_output=True, check=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return 0, False
    return len([line for line in completed.stdout.splitlines() if line]), True


def _rates(previous: dict[str, int], current: dict[str, int]) -> dict[str, float]:
    elapsed_seconds = (current["elapsed_ms"] - previous["elapsed_ms"]) / 1000
    return {
        f"{name}_per_second": (
            max(0.0, (current[name] - previous[name]) / elapsed_seconds)
            if elapsed_seconds > 0 else 0.0
        )
        for name in _COUNTERS
    }


class TelemetryRecorder:
    """Collect numeric whole-host metrics; never names, paths, env, labels, or commands."""

    def __init__(self, output: Path, period_seconds: float = 2.0):
        self.output = output
        self.period_seconds = period_seconds
        self.started_unix_ms = int(time.time() * 1000)
        self.started_monotonic = time.monotonic()
        self.samples: list[DeviceSample] = []
        self.stop_event = threading.Event()
        self.previous_cpu = _cpu_totals()
        self.oom_process: subprocess.Popen[str] | None = None
        self.sampling_errors = 0
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
            self._stop_oom_monitor()
            raise

    def _stop_oom_monitor(self) -> str:
        if self.oom_process is None:
            return ""
        self.oom_process.terminate()
        try:
            self.oom_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.oom_process.kill()
            try:
                self.oom_process.wait(timeout=10)
            except (OSError, subprocess.SubprocessError):
                pass
        except (OSError, subprocess.SubprocessError):
            pass
        finally:
            stdout = ""
            stream = getattr(self.oom_process, "stdout", None)
            if stream is not None:
                try:
                    stdout = stream.read()
                except OSError:
                    stdout = ""
            self.oom_process = None
        return stdout

    def _sample(self) -> None:
        total, idle = _cpu_totals()
        old_total, old_idle = self.previous_cpu
        delta_total = total - old_total
        cpu = 0.0 if delta_total <= 0 else 100.0 * (1.0 - (idle - old_idle) / delta_total)
        self.previous_cpu = (total, idle)
        memory = _meminfo()
        containers, _ = _container_count()
        network_rx, network_tx = _network_totals()
        disk_read, disk_write = _disk_totals()
        rootfs_used, rootfs_free = _rootfs_usage()
        counters = {
            "elapsed_ms": max(0, int((time.monotonic() - self.started_monotonic) * 1000)),
            "network_rx_bytes": network_rx,
            "network_tx_bytes": network_tx,
            "disk_read_bytes": disk_read,
            "disk_write_bytes": disk_write,
        }
        rates = _rates(self.samples[-1].model_dump(), counters) if self.samples else {
            f"{name}_per_second": 0.0 for name in _COUNTERS
        }
        self.samples.append(DeviceSample(
            elapsed_ms=int(counters["elapsed_ms"]),
            network_rx_bytes=int(counters["network_rx_bytes"]),
            network_tx_bytes=int(counters["network_tx_bytes"]),
            disk_read_bytes=int(counters["disk_read_bytes"]),
            disk_write_bytes=int(counters["disk_write_bytes"]),
            network_rx_bytes_per_second=float(rates["network_rx_bytes_per_second"]),
            network_tx_bytes_per_second=float(rates["network_tx_bytes_per_second"]),
            disk_read_bytes_per_second=float(rates["disk_read_bytes_per_second"]),
            disk_write_bytes_per_second=float(rates["disk_write_bytes_per_second"]),
            cpu_percent=max(0.0, min(100.0, cpu)),
            load1=max(0.0, float(Path("/proc/loadavg").read_text(encoding="utf-8").split()[0])),
            mem_available_bytes=max(0, memory.get("MemAvailable", 0)),
            swap_free_bytes=max(0, memory.get("SwapFree", 0)),
            running_containers=containers,
            rootfs_used_bytes=rootfs_used,
            rootfs_free_bytes=rootfs_free,
        ))

    def _loop(self) -> None:
        while not self.stop_event.wait(self.period_seconds):
            try:
                self._sample()
            except Exception:
                self.sampling_errors += 1
                self.stop_event.set()

    def stop(self, terminal_status: Literal["completed", "failed"] = "completed") -> DeviceTelemetry:
        if self.stopped:
            telemetry = validate_device_telemetry(self.output)
            if not isinstance(telemetry, DeviceTelemetry):
                raise ValueError("new telemetry recorder produced a legacy schema")
            return telemetry
        self.stopped = True
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join()
        oom_events = 0
        try:
            try:
                self._sample()
            except Exception:
                self.sampling_errors += 1
        finally:
            stdout = self._stop_oom_monitor()
            oom_events = len([line for line in stdout.splitlines() if line.strip()])
        memory = _meminfo()
        _, docker_available = _container_count()
        first = self.samples[0]
        last = self.samples[-1]
        telemetry = DeviceTelemetry(
            schema_version=2,
            started_unix_ms=self.started_unix_ms,
            finished_unix_ms=int(time.time() * 1000),
            host=HostCapacity(
                logical_cpus=os.cpu_count() or 1,
                total_memory_bytes=memory["MemTotal"],
                total_swap_bytes=memory.get("SwapTotal", 0),
                docker_metrics_available=docker_available,
                telemetry_scope="whole-host",
                network_scope="default-route-interfaces",
                disk_scope="whole-block-devices",
                filesystem_scope="root-filesystem",
            ),
            samples=tuple(self.samples),
            peaks=Peaks(
                cpu_percent=max(sample.cpu_percent for sample in self.samples),
                load1=max(sample.load1 for sample in self.samples),
                running_containers=max(sample.running_containers for sample in self.samples),
                network_rx_bytes_per_second=max(sample.network_rx_bytes_per_second for sample in self.samples),
                network_tx_bytes_per_second=max(sample.network_tx_bytes_per_second for sample in self.samples),
                disk_read_bytes_per_second=max(sample.disk_read_bytes_per_second for sample in self.samples),
                disk_write_bytes_per_second=max(sample.disk_write_bytes_per_second for sample in self.samples),
                rootfs_used_bytes=max(sample.rootfs_used_bytes for sample in self.samples),
            ),
            minima=Minima(
                mem_available_bytes=min(sample.mem_available_bytes for sample in self.samples),
                swap_free_bytes=min(sample.swap_free_bytes for sample in self.samples),
                rootfs_free_bytes=min(sample.rootfs_free_bytes for sample in self.samples),
            ),
            totals=IoTotals(**{
                name: max(0, getattr(last, name) - getattr(first, name)) for name in _COUNTERS
            }),
            docker_oom_events=oom_events,
            sampling_errors=self.sampling_errors,
            terminal_status="failed" if self.sampling_errors else terminal_status,
        )
        atomic_write_json(self.output, telemetry.model_dump(mode="json"))
        validate_device_telemetry(self.output)
        if self.sampling_errors:
            raise RuntimeError("device telemetry sampling failed; partial metrics were persisted")
        return telemetry
