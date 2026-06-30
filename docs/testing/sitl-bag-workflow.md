# SITL Checklist — ROS2 Bag Workflow
**Szenario:** `gz_x500`, Mission aufnehmen + im FlightLog abspielen

## Voraussetzungen
- SITL läuft und ROS2 Bridge verbunden
- `ros2 bag record` verfügbar (ROS2 Humble)
- `bags/` Verzeichnis schreibbar

## Schritt-für-Schritt

| # | Aktion | Expected Output |
|---|--------|----------------|
| 1 | ROS2Panel → Bag Recording → Topics auswählen (min: odometry + status) | Topics gecheckt |
| 2 | ▶ Start Recording | `[BAG] ✓ Recording started (2 topics)` |
| 3 | Drone armen + kurze Mission (30s) | Recording läuft: Dauer + Size steigen |
| 4 | ■ Stop Recording | `[BAG] ✓ Recording stopped`, Bag-Pfad angezeigt |
| 5 | FlightLog Panel → Bag laden (Pfad aus Schritt 4) | Bag-Inhalt sichtbar |
| 6 | Playback starten | Topics werden wiedergegeben |

## Preset-Test
| Preset | Topics | Einsatz |
|--------|--------|---------|
| minimal_mission | vehicle_status, global_pos, local_pos, odometry, attitude, control_mode, mission_result | Standard |
| full_px4_out | /px4_N/fmu/out/* | Diagnose |
| camera_gimbal | gimbal_device_attitude_status + camera/image_raw | Kamera-Test |
| swarm_multi_vehicle | vehicle_status + odometry aller Namespaces | Swarm |

## Trace Bundle prüfen
```
trace_runs/<ts>/
  ros2_bag/   → Bag-Verzeichnis vorhanden und nicht leer
  manifest.json → "bagPath": "bags/..."
```

## Pass / Fail
- [ ] Bag Recording startet ohne Fehler
- [ ] Bag-Größe wächst während Aufnahme
- [ ] Stop Recording gibt korrekten Pfad zurück
- [ ] Bag kann im FlightLog Panel geladen werden
- [ ] Trace Bundle enthält `ros2_bag/` Referenz im Manifest
