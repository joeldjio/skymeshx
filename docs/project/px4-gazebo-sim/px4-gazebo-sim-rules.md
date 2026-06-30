# PX4 + Gazebo + ROS2 Sim — Collaboration Rules
# Gültig für Bob & Codex

**Zweck:** Verbindliche Regeln für die gesamte PX4-Sim-Implementierungsphase.  
**Plan:** `docs/project/px4-gazebo-sim/px4-gazebo-sim-implementation-plan.md`  
**Feedback:** `docs/project/px4-gazebo-sim/px4-gazebo-sim-collab-feedback.md`

---

## 1. Coordination Rules

### R-01 — Feedback File First
Vor **jedem** Code-Commit schreibt der Autor einen kurzen Eintrag in `px4-gazebo-sim-collab-feedback.md`.  
Format: `### <ISO-Timestamp> | <Bob/Codex> | <Typ> | <Kurztitel>`  
Neue Einträge **oben** einfügen.

### R-02 — Keine simultanen Edits
Nicht dieselbe Python- oder QML-Datei gleichzeitig bearbeiten. Vor dem Bearbeiten im Feedback File ankündigen: `Working on: <datei>`.

### R-03 — API Contract vor Implementierung
Codex definiert jede neue Backend-API (Properties, Slots, Signals) im Feedback File **bevor** die Datei existiert.  
Bob wartet auf die API-Bestätigung bevor er die zugehörige QML-Seite implementiert.

### R-04 — Minimale Änderungen
Nur das implementieren was im Plan steht. Keine spontanen Refactors, keine ungeplanten Features.  
Ausnahme: Bugfix der einen bestehenden Test brechen würde — sofort melden.

---

## 2. Testing Rules

### R-05 — Alle Tests hardware-free
Jede neue Datei braucht hardware-free Tests. Kein MAVLink, kein ROS2, kein Gazebo, kein SITL in normalen Tests.  
Subprocess-Calls werden mit `unittest.mock.patch` gemockt.

### R-06 — SITL Tests sind opt-in
SITL-Tests werden mit `@pytest.mark.sitl` markiert.  
Sie werden **nur** ausgeführt wenn `SITL_AVAILABLE=1` gesetzt ist.  
Niemals in den normalen CI-Lauf eingebunden.

### R-07 — Bob führt alle pytest-Läufe durch
Codex kann pytest auf diesem System nicht ausführen (Windows Session-Error).  
Nach jedem Codex-Commit: Bob führt den relevanten pytest-Befehl aus und meldet Ergebnis im Feedback File.

### R-08 — Grüne Tests vor nächster Phase
Eine Phase darf erst begonnen werden wenn alle Tests der Vorgängerphase grün sind.

---

## 3. Architecture Rules

### R-09 — TraceLogger immer aktiv
`TraceLogger` läuft ab Implementierung immer — kein Feature-Flag, keine "nur im Debug-Modus"-Einschränkung.  
Rate-Limiting verhindert Performance-Impact: max 1 ROS2-Topic-Event pro Topic pro Sekunde.

### R-10 — Video: kein leeres Video-Rechteck
Die Map-Overlay und GimbalPanel Live View dürfen **niemals** ein leeres oder kaputtes Video-Rechteck zeigen, bevor der Stream-Status `receiving` ist.  
Zulässige Zustände sichtbar machen: `waiting`, `stalled`, `error` als Text/Badge.

### R-11 — MAVLink / PX4 ROS2 nicht vermischen
PX4-Sim läuft über `ros2_uxrce` Pfad. Kein automatisches Routing von PX4-Mission-Kommandos über ArduPilot-Code-Pfade.  
Das Autopilot-Backend wird im Launch-Profil explizit als `"autopilot": "px4"` gesetzt.

### R-12 — Namespace explizit
Namespaces (`px4_1` / `uav_1`) werden im Launch-Profil und im `manifest.json` explizit gesetzt.  
Kein implizites Raten des Namespaces aus dem Drone-ID.

