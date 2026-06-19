"""Regression: Swarm.formation() must assign distinct offsets to ALL followers
regardless of the leader's position in the drone list.

Previously, the loop used enumerate(drones) index to index into offsets[],
causing the last follower to always get offset (0,0) when the leader was not
at the tail of the list.
"""

import math

import pytest


class MockDrone:
    def __init__(self, did, lat=48.0, lon=11.0, alt=10.0):
        self.id = did
        self._lat = lat
        self._lon = lon
        self._alt = alt
        self.goto_calls = []
        self.connected = True
        self._conn = type("c", (), {"telemetry": type("t", (), {"armed": True})()})()

    @property
    def position(self):
        return (self._lat, self._lon, self._alt)

    def goto(self, lat, lon, alt, timeout=60.0):
        self.goto_calls.append((lat, lon, alt))
        return True

    @property
    def telemetry(self):
        return type("t", (), {"snapshot": lambda s: {}})()


def _make_swarm_with_leader_at(leader_idx: int, n: int = 4):
    """Build a Swarm with n drones, leader at position leader_idx."""
    from skymeshx.sdk.swarm_api import Swarm

    swarm = Swarm.__new__(Swarm)
    swarm._drones = {}
    swarm._lock = __import__("threading").Lock()
    swarm._event_cbs = {}
    swarm._following = False
    swarm._follow_thread = None

    drones = [MockDrone(f"D{i}") for i in range(n)]
    leader = drones[leader_idx]
    for d in drones:
        swarm._drones[d.id] = d
    return swarm, leader, drones


@pytest.mark.parametrize(
    "leader_idx,n",
    [
        (0, 4),  # leader first — classic case
        (1, 4),  # leader in middle
        (3, 4),  # leader last
        (0, 2),  # minimal swarm
        (0, 6),  # larger swarm
    ],
)
def test_all_followers_get_distinct_offsets(leader_idx, n):
    """Every non-leader drone must receive a GOTO with a non-zero offset."""
    swarm, leader, drones = _make_swarm_with_leader_at(leader_idx, n)

    import threading

    for t in list(swarm._drones.values()):
        t.goto_calls.clear()

    swarm.formation("line", spacing=5.0, leader=leader.id)
    # Give threads a moment to fire
    __import__("time").sleep(0.1)

    followers = [d for d in drones if d is not leader]
    assert len(followers) == n - 1

    # All followers must have received at least one goto call
    for f in followers:
        assert len(f.goto_calls) == 1, (
            f"Drone {f.id} (leader_idx={leader_idx}) got {len(f.goto_calls)} goto calls, expected 1"
        )

    # All follower target positions must differ from the leader position
    leader_lat, leader_lon, _ = leader.position
    for f in followers:
        tgt_lat, tgt_lon, _ = f.goto_calls[0]
        dist_m = math.sqrt(
            ((tgt_lat - leader_lat) * 111320) ** 2
            + ((tgt_lon - leader_lon) * 111320 * math.cos(math.radians(leader_lat)))
            ** 2
        )
        assert dist_m > 1.0, (
            f"Drone {f.id} target is too close to leader ({dist_m:.2f}m)"
        )

    # All follower targets must be mutually distinct
    targets = [f.goto_calls[0][:2] for f in followers]
    assert len(set(targets)) == len(targets), (
        f"Duplicate formation targets detected: {targets}"
    )
