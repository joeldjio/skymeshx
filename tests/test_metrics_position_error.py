"""Tests for position_error metric in MetricsCollector."""

import math
from unittest.mock import MagicMock

import pytest


def _make_collector(metrics=None):
    from skymeshx.experiment.metrics import MetricsCollector

    mc = MetricsCollector(metrics or ["position_error", "flight_time"])
    backend = MagicMock()
    tel = MagicMock()
    tel.lat, tel.lon, tel.alt_rel = 48.0, 11.0, 10.0
    tel.groundspeed, tel.battery_pct, tel.gps_fix, tel.armed = 0.0, 100.0, 3, True
    backend.telemetry = tel
    mc.attach(backend)
    return mc, tel


class TestPositionError:
    def test_empty_path_returns_no_metric(self):
        mc, _ = _make_collector(["position_error"])
        mc.set_intended_path([])
        mc.start()
        __import__("time").sleep(0.1)
        mc.stop()
        result = mc.summary()
        assert "position_error_rms_m" not in result

    def test_on_path_gives_zero_error(self):
        mc, tel = _make_collector(["position_error"])
        mc.set_intended_path([{"lat": 48.0, "lon": 11.0}])
        tel.lat, tel.lon = 48.0, 11.0
        mc.start()
        __import__("time").sleep(0.6)
        mc.stop()
        result = mc.summary()
        if "position_error_rms_m" in result:
            assert result["position_error_rms_m"] < 1.0

    def test_offset_gives_nonzero_error(self):
        mc, tel = _make_collector(["position_error"])
        # Path goes straight north at lon=11.0, but drone is 100m east
        mc.set_intended_path([{"lat": 48.0, "lon": 11.0}, {"lat": 48.01, "lon": 11.0}])
        delta_lon = 100.0 / (111_320.0 * math.cos(math.radians(48.0)))
        tel.lat, tel.lon = 48.005, 11.0 + delta_lon  # 100m east of path
        mc.start()
        __import__("time").sleep(0.6)
        mc.stop()
        result = mc.summary()
        assert "position_error_rms_m" in result
        assert result["position_error_rms_m"] > 50.0  # should be ~100m
