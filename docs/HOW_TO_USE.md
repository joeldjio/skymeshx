# SkyMeshX How To Use

Diese Anleitung erklaert, wie du die Software praktisch benutzt, welche Features es gibt und worauf du achten musst. Sie fasst die vorhandenen Setup-, UI-, Feature- und Security-Dokumente zu einem Arbeitsablauf zusammen.

## 1. Grundregeln vor jedem Flug

SkyMeshX kann reale UAVs steuern. Teste neue Workflows zuerst in SITL oder Demo-Modus, danach mit abgenommenen Propellern, und erst dann im echten Flug.

Wichtig:

- Der Standard-Port fuer ArduCopter SITL ist `tcp:127.0.0.1:5762`.
- `tcp:127.0.0.1:5760` ist typischerweise MAVProxy-aggregiert, nicht der Raw-SITL-Port.
- Nutze nie gleichzeitig zwei aktive Controller fuer dasselbe Fahrzeug, zum Beispiel MAVLink-UI und ROS2-Offboard fuer dieselbe Drohne.
- Mission Upload ist blockierend und darf nicht aus dem Qt/UI-Hauptthread heraus direkt laufen.
- Pruefe vor jedem Start: GPS, Akku, Home-Position, Geofence, Flugmodus, Failsafe, Propellerbereich, Missionhoehe und Wegpunktanzahl.
- Python-Experimentskripte und JSON-Szenarien gelten als vertrauenswuerdig. Starte nur Dateien, die du selbst kontrollierst.

## 2. Installation und Start

Core installieren:

```bash
pip install -e .
```

Mit Entwicklungs- und Test-Abhaengigkeiten:

```bash
pip install -e ".[dev]"
pip install -e ".[test]"
```

Tests ausfuehren:

```bash
python -m pytest -q
```

UI starten:

```bash
python -m tools.ui
```

Wenn der Einstiegspunkt in deiner Umgebung anders registriert ist, nutze:

```bash
python -m tools.ui.app
```

CLI-Beispiele:

```bash
skymeshx connect
skymeshx status --port tcp:127.0.0.1:5762
DRONE_PORT=udp:127.0.0.1:14550 skymeshx arm
```

Port-Aufloesung:

1. `--port`
2. Umgebungsvariable `DRONE_PORT`
3. Default `tcp:127.0.0.1:5762`

## 3. Erster sicherer Test mit SITL

1. Starte ArduCopter SITL.
2. Starte SkyMeshX UI mit `python -m tools.ui`.
3. Verbinde mit `tcp:127.0.0.1:5762`.
4. Warte auf stabile Telemetrie.
5. Fuehre kleine Kommandos aus: `ARM`, `TAKEOFF` mit niedriger Hoehe, `LAND`.
6. Teste Wegpunkte erst mit kleinen Distanzen.

Beispiel:

```bash
python examples/hover.py --port tcp:127.0.0.1:5762
```

Worauf achten:

- Wenn keine Verbindung kommt, pruefe ob SITL wirklich auf `5762` lauscht.
- Wenn du MAVProxy verwendest, kann `5760` richtig sein.
- Firewall und bereits belegte Ports koennen Verbindungen blockieren.

## 4. UI-Uebersicht

Die UI ist die zentrale Bodenstation fuer Verbindung, Telemetrie, Karte, Missionen, Schwarm, Sicherheit, ROS2, Experimente und Logs.

### Header

Im Header waehlst du Verbindungstyp und Ziel:

- Serial, UDP oder TCP
- Port/Endpoint
- Baudrate bei serieller Verbindung
- aktive Drohne
- Verbindungsstatus

Worauf achten:

- Die ausgewaehlte Drohne ist fuer viele Einzelaktionen relevant.
- Schwarm- und Missionsaktionen koennen mehrere Drohnen betreffen. Pruefe immer die markierten Ziel-Drohnen.

### InstrBar

Die InstrBar enthaelt schnelle Befehle:

- `ARM`
- `DISARM`
- `TAKEOFF`
- `LAND`
- `RTL`
- `HOLD`
- Zielhoehe
- APF/Sicherheitsfilter

Worauf achten:

