from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.sitl


DEFAULT_MAVLINK_ENDPOINT = "tcp:127.0.0.1:5762"
DEFAULT_ROS2_ODOMETRY_TOPIC = "/px4_1/fmu/out/vehicle_odometry"

SITL_SCENARIOS = (
    "sih_single_mission_upload",
    "gz_x500_single_coverage",
    "gz_x500_gimbal_solar",
    "gz_x500_mono_cam_video_map",
    "gz_x500_multi_swarm_2uav",
    "gz_x500_seeding_large_preview",
    "gz_world_ridge_terrain_lidar",
    "gz_world_walls_avoidance",
)


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _timeout() -> float:
    raw = os.environ.get("SITL_TIMEOUT_SEC", "10")
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 10.0


def _require_sitl(*, commands: bool = False, mission_upload: bool = False, ros2: bool = False) -> None:
    if not _flag("SITL_AVAILABLE"):
        pytest.skip("SITL smoke tests are opt-in: set SITL_AVAILABLE=1")
    if not sys.platform.startswith("linux"):
        pytest.skip("SITL smoke tests are Linux-only")
    if commands and not _flag("SITL_ALLOW_COMMANDS"):
        pytest.skip("Commanding tests require SITL_ALLOW_COMMANDS=1")
    if mission_upload and not _flag("SITL_ALLOW_MISSION_UPLOAD"):
        pytest.skip("Mission upload smoke requires SITL_ALLOW_MISSION_UPLOAD=1")
    if ros2 and not _flag("SITL_REQUIRE_ROS2"):
        pytest.skip("ROS2 smoke requires SITL_REQUIRE_ROS2=1")


def _endpoint() -> str:
    return os.environ.get("SITL_MAVLINK_ENDPOINT", DEFAULT_MAVLINK_ENDPOINT)


def _connect_mavlink() -> Any:
    mavutil = pytest.importorskip("pymavlink.mavutil")
    conn = mavutil.mavlink_connection(_endpoint(), autoreconnect=False)
    heartbeat = conn.wait_heartbeat(timeout=_timeout())
    if heartbeat is None:
        pytest.fail(f"No MAVLink heartbeat on {_endpoint()}")
    return conn


def _close_mavlink(conn: Any) -> None:
    close = getattr(conn, "close", None)
    if callable(close):
        close()


def _wait_armed(conn: Any, expected: bool) -> bool:
    mavutil = pytest.importorskip("pymavlink.mavutil")
    armed_flag = int(mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    deadline = time.monotonic() + _timeout()
    while time.monotonic() < deadline:
        msg = conn.recv_match(type="HEARTBEAT", blocking=True, timeout=1.0)
        if msg is None:
            continue
        armed = bool(int(getattr(msg, "base_mode", 0)) & armed_flag)
        if armed == expected:
            return True
    return False


def _command_arm(conn: Any, arm: bool) -> None:
    mavutil = pytest.importorskip("pymavlink.mavutil")
    conn.mav.command_long_send(
        conn.target_system,
        conn.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1.0 if arm else 0.0,
        0,
        0,
        0,
        0,
        0,
        0,
    )


def _mission_count_send(conn: Any, count: int) -> None:
    mavutil = pytest.importorskip("pymavlink.mavutil")
    try:
        conn.mav.mission_count_send(
            conn.target_system,
            conn.target_component,
            count,
            mavutil.mavlink.MAV_MISSION_TYPE_MISSION,
        )
    except TypeError:
        conn.mav.mission_count_send(conn.target_system, conn.target_component, count)


def _mission_item_int_send(conn: Any, seq: int, lat: float, lon: float, alt_m: float) -> None:
    mavutil = pytest.importorskip("pymavlink.mavutil")
    try:
        conn.mav.mission_item_int_send(
            conn.target_system,
            conn.target_component,
            seq,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            1 if seq == 0 else 0,
            1,
            0,
            0,
            0,
            0,
            int(lat * 1e7),
            int(lon * 1e7),
            alt_m,
            mavutil.mavlink.MAV_MISSION_TYPE_MISSION,
        )
    except TypeError:
        conn.mav.mission_item_int_send(
            conn.target_system,
            conn.target_component,
            seq,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            1 if seq == 0 else 0,
            1,
            0,
            0,
            0,
            0,
            int(lat * 1e7),
            int(lon * 1e7),
            alt_m,
        )


def _mission_item_send(conn: Any, seq: int, lat: float, lon: float, alt_m: float) -> None:
    mavutil = pytest.importorskip("pymavlink.mavutil")
    try:
        conn.mav.mission_item_send(
            conn.target_system,
            conn.target_component,
            seq,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            1 if seq == 0 else 0,
            1,
            0,
            0,
            0,
            0,
            lat,
            lon,
            alt_m,
            mavutil.mavlink.MAV_MISSION_TYPE_MISSION,
        )
    except TypeError:
        conn.mav.mission_item_send(
            conn.target_system,
            conn.target_component,
            seq,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            1 if seq == 0 else 0,
            1,
            0,
            0,
            0,
            0,
            lat,
            lon,
            alt_m,
        )


def _current_global_position(conn: Any) -> tuple[float, float]:
    msg = conn.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=_timeout())
    if msg is None:
        pytest.skip("No GLOBAL_POSITION_INT received; cannot build safe local mission")
    return float(msg.lat) / 1e7, float(msg.lon) / 1e7


