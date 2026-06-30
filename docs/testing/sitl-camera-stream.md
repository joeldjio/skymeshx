# SITL Checklist — Camera Stream (Video UDP)
**Szenario:** `gz_x500_mono_cam` oder `gz_x500_gimbal`, Video UDP Port 5600

## Voraussetzungen
- SITL mit Camera-Modell gestartet: `gz_x500_gimbal` oder `gz_x500_mono_cam`
- Gazebo Camera Plugin streamt auf UDP 5600
- SkyMeshX GCS geöffnet

## Schritt-für-Schritt

| # | Aktion | Expected Output |
|---|--------|----------------|
| 1 | ROS2Panel → Video Stream → URL: `udp://0.0.0.0:5600` | URL konfiguriert |
| 2 | Drone auswählen (px4_1), ▶ Start Probe | Status: "Waiting for stream …" |
| 3 | SITL: Kamera-Plugin läuft → kurz warten | Status wechselt zu "Stream receiving" |
| 4 | MapView prüfen: PIP-Overlay unten rechts erscheint | "📡  LIVE" Badge sichtbar, URL angezeigt |
| 5 | GimbalPanel prüfen | "LIVE"-Badge + grüner Rahmen, kein leeres Video-Rechteck |
| 6 | SITL stoppen → Stream abreißen | Status wechselt zu "stalled" → PIP-Overlay verschwindet |

## Wichtige R-10 Prüfung
**Kein leeres Video-Rechteck sichtbar, bevor Status = "receiving"!**

| Zustand | GimbalPanel | MapView PIP |
|---------|-------------|-------------|
| unconfigured | "📹 No Active Stream" | nicht sichtbar |
| waiting | "⏳ Waiting for stream …" + URL | nicht sichtbar |
| receiving | "LIVE"-Badge | 240×135 PIP sichtbar |
| stalled | "⚠ Stream stalled" | nicht sichtbar |
| error | "✕ Stream error" | nicht sichtbar |

## Trace Bundle prüfen
```
ui_events.jsonl → {type: "VIDEO_STATUS", status: "waiting"}, {type: "VIDEO_STATUS", status: "receiving"}
video/<droneId>_stream_probe.json → vorhanden
```

## Pass / Fail
- [ ] Stream Probe startet ohne Crash
- [ ] Status-Übergänge korrekt angezeigt
- [ ] R-10: KEIN leeres Video-Rechteck in irgendwelchem Zustand außer "receiving"
- [ ] PIP-Overlay erscheint genau wenn Status = "receiving"
- [ ] PIP-Overlay verschwindet wenn Stream abbricht
