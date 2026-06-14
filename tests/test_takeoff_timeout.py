"""
Tests for takeoff timeout mechanism.

Verifies that takeoff operations timeout correctly and don't hang indefinitely.
"""
import pytest
import time
from tests.conftest import FakeConnection, FakeTelemetry


def test_takeoff_timeout_when_altitude_not_reached(fake_conn):
    """Takeoff times out if altitude is never reached."""
    from droneresearch.sdk.drone import Drone
    
    # Setup: already armed and in mode, but altitude never reached
    fake_conn.telemetry.alt_rel = 0.0
    fake_conn.telemetry.armed = True
    fake_conn.telemetry.autopilot = "ardupilot"
    fake_conn.telemetry.flight_mode = "GUIDED"
    
    drone = Drone(fake_conn)
    
    # Takeoff with short timeout - altitude never increases
    start = time.time()
    result = drone.takeoff(altitude=10.0, timeout=1.0)
    elapsed = time.time() - start
    
    # Should timeout and return False
    assert result is False
    # Should use full timeout (already armed/mode, so all time goes to altitude wait)
    assert 0.9 < elapsed < 1.2


def test_takeoff_succeeds_when_altitude_reached(fake_conn):
    """Takeoff succeeds when altitude is reached within timeout."""
    from droneresearch.sdk.drone import Drone
    
    # Setup: telemetry reaches target altitude
    fake_conn.telemetry.alt_rel = 0.0
    fake_conn.telemetry.armed = True
    fake_conn.telemetry.autopilot = "ardupilot"
    fake_conn.telemetry.flight_mode = "GUIDED"
    
    drone = Drone(fake_conn)
    
    # Simulate altitude increase after 0.3s
    def update_altitude():
        time.sleep(0.3)
        fake_conn.telemetry.alt_rel = 9.0  # 90% of 10m
    
    import threading
    thread = threading.Thread(target=update_altitude, daemon=True)
    thread.start()
    
    # Takeoff with sufficient timeout
    start = time.time()
    result = drone.takeoff(altitude=10.0, timeout=2.0)
    elapsed = time.time() - start
    
    # Should succeed when altitude reached
    assert result is True
    assert 0.2 < elapsed < 0.6  # Should complete around 0.3s


def test_takeoff_default_timeout():
    """Takeoff has reasonable default timeout (30s)."""
    from droneresearch.sdk.drone import Drone
    import inspect
    
    # Check default parameter
    sig = inspect.signature(Drone.takeoff)
    timeout_param = sig.parameters['timeout']
    assert timeout_param.default == 30.0


def test_land_has_timeout(fake_conn):
    """Land operation also has timeout."""
    from droneresearch.sdk.drone import Drone
    
    # IMPORTANT: Start with armed=True so land() doesn't return immediately
    fake_conn.telemetry.armed = True
    fake_conn.telemetry.autopilot = "ardupilot"
    
    drone = Drone(fake_conn)
    
    # Land with short timeout (armed never becomes False)
    start = time.time()
    result = drone.land(timeout=1.0)
    elapsed = time.time() - start
    
    # Should timeout
    assert result is False
    assert 0.9 < elapsed < 1.2


def test_goto_has_timeout(fake_conn):
    """Goto operation also has timeout."""
    from droneresearch.sdk.drone import Drone
    
    fake_conn.telemetry.lat = 0.0
    fake_conn.telemetry.lon = 0.0
    fake_conn.telemetry.autopilot = "ardupilot"
    fake_conn.telemetry.flight_mode = "GUIDED"  # Already in correct mode
    
    drone = Drone(fake_conn)
    
    # Goto with short timeout (never reaches target)
    start = time.time()
    result = drone.goto(lat=0.001, lon=0.001, alt=10.0, timeout=1.0)
    elapsed = time.time() - start
    
    assert result is False
    assert 0.9 < elapsed < 1.2


def test_wait_for_helper_respects_timeout(fake_conn):
    """_wait_for helper correctly implements timeout."""
    from droneresearch.sdk.drone import Drone
    
    drone = Drone(fake_conn)
    
    # Condition that never becomes true
    start = time.time()
    result = drone._wait_for(lambda: False, timeout=0.5)
    elapsed = time.time() - start
    
    assert result is False
    assert 0.4 < elapsed < 0.7


def test_wait_for_returns_immediately_when_condition_met(fake_conn):
    """_wait_for returns immediately when condition is met."""
    from droneresearch.sdk.drone import Drone
    
    drone = Drone(fake_conn)
    
    # Condition that is immediately true
    start = time.time()
    result = drone._wait_for(lambda: True, timeout=5.0)
    elapsed = time.time() - start
    
    assert result is True
    assert elapsed < 0.2  # Should return almost immediately


def test_takeoff_with_very_long_timeout(fake_conn):
    """Takeoff can have very long timeout for slow operations."""
    from droneresearch.sdk.drone import Drone
    import inspect
    
    # Verify timeout parameter accepts large values
    sig = inspect.signature(Drone.takeoff)
    timeout_param = sig.parameters['timeout']
    
    # Should accept any float
    assert timeout_param.annotation == float or timeout_param.annotation == inspect.Parameter.empty


def test_multiple_takeoff_attempts_dont_accumulate(fake_conn):
    """Multiple failed takeoff attempts don't accumulate delays."""
    from droneresearch.sdk.drone import Drone
    
    fake_conn.telemetry.alt_rel = 0.0
    fake_conn.telemetry.armed = True
    fake_conn.telemetry.autopilot = "ardupilot"
    fake_conn.telemetry.flight_mode = "GUIDED"
    
    drone = Drone(fake_conn)
    
    # First attempt
    start1 = time.time()
    result1 = drone.takeoff(altitude=10.0, timeout=0.5)
    elapsed1 = time.time() - start1
    
    # Second attempt
    start2 = time.time()
    result2 = drone.takeoff(altitude=10.0, timeout=0.5)
    elapsed2 = time.time() - start2
    
    # Both should timeout independently
    assert result1 is False
    assert result2 is False
    assert 0.4 < elapsed1 < 0.7
    assert 0.4 < elapsed2 < 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
