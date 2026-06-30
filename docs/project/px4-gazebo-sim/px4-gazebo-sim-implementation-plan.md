# PX4 + Gazebo + ROS2 — Simulation Integration Plan
# Parallel Work Division: Bob (QML/UI) & Codex (Backend/Python)

**Erstellt:** 2026-06-26  
**Inputs:** Bob Plan + Codex Plan + Codex Synthesis (alle drei konsolidiert)  
**Koordination:** `docs/project/px4-gazebo-sim/px4-gazebo-sim-collab-feedback.md`  
**Regeln:** `docs/project/px4-gazebo-sim/px4-gazebo-sim-rules.md`  
**Voraussetzung:** `camera-seeding-solar-implementation-plan.md` abgeschlossen

---

## Ziel

Nach Abschluss dieses Plans kann der Nutzer auf Linux:

1. PX4 SITL + Gazebo (single & multi-vehicle, alle Welten) von der GCS starten
2. Kamera/Gimbal-Simulation in Gazebo nutzen, Video-Stream im GCS empfangen
3. Video-Overlay auf der Map sehen — aber **nur wenn Stream wirklich ankommt**
4. ROS2 Topics live im Topic Browser beobachten + in Bags aufnehmen
5. Alle Testläufe als **Trace Bundle** exportieren → Offline-Analyse ohne Live-Feedback möglich
6. Mission Planning / Swarm / Camera / Seeding / Solar **gegen SITL testen**

---

## Architektur (final konsolidiert)

```
Linux Host (Ubuntu 22.04, ROS2 Humble)
├── Gazebo Ignition (gz_x500_gimbal, gz_x500_mono_cam, multi-vehicle)
│   ├── Camera Plugin  ──────────────────────────────── UDP 5600/5601/5602
│   └── Sensor Plugins (IMU, GPS, Baro, Lidar)
├── PX4 SITL  ──────────────────────────────────────── uXRCE-DDS → UDP 8888
├── MicroXRCEAgent udp4 -p 8888
├── ROS2 Humble
│   ├── /px4_1/fmu/out/vehicle_status   ← Telemetrie
│   ├── /px4_1/fmu/out/mission_result   ← Mission-Tracking
│   ├── /px4_1/camera/image_raw          ← aus Camera Plugin
│   └── ros2 bag record ...              ← Bag Recorder
└── skymeshx GCS (PySide6 + QML)
    ├── MAVLink tcp:127.0.0.1:5762      ← ArduCopter SITL / PX4 MAVLink
    ├── ROS2 Bridge (px4_bridge.py)      ← PX4 Telemetrie, Offboard, Mission
    ├── VideoContext  ───────────────── UDP/RTP Probe → Status → Snapshot
    ├── TraceLogger + TraceContext ────── Trace Bundle pro Session
    └── ROS2 Bag Recorder               ← Presets: minimal_mission, full_px4_out
```

### Namespace-Konvention (fix)

| Modus | Default Namespace | Beispiel |
|-------|------------------|---------|
| PX4 Gazebo Multi-Vehicle | `px4_N` | `/px4_1/fmu/out/…` |
| PX4 Single-Vehicle (bestehend) | `uav_1` | `/uav_1/fmu/out/…` |
| Beide akzeptiert | frei editierbar in UI | im `manifest.json` festgehalten |

### MAVLink vs. ROS2 Trennung

PX4/uXRCE-DDS → ROS2 Bridge für Offboard, Topics, Formation.  
PX4 MAVLink optional für Camera/Gimbal-Kommandos — **kein automatisches ArduPilot-Routing** für PX4-Sim.

```json
{
  "autopilot": "px4",
  "controlPath": "ros2_uxrce",
  "optionalMavlinkEndpoint": "udp://127.0.0.1:14540",
  "namespace": "px4_1"
}
```

---

## Multi-Vehicle Ports (fix)

