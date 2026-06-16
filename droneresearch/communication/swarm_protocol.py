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
    from droneresearch.communication.swarm_protocol import SwarmCommunicationProtocol
    
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
import socket
import threading
import time
from typing import Any, Callable, Dict, Optional


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
                print(f"[SwarmComm] Failed to start: {e}")
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
        
        # Wait for receiver thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        # Close socket
        if self._socket:
            self._socket.close()
            self._socket = None
    
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
        if not self._running or not self._socket:
            return False
        
        try:
            # Build message
            message = {
                'sender': self.drone_id,
                'type': message_type,
                'data': data,
                'timestamp': time.time()
            }
            
            # Serialize to JSON
            payload = json.dumps(message).encode('utf-8')
            
            # Send broadcast
            self._socket.sendto(payload, (self.broadcast_addr, self.port))
            
            # Update statistics
            with self._lock:
                self._messages_sent += 1
                self._bytes_sent += len(payload)
            
            return True
            
        except Exception as e:
            print(f"[SwarmComm] Broadcast failed: {e}")
            return False
    
    def _receive_loop(self):
        """Background thread that receives messages."""
        while self._running:
            try:
                # Receive message (with timeout)
                data, addr = self._socket.recvfrom(self.buffer_size)
                
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
                            print(f"[SwarmComm] Callback error: {e}")
                
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"[SwarmComm] Invalid message format: {e}")
                    continue
                
            except socket.timeout:
                # Normal timeout, continue loop
                continue
            except Exception as e:
                if self._running:
                    print(f"[SwarmComm] Receive error: {e}")
    
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

# Made with Bob
