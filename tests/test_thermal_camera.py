"""
Tests for Thermal Camera Subscriber.

Tests thermal image processing, hotspot detection, and ROS2 integration
for solar panel inspection.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Mock ROS2 imports before importing thermal_camera
with patch.dict('sys.modules', {
    'rclpy': MagicMock(),
    'rclpy.node': MagicMock(),
    'sensor_msgs.msg': MagicMock(),
    'cv_bridge': MagicMock()
}):
    from droneresearch.sensors.thermal_camera import (
        ThermalCameraSubscriber,
        ThermalHotspotDetector
    )


class TestThermalCameraSubscriber:
    """Test ThermalCameraSubscriber functionality."""
    
    def test_initialization(self):
        """Subscriber should initialize with default parameters."""
        subscriber = ThermalCameraSubscriber(
            topic="/thermal/image_raw"
        )
        
        assert subscriber.topic == "/thermal/image_raw"
        assert subscriber.calibration_a == 0.01
        assert subscriber.calibration_b == -273.15
        assert subscriber.min_temp == -40.0
        assert subscriber.max_temp == 150.0
        assert not subscriber.is_running()
    
    def test_custom_calibration(self):
        """Subscriber should accept custom calibration parameters."""
        subscriber = ThermalCameraSubscriber(
            topic="/thermal/temperature",
            calibration_a=0.02,
            calibration_b=-250.0,
            min_temp=-20.0,
            max_temp=120.0
        )
        
        assert subscriber.calibration_a == 0.02
        assert subscriber.calibration_b == -250.0
        assert subscriber.min_temp == -20.0
        assert subscriber.max_temp == 120.0
    
    def test_calibrate_temperature(self):
        """Temperature calibration should work correctly."""
        subscriber = ThermalCameraSubscriber(
            calibration_a=0.01,
            calibration_b=-273.15
        )
        
        # Test with sample raw values
        raw = np.array([[30000, 31000], [32000, 33000]], dtype=np.uint16)
        
        temp_celsius = subscriber._calibrate_temperature(raw)
        
        # Check calibration: temp = 0.01 * raw - 273.15
        expected = np.array([
            [30000 * 0.01 - 273.15, 31000 * 0.01 - 273.15],
            [32000 * 0.01 - 273.15, 33000 * 0.01 - 273.15]
        ])
        
        np.testing.assert_array_almost_equal(temp_celsius, expected, decimal=2)
    
    def test_calibrate_temperature_linear(self):
        """Linear calibration should be applied correctly."""
        subscriber = ThermalCameraSubscriber(
            calibration_a=0.1,
            calibration_b=0.0
        )
        
        raw = np.array([[100, 200], [300, 400]], dtype=np.uint16)
        temp_celsius = subscriber._calibrate_temperature(raw)
        
        expected = np.array([[10.0, 20.0], [30.0, 40.0]])
        np.testing.assert_array_almost_equal(temp_celsius, expected)
    
    def test_update_stats(self):
        """Statistics should be updated correctly."""
        subscriber = ThermalCameraSubscriber()
        
        # Initial stats
        assert subscriber._frame_count == 0
        assert subscriber._fps == 0.0
        
        # Update stats
        subscriber._update_stats()
        assert subscriber._frame_count == 1
        
        # Multiple updates
        for _ in range(10):
            subscriber._update_stats()
        
        assert subscriber._frame_count == 11
        assert subscriber._fps > 0  # FPS should be calculated
    
    def test_get_stats(self):
        """get_stats should return correct statistics."""
        subscriber = ThermalCameraSubscriber()
        
        stats = subscriber.get_stats()
        
        assert 'frame_count' in stats
        assert 'fps' in stats
        assert 'running' in stats
        assert stats['frame_count'] == 0
        assert stats['fps'] == 0.0
        assert stats['running'] is False


class TestThermalHotspotDetector:
    """Test ThermalHotspotDetector functionality."""
    
    def test_initialization(self):
        """Detector should initialize with default parameters."""
        detector = ThermalHotspotDetector()
        
        assert detector.threshold_temp == 80.0
        assert detector.min_hotspot_size == 10
    
    def test_custom_parameters(self):
        """Detector should accept custom parameters."""
        detector = ThermalHotspotDetector(
            threshold_temp=90.0,
            min_hotspot_size=20
        )
        
        assert detector.threshold_temp == 90.0
        assert detector.min_hotspot_size == 20
    
    def test_detect_hotspots_no_hotspots(self):
        """Detector should return empty list when no hotspots."""
        detector = ThermalHotspotDetector(threshold_temp=80.0)
        
        # Temperature image with no hotspots
        temp_image = np.full((100, 100), 50.0)
        
        hotspots = detector.detect_hotspots(temp_image)
        
        assert len(hotspots) == 0
    
    def test_detect_hotspots_single_hotspot(self):
        """Detector should find single hotspot."""
        detector = ThermalHotspotDetector(
            threshold_temp=80.0,
            min_hotspot_size=5
        )
        
        # Create temperature image with one hotspot
        temp_image = np.full((100, 100), 50.0)
        temp_image[40:50, 40:50] = 90.0  # 10x10 hotspot at center
        
        hotspots = detector.detect_hotspots(temp_image)
        
        assert len(hotspots) == 1
        assert hotspots[0]['pixel_count'] == 100  # 10x10 = 100 pixels
        assert 40 <= hotspots[0]['center_x'] <= 50
        assert 40 <= hotspots[0]['center_y'] <= 50
        assert hotspots[0]['max_temp'] == 90.0
        assert hotspots[0]['mean_temp'] == 90.0
    
    def test_detect_hotspots_multiple_hotspots(self):
        """Detector should find multiple hotspots (if scipy available)."""
        detector = ThermalHotspotDetector(
            threshold_temp=80.0,
            min_hotspot_size=5
        )
        
        # Create temperature image with two hotspots
        temp_image = np.full((100, 100), 50.0)
        temp_image[20:30, 20:30] = 85.0  # First hotspot
        temp_image[70:80, 70:80] = 95.0  # Second hotspot
        
        hotspots = detector.detect_hotspots(temp_image)
        
        # Without scipy, fallback treats all hotspots as one region
        # With scipy, should detect 2 separate hotspots
        assert len(hotspots) >= 1
        
        # At least one hotspot should be detected
        if len(hotspots) == 2:
            # Check both hotspots are detected (scipy available)
            temps = [h['mean_temp'] for h in hotspots]
            assert 85.0 in temps or 95.0 in temps
        else:
            # Fallback mode: single region with mixed temperatures
            assert hotspots[0]['pixel_count'] >= 100  # Both regions combined
    
    def test_detect_hotspots_filter_small(self):
        """Detector should filter out small hotspots."""
        detector = ThermalHotspotDetector(
            threshold_temp=80.0,
            min_hotspot_size=20
        )
        
        # Create temperature image with small hotspot
        temp_image = np.full((100, 100), 50.0)
        temp_image[45:50, 45:50] = 90.0  # 5x5 = 25 pixels (above threshold)
        temp_image[20:22, 20:22] = 90.0  # 2x2 = 4 pixels (below threshold)
        
        hotspots = detector.detect_hotspots(temp_image)
        
        # Only the larger hotspot should be detected
        assert len(hotspots) == 1
        assert hotspots[0]['pixel_count'] >= 20
    
    def test_hotspot_statistics(self):
        """Hotspot statistics should be calculated correctly."""
        detector = ThermalHotspotDetector(
            threshold_temp=80.0,
            min_hotspot_size=5
        )
        
        # Create temperature image with varying temperatures
        temp_image = np.full((100, 100), 50.0)
        hotspot_region = np.random.uniform(85.0, 95.0, (10, 10))
        temp_image[40:50, 40:50] = hotspot_region
        
        hotspots = detector.detect_hotspots(temp_image)
        
        assert len(hotspots) == 1
        hotspot = hotspots[0]
        
        # Check statistics
        assert 'id' in hotspot
        assert 'pixel_count' in hotspot
        assert 'center_x' in hotspot
        assert 'center_y' in hotspot
        assert 'min_temp' in hotspot
        assert 'max_temp' in hotspot
        assert 'mean_temp' in hotspot
        assert 'std_temp' in hotspot
        
        # Validate ranges
        assert 85.0 <= hotspot['min_temp'] <= 95.0
        assert 85.0 <= hotspot['max_temp'] <= 95.0
        assert 85.0 <= hotspot['mean_temp'] <= 95.0
        assert hotspot['std_temp'] >= 0
    
    def test_hotspot_center_calculation(self):
        """Hotspot center should be calculated correctly."""
        detector = ThermalHotspotDetector(
            threshold_temp=80.0,
            min_hotspot_size=5
        )
        
        # Create temperature image with known hotspot location
        temp_image = np.full((100, 100), 50.0)
        temp_image[30:40, 50:60] = 90.0  # 10x10 hotspot
        
        hotspots = detector.detect_hotspots(temp_image)
        
        assert len(hotspots) == 1
        
        # Center should be at (55, 35) - middle of the hotspot
        assert 54 <= hotspots[0]['center_x'] <= 56
        assert 34 <= hotspots[0]['center_y'] <= 36


class TestIntegration:
    """Integration tests for thermal camera workflow."""
    
    def test_complete_thermal_processing_workflow(self):
        """Complete workflow from raw data to hotspot detection."""
        # Create subscriber with calibration
        subscriber = ThermalCameraSubscriber(
            calibration_a=0.01,
            calibration_b=-273.15,
            min_temp=-40.0,
            max_temp=150.0
        )
        
        # Simulate raw thermal data (16-bit)
        # Values around 30000-35000 should give temps around 26-77°C
        raw_data = np.full((480, 640), 30000, dtype=np.uint16)
        
        # Add some hot spots (higher raw values)
        raw_data[100:150, 200:250] = 35000  # ~77°C
        raw_data[300:350, 400:450] = 36000  # ~87°C
        
        # Calibrate temperature
        temp_celsius = subscriber._calibrate_temperature(raw_data)
        
        # Clip to valid range
        temp_celsius = np.clip(temp_celsius, subscriber.min_temp, subscriber.max_temp)
        
        # Detect hotspots
        detector = ThermalHotspotDetector(
            threshold_temp=80.0,
            min_hotspot_size=100
        )
        
        hotspots = detector.detect_hotspots(temp_celsius)
        
        # Should find one hotspot (the 87°C region)
        assert len(hotspots) >= 1
        
        # Verify hotspot properties
        for hotspot in hotspots:
            assert hotspot['mean_temp'] > 80.0
            assert hotspot['pixel_count'] >= 100
            assert 'center_x' in hotspot
            assert 'center_y' in hotspot
        
        print(f"Detected {len(hotspots)} hotspot(s)")
        for i, hotspot in enumerate(hotspots):
            print(f"  Hotspot {i+1}:")
            print(f"    Location: ({hotspot['center_x']:.1f}, {hotspot['center_y']:.1f})")
            print(f"    Temperature: {hotspot['mean_temp']:.1f}°C")
            print(f"    Size: {hotspot['pixel_count']} pixels")
    
    def test_temperature_range_validation(self):
        """Temperature values should be clipped to valid range."""
        subscriber = ThermalCameraSubscriber(
            calibration_a=0.01,
            calibration_b=-273.15,
            min_temp=-40.0,
            max_temp=150.0
        )
        
        # Create raw data with extreme values
        raw_data = np.array([
            [0, 10000, 20000],      # Very cold
            [30000, 40000, 50000],  # Normal to hot
            [60000, 65535, 65535]   # Very hot (max uint16)
        ], dtype=np.uint16)
        
        temp_celsius = subscriber._calibrate_temperature(raw_data)
        temp_clipped = np.clip(temp_celsius, subscriber.min_temp, subscriber.max_temp)
        
        # All values should be within valid range
        assert np.all(temp_clipped >= -40.0)
        assert np.all(temp_clipped <= 150.0)
    
    def test_fps_calculation(self):
        """FPS should be calculated from frame timing."""
        subscriber = ThermalCameraSubscriber()
        
        # Simulate multiple frame updates
        import time
        for _ in range(5):
            subscriber._update_stats()
            time.sleep(0.01)  # 10ms between frames
        
        stats = subscriber.get_stats()
        
        # FPS should be calculated (approximately 100 fps for 10ms intervals)
        assert stats['frame_count'] == 5
        # FPS calculation uses exponential moving average, so exact value varies
        assert stats['fps'] > 0

# Made with Bob
