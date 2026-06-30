"""
Test SwarmCommunicationProtocol functionality.

Tests:
- Protocol initialization
- Message broadcasting
- Message receiving
- Statistics tracking
- Thread safety
"""
import time
import threading

import pytest

from skymeshx.communication.swarm_protocol import SwarmCommunicationProtocol


def test_protocol_initialization():
    """Test protocol initialization."""
    protocol = SwarmCommunicationProtocol(
        drone_id="test_drone",
        port=5001,
        broadcast_addr='<broadcast>'
    )
    
    assert protocol.drone_id == "test_drone"
    assert protocol.port == 5001
    assert not protocol._running


def test_protocol_start_stop():
    """Test starting and stopping protocol."""
    protocol = SwarmCommunicationProtocol(drone_id="drone_1", port=5002)
    
    # Start protocol
    result = protocol.start()
    assert result is True
    assert protocol._running
    
    # Try to start again (should fail)
    result = protocol.start()
    assert result is False
    
    # Stop protocol
    protocol.stop()
    assert not protocol._running


def test_broadcast_message():
    """Test broadcasting a message."""
    protocol = SwarmCommunicationProtocol(drone_id="drone_1", port=5003)
    protocol.start()
    
    # Broadcast message
    result = protocol.broadcast("test", {"key": "value"})
    assert result is True
    
    # Check statistics
    stats = protocol.get_statistics()
    assert stats["messages_sent"] == 1
    assert stats["bytes_sent"] > 0
    
    protocol.stop()


def test_message_reception():
    """Test receiving messages from another drone."""
    received_messages = []
    
    def callback(sender, msg_type, data, timestamp):
        received_messages.append({
            "sender": sender,
            "type": msg_type,
            "data": data,
            "timestamp": timestamp
        })
    
    # Create two protocols on same port
    protocol1 = SwarmCommunicationProtocol(
        drone_id="drone_1",
        port=5004,
        callback=callback
    )
    protocol2 = SwarmCommunicationProtocol(
        drone_id="drone_2",
        port=5004
    )
    
    protocol1.start()
    protocol2.start()
    
    # Give time for sockets to bind
    time.sleep(0.1)
    
    # Drone 2 broadcasts message
    protocol2.broadcast("test_msg", {"value": 42})
    
    # Wait for message to be received
    time.sleep(0.5)
    
    # Check that drone 1 received the message
    assert len(received_messages) >= 1
    msg = received_messages[0]
    assert msg["sender"] == "drone_2"
    assert msg["type"] == "test_msg"
    assert msg["data"]["value"] == 42
    
    protocol1.stop()
    protocol2.stop()


def test_ignore_own_messages():
    """Test that drones ignore their own broadcast messages."""
    received_messages = []
    
    def callback(sender, msg_type, data, timestamp):
        received_messages.append(sender)
    
    protocol = SwarmCommunicationProtocol(
        drone_id="drone_1",
        port=5005,
        callback=callback
    )
    
    protocol.start()
    time.sleep(0.1)
    
    # Broadcast message
    protocol.broadcast("test", {"data": "value"})
    
    # Wait
    time.sleep(0.5)
    
    # Should not have received own message
    assert len(received_messages) == 0
    
    protocol.stop()


def test_statistics():
    """Test statistics tracking."""
    protocol = SwarmCommunicationProtocol(drone_id="drone_1", port=5006)
    protocol.start()
    
    # Send multiple messages
    for i in range(5):
        protocol.broadcast("test", {"count": i})
    
    stats = protocol.get_statistics()
    assert stats["messages_sent"] == 5
    assert stats["bytes_sent"] > 0
    assert stats["is_running"] is True
    
    protocol.stop()


def test_context_manager():
    """Test context manager support."""
    with SwarmCommunicationProtocol(drone_id="drone_1", port=5007) as protocol:
        assert protocol._running
        protocol.broadcast("test", {"data": "value"})
    
    # Should be stopped after context exit
    assert not protocol._running


def test_concurrent_broadcasts():
    """Test thread-safe concurrent broadcasts."""
    protocol = SwarmCommunicationProtocol(drone_id="drone_1", port=5008)
    protocol.start()
    
    def broadcast_messages(count):
        for i in range(count):
            protocol.broadcast("test", {"value": i})
    
    # Create multiple threads broadcasting concurrently
    threads = []
    for i in range(3):
        t = threading.Thread(target=broadcast_messages, args=(10,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Should have sent 30 messages total
    stats = protocol.get_statistics()
    assert stats["messages_sent"] == 30
    
    protocol.stop()


def test_multi_drone_communication():
    """Test communication between multiple drones."""
    messages_d1 = []
    messages_d2 = []
    messages_d3 = []
    
    def callback_d1(sender, msg_type, data, timestamp):
        messages_d1.append((sender, msg_type, data))
    
    def callback_d2(sender, msg_type, data, timestamp):
        messages_d2.append((sender, msg_type, data))
    
    def callback_d3(sender, msg_type, data, timestamp):
        messages_d3.append((sender, msg_type, data))
    
    # Create 3 drones
    d1 = SwarmCommunicationProtocol("drone_1", port=5009, callback=callback_d1)
    d2 = SwarmCommunicationProtocol("drone_2", port=5009, callback=callback_d2)
    d3 = SwarmCommunicationProtocol("drone_3", port=5009, callback=callback_d3)
    
    d1.start()
    d2.start()
    d3.start()
    
    time.sleep(0.1)
    
    # Each drone broadcasts a message
    d1.broadcast("status", {"battery": 75})
    d2.broadcast("status", {"battery": 80})
    d3.broadcast("status", {"battery": 90})
    
    # Wait for messages to propagate
    time.sleep(0.5)
    
    # Each drone should have received 2 messages (from the other 2 drones)
    assert len(messages_d1) == 2
    assert len(messages_d2) == 2
    assert len(messages_d3) == 2
    
    # Verify senders
    senders_d1 = {msg[0] for msg in messages_d1}
    assert senders_d1 == {"drone_2", "drone_3"}
    
    d1.stop()
    d2.stop()
    d3.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
