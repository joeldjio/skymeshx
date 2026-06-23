# Camera, Seeding, Solar Collaboration Feedback

**Purpose:** Coordinate parallel implementation between Codex and Bob  
**Created:** 2026-06-23  
**Implementation Plan:** `camera-seeding-solar-implementation-plan.md`

---

## 📋 How to Use This File

Each agent writes entries with:
- **Date/Time** - ISO 8601 format
- **Agent** - Codex or Bob
- **Status** - Progress, Blocker, API Request, Review, Question
- **Files** - Files touched or affected
- **Message** - Clear description of progress, issue, or request

---

## 🔄 Feedback Entries

### 2026-06-23T13:00:00Z | Bob | Progress | Initial Setup

**Files:** `docs/project/camera-seeding-solar-implementation-plan.md`, `docs/project/camera-seeding-solar-collab-feedback.md`

**Message:**
Created comprehensive implementation plan with checkboxes for both agents. Work is divided as follows:

**Codex owns:**
- Backend camera context (`tools/ui/context/camera_context.py`)
- Backend extensions (`tools/ui/backend.py`, `skymeshx/models/observation_uav.py`)
- Capability registry (`skymeshx/models/capabilities.py`)
- Solar inspection backend (`skymeshx/control/solar_inspection.py`)
- Seeding backend (`skymeshx/control/seeding_planner.py`)
- All backend tests

**Bob owns:**
- Camera UI (`tools/ui/qml/panels/GimbalPanel.qml`)
- Solar wizard UI (`tools/ui/qml/panels/SolarInspectionPanel.qml`)
- Seeding wizard UI (`tools/ui/qml/panels/SeedingPanel.qml`)
- Map overlays (`tools/ui/qml/MapView.qml`)
- Main QML integration (`tools/ui/qml/main.qml`)

**Shared files requiring coordination:**
- `tools/ui/context/mission_context.py` - Upload/execute separation
- `tools/ui/service_locator.py` - Context registration
- `tools/ui/context/__init__.py` - Context exports

**Next Steps:**
1. Codex: Create camera context API and document in this file
2. Bob: Review API and request changes if needed
3. Both: Begin Phase 1 tasks in parallel

---

## 📝 API Contract: Camera Context

### QML Context Name
```qml
camera
```

### Properties (Qt Properties)

| Property | Type | Description |
|----------|------|-------------|
| `currentSource` | `QString` | Currently selected camera source |
| `streamActive` | `bool` | Whether stream is currently active |
| `recordingActive` | `bool` | Whether recording is currently active |
| `recordingDuration` | `int` | Recording duration in seconds |
| `frameAge` | `int` | Age of last frame in milliseconds |
| `droppedFrames` | `int` | Number of dropped frames |
| `currentProfile` | `QString` | Current camera profile name |
| `lastError` | `QString` | Last error message (empty if no error) |

### Slots (QML-callable methods)

| Slot | Parameters | Returns | Description |
|------|------------|---------|-------------|
| `cameraStartStream` | `source: QString` | `bool` | Start camera stream from source |
| `cameraStopStream` | - | `bool` | Stop current camera stream |
| `cameraSnapshot` | - | `bool` | Capture snapshot from current stream |
| `cameraStartRecording` | `path: QString` | `bool` | Start recording to file path |
| `cameraStopRecording` | - | `bool` | Stop current recording |
| `setCameraProfile` | `profile: QVariantMap` | `bool` | Set camera profile (resolution, fps, etc.) |
| `getCameraStatus` | - | `QVariantMap` | Get current camera status |
| `setTempRange` | `min_c: float, max_c: float` | `bool` | Set thermal camera temperature range |
| `setColorPalette` | `palette: QString` | `bool` | Set thermal camera color palette |
| `setHotspotDetection` | `enabled: bool` | `bool` | Enable/disable hotspot detection |

### Signals (Qt Signals)

| Signal | Parameters | Description |
|--------|------------|-------------|
| `streamStarted` | `source: QString` | Emitted when stream starts |
| `streamStopped` | - | Emitted when stream stops |
| `recordingStarted` | `path: QString` | Emitted when recording starts |
| `recordingStopped` | `duration: int` | Emitted when recording stops |
| `snapshotCaptured` | `path: QString` | Emitted when snapshot is saved |
| `errorOccurred` | `message: QString` | Emitted on error |
| `statusChanged` | - | Emitted when status changes |

### Camera Status Object (QVariantMap)

