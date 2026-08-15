from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from skills_eval_harness.telemetry import TelemetryRecorder


class StubbornProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False
        self.wait_calls = 0

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: int) -> int:
        self.wait_calls += 1
        if self.wait_calls == 1:
            raise subprocess.TimeoutExpired("docker events", timeout)
        return 0


def test_startup_failure_kills_stubborn_oom_monitor(tmp_path: Path) -> None:
    process = StubbornProcess()
    recorder = TelemetryRecorder(tmp_path / "telemetry.json", 0.01)
    with (
        patch("skills_eval_harness.telemetry.subprocess.Popen", return_value=process),
        patch.object(recorder, "_sample", side_effect=RuntimeError("sample failed")),
        pytest.raises(RuntimeError, match="sample failed"),
    ):
        recorder.start()
    assert process.terminated is True
    assert process.killed is True
    assert process.wait_calls == 2
    assert recorder.oom_process is None
