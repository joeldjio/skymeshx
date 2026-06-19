# Formation Preview Feature

## Übersicht

Die Formation Preview zeigt eine 2D-Visualisierung der Schwarm-Formation **vor dem Start**, sodass Benutzer die Drohnen-Anordnung überprüfen können.

## Funktionen

### Visualisierung
- **Leader-Drohne**: Grüner Kreis in der Mitte (0,0)
- **Follower-Drohnen**: Blaue Kreise an berechneten Positionen
- **Koordinatensystem**: NED (North-East-Down), z-Achse nach oben
- **Kompass**: Zeigt Norden (N) an
- **Maßstab**: Dynamische Skalierung mit Distanzanzeige
- **Gitter**: Hilfslinien für bessere Orientierung

### Unterstützte Formationen
1. **Line** - Lineare Anordnung
2. **V-Shape** - V-Formation
3. **Circle** - Kreisformation
4. **Grid** - Gitteranordnung
5. **Diamond** - Rautenformation
6. **Letter R** - Buchstabe R
7. **Letter Z** - Buchstabe Z

### Parameter
- **Formation Type**: Dropdown zur Auswahl der Formation
- **Formation Size**: Anzahl der Drohnen (0 = alle)
- **Follow Distance**: Abstand zwischen Drohnen in Metern

## Technische Details

### Backend-Integration
Die Preview nutzt die `getFormationOffsets()` Methode aus `SwarmContext`:

```python
def getFormationOffsets(self, shape: str, count: int, spacing: float) -> list:
    """
    Get formation offsets for preview.
    Returns list of dicts: [{"north": float, "east": float}, ...]
    """
    from skymeshx.sdk.formations import formation_offsets
    
    if count <= 0:
        count = len(self._drones)
    
    offsets = formation_offsets(shape, count, spacing)
    return [{"north": n, "east": e} for n, e in offsets]
```

### QML-Komponente
Die `FormationPreview.qml` Komponente verwendet:
- **Canvas API** für 2D-Rendering
- **JavaScript** für Geometrie-Berechnungen
- **Property Bindings** für reaktive Updates

### Koordinatensystem
- **NED-Koordinaten**: North (x), East (y), Down (z)
- **Canvas-Mapping**: North → oben, East → rechts
- **Auto-Scaling**: Passt Zoom automatisch an alle Drohnen an

## Verwendung

### Im SwarmPanel
1. Navigiere zum **Swarm Panel**
2. Scrolle zum Abschnitt **FORMATION PREVIEW**
3. Wähle Formation Type, Size und Spacing
4. Die Preview aktualisiert sich automatisch

### Echtzeit-Updates
Die Preview reagiert auf Änderungen von:
- `swarm.formationType` → Formationstyp
- `swarm.formationSize` → Anzahl Drohnen
- `swarm.followDistance` → Abstand

## Implementierung

### Dateien
- `tools/ui/qml/components/FormationPreview.qml` - QML-Komponente (378 Zeilen)
- `tools/ui/qml/panels/SwarmPanel.qml` - Integration (Zeilen 943-997)
- `tools/ui/context/swarm_context.py` - Backend-Methode (Zeilen 1605-1623)

### Integration in SwarmPanel
```qml
FormationPreview {
    id: formationPreview
    width: parent.width
    height: 300
    
    formationType: {
        if (!swarm) return "line"
        const types = ["line", "v", "circle", "grid", "diamond", "letter_r", "letter_z"]
        return types[swarm.formationType] || "line"
    }
    droneCount: swarm ? swarm.formationSize : 0
    spacing: swarm ? swarm.followDistance : 8
}
```

## Beispiele

### Line Formation (5 Drohnen, 10m Abstand)
```
    N
    ↑
    
    ●  ← Follower 4 (40m Nord)
    ●  ← Follower 3 (30m Nord)
    ●  ← Follower 2 (20m Nord)
    ●  ← Follower 1 (10m Nord)
    ●  ← Leader (0,0)
```

### V-Shape Formation (5 Drohnen, 10m Abstand)
```
    N
    ↑
    
    ●           ●  ← Follower 3,4 (20m Nord, ±10m Ost)
      ●       ●    ← Follower 1,2 (10m Nord, ±5m Ost)
        ●          ← Leader (0,0)
```

### Circle Formation (8 Drohnen, 15m Radius)
```
    N
    ↑
    
        ●
    ●       ●
    
    ●   ●   ●
    
    ●       ●
        ●
```

## Vorteile

1. **Fehlerprävention**: Überprüfung vor dem Start verhindert Kollisionen
2. **Visualisierung**: Intuitive 2D-Darstellung der Formation
3. **Echtzeit**: Sofortige Updates bei Parameteränderungen
4. **Skalierung**: Automatische Anpassung an Drohnenanzahl
5. **Orientierung**: Kompass und Gitter für bessere Übersicht

## Zukünftige Erweiterungen

- [ ] 3D-Visualisierung mit Höhenunterschieden
- [ ] Drag-and-Drop für manuelle Positionierung
- [ ] Export der Formation als Waypoint-Mission
- [ ] Kollisionserkennung mit Hindernissen
- [ ] Animation der Formation während des Flugs
- [ ] Mehrere Leader-Drohnen (Multi-Cluster)

## Siehe auch

- [Formations API](../../skymeshx/sdk/formations.py)
- [Swarm Context](../../tools/ui/context/swarm_context.py)
- [UI Documentation](./ui-documentation.md)