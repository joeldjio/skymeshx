"""
Tests for AdaptiveAPFSafetyFilter velocity-based margin adaptation.

Verifies that safety margins increase appropriately based on relative
velocity between drones, providing larger separation when drones are
moving quickly toward each other.
"""
import pytest
from skymeshx.safety.apf import AdaptiveAPFSafetyFilter, Pose3D


def test_adaptive_margin_increases_with_velocity():
    """Margin should increase with relative velocity."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.5,
        gps_uncertainty=0.0,  # isolate velocity effect
        wind_speed=0.0,
        velocity_weight=1.0,
    )
    
    # Stationary drones
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    margin_stationary = apf.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Moving toward each other at 2 m/s
    vel_a_moving = Pose3D(2, 0, 0)
    vel_b_moving = Pose3D(-2, 0, 0)
    
    margin_moving = apf.compute_adaptive_margin(pos_a, pos_b, vel_a_moving, vel_b_moving)
    
    # Margin should increase with velocity
    assert margin_moving > margin_stationary
    
    # Expected increase: rel_vel * reaction_time = 4 m/s * 0.5s = 2m
    expected_increase = 4.0 * 0.5
    assert abs(margin_moving - margin_stationary - expected_increase) < 0.01


def test_adaptive_margin_parallel_motion():
    """Parallel motion should have less impact than head-on collision."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.5,
        gps_uncertainty=0.0,
        wind_speed=0.0,
    )
    
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    
    # Both moving in same direction (parallel)
    vel_parallel_a = Pose3D(2, 0, 0)
    vel_parallel_b = Pose3D(2, 0, 0)
    
    # Moving toward each other (head-on)
    vel_headon_a = Pose3D(2, 0, 0)
    vel_headon_b = Pose3D(-2, 0, 0)
    
    margin_parallel = apf.compute_adaptive_margin(pos_a, pos_b, vel_parallel_a, vel_parallel_b)
    margin_headon = apf.compute_adaptive_margin(pos_a, pos_b, vel_headon_a, vel_headon_b)
    
    # Head-on should require larger margin
    assert margin_headon > margin_parallel


def test_adaptive_margin_never_below_minimum():
    """Margin should never drop below min_separation."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.5,
        gps_uncertainty=0.0,
        wind_speed=0.0,
    )
    
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    margin = apf.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    assert margin >= apf.min_separation


def test_velocity_weight_scaling():
    """Velocity weight should scale the velocity contribution."""
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(2, 0, 0)
    vel_b = Pose3D(-2, 0, 0)
    
    # Low weight
    apf_low = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.5,
        velocity_weight=0.5,
        gps_uncertainty=0.0,
        wind_speed=0.0,
    )
    
    # High weight
    apf_high = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.5,
        velocity_weight=2.0,
        gps_uncertainty=0.0,
        wind_speed=0.0,
    )
    
    margin_low = apf_low.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    margin_high = apf_high.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Higher weight should produce larger margin
    assert margin_high > margin_low


def test_filter_with_high_velocity():
    """Filter should maintain larger separation for high-velocity drones."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        max_speed=5.0,
        reaction_time=0.5,
        gps_uncertainty=0.0,
        wind_speed=0.0,
        dt=0.05,
    )
    
    # Two drones moving toward each other
    positions = {
        "D1": Pose3D(0, 0, 10),
        "D2": Pose3D(4, 0, 10),  # 4m apart
    }
    
    desired = {
        "D1": Pose3D(5, 0, 10),   # wants to move right
        "D2": Pose3D(-5, 0, 10),  # wants to move left
    }
    
    # Run filter multiple times to build up velocity
    for _ in range(10):
        safe = apf.filter(positions, desired)
        positions = safe
    
    # After building velocity, drones should maintain separation
    final_dist = positions["D1"].dist(positions["D2"])
    
    # Should maintain at least min_separation
    assert final_dist >= apf.min_separation


def test_get_current_margin():
    """get_current_margin should return adaptive margin for drone pair."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.5,
        gps_uncertainty=0.3,
        wind_speed=1.0,
    )
    
    positions = {
        "D1": Pose3D(0, 0, 10),
        "D2": Pose3D(5, 0, 10),
    }
    
    desired = {
        "D1": Pose3D(2, 0, 10),
        "D2": Pose3D(3, 0, 10),
    }
    
    # First call - no velocity data yet
    margin = apf.get_current_margin("D1", "D2")
    assert margin is None
    
    # Run filter to build velocity data
    apf.filter(positions, desired)
    
    # Now should return a margin
    margin = apf.get_current_margin("D1", "D2")
    assert margin is not None
    assert margin >= apf.min_separation


def test_3d_velocity_calculation():
    """Relative velocity should account for all 3 dimensions."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.5,
        gps_uncertainty=0.0,
        wind_speed=0.0,
    )
    
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    
    # 2D velocity (horizontal only)
    vel_2d_a = Pose3D(2, 0, 0)
    vel_2d_b = Pose3D(-2, 0, 0)
    
    # 3D velocity (includes vertical)
    vel_3d_a = Pose3D(2, 0, 1)
    vel_3d_b = Pose3D(-2, 0, -1)
    
    margin_2d = apf.compute_adaptive_margin(pos_a, pos_b, vel_2d_a, vel_2d_b)
    margin_3d = apf.compute_adaptive_margin(pos_a, pos_b, vel_3d_a, vel_3d_b)
    
    # 3D velocity has larger magnitude, should produce larger margin
    assert margin_3d > margin_2d


def test_reaction_time_scaling():
    """Longer reaction time should increase velocity-based margin."""
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(2, 0, 0)
    vel_b = Pose3D(-2, 0, 0)
    
    # Short reaction time
    apf_short = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.2,
        gps_uncertainty=0.0,
        wind_speed=0.0,
    )
    
    # Long reaction time
    apf_long = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=1.0,
        gps_uncertainty=0.0,
        wind_speed=0.0,
    )
    
    margin_short = apf_short.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    margin_long = apf_long.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Longer reaction time should require larger margin
    assert margin_long > margin_short
    
    # Difference should be proportional to reaction time difference
    # rel_vel = 4 m/s, delta_reaction = 0.8s, expected delta = 3.2m
    expected_delta = 4.0 * (1.0 - 0.2)
    actual_delta = margin_long - margin_short
    assert abs(actual_delta - expected_delta) < 0.01

# Made with Bob