```json
{
  "source": "Test Source",
  "streamActive": false,
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
  "lastError": ""
}
```

### Camera Profile Object (QVariantMap)

```json
{
  "name": "High Resolution",
  "resolution": "1920x1080",
  "fps": 30,
  "hfov": 90.0,
  "vfov": 60.0,
  "format": "H264"
}
```

---

## 📝 API Contract: Capability Registry

### QML Context Name
```qml
capabilities
```

### Slots (QML-callable methods)

| Slot | Parameters | Returns | Description |
|------|------------|---------|-------------|
| `checkModeRequirements` | `mode: QString` | `QVariantMap` | Check if drone has required capabilities for mode |
| `getDroneCapabilities` | `drone_id: QString` | `QVariantMap` | Get capabilities for specific drone |

### Capability Check Result (QVariantMap)

```json
{
  "satisfied": true,
  "missing": [],
  "warnings": ["Thermal camera not detected - thermal inspection will be limited"]
}
```

### Drone Capabilities Object (QVariantMap)

```json
{
  "hasCamera": true,
  "hasThermalCamera": false,
  "hasGimbal": true,
  "hasDispenser": false,
  "cameraResolution": "1920x1080",
  "cameraFov": [90.0, 60.0],
  "gimbalAxes": ["pitch", "yaw"],
  "dispenserType": null
}
```

---

## 📝 API Contract: Mission Preview Data

### Solar Inspection Preview (QVariantMap)

```json
{
  "waypoints": [
    {"lat": 47.123, "lon": 8.456, "alt": 50.0},
    {"lat": 47.124, "lon": 8.457, "alt": 50.0}
  ],
  "triggerPoints": [
    {
      "lat": 47.123,
      "lon": 8.456,
      "gimbalAngle": -45.0,
      "footprint": [
        {"lat": 47.1229, "lon": 8.4559},
        {"lat": 47.1231, "lon": 8.4559},
        {"lat": 47.1231, "lon": 8.4561},
        {"lat": 47.1229, "lon": 8.4561}
      ]
    }
  ],
  "estimatedDuration": 1200,
  "estimatedBatteryUsage": 35.0,
  "totalImages": 150,
  "storageRequired": 450.0,
  "warnings": []
}
```

### Seeding Preview (QVariantMap)

```json
{
  "waypoints": [
    {"lat": 47.123, "lon": 8.456, "alt": 10.0},
    {"lat": 47.124, "lon": 8.457, "alt": 10.0}
  ],
  "rows": [
    {
      "start": {"lat": 47.123, "lon": 8.456},
      "end": {"lat": 47.124, "lon": 8.456},
      "direction": 0.0
    }
  ],
  "dropPoints": [
    {
      "lat": 47.123,
      "lon": 8.456,
      "seedCount": 50,
      "status": "planned"
    }
  ],
  "exclusionZones": [
    [
      {"lat": 47.1235, "lon": 8.4565},
      {"lat": 47.1236, "lon": 8.4565},
      {"lat": 47.1236, "lon": 8.4566},
      {"lat": 47.1235, "lon": 8.4566}
    ]
  ],
  "estimatedDuration": 1800,
  "estimatedBatteryUsage": 45.0,
  "totalSeeds": 5000,
  "seedUsagePercent": 75.0,
  "warnings": ["Tank refill may be required"]
}
```

---

## 🚧 Known Issues & Blockers

*No blockers yet - work starting*

---

## 💡 Questions & Discussions

*No questions yet*

---

## ✅ Completed Milestones

- [x] 2026-06-23 - Implementation plan created
- [x] 2026-06-23 - Feedback file initialized
- [x] 2026-06-23 - API contracts documented

---

## 📅 Next Review Points

1. **After Codex creates camera context** - Bob reviews API and tests integration
2. **After capability registry** - Bob tests in wizard UI
3. **Before mission context changes** - Both review upload/execute separation
4. **After preview data implementation** - Bob tests map overlay rendering
5. **Before final integration** - Both review complete workflow

---

## 📖 Reference Links

- Implementation Plan: [`camera-seeding-solar-implementation-plan.md`](camera-seeding-solar-implementation-plan.md)
- Comprehensive Plan: [`comprehensive-camera-seeding-solar-implementation.md`](comprehensive-camera-seeding-solar-implementation.md)
- Collaboration Plan: [`camera-seeding-solar-collab-plan.md`](camera-seeding-solar-collab-plan.md)
- Agent Rules: [`../../AGENTS.md`](../../AGENTS.md)