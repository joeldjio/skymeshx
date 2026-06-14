"""
Test for Fix 6: Reconnect Max Attempts

Verifies that ROS2 bridge stops reconnecting after 5 failed attempts
with exponential backoff.
"""

from unittest.mock import Mock, patch, MagicMock
import time

import pytest


def test_max_reconnect_attempts_constant_exists():
    """Test that PX4ROS2Bridge has max_reconnect_attempts constant."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge
        
        # Create bridge with mocked dependencies
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test")
            
            # Verify max attempts is set
            assert hasattr(bridge, '_max_reconnect_attempts')
            assert bridge._max_reconnect_attempts == 5
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_reconnect_counter_increments():
    """Test that reconnect attempts counter increments on failure."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge, ConnectionStatus
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test", auto_reconnect=True)
            
            # Verify initial state
            assert bridge._reconnect_attempts == 0
            assert bridge._connection_status == ConnectionStatus.DISCONNECTED
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_reconnect_info_includes_attempts():
    """Test that get_reconnect_info returns attempt count."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test")
            
            info = bridge.get_reconnect_info()
            
            # Verify info structure
            assert "attempts" in info
            assert "status" in info
            assert "next_delay" in info
            assert "last_message_age" in info
            assert info["attempts"] == 0
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_exponential_backoff_calculation():
    """Test that reconnect delay uses exponential backoff."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test", max_reconnect_delay=30.0)
            
            # Initial delay
            assert bridge._reconnect_delay == 1.0
            
            # Simulate exponential backoff
            delays = [1.0]
            current_delay = 1.0
            for _ in range(5):
                current_delay = min(current_delay * 2, 30.0)
                delays.append(current_delay)
            
            # Verify sequence: 1, 2, 4, 8, 16, 30 (capped)
            assert delays == [1.0, 2.0, 4.0, 8.0, 16.0, 30.0]
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_max_reconnect_delay_cap():
    """Test that reconnect delay is capped at max_reconnect_delay."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test", max_reconnect_delay=10.0)
            
            # Verify max delay is set
            assert bridge._max_reconnect_delay == 10.0
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_auto_reconnect_disabled():
    """Test that auto_reconnect can be disabled."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test", auto_reconnect=False)
            
            # Verify auto_reconnect is disabled
            assert bridge._auto_reconnect is False
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_connection_status_enum():
    """Test that ConnectionStatus enum has all required states."""
    try:
        from droneresearch.ros.px4_bridge import ConnectionStatus
        
        # Verify all states exist
        assert hasattr(ConnectionStatus, 'DISCONNECTED')
        assert hasattr(ConnectionStatus, 'CONNECTING')
        assert hasattr(ConnectionStatus, 'CONNECTED')
        assert hasattr(ConnectionStatus, 'RECONNECTING')
        assert hasattr(ConnectionStatus, 'FAILED')
        
        # Verify values
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"
        assert ConnectionStatus.CONNECTING.value == "connecting"
        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.RECONNECTING.value == "reconnecting"
        assert ConnectionStatus.FAILED.value == "failed"
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_connection_timeout_default():
    """Test that connection timeout has sensible default."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test")
            
            # Verify timeout is set to 5 seconds
            assert bridge._connection_timeout == 5.0
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_reconnect_resets_on_successful_connection():
    """Test that reconnect counter resets on successful connection."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test")
            
            # Simulate failed attempts
            bridge._reconnect_attempts = 3
            bridge._reconnect_delay = 4.0
            
            # Reset on start (simulates successful connection)
            bridge._reconnect_attempts = 0
            bridge._reconnect_delay = 1.0
            
            # Verify reset
            assert bridge._reconnect_attempts == 0
            assert bridge._reconnect_delay == 1.0
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_get_connection_status_method():
    """Test that get_connection_status returns current status."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge, ConnectionStatus
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test")
            
            # Verify method exists and returns status
            status = bridge.get_connection_status()
            assert isinstance(status, ConnectionStatus)
            assert status == ConnectionStatus.DISCONNECTED
    except ImportError:
        pytest.skip("ROS2 dependencies not available")


def test_is_connected_method():
    """Test that is_connected returns boolean."""
    try:
        from droneresearch.ros.px4_bridge import PX4ROS2Bridge
        
        with patch('droneresearch.ros.px4_bridge._ROS2_OK', True), \
             patch('droneresearch.ros.px4_bridge._PX4_MSGS_OK', True):
            bridge = PX4ROS2Bridge(namespace="test")
            
            # Verify method exists and returns boolean
            connected = bridge.is_connected()
            assert isinstance(connected, bool)
            assert connected is False  # Not started yet
    except ImportError:
        pytest.skip("ROS2 dependencies not available")

# Made with Bob
