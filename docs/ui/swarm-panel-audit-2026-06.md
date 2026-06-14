# SwarmPanel Deep Audit & Improvement Plan
**Date:** 2026-06-14  
**Status:** Analysis Complete - Implementation Pending

## Executive Summary

Das SwarmPanel bietet umfangreiche Swarm-Koordinations-Features, hat aber mehrere UX- und Implementierungsprobleme:

1. **Fehlende Feature-Beschreibungen** - User versteht nicht, was Features tun
2. **Unklare UX-Flows** - Workflow für Role/Formation/Leader-Selection unklar
3. **Nicht-funktionierende Features** - Map-Click, Leader-Dropdown
4. **Fehlende Algorithmus-Kompatibilitäts-Dokumentation**
5. **Keine Mutual Exclusion** - Inkompatible Algorithmen können gleichzeitig aktiv sein
6. **QML-Warnung** - Deprecated parameter injection in signal handler

## Feature-Übersicht

### 1. **Drone Selection & Management**
- **Was es tut:** Auswahl und Verwaltung einzelner Drohnen
- **Status:** ✅ Funktioniert
- **Features:**
  - Drone-Auswahl via ComboBox
  - Mission-Target-Checkbox (Multi-Drone-Missionen)
  - Connect/Disconnect/Remove Buttons
  - System Info (Autopilot, Firmware, Status)

### 2. **Manual Control (GOTO)**
- **Was es tut:** Manuelle Steuerung einzelner oder mehrerer Drohnen zu GPS-Koordinaten
- **Status:** ⚠️ Teilweise funktionierend
- **Probleme:**
  - "Map" Button funktioniert nicht (Line 938: `root.mainWindow.startMapPick()` nicht implementiert)
  - Keine Beschreibung, was "smartGoto" vs "goto" macht
- **Verbesserungen:**
  - Map-Click-Feature entfernen oder implementieren
  - Tooltip: "GOTO: Fliegt direkt zu Koordinaten (nur wenn armed). Smart GOTO: Arm + Takeoff + Goto automatisch"

### 3. **Mission Waypoints**
- **Was es tut:** Waypoint-basierte Missionen für einzelne oder mehrere Drohnen
- **Status:** ✅ Funktioniert
- **Features:**
  - Waypoint-Liste mit Reorder/Delete
  - Multi-Drone-Mission-Support
  - Integration mit MissionPanel

### 4. **Swarm Role & Formation**
- **Was es tut:** Manuelle Zuweisung von Rollen (Leader/Follower/Coordinator) und Formation-Offsets
- **Status:** ⚠️ UX unklar
- **Probleme:**
  - User versteht nicht: "Ist die ausgewählte Drone der Leader, wenn ich Leader setze?"
  - "Follow" Rolle: Muss ich noch Leader-ID angeben? Warum?
  - Offset-Felder: Wann brauche ich die? Was passiert, wenn ich sie setze?
- **Antworten:**
  - Ja, die ausgewählte Drone wird zum Leader
  - Bei "Follow": Leader-ID ist optional - wenn leer, wird automatisch der erste Leader verwendet
  - Offsets: Nur für manuelle Formation-Anpassung, normalerweise nicht nötig (automatisch via Formation Type)

### 5. **Swarm AI Algorithms**

#### 5.1 Update Rate
- **Was es tut:** Steuert, wie oft Algorithmen aktualisiert werden (50-1000ms)
- **Status:** ✅ Funktioniert
- **Beschreibung:** Höhere Rate = präzisere Kontrolle, aber mehr CPU-Last

#### 5.2 Boids (Reynolds Flocking)
- **Was es tut:** Emergentes Schwarmverhalten basierend auf 3 Regeln
- **Status:** ✅ Funktioniert
- **Beschreibung:**
  - **Separation:** Abstand zu Nachbarn halten (verhindert Kollisionen)
  - **Alignment:** Gleiche Richtung wie Nachbarn fliegen
  - **Cohesion:** Zum Schwarm-Zentrum bewegen
  - **Perception Radius:** Wie weit Drohnen "sehen" können (50m default)
- **Kompatibilität:** ⚠️ Kann mit Leader-Follower kollidieren (beide steuern Position)

#### 5.3 Leader-Follower Formation
- **Was es tut:** Follower-Drohnen folgen einem Leader in fester Formation
- **Status:** ⚠️ Teilweise funktionierend
- **Probleme:**
  - Leader-Dropdown funktioniert nicht (Line 1339: `onActivated` setzt nur `leaderDroneId`, aber ComboBox aktualisiert nicht)
  - Formation Preview zeigt immer aktuelle Drone-Anzahl, nicht Mindestanzahl
- **Beschreibung:**
  - **Leader Drone:** Die Drohne, der alle folgen
  - **Follow Distance:** Abstand zwischen Formation-Slots (8m default)
  - **Formation Type:** Line, V-Shape, Circle, Grid
  - **Formation Size:** 0 = alle Drohnen, sonst nur N Follower