| Drohne | MAVLink | uXRCE-DDS | Video UDP |
|--------|---------|-----------|----------|
| px4_1 / uav_1 | tcp:127.0.0.1:5762 | UDP 8888 | 5600 |
| px4_2 / uav_2 | tcp:127.0.0.1:5763 | UDP 8889 | 5601 |
| px4_3 / uav_3 | tcp:127.0.0.1:5764 | UDP 8890 | 5602 |

---

## Module und Aufgabenteilung

> **Regel:** Codex übernimmt alle komplexen Backend-Module (E, A, B.1, C, D, F).  
> Bob übernimmt alle QML-UI-Module (A.2, B.2, G) und Test-Checklisten.

---

### MODUL E — Trace + Bundle Foundation
**Priorität: P0 — wird zuerst implementiert**  
**Besitzer: Codex Backend + Bob UI-Controls**  
**Grund:** Ohne Trace-Bundle sind Linux-Testfehler offline nicht analysierbar.

**Status 2026-06-26 / Codex:**
- [x] E.1 `TraceLogger` implementiert
- [x] E.2 Trace Bundle Struktur implementiert
- [x] E.3 `TraceContext` implementiert und als `trace` registriert
- [x] E.5 `tools/analyze_trace.py` implementiert
- [x] E.6 Tests geschrieben: `tests/test_trace_logger.py`, `tests/test_trace_context.py`
- [x] Bob-Test gruen: `pytest tests/test_trace_logger.py tests/test_trace_context.py tests/test_video_stream_context.py -v` → 39 passed

#### E.1 — TraceLogger Python Singleton (Codex)

**Datei:** `skymeshx/core/trace_logger.py`

```python
logger = TraceLogger.get()               # Singleton — überall aufrufbar

# Session Management
logger.start_session(scenario: str, sim_config: dict) -> str   # gibt Bundle-Pfad zurück
logger.stop_session() -> str

# Event Logger (rate-limited: max 1/s pro Topic)
logger.log_ui_event(event_type: str, data: dict)
logger.log_mission_event(event_type: str, data: dict)
logger.log_wp_tracking(drone_id, seq, drone_lat, drone_lon,
                       target_lat, target_lon, distance_m, frame)
logger.log_ros2_health(topic, hz, last_age_s, qos)
logger.log_video_status(drone_id, status, port)
logger.log_error(source, msg)
logger.export_markdown(path)             # Markdown-Report für Remote-Analyse
```

Event-Typen:
- `app/session`, `qml_action`, `bridge_status`, `topic_health`
- `video_status`, `camera_status`, `gimbal_status`
- `mission_preview`, `mission_upload`, `mission_start`, `mission_pause`, `mission_abort`
- `wp_tracking`, `error`, `warning`

**Rate-Limiting:** ROS2 Topic-Events max 1 Eintrag/s pro Topic. MAVLink: nur State-Changes.

#### E.2 — Trace Bundle Struktur (Codex)

```
trace_runs/
  <timestamp>_<scenario>/
    manifest.json           ← Pflicht: host, px4, vehicles, world, artifacts
    app.log                 ← Kopie/Symlink des aktuellen syslog
    ui_events.jsonl         ← Button-Klicks, Tab-Wechsel, Wizard-Aktionen
    mission_trace.jsonl     ← Boundary, Preview, Upload, WP-Tracking
    ros2_topic_health.json  ← Topic-Raten, last age, QoS (Snapshot bei Stop)
    video/
      <droneId>_stream_probe.json
    ros2_bag/               ← von Bag Recorder (falls aktiv)
    config/
      sim_config.json       ← Launch-Profil (Model, World, Namespace, Ports)
      mission_config.json   ← aktive Mission-Parameter
```

**manifest.json Pflichtfelder:**
```json
{
  "schemaVersion": 1,
  "scenario": "gz_x500_gimbal_seeding_single",
  "createdAt": "...",
  "host": { "os": "linux", "distro": "ubuntu-22.04", "rosDistro": "humble" },
  "px4": { "gitCommit": "...", "simMode": "gz", "model": "gz_x500_gimbal", "world": "default" },
  "vehicles": [{ "droneId": "drone1", "namespace": "px4_1", "videoPort": 5600 }],
  "artifacts": { "uiEvents": "ui_events.jsonl", "missionTrace": "mission_trace.jsonl" }
}
```

