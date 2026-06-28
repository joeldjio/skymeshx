# PX4 ROS2 Gazebo Simulation Test Feedback

**Created:** 2026-06-26  
**Purpose:** Vorbereitung fuer Linux-basierte PX4 + ROS2 + Gazebo Tests nach Abschluss der Camera/Seeding/Solar Implementierung.  
**Context:** Der Nutzer kann die Simulation nur auf Linux ausfuehren und waehrend der Tests kein direktes Live-Feedback an Codex/Bob geben. Deshalb muss die Software aussagekraeftige Traces, Debugdaten, Logs und ROS2 Bags erzeugen, damit wir spaeter offline analysieren koennen.

---

## Ausgangslage

Der Nutzer konnte PX4 bereits mit Kamera, Gimbal und weiteren Sensoren simulieren, bisher aber vor allem mit QGroundControl als Ground Station. Ziel ist, dieselben Simulationsfaehigkeiten in SkyMeshX nutzbar zu machen:

- PX4 SITL mit Gazebo/GZ
- PX4 Multi-Vehicle Simulation
- PX4 SIH fuer schnelle/headless Tests
- ROS2/uXRCE-DDS Topic Bridge
- Camera/Gimbal/Sensor Simulation
- Video Stream Anzeige in der SkyMeshX Map
- ROS2 Bag Recording und spaetere Analyse
- Mission Planning, Seeding, Solar Inspection und Swarm zusammen testen

Offizielle PX4 Hinweise, die fuer diese Planung relevant sind:

- PX4 Gazebo Modelle wie `gz_x500_mono_cam` und `gz_x500_gimbal` koennen Kamera-Video streamen; default ist UDP/RTP auf Port `5600`.
- QGroundControl nutzt fuer diesen Stream `UDP h.264 Video Stream` mit Port `5600`; direkt per GStreamer ist ebenfalls moeglich.
- Bei Multi-Vehicle Video Streams werden Ports ab `5600` fortlaufend genutzt: `5600`, `5601`, `5602`, ...
- Multi-Vehicle Gazebo kann mit eindeutigen PX4 Instanzen (`-i`) und Namespaces/Topics wie `/px4_1/fmu/out/...`, `/px4_2/fmu/out/...` betrieben werden.
- SIH ist headless, schnell und reproduzierbar, aber nur der Quadrotor ist stabil empfohlen; andere Vehicle Types sind experimentell.

Sources:

- https://docs.px4.io/main/en/simulation/
- https://docs.px4.io/main/en/sim_gazebo_gz/
- https://docs.px4.io/main/en/sim_gazebo_gz/multi_vehicle_simulation
- https://docs.px4.io/main/en/sim_sih/

---

## Lokaler Stand im Repo

Vorhandene Bausteine:

- `docs/setup/px4-sitl-automation.md`
- `docs/setup/px4-mission-upload.md`
- `docs/setup/px4-mission-monitoring.md`
- `docs/setup/px4-frame-visualization.md`
- `skymeshx/ros/px4_bridge.py`
- `skymeshx/ros/px4_mission.py`
- `skymeshx/ros/bag_recorder.py`
- `tools/ui/context/ros2_context.py`
- `tools/ui/context/camera_context.py`
- ROS2 Panel existiert bereits.
- Bag recorder wrapper existiert bereits, ist aber fuer Sim-Test-Triage noch nicht als durchgaengiges "Trace Bundle" gedacht.

Wichtige Luecken:

- Video UDP/RTP Port ist in der UI aktuell nicht frei konfigurierbar.
- Video Stream wird nicht in der Map angezeigt.
- Es gibt keine robuste "Stream verfuegbar / nicht verfuegbar" Anzeige pro Drone.
- ROS2 Topic Health ist nicht ausreichend als Test-Artefakt exportiert.
- Es gibt kein einheitliches Sim-Test Trace Bundle, das alle spaeter benoetigten Daten zusammenhaelt.
- Multi-Vehicle ROS2 + Swarm + Mission Planning braucht eine klare Namens-/Port-Konvention.
- Camera/Gimbal Simulation muss mit Mission, Solar Preview und Map zusammen getestet werden.

