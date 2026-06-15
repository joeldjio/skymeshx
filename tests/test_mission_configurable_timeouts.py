"""Test configurable timeouts in MissionEngine."""

import pytest
from droneresearch.control.mission import MissionEngine, Waypoint


def test_default_timeouts(fake_conn):
    """Test that default timeout values are set correctly."""
    mission = MissionEngine(fake_conn)
    
    assert mission._handshake_timeout == 0.25
    assert mission._item_timeout == 3.0
    assert mission._ack_timeout == 5.0


def test_custom_timeouts(fake_conn):
    """Test that custom timeout values can be configured."""
    mission = MissionEngine(
        fake_conn,
        handshake_timeout=1.0,
        item_timeout=10.0,
        ack_timeout=15.0
    )
    
    assert mission._handshake_timeout == 1.0
    assert mission._item_timeout == 10.0
    assert mission._ack_timeout == 15.0


def test_timeout_used_in_upload(fake_conn, fake_mav):
    """Test that configured timeouts are actually used during upload."""
    # Use very short timeout to trigger timeout path
    mission = MissionEngine(fake_conn, handshake_timeout=0.01)
    mission.add(Waypoint(lat=48.0, lon=11.0, alt=20.0))
    
    # Upload should use push-all path due to short handshake timeout
    result = mission.upload()
    
    # Should succeed with push-all fallback
    assert result is True
    
    # Verify mission_count was sent
    assert len(fake_mav.sent) > 0
    assert fake_mav.sent[0][0] == "mission_count_send"


def test_longer_handshake_timeout(fake_conn, fake_mav):
    """Test that longer handshake timeout allows more time for response."""
    # Use longer timeout
    mission = MissionEngine(fake_conn, handshake_timeout=2.0)
    mission.add(Waypoint(lat=48.0, lon=11.0, alt=20.0))
    
    # Simulate delayed MISSION_REQUEST(0) after 0.5s
    import threading
    def delayed_request():
        import time
        time.sleep(0.5)
        # Trigger handshake path by setting event
        if 0 in mission._req_events:
            mission._req_events[0].set()
    
    threading.Thread(target=delayed_request, daemon=True).start()
    
    result = mission.upload()
    
    # Should succeed via handshake path
    assert result is True

# Made with Bob
