"""
MetricsCollector — quantitative flight metrics for research experiments.

Metrics collected:
    position_error  — RMS deviation from intended path (m)
    battery_drain   — Total battery % consumed
    flight_time     — Total airborne time (s)
    max_altitude    — Peak altitude reached (m)
    avg_groundspeed — Mean groundspeed (m/s)
    dist_traveled   — Total distance traveled (m)
    hover_stability — Std-dev of position during hover (m)
    gps_quality     — % of flight with 3D GPS fix

Usage:
    metrics = MetricsCollector(["flight_time", "battery_drain", "dist_traveled"])
    metrics.attach(backend)
    metrics.start()
    # ... fly ...
    metrics.stop()
    print(metrics.summary())
"""

import math
import statistics
import threading
import time
from typing import Any, Dict, List, Optional


class MetricsCollector:
    def __init__(self, metric_names: List[str]):
        self._requested = (
            set(metric_names) if metric_names else {"flight_time", "battery_drain"}
        )
        self._backend = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._samples: List[dict] = []
        self._start_bat = None
        self._start_t = None
        self._airborne_t = 0.0
        self._last_t = None
        self._was_airborne = False
        self._intended_path: List[tuple] = []  # (lat, lon) Soll-Punkte
        self._path_rms_errors: List[float] = []

    def set_intended_path(self, waypoints: List[dict]):
        """Set the intended flight path for position_error calculation.

        waypoints: list of {"lat": float, "lon": float} dicts
        """
        self._intended_path = [(wp["lat"], wp["lon"]) for wp in waypoints]

    def attach(self, backend):
        self._backend = backend

    def start(self):
        self._running = True
        self._start_t = time.time()
        self._samples = []
        self._thread = threading.Thread(
            target=self._collect_loop, daemon=True, name="metrics"
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def summary(self) -> Dict[str, Any]:
        if not self._samples:
            return {}
        result = {}
        lats = [s["lat"] for s in self._samples if s["lat"] != 0]
        alts = [s["alt"] for s in self._samples]
        speeds = [s["spd"] for s in self._samples]
        bats = [s["bat"] for s in self._samples if s["bat"] >= 0]
        gps = [s["gps"] for s in self._samples]

        if "flight_time" in self._requested:
            result["flight_time_s"] = round(self._airborne_t, 1)

        if "battery_drain" in self._requested and len(bats) >= 2:
            result["battery_drain_pct"] = round(bats[0] - bats[-1], 1)

        if "max_altitude" in self._requested and alts:
            result["max_altitude_m"] = round(max(alts), 2)

        if "avg_groundspeed" in self._requested and speeds:
            result["avg_groundspeed_ms"] = round(statistics.mean(speeds), 2)

        if "dist_traveled" in self._requested:
            result["dist_traveled_m"] = round(self._calc_distance(), 1)

        if "hover_stability" in self._requested and len(lats) > 10:
            lat_std = statistics.stdev(lats)
            lon_std = statistics.stdev(
                [s["lon"] for s in self._samples if s["lon"] != 0]
            )
            pos_std = math.sqrt(lat_std**2 + lon_std**2) * 111320
            result["hover_stability_m"] = round(pos_std, 3)

        if "gps_quality" in self._requested and gps:
            result["gps_fix_pct"] = round(
                100 * sum(1 for g in gps if g >= 3) / len(gps), 1
            )

        if "position_error" in self._requested and self._path_rms_errors:
            rms = math.sqrt(
                sum(e**2 for e in self._path_rms_errors) / len(self._path_rms_errors)
            )
            result["position_error_rms_m"] = round(rms, 3)
            result["position_error_max_m"] = round(max(self._path_rms_errors), 3)

        return result

    def _collect_loop(self):
        while self._running:
            if self._backend:
                t = self._backend.telemetry
                now = time.time()
                sample = {
                    "t": now,
                    "lat": t.lat,
                    "lon": t.lon,
                    "alt": t.alt_rel,
                    "spd": t.groundspeed,
                    "bat": t.battery_pct,
                    "gps": t.gps_fix,
                    "armed": t.armed,
                }
                self._samples.append(sample)
                if "position_error" in self._requested and self._intended_path:
                    err = self._min_path_dist(sample["lat"], sample["lon"])
                    if err is not None:
                        self._path_rms_errors.append(err)
                if self._start_bat is None and t.battery_pct >= 0:
                    self._start_bat = t.battery_pct
                if t.armed and t.alt_rel > 0.5:
                    if self._last_t is not None:
                        self._airborne_t += now - self._last_t
                    self._last_t = now
                else:
                    self._last_t = None
            time.sleep(0.5)

    def _min_path_dist(self, lat: float, lon: float) -> Optional[float]:
        """Minimale Distanz (Meter) vom Punkt zum nächsten Pfadsegment."""
        if not self._intended_path:
            return None
        min_d = float("inf")
        for plat, plon in self._intended_path:
            dlat = (lat - plat) * 111320.0
            dlon = (lon - plon) * 111320.0 * math.cos(math.radians(lat))
            d = math.sqrt(dlat**2 + dlon**2)
            if d < min_d:
                min_d = d
        return min_d

    def _calc_distance(self) -> float:
        total = 0.0
        pts = [(s["lat"], s["lon"]) for s in self._samples if s["lat"] != 0]
        for i in range(1, len(pts)):
            dlat = (pts[i][0] - pts[i - 1][0]) * 111320
            dlon = (
                (pts[i][1] - pts[i - 1][1]) * 111320 * math.cos(math.radians(pts[i][0]))
            )
            total += math.sqrt(dlat**2 + dlon**2)
        return total
