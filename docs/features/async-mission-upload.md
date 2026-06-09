# Async Mission Upload

Non-blocking mission upload for PX4 with progress tracking.

## Overview

The `PX4MissionUploader` class provides asynchronous mission upload functionality that doesn't block the UI thread. This allows the application to remain responsive while uploading waypoints to the drone.

## Features

- **Non-blocking**: Upload runs in background thread
- **Progress tracking**: Real-time progress updates (0-100%)
- **Status monitoring**: Track upload state (idle, sending, waiting, success, failed, cancelled)
- **Cancellation**: Cancel ongoing uploads
- **Error handling**: Graceful error handling with detailed status messages
- **Callback support**: Multiple progress callbacks can be registered

## Usage

### Basic Async Upload

```python
from droneresearch.ros.px4_mission import PX4MissionUploader

# Create uploader
uploader = PX4MissionUploader(node, namespace="uav_1")

# Define waypoints
waypoints = [
    {"lat": 47.397742, "lon": 8.545594, "alt": 10.0},
    {"lat": 47.397842, "lon": 8.545694, "alt": 15.0},
    {"lat": 47.397942, "lon": 8.545794, "alt": 20.0},
]

# Upload asynchronously
future = uploader.upload_async(waypoints, timeout=10.0)

# Do other work while uploading...
print("Upload in progress...")

# Wait for completion
success = future.result()  # Blocks until complete
print(f"Upload {'succeeded' if success else 'failed'}")
```

### With Progress Callback

```python
def on_progress(status, progress, message):
    """Called on each progress update."""
    print(f"[{status.value}] {progress*100:.0f}% - {message}")

# Upload with progress tracking
future = uploader.upload_async(
    waypoints, 
    timeout=10.0,
    progress_callback=on_progress
)

# Wait for completion
success = future.result()
```

### Query Upload Status

```python
# Start upload
future = uploader.upload_async(waypoints)

# Check status at any time
status = uploader.get_upload_status()
print(f"Status: {status['status']}")
print(f"Progress: {status['progress']*100:.0f}%")
print(f"Is uploading: {status['is_uploading']}")

# Wait for completion
success = future.result()
```

### Cancel Upload

```python
# Start upload
future = uploader.upload_async(waypoints)

# Cancel after some time
time.sleep(1.0)
uploader.cancel_upload()

# Check result
try:
    success = future.result(timeout=5.0)
    print(f"Upload cancelled: {not success}")
except Exception as e:
    print(f"Upload error: {e}")
```

### Multiple Progress Callbacks

```python
def ui_callback(status, progress, message):
    """Update UI progress bar."""
    update_progress_bar(progress * 100)

def log_callback(status, progress, message):
    """Log progress to file."""
    logger.info(f"{status.value}: {message}")

# Register multiple callbacks
uploader.add_progress_callback(ui_callback)
uploader.add_progress_callback(log_callback)

# Upload
future = uploader.upload_async(waypoints)
success = future.result()

# Remove callbacks when done
uploader.remove_progress_callback(ui_callback)
uploader.remove_progress_callback(log_callback)
```

## Upload Status States

The upload progresses through these states:

1. **IDLE**: No upload in progress
2. **SENDING_COUNT**: Sending mission count to PX4 (10% progress)
3. **SENDING_ITEMS**: Sending waypoint items (10-80% progress)
4. **WAITING_ACK**: Waiting for PX4 acknowledgment (80-100% progress)
5. **SUCCESS**: Upload completed successfully (100% progress)
6. **FAILED**: Upload failed (error occurred)
7. **CANCELLED**: Upload cancelled by user

## Progress Tracking

Progress is reported as a float from 0.0 to 1.0:

- **0.0-0.1**: Sending mission count
- **0.1-0.8**: Sending waypoint items (incremental)
- **0.8-1.0**: Waiting for acknowledgment
- **1.0**: Upload complete

## Error Handling

The async upload handles errors gracefully:

```python
future = uploader.upload_async(waypoints)

try:
    success = future.result(timeout=30.0)
    if success:
        print("✓ Upload successful")
    else:
        status = uploader.get_upload_status()
        print(f"✗ Upload failed: {status['status']}")
except TimeoutError:
    print("✗ Upload timed out")
    uploader.cancel_upload()
except Exception as e:
    print(f"✗ Upload error: {e}")
```

## UI Integration Example

```python
from PyQt6.QtCore import QThread, pyqtSignal

class MissionUploadWorker(QThread):
    """Worker thread for mission upload."""
    progress_updated = pyqtSignal(str, float, str)  # status, progress, message
    upload_finished = pyqtSignal(bool)  # success
    
    def __init__(self, uploader, waypoints):
        super().__init__()
        self.uploader = uploader
        self.waypoints = waypoints
    
    def on_progress(self, status, progress, message):
        """Forward progress to UI thread."""
        self.progress_updated.emit(status.value, progress, message)
    
    def run(self):
        """Run upload in background thread."""
        future = self.uploader.upload_async(
            self.waypoints,
            progress_callback=self.on_progress
        )
        success = future.result()
        self.upload_finished.emit(success)

# In UI code:
worker = MissionUploadWorker(uploader, waypoints)
worker.progress_updated.connect(self.update_progress_bar)
worker.upload_finished.connect(self.on_upload_complete)
worker.start()
```

## Comparison: Sync vs Async

### Synchronous Upload (Blocking)

```python
# Blocks UI thread for ~2-5 seconds
success = uploader.upload(waypoints)
# UI is frozen during upload
```

### Asynchronous Upload (Non-blocking)

```python
# Returns immediately, upload runs in background
future = uploader.upload_async(waypoints)
# UI remains responsive
# ...do other work...
success = future.result()  # Wait when ready
```

## Best Practices

1. **Always use async in UI applications** to prevent freezing
2. **Set appropriate timeouts** based on mission size (default: 10s)
3. **Handle cancellation** gracefully in long-running uploads
4. **Use progress callbacks** to update UI in real-time
5. **Check upload status** before starting new upload
6. **Remove callbacks** when no longer needed to prevent memory leaks

## Thread Safety

The async upload is thread-safe:

- Upload runs in dedicated thread pool (max 1 worker)
- Progress callbacks are called from worker thread
- Status queries are thread-safe
- Only one upload can run at a time (raises `RuntimeError` if concurrent)

## Performance

- **Overhead**: ~10ms for thread creation
- **Upload time**: ~50ms per waypoint + network latency
- **Memory**: Minimal (single thread, small queue)
- **CPU**: <1% during upload

## Limitations

- Only one upload can run at a time per uploader instance
- Progress callbacks must be thread-safe if updating UI
- Cancellation may not be immediate (checks between waypoints)
- ACK timeout is fixed per upload (cannot change mid-upload)

## See Also

- [PX4 Mission Protocol](https://mavlink.io/en/services/mission.html)
- [PX4 ROS2 Integration](https://docs.px4.io/main/en/ros2/user_guide.html)
- [Python concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)