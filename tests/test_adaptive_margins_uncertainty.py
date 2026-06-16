"""
Tests for AdaptiveAPFSafetyFilter uncertainty-based margin adaptation.

Verifies that safety margins increase appropriately based on sensor
uncertainty (GPS accuracy) and environmental conditions (wind), providing
larger separation when positioning is less reliable.
"""
import pytest
from droneresearch.safety.apf import AdaptiveAPFSafetyFilter, Pose3D


def test_adaptive_margin_increases_with_gps_uncertainty():
    """Margin should increase with GPS uncertainty."""
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    # Low GPS uncertainty
    apf_low = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.1,
        wind_speed=0.0,
        reaction_time=0.0,  # isolate uncertainty effect
        uncertainty_weight=2.0,
    )
    
    # High GPS uncertainty
    apf_high = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.5,
        wind_speed=0.0,
        reaction_time=0.0,
        uncertainty_weight=2.0,
    )
    
    margin_low = apf_low.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    margin_high = apf_high.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Higher uncertainty should require larger margin
    assert margin_high > margin_low
    
    # Expected increase: (0.5 - 0.1) * 2.0 = 0.8m
    expected_increase = (0.5 - 0.1) * 2.0
    assert abs(margin_high - margin_low - expected_increase) < 0.01


def test_uncertainty_weight_scaling():
    """Uncertainty weight should scale the GPS contribution."""
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    # 1-sigma weight
    apf_1sigma = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.3,
        uncertainty_weight=1.0,
        wind_speed=0.0,
        reaction_time=0.0,
    )
    
    # 2-sigma weight (95% confidence)
    apf_2sigma = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.3,
        uncertainty_weight=2.0,
        wind_speed=0.0,
        reaction_time=0.0,
    )
    
    margin_1sigma = apf_1sigma.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    margin_2sigma = apf_2sigma.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # 2-sigma should be exactly double the uncertainty contribution
    expected_increase = 0.3 * (2.0 - 1.0)
    actual_increase = margin_2sigma - margin_1sigma
    assert abs(actual_increase - expected_increase) < 0.01


def test_adaptive_margin_increases_with_wind():
    """Margin should increase with wind speed."""
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    # Calm conditions
    apf_calm = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        wind_speed=0.0,
        gps_uncertainty=0.0,
        reaction_time=0.0,
    )
    
    # Windy conditions
    apf_windy = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        wind_speed=5.0,
        gps_uncertainty=0.0,
        reaction_time=0.0,
        wind_factor_gain=0.2,
    )
    
    margin_calm = apf_calm.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    margin_windy = apf_windy.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Wind should increase margin
    assert margin_windy > margin_calm
    
    # Expected increase: wind_speed * wind_factor_gain = 5.0 * 0.2 = 1.0m
    expected_increase = 5.0 * 0.2
    assert abs(margin_windy - margin_calm - expected_increase) < 0.01


def test_wind_factor_gain_scaling():
    """Wind factor gain should scale wind contribution."""
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    # Low wind sensitivity
    apf_low = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        wind_speed=5.0,
        wind_factor_gain=0.1,
        gps_uncertainty=0.0,
        reaction_time=0.0,
    )
    
    # High wind sensitivity
    apf_high = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        wind_speed=5.0,
        wind_factor_gain=0.5,
        gps_uncertainty=0.0,
        reaction_time=0.0,
    )
    
    margin_low = apf_low.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    margin_high = apf_high.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Higher gain should produce larger margin
    assert margin_high > margin_low
    
    # Expected difference: 5.0 * (0.5 - 0.1) = 2.0m
    expected_diff = 5.0 * (0.5 - 0.1)
    actual_diff = margin_high - margin_low
    assert abs(actual_diff - expected_diff) < 0.01


def test_combined_uncertainty_factors():
    """All uncertainty factors should combine additively."""
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    # Individual factors
    apf_gps_only = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.3,
        uncertainty_weight=2.0,
        wind_speed=0.0,
        reaction_time=0.0,
    )
    
    apf_wind_only = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.0,
        wind_speed=5.0,
        wind_factor_gain=0.2,
        reaction_time=0.0,
    )
    
    # Combined
    apf_combined = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.3,
        uncertainty_weight=2.0,
        wind_speed=5.0,
        wind_factor_gain=0.2,
        reaction_time=0.0,
    )
    
    margin_gps = apf_gps_only.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    margin_wind = apf_wind_only.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    margin_combined = apf_combined.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Combined should equal sum of individual contributions
    gps_contribution = margin_gps - apf_gps_only.min_separation
    wind_contribution = margin_wind - apf_wind_only.min_separation
    expected_combined = apf_combined.min_separation + gps_contribution + wind_contribution
    
    assert abs(margin_combined - expected_combined) < 0.01