#### E.3 — TraceContext QML Wrapper (Codex)

**Datei:** `tools/ui/context/trace_context.py`

```python
# Properties
sessionActive: bool
sessionPath: str
sessionScenario: str

# Slots
startSession(scenario: str)
stopSession()
exportSummary()
openFolder()

# Signals
sessionStarted(path: str)
sessionStopped(path: str)
```

In `service_locator.py` als `trace` registrieren.

#### E.4 — Trace Bundle Controls UI (Bob)

**Datei:** `tools/ui/qml/panels/ROS2Panel.qml` (Debug Tab)

- "Start Trace Session" Button + Szenario-Name-Eingabe
- "Stop + Export" Button
- Session-Status (aktiv/inaktiv, Pfad)
- Laufzeit-Anzeige
- "Ordner öffnen" Link

#### E.5 — Trace Analyzer CLI (Codex)

**Datei:** `tools/analyze_trace.py`

```bash
python tools/analyze_trace.py trace_runs/2026-06-26_gz_x500/
# → Markdown Report: MAVLink-Lücken, Topic Drop-outs, WP-Tracking, Mission-Timing
```

#### E.6 — Tests (Codex)

```
tests/test_trace_logger.py    ← hardware-free, unittest
tests/test_trace_context.py   ← hardware-free, QObject mock
```

---

### MODUL A — PX4 SITL / Gazebo / SIH Launch Profiles
**Priorität: P1**  
**Besitzer: Codex Backend + Bob UI**

**Status 2026-06-26 / Codex:**
- [x] A.1 Launch Backend Slots implementiert: `startSitl`, `startMultiSitl`, `startSihSitl`, `stopSitl`, `stopAllSitl`, `getSitlStatus`, `listLaunchProfiles`
- [x] A.2 World/Profile-Daten in Launch-Profilen beruecksichtigt
- [x] A.4 Tests geschrieben: `tests/test_ros2_sitl_launcher.py`
- [x] Bob-Test gruen: `pytest tests/test_ros2_sitl_launcher.py tests/test_ros2_bag_recorder.py -v` -> 11 passed

#### A.1 — Launch Backend (Codex)

**Datei:** `tools/ui/context/ros2_context.py` (erweitern)

Neue Slots:
```python
startSitl(profile: dict)          # profile = {model, world, namespace, videoPort, pose}
startMultiSitl(profiles: list)    # Liste von Vehicle-Profiles
startSihSitl(profile: dict)       # kein Gazebo
stopSitl(namespace: str)
stopAllSitl()
getSitlStatus() -> dict           # {running, model, world, namespace, pid, uptime_s, gazebo_running}
listLaunchProfiles() -> list      # vordefinierte Profile
```

**Unterstützte Modelle:**
```
gz_x500             → Standard Quadcopter
gz_x500_mono_cam    → Forward-Kamera → UDP 5600
gz_x500_gimbal      → Gimbal + Downward-Kamera → UDP 5600
gz_x500_lidar_down  → Lidar rangefinder
gz_standard_vtol    → VTOL
gz_plane            → Fixed-Wing
sih_quadx           → SIH (kein Gazebo, headless)
```

#### A.2 — Gazebo World Profiles (Codex — komplex)

Launch-Profil um `worldProfile` erweitern:

| Profil | PX4 World | Einsatz |
|--------|-----------|---------|
| `empty_default` | `default` | Basis-Tests, Seeding, Solar |
| `aruco_precision_landing` | `aruco` | Downward-Camera, Precision Landing |
| `baylands_water` | `bayland` | Visuell, Über-Wasser |
| `ridge_terrain` | `ridge` | Terrain Following, Lidar |
| `walls_collision` | `walls` | APF, Collision Prevention |
| `windy_disturbance` | `windy` | Wind-Robustheit, Drift |
| `moving_platform` | `moving_platform` | PX4 v1.16+, Schiff/LKW |

