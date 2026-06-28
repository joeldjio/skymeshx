# Camera and Gimbal Panel - Phase 1

**Phase:** Camera & Gimbal Foundation  
**UI file:** `tools/ui/qml/panels/GimbalPanel.qml`  
**Backend context:** `tools/ui/context/camera_context.py`  
**QML context:** `camera`

## Scope

Phase 1 turns the existing Gimbal panel into the first Camera & Gimbal Control Center. It provides operator-facing controls for stream source selection, snapshots, recording, camera profile settings, thermal settings, and live status display.

This phase prepares the UI and backend contract. It does not yet implement real video frame rendering; the video area is currently a UI frame/placeholder ready for later QtMultimedia integration.

## Operator Workflow

1. Select an observation drone.
2. Choose a camera source.
3. Start the stream.
4. Capture snapshots or start recording.
5. Adjust camera profile settings.
6. Adjust thermal settings when using thermal inspection.
7. Monitor stream and recording status.
8. Stop recording and stream before leaving the workflow.

## Camera Sources

The source dropdown should use:

```qml
camera.availableSources
```

Known sources:

- `None`
- `RGB Camera`
- `Thermal Camera`
- `Multispectral`
- `RTSP Stream`
- `ROS2 Topic`
- `Test Source`

`Test Source` is the recommended source for UI testing because it does not require real hardware.

## Stream Controls

The UI calls:

```qml
camera.cameraStartStream(source)
camera.cameraStopStream()
```

Expected behavior:

- Stream start enables snapshot and recording controls.
- Stream stop disables recording-dependent controls.
- Starting `Test Source` should always work without a real drone.
- Non-test sources require a selected observation drone or compatible backend.

## Snapshot Controls

The UI calls:

```qml
camera.cameraSnapshot()
```

Expected behavior:

- Snapshot is allowed only when a stream is active.
- On success, `camera.snapshotCaptured(path)` is emitted.
- `camera.lastSnapshotPath` stores the latest path.

## Recording Controls

The UI calls:

```qml
camera.cameraStartRecording(path)
camera.cameraStopRecording()
```

Expected behavior:

- Recording is allowed only when a stream is active.
- Recording has a visible indicator.
- Duration is shown from `camera.recordingDuration`.
- Recording stops during app shutdown through `camera.shutdown()`.
- Recording is blocked if the target path has less than 1 GB free storage.

## Camera Settings

The UI should apply profile changes only after explicit operator action, not during QML component initialization.

Call:

```qml
camera.setCameraProfile({
    "name": profileName,
    "resolution": resolution,
    "fps": fps,
    "hfov": hfov,
    "vfov": vfov,
    "format": "H264"
})
```

Validation is done in the backend context:

- FPS: `1..60`
- HFOV/VFOV: `10..180`
- Profile must be an object/map

## Thermal Settings

The UI calls:

```qml
camera.setTempRange(minC, maxC)
camera.setColorPalette(palette)
camera.setHotspotDetection(enabled)
```

Supported palettes:

- `Ironbow`
- `Rainbow`
- `Grayscale`
- `Hot`
- `Cold`
- `Medical`

The UI should avoid applying thermal settings automatically while a ComboBox is initializing. Bob already fixed this pattern by applying settings only when the operator clicks the explicit apply button.

## Status Display

The UI can poll:

```qml
var status = camera.getCameraStatus()
```

Useful fields:

- `source`
- `streamActive`
- `recordingActive`
- `recordingDurationSec`
- `frameAgeMs`
- `droppedFrames`
- `profile`
- `resolution`
- `fps`
- `hfov`
- `vfov`
- `thermalEnabled`
- `hotspotDetection`
- `lastError`

Signals are also available for event-driven updates:

- `streamStarted(source)`
- `streamStopped()`
- `recordingStarted(path)`
- `recordingStopped(duration)`
- `snapshotCaptured(path)`
- `errorOccurred(message)`
- `statusChanged()`

## Video Display Placeholder

Phase 1 includes a video display area with:

- 16:9 aspect ratio
- inactive placeholder
- live indicator
- source/resolution/FPS overlay
- recording indicator

Actual video rendering is future work and likely belongs to a QtMultimedia/VideoOutput integration task.

## Error Handling

UI should show `camera.lastError` when an action returns `false`.

Common errors:

- Starting stream with `None`
- Snapshot while stream is stopped
- Recording while stream is stopped
- Invalid FPS/FOV
- Unsupported thermal palette
- Low storage for recording

## Integration Notes

Registered QML contexts from Phase 1:

- `camera`

Related QML context from Phase 2 support:

- `capabilities`

For Solar Inspection Wizard setup checks, use:

```qml
capabilities.checkModeRequirements("solar")
```

For selected drone checks, use:

```qml
capabilities.checkDroneModeRequirements(selectedDroneId, "solar")
```

## Tests

Backend tests:

```bash
python -m pytest tests/test_camera_context.py -q
```

Combined context tests:

```bash
python -m pytest tests/test_camera_context.py tests/test_capability_registry.py tests/test_capability_context.py -q
```

Latest reported result from Bob:

```text
tests/test_camera_context.py: 8 passed
combined context tests: 24 passed
```

## Phase 1 Done Criteria

Phase 1 is complete when:

- Camera controls render in `GimbalPanel.qml`.
- `camera` context is visible to QML.
- `Test Source` works without hardware.
- Snapshot and recording actions are guarded by stream state.
- Camera profile validation happens in backend context.
- Thermal settings can be configured.
- Status/error display is available.
- Hardware-free tests pass.

As of the latest feedback entry, Bob reported all related backend tests passing.