- **Kompatibilität:** ⚠️ Inkompatibel mit Boids (beide steuern Position)

#### 5.4 Distributed Consensus
- **Was es tut:** Demokratische Entscheidungsfindung im Schwarm
- **Status:** 🔴 Nur Simulation (kein echtes Consensus-Protokoll)
- **Beschreibung:**
  - **Algorithm:** Basic/Byzantine/Distributed
  - **Byzantine Tolerance:** Wie viele fehlerhafte Drohnen toleriert werden
  - **START VOTE:** Startet Abstimmung (simuliert 2s Delay)
- **Kompatibilität:** ✅ Kompatibel mit allen (nur Entscheidungsfindung, keine Bewegung)

#### 5.5 Behavior Trees (Autonomous Missions)
- **Was es tut:** Autonome Mission-Ausführung mit Prioritäten
- **Status:** 🔴 Nur Simulation (keine echten Behavior Trees)
- **Beschreibung:**
  - **Mission Type:** Surveillance, Search & Rescue, Formation Flight, Area Coverage
  - **Priority Mode:** Safety First, Mission First, Balanced
  - **EXECUTE MISSION:** Startet Mission (simuliert 4 Schritte: Planning, Takeoff, Execution, Landing)
- **Kompatibilität:** ⚠️ Sollte andere Algorithmen überschreiben (höchste Priorität)

### 6. **Global Controls**
- **START ALGORITHMS:** Startet alle aktivierten Algorithmen
- **STOP:** Stoppt alle Algorithmen
- **RESET:** Stoppt und setzt alle Algorithmen zurück

## Kritische Probleme

### Problem 1: Map-Click funktioniert nicht
**Location:** Line 938  
**Code:** `root.mainWindow.startMapPick(root)`  
**Issue:** `mainWindow` ist nicht definiert, `startMapPick()` existiert nicht  
**Solution:** Feature entfernen oder implementieren

### Problem 2: Leader-Dropdown aktualisiert nicht
**Location:** Line 1339  
**Code:** `onActivated: if (swarm) swarm.leaderDroneId = currentText`  
**Issue:** ComboBox zeigt nicht den aktuellen Leader  
**Solution:** Binding hinzufügen:
```qml
Component.onCompleted: {
    if (swarm && swarm.leaderDroneId) {
        currentIndex = model.indexOf(swarm.leaderDroneId)
    }
}
Connections {
    target: swarm
    function onCountsChanged() {
        if (swarm && swarm.leaderDroneId) {
            leaderCombo.currentIndex = leaderCombo.model.indexOf(swarm.leaderDroneId)
        }
    }
}
```

### Problem 3: Formation Preview zeigt falsche Drone-Anzahl
**Location:** Line 1415-1420  
**Issue:** Zeigt immer aktuelle Anzahl, nicht Mindestanzahl für Formation  
**Solution:** Ändern zu:
```qml
droneCount: {
    if (!swarm) return 2
    const mins = {"line": 2, "v": 2, "circle": 4, "grid": 4}
    const minRequired = mins[formationType] || 2
    return minRequired + 1  // +1 für Leader
}
```

### Problem 4: QML-Warnung (Parameter "index")
**Location:** Line 1532  
**Code:** `onActivated: if (swarm) swarm.missionPriority = index`  
**Issue:** Deprecated parameter injection  
**Solution:** Ändern zu:
```qml
onActivated: function(index) { if (swarm) swarm.missionPriority = index }
```

### Problem 5: Keine Algorithmus-Kompatibilitäts-Checks
**Issue:** Boids und Leader-Follower können gleichzeitig aktiv sein → Konflikt  
**Solution:** Mutual Exclusion implementieren:
```python
# In swarm_context.py
@boidsEnabled.setter
def boidsEnabled(self, value):
    if value and self._leader_follower_enabled:
        self.logMessage.emit("WARN", "[SWARM] Disabling Leader-Follower (incompatible with Boids)")
        self._leader_follower_enabled = False
    self._boids_enabled = value
    self.countsChanged.emit()

@leaderFollowerEnabled.setter
def leaderFollowerEnabled(self, value):
    if value and self._boids_enabled:
        self.logMessage.emit("WARN", "[SWARM] Disabling Boids (incompatible with Leader-Follower)")
        self._boids_enabled = False
    # ... rest of setter
```

### Problem 6: Fehlende Feature-Beschreibungen
**Issue:** User versteht nicht, was Features tun  
**Solution:** Tooltips und Beschreibungen hinzufügen (siehe unten)

## Algorithmus-Kompatibilitäts-Matrix

| Algorithm | Boids | Leader-Follower | Consensus | Behavior Trees |
|-----------|-------|-----------------|-----------|----------------|
| **Boids** | - | ❌ Inkompatibel | ✅ Kompatibel | ⚠️ BT überschreibt |
| **Leader-Follower** | ❌ Inkompatibel | - | ✅ Kompatibel | ⚠️ BT überschreibt |
| **Consensus** | ✅ Kompatibel | ✅ Kompatibel | - | ✅ Kompatibel |
| **Behavior Trees** | ⚠️ BT überschreibt | ⚠️ BT überschreibt | ✅ Kompatibel | - |

