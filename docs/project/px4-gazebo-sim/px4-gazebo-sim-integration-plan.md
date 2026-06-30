# PX4 + Gazebo + ROS2 Simulation Integration Plan
# Parallel Work Division: Bob & Codex

**Erstellt:** 2026-06-26  
**Zweck:** Planung aller Erweiterungen die nötig sind, um skymeshx GCS vollständig gegen PX4 SITL + Gazebo + ROS2 zu testen  
**Koordination:** `docs/project/px4-gazebo-sim/px4-gazebo-sim-collab-feedback.md`  
**Voraussetzung:** Implementierungsplan `camera-seeding-solar-implementation-plan.md` muss abgeschlossen sein

---

## 🎯 Ziel

Der Nutzer kann:
1. PX4 SITL + Gazebo (single & multi-vehicle) von der GCS UI aus starten und steuern
2. Kamera-Simulation (z.B. x500_gimbal, downward-facing camera) in Gazebo nutzen
3. Video-Stream aus der Simulation im GCS empfangen und **auf der Map darstellen**
4. ROS2 Topics (PX4 uXRCE-DDS) abonnieren und im ROS2 Panel live anzeigen
5. ROS2 Bag-Dateien aus der Sim aufnehmen + im FlightLog Panel abspielen
6. Mission Planning, Swarm-Steuerung und Camera/Seeding/Solar Wizards **komplett gegen SITL testen**
7. Trace & Debug-Logs automatisch sammeln, damit Bob/Codex nach Linux-Tests remote analysieren können

---

## 🏗️ Architektur-Übersicht

```
Linux Host (Ubuntu 22.04)
├── Gazebo Ignition 8 (Sim)          ← x500, x500_gimbal, multi-vehicle
│   ├── Camera Plugin (RTSP/UDP)      ← gst-launch oder gz-sim camera bridge
│   └── IMU / GPS / Baro Plugins
├── PX4 SITL (px4_sitl gz_x500_gimbal)
│   └── uXRCE-DDS → UDP 8888
├── MicroXRCEAgent udp4 -p 8888
├── ROS2 Humble
│   ├── /uav_1/fmu/out/vehicle_odometry
│   ├── /uav_1/camera/image_raw         ← aus Gazebo Camera Plugin
│   ├── /uav_1/gimbal/status
│   └── ros2 bag record ...
└── skymeshx GCS (PySide6 + QML)
    ├── MAVLink: tcp:127.0.0.1:5762   ← für Arm/Mode/Mission (ArduPilot kompat.)
    │   ODER PX4 MAVLink via MAVSDK
    ├── ROS2 Bridge (px4_bridge.py)    ← Telemetrie, Offboard, Formation
    ├── Video Stream Receiver          ← UDP/RTSP → QML VideoOutput
    └── Bag Playback (FlightLogPanel)
```

---

## 📋 Aufgaben

---

### Modul A — PX4 SITL Launcher (Codex Backend)

> **Status:** ROS2Panel hat bereits SITL-Start-Button + `ros2_context.py`.  
> Aber: Multi-Vehicle, Camera-Modell und SIH fehlen.

#### A.1 — Gazebo Model-Erweiterungen in ROS2 Context

| # | Aufgabe | Datei |
|---|---------|-------|
| A.1.1 | Modell-Liste erweitern: `x500_gimbal`, `x500_camera`, `rc_cessna`, `standard_vtol_0`, SIH | `tools/ui/context/ros2_context.py` |
| A.1.2 | `startSitl()` — optionalen Parameter `camera_enabled: bool` und `gimbal_enabled: bool` übergeben, PX4 mit richtigem Modell starten | `tools/ui/context/ros2_context.py` |
| A.1.3 | Multi-Vehicle: `startMultiSitl(count: int, base_port: int)` — startet N Instanzen mit gestaffelten Ports (`5762, 5763, …`) und Namespaces (`uav_1 … uav_N`) | `tools/ui/context/ros2_context.py` |
| A.1.4 | SIH (Software-In-the-Hardware) Modus: `startSihSitl()` — kein Gazebo, reiner Software-Sensor-Test | `tools/ui/context/ros2_context.py` |
| A.1.5 | `getSitlStatus() -> dict` — gibt `{running, model, namespace, pid, uptime_s, gazebo_running}` zurück | `tools/ui/context/ros2_context.py` |
| A.1.6 | Tests: hardware-free (subprocess mock) | `tests/test_ros2_sitl_launcher.py` |