def test_set_wind_speed():
    """set_wind_speed should update wind speed dynamically."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        wind_speed=0.0,
        wind_factor_gain=0.2,
        gps_uncertainty=0.0,
        reaction_time=0.0,
    )
    
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    # Initial margin with no wind
    margin_calm = apf.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Update wind speed
    apf.set_wind_speed(5.0)
    margin_windy = apf.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Margin should increase
    assert margin_windy > margin_calm
    assert abs(margin_windy - margin_calm - 1.0) < 0.01  # 5.0 * 0.2 = 1.0


def test_set_wind_speed_negative_clamped():
    """set_wind_speed should clamp negative values to zero."""
    apf = AdaptiveAPFSafetyFilter(min_separation=2.0)
    
    apf.set_wind_speed(-5.0)
    assert apf.wind_speed == 0.0


def test_set_gps_uncertainty():
    """set_gps_uncertainty should update GPS uncertainty dynamically."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.1,
        uncertainty_weight=2.0,
        wind_speed=0.0,
        reaction_time=0.0,
    )
    
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    # Initial margin with low uncertainty
    margin_low = apf.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Update GPS uncertainty
    apf.set_gps_uncertainty(0.5)
    margin_high = apf.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Margin should increase
    assert margin_high > margin_low
    expected_increase = (0.5 - 0.1) * 2.0
    assert abs(margin_high - margin_low - expected_increase) < 0.01


def test_set_gps_uncertainty_negative_clamped():
    """set_gps_uncertainty should clamp negative values to zero."""
    apf = AdaptiveAPFSafetyFilter(min_separation=2.0)
    
    apf.set_gps_uncertainty(-0.5)
    assert apf.gps_uncertainty == 0.0


def test_filter_with_high_uncertainty():
    """Filter should maintain larger separation with high uncertainty."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        max_speed=3.0,
        gps_uncertainty=0.5,
        uncertainty_weight=2.0,
        wind_speed=3.0,
        wind_factor_gain=0.2,
        dt=0.05,
    )
    
    # Two drones close together
    positions = {
        "D1": Pose3D(0, 0, 10),
        "D2": Pose3D(3, 0, 10),  # 3m apart
    }
    
    desired = {
        "D1": Pose3D(0, 0, 10),   # wants to stay
        "D2": Pose3D(3, 0, 10),   # wants to stay
    }
    
    # Run filter
    safe = apf.filter(positions, desired)
    
    # Drones should be pushed apart due to high uncertainty
    # (adaptive margin > 3m due to GPS + wind)
    final_dist = safe["D1"].dist(safe["D2"])
    
    # Expected adaptive margin: 2.0 + (0.5 * 2.0) + (3.0 * 0.2) = 3.6m
    # Since they start at 3m, repulsion should push them apart
    assert final_dist >= positions["D1"].dist(positions["D2"])


def test_all_factors_combined():
    """Test realistic scenario with all factors active."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        reaction_time=0.5,
        gps_uncertainty=0.3,
        uncertainty_weight=2.0,
        wind_speed=4.0,
        wind_factor_gain=0.2,
        velocity_weight=1.0,
    )
    
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    
    # Drones moving toward each other
    vel_a = Pose3D(2, 0, 0)
    vel_b = Pose3D(-2, 0, 0)
    
    margin = apf.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    # Expected components:
    # - Base: 2.0m
    # - Velocity: 4.0 m/s * 0.5s * 1.0 = 2.0m
    # - GPS: 0.3m * 2.0 = 0.6m
    # - Wind: 4.0 m/s * 0.2 = 0.8m
    # Total: 5.4m
    expected = 2.0 + 2.0 + 0.6 + 0.8
    
    assert abs(margin - expected) < 0.01


def test_margin_never_below_minimum_with_uncertainty():
    """Even with zero uncertainty, margin should not drop below minimum."""
    apf = AdaptiveAPFSafetyFilter(
        min_separation=2.0,
        gps_uncertainty=0.0,
        wind_speed=0.0,
        reaction_time=0.0,
    )
    
    pos_a = Pose3D(0, 0, 10)
    pos_b = Pose3D(5, 0, 10)
    vel_a = Pose3D(0, 0, 0)
    vel_b = Pose3D(0, 0, 0)
    
    margin = apf.compute_adaptive_margin(pos_a, pos_b, vel_a, vel_b)
    
    assert margin == apf.min_separation

# Made with Bob
