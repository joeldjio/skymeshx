"""
Tests for BatteryMonitor persistence (save/load history).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from skymeshx.safety.battery_monitor import BatteryMonitor, PowerSample


def test_save_load_empty_history():
    """Test save/load with no history."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        path = f.name
    
    try:
        monitor = BatteryMonitor(persistence_path=path)
        
        # Save empty history
        assert monitor.save_history() is True
        
        # Load should succeed
        assert monitor.load_history() is True
        
        # Verify file exists and is valid JSON
        with open(path, 'r') as f:
            data = json.load(f)
        assert data == {}
    finally:
        Path(path).unlink(missing_ok=True)


def test_save_load_single_drone():
    """Test save/load with single drone history."""
    # Create temp file and close it immediately
    f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    path = f.name
    f.close()
    
    try:
        monitor = BatteryMonitor(persistence_path=path)
        
        # Start monitoring and add samples
        monitor.start_monitoring("D1")
        monitor.update("D1", {"battery_pct": 100.0, "lat": 0, "lon": 0, "alt_rel": 10})
        monitor.update("D1", {"battery_pct": 95.0, "lat": 10, "lon": 0, "alt_rel": 10})
        monitor.update("D1", {"battery_pct": 90.0, "lat": 20, "lon": 0, "alt_rel": 10})
        
        # Save
        assert monitor.save_history() is True
        
        # Create new monitor and load
        monitor2 = BatteryMonitor(persistence_path=path)
        assert monitor2.load_history() is True
        
        # Verify history
        history = monitor2.get_history("D1")
        assert len(history) == 3
        assert history[0].battery_pct == 100.0
        assert history[1].battery_pct == 95.0
        assert history[2].battery_pct == 90.0
        assert history[0].position == (0, 0, 10)
        assert history[1].position == (10, 0, 10)
        assert history[2].position == (20, 0, 10)
    finally:
        Path(path).unlink(missing_ok=True)


def test_save_load_multiple_drones():
    """Test save/load with multiple drones."""
    # Create temp file and close it immediately
    f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    path = f.name
    f.close()
    
    try:
        monitor = BatteryMonitor(persistence_path=path, history_size=50)
        
        # Start monitoring and add samples for multiple drones
        monitor.start_monitoring("D1")
        monitor.start_monitoring("D2")
        monitor.start_monitoring("D3")
        for i in range(5):
            monitor.update("D1", {"battery_pct": 100 - i, "lat": i, "lon": 0, "alt_rel": 10})
            monitor.update("D2", {"battery_pct": 100 - i * 2, "lat": 0, "lon": i, "alt_rel": 10})
            monitor.update("D3", {"battery_pct": 100 - i * 3, "lat": i, "lon": i, "alt_rel": 10})
        
        # Save
        assert monitor.save_history() is True
        
        # Load into new monitor
        monitor2 = BatteryMonitor(persistence_path=path, history_size=50)
        assert monitor2.load_history() is True
        
        # Verify all drones
        h1 = monitor2.get_history("D1")
        h2 = monitor2.get_history("D2")
        h3 = monitor2.get_history("D3")
        
        assert len(h1) == 5
        assert len(h2) == 5
        assert len(h3) == 5
        
        assert h1[-1].battery_pct == 96.0
        assert h2[-1].battery_pct == 92.0
        assert h3[-1].battery_pct == 88.0
    finally:
        Path(path).unlink(missing_ok=True)


def test_auto_load_on_init():
    """Test that history is automatically loaded on init."""
    # Create temp file and close it immediately
    f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    path = f.name
    f.close()
    
    try:
        # Create and populate monitor
        monitor1 = BatteryMonitor(persistence_path=path)
        monitor1.start_monitoring("D1")
        monitor1.update("D1", {"battery_pct": 100.0, "lat": 0, "lon": 0, "alt_rel": 10})
        monitor1.update("D1", {"battery_pct": 95.0, "lat": 10, "lon": 0, "alt_rel": 10})
        monitor1.save_history()
        
        # Create new monitor - should auto-load
        monitor2 = BatteryMonitor(persistence_path=path)
        history = monitor2.get_history("D1")
        
        assert len(history) == 2
        assert history[0].battery_pct == 100.0
        assert history[1].battery_pct == 95.0
    finally:
        Path(path).unlink(missing_ok=True)