- `DISARM` in der Luft ist gefaehrlich, wenn Force-Disarm verwendet wird.
- `TAKEOFF` braucht passende Hoehe und einen Flugmodus, den der Autopilot akzeptiert.
- `RTL` haengt von korrekter Home-Position und genug Akku ab.

### Dashboard

Das Dashboard zeigt Telemetrie wie:

- Flugmodus
- Armed-Status
- Hoehe
- Geschwindigkeit
- Akku
- Position
- Link-/Systemstatus

Nutze das Dashboard als Plausibilitaetscheck vor jeder Aktion.

### MapView

Die Karte zeigt:

- aktuelle Drohnenpositionen
- Flugspur
- Wegpunkte
- Seed-Drops
- Sicherheitszonen
- Kollisionswarnungen

Typischer Workflow:

1. Karte auf Einsatzgebiet zentrieren.
2. Wegpunkte oder Feldgrenzen setzen.
3. Mission generieren.
4. Route visuell pruefen.
5. Upload ausloesen.

Worauf achten:

- GPS-Koordinaten muessen plausibel sein.
- Hoehen sind in Metern zu verstehen, meistens relativ/AGL im Missionskontext.
- Wegpunkte duerfen nicht in Hindernisse, Sperrbereiche oder ausserhalb der Funkreichweite fuehren.

## 5. Einzelne Drohne steuern

Python-Beispiel:

```python
from skymeshx import Drone

drone = Drone("D1", "tcp:127.0.0.1:5762")
if drone.connect():
    drone.arm()
    drone.takeoff(10)
    drone.land()
    drone.disconnect()
```

Worauf achten:

- Connection-Funktionen geben in diesem Projekt oft `True`/`False` zurueck statt Exceptions.
- Pruefe Rueckgabewerte.
- Fuehre nach Fehlern lieber `LAND` oder `RTL` aus, statt weitere Missionen zu starten.

## 6. Missionen und Wegpunkte

Missionen bestehen aus Wegpunkten und optionalen MAVLink-Kommandos. Der Mission Upload ist blockierend und dauert grob ca. 50 ms pro Wegpunkt.

Typischer Ablauf:

1. Wegpunkte erzeugen oder auf der Karte setzen.
2. Mission im UI pruefen.
3. Ziel-Drohnen auswaehlen.
4. Upload starten.
5. Upload-Ergebnis im Log pruefen.
6. Mission starten.

Worauf achten:

- Upload nicht im UI-Hauptthread ausfuehren.
- Vor dem Start Wegpunktanzahl, Hoehe, Geschwindigkeit und Endaktion pruefen.
- Bei ArduPilot gibt es relevante Limits, zum Beispiel fuer grosse Seeding-Missionen.
- Missionen auf fliegende Drohnen muessen anders behandelt werden als Missionen am Boden.

## 7. Drag-and-Drop Waypoints

In der UI koennen Wegpunkte direkt auf der Karte erstellt, verschoben und geloescht werden.

Nutzen:

- schnelle Missionsskizze
- visuelle Kontrolle
- manuelle Korrektur generierter Routen

Worauf achten:

- Nach dem Verschieben Mission neu validieren.
- Karte und Autopilot muessen dieselbe Realweltposition meinen.
- Kleine Drag-Fehler koennen in realen GPS-Koordinaten grosse Folgen haben.

## 8. Schwarmsteuerung

SkyMeshX unterstuetzt mehrere Drohnen mit parallelen Operationen.

Python-Beispiel:

```python
from skymeshx import Swarm

swarm = Swarm()
swarm.add("D1", "tcp:127.0.0.1:5762")
swarm.add("D2", "tcp:127.0.0.1:5763")
swarm.add("D3", "tcp:127.0.0.1:5764")

results = swarm.connect_all()
swarm.arm_all()
swarm.takeoff_all(10.0)
swarm.formation("v", spacing=5.0, leader="D1")
swarm.land_all()
swarm.disconnect_all()
```

Features:

- mehrere Drohnen hinzufuegen und entfernen
- paralleles Verbinden
- paralleles Arm/Takeoff/Land/RTL
- Formationen: Line, V, Grid, Circle, Wedge
- Leader-Follower
- Schwarm-Telemetrie

Worauf achten:

- Jede Drohne braucht eine eindeutige ID.
- Jede Drohne braucht einen eigenen Port/Endpoint.
- Formation spacing muss zu Drohnengroesse, Wind, GPS-Genauigkeit und Geschwindigkeit passen.
- APF und Kollisionswarnung aktivieren, bevor mehrere Drohnen eng fliegen.
- Nicht alle Drohnen schaffen Befehle gleich schnell; plane mit dem langsamsten Fahrzeug.

## 9. Formationen

Formationen verwenden lokale NED-Offsets relativ zum Leader.

Unterstuetzte Formen:

- `line`: Drohnen folgen hintereinander.
- `v`: V-Formation mit Leader an der Spitze.
- `grid`: Raster fuer Abdeckung.
- `circle`: Kreis um den Leader.
- `wedge`: engere V-Variante.

Worauf achten:

- Zu kleine Abstaende koennen Kollisionen verursachen.
- Zu grosse Abstaende koennen Funk, Sichtlinie oder Geofence verletzen.
- Dynamisches Folgen braucht stabile Telemetrie und realistische Update-Raten.

## 10. Safety: APF, Geofence, Batterie und Kollision

### APF Safety Filter

Der APF-Filter laeuft standardmaessig mit ca. 20 Hz und begrenzt Zielbewegungen anhand von:

- Mindestabstand
- Maximalgeschwindigkeit
- Repulsion/Attraction Gain
- Geofence-Radius
- Mindest-/Maximalhoehe
- Hindernisradius

Koordinaten:

- `Pose3D.x` = North
- `Pose3D.y` = East
- `Pose3D.z` = altitude above ground, positiv nach oben

Worauf achten:

- PX4 NED nutzt Down positiv, APF nutzt aber `z` als Hoehe positiv nach oben.
- Falsches Vorzeichen bei Hoehe ist ein klassischer Fehler.
- APF ersetzt keine echte Hinderniserkennung und keine Pilotverantwortung.

### Collision Prediction

Die Kollisionsvorhersage analysiert Positionen und Geschwindigkeiten und zeigt Warnungen auf der Karte.

Severity:

- Critical: sehr kleiner Abstand
- Warning: wahrscheinliche Annaeherung
- Caution: enger Vorbeiflug

Worauf achten:

- Nur bewaffnete/aktive Drohnen werden sinnvoll bewertet.
- Die Vorhersage ist linear und kennt geplante Kurven nur begrenzt.
- Ohne gueltige Velocity-Daten kann die Warnung fehlen oder ungenau sein.

### Smart Battery Monitoring

Der Akku-Monitor schaetzt:

- verbleibende Flugzeit
- Entfernung zur Home-Position
- benoetigten Akku fuer RTL
- kritische und praediktive RTL-Ausloesung

Worauf achten:

- Der Monitor braucht mehrere Samples, bevor Prognosen stabil sind.
- Wind, Payload und Batteriealter koennen die Schaetzung verfaelschen.
- Setze konservative Sicherheitsmargen fuer reale Fluege.

## 11. Feldabdeckung

Die Feldabdeckung erzeugt automatische Wegpunktmuster fuer Agrar-, Mapping- oder Suchmissionen.

Patterns:

- Parallel Lines
- Spiral
- Grid
- Zigzag

Typischer Ablauf:

1. Home-Position setzen.
2. Feldgrenze mit mindestens drei GPS-Punkten definieren.
3. Pattern, Hoehe, Speed, Line Spacing und Overlap waehlen.
4. Wegpunkte generieren.
5. Missionsdauer schaetzen.
6. Mission validieren und hochladen.

Worauf achten:

- Feldpunkte muessen geordnet sein, im Uhrzeigersinn oder gegen den Uhrzeigersinn.
- Die GPS-Umrechnung ist fuer lokale Bereiche gedacht, nicht fuer riesige Distanzen.
- Es gibt keine automatische Hindernisvermeidung in generierten Wegpunkten.
- Hoehe ist fest; Terrain Following ist nicht automatisch enthalten.

## 12. Seeding Mission Planner

Der Seeding Planner erweitert Feldabdeckung um Servo-gesteuerte Seed-Drops.

Parameter:

- Seed spacing
- Servo channel
- Open PWM
- Close PWM
- Dispense duration
- Wait after drop

Missionstruktur pro Drop:

1. Navigation waypoint
2. Servo open command
3. Servo close command

