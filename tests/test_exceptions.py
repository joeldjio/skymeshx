"""
Tests for custom exception types.

Verifies that all exception classes are properly defined and can be raised/caught.
"""
import pytest

from skymeshx.exceptions import (
    BatteryLowError,
    CollisionRiskError,
    CommandRejectedError,
    CommandTimeoutError,
    ConnectionError,
    DependencyError,
    SkyMeshXError,
    GeofenceBreachError,
    HeartbeatTimeoutError,
    InvalidConnectionStringError,
    InvalidParameterError,
    MissionUploadError,
    ROS2NotAvailableError,
    StateTransitionError,
    TimeoutError,
    TopicTimeoutError,
)


def test_base_exception():
    """Base exception can be raised and caught."""
    with pytest.raises(SkyMeshXError):
        raise SkyMeshXError("test error")


def test_connection_error():
    """ConnectionError inherits from SkyMeshXError."""
    with pytest.raises(SkyMeshXError):
        raise ConnectionError("connection failed")
    
    with pytest.raises(ConnectionError):
        raise HeartbeatTimeoutError("no heartbeat")


def test_invalid_connection_string():
    """InvalidConnectionStringError provides clear message."""
    with pytest.raises(InvalidConnectionStringError) as exc_info:
        raise InvalidConnectionStringError("invalid format")
    assert "invalid format" in str(exc_info.value)


def test_command_rejected_error():
    """CommandRejectedError stores command and result."""
    err = CommandRejectedError("ARM", 2, "safety check failed")
    assert err.command == "ARM"
    assert err.result == 2
    assert "ARM" in str(err)
    assert "result=2" in str(err)


def test_command_timeout_error():
    """CommandTimeoutError stores command and timeout."""
    err = CommandTimeoutError("TAKEOFF", 30.0)
    assert err.command == "TAKEOFF"
    assert err.timeout == 30.0
    assert "TAKEOFF" in str(err)
    assert "30" in str(err)


def test_mission_upload_error():
    """MissionUploadError can be raised."""
    with pytest.raises(MissionUploadError):
        raise MissionUploadError("upload failed")


def test_state_transition_error():
    """StateTransitionError stores from/to states."""
    err = StateTransitionError("IDLE", "FLYING", "not armed")
    assert err.from_state == "IDLE"
    assert err.to_state == "FLYING"
    assert "IDLE" in str(err)
    assert "FLYING" in str(err)
    assert "not armed" in str(err)


def test_invalid_parameter_error():
    """InvalidParameterError stores parameter and value."""
    err = InvalidParameterError("altitude", -5, "must be positive")
    assert err.param == "altitude"
    assert err.value == -5
    assert "altitude" in str(err)
    assert "-5" in str(err)
    assert "positive" in str(err)


def test_ros2_not_available_error():
    """ROS2NotAvailableError can be raised."""
    with pytest.raises(ROS2NotAvailableError):
        raise ROS2NotAvailableError("rclpy not found")


def test_topic_timeout_error():
    """TopicTimeoutError stores topic and timeout."""
    err = TopicTimeoutError("/fmu/out/vehicle_status", 5.0)
    assert err.topic == "/fmu/out/vehicle_status"
    assert err.timeout == 5.0
    assert "/fmu/out/vehicle_status" in str(err)


def test_geofence_breach_error():
    """GeofenceBreachError stores drone ID, position, and limit."""
    err = GeofenceBreachError("D1", (100.0, 200.0, 50.0), "max altitude 30m")
    assert err.drone_id == "D1"
    assert err.position == (100.0, 200.0, 50.0)
    assert err.limit == "max altitude 30m"
    assert "D1" in str(err)


def test_collision_risk_error():
    """CollisionRiskError stores drone IDs and distances."""
    err = CollisionRiskError("D1", "D2", 1.5, 2.0)
    assert err.drone1 == "D1"
    assert err.drone2 == "D2"
    assert err.distance == 1.5
    assert err.min_distance == 2.0
    assert "D1" in str(err)
    assert "D2" in str(err)
    assert "1.5" in str(err)


def test_battery_low_error():
    """BatteryLowError stores drone ID, battery level, and threshold."""
    err = BatteryLowError("D1", 8.5, 10.0)
    assert err.drone_id == "D1"
    assert err.battery_pct == 8.5
    assert err.threshold == 10.0
    assert "D1" in str(err)
    assert "8.5" in str(err)


def test_dependency_error():
    """DependencyError stores package and install command."""
    err = DependencyError("pymavlink", "pip install pymavlink")
    assert err.package == "pymavlink"
    assert err.install_cmd == "pip install pymavlink"
    assert "pymavlink" in str(err)
    assert "pip install" in str(err)


def test_timeout_error():
    """TimeoutError stores operation and timeout."""
    err = TimeoutError("mission upload", 60.0)
    assert err.operation == "mission upload"
    assert err.timeout == 60.0
    assert "mission upload" in str(err)
    assert "60" in str(err)


def test_exception_hierarchy():
    """Verify exception inheritance hierarchy."""
    # All custom exceptions inherit from SkyMeshXError
    assert issubclass(ConnectionError, SkyMeshXError)
    assert issubclass(CommandRejectedError, SkyMeshXError)
    assert issubclass(MissionUploadError, SkyMeshXError)
    assert issubclass(StateTransitionError, SkyMeshXError)
    assert issubclass(ROS2NotAvailableError, SkyMeshXError)
    assert issubclass(GeofenceBreachError, SkyMeshXError)
    
    # Specific inheritance chains
    assert issubclass(HeartbeatTimeoutError, ConnectionError)
    assert issubclass(InvalidConnectionStringError, ConnectionError)
    assert issubclass(CommandRejectedError, CommandTimeoutError.__bases__[0])  # Both inherit from CommandError
    assert issubclass(GeofenceBreachError, CollisionRiskError.__bases__[0])  # Both inherit from SafetyViolationError


def test_catch_base_exception():
    """Can catch all custom exceptions with base class."""
    exceptions_to_test = [
        ConnectionError("test"),
        CommandRejectedError("ARM", 2),
        MissionUploadError("test"),
        StateTransitionError("A", "B"),
        ROS2NotAvailableError("test"),
        GeofenceBreachError("D1", (0, 0, 0), "test"),
        TimeoutError("test", 1.0),
    ]
    
    for exc in exceptions_to_test:
        with pytest.raises(SkyMeshXError):
            raise exc

# Made with Bob
