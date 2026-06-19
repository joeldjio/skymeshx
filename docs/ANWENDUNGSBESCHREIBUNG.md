# SkyMeshX Project - Anwendungsbeschreibung

## Überblick

Das **SkyMeshX Project** (auch bekannt als **skymeshx**) ist eine umfassende Python-basierte Forschungsplattform für die Steuerung und Koordination von unbemannten Luftfahrzeugen (UAVs/Drohnen). Die Anwendung dient als Ground Control Station (GCS) mit moderner grafischer Benutzeroberfläche und bietet fortgeschrittene Funktionen für Schwarmsteuerung, autonome Missionen und Sicherheitsüberwachung.

## Hauptfunktionen

### 1. Ground Control Station (GCS)
- **Moderne Qt6/QML-Benutzeroberfläche** mit dunklem Theme und professionellem Design
- **Echtzeit-Telemetrie-Anzeige** für Position, Geschwindigkeit, Batteriestatus, GPS-Qualität
- **3D-Kartenansicht** zur Visualisierung von Drohnenpositionen und Flugpfaden
- **Multi-Drohnen-Dashboard** für gleichzeitige Überwachung mehrerer UAVs
- **Fluglog-Wiedergabe** zur Analyse vergangener Flüge

### 2. Drohnensteuerung
- **MAVLink-Protokoll-Unterstützung** für ArduPilot und PX4
- **ROS2-Integration** für erweiterte Robotik-Funktionen
- **Missionsplanung und -upload** mit Wegpunkt-Navigation
- **Manuelle Steuerung** über Kommandozeile oder GUI
- **Automatische Zustandsverwaltung** (FSM - Finite State Machine)

### 3. Schwarmkoordination
- **Multi-UAV-Koordination** für bis zu 10+ Drohnen gleichzeitig
- **Formationsflug** (Kreis, Linie, Gitter, V-Formation)
- **Kollisionsvermeidung** durch Artificial Potential Fields (APF)
- **Dezentralisierte Steuerung** mit Coordinator-UAV-Konzept
- **LLM-basierte Schwarmsteuerung** für natürlichsprachliche Befehle

### 4. Sicherheitssysteme
- **APF Safety Filter** (20Hz) zur Echtzeit-Kollisionsvermeidung
- **Geofencing** zur Begrenzung des Flugbereichs
- **Automatische Notfallprozeduren** (RTL - Return to Launch)
- **Batterieüberwachung** mit Warnungen bei niedrigem Ladestand
- **GPS-Qualitätsprüfung** vor dem Start

### 5. Datenerfassung und Analyse
- **JSONL-Logging** für strukturierte Telemetriedaten
- **ROS2 Bag Recording** für detaillierte Flugaufzeichnungen
- **Echtzeit-Plotting** von Flugparametern
- **Experimentverwaltung** für wissenschaftliche Studien
- **Metriken-Berechnung** (Position Error, Speed, etc.)

## Architektur

### Kernkomponenten

```
skymeshx/
├── core/              # Grundlegende Funktionen
│   ├── connection.py  # MAVLink-Verbindungsverwaltung
│   ├── fsm.py         # Zustandsmaschine für Drohnensteuerung
│   └── telemetry.py   # Telemetriedaten-Verarbeitung
│
├── autopilot/         # Autopilot-Backends
│   ├── mavlink/       # MAVLink-Backend (ArduPilot/PX4)
│   └── px4/           # PX4-spezifische Funktionen
│
├── ros/               # ROS2-Integration
│   ├── bridge.py      # ROS2-MAVLink-Bridge
│   ├── px4_bridge.py  # PX4-ROS2-Bridge mit Frame-Konvertierung
│   └── context.py     # ROS2-Kontext-Management
│
├── control/           # Steuerungslogik
│   ├── mission.py     # Missionsplanung und -upload
│   └── script_runner.py # Skript-basierte Steuerung
│
├── safety/            # Sicherheitssysteme
│   └── apf.py         # Artificial Potential Fields Filter
│
├── models/            # UAV-Modelle
│   ├── generic_uav.py      # Basis-UAV-Klasse
│   ├── coordinator_uav.py  # Schwarm-Koordinator
│   └── observation_uav.py  # Beobachtungs-UAV
│
├── sdk/               # High-Level API
│   ├── drone.py       # Einfache Drohnen-API
│   ├── swarm_api.py   # Schwarm-API
│   └── formations.py  # Formationsalgorithmen
│
├── data/              # Datenmanagement
│   ├── logger.py      # JSONL-Logger
│   └── store.py       # Datenspeicherung
│
├── simulation/        # Simulationstools
│   ├── sitl.py        # SITL-Management
│   └── replay.py      # Flugwiedergabe
│
└── llm/               # LLM-Integration
    └── swarm_commander.py # Natürlichsprachliche Steuerung
```

