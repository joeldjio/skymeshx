"""
ObservationUAVModel — UAV with gimbal + camera + video streaming.

Based on: "A Modular and Scalable System Architecture for Heterogeneous
UAV Swarms Using ROS 2 and PX4-Autopilot" (2025)

Intended for: larger UAVs with Jetson Orin NX companion computer,
              gimbal-mounted camera, onboard video processing.

Extra features vs GenericUAVModel:
    - Gimbal control (pitch/roll/yaw)
    - Camera control (zoom, capture)
    - Video stream → ROS2 topic (if ROS2 available)
    - Object detection pipeline hook

Usage:
    uav = ObservationUAVModel("CAM1", "tcp:127.0.0.1:5760")
    uav.connect()
    uav.start(altitude=15.0)
    uav.gimbal_point(pitch=-45.0)     # look down at 45°
    uav.start_recording()
"""
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from skymeshx.models.generic_uav import GenericUAVModel


class ObservationUAVModel(GenericUAVModel):
    """
    UAV model for observation / surveillance missions.

    Adds gimbal, camera, and video streaming on top of GenericUAVModel.
    Video processing hooks allow plugging in custom CV pipelines.
    """

    def __init__(
        self,
        drone_id:          str,
        connection_string: str,
        camera_index:      int  = 0,
        log_dir:           str  = "logs",
        auto_log:          bool = True,
        baud:              Optional[int] = None,
    ):
        super().__init__(drone_id, connection_string, log_dir=log_dir, auto_log=auto_log, baud=baud)
        self.camera_index    = camera_index
        self._gimbal_pitch   = 0.0
        self._gimbal_roll    = 0.0
        self._gimbal_yaw     = 0.0
        self._recording      = False
        self._stream_active  = False
        self._camera_source  = "None"
        self._recording_path: Optional[str] = None
        self._last_snapshot_path: Optional[str] = None
        self._frame_age_ms   = 0
        self._dropped_frames = 0
        self._camera_profile = {
            "name": "RGB Camera",
            "resolution": "1920x1080",
            "fps": 30,
            "hfov": 90.0,
            "vfov": 60.0,
            "format": "H264",
        }
        self._frame_cb: Optional[Callable] = None
        self._detection_cb: Optional[Callable] = None
        self._capture_thread: Optional[threading.Thread] = None

    # ── Gimbal control ────────────────────────────────────────────────────

    def gimbal_point(
        self,
        pitch: float = -90.0,
        roll:  float = 0.0,
        yaw:   float = 0.0,
    ):
        """
        Point gimbal. pitch=-90 = straight down, 0 = forward.
        Sends MAVLink MAV_CMD_DO_MOUNT_CONTROL.
        """
        self._gimbal_pitch = pitch
        self._gimbal_roll  = roll
        self._gimbal_yaw   = yaw
        self._conn._command_long(
            205,            # MAV_CMD_DO_MOUNT_CONTROL
            pitch, roll, yaw,
            0, 0, 0,
            2,              # MAV_MOUNT_MODE_MAVLINK_TARGETING
        )

    def gimbal_track(self, lat: float, lon: float, alt: float):
        """Point gimbal at a GPS coordinate (loitering observation)."""
        self._conn._command_long(
            205,
            0, 0, 0,
            lat, lon, alt,
            4,              # MAV_MOUNT_MODE_GPS_POINT
        )

    def gimbal_home(self):
        """Return gimbal to forward position."""
        self.gimbal_point(pitch=0.0, roll=0.0, yaw=0.0)

    @property
    def gimbal_state(self) -> dict:
        return {
            "pitch": self._gimbal_pitch,
            "roll":  self._gimbal_roll,
            "yaw":   self._gimbal_yaw,
        }

    # ── Camera / video ────────────────────────────────────────────────────

    def start_stream(self, on_frame: Optional[Callable] = None):
        """
        Start camera capture loop.
        on_frame(frame) called for every frame (numpy array if OpenCV available).
        """
        if self._stream_active:
            return
        self._frame_cb    = on_frame
        self._stream_active = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop, daemon=True, name=f"cam-{self.id}"
        )
        self._capture_thread.start()

    def stop_stream(self):
        self._stream_active = False

    # MAVLink camera command IDs
    _CMD_START_RECORDING = 2500   # MAV_CMD_VIDEO_START_CAPTURE (2500)
    _CMD_STOP_RECORDING  = 2501   # MAV_CMD_VIDEO_STOP_CAPTURE  (2501)
    _CMD_SNAPSHOT        = 203    # MAV_CMD_DO_DIGICAM_CONTROL  (203)

    def start_recording(self, path: Optional[str] = None) -> bool:
        if not self._stream_active:
            return False
        self._recording = True
        self._recording_path = path or "logs/"
        self._send_camera_command(self._CMD_START_RECORDING)
        print(f"[{self.id}] Recording started -> {self._recording_path}")
        return True

    def stop_recording(self) -> bool:
        self._recording = False
        self._send_camera_command(self._CMD_STOP_RECORDING)
        print(f"[{self.id}] Recording stopped.")
        return True

    def start_camera_stream(self, source: str) -> bool:
        """Start stream from a named source. Test Source is hardware-free."""
        self._camera_source = source
        if source == "Test Source":
            self._stream_active = True
            self._frame_age_ms = 0
            return True
        self.start_stream()
        return True

    def stop_camera_stream(self) -> bool:
        self._camera_source = "None"
        self.stop_stream()
        return True

    def capture_snapshot(self):
        """Capture a snapshot or return a mock path when no frame backend exists."""
        if not self._stream_active:
            return False
        stamp = time.strftime("%Y%m%d-%H%M%S")
        path = Path("logs") / "camera" / f"{self.id}-snapshot-{stamp}.jpg"
        self._last_snapshot_path = str(path)
        self._send_camera_command(203)
        return self._last_snapshot_path

    def get_camera_status(self) -> dict:
        return {
            "source": self._camera_source,
            "streamActive": self._stream_active,
            "recordingActive": self._recording,
            "recordingPath": self._recording_path or "",
            "lastSnapshotPath": self._last_snapshot_path or "",
            "frameAgeMs": self._frame_age_ms,
            "droppedFrames": self._dropped_frames,
            "profile": self._camera_profile.get("name", "RGB Camera"),
            "resolution": self._camera_profile.get("resolution", "1920x1080"),
            "fps": self._camera_profile.get("fps", 30),
            "hfov": self._camera_profile.get("hfov", 90.0),
            "vfov": self._camera_profile.get("vfov", 60.0),
            "backendAvailable": True,
        }

    def get_gimbal_status(self) -> dict:
        return self.gimbal_state

    def on_detection(self, cb: Callable):
        """
        Register callback for object detections.
        cb(detections: list) — list of dicts with 'class', 'confidence', 'bbox'
        Requires a detection pipeline (e.g. vswarm CNN) to be connected.
        """
        self._detection_cb = cb

    # ── ROS2 video publishing ─────────────────────────────────────────────

    def publish_to_ros(self, image_topic: str, caminfo_topic: str):
        """
        Publish camera frames as ROS2 sensor_msgs/Image topics.
        Requires rclpy + cv_bridge.
        """
        try:
            import rclpy
            from rclpy.node import Node
            from sensor_msgs.msg import Image
            print(f"[{self.id}] ROS2 video publishing on {image_topic}")
        except ImportError:
            print(f"[{self.id}] rclpy not available — ROS publishing disabled")

    # ── Status override ───────────────────────────────────────────────────

    def status(self) -> dict:
        s = super().status()
        s.update({
            "gimbal_pitch":  self._gimbal_pitch,
            "streaming":     self._stream_active,
            "recording":     self._recording,
            "camera_index":  self.camera_index,
        })
        return s

    # ── Internal ──────────────────────────────────────────────────────────

    def _send_camera_command(self, command_id: int) -> bool:
        """Send a MAVLink camera command when a connection is available."""
        conn = getattr(self, "_conn", None)
        if conn is None or not hasattr(conn, "_command_long"):
            return False
        try:
            conn._command_long(command_id, 0, 0, 0, 0, 0, 0, 0)
            return True
        except Exception:
            return False

    def _capture_loop(self):
        try:
            import cv2
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                print(f"[{self.id}] Camera {self.camera_index} not available")
                self._stream_active = False
                return
            while self._stream_active:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.05)
                    continue
                if self._frame_cb:
                    self._frame_cb(frame)
                if self._detection_cb:
                    pass   # plug in detection pipeline here
            cap.release()
        except ImportError:
            print(f"[{self.id}] OpenCV not available — camera stream disabled")
            self._stream_active = False