Schema-Erweiterung:
```json
{
  "worldProfile": "ridge_terrain",
  "world": "ridge",
  "model": "gz_x500_lidar_down",
  "modelPose": "0,0,0,0,0,0",
  "worldEnv": { "PX4_GZ_WORLD": "ridge" }
}
```

Manifest muss `gazeboWorld` Block enthalten.

#### A.3 — SITL UI (Bob)

**Datei:** `tools/ui/qml/panels/ROS2Panel.qml` (Connection Tab)

- Model-Dropdown: alle Modelle aus A.1
- World-Profil-Dropdown mit Kompatibilitäts-Warnungen:
  - `lawn` → Warnung: low frame rate / segfaults
  - `ridge` ohne lidar-Modell → Warnung
  - `moving_platform` ohne angepasste `modelPose` → Warnung
- Namespace-Modus: `px4_N` / `uav_N` / custom
- Vehicle-Anzahl (1–5)
- Camera/Gimbal-Toggle (nur bei kompatiblen Modellen sichtbar)
- Video Base Port (default: 5600)
- Advanced: Raw `PX4_GZ_WORLD`, `PX4_GZ_MODEL_POSE`, Platform-Speed/Heading
- Start/Stop All + Status-Liste mit PID + Uptime

#### A.4 — Tests (Codex)

```
tests/test_ros2_sitl_launcher.py    ← subprocess mock, hardware-free
```

---

### MODUL B — Video Stream
**Priorität: P1**  
**Besitzer: Codex Backend + Bob UI**

#### B.1 — VideoContext Backend (Codex)

**Datei:** `tools/ui/context/video_stream_context.py`

State Machine pro Drone:
```
unconfigured → waiting → receiving
                       → stalled
                       → error
```

```python
# Properties
streamStatus: str     # "unconfigured" | "waiting" | "receiving" | "stalled" | "error"
streamUrl: str
droneId: str
frameWidth: int
frameHeight: int
fps: float
lastError: str

# Slots
setVideoSource(droneId: str, host: str, port: int, protocol: str)
startVideoProbe(droneId: str)       # UDP Port anpingen, Status aktualisieren
stopVideoProbe(droneId: str)
startStream(url: str, droneId: str)  # Phase 2: GStreamer
stopStream(droneId: str)
getVideoStatus(droneId: str) -> dict

# Signals
videoStatusChanged(droneId: str, status: str)
snapshotAvailable(droneId: str)     # Phase 2
```

**Phase 1 (MVP):** Probe + Status. Kein dekodiertes Video.  
**Phase 2 (später):** GStreamer appsink → QImage → QML Image.

Trace-Integration: `log_video_status()` bei jedem Status-Wechsel.

In `service_locator.py` als `videoStream` registrieren.

#### B.2 — Video UI (Bob)

**ROS2Panel** (Video-Sektion):
- Port-Eingabe pro Drone (default: `5600 + instanceIndex - 1`)
- "Probe Stream" Button
- Status-Badge: waiting / receiving / stalled / error mit Farbe

**MapView.qml** — Drone-Marker:
- Camera-Badge am Marker wenn Video konfiguriert
- PIP-Overlay **NUR** wenn `status === "receiving"` (absolut kein leeres Video-Rechteck!)
- Status-Text bei `waiting`: `Camera stream: waiting on udp://0.0.0.0:5600`

**GimbalPanel.qml** — Live View:
- Video-Widget mit Status-Overlay
- Placeholder wenn nicht `receiving`

#### B.3 — Tests (Codex)

```
tests/test_video_stream_context.py    ← hardware-free, state machine mock
```

---

### MODUL C — ROS2 Topic Discovery + Health
**Priorität: P1/P2**  
**Besitzer: Codex Backend + Bob UI**

