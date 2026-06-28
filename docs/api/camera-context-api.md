# Camera Context API

**Phase:** Camera & Gimbal Foundation  
**QML context:** `camera`  
**Implementation:** `tools/ui/context/camera_context.py`  
**Tests:** `tests/test_camera_context.py`

## Purpose

`CameraContext` exposes camera, stream, recording, snapshot, and thermal settings to QML. It is designed to work with real observation drones when available and to remain hardware-free for tests and UI development through `Test Source`.

The context is registered in `tools/ui/service_locator.py` as:

```qml
camera
```

## Safety Rules

- Camera failures must not crash mission planning or the UI.
- `Test Source` must work without MAVLink, ROS2, SITL, or a real camera.
- Recording requires an active stream.
- Snapshot capture requires an active stream.
- Recording is blocked when the target storage has less than 1 GB free.
- Shutdown stops active recording and streaming through `camera.shutdown()`.

## QML Properties

| Property | Type | Description |
| --- | --- | --- |
| `availableSources` | list | Camera source names for dropdowns. |
| `selectedDroneId` | string | Drone selected for delegated camera actions. |
| `currentSource` | string | Current stream source. |
| `streamActive` | bool | True when a stream is active. |
| `recordingActive` | bool | True when recording is active. |
| `recordingDuration` | int | Recording duration in seconds. |
| `frameAge` | int | Last frame age in milliseconds. |
| `droppedFrames` | int | Dropped frame counter. |
| `currentProfile` | string | Active camera profile name. |
| `lastError` | string | Last camera error, empty when clear. |
| `lastSnapshotPath` | string | Last snapshot path. |

## QML Slots

```qml
camera.setSelectedDrone(droneId)
camera.cameraStartStream(source)
camera.cameraStopStream()
camera.cameraSnapshot()
camera.cameraStartRecording(path)
camera.cameraStopRecording()
camera.setCameraProfile(profile)
camera.getCameraStatus()
camera.setTempRange(minC, maxC)
camera.setColorPalette(palette)
camera.setHotspotDetection(enabled)
```

## Signals

| Signal | Parameters | Description |
| --- | --- | --- |
| `streamStarted` | `source` | Stream started successfully. |
| `streamStopped` | none | Stream stopped. |
| `recordingStarted` | `path` | Recording started. |
| `recordingStopped` | `duration` | Recording stopped. |
| `snapshotCaptured` | `path` | Snapshot captured. |
| `errorOccurred` | `message` | Camera operation failed. |
| `statusChanged` | none | Any status field changed. |

## Status Object

`camera.getCameraStatus()` returns a QML-friendly object:

```json
{
  "source": "Test Source",
  "streamActive": true,
  "recordingActive": false,
  "recordingDurationSec": 0,
  "frameAgeMs": 0,
  "droppedFrames": 0,
  "profile": "RGB Camera",
  "resolution": "1920x1080",
  "fps": 30,
  "hfov": 90.0,
  "vfov": 60.0,
  "thermalEnabled": false,
  "hotspotDetection": false,
  "temperatureMinC": -40.0,
  "temperatureMaxC": 200.0,
  "colorPalette": "Ironbow",
  "lastError": "",
  "selectedDroneId": "CAM1",
  "lastSnapshotPath": ""
}
```

## Camera Profile

`setCameraProfile(profile)` accepts a map:

```json
{
  "name": "High Resolution",
  "resolution": "3840x2160",
  "fps": 24,
  "hfov": 84.0,
  "vfov": 56.0,
  "format": "H264"
}
```

Validation:

- `fps` must be between 1 and 60.
- `hfov` and `vfov` must be between 10 and 180 degrees.
- Non-object profiles are rejected.

## Thermal Settings

Supported palettes:

- `Ironbow`
- `Rainbow`
- `Grayscale`
- `Hot`
- `Cold`
- `Medical`

Temperature range validation:

- Minimum must be less than maximum.
- Range must stay between `-40 C` and `200 C`.

## Usage Examples

Start a mock stream:

```qml
camera.cameraStartStream("Test Source")
```

Start recording to an automatic path:

```qml
camera.cameraStartRecording("")
```

Set selected observation drone:

```qml
camera.setSelectedDrone(selectedDroneId)
camera.cameraStartStream("RGB Camera")
```

Apply profile:

```qml
camera.setCameraProfile({
    "name": "Inspection",
    "resolution": "1920x1080",
    "fps": 30,
    "hfov": 90,
    "vfov": 60,
    "format": "H264"
})
```

## Backend Delegation

`CameraContext` delegates to `SwarmBackend` when a selected observation backend exists. Otherwise, `Test Source` remains available.

Relevant backend methods:

- `DroneBackend.camera_start_stream(source)`
- `DroneBackend.camera_stop_stream()`
- `DroneBackend.camera_snapshot()`
- `DroneBackend.camera_start_recording(path)`
- `DroneBackend.camera_stop_recording()`
- `DroneBackend.get_camera_status()`
- `SwarmBackend.set_camera_context(camera_context)`
- `SwarmBackend.get_camera_context()`

## Observation UAV Integration

`ObservationUAVModel` exposes:

- `start_camera_stream(source)`
- `stop_camera_stream()`
- `capture_snapshot()`
- `start_recording(path)`
- `stop_recording()`
- `get_camera_status()`
- `get_gimbal_status()`

Basic MAVLink command mapping:

| Action | MAVLink command |
| --- | --- |
| Snapshot | `MAV_CMD_DO_DIGICAM_CONTROL` (`203`) |
| Start recording | `MAV_CMD_VIDEO_START_CAPTURE` (`2500`) |
| Stop recording | `MAV_CMD_VIDEO_STOP_CAPTURE` (`2501`) |

## Tests

Run:

```bash
python -m pytest tests/test_camera_context.py -q
```

Coverage includes:

- Mock stream start/stop
- Fake observation backend delegation
- Snapshot and recording behavior
- Profile validation
- Thermal settings validation
- Signal emissions
- Shutdown cleanup
- SwarmBackend camera context getter

Latest reported result from Bob:

```text
8 passed
```

