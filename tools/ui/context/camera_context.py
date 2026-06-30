"""
CameraContext - QML-facing camera, recording, and thermal settings bridge.

The context is deliberately hardware-free by default. If a SwarmContext is
injected, camera calls are delegated to the selected observation drone when
possible; otherwise the Test Source path still behaves predictably for UI work
and automated tests.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot


class CameraContext(QObject):
    """Expose camera controls and status to QML."""

    streamStarted = Signal(str, arguments=["source"])
    streamStopped = Signal()
    recordingStarted = Signal(str, arguments=["path"])
    recordingStopped = Signal(int, arguments=["duration"])
    snapshotCaptured = Signal(str, arguments=["path"])
    errorOccurred = Signal(str, arguments=["message"])
    statusChanged = Signal()
    logMessage = Signal(str, str, arguments=["level", "text"])

    def __init__(self, parent=None):
        super().__init__(parent)
        self._swarm_context: Optional[Any] = None
        self._selected_drone_id = ""
        self._available_sources = [
            "None",
            "RGB Camera",
            "Thermal Camera",
            "Multispectral",
            "RTSP Stream",
            "ROS2 Topic",
            "Test Source",
        ]
        self._current_source = "None"
        self._stream_active = False
        self._recording_active = False
        self._recording_started_at = 0.0
        self._recording_duration = 0
        self._recording_path = ""
        self._frame_age = 0
        self._dropped_frames = 0
        self._last_error = ""
        self._last_snapshot_path = ""
        self._profile = {
            "name": "RGB Camera",
            "resolution": "1920x1080",
            "fps": 30,
            "hfov": 90.0,
            "vfov": 60.0,
            "format": "H264",
        }
        self._temp_min_c = -40.0
        self._temp_max_c = 200.0
        self._color_palette = "Ironbow"
        self._hotspot_detection = False

        self._recording_timer = QTimer(self)
        self._recording_timer.setInterval(1000)
        self._recording_timer.timeout.connect(self._update_recording_duration)

    def set_swarm_context(self, swarm_context: Any) -> None:
        self._swarm_context = swarm_context

    def shutdown(self) -> None:
        """Stop active camera activity during application shutdown."""
        if self._recording_active:
            self.cameraStopRecording()
        if self._stream_active:
            self.cameraStopStream()
        self._recording_timer.stop()

    @Property("QVariantList", notify=statusChanged)
    def availableSources(self):
        return list(self._available_sources)

    @Property(str, notify=statusChanged)
    def selectedDroneId(self):
        return self._selected_drone_id

    @selectedDroneId.setter
    def selectedDroneId(self, value):
        if self._selected_drone_id != value:
            self._selected_drone_id = str(value or "")
            self.statusChanged.emit()

    @Property(str, notify=statusChanged)
    def currentSource(self):
        return self._current_source

    @Property(bool, notify=statusChanged)
    def streamActive(self):
        return self._stream_active

    @Property(bool, notify=statusChanged)
    def recordingActive(self):
        return self._recording_active

    @Property(int, notify=statusChanged)
    def recordingDuration(self):
        return self._recording_duration

    @Property(int, notify=statusChanged)
    def frameAge(self):
        return self._frame_age

    @Property(int, notify=statusChanged)
    def droppedFrames(self):
        return self._dropped_frames

    @Property(str, notify=statusChanged)
    def currentProfile(self):
        return str(self._profile.get("name", "RGB Camera"))

    @Property(str, notify=statusChanged)
    def lastError(self):
        return self._last_error

    @Property(str, notify=statusChanged)
    def lastSnapshotPath(self):
        return self._last_snapshot_path

    @Slot(str)
    def setSelectedDrone(self, drone_id: str) -> None:
        self.selectedDroneId = drone_id

    @Slot(str, result=bool)
    def cameraStartStream(self, source: str) -> bool:
        source = str(source or "").strip()
        if not source or source == "None":
            return self._fail("Camera source is required")
        if not self._validate_source(source):
            return False

        backend = self._selected_backend()
        delegated = False
        if backend is not None and hasattr(backend, "camera_start_stream"):
            delegated = bool(backend.camera_start_stream(source))

        # Delegation failed for a real source — do NOT mark the stream as active.
        if backend is not None and not delegated and source != "Test Source":
            return self._fail("Selected drone has no available camera stream")

        # For "Test Source" with no backend, delegation is skipped intentionally.
        # Only mark active after a successful delegation or when using Test Source.
        self._current_source = source
        self._stream_active = True
        self._frame_age = 0
        self._last_error = ""
        self.streamStarted.emit(source)
        self.statusChanged.emit()
        self.logMessage.emit("INFO", f"[CAMERA] Stream started: {source}")
        return True

    @Slot(result=bool)
    def cameraStopStream(self) -> bool:
        backend = self._selected_backend()
        if backend is not None and hasattr(backend, "camera_stop_stream"):
            backend.camera_stop_stream()

        self._stream_active = False
        self._frame_age = 0
        self.streamStopped.emit()
        self.statusChanged.emit()
        self.logMessage.emit("INFO", "[CAMERA] Stream stopped")
        return True

    @Slot(result=bool)
    def cameraSnapshot(self) -> bool:
        if not self._stream_active:
            return self._fail("Cannot capture snapshot while stream is stopped")

        backend = self._selected_backend()
        path = ""
        if backend is not None and hasattr(backend, "camera_snapshot"):
            result = backend.camera_snapshot()
            if isinstance(result, str):
                path = result
            elif not result:
                return self._fail("Selected drone failed to capture snapshot")

        if not path:
            path = str(self._default_media_dir() / f"snapshot-{self._stamp()}.jpg")

        self._last_snapshot_path = path
        self.snapshotCaptured.emit(path)
        self.statusChanged.emit()
        self.logMessage.emit("INFO", f"[CAMERA] Snapshot captured: {path}")
        return True

    @Slot(str, result=bool)
    def cameraStartRecording(self, path: str) -> bool:
        if not self._stream_active:
            return self._fail("Cannot record while stream is stopped")

        recording_path = self._normalize_recording_path(path)
        if not recording_path:
            return False
        if not self._has_recording_space(recording_path):
            return self._fail("Recording blocked: less than 1 GB free storage")

        backend = self._selected_backend()
        if backend is not None and hasattr(backend, "camera_start_recording"):
            if not backend.camera_start_recording(str(recording_path)):
                return self._fail("Selected drone failed to start recording")

        self._recording_active = True
        self._recording_started_at = time.monotonic()
        self._recording_duration = 0
        self._recording_path = str(recording_path)
        self._last_error = ""
        self._recording_timer.start()
        self.recordingStarted.emit(self._recording_path)
        self.statusChanged.emit()
        self.logMessage.emit("INFO", f"[CAMERA] Recording started: {self._recording_path}")
        return True

    @Slot(result=bool)
    def cameraStopRecording(self) -> bool:
        backend = self._selected_backend()
        if backend is not None and hasattr(backend, "camera_stop_recording"):
            backend.camera_stop_recording()

        duration = self._recording_duration
        if self._recording_active:
            duration = max(duration, int(time.monotonic() - self._recording_started_at))

        self._recording_active = False
        self._recording_timer.stop()
        self._recording_duration = duration
        self.recordingStopped.emit(duration)
        self.statusChanged.emit()
        self.logMessage.emit("INFO", f"[CAMERA] Recording stopped after {duration}s")
        return True

    @Slot("QVariant", result=bool)
    def setCameraProfile(self, profile) -> bool:
        if not isinstance(profile, dict):
            return self._fail("Camera profile must be an object")

        next_profile = dict(self._profile)
        next_profile.update(profile)

        try:
            fps = int(next_profile.get("fps", 30))
            hfov = float(next_profile.get("hfov", 90.0))
            vfov = float(next_profile.get("vfov", 60.0))
        except (TypeError, ValueError):
            return self._fail("Camera profile contains invalid numeric values")

        if fps < 1 or fps > 60:
            return self._fail("Camera FPS must be between 1 and 60")
        if hfov < 10.0 or hfov > 180.0 or vfov < 10.0 or vfov > 180.0:
            return self._fail("Camera FOV must be between 10 and 180 degrees")

        next_profile["fps"] = fps
        next_profile["hfov"] = hfov
        next_profile["vfov"] = vfov
        self._profile = next_profile
        self._last_error = ""
        self.statusChanged.emit()
        return True

    @Slot(result="QVariant")
    def getCameraStatus(self):
        backend_status = {}
        backend = self._selected_backend()
        if backend is not None and hasattr(backend, "get_camera_status"):
            status = backend.get_camera_status()
            if isinstance(status, dict):
                backend_status = status

        status = {
            "source": self._current_source,
            "streamActive": self._stream_active,
            "recordingActive": self._recording_active,
            "recordingDurationSec": self._recording_duration,
            "frameAgeMs": self._frame_age,
            "droppedFrames": self._dropped_frames,
            "profile": self._profile.get("name", "RGB Camera"),
            "resolution": self._profile.get("resolution", "1920x1080"),
            "fps": self._profile.get("fps", 30),
            "hfov": self._profile.get("hfov", 90.0),
            "vfov": self._profile.get("vfov", 60.0),
            "thermalEnabled": self._current_source == "Thermal Camera",
            "hotspotDetection": self._hotspot_detection,
            "temperatureMinC": self._temp_min_c,
            "temperatureMaxC": self._temp_max_c,
            "colorPalette": self._color_palette,
            "lastError": self._last_error,
            "selectedDroneId": self._selected_drone_id,
            "lastSnapshotPath": self._last_snapshot_path,
        }
        status.update(backend_status)
        return status

    @Slot(float, float, result=bool)
    def setTempRange(self, min_c: float, max_c: float) -> bool:
        if min_c >= max_c:
            return self._fail("Temperature minimum must be below maximum")
        if min_c < -40.0 or max_c > 200.0:
            return self._fail("Temperature range must stay between -40 C and 200 C")
        self._temp_min_c = float(min_c)
        self._temp_max_c = float(max_c)
        self._last_error = ""
        self.statusChanged.emit()
        return True

    @Slot(str, result=bool)
    def setColorPalette(self, palette: str) -> bool:
        valid = {"Ironbow", "Rainbow", "Grayscale", "Hot", "Cold", "Medical"}
        if palette not in valid:
            return self._fail(f"Unsupported thermal palette: {palette}")
        self._color_palette = palette
        self._last_error = ""
        self.statusChanged.emit()
        return True

    @Slot(bool, result=bool)
    def setHotspotDetection(self, enabled: bool) -> bool:
        self._hotspot_detection = bool(enabled)
        self._last_error = ""
        self.statusChanged.emit()
        return True

    def _selected_backend(self):
        if self._swarm_context is None or not hasattr(self._swarm_context, "backend"):
            return None

        backend = self._swarm_context.backend
        if self._selected_drone_id:
            return backend.get_backend(self._selected_drone_id)

        for candidate in backend.all_backends().values():
            if getattr(candidate, "drone_type", "") == "observation":
                return candidate
        return None

    def _validate_source(self, source: str) -> bool:
        if source in self._available_sources:
            return True
        lowered = source.lower()
        if lowered.startswith(("rtsp://", "rtsps://")):
            return True
        # Device paths (e.g. /dev/video0) — restrict to /dev/ only to prevent
        # arbitrary filesystem access via path traversal.
        if lowered.startswith("/dev/") and " " not in source:
            return True
        return self._fail(f"Unsupported camera source: {source}")

    def _normalize_recording_path(self, path: str) -> Optional[Path]:
        raw = str(path or "").strip()
        if raw.startswith("file:///"):
            raw = raw[8:]
        elif raw.startswith("file://"):
            raw = raw[7:]

        target = Path(raw) if raw else self._default_media_dir() / f"recording-{self._stamp()}.mp4"
        if target.exists() and target.is_dir():
            target = target / f"recording-{self._stamp()}.mp4"
        if not target.suffix:
            target = target.with_suffix(".mp4")

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._fail(f"Recording path is not writable: {exc}")
            return None
        return target

    def _has_recording_space(self, path: Path) -> bool:
        try:
            usage = shutil.disk_usage(path.parent)
        except OSError:
            return False
        return usage.free >= 1_000_000_000

    def _default_media_dir(self) -> Path:
        return Path(os.environ.get("SKYMESHX_MEDIA_DIR", "logs")) / "camera"

    def _update_recording_duration(self) -> None:
        if not self._recording_active:
            return
        self._recording_duration = int(time.monotonic() - self._recording_started_at)
        self.statusChanged.emit()

    def _fail(self, message: str) -> bool:
        self._last_error = message
        self.errorOccurred.emit(message)
        self.statusChanged.emit()
        self.logMessage.emit("ERROR", f"[CAMERA] {message}")
        return False

    def _stamp(self) -> str:
        return time.strftime("%Y%m%d-%H%M%S")
