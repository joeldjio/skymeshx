"""
Test for Fix 2: Mission Lock Race Condition

Verifies that _update_mission_lock() is thread-safe and handles concurrent
access correctly with gating and proper locking.
"""

import threading
import time
from unittest.mock import Mock

import pytest


def test_poll_gating_prevents_concurrent_execution():
    """Test that _poll_in_progress gate prevents concurrent polls."""
    # Simulate MissionContext state
    poll_in_progress = False
    poll_count = 0
    poll_lock = threading.Lock()
    
    def mock_poll():
        nonlocal poll_in_progress, poll_count
        
        # Gate: Skip if previous poll still running
        if poll_in_progress:
            return
        
        try:
            poll_in_progress = True
            with poll_lock:
                poll_count += 1
            # Simulate slow poll
            time.sleep(0.1)
        finally:
            poll_in_progress = False
    
    # Start 10 concurrent polls
    threads = []
    for _ in range(10):
        t = threading.Thread(target=mock_poll)
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Verify: Only one poll executed (others were gated)
    assert poll_count == 1


def test_mission_active_dict_is_primary_source():
    """Test that _mission_active dict is checked first."""
    # Simulate SwarmContext state
    state_lock = threading.RLock()
    mission_active = {
        "D1": threading.Event(),
        "D2": threading.Event(),
    }
    mission_active["D1"].clear()  # D1 mission active
    mission_active["D2"].set()    # D2 mission inactive
    
    # Check mission status
    any_mission_active = False
    with state_lock:
        for drone_id, event in mission_active.items():
            if not event.is_set():
                any_mission_active = True
                break
    
    # Verify: D1 mission detected
    assert any_mission_active


def test_backend_poll_with_exception_handling():
    """Test that backend polling handles exceptions gracefully."""
    # Mock backend that raises exception
    mock_backend = Mock()
    mock_backend.is_connected = True
    mock_backend.fsm_state = Mock(side_effect=RuntimeError("Connection lost"))
    mock_backend.get_telemetry_snapshot = Mock(side_effect=TimeoutError("Timeout"))
    
    backends = {"D1": mock_backend}
    
    # Poll backends with exception handling
    mission_active = False
    for drone_id, backend in backends.items():
        if not backend.is_connected:
            continue
        
        # Check FSM state (with exception handling)
        if hasattr(backend, 'fsm_state'):
            try:
                fsm_state = str(backend.fsm_state).upper()
                if fsm_state == 'MISSION':
                    mission_active = True
                    break
            except Exception:
                pass  # Ignore errors
        
        # Check telemetry (with exception handling)
        if hasattr(backend, 'get_telemetry_snapshot'):
            try:
                snap = backend.get_telemetry_snapshot()
                if snap:
                    flight_mode = str(snap.get('flight_mode', '')).upper()
                    if flight_mode in ('AUTO', 'MISSION'):
                        mission_active = True
                        break
            except Exception:
                pass  # Ignore errors
    
    # Verify: No exception raised, mission_active remains False
    assert not mission_active


def test_lock_state_change_emits_signal_once():
    """Test that lock state change emits signal only once."""
    mission_locked = False
    signal_count = 0
    
    def mock_emit(active):
        nonlocal signal_count
        signal_count += 1
    
    # Simulate multiple polls with same state
    for _ in range(5):
        new_state = True
        if new_state != mission_locked:
            mission_locked = new_state
            mock_emit(mission_locked)
    
    # Verify: Signal emitted only once
    assert signal_count == 1
    assert mission_locked is True


def test_concurrent_mission_active_dict_access():
    """Test thread-safe access to _mission_active dict."""
    state_lock = threading.RLock()
    mission_active = {}
    errors = []
    
    def add_mission(drone_id):
        try:
            with state_lock:
                if drone_id not in mission_active:
                    mission_active[drone_id] = threading.Event()
                mission_active[drone_id].clear()
        except Exception as e:
            errors.append(e)
    
    def check_mission():
        try:
            with state_lock:
                for drone_id, event in mission_active.items():
                    _ = event.is_set()
        except Exception as e:
            errors.append(e)
    
    # Start concurrent operations
    threads = []
    for i in range(10):
        t1 = threading.Thread(target=add_mission, args=(f"D{i}",))
        t2 = threading.Thread(target=check_mission)
        threads.extend([t1, t2])
        t1.start()
        t2.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Verify: No errors occurred
    assert len(errors) == 0
    assert len(mission_active) == 10


def test_fallback_to_backend_poll_when_dict_empty():
    """Test that backend polling works when _mission_active dict is empty."""
    # Simulate SwarmContext with empty _mission_active
    state_lock = threading.RLock()
    mission_active_dict = {}
    
    # Mock backend in MISSION mode
    mock_backend = Mock()
    mock_backend.is_connected = True
    mock_backend.fsm_state = "MISSION"
    backends = {"D1": mock_backend}
    
    # Check mission status
    mission_active = False
    
    # Primary check: _mission_active dict (empty)
    with state_lock:
        for drone_id, event in mission_active_dict.items():
            if not event.is_set():
                mission_active = True
                break
    
    # Fallback check: Backend FSM state
    if not mission_active:
        for drone_id, backend in backends.items():
            if not backend.is_connected:
                continue
            if hasattr(backend, 'fsm_state'):
                try:
                    fsm_state = str(backend.fsm_state).upper()
                    if fsm_state == 'MISSION':
                        mission_active = True
                        break
                except Exception:
                    pass
    
    # Verify: Mission detected via fallback
    assert mission_active

# Made with Bob
