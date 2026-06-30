# SITL Checklist — Solar Inspection Mission
**Szenario:** `gz_x500_gimbal`, World: `empty_default`, NS: `px4_1`

## Voraussetzungen
- SITL läuft: `gz_x500_gimbal`, Camera/Gimbal-Toggle aktiviert
- ROS2 Bridge verbunden
- GPS fix ≥ 3D
- GimbalPanel zeigt Drone-Auswahl

## Schritt-für-Schritt

| # | Aktion | Expected Output |
|---|--------|----------------|
| 1 | MapView → Solar Row Draw Mode aktivieren | Blauer Banner: SOLAR ROW |
| 2 | Start + End-Punkt für 5-6 Panel-Reihen klicken | Solar-Reihen auf Karte |
| 3 | Solar Inspection Panel → Preview | Trigger-Points + Footprints auf Karte |
| 4 | Solar Panel → Upload Mission | `mission_upload` im Trace |
| 5 | ARM + TAKEOFF 20m | Altitude ~20m |
| 6 | Solar Panel → Start | Mission startet |
| 7 | GimbalPanel beobachten: Gimbal-Status sichtbar? | Gimbal Panel: Angle-Daten |
| 8 | Mission abwarten (alle Rows) → RTL | Mission: finished |
| 9 | DISARM nach Land | Armed: DISARMED |

## Trace Bundle prüfen
```
ui_events.jsonl → {type: "camera_status"} oder {type: "gimbal_status"} Einträge
mission_trace.jsonl → mission_start, wp_tracking Einträge
```

## Pass / Fail
- [ ] Solar Rows gezeichnet + Preview korrekt
- [ ] Trigger Points sichtbar auf Karte
- [ ] Mission Upload ohne Fehler
- [ ] Drone fliegt Solar-Pattern ab
- [ ] Gimbal-Status im GimbalPanel erkennbar