#### A.2 — ROS2Panel SITL UI (Bob QML)

| # | Aufgabe | Datei |
|---|---------|-------|
| A.2.1 | Model-Dropdown: `x500`, `x500_gimbal`, `x500_camera`, `iris`, `plane`, `standard_vtol`, `sih` | `tools/ui/qml/panels/ROS2Panel.qml` |
| A.2.2 | Toggle: "Camera aktivieren" + "Gimbal aktivieren" (nur sichtbar bei kompatiblen Modellen) | `tools/ui/qml/panels/ROS2Panel.qml` |
| A.2.3 | Multi-Vehicle Sektion: Anzahl (1–5), "Alle starten" / "Alle stoppen" | `tools/ui/qml/panels/ROS2Panel.qml` |
| A.2.4 | SITL Status-Box: Modell, Namespace, PID, Uptime, Gazebo-Status | `tools/ui/qml/panels/ROS2Panel.qml` |
| A.2.5 | SIH-Mode Button (kein Gazebo) | `tools/ui/qml/panels/ROS2Panel.qml` |

---

### Modul B — Video Stream (Bob QML + Codex Backend)

> **Problem:** Kein UDP/RTSP Video-Empfang in der GCS. User will Stream auf der Map sehen.

#### B.1 — Video Stream Backend (Codex)

| # | Aufgabe | Datei |
|---|---------|-------|
| B.1.1 | `VideoStreamContext(QObject)` — QML-exposed context | `tools/ui/context/video_stream_context.py` |
| B.1.2 | Properties: `streamUrl: str`, `streamActive: bool`, `frameWidth/Height: int`, `fps: float`, `latencyMs: float`, `droneId: str` | — |
| B.1.3 | Slot `startStream(url: str, drone_id: str)` — akzeptiert `udp://0.0.0.0:5600`, `rtsp://…`, `gst://…` | — |
| B.1.4 | Slot `stopStream()` | — |
| B.1.5 | Signal `streamStarted(url: str)` | — |
| B.1.6 | Signal `streamStopped()` | — |
| B.1.7 | Signal `streamError(msg: str)` | — |
| B.1.8 | Signal `frameReceived()` — getaktet bei ~5 Hz für UI-Update (nicht jeden Frame) | — |
| B.1.9 | GStreamer-Pipeline (optional, nur wenn `gst` verfügbar): UDP H.264 → JPEG-Frames → QImage | — |
| B.1.10 | Fallback: einfaches MJPEG via HTTP wenn kein GStreamer | — |
| B.1.11 | Hardware-free: wenn kein Stream verfügbar, zeigt Placeholder-Frame | — |
| B.1.12 | In `service_locator.py` registrieren als `videoStream` | `tools/ui/service_locator.py` |
| B.1.13 | Tests: mock stream, start/stop, error handling | `tests/test_video_stream_context.py` |

#### B.2 — Video Stream UI (Bob QML)

| # | Aufgabe | Datei |
|---|---------|-------|
| B.2.1 | **ROS2Panel** — neue Sektion "Video Stream": URL-Eingabe (UDP/RTSP), Drone-Selector, Start/Stop Button | `tools/ui/qml/panels/ROS2Panel.qml` |
| B.2.2 | Stream-Status Indicator: FPS, Latenz, Auflösung | — |
| B.2.3 | **GimbalPanel** — "Live View" Widget: zeigt VideoOutput wenn Stream aktiv, Placeholder wenn nicht | `tools/ui/qml/panels/GimbalPanel.qml` |
| B.2.4 | **MapView** — floating Video-Overlay (minimierbar, oben rechts): nur sichtbar wenn `videoStream.streamActive === true`, sonst unsichtbar | `tools/ui/qml/MapView.qml` |
| B.2.5 | Map Overlay: "PIP" (Picture-In-Picture) — kleines Kamerabild mit Gimbal-Footprint auf der Karte | `tools/ui/qml/MapView.qml` |
| B.2.6 | URL-Schema Erkennung: zeigt UDP/RTSP/GStreamer als Hinweis-Text | — |