### UI-Komponenten

```
tools/ui/
├── app.py             # Hauptanwendung
├── backend.py         # Backend-Logik
├── main_window.py     # Hauptfenster
│
├── context/           # Kontext-Manager (Service Locator Pattern)
│   ├── swarm_context.py      # Schwarmverwaltung
│   ├── telemetry_context.py  # Telemetriedaten
│   ├── safety_context.py     # Sicherheitssysteme
│   ├── experiment_context.py # Experimentverwaltung
│   └── ros2_context.py       # ROS2-Integration
│
└── qml/               # QML-UI-Komponenten
    ├── main.qml       # Hauptlayout
    ├── components/    # Wiederverwendbare Komponenten
    │   ├── Theme.qml  # Design-System (Farben, Spacing, etc.)
    │   ├── Header.qml # Kopfzeile
    │   └── NavBar.qml # Navigation
    └── panels/        # Hauptpanels
        ├── DashboardPanel.qml  # Übersicht
        ├── SwarmPanel.qml      # Schwarmsteuerung
        ├── SafetyPanel.qml     # Sicherheitsüberwachung
        ├── ROS2Panel.qml       # ROS2-Integration
        └── ExperimentPanel.qml # Experimentverwaltung
```

## Wie es funktioniert

### 1. Verbindungsaufbau

```python
from skymeshx.sdk import Drone

# Verbindung zu einer Drohne herstellen
drone = Drone()
drone.connect("tcp:127.0.0.1:5762")  # SITL-Simulation
# oder
drone.connect("udp:127.0.0.1:14550")  # Reale Drohne
```

**Ablauf:**
1. MAVLink-Verbindung wird über `pymavlink` hergestellt
2. Heartbeat-Nachrichten werden gesendet (1Hz)
3. Telemetriedaten werden empfangen und verarbeitet
4. Zustandsmaschine (FSM) wird initialisiert

### 2. Zustandsverwaltung (FSM)

Die Drohne durchläuft verschiedene Zustände:

```
DISCONNECTED → CONNECTED → ARMED → AIRBORNE → MISSION → LANDING → LANDED
                    ↓                                              ↓
                  DISARMED ←────────────────────────────────────────
```

**Wichtige Zustände:**
- `DISCONNECTED`: Keine Verbindung
- `CONNECTED`: Verbunden, aber nicht bereit
- `ARMED`: Motoren scharf, bereit zum Start
- `AIRBORNE`: In der Luft
- `MISSION`: Führt Mission aus
- `LANDING`: Landeanflug
- `LANDED`: Gelandet

### 3. Missionsausführung

```python
from skymeshx.control import MissionEngine

# Mission erstellen
mission = MissionEngine(drone.connection)
mission.add_takeoff(altitude=10)
mission.add_waypoint(lat=47.397742, lon=8.545594, alt=20)
mission.add_waypoint(lat=47.398, lon=8.546, alt=20)
mission.add_land()

# Mission hochladen und starten
mission.upload()
drone.set_mode("AUTO")
```

**Ablauf:**
1. Wegpunkte werden im MAVLink-Format erstellt
2. Mission wird über `MISSION_COUNT` und `MISSION_ITEM` hochgeladen
3. Drohne wechselt in AUTO-Modus
4. Wegpunkte werden nacheinander abgeflogen

### 4. Schwarmkoordination

