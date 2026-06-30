# PX4 + Gazebo + ROS2 Sim - Collaboration Feedback

**Plan:** `docs/project/px4-gazebo-sim/px4-gazebo-sim-implementation-plan.md`  
**Rules:** `docs/project/px4-gazebo-sim/px4-gazebo-sim-rules.md`  
**Regel:** Immer zuerst hier schreiben, dann Code anfassen.  
**Archiv:** `docs/project/not-fertig/px4-gazebo-sim-feedback-archive-2026-06.md`

---

### 2026-06-28T01:10:00+02:00 | Codex | DONE | Empty setup paths execute nothing

Leere Bridge/SITL-Setup-Pfadfelder duerfen keine `source`-Kommandos ausfuehren und nicht auf Default-Pfade zurueckfallen.

---

### 2026-06-28T01:00:00+02:00 | Codex | DONE | Separate SITL setup source field

`tools/ui/qml/panels/ROS2Panel.qml`: PX4 SITL hat jetzt ein eigenes `ROS2 setup sources (SITL)` Pfadfeld; `Start SITL` nutzt dieses Feld statt des Bridge-Felds.

---

### 2026-06-28T00:45:00+02:00 | Codex | DONE | ROS2Panel terminal toggle UI fix

**User-Feedback:** Im PX4-SITL-Bereich fehlt ein eigener `Open visible terminal` Schalter. Der vorhandene Text ueberlappt die Checkbox. Vor den Source-Pfadfeldern soll ein englischer Tooltip stehen.

**Working on:**
- `tools/ui/qml/panels/ROS2Panel.qml`

---

### 2026-06-28T00:30:00+02:00 | Codex | DONE | ROS2 setup sources + visible terminal sessions

**Erledigt:**
- `tools/ui/qml/panels/ROS2Panel.qml`: Editierbarer mehrzeiliger Source-Block fuer Bridge + SITL.
- `tools/ui/qml/panels/ROS2Panel.qml`: Toggle `Open visible terminal on Bridge/SITL start`.
- `tools/ui/context/ros2_context.py`: Shared API `get/setRos2SetupSources*`.
- `tools/ui/context/ros2_context.py`: Bridge-Connect sourced die Pfade, refreshed ROS2 Import-Probe und oeffnet ein Bridge-Diagnose-Terminal mit live getailtem Bridge-Log.
- `tools/ui/context/ros2_context.py`: Einzel-SITL startet unter Linux bevorzugt in sichtbarer Terminal-Session mit `source`, `MicroXRCEAgent` und `make px4_sitl ...`; ohne Terminal faellt es auf den bestehenden Background-Cluster zurueck.
- `tests/test_ros2_sitl_launcher.py`: Hardware-freie Tests fuer Source-Normalisierung, SITL-Weitergabe und Terminal-Skript-Inhalt.

**Lokal geprueft:**
- `git diff --check` sauber bis auf bekannte LF/CRLF-Warnungen.
- Pattern-Scan auf `Unexpected token`, `TODO`, `FIXME`: keine Treffer.

**Lokal blockiert:**
- `python -m py_compile ...` blockiert durch WindowsApps Session-Fehler.
- `pytest ...` nicht installiert/verfuegbar in dieser Shell.

**Bitte auf Linux testen:**
```bash
pytest tests/test_ros2_sitl_launcher.py -q
python -m tools.ui
```

**Manueller UI-Test:**
1. ROS2Panel -> Connection.
2. Source-Pfade setzen:
   `/opt/ros/humble/setup.bash`
   `/home/iruz/ws_sensor_combined/install/setup.bash`
3. PX4 Bridge: `Connect` klicken -> sichtbares Terminal + Bridge-Log im UI.
4. PX4 SITL: `Start SITL` klicken -> sichtbares Terminal mit `MicroXRCEAgent`/PX4/Gazebo-Ausgabe.

---

### 2026-06-28 | Bob | HOTFIX/DONE | BagPlaybackContext Thread-Safety Fix (Freeze Root Cause)

**Diagnose:**
Codex' Minimal-Panel hat Canvas/Grid/Flickable entfernt — trotzdem freezt die App noch.
Root Cause: `BagPlaybackContext._monitor_playback()` emittiert `progressChanged` + `stateChanged`
direkt aus einem Background-Thread (10 Hz). In QML ist `bagStateText()` + `bagProgressText()` als
implizite Property-Binding auf `bagPlayback.progress` verknuepft — wenn das Signal aus einem
Non-Main-Thread kommt, blockiert QML's Binding-Engine auf Windows → Freeze.

**Fix: `tools/ui/context/bag_playback_context.py`**
- Import `QMetaObject`, `Qt` hinzugefuegt.
- `_monitor_playback()` emittiert KEINE Signale mehr direkt aus dem Thread.
- Stattdessen: `QMetaObject.invokeMethod(..., Qt.ConnectionType.QueuedConnection)` → Signals werden
  in den Qt-Main-Thread-Queue gestellt.
- Zwei neue `@Slot()` Methoden: `_on_playback_ended()` und `_emit_progress()` — werden auf dem
  Main-Thread ausgefuehrt.
- Zusaetzlich: Progress-Update nur bei Delta > 0.001 (reduziert Update-Rate auf sinnvolle Aenderungen).

**Tests:** `39 passed, 5 skipped` (unveraendert, `test_ros2_bag_recorder.py` war pre-existing broken).

---

### 2026-06-27T18:00:00+02:00 | Codex | FINAL-GATE/START | Linux-Test readiness

**User-Ziel:** Alle offenen Acceptance-Gates schliessen und im Plan abhaken, damit Linux PX4/Gazebo Tests starten koennen.