**Standard PX4 Gazebo Video-URL:** `udp://0.0.0.0:5600`  
**Gazebo Camera Plugin Config (in SDF):**
```xml
<plugin name="GstCameraPlugin" filename="libgazebo_gst_camera_plugin.so">
  <udpHost>127.0.0.1</udpHost>
  <udpPort>5600</udpPort>
</plugin>
```

---

### Modul C — ROS2 Topic Browser (Bob QML + Codex Backend)

> **Problem:** ROS2Panel zeigt nur fest verdrahtete Topics. User will alle verfügbaren Topics sehen und abonnieren.

#### C.1 — Topic Discovery Backend (Codex)

| # | Aufgabe | Datei |
|---|---------|-------|
| C.1.1 | Slot `discoverTopics(namespace: str) -> list[str]` — ruft `rclpy.get_topic_names_and_types()` auf | `tools/ui/context/ros2_context.py` |
| C.1.2 | Slot `subscribeToTopic(topic: str, drone_id: str)` — abonniert Topic und leitet Nachrichten als JSON-Signal weiter | — |
| C.1.3 | Signal `topicMessage(topic: str, json_data: str, timestamp: float)` | — |
| C.1.4 | Topic-Rate Messung: `getTopicRate(topic: str) -> float` — Nachrichten pro Sekunde | — |
| C.1.5 | Wichtige PX4 Topics auto-subscriben wenn Bridge aktiv: `vehicle_odometry`, `vehicle_status`, `battery_status`, `sensor_combined`, `vehicle_gps_position` | — |

#### C.2 — Topic Browser UI (Bob QML)

| # | Aufgabe | Datei |
|---|---------|-------|
| C.2.1 | ROS2Panel — neue Sektion "Topic Browser": "Discover" Button, scrollbare Topic-Liste mit Rate-Badges | `tools/ui/qml/panels/ROS2Panel.qml` |
| C.2.2 | Topic Filter-Eingabe (z.B. nur `/fmu/out/*`) | — |
| C.2.3 | Topic anklicken → Wert-Preview (letzter Wert als JSON, kompakt formatiert) | — |
| C.2.4 | Topic zu "Watch List" hinzufügen → bleibt in Sidebar sichtbar | — |

---

### Modul D — ROS2 Bag Recorder (Codex Backend + Bob QML)

> **Problem:** Bag-Aufnahme fehlt vollständig. FlightLogPanel kann bereits `.mcap`/`.db3` abspielen.

#### D.1 — Bag Recorder Backend (Codex)

| # | Aufgabe | Datei |
|---|---------|-------|
| D.1.1 | Slot `startBagRecord(topics: list[str], output_dir: str)` — startet `ros2 bag record` als Subprocess | `tools/ui/context/ros2_context.py` |
| D.1.2 | Slot `stopBagRecord() -> str` — stoppt Aufnahme, gibt Bag-Pfad zurück | — |
| D.1.3 | Property `bagRecording: bool` | — |
| D.1.4 | Property `bagRecordPath: str` — aktueller Aufnahme-Pfad | — |
| D.1.5 | Signal `bagRecordStarted(path: str)` | — |
| D.1.6 | Signal `bagRecordStopped(path: str, size_mb: float)` | — |
| D.1.7 | Default-Topics: alle PX4 `/fmu/out/*` Topics + Camera topics | — |
| D.1.8 | Tests: subprocess mock, start/stop | `tests/test_ros2_bag_recorder.py` |

#### D.2 — Bag Recorder UI (Bob QML)

