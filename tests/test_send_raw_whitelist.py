"""
Test send_raw() message type whitelist security feature.
"""
import pytest
from tests.conftest import FakeConnection


def test_send_raw_allows_whitelisted_messages(fake_conn):
    """Whitelisted message types should be allowed."""
    # These should not raise
    fake_conn.send_raw("heartbeat", type=0, autopilot=0, base_mode=0, custom_mode=0, system_status=0, mavlink_version=3)
    fake_conn.send_raw("command_long", command=400, param1=1, param2=0, param3=0, param4=0, param5=0, param6=0, param7=0)
    fake_conn.send_raw("set_position_target_global_int", time_boot_ms=0, target_system=1, target_component=1, 
                      coordinate_frame=6, type_mask=0x0FF8, lat_int=0, lon_int=0, alt=0, vx=0, vy=0, vz=0, 
                      afx=0, afy=0, afz=0, yaw=0, yaw_rate=0)


def test_send_raw_blocks_non_whitelisted_messages(fake_conn):
    """Non-whitelisted message types should raise ValueError."""
    with pytest.raises(ValueError, match="not in whitelist"):
        fake_conn.send_raw("arbitrary_dangerous_message", foo="bar")
    
    with pytest.raises(ValueError, match="not in whitelist"):
        fake_conn.send_raw("system_time", time_unix_usec=0, time_boot_ms=0)
    
    with pytest.raises(ValueError, match="not in whitelist"):
        fake_conn.send_raw("statustext", severity=0, text="test")


def test_send_raw_whitelist_contains_expected_messages():
    """Verify whitelist contains commonly used message types."""
    from skymeshx.core.connection import MAVLinkConnection
    
    expected = {
        "heartbeat",
        "command_long",
        "command_int",
        "set_position_target_global_int",
        "set_position_target_local_ned",
        "mission_item",
        "mission_count",
        "param_set",
    }
    
    assert expected.issubset(MAVLinkConnection.ALLOWED_RAW_MESSAGES)


def test_send_raw_error_message_shows_allowed_types(fake_conn):
    """Error message should list allowed message types."""
    with pytest.raises(ValueError) as exc_info:
        fake_conn.send_raw("bad_message")
    
    error_msg = str(exc_info.value)
    assert "not in whitelist" in error_msg
    assert "Allowed types:" in error_msg
    # Should show some whitelisted types
    assert "heartbeat" in error_msg or "command_long" in error_msg