def test_no_persistence_path():
    """Test that save/load return False when no path configured."""
    monitor = BatteryMonitor()  # No persistence_path
    
    assert monitor.save_history() is False
    assert monitor.load_history() is False


def test_load_nonexistent_file():
    """Test loading from nonexistent file."""
    monitor = BatteryMonitor(persistence_path="/tmp/nonexistent_battery_history.json")
    
    # Should return False but not crash
    assert monitor.load_history() is False


def test_history_size_limit():
    """Test that history respects size limit after load."""
    # Create temp file and close it immediately
    f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    path = f.name
    f.close()
    
    try:
        # Create monitor with large history
        monitor1 = BatteryMonitor(persistence_path=path, history_size=100)
        monitor1.start_monitoring("D1")
        for i in range(150):  # Add more than limit
            monitor1.update("D1", {"battery_pct": 100 - i * 0.1, "lat": i, "lon": 0, "alt_rel": 10})
        monitor1.save_history()
        
        # Load with smaller limit
        monitor2 = BatteryMonitor(persistence_path=path, history_size=50)
        assert monitor2.load_history() is True
        
        history = monitor2.get_history("D1")
        # Should only keep last 50 samples (most recent)
        assert len(history) == 50
    finally:
        Path(path).unlink(missing_ok=True)


def test_get_set_history():
    """Test get_history and set_history methods."""
    monitor = BatteryMonitor()
    
    # Create sample history
    samples = [
        PowerSample(timestamp=1.0, battery_pct=100.0, position=(0, 0, 10), distance_traveled=0.0),
        PowerSample(timestamp=2.0, battery_pct=95.0, position=(10, 0, 10), distance_traveled=10.0),
        PowerSample(timestamp=3.0, battery_pct=90.0, position=(20, 0, 10), distance_traveled=10.0),
    ]
    
    # Set history
    monitor.set_history("D1", samples)
    
    # Get history
    history = monitor.get_history("D1")
    assert len(history) == 3
    assert history[0].battery_pct == 100.0
    assert history[1].battery_pct == 95.0
    assert history[2].battery_pct == 90.0
    
    # Verify it's a copy (modifying returned list doesn't affect internal state)
    history.append(PowerSample(timestamp=4.0, battery_pct=85.0, position=(30, 0, 10), distance_traveled=10.0))
    history2 = monitor.get_history("D1")
    assert len(history2) == 3  # Still 3, not 4


def test_corrupted_json():
    """Test handling of corrupted JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        path = f.name
        f.write("{ invalid json }")
    
    try:
        monitor = BatteryMonitor(persistence_path=path)
        
        # Should return False but not crash
        assert monitor.load_history() is False
    finally:
        Path(path).unlink(missing_ok=True)


def test_position_tuple_conversion():
    """Test that position lists are converted to tuples on load."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        path = f.name
        # Manually create JSON with position as list
        data = {
            "D1": [
                {
                    "timestamp": 1.0,
                    "battery_pct": 100.0,
                    "position": [10, 20, 30],  # List, not tuple
                    "distance_traveled": 0.0
                }
            ]
        }
        json.dump(data, f)
    
    try:
        
        # Load
        monitor = BatteryMonitor(persistence_path=path)
        assert monitor.load_history() is True
        
        # Verify position is tuple
        history = monitor.get_history("D1")
        assert len(history) == 1
        assert history[0].position == (10, 20, 30)
        assert isinstance(history[0].position, tuple)
    finally:
        Path(path).unlink(missing_ok=True)

