"""
Tests for NED/ENU frame conversion functions.

Verifies that frame conversions are mathematically correct and consistent
across different modules.
"""
import pytest
import math


def test_ned_to_enu_px4_bridge():
    """Test NED→ENU conversion in px4_bridge."""
    from droneresearch.ros.px4_bridge import ned_to_enu
    
    # Test case: North=1, East=2, Down=3
    result = ned_to_enu(1.0, 2.0, 3.0)
    
    # Expected: ENU = (East, North, -Down) = (2, 1, -3)
    assert result == (2.0, 1.0, -3.0), f"Expected (2.0, 1.0, -3.0), got {result}"


def test_enu_to_ned_px4_bridge():
    """Test ENU→NED conversion in px4_bridge."""
    from droneresearch.ros.px4_bridge import enu_to_ned
    
    # Test case: East=2, North=1, Up=-3
    result = enu_to_ned(2.0, 1.0, -3.0)
    
    # Expected: NED = (North, East, -Up) = (1, 2, 3)
    assert result == (1.0, 2.0, 3.0), f"Expected (1.0, 2.0, 3.0), got {result}"


def test_ned_to_enu_px4_formation():
    """Test NED→ENU conversion in px4_formation."""
    from droneresearch.ros.px4_formation import ned_to_enu
    
    # Test case: North=1, East=2, Down=3
    result = ned_to_enu(1.0, 2.0, 3.0)
    
    # Expected: ENU = (East, North, -Down) = (2, 1, -3)
    assert result == (2.0, 1.0, -3.0), f"Expected (2.0, 1.0, -3.0), got {result}"


def test_enu_to_ned_px4_formation():
    """Test ENU→NED conversion in px4_formation."""
    from droneresearch.ros.px4_formation import enu_to_ned
    
    # Test case: East=2, North=1, Up=-3
    result = enu_to_ned(2.0, 1.0, -3.0)
    
    # Expected: NED = (North, East, -Up) = (1, 2, 3)
    assert result == (1.0, 2.0, 3.0), f"Expected (1.0, 2.0, 3.0), got {result}"


def test_ned_enu_roundtrip_px4_bridge():
    """Test NED→ENU→NED roundtrip in px4_bridge."""
    from droneresearch.ros.px4_bridge import ned_to_enu, enu_to_ned
    
    # Original NED coordinates
    n, e, d = 10.0, 20.0, 30.0
    
    # Convert to ENU and back
    enu = ned_to_enu(n, e, d)
    ned = enu_to_ned(*enu)
    
    # Should get back original values
    assert ned == (n, e, d), f"Roundtrip failed: {(n, e, d)} → {enu} → {ned}"


def test_ned_enu_roundtrip_px4_formation():
    """Test NED→ENU→NED roundtrip in px4_formation."""
    from droneresearch.ros.px4_formation import ned_to_enu, enu_to_ned
    
    # Original NED coordinates
    n, e, d = 10.0, 20.0, 30.0
    
    # Convert to ENU and back
    enu = ned_to_enu(n, e, d)
    ned = enu_to_ned(*enu)
    
    # Should get back original values
    assert ned == (n, e, d), f"Roundtrip failed: {(n, e, d)} → {enu} → {ned}"


def test_frd_to_flu():
    """Test FRD→FLU body frame conversion."""
    from droneresearch.ros.px4_bridge import frd_to_flu
    
    # Test case: Forward=1, Right=2, Down=3
    result = frd_to_flu(1.0, 2.0, 3.0)
    
    # Expected: FLU = (Forward, -Right, -Down) = (1, -2, -3)
    assert result == (1.0, -2.0, -3.0), f"Expected (1.0, -2.0, -3.0), got {result}"


def test_consistency_between_modules():
    """Test that both modules produce identical results."""
    from droneresearch.ros.px4_bridge import ned_to_enu as ned_to_enu_bridge
    from droneresearch.ros.px4_bridge import enu_to_ned as enu_to_ned_bridge
    from droneresearch.ros.px4_formation import ned_to_enu as ned_to_enu_formation
    from droneresearch.ros.px4_formation import enu_to_ned as enu_to_ned_formation
    
    # Test multiple coordinate sets
    test_cases = [
        (0.0, 0.0, 0.0),
        (1.0, 2.0, 3.0),
        (-5.0, 10.0, -15.0),
        (100.0, -50.0, 25.0),
    ]
    
    for n, e, d in test_cases:
        # NED→ENU should be identical
        enu_bridge = ned_to_enu_bridge(n, e, d)
        enu_formation = ned_to_enu_formation(n, e, d)
        assert enu_bridge == enu_formation, \
            f"NED→ENU mismatch for ({n},{e},{d}): bridge={enu_bridge}, formation={enu_formation}"
        
        # ENU→NED should be identical
        ned_bridge = enu_to_ned_bridge(*enu_bridge)
        ned_formation = enu_to_ned_formation(*enu_formation)
        assert ned_bridge == ned_formation, \
            f"ENU→NED mismatch: bridge={ned_bridge}, formation={ned_formation}"


def test_zero_coordinates():
    """Test conversion of zero coordinates."""
    from droneresearch.ros.px4_bridge import ned_to_enu, enu_to_ned
    
    # Zero should remain zero
    assert ned_to_enu(0.0, 0.0, 0.0) == (0.0, 0.0, 0.0)
    assert enu_to_ned(0.0, 0.0, 0.0) == (0.0, 0.0, 0.0)


def test_altitude_sign_convention():
    """Test that altitude (z-axis) sign is correctly inverted."""
    from droneresearch.ros.px4_bridge import ned_to_enu, enu_to_ned
    
    # Positive altitude in NED (down) should be negative in ENU (up)
    n, e, d = 0.0, 0.0, 10.0  # 10m down in NED
    enu_e, enu_n, enu_u = ned_to_enu(n, e, d)
    assert enu_u == -10.0, f"Expected -10.0 up in ENU, got {enu_u}"
    
    # Negative altitude in NED (up) should be positive in ENU (up)
    n, e, d = 0.0, 0.0, -10.0  # 10m up in NED
    enu_e, enu_n, enu_u = ned_to_enu(n, e, d)
    assert enu_u == 10.0, f"Expected 10.0 up in ENU, got {enu_u}"


def test_north_east_swap():
    """Test that North and East are correctly swapped."""
    from droneresearch.ros.px4_bridge import ned_to_enu
    
    # Pure North in NED should be pure North in ENU (second component)
    enu_e, enu_n, enu_u = ned_to_enu(10.0, 0.0, 0.0)
    assert enu_n == 10.0 and enu_e == 0.0, \
        f"Pure North failed: expected (0, 10, 0), got ({enu_e}, {enu_n}, {enu_u})"
    
    # Pure East in NED should be pure East in ENU (first component)
    enu_e, enu_n, enu_u = ned_to_enu(0.0, 10.0, 0.0)
    assert enu_e == 10.0 and enu_n == 0.0, \
        f"Pure East failed: expected (10, 0, 0), got ({enu_e}, {enu_n}, {enu_u})"

# Made with Bob
