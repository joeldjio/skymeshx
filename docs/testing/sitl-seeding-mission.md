# SITL Checklist — Seeding Mission
**Szenario:** `gz_x500` single vehicle, Seeding Wizard vollständig gegen SITL

## Voraussetzungen
- SITL läuft: `gz_x500`, World: `empty_default`, NS: `px4_1`
- ROS2 Bridge verbunden
- MAVLink auf `tcp:127.0.0.1:5762`
- GPS fix ≥ 3D

## Schritt-für-Schritt

| # | Aktion | Expected Output |
|---|--------|----------------|
| 1 | MapView → Boundary Draw Mode aktivieren | Grüner Banner: FIELD BOUNDARY |
| 2 | 4 Eckpunkte auf Karte klicken (ca. 100m × 100m) | Polygon auf Karte |
| 3 | Seeding Panel → Preview | Drop-Points + Flight-Rows auf Karte sichtbar |
| 4 | Seeding Panel → Upload Mission | `mission_upload started` im Log |
| 5 | ROS2Panel → ARM + TAKEOFF 15m | Armed + Altitude ~15m |
| 6 | Seeding Panel / Mission Panel → Start | Mission starts, WP-Counter erhöht sich |
| 7 | Beobachten: Drone fliegt Reihen ab | uORB Snapshot: Armed, Altitude ~15m |
| 8 | Seeding Panel → Pause | Mission paused (LOITER) |
| 9 | Seeding Panel → Resume | Mission fortsetzt |
| 10 | Mission abgeschlossen → RTL / Land | Armed: DISARMED |

## Trace Bundle prüfen
```
mission_trace.jsonl →
  {type: "mission_upload", status: "started"}
  {type: "mission_upload", status: "finished", success: true}
  {type: "mission_log"} × N
```

## Pass / Fail
- [ ] Boundary gezeichnet und Preview gerendert
- [ ] Mission Upload erfolgreich (keine Timeout-Fehler)
- [ ] Drone startet und fliegt Reihen
- [ ] Pause/Resume funktioniert ohne Mission-Abbruch
- [ ] Mission completed Log-Eintrag erscheint
