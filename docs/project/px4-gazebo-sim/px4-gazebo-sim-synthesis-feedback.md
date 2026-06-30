# PX4 Gazebo ROS2 Simulation Synthesis Feedback

**Created:** 2026-06-26  
**Inputs compared:**

- `docs/project/px4-gazebo-sim-integration-plan.md` by Bob
- `docs/project/px4-ros2-gazebo-sim-test-feedback.md` by Codex

**Purpose:** Gemeinsame Synthese fuer die naechste grosse Integrationsphase nach Camera/Seeding/Solar: PX4 SITL + Gazebo + ROS2 + Video + Bags + Trace, so dass Linux-only Tests spaeter offline analysierbar sind.

---

## Executive Summary

Bob und Codex sind in der Zielrichtung gleich:

- PX4/Gazebo/SIH soll aus der GCS testbar werden.
- Kamera/Gimbal/Video aus Gazebo soll in SkyMeshX sichtbar werden.
- ROS2/uXRCE-DDS Topics sollen nicht nur intern genutzt, sondern im ROS2 Tab beobachtbar sein.
- ROS2 Bags und strukturierte Trace-Daten sind Pflicht, weil der Nutzer waehrend Linux-Tests kein Live-Feedback geben kann.
- Upload != Execute bleibt eine harte Regel.

Bob liefert die bessere **Modul- und Rollenstruktur**.  
Codex liefert die tiefere **Trace-/Debug-/Offline-Analyse-Struktur**.

Die Synthese sollte daher Bobs Modulplan als Arbeitsstruktur nutzen, aber Codex' Trace Bundle, Topic Health, Mission Trace und Video-Availability Gate als verbindliche Acceptance Criteria aufnehmen.

---

## Wichtige Unterschiede

### 1. Trace Scope

Bob:

- `TraceLogger` in `skymeshx/core/trace_logger.py`
- Trace Types: MAVLink, ROS2, QML_SIGNAL, PYTHON_CALL, STATE_CHANGE, ERROR
- Analyzer CLI `tools/analyze_trace.py`
- Trace Tab im LogPanel

Codex:

- Trace Session Folder mit `manifest.json`
- `ui_events.jsonl`
- `mission_trace.jsonl`
- `ros2_topic_health.json`
- Bag Path, config snapshots, video probe artifacts
- Offline analysierbarer Run-Ordner als zentrales Artefakt

**Synthese:**

Implementiere beides als ein System:

```text
TraceLogger = low-level event writer
TraceContext = UI/session-facing trace manager
Trace Bundle = output folder with manifest + logs + bags + health snapshots
Trace Analyzer = offline report generator
```

### 2. Video Stream

Bob:

- `VideoStreamContext`
- QML Properties fuer active/fps/latency/resolution
- UDP/RTSP/GStreamer URL
- GimbalPanel Live View
- Map PIP Overlay

Codex:

- Pro Drone Video Source: host/port/protocol
- Stream status state machine: unconfigured/waiting/receiving/stalled/error
- Map zeigt Video erst wenn Stream wirklich `receiving`
- PX4 Gazebo default ports: 5600, 5601, 5602
- Erst MVP mit probe/status/snapshot, dann QML Live Video

**Synthese:**

Phase 1 Video darf noch kein perfektes Live-Decoding brauchen. Pflicht ist zuerst:

- UDP Port konfigurierbar
- Stream probe/status
- Map zeigt nur Badge/Status, kein leeres kaputtes Video
- Trace schreibt Stream-Verfuegbarkeit

Phase 2:

- GStreamer/QtMultimedia decoding
- GimbalPanel Live View
- Map PIP Overlay

### 3. ROS2 Topics

Bob:

- Topic Browser mit Discovery, Subscribe, JSON Preview, Rate Badges
- Auto-Subscribe wichtiger PX4 Topics

Codex:

- Topic Health als exportierbares Test-Artefakt
- Mindest-Topic-Set pro Namespace
- Message age, estimated Hz, QoS

**Synthese:**

Topic Browser ist UI-Feature. Topic Health ist Test-/Trace-Feature. Beide muessen auf derselben Backend-Messung basieren:

```text
ROS2Context topic registry
  -> QML Topic Browser
  -> trace_runs/.../ros2_topic_health.json
```