Worauf achten:

- ArduPilot-Limit: maximal ca. 700 Wegpunkte.
- Kleine Seed-Abstaende erzeugen sehr viele Wegpunkte.
- Servo-Kanal, PWM-Werte und Stromversorgung vor dem Flug testen.
- `SERVOx_FUNCTION` und Flight-Controller-Ausgang muessen passen.
- Mechanik auf Klemmen, Verstopfung und Reaktionszeit testen.

## 13. Solar Park Inspection

Solar Inspection plant Flugbahnen entlang Panel-Reihen und kombiniert:

- Wegpunkte entlang Reihen
- Gimbal Pitch/Roll/Yaw
- Kamera-Trigger
- Thermal Camera Subscriber
- Hotspot Detection

Typischer Ablauf:

1. Panel-Reihen als Start-/End-GPS-Punkte definieren.
2. Hoehe ueber Panelen setzen.
3. Kamera-FOV, Overlap, Speed und Triggerdistanz setzen.
4. Mission generieren.
5. Thermal Topic pruefen.
6. Mission fliegen und Hotspots loggen.

Worauf achten:

- Gimbal Pitch `-90` bedeutet nach unten.
- Thermal-Kalibrierung muss zur Kamera passen.
- Hotspot-Schwellenwerte sind sensor- und wetterabhaengig.
- Bildueberlappung erhoeht Qualitaet, aber auch Flugzeit.

## 14. ROS2 und PX4 Bridge

SkyMeshX nutzt fuer PX4 ROS2 uXRCE-DDS.

Wichtig:

- PX4 native Frames: NED und FRD.
- ROS2 Standard Frames: ENU und FLU.
- PX4 Topics: `/fmu/out/*` und `/fmu/in/*`.
- Das ist nicht MAVLink-over-ROS und nicht FastRTPS.

Voraussetzungen:

- ROS2 Humble oder kompatibel
- `px4_msgs`
- `MicroXRCEAgent`
- PX4 SITL oder Hardware mit uXRCE-DDS

Startbeispiel:

```bash
MicroXRCEAgent udp4 -p 8888
```

PX4 SITL:

```bash
PX4_UXRCE_DDS_NS=uav_1 make px4_sitl gz_x500
```

UI:

```bash
python -m tools.ui.app
```

Dann im ROS2-Panel Namespace `uav_1` setzen und Bridge starten.

Worauf achten:

- `rclpy.init()` nicht direkt mehrfach aufrufen. Im Code `acquire_ros()` und `release_ros()` verwenden.
- Namespace muss zu PX4 passen.
- `px4_msgs` muss in derselben Shell gesourced sein.
- Offboard-Steuerung erfordert stabile Setpoint-Publikation.
- Frames immer bewusst konvertieren: NED/ENU, FRD/FLU.

## 15. Frame Conventions

Merke:

- NED: North, East, Down
- ENU: East, North, Up
- FRD: Forward, Right, Down
- FLU: Forward, Left, Up

Konvertierungen liegen in:

- `skymeshx/ros/px4_bridge.py`
- `ned_to_enu()`
- `enu_to_ned()`
- `frd_to_flu()`

Worauf achten:

- Hoehe ist der haeufigste Fehler: Down positiv in NED, Up positiv in ENU/APF.
- Beschleunigungen, Attitude und Gimbal-Winkel koennen andere Achsrichtungen haben.
- Dokumentiere im eigenen Code immer, in welchem Frame eine Variable ist.

## 16. Raspberry Pi Server

Der Pi-Server ist fuer kleine Hardware optimiert, besonders Raspberry Pi 1.

Er kann:

- MAVLink verbinden
- Telemetrie lesen
- REST API auf Port 8080 anbieten
- Web Dashboard liefern
- Kommandos senden: ARM, DISARM, TAKEOFF, LAND, RTL, GOTO, MODE
- Log-Ringbuffer anzeigen

Start:

```bash
python3 pi/server.py --port /dev/ttyUSB0 --baud 57600
```

SITL:

```bash
python3 pi/server.py --port tcp:127.0.0.1:5762
```

Demo:

```bash
python3 pi/server.py --demo
```

Remote sicher betreiben:

```bash
python3 pi/server.py --host 0.0.0.0 --api-token <token>
```