```python
from skymeshx.sdk import SwarmAPI

# Schwarm erstellen
swarm = SwarmAPI()
swarm.add_drone("D1", "tcp:127.0.0.1:5762")
swarm.add_drone("D2", "tcp:127.0.0.1:5772")
swarm.add_drone("D3", "tcp:127.0.0.1:5782")

# Alle Drohnen verbinden
swarm.connect_all()

# Formation fliegen
swarm.circle_formation(radius=20, altitude=15)
```

**Ablauf:**
1. Jede Drohne erhält eine Position in der Formation
2. APF Safety Filter berechnet sichere Trajektorien
3. Kollisionsvermeidung durch Abstoßungskräfte
4. Koordinator-UAV überwacht den Schwarm

### 5. Sicherheitssysteme

**APF (Artificial Potential Fields):**
- Läuft mit 20Hz
- Berechnet Abstoßungskräfte zwischen Drohnen
- Verhindert Kollisionen durch Trajektorien-Anpassung
- Verwendet lokale NED-Koordinaten (North-East-Down)

```python
from skymeshx.safety import APFFilter

# APF-Filter erstellen
apf = APFFilter(
    repulsion_gain=2.0,
    min_distance=5.0,  # Mindestabstand in Metern
    max_speed=5.0      # Maximale Geschwindigkeit
)

# Position filtern
safe_position = apf.filter(
    current_pos=(0, 0, -10),
    target_pos=(10, 10, -10),
    obstacles=[(5, 5, -10)]  # Andere Drohnen
)
```

### 6. ROS2-Integration

**Frame-Konvertierung (PX4):**
- PX4 verwendet NED (North-East-Down) + FRD (Forward-Right-Down)
- ROS2 verwendet ENU (East-North-Up) + FLU (Forward-Left-Up)
- Automatische Konvertierung durch `px4_bridge.py`

```python
from skymeshx.ros import PX4Bridge

# Bridge erstellen
bridge = PX4Bridge(drone_id="D1")
bridge.start()

# Offboard-Steuerung
bridge.send_position_setpoint(
    x=10.0,  # North (NED) oder East (ENU)
    y=5.0,   # East (NED) oder North (ENU)
    z=-15.0  # Down (NED) oder Up (ENU)
)
```

### 7. Datenerfassung

**JSONL-Logging:**
```python
from skymeshx.data import Logger

# Logger erstellen
logger = Logger("flight_data.jsonl")
logger.start()

# Telemetriedaten loggen
logger.log({
    "timestamp": time.time(),
    "drone_id": "D1",
    "position": {"lat": 47.397, "lon": 8.545, "alt": 15.0},
    "velocity": {"vx": 2.0, "vy": 1.0, "vz": 0.0},
    "battery": 85.0
})

logger.stop()
```

**ROS2 Bag Recording:**
```python
from skymeshx.ros import BagRecorder

# Recorder erstellen
recorder = BagRecorder(output_dir="bags/")
recorder.start_recording(topics=[
    "/fmu/out/vehicle_local_position",
    "/fmu/out/vehicle_status"
])

# ... Flug durchführen ...

recorder.stop_recording()
```

## Verwendungsszenarien

### 1. Einzeldrohnen-Steuerung
```bash
# CLI verwenden
skymeshx connect --port tcp:127.0.0.1:5762
skymeshx arm
skymeshx takeoff --altitude 10
skymeshx goto --lat 47.398 --lon 8.546 --alt 15
skymeshx land
```

### 2. Schwarmflug
```bash
# Python-Skript
python examples/swarm_circle.py --num-drones 5 --radius 20
```

### 3. Autonome Exploration
```bash
# Mit Frontier-basierter Exploration
python examples/autonomous_exploration.py --backend px4
```

### 4. LLM-gesteuerte Schwärme
```bash
# Natürlichsprachliche Befehle
python examples/llm_swarm_control.py --interactive
> "Fly 3 drones in a circle formation at 15m altitude"
```

### 5. Experimentdurchführung
```bash
# Geschwindigkeitsexperiment
python examples/speed_experiment.py --speeds 1,2,3,4,5
```

## Technische Details

### Kommunikationsprotokolle

