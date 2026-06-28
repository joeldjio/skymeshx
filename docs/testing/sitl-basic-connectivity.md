# SITL Checklist — Basic Connectivity
**Szenario:** `gz_x500` single vehicle, leere Welt, MAVLink + ROS2 Bridge

## Voraussetzungen
- PX4-Autopilot unter `~/PX4-Autopilot` gebaut
- ROS2 Humble installiert + `px4_msgs` gebaut
- MicroXRCEAgent verfügbar
- Namespace: `px4_1` (oder `uav_1`)
- Ports: MAVLink `tcp:127.0.0.1:5762`, uXRCE-DDS `udp:8888`

## Schritt-für-Schritt

| # | Aktion | Expected Output |
|---|--------|----------------|
| 1 | ROS2Panel → SITL Steuerung → Model: `gz_x500`, World: `empty_default` → Start SITL | SITL Status: ✓ Running, Gazebo: ✓ |
| 2 | ROS2Panel → PX4 Connection → NS: `px4_1` → Connect to PX4 | Bridge Started Log-Eintrag |
| 3 | LogPanel → Bridge-Status prüfen | `[px4_1] ROS2 Bridge 🟢 Started` |
| 4 | ROS2Panel → Live uORB Snapshot prüfen | `Armed: DISARMED`, GPS Fix: ≥ 3D |
| 5 | Vehicle Commands → ARM | Armed: ARMED |
| 6 | Vehicle Commands → TAKEOFF 5m | Alt (rel): ~5.0m |
| 7 | Vehicle Commands → RTL | Alt sinkt, zurück zu Home |
| 8 | Vehicle Commands → DISARM (nach Land) | Armed: DISARMED |
| 9 | ROS2Panel → Stop SITL | SITL Status: gestoppt |

## Trace Bundle prüfen
```
trace_runs/<ts>_sitl_basic/
  manifest.json   → px4.model = "gz_x500", vehicles[0].namespace = "px4_1"
  ui_events.jsonl → bridge_status, qml_action Einträge vorhanden
```

## Pass / Fail
- [ ] SITL startet und Gazebo öffnet sich
- [ ] Bridge verbindet sich (kein Timeout)
- [ ] ARM/DISARM funktioniert via uXRCE-DDS
- [ ] Telemetrie (GPS, Alt, Armed) sichtbar in Snapshot
- [ ] RTL führt Drone zurück und landet
