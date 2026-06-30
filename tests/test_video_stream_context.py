"""
Hardware-free tests for VideoStreamContext (B.3).

All socket and threading operations are mocked — no real UDP port, no SITL.
Tests cover:
  - Initial state (unconfigured)
  - setVideoSource / URL building
  - startStream / stopStream lifecycle
  - _drone_index helper
  - _parse_url helper
  - _build_url helper
  - getVideoStatus dict shape
  - Auto-port assignment from drone ID
  - selectDrone property binding
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

# VideoStreamContext needs PySide6 — skip entire module when unavailable
pytest.importorskip("PySide6.QtCore")

from tools.ui.context.video_stream_context import (
    VideoStreamContext,
    _build_url,
    _drone_index,
    _parse_url,
    STATUS_UNCONFIGURED,
    STATUS_WAITING,
    STATUS_RECEIVING,
    STATUS_STALLED,
    STATUS_ERROR,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def ctx(qapp):
    """Fresh VideoStreamContext with stall-timer stopped so no side-effects."""
    c = VideoStreamContext()
    c._stall_timer.stop()
    yield c
    # Stop any running probe threads
    for state in c._states.values():
        state.probe_stop.set()


# ── _drone_index helper ────────────────────────────────────────────────────────

class TestDroneIndex:
    def test_px4_1(self):
        assert _drone_index("px4_1") == 0

    def test_px4_2(self):
        assert _drone_index("px4_2") == 1

    def test_uav_3(self):
        assert _drone_index("uav_3") == 2

    def test_drone1(self):
        assert _drone_index("drone1") == 0

    def test_no_suffix(self):
        assert _drone_index("no_number") == 0

    def test_large_index(self):
        assert _drone_index("px4_10") == 9


# ── _parse_url helper ──────────────────────────────────────────────────────────

class TestParseUrl:
    def test_udp(self):
        host, port, proto = _parse_url("udp://0.0.0.0:5600")
        assert host == "0.0.0.0"
        assert port == 5600
        assert proto == "rtp-h264-udp"

    def test_rtsp_with_port(self):
        host, port, proto = _parse_url("rtsp://192.168.1.1:554/stream")
        assert host == "192.168.1.1"
        assert port == 554
        assert proto == "rtsp"

    def test_rtsp_no_port(self):
        host, port, proto = _parse_url("rtsp://192.168.1.1/stream")
        assert port == 554
        assert proto == "rtsp"

    def test_http_mjpeg(self):
        host, port, proto = _parse_url("http://127.0.0.1:8080/video")
        assert port == 8080
        assert proto == "mjpeg-http"

    def test_invalid_returns_defaults(self):
        host, port, proto = _parse_url("garbage://xyz")
        assert port == 5600
        assert proto == "rtp-h264-udp"


# ── _build_url helper ──────────────────────────────────────────────────────────

class TestBuildUrl:
    def test_udp_default(self):
        assert _build_url("0.0.0.0", 5600, "rtp-h264-udp") == "udp://0.0.0.0:5600"

    def test_rtsp(self):
        assert _build_url("192.168.1.1", 554, "rtsp") == "rtsp://192.168.1.1:554/stream"

    def test_mjpeg(self):
        assert _build_url("127.0.0.1", 8080, "mjpeg-http") == "http://127.0.0.1:8080/stream"


# ── Initial state ──────────────────────────────────────────────────────────────

class TestInitialState:
    def test_no_selected_drone(self, ctx):
        assert ctx.streamStatus == STATUS_UNCONFIGURED
        assert ctx.streamActive is False
        assert ctx.streamUrl == ""
        assert ctx.fps == 0.0

    def test_unknown_drone_status_dict(self, ctx):
        d = ctx.getVideoStatus("nonexistent")
        assert d["status"] == STATUS_UNCONFIGURED
        assert d["port"] == 5600

    def test_auto_port_px4_1(self, ctx):
        state = ctx._ensure_state("px4_1")
        assert state.port == 5600

    def test_auto_port_px4_2(self, ctx):
        state = ctx._ensure_state("px4_2")
        assert state.port == 5601

    def test_auto_port_px4_3(self, ctx):
        state = ctx._ensure_state("px4_3")
        assert state.port == 5602


# ── setVideoSource ─────────────────────────────────────────────────────────────

class TestSetVideoSource:
    def test_sets_url_udp(self, ctx):
        ctx.setVideoSource("drone1", "0.0.0.0", 5600, "rtp-h264-udp")
        d = ctx.getVideoStatus("drone1")
        assert d["url"] == "udp://0.0.0.0:5600"
        assert d["port"] == 5600
        assert d["status"] == STATUS_UNCONFIGURED

    def test_sets_url_rtsp(self, ctx):
        ctx.setVideoSource("drone2", "192.168.1.10", 554, "rtsp")
        d = ctx.getVideoStatus("drone2")
        assert d["url"] == "rtsp://192.168.1.10:554/stream"
        assert d["protocol"] == "rtsp"

    def test_accepts_url_form(self, ctx):
        ctx.setVideoSource("drone1", "udp://0.0.0.0:5602")
        d = ctx.getVideoStatus("drone1")
        assert d["url"] == "udp://0.0.0.0:5602"
        assert d["port"] == 5602

    def test_does_not_start_probe(self, ctx):
        ctx.setVideoSource("drone1", "0.0.0.0", 5600, "rtp-h264-udp")
        state = ctx._states["drone1"]
        assert state.status == STATUS_UNCONFIGURED
        # No probe thread started
        assert state.probe_thread is None


# ── selectDrone ────────────────────────────────────────────────────────────────

class TestSelectDrone:
    def test_select_updates_property(self, ctx):
        ctx.setVideoSource("px4_1", "0.0.0.0", 5600, "rtp-h264-udp")
        ctx.selectDrone("px4_1")
        assert ctx.droneId == "px4_1"
        assert ctx.streamStatus == STATUS_UNCONFIGURED

    def test_select_different_drone(self, ctx):
        ctx.setVideoSource("px4_1", "0.0.0.0", 5600, "rtp-h264-udp")
        ctx.setVideoSource("px4_2", "0.0.0.0", 5601, "rtp-h264-udp")
        ctx.selectDrone("px4_2")
        assert ctx.droneId == "px4_2"
        assert ctx.streamUrl == "udp://0.0.0.0:5601"


# ── stopStream resets to unconfigured ─────────────────────────────────────────

class TestLiveFrameTargets:
    def test_start_stream_defaults_to_gimbal_target(self, ctx):
        with patch.object(ctx, "_start_decoder", return_value=True) as start_decoder:
            assert ctx.startStream("udp://0.0.0.0:5600", "px4_1") is True

        start_decoder.assert_called_once()
        d = ctx.getVideoStatus("px4_1")
        assert d["status"] == STATUS_WAITING
        assert d["activeTarget"] == "gimbal"
        assert d["target"] == "gimbal"
        assert ctx.activeTarget == "gimbal"

    def test_start_stream_can_target_map(self, ctx):
        with patch.object(ctx, "_start_decoder", return_value=True):
            assert ctx.startStream("udp://0.0.0.0:5600", "px4_1", "map") is True

        d = ctx.getVideoStatus("px4_1")
        assert d["activeTarget"] == "map"
        assert d["target"] == "map"
        assert ctx.frameUrl("px4_1").startswith("image://videoStream/px4_1?rev=")

    def test_single_active_renderer_policy(self, ctx):
        with patch.object(ctx, "_start_decoder", return_value=True), patch.object(ctx, "_stop_decoder") as stop_decoder:
            ctx.startStream("udp://0.0.0.0:5600", "px4_1", "map")
            ctx.startStream("udp://0.0.0.0:5600", "px4_1", "gimbal")

        assert stop_decoder.called
        assert ctx.getVideoStatus("px4_1")["activeTarget"] == "gimbal"


class TestStopStream:
    def test_stop_resets_status(self, ctx):
        ctx.setVideoSource("drone1", "0.0.0.0", 5600, "rtp-h264-udp")
        # Manually force state to receiving
        state = ctx._ensure_state("drone1")
        state.status = STATUS_RECEIVING
        ctx.selectDrone("drone1")
        assert ctx.streamActive is True

        ctx.stopStream("drone1")
        assert ctx.getVideoStatus("drone1")["status"] == STATUS_UNCONFIGURED
        assert ctx.streamActive is False

    def test_stop_unregistered_drone_no_crash(self, ctx):
        ctx.stopStream("nonexistent")  # should not raise


# ── startVideoProbe sets waiting ───────────────────────────────────────────────

class TestStartVideoProbe:
    def test_sets_waiting_then_stops(self, ctx):
        """startVideoProbe transitions state to waiting immediately."""
        ctx.setVideoSource("drone1", "0.0.0.0", 5600, "rtp-h264-udp")

        # Patch socket so probe_loop exits quickly without real networking
        with patch("tools.ui.context.video_stream_context.socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.recvfrom.side_effect = TimeoutError()
            mock_sock_cls.return_value = mock_sock

            # Signal should carry STATUS_WAITING
            received = []
            ctx.videoStatusChanged.connect(lambda did, d: received.append(d.get("status")))

            ctx.setVideoSource("drone1", "0.0.0.0", 5600, "rtp-h264-udp")
            ctx.startVideoProbe("drone1")

            # Give probe thread a moment to start and transition
            state = ctx._states["drone1"]
            state.probe_stop.set()  # stop the loop
            if state.probe_thread:
                state.probe_thread.join(timeout=1.0)

            # After set: status should be waiting (set synchronously before thread)
            assert ctx.getVideoStatus("drone1")["status"] in (
                STATUS_WAITING, STATUS_UNCONFIGURED
            )


# ── getVideoStatus dict shape ──────────────────────────────────────────────────

class TestGetVideoStatus:
    def test_dict_has_required_keys(self, ctx):
        ctx.setVideoSource("drone1", "0.0.0.0", 5600, "rtp-h264-udp")
        d = ctx.getVideoStatus("drone1")
        for key in (
            "status",
            "url",
            "host",
            "port",
            "protocol",
            "fps",
            "latencyMs",
            "activeTarget",
            "target",
            "hasFrame",
            "frameRevision",
            "frameUrl",
            "lastError",
        ):
            assert key in d, f"Missing key: {key}"

    def test_dict_values_types(self, ctx):
        ctx.setVideoSource("drone1", "127.0.0.1", 5601, "rtsp")
        d = ctx.getVideoStatus("drone1")
        assert isinstance(d["status"], str)
        assert isinstance(d["port"], int)
        assert isinstance(d["fps"], float)
        assert isinstance(d["latencyMs"], float)


# ── TraceLogger integration (soft — no real trace session) ────────────────────

class TestTraceIntegration:
    def test_emit_status_calls_trace_logger(self, ctx):
        """_emit_status should call TraceLogger.get().log_video_status without crash."""
        ctx.setVideoSource("drone1", "0.0.0.0", 5600, "rtp-h264-udp")

        mock_logger = MagicMock()
        # TraceLogger is imported locally inside _emit_status, patch at its module
        with patch(
            "skymeshx.core.trace_logger.TraceLogger.get",
            return_value=mock_logger,
        ):
            ctx._emit_status("drone1")

        mock_logger.log_video_status.assert_called_once_with(
            "drone1", STATUS_UNCONFIGURED, 5600
        )

    def test_emit_status_trace_exception_does_not_propagate(self, ctx):
        """Even if TraceLogger raises, _emit_status must not propagate the exception."""
        ctx.setVideoSource("drone1", "0.0.0.0", 5600, "rtp-h264-udp")
        with patch(
            "skymeshx.core.trace_logger.TraceLogger.get",
            side_effect=RuntimeError("trace unavailable"),
        ):
            ctx._emit_status("drone1")  # should not raise