---

## Zielbild

Nach Umsetzung soll der Nutzer auf Linux einen Testlauf starten koennen und danach einen Ordner an Codex/Bob geben, z.B.:

```text
trace_runs/
  2026-06-26_153012_px4_gz_x500_gimbal_2uav/
    manifest.json
    app.log
    ui_events.jsonl
    mission_trace.jsonl
    ros2_topic_health.json
    px4_topics_snapshot.txt
    ros2_bag/
    video/
      uav_1_stream_probe.json
      uav_2_stream_probe.json
    screenshots/
    config/
      sim_config.json
      mission_config.json
      camera_config.json
```

Dieser Ordner muss ausreichen, um spaeter zu beantworten:

- Welche PX4/Gazebo/SIH Variante lief?
- Welche Modelle wurden gestartet?
- Welche ROS2 Namespaces und PX4 Instanzen wurden benutzt?
- Welche UDP Video Ports waren konfiguriert und erreichbar?
- Welche ROS2 Topics waren vorhanden?
- Welche Topics wurden gebaggt?
- Welche Mission wurde geplant, previewed, uploaded und gestartet?
- Welche Drone hat welche Waypoints bekommen?
- Welche Frames/Koordinaten wurden verwendet?
- Was sah die UI zum Zeitpunkt von Fehlern?
- Welche Kamera/Gimbal/Capability-Zustaende wurden erkannt?

---

## Konventionen fuer PX4/Gazebo/ROS2 Tests

### Drone IDs

SkyMeshX UI IDs:

```text
drone1, drone2, drone3
```

PX4 ROS2 namespaces fuer Gazebo Multi-Vehicle:

```text
px4_1, px4_2, px4_3
```

Alternative fuer bisherige Repo-Dokus:

```text
uav_1, uav_2, uav_3
```

Entscheidung erforderlich: Fuer PX4 Gazebo Multi-Vehicle sollte die App `px4_N` als Default akzeptieren, weil die offiziellen Beispiele `/px4_1/fmu/...` zeigen. Die UI darf aber `uav_N` weiter erlauben.

### Video UDP Ports

Default:

```text
drone1 / px4_1 -> UDP RTP 5600
drone2 / px4_2 -> UDP RTP 5601
drone3 / px4_3 -> UDP RTP 5602
```

Die UI muss pro Drone folgende Felder erlauben:

```json
{
  "videoEnabled": true,
  "videoProtocol": "rtp-h264-udp",
  "videoHost": "0.0.0.0",
  "videoPort": 5600,
  "autoDetect": true
}
```

Wichtig: Der Stream wird erst angezeigt, wenn er wirklich verfuegbar ist. Vorher zeigt die Map nur einen neutralen Status:

```text
Camera stream: waiting on udp://0.0.0.0:5600
```

### ROS2 Topic Mindestset

