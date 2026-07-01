"""
ROS2 Bag Playback Context for UI

Provides video-player-like controls for ROS2 bag file playback.
Manages subprocess for `ros2 bag play` command.
"""
from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QMetaObject, Qt, Signal, Slot, Property


class BagPlaybackContext(QObject):
    """
    Context for controlling ROS2 bag playback.
    
    Signals:
        stateChanged: Playback state changed (stopped/playing/paused)
        progressChanged: Playback progress changed (0.0-1.0)
        durationChanged: Total duration discovered (seconds)
        errorOccurred: Error during playback
    """
    
    stateChanged = Signal(str)  # "stopped", "playing", "paused"
    progressChanged = Signal(float)  # 0.0 to 1.0
    durationChanged = Signal(float)  # seconds
    playbackRateChanged = Signal(float)  # playback speed
    errorOccurred = Signal(str)
    
    # Default allowed bag directories. FileDialog-selected paths are always
    # permitted regardless of this list (see _validate_bag_path).
    _DEFAULT_BAG_DIRS = ("bags",)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._state = "stopped"
        self._progress = 0.0
        self._duration = 0.0
        self._playback_rate = 1.0
        self._bag_path: Optional[Path] = None
        self._process: Optional[subprocess.Popen] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = False
        # Set to True for the *next* loadBag call when the path came from a
        # FileDialog (user explicitly chose it) so we skip the bags/ restriction.
        self._dialog_selected: bool = False
    
    @Property(str, notify=stateChanged)
    def state(self) -> str:
        """Current playback state: stopped/playing/paused"""
        return self._state
    
    @Property(float, notify=progressChanged)
    def progress(self) -> float:
        """Playback progress (0.0 to 1.0)"""
        return self._progress
    
    @Property(float, notify=durationChanged)
    def duration(self) -> float:
        """Total duration in seconds"""
        return self._duration
    
    @Property(float, notify=playbackRateChanged)
    def playbackRate(self) -> float:
        """Playback speed multiplier"""
        return self._playback_rate
    
    @playbackRate.setter
    def playbackRate(self, rate: float):
        """Set playback speed (0.1 to 10.0)"""
        new_rate = max(0.1, min(10.0, rate))
        if new_rate != self._playback_rate:
            self._playback_rate = new_rate
            self.playbackRateChanged.emit(self._playback_rate)
    
    def _validate_bag_path(self, path: str) -> Optional[Path]:
        """Return a validated Path or None with an error emitted.

        Paths that come from a FileDialog call (self._dialog_selected is True)
        are accepted without restriction.  All other paths must resolve inside
        one of _DEFAULT_BAG_DIRS relative to the current working directory.
        """
        # Strip file:// URI prefix
        raw = path.strip()
        if raw.startswith("file:///"):
            raw = raw[8:]
        elif raw.startswith("file://"):
            raw = raw[7:]

        bag_path = Path(raw).resolve()

        if self._dialog_selected:
            # Path explicitly chosen by the user via FileDialog — allow it.
            self._dialog_selected = False
            return bag_path

        # Non-dialog path: must be inside an allowed directory.
        cwd = Path.cwd().resolve()
        allowed_roots = [
            (cwd / d).resolve() for d in self._DEFAULT_BAG_DIRS
        ]
        for root in allowed_roots:
            try:
                bag_path.relative_to(root)
                return bag_path
            except ValueError:
                pass

        self.errorOccurred.emit(
            f"Bag path '{path}' is outside the allowed bags/ directory. "
            "Use the file picker to open bags from other locations."
        )
        return None

    @Slot(str)
    def loadBagFromDialog(self, path: str) -> None:
        """Load a bag file that was selected via a FileDialog (no path restriction)."""
        self._dialog_selected = True
        self.loadBag(path)

    @Slot(str)
    def loadBag(self, path: str) -> None:
        """
        Load a ROS2 bag file.

        The path must be inside the bags/ directory unless this call was
        triggered via loadBagFromDialog() (FileDialog-selected path).

        Args:
            path: Path to .mcap or bag directory
        """
        try:
            bag_path = self._validate_bag_path(path)
            if bag_path is None:
                return  # Error already emitted

            if not bag_path.exists():
                self.errorOccurred.emit(f"Bag file not found: {path}")
                return

            # Stop any existing playback
            if self._state != "stopped":
                self.stop()

            self._bag_path = bag_path

            # Get bag info to determine duration
            self._get_bag_info()

        except Exception as e:
            self.errorOccurred.emit(f"Failed to load bag: {e}")
    
    def _get_bag_info(self) -> None:
        """Extract bag metadata (duration, topics, etc.)"""
        if not self._bag_path:
            return
        
        try:
            # Run `ros2 bag info` to get metadata
            result = subprocess.run(
                ["ros2", "bag", "info", str(self._bag_path)],
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            if result.returncode != 0:
                self.errorOccurred.emit(f"Failed to get bag info: {result.stderr}")
                return
            
            # Parse duration from output (format: "Duration: 123.45s")
            for line in result.stdout.split('\n'):
                if 'Duration:' in line:
                    duration_str = line.split('Duration:')[1].strip().rstrip('s')
                    self._duration = float(duration_str)
                    self.durationChanged.emit(self._duration)
                    break
        
        except subprocess.TimeoutExpired:
            self.errorOccurred.emit("Timeout getting bag info")
        except Exception as e:
            self.errorOccurred.emit(f"Error parsing bag info: {e}")
    
    @Slot()
    def play(self) -> None:
        """Start or resume playback"""
        if not self._bag_path:
            self.errorOccurred.emit("No bag file loaded")
            return
        
        if self._state == "playing":
            return  # Already playing
        
        try:
            # Build ros2 bag play command
            cmd = [
                "ros2", "bag", "play",
                str(self._bag_path),
                "--rate", str(self._playback_rate),
                "--clock"  # Publish /clock for simulation time
            ]
            
            # Start subprocess
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Update state
            self._state = "playing"
            self.stateChanged.emit(self._state)
            
            # Start monitoring thread
            self._stop_monitoring = False
            self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
            self._monitor_thread.start()
        
        except Exception as e:
            self.errorOccurred.emit(f"Failed to start playback: {e}")
    
    @Slot()
    def pause(self) -> None:
        """Pause playback (not supported by ros2 bag play - will stop instead)"""
        # Note: ros2 bag play doesn't support pause, so we stop
        self.stop()
    
    @Slot()
    def stop(self) -> None:
        """Stop playback"""
        if self._process:
            self._stop_monitoring = True
            self._process.terminate()
            try:
                self._process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
        
        self._state = "stopped"
        self._progress = 0.0
        self.stateChanged.emit(self._state)
        self.progressChanged.emit(self._progress)
    
    @Slot(float)
    def seek(self, position: float) -> None:
        """
        Seek to position (0.0 to 1.0).
        
        Note: ros2 bag play doesn't support seeking, so this will
        restart playback from the beginning with --start-offset.
        """
        if not self._bag_path or self._duration <= 0:
            return
        
        # Calculate time offset
        offset = position * self._duration
        
        # Stop current playback
        was_playing = self._state == "playing"
        self.stop()
        
        # Restart with offset
        try:
            cmd = [
                "ros2", "bag", "play",
                str(self._bag_path),
                "--rate", str(self._playback_rate),
                "--clock",
                "--start-offset", str(offset)
            ]
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self._state = "playing"
            self._progress = position
            self.stateChanged.emit(self._state)
            self.progressChanged.emit(self._progress)
            
            # Restart monitoring
            self._stop_monitoring = False
            self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
            self._monitor_thread.start()
        
        except Exception as e:
            self.errorOccurred.emit(f"Failed to seek: {e}")
    
    def _monitor_playback(self) -> None:
        """Monitor playback progress (runs in background thread).

        Signal emission is marshalled to the main thread via
        QMetaObject.invokeMethod to avoid data races on Windows.
        """
        start_time = time.time()

        while not self._stop_monitoring and self._process:
            # Check if process is still running
            if self._process.poll() is not None:
                # Process ended — marshal to main thread
                QMetaObject.invokeMethod(
                    self, "_on_playback_ended",
                    Qt.ConnectionType.QueuedConnection,
                )
                break

            # Update progress based on elapsed time
            # Read _playback_rate under a snapshot to avoid data races with
            # the main thread calling setPlaybackRate().
            playback_rate = self._playback_rate
            if self._duration > 0:
                elapsed = (time.time() - start_time) * playback_rate
                progress = min(1.0, elapsed / self._duration)
                if abs(progress - self._progress) > 0.001:
                    self._progress = progress
                    QMetaObject.invokeMethod(
                        self, "_emit_progress",
                        Qt.ConnectionType.QueuedConnection,
                    )

            time.sleep(0.1)  # Update at 10Hz

    @Slot()
    def _on_playback_ended(self) -> None:
        """Called on the main thread when the playback process exits."""
        self._state = "stopped"
        self._progress = 1.0
        self.stateChanged.emit(self._state)
        self.progressChanged.emit(self._progress)

    @Slot()
    def _emit_progress(self) -> None:
        """Called on the main thread to emit the latest progress value."""
        self.progressChanged.emit(self._progress)
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        self.stop()