### 4. Bag Recorder

Bob:

- ROS2Panel Bag Recorder UI
- Start/Stop
- FlightLog Link
- Tests mit subprocess mock

Codex:

- Topic Presets:
  - minimal_mission
  - full_px4_out
  - camera_gimbal
  - swarm_multi_vehicle
- Bag output path wird im manifest referenziert
- Auto-start/auto-stop optional

**Synthese:**

Bob's UI + Codex presets/manifest. Bag Recording muss immer ins Trace Bundle integrierbar sein.

### 5. SITL Launch

Bob:

- Erweitert ROS2Context `startSitl`, `startMultiSitl`, `startSihSitl`
- Model Dropdown, Camera/Gimbal Toggle, Multi-Vehicle UI
- Namespaces `uav_N`
- Ports `5762, 5763, ...`

Codex:

- PX4 Gazebo offizielle Multi-Vehicle Beispiele nutzen haeufig `/px4_N/fmu/...`
- Video Ports `5600 + index`
- Manifest muss Namespace/Instance/Port eindeutig dokumentieren

**Synthese:**

UI muss beide Namespace-Patterns akzeptieren:

```text
uav_N  -> bisherige Repo-Konvention
px4_N  -> offizielle PX4 Multi-Vehicle Beispiele
```

Die Default-Entscheidung sollte explizit im Launch-Profil stehen. Empfehlung fuer PX4/Gazebo:

```text
default namespace pattern: px4_N
compat alias: uav_N
```

### 6. MAVLink vs ROS2/PX4

Bob Architektur nennt:

```text
MAVLink tcp:127.0.0.1:5762 fuer Arm/Mode/Mission (ArduPilot kompat.)
ODER PX4 MAVLink via MAVSDK
ROS2 Bridge fuer Telemetrie/Offboard/Formation
```

Codex Hinweis:

PX4 native Integration sollte fuer PX4-Sim nicht als "ArduPilot kompatibel" behandelt werden. Der repo-interne Standardport `tcp:127.0.0.1:5762` ist fuer ArduCopter SITL wichtig, aber PX4/Gazebo braucht eine klar getrennte Verbindungsschicht:

- PX4/uXRCE-DDS fuer ROS2 Topics, Offboard, Mission Upload sofern moeglich
- PX4 MAVLink/MAVSDK optional fuer Camera/Gimbal/Mission-Kommandos, aber nicht stillschweigend ueber ArduPilot-Pfade

**Synthese:**

Fuehre einen expliziten `vehicleBackend`/`simBackend` ein:

```json
{
  "autopilot": "px4",
  "controlPath": "ros2_uxrce",
  "optionalMavlinkEndpoint": "udp://127.0.0.1:14540",
  "namespace": "px4_1"
}
```

Keine automatische Vermischung von ArduPilot MissionEngine und PX4 ROS2 MissionUploader.

---

## Gemeinsamer Modulplan

### Module E First: Trace + Bundle Foundation

**Priority:** P0  
**Reason:** Ohne Trace kann der Linux-Test nicht sinnvoll offline ausgewertet werden.

Use Bob's `TraceLogger`, plus Codex' trace bundle structure.

Deliverables:

- `skymeshx/core/trace_logger.py`
- `tools/ui/context/trace_context.py`
- `tools/analyze_trace.py`
- `trace_runs/<timestamp>_<scenario>/manifest.json`
- `ui_events.jsonl`
- `mission_trace.jsonl`
- `ros2_topic_health.json`
- `app.log` reference/copy
- optional `screenshots/`

Required event types:

- app/session
- qml action
- bridge status
- topic health
- video status
- mission preview/upload/start/pause/abort
- mission current waypoint
- drone position vs active waypoint distance
- camera/gimbal status
- error/warning

Owner:

- Codex backend
- Bob QML buttons/status later

Tests:

- `tests/test_trace_logger.py`
- `tests/test_trace_context.py`

---

### Module A: PX4 SITL/Gazebo/SIH Launch Profiles

**Priority:** P1

Merge Bob A.1/A.2 with Codex manifest requirements.

Backend:

- Extend `tools/ui/context/ros2_context.py`
- Add launch profiles:
  - `gz_x500`
  - `gz_x500_mono_cam`
  - `gz_x500_gimbal`
  - `plane`
  - `standard_vtol`
  - `sih_quadx`
- Add:
  - `startSitl(profile: dict)`
  - `startMultiSitl(profile: dict)`
  - `startSihSitl(profile: dict)`
  - `stopSitl()`
  - `getSitlStatus() -> dict`
- Persist profile into trace manifest.

UI:

- ROS2Panel Connection tab:
  - Model dropdown
  - namespace pattern selector (`px4_N`, `uav_N`, custom)
  - vehicle count
  - camera/gimbal toggles
  - video base port
  - start/stop all
  - status list

Tests:

- `tests/test_ros2_sitl_launcher.py`
- subprocess mocked

---

### Module A2: Gazebo World Profiles

**Priority:** P1  
**Reason:** The same vehicle model can behave very differently depending on the Gazebo world. World selection must be explicit, reproducible, and recorded in the trace manifest.

PX4 Gazebo supports multiple worlds. The default world is an empty grey plane, but model-specific worlds may be selected automatically if a matching world exists. The world can also be forced through `PX4_GZ_WORLD`, for example:

```bash
PX4_GZ_WORLD=ridge make px4_sitl gz_x500_lidar_down
PX4_GZ_MODEL_POSE=0,0,2.2 PX4_GZ_WORLD=moving_platform make px4_sitl gz_standard_vtol
```

World profiles to support:

| Profile | PX4 world | Primary use |
|---------|-----------|-------------|
| `empty_default` | `default` | baseline mission, camera, seeding, solar smoke tests |
| `aruco_precision_landing` | `aruco` | downward camera / precision landing / marker detection |
| `baylands_water` | `bayland` | visual navigation and over-water scenario checks |
| `ridge_terrain` | `ridge` | terrain following, lidar/down rangefinder validation |
| `walls_collision` | `walls` | collision prevention, APF/avoidance debug |
| `windy_disturbance` | `windy` | wind robustness, position hold, mission tracking drift |
| `moving_platform` | `moving_platform` | takeoff/landing from moving vehicle/ship/truck platform |
| `rover_grid` | `rover` | ground grid reference, rover-specific future tests |

Notes from PX4 docs:

- `lawn` exists but is not recommended because low frame rate can cause segmentation faults in some frames.
- `ridge` is described for PX4 v1.18 and pairs naturally with `x500_lidar_down`.
- `moving_platform` is PX4 v1.16+ and can be configured with:
  - `PX4_GZ_PLATFORM_VEL`
  - `PX4_GZ_PLATFORM_HEADING_DEG`
- `aruco` is intended with `x500_mono_cam_down` for precision landing tests.

Backend requirements:

- Extend SITL launch profile schema:

```json
{
  "worldProfile": "ridge_terrain",
  "world": "ridge",
  "model": "gz_x500_lidar_down",
  "modelPose": "0,0,0,0,0,0",
  "worldEnv": {
    "PX4_GZ_WORLD": "ridge"
  }
}
```

- For moving platform:

```json
{
  "worldProfile": "moving_platform",
  "world": "moving_platform",
  "model": "gz_standard_vtol",
  "modelPose": "0,0,2.2,0,0,0",
  "worldEnv": {
    "PX4_GZ_WORLD": "moving_platform",
    "PX4_GZ_MODEL_POSE": "0,0,2.2",
    "PX4_GZ_PLATFORM_VEL": "1.0",
    "PX4_GZ_PLATFORM_HEADING_DEG": "0"
  }
}
```

UI requirements:

- ROS2Panel Connection tab gets a `World Profile` dropdown.
- Selecting a world profile auto-suggests compatible model(s).
- Show warnings for risky/unsupported combinations:
  - `lawn` -> warn about low frame rate / possible segfaults.
  - `ridge` without lidar/rangefinder model -> warn that terrain-following value is limited.
  - `moving_platform` without adjusted `PX4_GZ_MODEL_POSE` -> warn that vehicle may spawn below/inside platform.
- Advanced settings:
  - raw `PX4_GZ_WORLD`
  - raw `PX4_GZ_MODEL_POSE`
  - moving platform speed/heading

Trace requirements:

`manifest.json` must include:

