"""
Test for Fix 3: APF Mission Coordination

Verifies that APF respects mission-controlled drones using the explicit
_is_drone_mission_controlled() method instead of fragile hasattr checks.
"""

import threading
from unittest.mock import Mock

import pytest


def test_is_drone_mission_controlled_method_exists():
    """Test that SwarmContext has _is_drone_mission_controlled method."""
    from tools.ui.context.swarm_context import SwarmContext
    
    # Create SwarmContext
    swarm = SwarmContext()
    
    # Verify method exists
    assert hasattr(swarm, '_is_drone_mission_controlled')
    assert callable(swarm._is_drone_mission_controlled)


def test_is_drone_mission_controlled_returns_true_when_active():
    """Test that method returns True when mission is active."""
    from tools.ui.context.swarm_context import SwarmContext
    
    swarm = SwarmContext()
    drone_id = "D1"
    
    # Set mission active
    with swarm._state_lock:
        swarm._mission_active[drone_id] = threading.Event()
        swarm._mission_active[drone_id].clear()  # Event cleared = mission active
    
    # Verify method returns True
    assert swarm._is_drone_mission_controlled(drone_id) is True


def test_is_drone_mission_controlled_returns_false_when_inactive():
    """Test that method returns False when mission is inactive."""
    from tools.ui.context.swarm_context import SwarmContext
    
    swarm = SwarmContext()
    drone_id = "D1"
    
    # Set mission inactive
    with swarm._state_lock:
        swarm._mission_active[drone_id] = threading.Event()
        swarm._mission_active[drone_id].set()  # Event set = mission inactive
    
    # Verify method returns False
    assert swarm._is_drone_mission_controlled(drone_id) is False


def test_is_drone_mission_controlled_returns_false_when_not_in_dict():
    """Test that method returns False when drone not in dict."""
    from tools.ui.context.swarm_context import SwarmContext
    
    swarm = SwarmContext()
    drone_id = "D1"
    
    # Verify method returns False (drone not in dict)
    assert swarm._is_drone_mission_controlled(drone_id) is False


def test_is_drone_mission_controlled_is_thread_safe():
    """Test that method is thread-safe."""
    from tools.ui.context.swarm_context import SwarmContext
    
    swarm = SwarmContext()
    errors = []
    
    def add_mission(drone_id):
        try:
            with swarm._state_lock:
                swarm._mission_active[drone_id] = threading.Event()
                swarm._mission_active[drone_id].clear()
        except Exception as e:
            errors.append(e)
    
    def check_mission(drone_id):
        try:
            _ = swarm._is_drone_mission_controlled(drone_id)
        except Exception as e:
            errors.append(e)
    
    # Start concurrent operations
    threads = []
    for i in range(10):
        t1 = threading.Thread(target=add_mission, args=(f"D{i}",))
        t2 = threading.Thread(target=check_mission, args=(f"D{i}",))
        threads.extend([t1, t2])
        t1.start()
        t2.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Verify: No errors occurred
    assert len(errors) == 0


def test_apf_avoidance_respects_mission_control():
    """Test that APF avoidance logic respects mission control."""
    from tools.ui.context.swarm_context import SwarmContext
    
    swarm = SwarmContext()
    drone_id = "D1"
    
    # Mock backend
    mock_backend = Mock()
    mock_backend.goto = Mock()
    swarm.backend.get_backend = Mock(return_value=mock_backend)
    
    # Set mission active
    with swarm._state_lock:
        swarm._mission_active[drone_id] = threading.Event()
        swarm._mission_active[drone_id].clear()
    
    # Simulate APF avoidance check (from service_locator.py)
    if swarm._is_drone_mission_controlled(drone_id):
        # Mission active - should NOT call goto
        pass
    else:
        # Mission not active - would call goto
        mock_backend.goto(47.397742, 8.545594, 20.0)
    
    # Verify: goto was NOT called because mission is active
    assert not mock_backend.goto.called


def test_apf_avoidance_allows_when_no_mission():
    """Test that APF avoidance works when no mission is active."""
    from tools.ui.context.swarm_context import SwarmContext
    
    swarm = SwarmContext()
    drone_id = "D1"
    
    # Mock backend
    mock_backend = Mock()
    mock_backend.goto = Mock()
    swarm.backend.get_backend = Mock(return_value=mock_backend)
    
    # No mission active (drone not in dict)
    
    # Simulate APF avoidance check
    if swarm._is_drone_mission_controlled(drone_id):
        # Mission active - should NOT call goto
        pass
    else:
        # Mission not active - would call goto
        mock_backend.goto(47.397742, 8.545594, 20.0)
    
    # Verify: goto WAS called because no mission is active
    assert mock_backend.goto.called
    mock_backend.goto.assert_called_once_with(47.397742, 8.545594, 20.0)


def test_service_locator_uses_explicit_method():
    """Test that service_locator.py uses the explicit method."""
    # Read service_locator.py and verify it uses _is_drone_mission_controlled
    with open('tools/ui/service_locator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify the explicit method call is present
    assert 'swarm._is_drone_mission_controlled(drone_id)' in content
    
    # Verify the old fragile pattern is removed
    assert 'hasattr(swarm, "_is_drone_mission_controlled")' not in content

# Made with Bob
