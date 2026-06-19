"""Regression: GenericUAVModel._sync_armed() and _sync_mode() must advance
the FSM when reconnecting to an already-armed / airborne drone.

Previously both callbacks only handled the normal arm/disarm sequence and
left the FSM stuck at IDLE after a reconnect.
"""

from unittest.mock import MagicMock, patch

import pytest

from skymeshx.core.fsm import DroneState


def _make_uav(armed=False, alt=0.0, mode="STABILIZE"):
    """Build a GenericUAVModel without a real MAVLink connection."""
    with patch("skymeshx.sdk.drone.MAVLinkConnection") as MockConn:
        instance = MockConn.return_value
        from skymeshx.core.telemetry import TelemetryState

        tel = TelemetryState()
        tel.update(armed=armed, alt_rel=alt, flight_mode=mode)
        instance.telemetry = tel
        instance.connected = True
        instance.on = MagicMock()

        from skymeshx.models.generic_uav import GenericUAVModel

        uav = GenericUAVModel.__new__(GenericUAVModel)
        uav.id = "D_test"
        uav._conn = instance
        uav._logger = None
        uav._store = MagicMock()
        uav._mission = MagicMock()
        uav._event_cbs = {}
        uav._stop = __import__("threading").Event()
        from skymeshx.core.fsm import StateMachine

        uav.fsm = StateMachine("D_test")
        uav.swarm_role = "none"
        uav.leader_id = None
        uav.formation_offset = (0.0, 0.0, 0.0)
        uav.swarm_id = None
        uav._mission_thread = None
    return uav


class TestReconnectFSMSync:
    def test_armed_drone_on_reconnect_advances_to_armed(self):
        uav = _make_uav(armed=False, alt=0.0)
        assert uav.fsm.state == DroneState.IDLE
        # Simulate reconnect: autopilot reports armed=True
        uav._conn.telemetry.update(armed=True, alt_rel=0.0)
        uav._sync_armed(True)
        assert uav.fsm.state == DroneState.ARMED

    def test_airborne_drone_on_reconnect_advances_to_flying(self):
        uav = _make_uav(armed=False, alt=0.0)
        assert uav.fsm.state == DroneState.IDLE
        uav._conn.telemetry.update(armed=True, alt_rel=15.0)
        uav._sync_armed(True)
        assert uav.fsm.state == DroneState.FLYING

    def test_mode_change_on_already_flying_advances_fsm(self):
        uav = _make_uav(armed=False, alt=0.0)
        assert uav.fsm.state == DroneState.IDLE
        uav._conn.telemetry.update(armed=True, alt_rel=10.0)
        uav._sync_mode("GUIDED")
        assert uav.fsm.state == DroneState.FLYING

    def test_normal_disarm_resets_to_idle(self):
        uav = _make_uav()
        uav.fsm.transition(DroneState.ARMING)
        uav.fsm.transition(DroneState.ARMED)
        uav.fsm.transition(DroneState.TAKEOFF)
        uav.fsm.transition(DroneState.FLYING)
        uav.fsm.transition(DroneState.LANDING, force=True)
        uav._conn.telemetry.update(alt_rel=0.0)
        uav._sync_armed(False)
        assert uav.fsm.state == DroneState.IDLE