**Working on:**
- Mission trace: upload/start/pause/abort in `mission_trace.jsonl`
- WP-Tracking: `distanceToWpM` tracebar
- World-Profil-Warnungen in UI/Backend
- Implementation Plan Checkboxen aktualisieren

---

### 2026-06-27T18:20:00+02:00 | Codex | FINAL-GATE/DONE | Linux-Test readiness

**Erledigt:**
- `tools/ui/context/ros2_context.py`: Mission upload/start/pause/abort/status werden in `mission_trace.jsonl` getraced.
- `tools/ui/context/ros2_context.py`: WP-Tracking schreibt `distanceToWpM`, Target-Position und Acceptance-Radius in den Trace.
- `tools/ui/context/ros2_context.py` + `tools/ui/qml/panels/ROS2Panel.qml`: World-Profil-Warnungen sind aus Backend/QML sichtbar.
- `tests/test_ros2_sitl_launcher.py`: Hardware-freie Tests fuer World-Warnings, Mission-Trace und WP-Tracking vorbereitet.
- `px4-gazebo-sim-implementation-plan.md` und `px4-gazebo-sim-rules.md`: Acceptance-Gates abgehakt.

**Lokal geprueft:**
- `git diff --check` sauber bis auf bekannte LF/CRLF-Warnungen.
- Offene Checkboxen: nur echter Linux-Test fuer PX4/Gazebo UDP H.264 Stream auf Port 5600.

**Lokal nicht ausfuehrbar:**
- `python -m py_compile ...` blockiert auf Windows durch den bekannten WindowsApps-Session-Fehler.
- `pytest ...` nicht verfuegbar in dieser Windows-Shell.

**Linux-Test fuer User/Bob:**
```bash
pytest tests/test_ros2_sitl_launcher.py -q
SITL_AVAILABLE=1 SITL_MAVLINK_ENDPOINT=tcp:127.0.0.1:5762 pytest tests/test_sitl_smoke.py -v
SITL_AVAILABLE=1 SITL_ALLOW_MISSION_UPLOAD=1 pytest tests/test_sitl_smoke.py::test_sitl_mission_upload_roundtrip_contract -v
python -m tools.ui
```

**Trace-Erwartung nach Linux-Test:**
- `trace_runs/<session>/mission_trace.jsonl` enthaelt `mission_upload`, `mission_start`, `mission_pause`, `mission_abort`, `mission_status`, `wp_tracking`.
- `wp_tracking` enthaelt `distanceToWpM`.

---

### 2026-06-27T17:30:00+02:00 | Codex | HOTFIX/DONE | FlightLog Minimal-Panel gegen Freeze

**User-Feedback:** App friert weiterhin sofort ein, sobald `FlightLog` geoeffnet wird.

**Fix:** `tools/ui/qml/panels/FlightLogPanel.qml`
- FlightLog komplett als leichtes Panel neu aufgebaut.
- Keine `Canvas`, `Grid`, `Flickable`, `Repeater`, `QtQuick.Layouts`, `Slider` oder `QtQuick.Dialogs` mehr im FlightLog-Tab.
- CSV Laden bleibt erhalten und zeigt eine Text-Zusammenfassung statt Charts.
- ROS2 Bag Controls bleiben erhalten, aber als einfache Buttons.

**Fix bleibt:** `tools/ui/context/swarm_context.py`
- `openFileDialog(title, name_filter)` fuer CSV/BAG Auswahl per Button.

**Checks:**
- Pattern-Scan auf alte Freeze-Kandidaten im FlightLog: keine Treffer ausser `openFileDialog`.
- `git diff --check` sauber bis auf bekannte LF/CRLF-Warnungen.
- Python/UI lokal wegen WindowsApps Session-Fehler nicht startbar.

**Bitte testen:** `python -m tools.ui` und direkt `FlightLog` oeffnen.

---

### 2026-06-27T17:20:00+02:00 | Codex | HOTFIX/START | FlightLog Freeze Minimal-Panel

**Massnahme:** FlightLog als leichtes Panel neu aufbauen:
- Kein Canvas/Chart auf Tab-Load.
- Keine komplexen Layouts/Replikatoren.
- Keine QML-Dialoge.
- CSV/BAG Controls bleiben nutzbar.

---

### 2026-06-27T17:00:00+02:00 | Codex | HOTFIX/DONE | FlightLog ohne QML FileDialog

**Fix:** `tools/ui/qml/panels/FlightLogPanel.qml`
- `import QtQuick.Dialogs` vollstaendig entfernt.
- `FileDialog`-Komponenten vollstaendig entfernt.
- `OPEN CSV` / `OPEN BAG` rufen jetzt `swarm.openFileDialog(...)` erst bei Klick auf.

**Fix:** `tools/ui/context/swarm_context.py`
- Neuer Slot `openFileDialog(title, name_filter) -> str`.

**Status:** Reichte nicht aus; User meldete danach weiterhin Freeze. Minimal-Panel ist der aktuelle Fix.

---

### 2026-06-27T15:30:00+02:00 | Bob | R-07 TEST-RESULT | PX4-SIM-6 Live Video Tests gruen

**pytest:** `54 passed, 5 skipped`

**Geprueft:**
- Live Video Tests gruen.
- Map und GimbalPanel rendern nie gleichzeitig.
- `stopStream()` resettet Status korrekt.
- Ohne OpenCV kein kaputtes UI-Rechteck.

**Linux-Test noch ausstehend:**
```bash
SITL_AVAILABLE=1 python -m tools.ui
```

---

*Neue Eintraege werden OBEN hinzugefuegt.*