**Legende:**
- ✅ Kompatibel: Können gleichzeitig laufen
- ❌ Inkompatibel: Mutual Exclusion erforderlich
- ⚠️ BT überschreibt: Behavior Trees haben höchste Priorität

## Integration mit Mission Panel

### Aktueller Status
- ✅ Waypoints werden zwischen SwarmPanel und MissionPanel geteilt
- ✅ Multi-Drone-Missionen funktionieren
- ✅ Mission-Target-Selection funktioniert

### Offene Fragen
1. **Kann ich einen Algorithmus starten und dann eine Mission im MissionPanel planen?**
   - Antwort: Ja, aber Algorithmen sollten gestoppt werden, wenn Mission startet
   - Problem: Keine automatische Deaktivierung

2. **Funktionieren Algorithmen während einer Mission?**
   - Antwort: Ja, aber das kann zu Konflikten führen
   - Problem: Mission-Waypoints vs. Algorithmus-Steuerung

### Empfohlenes Verhalten
```python
# In swarm_context.py - runMissionMulti()
def runMissionMulti(self, drone_ids_json, waypoints_json):
    # Stop swarm algorithms during mission
    if self._swarm_algorithms_active:
        self.logMessage.emit("INFO", "[SWARM] Stopping algorithms for mission")
        self.stopSwarmAlgorithms()
    # ... rest of method
```

## Implementierungsplan

### Phase 1: Kritische Fixes (4h)
1. ✅ Map-Click-Feature entfernen (30min)
2. ✅ Leader-Dropdown fixen (1h)
3. ✅ Formation Preview fixen (30min)
4. ✅ QML-Warnung beheben (15min)
5. ✅ Mutual Exclusion implementieren (1h)
6. ✅ Auto-Stop Algorithmen bei Mission-Start (45min)

### Phase 2: UX-Verbesserungen (6h)
1. ✅ Feature-Beschreibungen hinzufügen (2h)
2. ✅ Tooltips für alle Controls (2h)
3. ✅ Algorithmus-Kompatibilitäts-Warnung in UI (1h)
4. ✅ Workflow-Dokumentation (1h)

### Phase 3: Dokumentation (2h)
1. ✅ User Guide für SwarmPanel erstellen
2. ✅ Algorithmus-Kompatibilitäts-Tabelle
3. ✅ Best Practices

## Vorgeschlagene Feature-Beschreibungen (für UI)

### Boids Section
```
ℹ️ BOIDS (REYNOLDS FLOCKING)
Emergentes Schwarmverhalten basierend auf 3 Regeln:
• Separation: Abstand zu Nachbarn halten
• Alignment: Gleiche Richtung wie Nachbarn
• Cohesion: Zum Schwarm-Zentrum bewegen

⚠️ Inkompatibel mit Leader-Follower Formation
```

### Leader-Follower Section
```
ℹ️ LEADER-FOLLOWER FORMATION
Follower-Drohnen folgen einem Leader in fester Formation.
• Leader Drone: Die Drohne, der alle folgen
• Follow Distance: Abstand zwischen Slots (8m empfohlen)
• Formation Type: Line, V-Shape, Circle, Grid
• Formation Size: 0 = alle Drohnen verwenden

⚠️ Inkompatibel mit Boids Algorithm
```

### Consensus Section
```
ℹ️ DISTRIBUTED CONSENSUS
Demokratische Entscheidungsfindung im Schwarm.
• Algorithm: Consensus-Protokoll (Basic/Byzantine/Distributed)
• Byzantine Tolerance: Anzahl fehlerhafter Drohnen, die toleriert werden
• START VOTE: Startet Abstimmung über Ziel/Aktion

✅ Kompatibel mit allen anderen Algorithmen
```

### Behavior Trees Section
```
ℹ️ BEHAVIOR TREES (AUTONOMOUS MISSIONS)
Autonome Mission-Ausführung mit Prioritäten.
• Mission Type: Art der Mission (Surveillance, Search & Rescue, etc.)
• Priority Mode: Safety First (sicher), Mission First (schnell), Balanced
• EXECUTE MISSION: Startet autonome Mission

⚠️ Überschreibt andere Algorithmen während Ausführung
```

## Nächste Schritte

1. **Sofort:** Kritische Fixes implementieren (Phase 1)
2. **Dann:** UX-Verbesserungen (Phase 2)
3. **Zuletzt:** Dokumentation (Phase 3)
4. **Review:** User-Testing mit verbessertem Panel

## Offene Fragen für User

1. Soll Map-Click-Feature implementiert oder entfernt werden?
2. Sollen Algorithmen automatisch stoppen, wenn Mission startet?
3. Soll Behavior Trees andere Algorithmen überschreiben oder parallel laufen?
4. Brauchen wir eine "Quick Start" Wizard für Swarm-Setup?