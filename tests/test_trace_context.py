from __future__ import annotations

import json
from pathlib import Path

from skymeshx.core.trace_logger import TraceLogger
from tools.ui.context.trace_context import TraceContext


def test_trace_context_start_stop_and_export(qapp, tmp_path):
    logger = TraceLogger(root=tmp_path / "trace_runs")
    ctx = TraceContext(logger=logger)
    events = []

    ctx.sessionStarted.connect(lambda path: events.append(("started", path)))
    ctx.sessionStopped.connect(lambda path: events.append(("stopped", path)))

    ok = ctx.startSession(
        "gz_x500_gimbal",
        {
            "px4": {"model": "gz_x500_gimbal", "world": "default"},
            "vehicles": [{"droneId": "drone1", "namespace": "px4_1", "videoPort": 5600}],
        },
    )

    assert ok is True
    assert ctx.sessionActive is True
    assert ctx.sessionScenario == "gz_x500_gimbal"
    assert Path(ctx.sessionPath).exists()
    assert events[0][0] == "started"

    logger.log_mission_event("mission_start", {"droneId": "drone1"})

    stopped_path = ctx.stopSession()
    assert Path(stopped_path).exists()
    assert ctx.sessionActive is False
    assert events[-1] == ("stopped", stopped_path)

    summary_path = ctx.exportSummary()
    assert Path(summary_path).exists()
    assert "Trace Summary" in Path(summary_path).read_text(encoding="utf-8")


def test_trace_context_reports_nested_session_error(qapp, tmp_path):
    logger = TraceLogger(root=tmp_path / "trace_runs")
    ctx = TraceContext(logger=logger)
    errors = []
    ctx.sessionError.connect(errors.append)

    assert ctx.startSession("one", {}) is True
    assert ctx.startSession("two", {}) is False

    assert errors
    assert "already active" in errors[-1]
    assert ctx.lastError == errors[-1]
    ctx.stopSession()


def test_trace_context_manifest_includes_world_profile(qapp, tmp_path):
    logger = TraceLogger(root=tmp_path / "trace_runs")
    ctx = TraceContext(logger=logger)

    assert ctx.startSession(
        "ridge_test",
        {
            "model": "gz_x500_lidar_down",
            "worldProfile": "ridge_terrain",
            "world": "ridge",
            "modelPose": "0,0,0,0,0,0",
            "worldEnv": {"PX4_GZ_WORLD": "ridge"},
        },
    )
    session_path = Path(ctx.sessionPath)
    ctx.stopSession()

    manifest = json.loads((session_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["px4"]["model"] == "gz_x500_lidar_down"
    assert manifest["px4"]["world"] == "ridge"
    assert manifest["gazeboWorld"]["profile"] == "ridge_terrain"
    assert manifest["gazeboWorld"]["env"]["PX4_GZ_WORLD"] == "ridge"


def test_service_locator_registers_trace_context(qapp):
    from tools.ui.service_locator import build_default_locator

    locator = build_default_locator()
    locator.eager_init()

    assert locator.has("trace")
    assert isinstance(locator["trace"], TraceContext)
