# SITL Checklist — ROS2 Bridge + Topic Browser
**Szenario:** `gz_x500_gimbal`, NS: `px4_1`, ROS2 Humble

## Voraussetzungen
- MicroXRCEAgent läuft: `MicroXRCEAgent udp4 -p 8888`
- SITL gestartet und Bridge verbunden
- ROS2 Humble + px4_msgs installiert

## Schritt-für-Schritt

| # | Aktion | Expected Output |
|---|--------|----------------|
| 1 | ROS2Panel → Connect to PX4 → NS: `px4_1` | Bridge Started |
| 2 | Live uORB Snapshot: alle Felder füllen sich | Armed, GPS, Alt sichtbar |
| 3 | Topic Browser → Discover Topics | Liste von `/px4_1/fmu/out/*` Topics |
| 4 | Filter: `/fmu/out` → gefilterte Liste | Nur `/px4_1/fmu/out/…` sichtbar |
| 5 | Topic anklicken: `/px4_1/fmu/out/vehicle_status` | Subscribe-Log erscheint |
| 6 | Mindest-Topic-Set prüfen (alle vorhanden?): | Alle 9 Pflicht-Topics vorhanden |
| 7 | Bridge Disconnect → Stop Bridge | `🔴 Stopped` Log-Eintrag |
| 8 | Bridge erneut starten | Reconnect klappt |

## Mindest-Topic-Set (alle müssen vorhanden sein)
```
/px4_1/fmu/out/vehicle_status
/px4_1/fmu/out/vehicle_global_position
/px4_1/fmu/out/vehicle_local_position
/px4_1/fmu/out/vehicle_odometry
/px4_1/fmu/out/vehicle_attitude
/px4_1/fmu/out/vehicle_control_mode
/px4_1/fmu/out/battery_status
/px4_1/fmu/out/failsafe_flags
/px4_1/fmu/out/mission_result
```

## Trace Bundle prüfen
```
ui_events.jsonl → bridge_status: {active: true}, {active: false}
ros2_topic_health.json → Topic-Raten nach Session-Stop
```

## Pass / Fail
- [ ] Bridge verbindet sich < 5s nach SITL-Start
- [ ] Alle 9 Pflicht-Topics im Browser sichtbar
- [ ] Filter funktioniert korrekt
- [ ] Disconnect/Reconnect funktioniert
- [ ] `ros2_topic_health.json` enthält Hz-Daten nach Session-Stop