| # | Aufgabe | Datei |
|---|---------|-------|
| D.2.1 | ROS2Panel — neue Sektion "Bag Recorder": Start/Stop Button, Recording-Indicator (rot blinkend), Dateigröße | `tools/ui/qml/panels/ROS2Panel.qml` |
| D.2.2 | Ausgabe-Pfad konfigurierbar | — |
| D.2.3 | Nach Aufnahme: "Im FlightLog öffnen" Button (navigiert zu FlightLog Tab + lädt Bag) | — |

---

### Modul E — Trace & Debug Logging (Codex Backend + Bob QML)

> **Ziel:** User testet auf Linux, kann kein Feedback geben — alle Informationen müssen automatisch geloggt werden.

#### E.1 — Structured Trace Logger (Codex)

| # | Aufgabe | Datei |
|---|---------|-------|
| E.1.1 | `TraceLogger` — schreibt strukturierte JSON-Trace-Datei neben dem Syslog | `skymeshx/core/trace_logger.py` |
| E.1.2 | Trace-Einträge: `{ts, type, source, data}` — Types: `MAVLINK_MSG`, `ROS2_MSG`, `QML_SIGNAL`, `PYTHON_CALL`, `STATE_CHANGE`, `ERROR` | — |
| E.1.3 | MAVLink Hook: logged empfangene + gesendete MAVLink-Nachrichten (inkl. Typ, sys_id, seq) mit Timestamp | — |
| E.1.4 | ROS2 Hook: logged eingehende PX4 Topics mit Frequenz (nicht jeden Frame — max 1 Log/s pro Topic) | — |
| E.1.5 | State-Change Hook: logged FSM-Übergänge, Mission-Uploads, ARM/DISARM | — |
| E.1.6 | Auto-Rotation: neue Datei pro Session, max 50MB, dann neues File | — |
| E.1.7 | Tests: hardware-free | `tests/test_trace_logger.py` |

#### E.2 — Trace Analyzer Tool (Codex)

| # | Aufgabe | Datei |
|---|---------|-------|
| E.2.1 | `tools/analyze_trace.py` — CLI-Script, liest JSON-Trace und gibt Zusammenfassung aus | `tools/analyze_trace.py` |
| E.2.2 | Analyse: MAVLink-Lücken (>500ms ohne Nachricht), ROS2 Topic Drop-out, Mission-Timing | — |
| E.2.3 | Export: Markdown-Report generieren (kann von Bob/Codex gelesen werden) | — |

#### E.3 — Debug Panel UI (Bob QML)

| # | Aufgabe | Datei |
|---|---------|-------|
| E.3.1 | **LogPanel** — neuer Tab "Trace" neben "System Log": zeigt letzte 200 Trace-Einträge (TYPE + SOURCE + DATA) | `tools/ui/qml/panels/LogPanel.qml` |
| E.3.2 | Filter nach Type (MAVLINK / ROS2 / STATE / ERROR) | — |
| E.3.3 | "Export Trace" Button → schreibt aktuelle Session nach `logs/trace/` | — |
| E.3.4 | Timing-Anzeige: MAVLink Latenz, ROS2 Topic Rate (aus Trace-Daten) | — |

---

### Modul F — Mission Integration Tests gegen SITL (Codex)

> **Ziel:** Automatisierte hardware-free Tests + manuelle SITL-Tests mit klaren Checklisten.

#### F.1 — SITL Integration Test Checklisten

Jede Checklist wird als `.md` Datei in `docs/testing/` abgelegt und nach dem Test vom User ausgefüllt.