```json
{
  "gazeboWorld": {
    "profile": "ridge_terrain",
    "world": "ridge",
    "modelPose": "0,0,0,0,0,0",
    "env": {
      "PX4_GZ_WORLD": "ridge"
    },
    "source": "PX4 docs Gazebo Worlds"
  }
}
```

Test matrix additions:

- `gz_world_default_camera_video`
- `gz_world_aruco_downward_camera`
- `gz_world_ridge_terrain_lidar`
- `gz_world_walls_avoidance`
- `gz_world_windy_mission_tracking`
- `gz_world_moving_platform_vtol`

Sources:

- https://docs.px4.io/main/en/sim_gazebo_gz/worlds

---

### Module B: Video Stream Backend + UI

**Priority:** P1

Backend file:

```text
tools/ui/context/video_stream_context.py
```

Minimum API:

```python
setVideoSource(droneId: str, host: str, port: int, protocol: str)
startVideoProbe(droneId: str)
stopVideoProbe(droneId: str)
startStream(url: str, droneId: str)
stopStream(droneId: str)
getVideoStatus(droneId: str) -> dict
videoStatusChanged(droneId: str, status: dict)
```

Status states:

```text
unconfigured
waiting
receiving
stalled
error
```

PX4/Gazebo defaults:

```text
px4_1/drone1 -> udp://0.0.0.0:5600
px4_2/drone2 -> udp://0.0.0.0:5601
px4_3/drone3 -> udp://0.0.0.0:5602
```

UI:

- ROS2Panel Video section
- GimbalPanel Live View
- Map marker camera badge
- Map PIP overlay only when `receiving`
- Placeholder/status when waiting

Tests:

- `tests/test_video_stream_context.py`
- no real stream required

---

### Module C: ROS2 Topic Discovery + Health

**Priority:** P1/P2

Backend:

- Extend `ROS2Context`
- Add:
  - `discoverTopics(namespace: str) -> list`
  - `getTopicHealth(namespace: str) -> dict`
  - `subscribeToTopic(topic: str, droneId: str)`
  - `topicMessage(topic, json_data, timestamp)`
  - rate/age tracking
- Export health to trace bundle.

UI:

- ROS2Panel Topics tab:
  - Discover
  - Filter
  - Rate badges
  - Last message age
  - JSON preview
  - Watch list

Required PX4 minimum topics:

```text
/<ns>/fmu/out/vehicle_status
/<ns>/fmu/out/vehicle_global_position
/<ns>/fmu/out/vehicle_local_position
/<ns>/fmu/out/vehicle_odometry
/<ns>/fmu/out/vehicle_attitude
/<ns>/fmu/out/vehicle_control_mode
/<ns>/fmu/out/battery_status
/<ns>/fmu/out/failsafe_flags
/<ns>/fmu/out/mission_result
```

---

### Module D: ROS2 Bag Recorder

**Priority:** P2

Use existing:

```text
skymeshx/ros/bag_recorder.py
```

Extend through:

```text
tools/ui/context/ros2_context.py
```

Backend slots:

- `startBagRecord(topics, output_dir, preset)`
- `stopBagRecord() -> str`
- `getBagStatus() -> dict`

Signals:

- `bagRecordStarted(path)`
- `bagRecordStopped(path, size_mb)`
- `bagRecordError(message)`

Presets:

- `minimal_mission`
- `full_px4_out`
- `camera_gimbal`
- `swarm_multi_vehicle`

UI:

- ROS2Panel Bag tab
- red recording indicator
- output path
- bag size/duration
- open in FlightLog

Tests:

- `tests/test_ros2_bag_recorder.py`

---

### Module F: SITL Test Checklists + Smoke Tests

**Priority:** P2

Docs:

```text
docs/testing/sitl-basic-connectivity.md
docs/testing/sitl-seeding-mission.md
docs/testing/sitl-solar-mission.md
docs/testing/sitl-camera-stream.md
docs/testing/sitl-ros2-bridge.md
docs/testing/sitl-multi-vehicle.md
docs/testing/sitl-bag-workflow.md
```

Tests:

```text
tests/test_sitl_smoke.py
```

Rules:

- `@pytest.mark.sitl`
- skipped unless `SITL_AVAILABLE=1`
- Linux only
- never required for normal CI

