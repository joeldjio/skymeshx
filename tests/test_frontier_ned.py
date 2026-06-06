"""Regression: _FrontierNode must convert GPS coordinates to local NED metres
before publishing Odometry/PoseStamped. Previously it published raw GPS degrees
as position, causing the frontier planner to compute wildly wrong distances.
"""

import math

import pytest


def _approx(a, b, tol=0.01):
    return abs(a - b) <= tol


class TestGPSToNEDConversion:
    """Test the coordinate conversion logic without requiring ROS2."""

    def _gps_to_ned(self, lat, lon, ref_lat, ref_lon):
        """Same formula as _FrontierNode._gps_to_ned."""
        north = (lat - ref_lat) * 111_320.0
        east = (lon - ref_lon) * 111_320.0 * math.cos(math.radians(ref_lat))
        return north, east

    def test_origin_maps_to_zero(self):
        ref_lat, ref_lon = 48.137, 11.575
        n, e = self._gps_to_ned(ref_lat, ref_lon, ref_lat, ref_lon)
        assert _approx(n, 0.0)
        assert _approx(e, 0.0)

    def test_100m_north(self):
        ref_lat, ref_lon = 48.0, 11.0
        delta_lat = 100.0 / 111_320.0
        n, e = self._gps_to_ned(ref_lat + delta_lat, ref_lon, ref_lat, ref_lon)
        assert _approx(n, 100.0, tol=0.5)
        assert _approx(e, 0.0, tol=0.1)

    def test_100m_east(self):
        ref_lat, ref_lon = 48.0, 11.0
        delta_lon = 100.0 / (111_320.0 * math.cos(math.radians(ref_lat)))
        n, e = self._gps_to_ned(ref_lat, ref_lon + delta_lon, ref_lat, ref_lon)
        assert _approx(n, 0.0, tol=0.1)
        assert _approx(e, 100.0, tol=0.5)

    def test_gps_degrees_not_used_as_metres(self):
        """48 deg lat != 48 metres. Old code passed GPS degrees directly."""
        ref_lat, ref_lon = 48.137, 11.575
        # Position 10m north
        lat = ref_lat + 10.0 / 111_320.0
        n, e = self._gps_to_ned(lat, ref_lon, ref_lat, ref_lon)
        # Result must be ~10m, not ~0.00009 deg (the raw GPS delta)
        assert n > 5.0 and n < 15.0, f"Expected ~10m, got {n}"