| # | Checkliste | Inhalt |
|---|-----------|--------|
| F.1.1 | `sitl-basic-connectivity.md` | Connect → ARM → TAKEOFF → RTL Sequenz |
| F.1.2 | `sitl-seeding-mission.md` | Boundary zeichnen → Preview → Upload → Start → Pause → Abort |
| F.1.3 | `sitl-solar-mission.md` | Rows zeichnen → Preview → Upload → Start |
| F.1.4 | `sitl-camera-stream.md` | Gazebo Camera Plugin → UDP Stream → GCS empfängt → Map-Overlay |
| F.1.5 | `sitl-ros2-bridge.md` | Bridge connect → Topic-Raten prüfen → Formation → Offboard |
| F.1.6 | `sitl-multi-vehicle.md` | 3x SITL starten → alle 3 verbinden → Swarm Mission |
| F.1.7 | `sitl-bag-workflow.md` | Bag aufnehmen → stoppen → im FlightLog abspielen |

#### F.2 — Automatisierte SITL Smoke Tests (Codex)

| # | Aufgabe | Datei |
|---|---------|-------|
| F.2.1 | `tests/test_sitl_smoke.py` — pytest-marked `@pytest.mark.sitl` (nur auf Linux mit `SITL_AVAILABLE=1`) | `tests/test_sitl_smoke.py` |
| F.2.2 | Test: MAVLink connect → HEARTBEAT empfangen → ARMED → DISARMED | — |
| F.2.3 | Test: Mission Upload (5 WPs) → Download → Vergleich | — |
| F.2.4 | Test: ROS2 Bridge → `vehicle_odometry` empfangen innerhalb 3s | — |
| F.2.5 | Diese Tests werden standardmäßig übersprungen (kein SITL nötig für CI) | — |

---

### Modul G — ROS2 Panel Overhaul (Bob QML)

> Das bestehende Panel ist gut aber braucht Struktur für alle neuen Features.

| # | Aufgabe |
|---|---------|
| G.1 | Panel in 4 Tabs aufteilen: **Connection**, **Topics**, **Bag**, **Debug** |
| G.2 | Connection Tab: SITL Launch, Bridge Connect, Formation (bestehend) |
| G.3 | Topics Tab: Topic Browser (C.2), Video Stream (B.2.1) |
| G.4 | Bag Tab: Recorder (D.2) + Quick-Link zum FlightLog |
| G.5 | Debug Tab: Trace Viewer (E.3), MAVLink Latenz, Topic Rates |

---

## 📊 Prioritäten-Matrix

| Modul | Priorität | Schwierigkeit | Wer |
|-------|-----------|---------------|-----|
| **E — Trace Logging** | 🔴 HOCH | Niedrig | Codex |
| **B.1 — Video Backend** | 🔴 HOCH | Mittel | Codex |
| **B.2 — Video UI** | 🔴 HOCH | Niedrig | Bob |
| **A.1 — SITL Multi-Vehicle** | 🟡 MITTEL | Niedrig | Codex |
| **A.2 — SITL UI** | 🟡 MITTEL | Niedrig | Bob |
| **D — Bag Recorder** | 🟡 MITTEL | Niedrig | Codex + Bob |
| **C — Topic Browser** | 🟡 MITTEL | Mittel | Codex + Bob |
| **F — Integration Tests** | 🟡 MITTEL | Mittel | Codex |
| **G — Panel Overhaul** | 🟠 NIEDRIG | Mittel | Bob |

---

## 🚀 Empfohlene Reihenfolge

```
Phase A (Fundament):
  1. E.1 Trace Logger (Codex)           ← sofort, braucht kein Gazebo
  2. A.1 SITL Multi-Vehicle (Codex)     ← bestehende Infra erweitern
  3. A.2 SITL UI Updates (Bob)          ← modell/camera toggle

Phase B (Video):
  4. B.1 Video Stream Backend (Codex)   ← UDP/RTSP Receiver
  5. B.2.1 Stream UI in ROS2Panel (Bob) ← URL-Eingabe, Status
  6. B.2.4 Map Overlay (Bob)            ← PIP auf der Karte

Phase C (Topics & Bags):
  7. D.1 Bag Recorder Backend (Codex)
  8. D.2 Bag UI (Bob)
  9. C.1 Topic Discovery (Codex)
  10. C.2 Topic Browser UI (Bob)

Phase D (Tests & Checklisten):
  11. F.1 Test-Checklisten anlegen (Bob)
  12. F.2 SITL Smoke Tests (Codex)
  13. E.2 Trace Analyzer (Codex)
  14. E.3 Debug Panel UI (Bob)

Phase E (Panel Overhaul):
  15. G ROS2 Panel in Tabs aufteilen (Bob)
```

