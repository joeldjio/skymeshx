"""Test swarm formation with APF collision avoidance."""

import pytest
import time
from skymeshx.sdk.swarm_api import Swarm


def test_formation_parallel_default(fake_conn, snap_factory):
    """Test that formation() uses parallel movements by default."""
    swarm = Swarm(auto_log=False)
    
    # Add 3 drones
    for i in range(3):
        conn = fake_conn  # Reuse same fake connection for simplicity
        conn.telemetry.update(lat=48.0, lon=11.0, alt_rel=10.0, flight_mode="GUIDED")
        swarm.add(f"D{i}", conn)
    
    start_time = time.time()
    swarm.formation("line", spacing=5.0, use_apf=False)
    elapsed = time.time() - start_time
    
    # Parallel execution should be fast (<1 second)
    assert elapsed < 1.0


def test_formation_sequential_with_apf(fake_conn, snap_factory):
    """Test that formation() uses sequential movements with use_apf=True."""
    swarm = Swarm(auto_log=False)
    
    # Add 3 drones
    for i in range(3):
        conn = fake_conn
        conn.telemetry.update(lat=48.0, lon=11.0, alt_rel=10.0, flight_mode="GUIDED")
        swarm.add(f"D{i}", conn)
    
    start_time = time.time()
    swarm.formation("line", spacing=5.0, use_apf=True, stagger_delay=0.5)
    elapsed = time.time() - start_time
    
    # Sequential with 0.5s delay between 2 followers = ~1.0s minimum
    # (leader doesn't move, so 2 followers with 1 delay between them)
    assert elapsed >= 0.5


def test_formation_custom_stagger_delay(fake_conn, snap_factory):
    """Test that custom stagger_delay is respected."""
    swarm = Swarm(auto_log=False)
    
    # Add 4 drones (1 leader + 3 followers)
    for i in range(4):
        conn = fake_conn
        conn.telemetry.update(lat=48.0, lon=11.0, alt_rel=10.0, flight_mode="GUIDED")
        swarm.add(f"D{i}", conn)
    
    start_time = time.time()
    swarm.formation("circle", spacing=5.0, use_apf=True, stagger_delay=0.2)
    elapsed = time.time() - start_time
    
    # 3 followers with 0.2s delay = ~0.4s minimum (2 delays)
    assert elapsed >= 0.4
    assert elapsed < 1.0  # Should not take too long


def test_formation_apf_with_leader(fake_conn, snap_factory):
    """Test that APF mode works with explicit leader."""
    swarm = Swarm(auto_log=False)
    
    # Add 3 drones
    for i in range(3):
        conn = fake_conn
        conn.telemetry.update(lat=48.0, lon=11.0, alt_rel=10.0, flight_mode="GUIDED")
        swarm.add(f"D{i}", conn)
    
    # Use D1 as leader
    swarm.formation("v", spacing=5.0, leader="D1", use_apf=True, stagger_delay=0.3)
    
    # Should complete without error


def test_formation_shapes_with_apf(fake_conn, snap_factory):
    """Test that all formation shapes work with APF mode."""
    swarm = Swarm(auto_log=False)
    
    # Add 5 drones for variety
    for i in range(5):
        conn = fake_conn
        conn.telemetry.update(lat=48.0, lon=11.0, alt_rel=10.0, flight_mode="GUIDED")
        swarm.add(f"D{i}", conn)
    
    shapes = ["line", "v", "grid", "circle"]
    
    for shape in shapes:
        swarm.formation(shape, spacing=5.0, use_apf=True, stagger_delay=0.1)
        # Should complete without error


def test_formation_empty_swarm(fake_conn):
    """Test that formation() handles empty swarm gracefully."""
    swarm = Swarm(auto_log=False)
    
    # Should not crash with empty swarm
    swarm.formation("line", spacing=5.0, use_apf=True)