Worauf achten:

- Standardmaessig lokal binden, wenn kein Remote-Zugriff noetig ist.
- Remote-Zugriff braucht Token, Firewall und idealerweise TLS/Reverse Proxy.
- CORS nur aktivieren, wenn du genau weisst, welche Web-Origin zugreifen darf.
- Der Pi-Server soll leicht bleiben: keine Qt UI, kein ROS2 auf Pi 1.

## 17. Experiment Panel

Das Experiment Panel kann Python-Skripte oder JSON-Szenarien starten.

Geeignet fuer:

- reproduzierbare Tests
- Forschungsablaeufe
- Missionssequenzen
- Demo-Szenarien

Worauf achten:

- Skripte sind Codeausfuehrung. Nur vertrauenswuerdige Dateien starten.
- Pfade muessen innerhalb erlaubter Projektbereiche liegen.
- Experimente sollten klare Abbruchbedingungen haben.
- Bei realen Drohnen immer Failsafe und manuelle Uebernahme einplanen.

## 18. Logs, Flight Logs und Bag Playback

### Log Panel

Zeigt Runtime-Ereignisse, Fehler und Statusmeldungen.

Worauf achten:

- Bei Upload- oder Steuerungsfehlern zuerst hier nachsehen.
- Queue-Full-Situationen koennen bedeuten, dass zu viele Events erzeugt werden.

### FlightLog Panel

CSV-Logs werden analysiert, typischerweise mit Spalten:

- `timestamp`
- `alt_rel`
- `groundspeed`
- `battery_pct`
- `vz`

Die UI kann Charts und Statistiken anzeigen.

### ROS2 Bag Playback

Bag Playback ist fuer reproduzierbare ROS2-Auswertung.

Worauf achten:

- `/clock` kann das Zeitverhalten im ROS-Graph beeinflussen.
- Playback-Rate und Looping koennen Algorithmen anders belasten als Live-Betrieb.
- Komprimierte Bags sparen Speicher, kosten aber CPU.

## 19. Sensorik, Perception und Mapping

Die Software enthaelt Integrationspunkte fuer:

- Thermal Camera
- Hotspot Detection
- ESCAPE Framework Integration
- Distributed Mapping
- ROS2 Sensordaten

Worauf achten:

- Sensor-Topics muessen existieren und korrekt gesourced sein.
- Kalibrierungen sind nicht optional, wenn du echte Messwerte interpretierst.
- Perception-Ergebnisse duerfen nicht ungeprueft als Flugkommandos verwendet werden.

## 20. Gimbal und Observation UAV

Gimbal-Funktionen werden fuer Inspektion, Kameraausrichtung und Beobachtung genutzt.

Typische Parameter:

- Pitch
- Roll
- Yaw
- Trigger-Distanz
- Kamera-FOV

Worauf achten:

- Gimbal-Kommandos muessen vom Autopilot und Mount unterstuetzt werden.
- Winkelbereiche variieren je nach Hardware.
- Teste Kamera-Trigger und Mount-Control am Boden.

## 21. LLM- und Natural-Language-Steuerung

Beispiele wie `examples/llm_swarm_control.py` erlauben natuerlichsprachliche Steuerung, besonders im Mock- oder Forschungsmodus.

Startbeispiel:

```bash
python examples/llm_swarm_control.py --backend mock --interactive
```

Worauf achten:

- LLM-Ausgaben muessen validiert werden, bevor sie reale Flugkommandos werden.
- Keine sicherheitskritischen Befehle ohne explizite Freigabe ausfuehren.
- Cloud-LLM-Nutzung kann Positions-, Missions- oder Betriebsdaten extern verarbeiten.

## 22. Installer, Updater und Builds

Installer-Build:

```powershell
tools/installer/build.ps1 -Target all
```

Oder gezielt:

```powershell
tools/installer/build.ps1 -Target gcs
tools/installer/build.ps1 -Target cli
```

Worauf achten:

- Build-Skripte koennen Dateien erzeugen oder externe Tools erwarten.
- Updater muessen Signaturen/Hashes pruefen, bevor Artefakte ausgefuehrt werden.
- Secrets, Lizenzschluessel und Tokens duerfen nicht im Repo landen.

## 23. Security-Baseline im Betrieb