---

### Module G: ROS2 Panel Overhaul

**Priority:** P3, but UI clarity becomes important once A-D exist.

Tabs:

```text
Connection
Topics
Bag
Video
Debug
```

Bob owns QML layout. Codex owns context/API correctness.

---

## Final Recommended Order

1. Trace foundation: `TraceLogger` + `TraceContext` + manifest + JSONL.
2. Video source config/probe/status, no full decoding yet.
3. ROS2 topic health export.
4. Bag recorder UI/API with presets.
5. SITL launch profile improvements.
6. Topic browser UI.
7. Map/Gimbal live video display.
8. SITL checklists and skipped smoke tests.
9. Trace analyzer.
10. ROS2 panel tab overhaul.

Reason:

The user's main risk is not that features are impossible; the risk is that Linux-only sim failures are opaque. Trace and health artifacts must come first.

---

## Concrete First Task Split

### Codex Task 1

Implement Trace Foundation:

- `skymeshx/core/trace_logger.py`
- `tools/ui/context/trace_context.py`
- service locator registration
- session manifest
- JSONL appenders
- hardware-free tests

### Bob Task 1

Design ROS2Panel integration points:

- where Trace Session controls live
- where Video Source controls live
- how Connection/Topics/Bag/Debug tabs should be arranged

### Codex Task 2

Implement Video Source Probe:

- `tools/ui/context/video_stream_context.py`
- UDP port config per drone
- state machine
- no real decoded video required in MVP
- trace events

### Bob Task 2

Map/Gimbal UI placeholder:

- camera badge on selected drone
- waiting/receiving/stalled status
- no blank video rectangle until stream is receiving

---

## Decisions Needed From User

1. Namespace default for PX4 Gazebo: `px4_N` or `uav_N`?
   - Recommendation: `px4_N` for PX4 Gazebo, keep `uav_N` as alias.
2. First camera target:
   - `gz_x500_mono_cam`
   - `gz_x500_gimbal`
   - Recommendation: `gz_x500_gimbal`, because solar/camera/gimbal workflow needs it.
3. First video implementation:
   - probe/status only
   - snapshot frames
   - full live QML video
   - Recommendation: probe/status first, then snapshot, then live video.
4. Trace location:
   - `trace_runs/`
   - `logs/sim_traces/`
   - Recommendation: `trace_runs/` because it is not a normal rotating log folder and should be easy to zip/send.
5. ROS2 distro:
   - Humble only?
   - Humble + Jazzy?
   - Recommendation: Humble first, because existing docs use Humble.

---

## Risks

### Video Decode Risk

GStreamer -> QML frame transfer can become platform-specific. Start with stream probe/status and make live video a second step.

### PX4 Namespace Drift

Repo docs currently use `uav_N`; PX4 examples often use `px4_N`. Make namespace explicit everywhere and record it in manifest.

### MAVLink/PX4 Confusion

Do not route PX4 mission tests through ArduPilot assumptions. Keep PX4 ROS2/uXRCE mission path explicit.

### Trace Volume

TraceLogger must rate-limit ROS2 topic events and high-rate telemetry. Log health/rate summaries by default, not every message.

### SITL Tests in Normal CI

SITL smoke tests must be opt-in only.

---

## Acceptance Criteria For Starting Linux Sim Test Phase

Minimum:

- Trace session can be started/stopped.
- Manifest records PX4 model, namespace, video port, scenario.
- ROS2 topic health snapshot is exported.
- Bag recording can be started/stopped or at least documented as CLI fallback.
- Video port can be configured per drone.
- Map/Gimbal UI does not show broken video before stream is available.
- Mission upload/start/pause/abort are traced.
- Active waypoint vs drone distance is traceable.

Better:

- ROS2Panel has Connection/Topics/Bag/Video/Debug tabs.
- Topic browser shows topic rates.
- Video snapshot/live view works.
- Trace analyzer produces Markdown summary.

---

## Coordination File

Use Bob's coordination target:

```text
docs/project/px4-gazebo-sim/px4-gazebo-sim-collab-feedback.md
```

This synthesis file is the merged planning baseline. Future implementation updates should go to the collab feedback file, not to this synthesis file unless the plan changes materially.