### R-13 — Upload ≠ Execute (gilt weiter)
Diese Regel aus der Camera/Seeding/Solar-Phase gilt auch für PX4-Sim-Tests.  
Kein Upload-Worker startet automatisch die Mission.

### R-14 — Trace Bundle Pfad
Trace Bundles liegen in `trace_runs/<timestamp>_<scenario>/` im Projekt-Root.  
Nicht unter `logs/` (das ist für rotierende System-Logs).

---

## 4. Complexity Split

### R-15 — Codex übernimmt komplexe Aufgaben

| Komplex → Codex | Einfach → Bob |
|----------------|---------------|
| `TraceLogger` Singleton mit JSONL-Writer, Rate-Limiter, Manifest, Session-Management | Trace Bundle Controls UI (Start/Stop Buttons, Status-Text) |
| `VideoContext` State Machine (unconfigured/waiting/receiving/stalled/error) | Video Port-Eingabe, Status-Badge Farben, Map-Overlay Bedingung |
| ROS2 Topic Discovery + Health Messung (Hz, last age, QoS, auto-subscribe) | Topic Browser UI (Liste, Filter, Hz-Badge, Watch List) |
| Bag Recorder Presets + subprocess-Steuerung + manifest-Integration | Bag UI (Preset-Dropdown, Start/Stop, Dauer, FlightLog-Link) |
| SITL Launch Profiles + Gazebo World Profiles + `PX4_GZ_WORLD` Env-Handling | SITL UI (Dropdown, World-Profil, Warnungen, Multi-Vehicle) |
| SITL Smoke Tests `@pytest.mark.sitl` | SITL Test-Checklisten (Markdown, manuell) |
| `analyze_trace.py` CLI → Markdown Report | ROS2 Panel 5-Tab Overhaul (Connection/Topics/Bag/Video/Debug) |

### R-16 — Feedback File Bereinigung
Die Feedback-Datei darf **max. 25 Einträge** enthalten. Sobald sie diese Grenze überschreitet:

1. Alle Einträge **älter als die laufende Phase** werden in eine Archiv-Datei verschoben:
   `docs/project/not-fertig/px4-gazebo-sim-feedback-archive-<YYYY-MM>.md`
2. In der aktiven Feedback-Datei bleibt ein **Platzhalter-Verweis**:
   `> Ältere Einträge → [Archiv YYYY-MM](not-fertig/px4-gazebo-sim-feedback-archive-YYYY-MM.md)`
3. Die letzten **5 Einträge** bleiben immer in der aktiven Datei, auch wenn sie alt sind (Kontext-Anker).
4. Wer den Bereinigungsschritt durchführt, schreibt danach einen `[CLEANUP]`-Eintrag als neuen obersten Eintrag.

**Wann bereinigen?**
- Am Start einer neuen Phase (z. B. nach Phase 1 → Phase 2)
- Oder wenn die Datei `> 200 Zeilen` überschreitet — was auch zuerst eintritt

---

## 5. Acceptance Gate

Bevor der Nutzer die ersten Linux-SITL-Tests durchführt, müssen folgende Punkte erfüllt sein:

- [x] `TraceLogger` + `TraceContext` implementiert und getestet
- [x] `manifest.json` enthält: PX4 Modell, World, Namespace, Video-Port, Szenario
- [x] `ros2_topic_health.json` wird beim Session-Stop exportiert
- [x] `mission_trace.jsonl` enthält `wp_tracking` Einträge
- [x] Video-Port pro Drone konfigurierbar in der UI
- [x] Map/GimbalPanel zeigt **kein leeres Video** vor `receiving`
- [x] Bag Recording start/stop funktioniert
- [x] Mission upload/start/pause/abort sind im Trace sichtbar

---

## 6. Kommunikation

- **Sprache:** Deutsch (User) + Englisch (Code, APIs, Docstrings)
- **Feedback-Einträge:** Deutsch erlaubt, Englisch für Code-Snippets
- **Entscheidungen:** Im Feedback File dokumentieren, nicht im Code-Kommentar verstecken
- **Blocker:** Sofort im Feedback File melden mit `[BLOCKER]` Tag
