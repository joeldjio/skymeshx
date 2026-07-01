from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("rclpy", reason="ROS2/rclpy not available in this environment")

from tools.ui.context.ros2_context import ROS2Context  # noqa: E402


class FakeBagRecorder:
    instances = []

    def __init__(self, output_dir="./bags"):
        self.output_dir = Path(output_dir)
        self.recording = False
        self.topics = []
        self.bag_name = ""
        self.compression = ""
        self.path = ""
        FakeBagRecorder.instances.append(self)

    def start_recording(self, topics, bag_name=None, compression="zstd"):
        self.recording = True
        self.topics = list(topics)
        self.bag_name = bag_name or "fake_bag"
        self.compression = compression
        self.path = str(self.output_dir / self.bag_name)
        return True

    def stop_recording(self):
        was_recording = self.recording
        self.recording = False
        return was_recording

    def is_recording(self):
        return self.recording

    def get_recording_status(self):
        return {
            "recording": self.recording,
            "duration_sec": 3.0 if self.recording else 0.0,
            "bag_path": self.path,
            "size_mb": 1.25,
        }


def test_bag_preset_resolves_px4_topics(qapp, tmp_path):
    ctx = ROS2Context()
    ctx._sitl_profiles = [{"namespace": "px4_2"}]

    topics = ctx._resolve_bag_topics([], "minimal_mission")

    assert "/px4_2/fmu/out/vehicle_status" in topics
    assert "/px4_2/fmu/out/vehicle_odometry" in topics
    assert "/px4_2/fmu/out/mission_result" in topics


def test_full_px4_out_preset_uses_wildcard(qapp):
    ctx = ROS2Context()
    ctx._sitl_profiles = [{"namespace": "px4_1"}]

    topics = ctx._resolve_bag_topics([], "full_px4_out")

    assert topics == ["/px4_1/fmu/out/*"]


def test_start_bag_record_with_preset_uses_output_dir_and_signals(qapp, tmp_path):
    FakeBagRecorder.instances.clear()
    ctx = ROS2Context()
    ctx._sitl_profiles = [{"namespace": "px4_1"}]
    started = []
    ctx.bagRecordStarted.connect(started.append)

    with patch("skymeshx.ros.bag_recorder.ROS2BagRecorder", FakeBagRecorder):
        assert ctx.startBagRecord([], str(tmp_path), "minimal_mission") is True

    recorder = FakeBagRecorder.instances[0]
    assert recorder.output_dir == tmp_path
    assert "/px4_1/fmu/out/vehicle_status" in recorder.topics
    assert recorder.compression == "zstd"
    assert started == [recorder.path]
    assert ctx.isBagRecording() is True


def test_stop_bag_record_returns_path_and_signal(qapp, tmp_path):
    FakeBagRecorder.instances.clear()
    ctx = ROS2Context()
    stopped = []
    ctx.bagRecordStopped.connect(lambda path, size: stopped.append((path, size)))

    with patch("skymeshx.ros.bag_recorder.ROS2BagRecorder", FakeBagRecorder):
        assert ctx.startBagRecord([], str(tmp_path), "minimal_mission") is True
        path = ctx.stopBagRecord()

    assert path
    assert stopped == [(path, 1.25)]
    assert ctx.isBagRecording() is False


def test_legacy_start_bag_recording_api_still_works(qapp):
    FakeBagRecorder.instances.clear()
    ctx = ROS2Context()

    with patch("skymeshx.ros.bag_recorder.ROS2BagRecorder", FakeBagRecorder):
        assert ctx.startBagRecording(["/fmu/out/vehicle_odometry"], "legacy_bag", "zstd") is True

    recorder = FakeBagRecorder.instances[0]
    assert recorder.topics == ["/fmu/out/vehicle_odometry"]
    assert recorder.bag_name == "legacy_bag"
    assert ctx.getBagRecordingStatus()["recording"] is True


def test_get_bag_status_alias(qapp, tmp_path):
    FakeBagRecorder.instances.clear()
    ctx = ROS2Context()

    with patch("skymeshx.ros.bag_recorder.ROS2BagRecorder", FakeBagRecorder):
        assert ctx.startBagRecord([], str(tmp_path), "minimal_mission") is True

    assert ctx.getBagStatus()["recording"] is True