def test_sitl_mavlink_heartbeat_smoke() -> None:
    _require_sitl()
    conn = _connect_mavlink()
    try:
        assert conn.target_system > 0
        assert conn.target_component > 0
    finally:
        _close_mavlink(conn)


def test_sitl_arm_disarm_roundtrip() -> None:
    _require_sitl(commands=True)
    conn = _connect_mavlink()
    try:
        _command_arm(conn, True)
        assert _wait_armed(conn, True), "SITL did not report armed state"

        _command_arm(conn, False)
        assert _wait_armed(conn, False), "SITL did not report disarmed state"
    finally:
        _close_mavlink(conn)


def test_sitl_mission_upload_roundtrip_contract() -> None:
    _require_sitl(mission_upload=True)
    mavutil = pytest.importorskip("pymavlink.mavutil")
    conn = _connect_mavlink()
    try:
        lat, lon = _current_global_position(conn)
        mission = [
            (lat, lon, 10.0),
            (lat + 0.00005, lon, 10.0),
        ]

        conn.mav.mission_clear_all_send(conn.target_system, conn.target_component)
        _mission_count_send(conn, len(mission))

        sent = set()
        deadline = time.monotonic() + _timeout()
        while len(sent) < len(mission) and time.monotonic() < deadline:
            request = conn.recv_match(
                type=["MISSION_REQUEST_INT", "MISSION_REQUEST"],
                blocking=True,
                timeout=1.0,
            )
            if request is None:
                continue
            seq = int(request.seq)
            assert 0 <= seq < len(mission)
            if request.get_type() == "MISSION_REQUEST_INT":
                _mission_item_int_send(conn, seq, *mission[seq])
            else:
                _mission_item_send(conn, seq, *mission[seq])
            sent.add(seq)

        assert sent == {0, 1}
        ack = conn.recv_match(type="MISSION_ACK", blocking=True, timeout=_timeout())
        assert ack is not None
        assert int(ack.type) == int(mavutil.mavlink.MAV_MISSION_ACCEPTED)
    finally:
        _close_mavlink(conn)


def test_sitl_ros2_vehicle_odometry_topic_visible() -> None:
    _require_sitl(ros2=True)
    ros2 = shutil.which("ros2")
    if ros2 is None:
        pytest.skip("ros2 CLI not found in PATH")

    topic = os.environ.get("SITL_ROS2_ODOMETRY_TOPIC", DEFAULT_ROS2_ODOMETRY_TOPIC)
    result = subprocess.run(
        [ros2, "topic", "list"],
        check=False,
        capture_output=True,
        text=True,
        timeout=_timeout(),
    )

    assert result.returncode == 0, result.stderr
    assert topic in result.stdout.splitlines()


def test_sitl_trace_bundle_contract() -> None:
    _require_sitl()
    trace_dir = os.environ.get("SITL_TRACE_DIR")
    if not trace_dir:
        pytest.skip("Set SITL_TRACE_DIR to validate a trace bundle")

    root = Path(trace_dir)
    manifest_path = root / "manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("schemaVersion") == 1
    assert manifest.get("scenario") in SITL_SCENARIOS
    assert manifest.get("vehicles")
    assert (root / "mission_trace.jsonl").exists()

    health_path = root / "ros2_topic_health.json"
    if health_path.exists():
        health = json.loads(health_path.read_text(encoding="utf-8"))
        assert isinstance(health, dict)