Pro Drone sollte mindestens beobachtet/geprueft werden:

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
/<ns>/fmu/in/vehicle_command
/<ns>/fmu/in/trajectory_setpoint
/<ns>/fmu/in/offboard_control_mode
```

Optional fuer Sensor-/Camera-/Gimbal-Sim:

```text
/<ns>/fmu/out/sensor_combined
/<ns>/fmu/out/vehicle_gps_position
/<ns>/fmu/in/vehicle_visual_odometry
/<ns>/fmu/out/gimbal_device_attitude_status
/<ns>/fmu/in/gimbal_device_set_attitude
```

Die genauen Gimbal Topic-Namen muessen gegen `px4_msgs` und die verwendete PX4-Version validiert werden.

---

## Trace- und Debug-Anforderungen

### 1. Trace Manifest

Neue Datei pro Testlauf:

```text
trace_runs/<timestamp>_<scenario>/manifest.json
```

Pflichtfelder:

```json
{
  "schemaVersion": 1,
  "createdAt": "2026-06-26T15:30:12+02:00",
  "scenario": "px4_gz_x500_gimbal_seeding_single",
  "host": {
    "os": "linux",
    "distro": "ubuntu-22.04",
    "kernel": "...",
    "python": "...",
    "rosDistro": "humble"
  },
  "px4": {
    "px4Dir": "/home/iruz/PX4-Autopilot",
    "gitCommit": "...",
    "simMode": "gz",
    "model": "gz_x500_gimbal",
    "world": "default"
  },
  "vehicles": [
    {
      "droneId": "drone1",
      "px4Instance": 1,
      "namespace": "px4_1",
      "model": "gz_x500_gimbal",
      "pose": "0,0,0,0,0,0",
      "videoPort": 5600
    }
  ],
  "artifacts": {
    "appLog": "app.log",
    "uiEvents": "ui_events.jsonl",
    "missionTrace": "mission_trace.jsonl",
    "ros2Bag": "ros2_bag/",
    "topicHealth": "ros2_topic_health.json"
  }
}
```

### 2. UI Event Trace

Neue JSONL Datei:

```text
ui_events.jsonl
```

Events:

- App started
- ROS2 bridge start/stop
- Drone add/remove
- Camera stream configured
- Camera stream available/unavailable
- Mission mode changed
- Boundary/solar row/exclusion zone draw events
- Preview generated
- Upload started/finished
- Start/Pause/Abort pressed
- Map overlay updated
- Errors/warnings

Beispiel:

```json
{"t":"2026-06-26T15:33:01.123+02:00","type":"mission_upload_started","droneId":"drone1","mode":"seeding","waypoints":482}
```

### 3. Mission Trace

Neue JSONL Datei:

```text
mission_trace.jsonl
```

Muss enthalten:

- Boundary Points
- Generated preview hash
- Waypoint count
- Drop point count
- Mission split/chunk info, falls vorhanden
- Upload ACK/Reject
- Start mode command
- PX4 mission_result changes
- Current mission item over time
- Position-vs-active-waypoint distance

Wichtig fuer den zuletzt beobachteten Fehler "Drohne flog neben WP":

Pro Tick im Mission Trace:

```json
{
  "type": "wp_tracking",
  "droneId": "drone1",
  "currentSeq": 12,
  "droneLat": -35.36352,
  "droneLon": 149.16465,
  "targetLat": -35.36360,
  "targetLon": 149.16470,
  "distanceToWpM": 9.4,
  "acceptanceRadiusM": 2.0,
  "frame": "GLOBAL_RELATIVE_ALT"
}
```

### 4. ROS2 Topic Health Snapshot

Neue Datei:

```text
ros2_topic_health.json
```

Pro Topic:

```json
{
  "/px4_1/fmu/out/vehicle_odometry": {
    "seen": true,
    "messageCount": 1832,
    "lastMessageAgeSec": 0.04,
    "estimatedHz": 29.8,
    "qos": "sensor_data"
  }
}
```

### 5. ROS2 Bag Recording

Bag Recording muss als First-Class Feature im ROS2 Tab funktionieren:

- Start/Stop Recording
- Topic Presets:
  - `minimal_mission`
  - `full_px4_out`
  - `camera_gimbal`
  - `swarm_multi_vehicle`
- Bag output path wird im Manifest referenziert.
- UI zeigt Aufnahmedauer und Bag-Groesse.

Default Preset `minimal_mission`:

```text
/<ns>/fmu/out/vehicle_status
/<ns>/fmu/out/vehicle_global_position
/<ns>/fmu/out/vehicle_local_position
/<ns>/fmu/out/vehicle_odometry
/<ns>/fmu/out/vehicle_attitude
/<ns>/fmu/out/vehicle_control_mode
/<ns>/fmu/out/mission_result
/<ns>/fmu/out/failsafe_flags
```

---

## Video Stream Anforderungen

### Backend

Neue oder erweiterte Komponente:

```text
tools/ui/context/video_context.py
```

Aufgaben:

- pro Drone UDP/RTP/H264 Quelle konfigurieren
- Port pruefen/proben
- Stream status publishen:
  - `unconfigured`
  - `waiting`
  - `receiving`
  - `stalled`
  - `error`
- optional GStreamer Pipeline starten
- optional Snapshot fuer Map Overlay bereitstellen
- Logs in Trace Bundle schreiben

Minimal API fuer QML:

```python
setVideoSource(droneId: str, host: str, port: int, protocol: str)
startVideoProbe(droneId: str)
stopVideoProbe(droneId: str)
getVideoStatus(droneId: str) -> dict
videoStatusChanged(droneId: str, status: dict)
```

### UI

Map:

- Drone marker zeigt Camera Badge, wenn Stream konfiguriert ist.
- Kleines Video Preview Panel auf der Map, aber nur wenn Stream `receiving`.
- Wenn Stream noch nicht da ist: kompakter Status statt leerer/kaputter Videoflaeche.
- Bei Multi-Vehicle: Auswahl "Video von selected drone".

Gimbal/Camera Panel:

- Video Port Input
- Auto-detect default: `5600 + instanceIndex - 1`
- Button "Probe Stream"
- Status: waiting/receiving/stalled/error

### GStreamer Pipeline

Default Pipeline fuer PX4 Gazebo:

```bash
gst-launch-1.0 -v udpsrc port=5600 \
  caps='application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264' \
  ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink sync=false
