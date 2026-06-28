# PX4 + Gazebo + ROS2 Sim - Feedback Archive 2026-06

Archivierte Eintraege aus `docs/project/px4-gazebo-sim/px4-gazebo-sim-collab-feedback.md`.

## Archiviert am 2026-06-26

Diese Eintraege wurden aus der aktiven Feedback-Datei entfernt, weil sie ueber 200 Zeilen hatte. Die letzten 5 aktiven Eintraege bleiben als Kontext-Anker in der Arbeitsdatei.

---

## Archiviert am 2026-06-27

Diese Eintraege wurden erneut aus der aktiven Feedback-Datei entfernt, weil sie nach PX4-SIM-6 wieder ueber 200 Zeilen hatte.

### 2026-06-27T13:15:00+02:00 | Bob | R-07 TEST-RESULT | PX4-SIM-5 F.2 Smoke Tests gruen

Bob meldete:

```bash
pytest tests/test_sitl_smoke.py -v
# 5 skipped, SITL_AVAILABLE nicht gesetzt

pytest tests/test_trace_logger.py tests/test_trace_context.py tests/test_video_stream_context.py \
       tests/test_ros2_sitl_launcher.py tests/test_ros2_bag_recorder.py tests/test_sitl_smoke.py -q
# 50 passed, 5 skipped
```

Damit war F.2 offiziell abgehakt. Alle SITL-Smoke-Tests skippten korrekt ohne SITL und starteten kein Gazebo/PX4/MAVLink.

---

### 2026-06-26T22:04:00+02:00 | Codex | TEST-REQUEST | PX4-SIM-5 F.2 bitte von Bob testen

Codex bat Bob um:
- `python -m py_compile tests/test_sitl_smoke.py`
- `pytest tests/test_sitl_smoke.py -q`
- kombinierten Backend-Testlauf mit Trace, Video, ROS2/SITL, Bag und Smoke Tests

Optionaler Linux-SITL-Test wurde mit `SITL_AVAILABLE=1` und separaten Flags fuer Commands/Mission/ROS2 dokumentiert.

---

### 2026-06-26T21:58:39+02:00 | Codex | CLEANUP | R-16 Feedback-Datei gekuerzt

Codex kuerzte die Feedback-Datei nach R-16 und verwies auf dieses Archiv.

---

### 2026-06-26T21:59:00+02:00 | Codex | API/START | PX4-SIM-5 F.2 SITL Smoke Tests

Codex startete die opt-in SITL-Smoke-Tests:
- alle Tests `@pytest.mark.sitl`
- skip ohne `SITL_AVAILABLE=1`
- Linux only
- separate Schutzflags fuer Arm/Disarm, Mission Upload und ROS2 Topic Smoke

---

### 2026-06-27T12:30:00+02:00 | Bob | DONE | G - Panel Overhaul: ROS2Panel in 5 Tabs

Bob meldete den ROS2Panel-Overhaul:
- Connection
- Topics
- Bag
- Video
- Debug

Gemeldet: `50 passed`.

---

### 2026-06-27T11:30:00+02:00 | Bob | R-07 TEST-RESULT | PX4-SIM-3/4 Backend Tests gruen

Bob meldete:

```bash
pytest tests/test_ros2_sitl_launcher.py tests/test_ros2_bag_recorder.py -v
# 11 passed

pytest tests/test_trace_logger.py tests/test_trace_context.py tests/test_video_stream_context.py \
       tests/test_ros2_sitl_launcher.py tests/test_ros2_bag_recorder.py -v
# 50 passed
```

Damit waren PX4-SIM-1, PX4-SIM-2, PX4-SIM-3/4 offiziell gruen.

---

### 2026-06-26T20:30:00+02:00 | Bob | R-07 TEST-RESULT | PX4-SIM-1 + B.3 Tests gruen

Bob meldete:

```bash
pytest tests/test_trace_logger.py tests/test_trace_context.py tests/test_video_stream_context.py -v
# 39 passed
```

Damit waren PX4-SIM-1 und B.3 offiziell gruen. Bob bat Codex danach um die ROS2/SITL/Bag Backend-Erweiterungen.

---

### 2026-06-26T16:21:13+02:00 | Codex | TEST-REQUEST | ROS2/SITL/Bag Backend bitte testen

Codex meldete A.1/A.2/C.1/D.1 als implementiert:
- `tools/ui/context/ros2_context.py`
- `tests/test_ros2_sitl_launcher.py`
- `tests/test_ros2_bag_recorder.py`

Angefragte Bob-Checks:

```bash
python -m py_compile tools/ui/context/ros2_context.py tests/test_ros2_sitl_launcher.py tests/test_ros2_bag_recorder.py
pytest tests/test_ros2_sitl_launcher.py tests/test_ros2_bag_recorder.py -q
pytest tests/test_trace_logger.py tests/test_trace_context.py tests/test_video_stream_context.py tests/test_ros2_sitl_launcher.py tests/test_ros2_bag_recorder.py -q
```

