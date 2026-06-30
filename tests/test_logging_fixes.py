"""Tests for logging fixes: JSONL event logging and battery history persistence."""

import json
import tempfile
import time
from pathlib import Path

import pytest


class TestJSONLEventLogging:
    """Test that JSONL files are populated with actual events."""
    
    def test_drone_commands_logged_to_jsonl(self, tmp_path):
        """Verify that drone commands (arm, takeoff, etc.) are logged to JSONL."""
        from skymeshx.sdk.drone import Drone
        from tests.conftest import FakeConnection
        
        # Create drone with logging enabled
        fake_conn = FakeConnection()
        drone = Drone(fake_conn, drone_id="test_drone", log_dir=str(tmp_path), auto_log=True)
        
        # Connect to start logging
        drone.connect()
        
        # Simulate commands that should be logged
        drone.arm(force=False)
        drone.takeoff(altitude=10.0)
        drone.land()
        drone.rtl()
        
        # Stop logging
        drone.disconnect()
        
        # Check JSONL file exists and has content
        jsonl_files = list(tmp_path.glob("*_events.jsonl"))
        assert len(jsonl_files) == 1, "Expected one JSONL file"
        
        # Read and verify events
        lines = jsonl_files[0].read_text().strip().splitlines()
        assert len(lines) >= 4, f"Expected at least 4 events, got {len(lines)}"
        
        events = [json.loads(line) for line in lines]
        event_names = [e["event"] for e in events]
        
        # Verify expected events are present
        assert "arm_command" in event_names
        assert "takeoff_command" in event_names
        assert "land_command" in event_names
        assert "rtl_command" in event_names
    
    def test_armed_state_changes_logged(self, tmp_path):
        """Verify that armed/disarmed state changes are logged."""
        from skymeshx.sdk.drone import Drone
        from tests.conftest import FakeConnection
        
        fake_conn = FakeConnection()
        drone = Drone(fake_conn, drone_id="test_drone", log_dir=str(tmp_path), auto_log=True)
        drone.connect()
        
        # Simulate armed state change
        fake_conn._telemetry.armed = True
        fake_conn._emit("armed", True)
        time.sleep(0.1)  # Allow event to be processed
        
        fake_conn._telemetry.armed = False
        fake_conn._emit("armed", False)
        time.sleep(0.1)
        
        drone.disconnect()
        
        # Check events
        jsonl_files = list(tmp_path.glob("*_events.jsonl"))
        lines = jsonl_files[0].read_text().strip().splitlines()
        events = [json.loads(line) for line in lines]
        event_names = [e["event"] for e in events]
        
        assert "armed" in event_names
        assert "disarmed" in event_names


class TestBatteryHistoryPersistence:
    """Test that battery history is saved periodically and on shutdown."""
    
    def test_battery_history_auto_save(self, tmp_path):
        """Verify that battery history is auto-saved periodically."""
        from skymeshx.safety.battery_monitor import BatteryMonitor
        
        history_path = tmp_path / "battery_history.json"
        
        # Create monitor with short auto-save interval for testing
        monitor = BatteryMonitor(
            persistence_path=str(history_path),
            auto_save_interval=0.5  # 0.5 second for testing
        )
        
        # Start monitoring and add some samples
        monitor.start_monitoring("test_drone")
        
        for i in range(5):
            monitor.update("test_drone", {
                "battery_pct": 100 - i,
                "lat": 47.0 + i * 0.0001,
                "lon": 8.0 + i * 0.0001,
                "alt_rel": 10.0
            })
            time.sleep(0.15)  # Total 0.75s > 0.5s interval
        
        # Wait a bit more for auto-save thread to complete
        time.sleep(0.3)
        
        # Verify file was created
        assert history_path.exists(), "Battery history file should be auto-saved"
        
        # Verify content
        with open(history_path) as f:
            data = json.load(f)
        
        assert "test_drone" in data
        assert len(data["test_drone"]) > 0
        
        # Cleanup
        monitor.shutdown()
    
    def test_battery_history_saved_on_shutdown(self, tmp_path):
        """Verify that battery history is saved when monitor is shut down."""
        from skymeshx.safety.battery_monitor import BatteryMonitor
        
        history_path = tmp_path / "battery_history.json"
        
        # Create monitor with long auto-save interval (won't trigger during test)
        monitor = BatteryMonitor(
            persistence_path=str(history_path),
            auto_save_interval=3600.0  # 1 hour
        )
        
        monitor.start_monitoring("test_drone")
        
        # Add samples
        for i in range(3):
            monitor.update("test_drone", {
                "battery_pct": 100 - i * 5,
                "lat": 47.0,
                "lon": 8.0,
                "alt_rel": 10.0
            })
        
        # File should not exist yet (auto-save hasn't triggered)
        assert not history_path.exists(), "File should not exist before shutdown"
        
        # Shutdown should save
        monitor.shutdown()
        
        # Now file should exist
        assert history_path.exists(), "Battery history should be saved on shutdown"
        
        # Verify content
        with open(history_path) as f:
            data = json.load(f)
        
        assert "test_drone" in data
        assert len(data["test_drone"]) == 3
    
    def test_battery_history_loaded_on_init(self, tmp_path):
        """Verify that existing battery history is loaded on initialization."""
        from skymeshx.safety.battery_monitor import BatteryMonitor, PowerSample
        
        history_path = tmp_path / "battery_history.json"
        
        # Create initial history
        initial_data = {
            "drone1": [
                {
                    "timestamp": time.time(),
                    "battery_pct": 95.0,
                    "position": [47.0, 8.0, 10.0],
                    "distance_traveled": 0.0
                }
            ]
        }
        
        with open(history_path, 'w') as f:
            json.dump(initial_data, f)
        
        # Create monitor - should load existing history
        monitor = BatteryMonitor(
            persistence_path=str(history_path),
            auto_save_interval=3600.0
        )
        
        # Verify history was loaded
        history = monitor.get_history("drone1")
        assert len(history) == 1
        assert history[0].battery_pct == 95.0
        
        monitor.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
