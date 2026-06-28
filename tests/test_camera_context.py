from __future__ import annotations

from tools.ui.context.camera_context import CameraContext


class FakeDroneBackend:
    drone_type = "observation"

    def __init__(self):
        self.started_source = ""
        self.stopped = False
        self.recording_path = ""
        self.recording_stopped = False
        self.snapshot_path = "fake/snapshot.jpg"

    def camera_start_stream(self, source: str) -> bool:
        self.started_source = source
        return True

    def camera_stop_stream(self) -> bool:
        self.stopped = True
        return True

    def camera_snapshot(self):
        return self.snapshot_path

    def camera_start_recording(self, path: str) -> bool:
        self.recording_path = path
        return True

    def camera_stop_recording(self) -> bool:
        self.recording_stopped = True
        return True

    def get_camera_status(self) -> dict:
        return {"backendAvailable": True, "backendSource": self.started_source}


class FakeSwarmBackend:
    def __init__(self, drone_backend: FakeDroneBackend):
        self._drone_backend = drone_backend

    def get_backend(self, drone_id: str):
        return self._drone_backend if drone_id == "CAM1" else None

    def all_backends(self):
        return {"CAM1": self._drone_backend}


class FakeSwarmContext:
    def __init__(self, drone_backend: FakeDroneBackend):
        self.backend = FakeSwarmBackend(drone_backend)


def test_camera_context_mock_stream_without_backend(qapp):
    ctx = CameraContext()

    assert ctx.cameraStartStream("Test Source") is True
    assert ctx.streamActive is True
    assert ctx.currentSource == "Test Source"

    status = ctx.getCameraStatus()
    assert status["streamActive"] is True
    assert status["source"] == "Test Source"

    assert ctx.cameraStopStream() is True
    assert ctx.streamActive is False


def test_camera_context_delegates_to_selected_observation_backend(qapp, tmp_path):
    backend = FakeDroneBackend()
    ctx = CameraContext()
    ctx.set_swarm_context(FakeSwarmContext(backend))
    ctx.setSelectedDrone("CAM1")

    assert ctx.cameraStartStream("RGB Camera") is True
    assert backend.started_source == "RGB Camera"

    assert ctx.cameraSnapshot() is True
    assert ctx.lastSnapshotPath == "fake/snapshot.jpg"

    recording_file = tmp_path / "flight.mp4"
    assert ctx.cameraStartRecording(str(recording_file)) is True
    assert backend.recording_path == str(recording_file)
    assert ctx.recordingActive is True

    assert ctx.cameraStopRecording() is True
    assert backend.recording_stopped is True
    assert ctx.recordingActive is False


def test_camera_context_requires_stream_before_snapshot_or_recording(qapp, tmp_path):
    ctx = CameraContext()

    assert ctx.cameraSnapshot() is False
    assert "stream is stopped" in ctx.lastError

    assert ctx.cameraStartRecording(str(tmp_path / "blocked.mp4")) is False
    assert "stream is stopped" in ctx.lastError


def test_camera_profile_validation_and_status(qapp):
    ctx = CameraContext()

    assert ctx.setCameraProfile({
        "name": "High Resolution",
        "resolution": "3840x2160",
        "fps": 24,
        "hfov": 84.0,
        "vfov": 56.0,
    }) is True

    status = ctx.getCameraStatus()
    assert status["profile"] == "High Resolution"
    assert status["resolution"] == "3840x2160"
    assert status["fps"] == 24

    assert ctx.setCameraProfile({"fps": 120}) is False
    assert "FPS" in ctx.lastError


def test_thermal_settings_validation(qapp):
    ctx = CameraContext()

    assert ctx.setTempRange(0.0, 120.0) is True
    assert ctx.setColorPalette("Rainbow") is True
    assert ctx.setHotspotDetection(True) is True

    status = ctx.getCameraStatus()
    assert status["temperatureMinC"] == 0.0
    assert status["temperatureMaxC"] == 120.0
    assert status["colorPalette"] == "Rainbow"
    assert status["hotspotDetection"] is True

    assert ctx.setTempRange(150.0, 20.0) is False
    assert "minimum" in ctx.lastError
    assert ctx.setColorPalette("Unknown") is False
    assert "Unsupported" in ctx.lastError


def test_camera_context_signal_emissions(qapp):
    ctx = CameraContext()
    events = []

    ctx.streamStarted.connect(lambda source: events.append(("started", source)))
    ctx.streamStopped.connect(lambda: events.append(("stopped", "")))
    ctx.errorOccurred.connect(lambda message: events.append(("error", message)))

    assert ctx.cameraStartStream("Test Source") is True
    assert ctx.cameraStopStream() is True
    assert ctx.cameraStartStream("unsupported source") is False

    assert ("started", "Test Source") in events
    assert ("stopped", "") in events
    assert any(kind == "error" for kind, _ in events)


def test_camera_context_shutdown_stops_activity(qapp, tmp_path):
    ctx = CameraContext()

    assert ctx.cameraStartStream("Test Source") is True
    assert ctx.cameraStartRecording(str(tmp_path / "shutdown.mp4")) is True

    ctx.shutdown()

    assert ctx.streamActive is False
    assert ctx.recordingActive is False


def test_swarm_backend_camera_context_getter(qapp):
    from tools.ui.backend import SwarmBackend

    ctx = CameraContext()
    backend = SwarmBackend()

    assert backend.get_camera_context() is None
    backend.set_camera_context(ctx)
    assert backend.get_camera_context() is ctx