```

Fuer Qt/QML sollte nicht direkt `autovideosink` genutzt werden. Implementierungsoptionen:

1. Erst MVP: externer GStreamer Probe + Status + Snapshot.
2. Dann Map-Overlay: GStreamer -> appsink -> QImage/QVideoFrame -> QML Image/VideoOutput.
3. Alternativ lokaler UDP Stream an QtMultimedia, falls stabil genug.

---

## ROS2 Tab Anforderungen

Der bestehende ROS2 Tab soll fuer Sim-Test-Triage erweitert werden:

### Topic Browser

- `ros2 topic list` equivalent anzeigen
- Filter nach namespace/drone
- Topic status:
  - seen/unseen
  - Hz
  - last age
  - type, falls ermittelbar

### Bridge Health

Pro Drone:

- namespace
- bridge active
- last telemetry age
- vehicle_status.nav_state
- arming_state
- failsafe flags
- current mission seq
- local position NED + ENU

### Bag Controls

- Preset Auswahl
- Bag name/scenario name
- Start/Stop
- Auto-start bag when scenario starts
- Auto-stop bag on app exit / sim stop

### Trace Bundle Controls

- "Start Trace Session"
- "Stop Trace Session"
- "Open Trace Folder"
- "Export Trace Summary"

---

## Mission Planning + Swarm Integration Checks

### Single Vehicle

Test sequence:

1. Start PX4 Gazebo with `gz_x500_gimbal` or `gz_x500_mono_cam`.
2. Start uXRCE-DDS Agent.
3. Start SkyMeshX.
4. Start ROS2 bridge for `drone1` namespace `px4_1`.
5. Configure video port `5600`.
6. Verify stream status.
7. Draw field.
8. Generate seeding preview.
9. Upload mission.
10. Start mission.
11. Record ROS2 bag + mission trace.
12. Confirm map drone position, active waypoint, and PX4 mission_result agree.

### Multi Vehicle

Test sequence:

1. Start `px4_1`, `px4_2`, optionally `px4_3`.
2. Use video ports `5600`, `5601`, `5602`.
3. Start bridge per namespace.
4. Verify topics for each namespace.
5. Generate swarm/seeding/coverage split.
6. Verify each drone has distinct uploaded mission.
7. Confirm start/abort affects selected/all intended drones only.

### SIH

Use for:

- fast mission upload/start/abort regression
- ROS2 topic health
- bag recording
- mission monitoring

Do not use for:

- video stream
- Gazebo camera/gimbal visual checks
- realistic sensor/camera simulation

---

## Required Implementation Work

### Phase PX4-SIM-1: Trace Infrastructure

Owner suggestion: Codex

- Create `tools/ui/context/trace_context.py`
- Create trace session folder with `manifest.json`
- Append JSONL UI events and mission events
- Wire critical signals:
  - ROS2 bridge status
  - camera/video status
  - mission upload/start/pause/abort
  - preview generation
  - map overlay updates
- Add hardware-free tests for trace writing.

### Phase PX4-SIM-2: Video Stream Configuration

Owner suggestion: Codex backend + Bob UI

- Add `VideoContext`
- Add configurable UDP/RTP/H264 source per drone
- Add stream probe/status
- Add QML controls in Camera/Gimbal or ROS2 panel
- Add Map video badge and conditional preview area
- Do not show broken/blank video panel before stream is available.

### Phase PX4-SIM-3: ROS2 Topic Health + Bag Presets

Owner suggestion: Codex

- Extend `ROS2Context` with topic discovery/health.
- Add topic health export to trace bundle.
- Expose bag recorder controls to QML.
- Add presets for mission/camera/swarm.

### Phase PX4-SIM-4: PX4/Gazebo Launch Profiles

Owner suggestion: Bob UI + Codex backend review

- Extend SITL automation config:
  - model: `gz_x500`, `gz_x500_mono_cam`, `gz_x500_gimbal`
  - namespace mode: `px4_N` or `uav_N`
  - vehicle count
  - pose list
  - video ports
  - world
  - speed factor
- Add profile export to manifest.

### Phase PX4-SIM-5: Mission/Sensor Integration Test Matrix

Owner suggestion: Both

Scenarios:

- `sih_single_mission_upload`
- `gz_x500_single_coverage`
- `gz_x500_gimbal_solar`
- `gz_x500_mono_cam_video_map`
- `gz_x500_multi_swarm_2uav`
- `gz_x500_seeding_large_preview`

Each scenario must produce a trace bundle.

---

## Acceptance Criteria

Before Linux-only simulation testing begins:

- UI can configure video UDP port per drone.
- Map does not show video until stream is receiving.
- ROS2 tab can show required PX4 topics per namespace.
- ROS2 bag can start/stop from UI.
- Trace bundle can be started/stopped from UI.
- Mission upload/start events are traceable.
- Active waypoint distance to drone is recorded.
- Multi-vehicle namespace/port mapping is explicit in manifest.
- Bob/Codex can analyze a failed test run from files alone.

---

## Open Questions

1. Which PX4 branch/version will be used for Linux tests?
2. Which ROS2 distro: Humble only, or Jazzy as well?
3. Which Gazebo version: Garden/Harmonic?
4. Which camera model will be first target: `gz_x500_mono_cam` or `gz_x500_gimbal`?
5. Should SkyMeshX use namespaces `px4_N` by default for PX4 simulation, while preserving `uav_N` as alias?
6. Do we need live decoded video in QML immediately, or is probe/status/snapshot enough for the first simulation test?
7. Should trace bundles live under `trace_runs/` or `logs/sim_traces/`?

---

## Immediate Recommendation

Do not wait until the full camera/seeding/solar plan is "perfect" before adding trace support. The next implementation should be:

1. `TraceContext` + manifest + JSONL event logs.
2. ROS2 topic health snapshot.
3. Bag preset recording from UI.
4. Video port config + stream availability probe.

This gives enough observability for the Linux PX4/Gazebo tests where the user cannot provide live feedback.
