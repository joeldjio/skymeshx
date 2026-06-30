# SITL Checklist — Multi-Vehicle (3x SITL)
**Szenario:** 3× `gz_x500`, NS: `px4_1/px4_2/px4_3`, Ports: 5762/5763/5764

## Voraussetzungen
- PX4 Multi-Vehicle Bash-Skript oder manuell starten
- 3× MicroXRCEAgent auf Ports 8888/8889/8890
- ROS2 Humble + px4_msgs installiert

## Starten (Referenz)
```bash
PX4_UXRCE_DDS_NS=px4_1 make px4_sitl gz_x500 &
PX4_UXRCE_DDS_NS=px4_2 make px4_sitl gz_x500 &
PX4_UXRCE_DDS_NS=px4_3 make px4_sitl gz_x500 &
```

## Alternativ: GCS Multi-Vehicle SITL
ROS2Panel → Multi-Vehicle SITL → Count: 3, Base Port: 5762 → ▶ Start All

## Schritt-für-Schritt

| # | Aktion | Expected Output |
|---|--------|----------------|
| 1 | Alle 3 SITL-Instanzen starten | 3× Drone in Gazebo sichtbar |
| 2 | Drone 1 (px4_1) auswählen → Connect Bridge | Bridge für px4_1 verbunden |
| 3 | Drone 2 (px4_2) auswählen → Connect Bridge | Bridge für px4_2 verbunden |
| 4 | Drone 3 (px4_3) auswählen → Connect Bridge | Bridge für px4_3 verbunden |
| 5 | MapView: 3 Drone-Marker sichtbar? | 3× Marker auf Karte |
| 6 | Alle 3 armen | Alle ARMED |
| 7 | Alle 3 takeoff 10m | Alle ~10m Höhe |
| 8 | Formation: Leader=px4_1, Shape=v | Formation V-Shape |
| 9 | Alle RTL → Land → Disarm | Alle sicher gelandet |
| 10 | Alle SITL stoppen | GCS zeigt 0 Dronen |

## Multi-Vehicle Port-Tabelle
| Drone | MAVLink | uXRCE-DDS | Video |
|-------|---------|-----------|-------|
| px4_1 | 5762 | 8888 | 5600 |
| px4_2 | 5763 | 8889 | 5601 |
| px4_3 | 5764 | 8890 | 5602 |

## Pass / Fail
- [ ] Alle 3 Instanzen starten ohne Konflikte
- [ ] Alle 3 Bridges verbinden sich
- [ ] Alle 3 Dronen auf Karte sichtbar
- [ ] Formation Control startet mit 3 Vehicles
- [ ] Kein Namespace-Konflikt zwischen px4_1/2/3