---

## 🔗 Wichtige Links & Referenzen

| Resource | URL |
|----------|-----|
| PX4 Gazebo Sim | https://docs.px4.io/main/en/sim_gazebo_gz/ |
| PX4 Multi-Vehicle | https://docs.px4.io/main/en/sim_gazebo_gz/multi_vehicle_simulation |
| PX4 SIH | https://docs.px4.io/main/en/sim_sih/ |
| PX4 Camera Sim | https://docs.px4.io/main/en/sim_gazebo_gz/#camera |
| PX4 uXRCE-DDS | https://docs.px4.io/main/en/middleware/uxrce_dds |
| Gazebo Camera Plugin | https://github.com/PX4/PX4-Autopilot/tree/main/Tools/simulation/gazebo-classic |
| GStreamer UDP H.264 | `gst-launch-1.0 udpsrc port=5600 ! ...` |

---

## 🔧 PX4 Gazebo Camera Konfiguration (Referenz)

```bash
# x500 mit Gimbal + Downward Camera
PX4_UXRCE_DDS_NS=uav_1 make px4_sitl gz_x500_gimbal

# x500 mit Forward Camera
PX4_UXRCE_DDS_NS=uav_1 make px4_sitl gz_x500_camera

# SIH (kein Gazebo, reine Software-Simulation)
make px4_sitl sihsim_quadx

# Multi-Vehicle (3 Drohnen)
PX4_UXRCE_DDS_NS=uav_1 make px4_sitl gz_x500 &
PX4_UXRCE_DDS_NS=uav_2 make px4_sitl gz_x500 &
PX4_UXRCE_DDS_NS=uav_3 make px4_sitl gz_x500 &
```

```bash
# GStreamer UDP Stream empfangen (QGroundControl Methode)
gst-launch-1.0 -v udpsrc port=5600 caps='application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264' \
  ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink
```

---

## 📂 Neue Dateien (Übersicht)

```
skymeshx/core/trace_logger.py              ← E.1 Trace Logger
tools/ui/context/video_stream_context.py   ← B.1 Video Stream
tools/analyze_trace.py                     ← E.2 Trace Analyzer
tests/test_ros2_sitl_launcher.py           ← A.1 Tests
tests/test_video_stream_context.py         ← B.1 Tests
tests/test_ros2_bag_recorder.py            ← D.1 Tests
tests/test_trace_logger.py                 ← E.1 Tests
tests/test_sitl_smoke.py                   ← F.2 SITL Smoke (skipped ohne SITL)
docs/testing/sitl-basic-connectivity.md    ← F.1 Checklisten
docs/testing/sitl-seeding-mission.md
docs/testing/sitl-solar-mission.md
docs/testing/sitl-camera-stream.md
docs/testing/sitl-ros2-bridge.md
docs/testing/sitl-multi-vehicle.md
docs/testing/sitl-bag-workflow.md
```

---

## 🚨 Wichtige Regeln

1. **Kein SITL nötig für Tests** — alle Unit Tests müssen hardware-free bleiben (subprocess mocking)
2. **SITL Smoke Tests** — nur mit `@pytest.mark.sitl` markiert, standardmäßig übersprungen
3. **Trace Logger** — immer aktiv (auch ohne SITL), kein Performance-Impact durch Rate-Limiting
4. **Video Stream** — UI-Overlay NUR sichtbar wenn `videoStream.streamActive === true`
5. **Bag Recorder** — stoppt automatisch wenn Bridge disconnected
6. **Upload ≠ Execute** — gilt auch für SITL-Tests

---

## 📝 Koordinations-Datei

Alle Updates zwischen Bob und Codex gehen in:
`docs/project/px4-gazebo-sim/px4-gazebo-sim-collab-feedback.md`