Bob meldete diesen Block spaeter mit 50 passed gruen.

---

### 2026-06-26T16:09:43+02:00 | Codex | API/START | PX4-SIM-3/4 Backend: SITL, Topics, Bags

Codex startete:
- SITL Launch/Profile API in `tools/ui/context/ros2_context.py`
- Topic API: `discoverTopics`, `getTopicHealth`, `subscribeToTopic`
- Bag API: `startBagRecord`, `stopBagRecord`, `getBagStatus`

Regeln:
- Normale Tests bleiben hardware-free.
- Launch-Profile enthalten `autopilot="px4"` und `controlPath="ros2_uxrce"`.
- Upload != Execute bleibt unberuehrt.
- Trace wird fuer Launch/Topic/Bag angebunden.

---

### 2026-06-26T20:00:00+02:00 | Bob | DONE | PX4-SIM-2/3/4/F.1 - UI-Module fertig

Bob meldete fertig:
- Trace Controls UI in `tools/ui/qml/panels/LogPanel.qml`
- SITL UI, Multi-Vehicle UI, Video UI, Topic Browser und Bag UI in `tools/ui/qml/panels/ROS2Panel.qml`
- Map Video PIP in `tools/ui/qml/MapView.qml`
- GimbalPanel status-aware Placeholder in `tools/ui/qml/panels/GimbalPanel.qml`
- Manuelle Checklisten unter `docs/testing/`
- `VideoStreamContext` MVP mit UDP-Probe, PX4-Default-Ports und TraceLogger-Integration

Gemeldete Tests:
- `pytest tests/test_apf.py tests/test_field_coverage.py tests/test_seeding_planner.py tests/test_solar_inspection.py -q` -> 79 passed
- TraceLogger Import-Smoke -> OK
- VideoStreamContext Import-Smoke -> OK

Bob bat Codex um hardware-free Tests fuer VideoStreamContext sowie Trace-Tests.

---

### 2026-06-26T12:37:15+02:00 | Codex | TEST-REQUEST | PX4-SIM-1 bitte von Bob testen

Codex bat Bob um Test der Trace Foundation:
- `skymeshx/core/trace_logger.py`
- `tools/ui/context/trace_context.py`
- `tools/analyze_trace.py`
- `tests/test_trace_logger.py`
- `tests/test_trace_context.py`
- `tools/ui/service_locator.py`
- `tools/ui/context/video_stream_context.py`

Angefragte Befehle:

```bash
python -m py_compile skymeshx/core/trace_logger.py tools/ui/context/trace_context.py tools/ui/context/video_stream_context.py tools/ui/service_locator.py tools/analyze_trace.py tests/test_trace_logger.py tests/test_trace_context.py
pytest tests/test_trace_logger.py tests/test_trace_context.py -q
pytest tests/test_video_stream_context.py -q
```

Hinweis: Codex konnte auf Windows wegen Session/PATH-Problem kein Python/Pytest ausfuehren.

---

### 2026-06-26T12:29:18+02:00 | Codex | API/START | PX4-SIM-1 Trace Foundation

Codex definierte und startete:
- `TraceLogger.get()` Singleton
- Trace Session Management
- `log_ui_event`, `log_mission_event`, `log_wp_tracking`, `log_ros2_health`, `log_video_status`, `log_error`
- Trace Bundle unter `trace_runs/<timestamp>_<scenario>/`
- QML Wrapper `TraceContext`
- Analyzer CLI `tools/analyze_trace.py`

Normale Tests sollten hardware-free bleiben.

---

### 2026-06-26T17:00:00+02:00 | Bob | Synthese | Konsolidierter Plan verabschiedet

Bob konsolidierte die Inputs in `docs/project/px4-gazebo-sim/px4-gazebo-sim-implementation-plan.md`.

Wichtige Entscheidungen:
- Video-Backend: `tools/ui/context/video_stream_context.py`
- Namespace: `px4_N` Default fuer Gazebo Multi-Vehicle, `uav_N` weiter erlaubt
- Trace: Python Singleton plus QML Wrapper
- Trace Bundle: `trace_runs/<ts>_<scenario>/`
- Video: erst Probe/Status/Snapshot, Live-Video spaeter
- WP-Tracking Trace-Typ ist Pflicht
- World Profiles fuer `ridge`, `aruco`, `walls`, `windy`, `moving_platform`
- MAVLink/PX4 explizit trennen, kein Auto-Routing ueber ArduPilot-Pfade

Aufteilung:
- Codex: Trace, SITL/World Backend, Video Backend, Topics, Bags, Smoke Tests
- Bob: UI, Checklisten, ROS2Panel Overhaul
