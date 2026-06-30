"""
Swarm Communication Protocol — UDP broadcast for inter-drone communication.

Lightweight protocol for local network swarms. Uses UDP broadcast to
send messages to all drones in range without requiring a central server.

Key Features:
- UDP broadcast (no server required)
- JSON message format
- Automatic message timestamping
- Configurable port and broadcast address
- Thread-safe send/receive
- Message filtering by type
- Callback-based message handling

Message Format:
    {
        "sender": "drone_1",
        "type": "bid",
        "data": {"task_id": "T1", "bid": 15.5},
        "timestamp": 1234567890.123
    }

Usage:
    from skymeshx.communication.swarm_protocol import SwarmCommunicationProtocol
    
    def on_message(sender, msg_type, data, timestamp):
        print(f"Received {msg_type} from {sender}: {data}")
    
    protocol = SwarmCommunicationProtocol(
        drone_id="drone_1",
        port=5000,
        callback=on_message
    )
    
    protocol.start()
    protocol.broadcast("bid", {"task_id": "T1", "bid": 15.5})
    protocol.stop()
"""
from __future__ import annotations

import json
import logging
import socket
import threading
import time
from typing import Any, Callable, Dict, Optional

_log = logging.getLogger(__name__)


class SwarmCommunicationProtocol:
    """
    Lightweight UDP broadcast protocol for inter-drone communication.
    
    Enables drones to communicate without a central server by using
    UDP broadcast on the local network.
    
    Thread Safety:
        - start() and stop() are thread-safe
        - broadcast() is thread-safe
        - Callback is invoked from receiver thread
        - Multiple protocols can run on different ports
    
    Parameters:
        drone_id         : Unique identifier for this drone
        port             : UDP port for communication (default 5000)
        broadcast_addr   : Broadcast address (default '<broadcast>')
        callback         : Function called on message receipt
        buffer_size      : UDP receive buffer size (default 4096 bytes)
    """
    
    def __init__(
        self,
        drone_id: str,
        port: int = 5000,
        broadcast_addr: str = '<broadcast>',
        callback: Optional[Callable[[str, str, Dict[str, Any], float], None]] = None,
        buffer_size: int = 4096
    ):
        self.drone_id = drone_id
        self.port = port
        self.broadcast_addr = broadcast_addr
        self.callback = callback
        self.buffer_size = buffer_size
        
        self._socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Statistics
        self._messages_sent = 0
        self._messages_received = 0
        self._bytes_sent = 0
        self._bytes_received = 0
        self._last_message_time = 0.0
    
    def start(self) -> bool:
        """
        Start listening for messages.
        
        Returns:
            True if started successfully, False if already running
        """
        with self._lock:
            if self._running:
                return False
            
            try:
                # Create UDP socket
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                # Bind to port (listen on all interfaces)
                self._socket.bind(('', self.port))
                
                # Set timeout for non-blocking receive
                self._socket.settimeout(0.5)
                
                # Start receiver thread
                self._running = True
                self._thread = threading.Thread(
                    target=self._receive_loop,
                    daemon=True,
                    name=f"SwarmComm-{self.drone_id}"
                )
                self._thread.start()
                
                return True
                
            except Exception as e:
                _log.error("[SwarmComm] Failed to start: %s", e)
                self._running = False
                if self._socket:
                    self._socket.close()
                    self._socket = None
                return False
    
    def stop(self):
        """Stop listening and clean up resources."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            # Close the socket while holding the lock so that broadcast() and
            # _receive_loop() cannot use it after we set _running=False.
            if self._socket:
                try:
                    self._socket.close()
                except Exception:
                    pass
                self._socket = None

        # Wait for receiver thread to finish outside the lock.
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
    
    def broadcast(self, message_type: str, data: Dict[str, Any]) -> bool:
        """
        Broadcast a message to all drones in range.

        Args:
            message_type : Type of message (e.g., "bid", "task", "status")
            data         : Message payload (must be JSON-serializable)

        Returns:
            True if sent successfully, False otherwise

        Thread Safety:
            Safe to call from multiple threads concurrently.
        """
        # Acquire the lock to read both _running and _socket atomically so
        # that stop() cannot close the socket between our check and sendto().
        with self._lock:
            if not self._running or not self._socket:
                return False
            sock = self._socket

        try:
            message = {
                'sender': self.drone_id,
                'type': message_type,
                'data': data,
                'timestamp': time.time()
            }
            payload = json.dumps(message).encode('utf-8')
            sock.sendto(payload, (self.broadcast_addr, self.port))

            with self._lock:
                self._messages_sent += 1
                self._bytes_sent += len(payload)

            return True

        except Exception as e:
            _log.warning("[SwarmComm] Broadcast failed: %s", e)
            return False
    
    def _receive_loop(self):
        """Background thread that receives messages."""
        while self._running:
            # Snapshot the socket under lock; stop() may clear it at any time.
            with self._lock:
                sock = self._socket
            if sock is None:
                break
            try:
                data, addr = sock.recvfrom(self.buffer_size)
                
                # Update statistics
                with self._lock:
                    self._messages_received += 1
                    self._bytes_received += len(data)
                    self._last_message_time = time.time()
                
                # Parse message
                try:
                    message = json.loads(data.decode('utf-8'))
                    
                    # Extract fields
                    sender = message.get('sender')
                    msg_type = message.get('type')
                    msg_data = message.get('data', {})
                    timestamp = message.get('timestamp', 0.0)
                    
                    # Ignore messages from self
                    if sender == self.drone_id:
                        continue
                    
                    # Call user callback
                    if self.callback and sender and msg_type:
                        try:
                            self.callback(sender, msg_type, msg_data, timestamp)
                        except Exception as e:
                                _log.warning("[SwarmComm] Callback error: %s", e)
                
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    _log.debug("[SwarmComm] Invalid message format: %s", e)
                    continue

            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    _log.warning("[SwarmComm] Receive error: %s", e)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get communication statistics.
        
        Returns:
            Dictionary with:
            - messages_sent: Total messages sent
            - messages_received: Total messages received
            - bytes_sent: Total bytes sent
            - bytes_received: Total bytes received
            - last_message_time: Timestamp of last received message
            - is_running: Whether protocol is active
        """
        with self._lock:
            return {
                "messages_sent": self._messages_sent,
                "messages_received": self._messages_received,
                "bytes_sent": self._bytes_sent,
                "bytes_received": self._bytes_received,
                "last_message_time": self._last_message_time,
                "is_running": self._running
            }
    
    def __enter__(self):
        """Context manager support."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        self.stop()
        return False
