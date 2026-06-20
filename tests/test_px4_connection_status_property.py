"""Test PX4 connection status property."""

import pytest
from skymeshx.ros.px4_bridge import ConnectionStatus

# Skip if ROS2 not available
pytest.importorskip("rclpy")
pytest.importorskip("px4_msgs")


def test_connection_status_property():
    """Test that connection_status property returns current status."""
    from skymeshx.ros.px4_bridge import PX4ROS2Bridge
    
    bridge = PX4ROS2Bridge(namespace="test")
    
    # Should start as DISCONNECTED
    assert bridge.connection_status == ConnectionStatus.DISCONNECTED
    assert isinstance(bridge.connection_status, ConnectionStatus)


def test_connection_status_property_vs_method():
    """Test that property and method return same value."""
    from skymeshx.ros.px4_bridge import PX4ROS2Bridge
    
    bridge = PX4ROS2Bridge(namespace="test")
    
    # Property and method should return same value
    assert bridge.connection_status == bridge.get_connection_status()


def test_connection_status_enum_values():
    """Test that ConnectionStatus enum has expected values."""
    assert ConnectionStatus.DISCONNECTED.value == "disconnected"
    assert ConnectionStatus.CONNECTING.value == "connecting"
    assert ConnectionStatus.CONNECTED.value == "connected"
    assert ConnectionStatus.RECONNECTING.value == "reconnecting"
    assert ConnectionStatus.FAILED.value == "failed"


def test_is_connected_uses_status():
    """Test that is_connected() checks connection_status."""
    from skymeshx.ros.px4_bridge import PX4ROS2Bridge
    
    bridge = PX4ROS2Bridge(namespace="test")
    
    # Should not be connected initially
    assert not bridge.is_connected()
    assert bridge.connection_status != ConnectionStatus.CONNECTED