**Status 2026-06-26 / Codex:**
- [x] C.1 `discoverTopics`, `getTopicHealth`, `subscribeToTopic`, `topicMessage` implementiert
- [x] Topic Health schreibt ueber `TraceLogger` in aktive Trace Sessions
- [x] Hardware-free Tests in `tests/test_ros2_sitl_launcher.py` enthalten
- [x] Bob-Test gruen: enthalten im Backend-Lauf `50 passed`

#### C.1 — Topic Backend (Codex)

**Datei:** `tools/ui/context/ros2_context.py` (erweitern)

```python
discoverTopics(namespace: str) -> list[str]
getTopicHealth(namespace: str) -> dict      # {topic: {hz, lastAgeSec, qos, seen}}
subscribeToTopic(topic: str, droneId: str)
topicMessage(topic: str, json_data: str, timestamp: float)  # Signal
```

Auto-Subscribe Mindestset:
```
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

Topic Health Export → `ros2_topic_health.json` im Trace Bundle.

#### C.2 — Topic Browser UI (Bob)

**ROS2Panel** (Topics Tab):
- "Discover" Button
- Filter-Eingabe (z.B. `/fmu/out/*`)
- Topic-Liste mit Hz-Badge, last-age, seen/unseen
- Topic anklicken → letzter Wert als kompaktes JSON
- "Watch List" Pinning

---

### MODUL D — ROS2 Bag Recorder
**Priorität: P2**  
**Besitzer: Codex Backend + Bob UI**

**Status 2026-06-26 / Codex:**
- [x] D.1 Bag Backend Aliase/Slots implementiert: `startBagRecord`, `stopBagRecord`, `getBagStatus`
- [x] Alte UI-API `startBagRecording`, `stopBagRecording`, `getBagRecordingStatus` bleibt kompatibel
- [x] Bag Presets implementiert: `minimal_mission`, `full_px4_out`, `camera_gimbal`, `swarm_multi_vehicle`
- [x] Tests geschrieben: `tests/test_ros2_bag_recorder.py`
- [x] Bob-Test gruen: enthalten im Backend-Lauf `50 passed`

#### D.1 — Bag Backend (Codex)

**Bestehend:** `skymeshx/ros/bag_recorder.py` erweitern über `ros2_context.py`

```python
startBagRecord(topics: list, output_dir: str, preset: str)
stopBagRecord() -> str       # gibt Bag-Pfad zurück
getBagStatus() -> dict

# Signals
bagRecordStarted(path: str)
bagRecordStopped(path: str, size_mb: float)
bagRecordError(message: str)
```

**Presets:**
```python
"minimal_mission"     → vehicle_status, global_pos, local_pos, odometry, attitude,
                         control_mode, mission_result, failsafe_flags
"full_px4_out"        → /<ns>/fmu/out/*
"camera_gimbal"       → gimbal_device_attitude_status, gimbal_device_set_attitude,
                         camera/image_raw
"swarm_multi_vehicle" → vehicle_status, odometry, trajectory_setpoint (alle Namespaces)
```

Auto-Stop wenn Bridge disconnected. Bag-Pfad ins Trace Manifest schreiben.

#### D.2 — Bag UI (Bob)

**ROS2Panel** (Bag Tab):
- Preset-Dropdown
- Szenario-Name-Eingabe
- Start/Stop Button
- Rote blinkende Recording-Indicator
- Dauer + Dateigröße
- "Im FlightLog öffnen" Button (→ FlightLog Tab + Bag laden)

#### D.3 — Tests (Codex)

```
tests/test_ros2_bag_recorder.py    ← subprocess mock, hardware-free
```

---

### MODUL F — SITL Test Checklisten + Smoke Tests
**Priorität: P2**  
**Besitzer: Codex Tests + Bob Checklisten**

#### F.1 — Manuelle Test-Checklisten (Bob)

```
docs/testing/sitl-basic-connectivity.md
docs/testing/sitl-seeding-mission.md
docs/testing/sitl-solar-mission.md
docs/testing/sitl-camera-stream.md
docs/testing/sitl-ros2-bridge.md
docs/testing/sitl-multi-vehicle.md
docs/testing/sitl-bag-workflow.md
```

Jede Checklist enthält:
- Voraussetzungen (Modell, World, Namespace, Ports)
- Schritt-für-Schritt-Sequenz
- Expected Output
- Trace-Bundle prüfen: welche Felder müssen vorhanden sein?

#### F.2 — Automatisierte Smoke Tests (Codex)

**Datei:** `tests/test_sitl_smoke.py`

**Status 2026-06-26 / Codex:**
- [x] Feedback/API-Start nach R-01/R-03 geschrieben
- [x] Opt-in SITL Smoke Tests implementiert: `tests/test_sitl_smoke.py`
- [x] Bob-Test gruen: `5 skipped` ohne SITL_AVAILABLE, `50 passed / 5 skipped` im kombinierten Lauf

Regeln:
- `@pytest.mark.sitl`
- Nur ausgeführt wenn `SITL_AVAILABLE=1` gesetzt
- Linux only
- Niemals in normalem CI

Szenarien:
```
sih_single_mission_upload
gz_x500_single_coverage
gz_x500_gimbal_solar
gz_x500_mono_cam_video_map
gz_x500_multi_swarm_2uav
gz_x500_seeding_large_preview
gz_world_ridge_terrain_lidar
gz_world_walls_avoidance
```

---

### MODUL G — ROS2 Panel Overhaul
**Priorität: P3 — nach A–D**  
**Besitzer: Bob QML (Codex prüft API-Korrektheit)**

**Status 2026-06-27 / Bob:**
- [x] `tools/ui/qml/panels/ROS2Panel.qml` in 5 Tabs refaktoriert: Connection, Topics, Bag, Video, Debug
- [x] Bag Preset Selector nutzt Codex API `startBagRecord(..., preset)`
- [x] Video Tab mit Drone Selector und PX4 Quick Ports
- [x] Multi-Vehicle Stop nutzt `stopAllSitl()`
- [x] Bob-Test gruen: kombinierter Backend/UI-naher Testlauf `50 passed`

5 Tabs:
- **Connection** — SITL Launch, World-Profil, Bridge Connect, Formation (bestehend)
- **Topics** — Topic Browser (C.2), Bridge Health pro Drone
- **Bag** — Bag Recorder (D.2) + FlightLog-Link
- **Video** — Video Source Config (B.2)
- **Debug** — Trace Bundle Controls (E.4), MAVLink Latenz, Topic Rates

---

## Implementierungs-Reihenfolge

```
PX4-SIM-1 (Fundament — kein SITL nötig):
  Codex: E.1 TraceLogger + E.2 Bundle Struktur + E.3 TraceContext + E.5 Analyzer + Tests
  Bob:   E.4 Trace Bundle Controls im ROS2Panel Debug-Tab

PX4-SIM-2 (Video MVP):
  Codex: B.1 VideoContext (Probe/Status/Snapshot) + B.3 Tests
  Bob:   B.2 Port-Eingabe, Status-Badge, Map Camera-Badge, kein leeres Video

PX4-SIM-3 (ROS2 Topics + Bags):
  Codex: C.1 Topic Health + D.1 Bag Presets + D.3 Tests
  Bob:   C.2 Topic Browser UI + D.2 Bag UI

PX4-SIM-4 (SITL Launcher + Welten):
  Codex: A.1 Launch Profiles + A.2 World Profiles + A.4 Tests
  Bob:   A.3 SITL UI (Dropdown, World-Profil, Warnungen)

PX4-SIM-5 (Tests + Panel):
  Codex: F.2 Smoke Tests
  Bob:   F.1 Checklisten + G Panel Overhaul (5 Tabs)

PX4-SIM-6 (Video Phase 2 — optional):
  Codex: GStreamer appsink → QImage Backend
  Bob:   GimbalPanel Live View + Map PIP Overlay
```

**Status 2026-06-27 / Codex:**
- [x] Live-Frame Backend implementiert: optional OpenCV/GStreamer Decoder -> QImage -> `image://videoStream`
- [x] Single-Renderer-Policy implementiert: `activeTarget` ist `map`, `gimbal` oder leer
- [x] Map PIP rendert echte Frames nur wenn `activeTarget == "map"` und `hasFrame == true`
- [x] GimbalPanel rendert echte Frames erst nach Klick auf `Start Stream`
- [x] `End Stream` stoppt Decoder/Rendering
- [ ] Bob/Linux-Test ausstehend: echter PX4/Gazebo UDP H.264 Stream auf Port 5600

---

## Neue Dateien (vollständige Liste)

```
# Codex
skymeshx/core/trace_logger.py              ← E.1 TraceLogger Singleton
tools/ui/context/trace_context.py          ← E.3 TraceContext QML Wrapper
tools/ui/context/video_stream_context.py   ← B.1 VideoContext
tools/analyze_trace.py                     ← E.5 CLI Analyzer → Markdown
tests/test_trace_logger.py
tests/test_trace_context.py
tests/test_video_stream_context.py
tests/test_ros2_bag_recorder.py
tests/test_ros2_sitl_launcher.py
tests/test_sitl_smoke.py                   ← @pytest.mark.sitl (skipped ohne SITL)

# Bob
docs/testing/sitl-basic-connectivity.md
docs/testing/sitl-seeding-mission.md
docs/testing/sitl-solar-mission.md
docs/testing/sitl-camera-stream.md
docs/testing/sitl-ros2-bridge.md
docs/testing/sitl-multi-vehicle.md
docs/testing/sitl-bag-workflow.md
```

---

## Acceptance Criteria für Linux-Sim-Testphase

Minimum bevor erste SITL-Tests:

- [x] Trace Session start/stop funktioniert
- [x] `manifest.json` enthält PX4 Modell, Namespace, Video-Port, World, Szenario
- [x] `ros2_topic_health.json` wird exportiert
- [x] Bag Recording start/stop funktioniert (oder CLI-Fallback dokumentiert)
- [x] Video-Port pro Drone konfigurierbar
- [x] Map zeigt **kein kaputtes/leeres Video** vor `receiving`
- [x] Mission upload/start/pause/abort sind in `mission_trace.jsonl` sichtbar
- [x] WP-Tracking (`distanceToWpM`) ist tracebar

Besser:

- [x] ROS2Panel hat Connection/Topics/Bag/Video/Debug Tabs
- [x] Topic Browser zeigt Hz-Raten
- [x] Video Live View funktioniert (Snapshot bleibt ueber CameraContext)
- [x] Trace Analyzer generiert Markdown-Summary
- [x] World-Profil-Warnungen in der UI

---

## Offene Fragen (User muss entscheiden)

1. **Namespace Default** für Gazebo: `px4_N` oder `uav_N`?
   → Empfehlung: `px4_N` für PX4 Gazebo, `uav_N` als Alias
2. **Erstes Kamera-Modell**: `gz_x500_mono_cam` oder `gz_x500_gimbal`?
   → Empfehlung: `gz_x500_gimbal` (Solar/Camera/Gimbal Workflow braucht es)
3. **Video MVP-Scope**: Probe/Status only, oder Snapshot, oder Live Video?
   → Empfehlung: Probe/Status → Snapshot → Live Video (3 Stufen)
4. **Trace Bundle Pfad**: `trace_runs/` oder `logs/sim_traces/`?
   → Empfehlung: `trace_runs/` (leicht zu zippen + senden, kein rotierender Log)
5. **ROS2 Distro**: Humble only, oder Humble + Jazzy?
   → Empfehlung: Humble first
6. **Gazebo Version**: Garden oder Harmonic?
   → Beeinflusst Modell-Namen und World-Namen
