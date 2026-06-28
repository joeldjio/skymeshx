from __future__ import annotations

from unittest.mock import patch

from tools.ui.context.ros2_context import ROS2Context


class FakeProcess:
    pid = 4321

    def poll(self):
        return None


class FakePX4GazeboCluster:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._running = False
        self._processes = [("px4_sitl_px4_1", FakeProcess())]
        FakePX4GazeboCluster.instances.append(self)

    def start(self):
        self._running = True
        return True

    def stop(self):
        self._running = False

    def is_running(self):
        return self._running


def _sync_context(qapp):
    ctx = ROS2Context()
    ctx._run_async = lambda target: target()
    return ctx


def test_list_launch_profiles_contains_px4_camera_models(qapp):
    ctx = ROS2Context()

    profiles = ctx.listLaunchProfiles()
    ids = {profile["id"] for profile in profiles}

    assert "gz_x500" in ids
    assert "gz_x500_gimbal" in ids
    assert "gz_x500_mono_cam" in ids
    assert "sih_quadx" in ids


def test_start_sitl_profile_normalizes_gz_model_for_cluster(qapp):
    FakePX4GazeboCluster.instances.clear()
    ctx = _sync_context(qapp)

    with patch("skymeshx.simulation.PX4GazeboCluster", FakePX4GazeboCluster):
        assert ctx.startSitl(
            {
                "model": "gz_x500_gimbal",
                "world": "default",
                "namespace": "px4_1",
                "videoPort": 5600,
            }
        )

    cluster = FakePX4GazeboCluster.instances[0]
    assert cluster.kwargs["num_drones"] == 1
    assert cluster.kwargs["model"] == "x500_gimbal"
    assert cluster.kwargs["world"] == "default"
    assert cluster.kwargs["namespace_prefix"] == "px4"

    status = ctx.getSitlStatus()
    assert status["running"] is True
    assert status["model"] == "gz_x500_gimbal"
    assert status["namespace"] == "px4_1"
    assert status["pid"] == 4321
    assert status["gazebo_running"] is True


def test_start_multi_sitl_builds_px4_namespace_and_ports(qapp):
    FakePX4GazeboCluster.instances.clear()
    ctx = _sync_context(qapp)

    with patch("skymeshx.simulation.PX4GazeboCluster", FakePX4GazeboCluster):
        assert ctx.startMultiSitl(3, 5762)

    cluster = FakePX4GazeboCluster.instances[0]
    status = ctx.getSitlStatus()

    assert cluster.kwargs["num_drones"] == 3
    assert cluster.kwargs["namespace_prefix"] == "px4"
    assert status["vehicle_count"] == 3
    assert [v["namespace"] for v in status["vehicles"]] == ["px4_1", "px4_2", "px4_3"]
    assert [v["mavlinkPort"] for v in status["vehicles"]] == [5762, 5763, 5764]
    assert [v["videoPort"] for v in status["vehicles"]] == [5600, 5601, 5602]


def test_stop_sitl_updates_status(qapp):
    FakePX4GazeboCluster.instances.clear()
    ctx = _sync_context(qapp)

    with patch("skymeshx.simulation.PX4GazeboCluster", FakePX4GazeboCluster):
        assert ctx.startSitl({"model": "gz_x500", "namespace": "px4_1"})
        assert ctx.stopSitl()

    assert ctx.getSitlStatus()["running"] is False
    assert ctx.getSitlStatus()["status"] == "stopped"


def test_discover_topics_and_topic_health_are_hardware_free(qapp):
    ctx = ROS2Context()

    topics = ctx.discoverTopics("px4_1")
    assert "/px4_1/fmu/out/vehicle_odometry" in topics
    assert "/px4_1/fmu/out/vehicle_status" in topics

    assert ctx.subscribeToTopic("/px4_1/fmu/out/vehicle_odometry", "drone1") is True
    ctx._record_topic_message("/px4_1/fmu/out/vehicle_odometry", "{}", "sensor_data")

    health = ctx.getTopicHealth("px4_1")
    assert health["/px4_1/fmu/out/vehicle_odometry"]["seen"] is True
    assert health["/px4_1/fmu/out/vehicle_odometry"]["messageCount"] == 1


def test_world_profile_warnings_are_backend_visible(qapp):
    ctx = ROS2Context()

    ridge_warnings = ctx.getWorldProfileWarnings("gz_x500", "ridge_terrain")
    assert any("ridge_terrain" in warning for warning in ridge_warnings)
    assert ctx.getWorldProfileWarnings("gz_x500_lidar_down", "ridge_terrain") == []

    aruco_warnings = ctx.getWorldProfileWarnings("gz_x500", "aruco_precision_landing")
    assert any("aruco_precision_landing" in warning for warning in aruco_warnings)
    assert ctx.getWorldProfileWarnings("gz_x500_mono_cam", "aruco_precision_landing") == []

    moving_warnings = ctx.getWorldProfileWarnings("gz_standard_vtol", "moving_platform")
    assert any("PX4_GZ_MODEL_POSE" in warning for warning in moving_warnings)


def test_ros2_mission_trace_events_and_wp_tracking(qapp):
    class FakeTrace:
        def __init__(self):
            self.mission_events = []
            self.wp_events = []

        def log_mission_event(self, event_type, data):
            self.mission_events.append((event_type, data))

        def log_wp_tracking(
            self,
            drone_id,
            seq,
            drone_lat,
            drone_lon,
            target_lat,
            target_lon,
            distance_m,
            frame,
            acceptance_radius_m=None,
        ):
            self.wp_events.append(
                {
                    "droneId": drone_id,
                    "seq": seq,
                    "distanceToWpM": distance_m,
                    "frame": frame,
                    "acceptanceRadiusM": acceptance_radius_m,
                }
            )

    class FakeBridge:
        def __init__(self):
            self.telemetry = {"lat": 47.397742, "lon": 8.545594}
            self.status_callback = None
            self.uploaded = []
            self.started = False
            self.paused = False
            self.cleared = False

        def upload_mission(self, waypoints, timeout=10.0):
            self.uploaded = [dict(wp) for wp in waypoints]
            return True

        def on_mission_status(self, callback):
            self.status_callback = callback

        def get_mission_waypoints(self):
            return list(self.uploaded)

        def start_mission(self):
            self.started = True

        def pause_mission(self):
            self.paused = True

        def clear_mission(self):
            self.cleared = True
            return True

    ctx = ROS2Context()
    bridge = FakeBridge()
    ctx._bridges["drone1"] = bridge
    trace = FakeTrace()
    waypoints = [{"lat": 47.397842, "lon": 8.545694, "alt": 10.0, "accept_radius": 2.5}]

    with patch("skymeshx.core.trace_logger.TraceLogger.get", return_value=trace):
        assert ctx.uploadMission("drone1", waypoints) is True
        assert bridge.status_callback is not None
        bridge.status_callback({"active": True, "current_seq": 0, "total_count": 1})
        ctx.startMission("drone1")
        ctx.pauseMission("drone1")
        ctx.abortMission("drone1")
        assert ctx.clearMission("drone1") is True

    event_types = [event_type for event_type, _data in trace.mission_events]
    assert "mission_upload" in event_types
    assert "mission_status" in event_types
    assert "mission_start" in event_types
    assert "mission_pause" in event_types
    assert "mission_abort" in event_types

    assert trace.wp_events
    assert trace.wp_events[0]["droneId"] == "drone1"
    assert trace.wp_events[0]["distanceToWpM"] > 0.0
    assert trace.wp_events[0]["acceptanceRadiusM"] == 2.5
