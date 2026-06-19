"""Test goto() with configurable acceptance radius and velocity check."""

import pytest
from skymeshx.sdk.drone import Drone


def test_goto_default_acceptance_radius(fake_conn, snap_factory):
    """Test goto() with default 2.0m acceptance radius."""
    drone = Drone(fake_conn, drone_id="test")
    
    # Set initial position
    fake_conn.telemetry.update(
        lat=48.0,
        lon=11.0,
        alt_rel=10.0,
        groundspeed=0.0,
        flight_mode="GUIDED"
    )
    
    # Target 1.5m away (within default 2.0m radius)
    # 1.5m ≈ 0.0000135 degrees at equator
    target_lat = 48.0 + 0.0000135
    target_lon = 11.0
    
    result = drone.goto(target_lat, target_lon, 10.0, timeout=1.0)
    
    # Should succeed (within 2.0m radius)
    assert result is True


def test_goto_custom_acceptance_radius(fake_conn, snap_factory):
    """Test goto() with custom acceptance radius."""
    drone = Drone(fake_conn, drone_id="test")
    
    # Set initial position
    fake_conn.telemetry.update(
        lat=48.0,
        lon=11.0,
        alt_rel=10.0,
        groundspeed=0.0,
        flight_mode="GUIDED"
    )
    
    # Target 3.0m away
    # 3.0m ≈ 0.000027 degrees at equator
    target_lat = 48.0 + 0.000027
    target_lon = 11.0
    
    # Should fail with 2.0m radius
    result = drone.goto(target_lat, target_lon, 10.0, timeout=0.5, acceptance_radius=2.0)
    assert result is False
    
    # Should succeed with 5.0m radius
    result = drone.goto(target_lat, target_lon, 10.0, timeout=0.5, acceptance_radius=5.0)
    assert result is True


def test_goto_altitude_check(fake_conn, snap_factory):
    """Test goto() with altitude verification."""
    drone = Drone(fake_conn, drone_id="test")
    
    # Set initial position at wrong altitude
    fake_conn.telemetry.update(
        lat=48.0,
        lon=11.0,
        alt_rel=10.0,  # Current altitude
        groundspeed=0.0,
        flight_mode="GUIDED"
    )
    
    # Target same position but different altitude
    target_alt = 15.0
    
    # Should fail with altitude check (5m error > 1m threshold)
    result = drone.goto(48.0, 11.0, target_alt, timeout=0.5, check_altitude=True)
    assert result is False
    
    # Should succeed without altitude check
    result = drone.goto(48.0, 11.0, target_alt, timeout=0.5, check_altitude=False)
    assert result is True


def test_goto_velocity_check(fake_conn, snap_factory):
    """Test goto() with velocity verification."""
    drone = Drone(fake_conn, drone_id="test")
    
    # Set initial position with high velocity (still moving)
    fake_conn.telemetry.update(
        lat=48.0,
        lon=11.0,
        alt_rel=10.0,
        groundspeed=2.0,  # Still moving fast
        flight_mode="GUIDED"
    )
    
    # Should fail with velocity check (2.0 m/s > 0.5 m/s threshold)
    result = drone.goto(48.0, 11.0, 10.0, timeout=0.5, check_velocity=True)
    assert result is False
    
    # Should succeed without velocity check
    result = drone.goto(48.0, 11.0, 10.0, timeout=0.5, check_velocity=False)
    assert result is True


def test_goto_all_checks_pass(fake_conn, snap_factory):
    """Test goto() when all arrival criteria are met."""
    drone = Drone(fake_conn, drone_id="test")
    
    # Set perfect arrival state
    fake_conn.telemetry.update(
        lat=48.0,
        lon=11.0,
        alt_rel=10.0,
        groundspeed=0.2,  # Slow enough (< 0.5 m/s)
        flight_mode="GUIDED"
    )
    
    # All checks should pass
    result = drone.goto(
        48.0, 11.0, 10.0,
        timeout=1.0,
        acceptance_radius=2.0,
        check_altitude=True,
        check_velocity=True
    )
    
    assert result is True


def test_goto_mode_change_timeout_budget(fake_conn, snap_factory):
    """Test that goto() properly distributes timeout budget for mode change."""
    drone = Drone(fake_conn, drone_id="test")
    
    # Start in wrong mode
    fake_conn.telemetry.update(
        lat=48.0,
        lon=11.0,
        alt_rel=10.0,
        groundspeed=0.0,
        flight_mode="STABILIZE"  # Wrong mode
    )
    
    # Should use 20% of timeout for mode change
    result = drone.goto(48.0, 11.0, 10.0, timeout=5.0)
    
    # Mode should have been changed to GUIDED
    assert fake_conn.telemetry.flight_mode == "GUIDED"

# Made with Bob
