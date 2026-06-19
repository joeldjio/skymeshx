"""Regression: MAVLinkConnection.goto() must use SET_POSITION_TARGET_GLOBAL_INT
instead of the deprecated mission_item_send.
"""

from unittest.mock import MagicMock, patch

import pytest


def test_goto_uses_set_position_target_global_int():
    """goto() must call set_position_target_global_int_send, not mission_item_send."""
    from skymeshx.core.connection import MAVLinkConnection

    conn = MAVLinkConnection.__new__(MAVLinkConnection)
    # Minimal setup — bypass __init__
    conn._mav = MagicMock()
    conn._mav.target_system = 1
    conn._mav.target_component = 1
    conn._listeners = {}
    conn._cmd_lock = __import__("threading").Lock()
    conn._pending_cmds = {}
    conn.telemetry = MagicMock()

    conn.goto(47.123456, 11.654321, 20.0)

    conn._mav.mav.set_position_target_global_int_send.assert_called_once()
    conn._mav.mav.mission_item_send.assert_not_called()


def test_goto_encodes_lat_lon_correctly():
    """lat/lon must be encoded as int32 (degrees * 1e7)."""
    from skymeshx.core.connection import MAVLinkConnection

    conn = MAVLinkConnection.__new__(MAVLinkConnection)
    conn._mav = MagicMock()
    conn._mav.target_system = 1
    conn._mav.target_component = 1
    conn._listeners = {}
    conn._cmd_lock = __import__("threading").Lock()
    conn._pending_cmds = {}
    conn.telemetry = MagicMock()

    conn.goto(48.137, 11.575, 10.0)

    args = conn._mav.mav.set_position_target_global_int_send.call_args
    # lat_int is arg index 5, lon_int is arg index 6
    positional = args[0]
    lat_int = positional[5]
    lon_int = positional[6]
    assert lat_int == int(48.137 * 1e7)
    assert lon_int == int(11.575 * 1e7)


def test_goto_uses_relative_alt_frame():
    """Frame must be MAV_FRAME_GLOBAL_RELATIVE_ALT (6)."""
    from skymeshx.core.connection import MAVLinkConnection

    conn = MAVLinkConnection.__new__(MAVLinkConnection)
    conn._mav = MagicMock()
    conn._mav.target_system = 1
    conn._mav.target_component = 1
    conn._listeners = {}
    conn._cmd_lock = __import__("threading").Lock()
    conn._pending_cmds = {}
    conn.telemetry = MagicMock()

    conn.goto(0.0, 0.0, 15.0)

    args = conn._mav.mav.set_position_target_global_int_send.call_args[0]
    frame = args[3]  # 4th positional arg
    assert frame == 6, f"Expected MAV_FRAME_GLOBAL_RELATIVE_ALT (6), got {frame}"