Empfohlene Defaults:

- Pi/API lokal binden: `127.0.0.1`
- API Token verwenden
- Body-Limits aktiv lassen
- CORS deaktiviert lassen, wenn nicht benoetigt
- Keine Shell-/Script-Ausfuehrung aus untrusted Pfaden
- Logs nicht mit Secrets fuellen
- UI-Dateipfade validieren

REST API mit Token:

```bash
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8080/api/telemetry
```

Worauf achten:

- Remote-Kommandos sind Flugsteuerung. Behandle sie wie sicherheitskritische Admin-Aktionen.
- Ein offenes `0.0.0.0` ohne Token ist nicht akzeptabel.
- Browser-Dashboards brauchen Schutz gegen XSS und unsichere CORS-Regeln.

## 24. Entwicklung und Tests

Die Tests sind hardwarefrei. MAVLink, ROS2 und SITL werden gemockt.

Volle Suite:

```bash
pytest tests/
```

Ohne slow marker:

```bash
pytest tests/ -k "not slow"
```

Einzelne Module:

```bash
pytest tests/test_apf.py -v
pytest tests/test_battery_monitor.py -v
pytest tests/test_collision_prediction.py -v
pytest tests/test_solar_inspection.py -v
```

Worauf achten:

- Nutze `FakeConnection`, `FakeTelemetry` und `FakeMav` statt echter Hardware in Tests.
- Optional Dependencies wie ROS2 und PyQt muessen lazy bleiben.
- Pi-Code soll stdlib-arm bleiben, ausser `pymavlink` und `pyserial`.

## 25. Troubleshooting Schnellhilfe

Keine Verbindung:

- Port pruefen: meistens `tcp:127.0.0.1:5762`.
- SITL/Autopilot laeuft?
- Firewall oder falsches Protokoll?
- Serial-Baudrate korrekt?

Keine ROS2-Telemetrie:

- `MicroXRCEAgent` laeuft?
- `px4_msgs` gesourced?
- Namespace korrekt?
- PX4 sendet uXRCE-DDS?

Mission startet nicht:

- Flugmodus korrekt?
- GPS fix vorhanden?
- Wegpunkte gueltig?
- Upload erfolgreich?
- Autopilot akzeptiert Missionstyp?

Drohnen kommen zu nah:

- Formation spacing erhoehen.
- APF aktivieren.
- Kollisionsvorhersage aktivieren.
- Update-Rate und Geschwindigkeit reduzieren.

Seeding Mission zu gross:

- Seed spacing erhoehen.
- Feld in mehrere Missionen teilen.
- Wegpunktlimit beachten.

Solar Hotspots fehlen:

- Thermal Topic pruefen.
- Kalibrierung pruefen.
- Threshold senken.
- `min_hotspot_size` anpassen.

Pi Server unsicher erreichbar:

- Auf `127.0.0.1` binden oder Token erzwingen.
- Firewall setzen.
- CORS deaktivieren.

## 26. Empfohlener Arbeitsablauf fuer neue Features

1. Feature mit Tests oder Demo-Modus pruefen.
2. In SITL testen.
3. UI-Workflow mit Logs pruefen.
4. Security- und Safety-Checks durchgehen.
5. Mit echter Hardware am Boden testen.
6. Erst dann mit niedriger Hoehe und kleinem Missionsradius fliegen.

## 27. Weiterfuehrende Dokumente

- [Complete Feature Description](features/complete-feature-description.md)
- [UI Documentation](ui/ui-documentation.md)
- [Installation](setup/installation.md)
- [PX4 SITL](setup/px4-sitl.md)
- [Frame Conventions](setup/frame-conventions.md)
- [Raspberry Pi](setup/raspberry-pi.md)
- [Swarm Coordination](features/swarm-coordination.md)
- [Field Coverage Planning](features/field-coverage-planning.md)
- [Seeding Mission Planner](features/seeding-mission-planner.md)
- [Solar Inspection](features/solar-inspection.md)
- [Collision Prediction](features/collision-prediction.md)
- [Battery Monitoring](features/battery-monitoring.md)
- [Security Baseline](security/SECURITY_BASELINE.md)
- [Security Remediation Plan](security/SECURITY_REMEDIATION_PLAN.md)
