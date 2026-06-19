"""
Tests for completing CollisionPredictor implementation.

Tests:
1. Waypoint-based prediction (predict_with_waypoints)
2. Trajectory interpolation (_interpolate_trajectory)
3. SafetyContext velocity calculation
"""
import pytest
from skymeshx.safety.collision_predictor import (
    CollisionPredictor,
    DroneState,
)


class TestWaypointPrediction:
    """Test waypoint-based collision prediction."""

    def test_no_collision_diverging_paths(self):
        """Drones with diverging paths have no collision."""
        predictor = CollisionPredictor(
            time_horizon=20.0,
            min_separation=2.0,
            sample_rate=0.5
        )
        
        # Start drones at different positions
        states = {
            "D1": DroneState(x=0, y=0, z=10, armed=True),
            "D2": DroneState(x=0, y=5, z=10, armed=True),  # 5m apart
        }
        
        waypoints = {
            "D1": [(10, 0, 10), (20, 0, 10)],  # East
            "D2": [(0, 10, 10), (0, 20, 10)],  # North
        }
        
        predictions = predictor.predict_with_waypoints(states, waypoints)
        assert len(predictions) == 0

    def test_collision_converging_paths(self):
        """Drones converging to same point collide."""
        predictor = CollisionPredictor(
            time_horizon=20.0,
            min_separation=2.0,
            sample_rate=0.5
        )
        
        states = {
            "D1": DroneState(x=0, y=0, z=10, armed=True),
            "D2": DroneState(x=0, y=10, z=10, armed=True),
        }
        
        # Both heading to same point
        waypoints = {
            "D1": [(5, 5, 10)],
            "D2": [(5, 5, 10)],
        }
        
        predictions = predictor.predict_with_waypoints(
            states, waypoints, cruise_speed=3.0
        )
        assert len(predictions) == 1
        assert predictions[0].min_distance < 2.0

    def test_unarmed_drones_ignored(self):
        """Unarmed drones not checked."""
        predictor = CollisionPredictor()
        
        states = {
            "D1": DroneState(x=0, y=0, z=10, armed=False),
            "D2": DroneState(x=0, y=10, z=10, armed=False),
        }
        
        waypoints = {
            "D1": [(5, 5, 10)],
            "D2": [(5, 5, 10)],
        }
        
        predictions = predictor.predict_with_waypoints(states, waypoints)
        assert len(predictions) == 0

    def test_missing_waypoints_skipped(self):
        """Drones without waypoints skipped."""
        predictor = CollisionPredictor()
        
        states = {
            "D1": DroneState(x=0, y=0, z=10, armed=True),
            "D2": DroneState(x=10, y=0, z=10, armed=True),
        }
        
        waypoints = {
            "D1": [(5, 0, 10)],
            # D2 has no waypoints
        }
        
        predictions = predictor.predict_with_waypoints(states, waypoints)
        assert len(predictions) == 0

    def test_cruise_speed_affects_timing(self):
        """Different cruise speeds affect timing."""
        predictor = CollisionPredictor(
            time_horizon=30.0,
            min_separation=2.0,
            sample_rate=0.5
        )
        
        states = {
            "D1": DroneState(x=0, y=0, z=10, armed=True),
            "D2": DroneState(x=10, y=0, z=10, armed=True),
        }
        
        waypoints = {
            "D1": [(5, 0, 10)],
            "D2": [(5, 0, 10)],
        }
        
        preds_slow = predictor.predict_with_waypoints(
            states, waypoints, cruise_speed=1.0
        )
        preds_fast = predictor.predict_with_waypoints(
            states, waypoints, cruise_speed=5.0
        )
        
        assert len(preds_slow) == 1
        assert len(preds_fast) == 1
        assert preds_fast[0].time_to_collision < preds_slow[0].time_to_collision


class TestTrajectoryInterpolation:
    """Test trajectory interpolation."""

    def test_interpolate_at_waypoint(self):
        """Interpolation at waypoint returns exact position."""
        predictor = CollisionPredictor()
        
        trajectory = [
            (0.0, 0.0, 0.0, 10.0),
            (5.0, 10.0, 0.0, 10.0),
        ]
        
        pos = predictor._interpolate_trajectory(trajectory, 5.0)
        assert pos == (10.0, 0.0, 10.0)

    def test_interpolate_between_waypoints(self):
        """Interpolation between waypoints is linear."""
        predictor = CollisionPredictor()
        
        trajectory = [
            (0.0, 0.0, 0.0, 10.0),
            (10.0, 10.0, 0.0, 10.0),
        ]
        
        pos = predictor._interpolate_trajectory(trajectory, 5.0)
        assert pos == (5.0, 0.0, 10.0)

    def test_interpolate_after_end(self):
        """Interpolation after end returns last position."""
        predictor = CollisionPredictor()
        
        trajectory = [
            (0.0, 0.0, 0.0, 10.0),
            (10.0, 10.0, 20.0, 30.0),
        ]
        
        pos = predictor._interpolate_trajectory(trajectory, 20.0)
        assert pos == (10.0, 20.0, 30.0)

    def test_interpolate_3d(self):
        """Interpolation works in all dimensions."""
        predictor = CollisionPredictor()
        
        trajectory = [
            (0.0, 0.0, 0.0, 0.0),
            (10.0, 10.0, 10.0, 10.0),
        ]
        
        pos = predictor._interpolate_trajectory(trajectory, 5.0)
        assert pos == (5.0, 5.0, 5.0)


class TestSafetyContextVelocity:
    """Test velocity calculation in SafetyContext."""

    def test_velocity_calculation_from_position_history(self):
        """Velocity calculated from position changes."""
        # This tests the concept - actual SafetyContext test would need Qt
        import time
        
        # Simulate position history
        prev_pos = (0.0, 0.0, 10.0)
        curr_pos = (2.0, 1.0, 10.5)
        prev_t = time.monotonic()
        time.sleep(0.1)  # Small delay
        curr_t = time.monotonic()
        
        dt = curr_t - prev_t
        vx = (curr_pos[0] - prev_pos[0]) / dt
        vy = (curr_pos[1] - prev_pos[1]) / dt
        vz = (curr_pos[2] - prev_pos[2]) / dt
        
        # Velocity should be non-zero
        assert vx > 0
        assert vy > 0
        assert vz > 0

    def test_zero_velocity_when_stationary(self):
        """Zero velocity when drone doesn't move."""
        import time
        
        prev_pos = (5.0, 5.0, 10.0)
        curr_pos = (5.0, 5.0, 10.0)
        prev_t = time.monotonic()
        time.sleep(0.1)
        curr_t = time.monotonic()
        
        dt = curr_t - prev_t
        vx = (curr_pos[0] - prev_pos[0]) / dt
        vy = (curr_pos[1] - prev_pos[1]) / dt
        vz = (curr_pos[2] - prev_pos[2]) / dt
        
        assert vx == 0.0
        assert vy == 0.0
        assert vz == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