**MAVLink:**
- Binärprotokoll für Drohnenkommunikation
- Unterstützt ArduPilot und PX4
- Nachrichten: `HEARTBEAT`, `COMMAND_LONG`, `MISSION_ITEM`, etc.
- Standard-Ports: 5760 (MAVProxy), 5762 (SITL), 14550 (UDP)

**ROS2:**
- Robotics Middleware Framework
- DDS-basierte Kommunikation (uXRCE-DDS für PX4)
- Topics: `/fmu/out/*` (PX4→ROS2), `/fmu/in/*` (ROS2→PX4)

### Koordinatensysteme

**NED (North-East-Down):**
- X: Nord
- Y: Ost
- Z: Unten (negativ = Höhe)
- Verwendet von ArduPilot und PX4

**ENU (East-North-Up):**
- X: Ost
- Y: Nord
- Z: Oben (positiv = Höhe)
- ROS2-Standard

**APF-Koordinaten:**
- Lokale NED-Meter
- Z ist **positiv nach oben** (Höhe über Grund)
- Filter invertiert Z intern für NED-Berechnungen

### Performance

**Echtzeit-Anforderungen:**
- Telemetrie-Update: 10Hz
- APF Safety Filter: 20Hz
- Heartbeat: 1Hz
- Mission-Upload: ~50ms pro Wegpunkt

**Ressourcenverbrauch:**
- UI: ~100-200 MB RAM
- Backend: ~50-100 MB RAM pro Drohne
- Raspberry Pi Server: ~20 MB RAM, <5% CPU

## Installation und Setup

### Voraussetzungen
- Python 3.8+
- PyQt6 (für UI)
- pymavlink
- Optional: ROS2 Humble, px4_msgs

### Installation
```bash
# Basis-Installation
pip install -e .

# Mit ROS2-Unterstützung
pip install -e ".[ros]"

# Mit Test-Dependencies
pip install -e ".[test]"
```

### SITL-Simulation starten
```bash
# ArduCopter SITL
sim_vehicle.py -v ArduCopter --console --map

# PX4 SITL mit Gazebo
cd ~/PX4-Autopilot
make px4_sitl gazebo
```

### UI starten
```bash
python -m tools.ui
```

## Testing

Das Projekt verfügt über umfangreiche Tests:

```bash
# Alle Tests ausführen (~1 Sekunde)
pytest tests/

# Spezifische Tests
pytest tests/test_apf.py -v
pytest tests/test_mission.py -v

# Mit Coverage
pytest tests/ --cov=skymeshx
```

**Test-Architektur:**
- Hardware-frei durch Mocking
- Fixtures in `tests/conftest.py`
- `FakeConnection`, `FakeMav`, `FakeTelemetry`
- Keine echten Drohnen oder SITL erforderlich

## Lizenzierung

Das Projekt verwendet ein duales Lizenzmodell:
- **Open Source**: GPL-3.0 für nicht-kommerzielle Nutzung
- **Commercial**: Kommerzielle Lizenz für Unternehmen

Lizenzprüfung erfolgt über `tools/ui/license.py` mit Hardware-ID-basierter Aktivierung.

## Weiterführende Dokumentation

- [`docs/setup/installation.md`](setup/installation.md) - Detaillierte Installationsanleitung
- [`docs/setup/px4-sitl.md`](setup/px4-sitl.md) - PX4 SITL Setup
- [`docs/setup/raspberry-pi.md`](setup/raspberry-pi.md) - Raspberry Pi Deployment
- [`docs/ui/ui-documentation.md`](ui/ui-documentation.md) - UI-Dokumentation
- [`docs/project/overview.md`](project/overview.md) - Projekt-Übersicht
- [`AGENTS.md`](../AGENTS.md) - Entwickler-Richtlinien

## Support und Entwicklung

**Repository:** https://github.com/yourusername/skymeshxproject

**Entwicklung:**
- Feature Branches für neue Funktionen
- Pull Requests mit Code Review
- CI/CD mit GitHub Actions
- Automatische Tests bei jedem Commit

**Kontakt:**
- Issues auf GitHub
- Diskussionen im Repository
- E-Mail: support@example.com