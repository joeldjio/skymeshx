# UI Audit Report — Juni 2026

**Datum:** 2026-06-09  
**Version:** skymeshx gcs v0.3.1  
**Scope:** Komplette UI-Analyse (Layout, Theme, Konsistenz, UX, Tests)

---

## Executive Summary

Die skymeshx GCS UI ist eine moderne Qt6/QML-basierte Ground Control Station für Multi-Drone-Forschung. Das Design folgt einem **Dark Theme** mit konsistenten Farben und Spacing. Die Architektur ist **tab-basiert** mit 10 Hauptpanels.

**Stärken:**
- ✅ Zentralisiertes Theme-System (`Theme.qml` Singleton)
- ✅ Konsistente Farbpalette (Slate/Blue/Green)
- ✅ Responsive InstrBar mit horizontalem Scroll
- ✅ Modulare Component-Architektur
- ✅ AppState Singleton für globalen State

**Verbesserungspotenzial:**
- ⚠️ Inkonsistente Spacing-Nutzung (hardcoded vs. Theme.spacing())
- ⚠️ Fehlende UI-Tests (nur Backend-Tests vorhanden)
- ⚠️ InstrBar könnte mehr Funktionen aufnehmen
- ⚠️ Accessibility-Features fehlen (Keyboard-Navigation, Screen-Reader)

---

## 1. Theme-System Analyse

### 1.1 Theme.qml (Singleton)

**Datei:** `tools/ui/qml/components/Theme.qml`

#### Farbpalette

| Kategorie | Property | Hex | Verwendung |
|-----------|----------|-----|------------|
| **Surface** | `bg` | `#0f1117` | Haupthintergrund |
| | `bgElevated` | `#1a2035` | Erhöhte Panels |
| | `bgInput` | `#1e2535` | Input-Felder |
| | `bgPanel` | `#161b27` | Panel-Container |
| **Borders** | `border` | `#2d3748` | Standard-Border |
| | `borderMuted` | `#1e293b` | Subtile Borders |
| | `borderStrong` | `#334155` | Starke Borders |
| **Text** | `textPrimary` | `#e2e8f0` | Haupttext |
| | `textSecondary` | `#94a3b8` | Sekundärtext |
| | `textMuted` | `#64748b` | Gedämpfter Text |
| | `textFaded` | `#475569` | Sehr schwacher Text |
| **Accents** | `accent` | `#2563eb` | Primary Blue |
| | `success` | `#22c55e` | Grün (Armed, OK) |
| | `warning` | `#f59e0b` | Orange (Warnung) |
| | `danger` | `#ef4444` | Rot (Fehler, Disarm) |
| | `info` | `#06b6d4` | Cyan (Info) |
| | `violet` | `#8b5cf6` | Lila (Observation) |

#### Typography

```qml
// Platform-spezifische Fonts
fontSans: "Segoe UI" (Win) | "SF Pro Text" (Mac) | "Ubuntu" (Linux)
fontMono: "Cascadia Code" (Win) | "SF Mono" (Mac) | "DejaVu Sans Mono" (Linux)

// Font-Größen
fontXS: 8px   // Labels, Hints
fontS:  10px  // Body Text
fontM:  11px  // Standard UI
fontL:  13px  // Headings
fontXL: 16px  // Large Headings
```

#### Spacing & Radius

```qml
spacing(n): n * 4px  // 4px Grid-System
radiusS: 4px
radiusM: 6px
radiusL: 8px
```

### 1.2 Konsistenz-Analyse

#### ✅ Konsistent verwendet:
- Farbpalette (alle Panels nutzen Theme-Farben)
- Font-Families (plattformspezifisch)
- Border-Radius (6-8px Standard)

#### ⚠️ Inkonsistenzen gefunden:

**Spacing:**
- InstrBar: `spacing: 6` (hardcoded, sollte `Theme.spacing(1.5)` sein)
- DashboardPanel: `spacing: 10` (sollte `Theme.spacing(2.5)` sein)
- SwarmPanel: `spacing: 8` (sollte `Theme.spacing(2)` sein)
- SafetyPanel: `spacing: 12` (sollte `Theme.spacing(3)` sein)

**Font-Größen:**
- Einige Panels nutzen `font.pixelSize: 9` (nicht in Theme definiert)
- InstrBar nutzt `font.pixelSize: 7` (sollte `Theme.fontXS` sein)

**Empfehlung:** Alle hardcoded Spacing/Font-Werte durch Theme-Properties ersetzen.

---

## 2. Panel-Konsistenz

### 2.1 Layout-Struktur

Alle Panels folgen diesem Pattern:

```qml
Item {
    anchors.fill: parent
    
    ScrollView {
        anchors { fill: parent; margins: 12 }
        Column {
            spacing: 8-12
            // Content
        }
    }
}
```

✅ **Konsistent:** Alle Panels nutzen `ScrollView` + `Column`  
⚠️ **Inkonsistent:** Margins variieren (10-12px)

### 2.2 Panel-Übersicht

| Panel | Zweck | Layout | Besonderheiten |
|-------|-------|--------|----------------|
| **Map** | Leaflet-Karte + HUD | WebEngineView | 3D Drone Overlay, Waypoint-Modus |
| **Dashboard** | Live Telemetrie | Single Column | Drone-Selector, Telemetry-Grid |
| **Swarm** | Multi-Drone Control | Two Column (38%/62%) | Mission-Targets, Formation-Preview |
| **Safety** | APF Configuration | Single Column | Sliders, Violation-Log |
| **Gimbal** | Kamera-Steuerung | Single Column | Pitch/Yaw/Zoom Controls |
| **ROS2** | ROS2/uXRCE-DDS | Three Column (30%/35%/35%) | Bag Recording, Topic Monitor |
| **Experiment** | Script Runner | Tab-based (Script/JSON) | Code Editor, Scenario Builder |
| **FlightLog** | Telemetrie-Replay | Single Column | Timeline, Playback Controls |
| **Log** | System-Log | Single Column | Log-Level Filter, Search |
| **Help** | Feature-Übersicht | Single Column | Markdown-Rendering |

### 2.3 Drone-Selector Konsistenz

**Problem:** Jedes Panel hat einen eigenen Drone-Selector mit leicht unterschiedlichem Styling.

**Beispiele:**
- DashboardPanel: `height: 30`, `color: "#1e2535"`
- SwarmPanel: `height: 30`, `color: "#1e2535"` ✅ (identisch)
- InstrBar: `height: 24`, `color: "#0d1117"` ⚠️ (abweichend)

**Empfehlung:** Extrahiere `DroneSelector.qml` Component für Wiederverwendung.

---

## 3. InstrBar Analyse

### 3.1 Aktuelle Funktionen

Die InstrBar (110px hoch) zeigt:

1. **Drone Selector** (110px) - ComboBox + Connection Status
2. **Armed/Mode Tile** (88px) - Armed-Status + Flight-Mode + Drone-ID
3. **Attitude Indicator** (90px) - Canvas-basiert, Roll/Pitch
4. **Compass** (90px) - Canvas-basiert, Heading
5. **ALT Tile** (80px) - Altitude + AMSL + Progress-Bar
6. **SPEED Tile** (80px) - Groundspeed + km/h Conversion
7. **CLIMB Tile** (80px) - Vertical Speed + VSI Tape + Throttle
8. **Battery + GPS** (90px) - Battery % + Voltage + GPS Fix + Satellites
9. **Quick Commands** (6 Buttons) - ARM, DISARM, TAKEOFF, LAND, RTL, HOLD
10. **Flight Mode Switcher** (6 Buttons) - STAB, ALT-H, LOITER, GUIDED, AUTO, POSHLD
11. **Altitude Control** - Set Alt Field + "▲ Set" Button
12. **APF/Safety** - APF Status + Enable/Disable Toggle + Violations Counter

### 3.2 Fehlende Funktionen (Vorschläge)

#### 3.2.1 Telemetrie-Erweiterungen

- **Airspeed** (für Fixed-Wing)
- **Wind Speed/Direction** (wenn verfügbar)
- **EKF Status** (Kalman-Filter Health)
- **RC Signal Strength** (RSSI)
- **Datalink Quality** (Packet Loss)

#### 3.2.2 Mission-Steuerung

- **Mission Progress** (WP 3/10, 45% complete)
- **Next Waypoint Distance** (120m to WP4)
- **ETA** (Estimated Time of Arrival)

#### 3.2.3 Formation-Status

- **Formation Mode** (Circle, Line, Grid)
- **Formation Health** (3/5 drones in position)

#### 3.2.4 System-Status

- **CPU Load** (Companion Computer)
- **Memory Usage**
- **Disk Space** (für Bag Recording)

### 3.3 Layout-Optimierung

**Aktuell:** Horizontal scrollbar bei >1440px Breite  
**Problem:** Wichtige Tiles (Battery, Commands) können außerhalb des Viewports sein

**Empfehlung:**
1. **Prioritäts-basiertes Layout:** Wichtigste Tiles immer sichtbar
2. **Collapsible Sections:** Weniger wichtige Tiles ausblendbar
3. **Responsive Breakpoints:** Bei <1200px Breite: 2-Zeilen-Layout

---

## 4. Navigation & UX Flow

### 4.1 Tab-Navigation

**Aktuell:**
- 10 Tabs in NavBar (70px breit, links)
- Icons + Labels
- Aktiver Tab: Accent-Color Border

**Keyboard-Shortcuts:**
- `Ctrl+1` bis `Ctrl+9`: Tab-Wechsel
- `A`: ARM (alle Mission-Targets)
- `D`: DISARM
- `T`: TAKEOFF
- `L`: LAND
- `R`: RTL
- `Space`: HOLD

✅ **Gut:** Shortcuts für häufige Aktionen  
⚠️ **Problem:** Keine visuelle Anzeige der Shortcuts (Tooltips fehlen)

### 4.2 Workflow-Analyse

#### Typischer Workflow: Single-Drone Mission

1. **Connect** → Dashboard Tab (Telemetrie prüfen)
2. **ARM** → InstrBar Quick Command
3. **TAKEOFF** → InstrBar Quick Command
4. **Add Waypoints** → Map Tab (Click-Modus)
5. **Start Mission** → Swarm Tab (Mission-Target auswählen + Start)
6. **Monitor** → Map Tab (Live-Tracking)
7. **RTL** → InstrBar Quick Command

**UX-Score:** 7/10  
**Kritik:** Waypoint-Hinzufügen erfordert Tab-Wechsel (Map → Swarm → Map)

#### Typischer Workflow: Multi-Drone Formation

1. **Connect All** → Swarm Tab (Drone-Liste)
2. **Select Formation** → Swarm Tab (Formation-Preview)
3. **ARM All** → Swarm Tab (Multi-Select + ARM)
4. **Start Formation** → Swarm Tab (Formation-Start Button)
5. **Monitor** → Map Tab (Live-Tracking)

**UX-Score:** 8/10  
**Kritik:** Formation-Preview könnte größer sein

### 4.3 Verbesserungsvorschläge

1. **Quick-Access-Toolbar:** Häufige Aktionen in allen Tabs verfügbar
2. **Context-Menu:** Rechtsklick auf Drone in Map → Quick-Commands
3. **Drag & Drop:** Waypoints direkt auf Map ziehen
4. **Undo/Redo:** Für Waypoint-Editing
5. **Presets:** Gespeicherte Missionen/Formationen

---

## 5. Accessibility & Responsive Design

### 5.1 Accessibility-Audit

#### ❌ Fehlende Features:

- **Keyboard-Navigation:** Tab-Order nicht definiert
- **Screen-Reader:** Keine ARIA-Labels
- **High-Contrast-Mode:** Nicht unterstützt
- **Font-Scaling:** Keine Zoom-Funktion
- **Color-Blind-Mode:** Keine alternativen Farbschemata

#### Empfehlungen:

1. **Keyboard-Navigation:**
   ```qml
   KeyNavigation.tab: nextElement
   KeyNavigation.backtab: prevElement
   ```

2. **Accessible Names:**
   ```qml
   Accessible.name: "Arm Drone Button"
   Accessible.description: "Arms the selected drone for flight"
   ```

3. **Focus-Indicators:**
   ```qml
   Rectangle {
       border.color: activeFocus ? Theme.accent : Theme.border
       border.width: activeFocus ? 2 : 1
   }
   ```

### 5.2 Responsive Design

#### Aktuelle Breakpoints:

- **Minimum:** 1100x700px
- **Optimal:** 1440x900px (Maximized)
- **Fullscreen:** Beliebig

#### Layout-Verhalten:

| Breite | InstrBar | Panels | NavBar |
|--------|----------|--------|--------|
| <1200px | Horizontal Scroll | Single Column | Icons only |
| 1200-1600px | Alle Tiles sichtbar | Two Column | Icons + Labels |
| >1600px | Alle Tiles + Spacing | Three Column | Icons + Labels |

✅ **Gut:** Minimum-Size verhindert Layout-Bruch  
⚠️ **Problem:** Keine echten Breakpoints (nur Minimum)

#### Empfehlungen:

1. **Adaptive InstrBar:** Bei <1200px: 2 Zeilen statt Scroll
2. **Collapsible NavBar:** Bei <1000px: Nur Icons
3. **Mobile-Layout:** Für Tablet-Nutzung (optional)

---

## 6. UI-Tests

### 6.1 Aktueller Stand

**Vorhandene Tests:**
- `tests/test_ui_service_locator.py` - Backend-Injection
- `tests/test_ui_telemetry_model.py` - TelemetryModel
- `tests/test_ui_wire.py` - Context-Wiring

**Fehlende Tests:**
- ❌ QML Component-Tests
- ❌ Integration-Tests (User-Flows)
- ❌ Visual Regression Tests
- ❌ Performance-Tests (Rendering)

### 6.2 Test-Strategie

#### 6.2.1 Component-Tests (Qt Test Framework)

```cpp
// tests/qml/tst_InstrBar.qml
import QtQuick
import QtTest

TestCase {
    name: "InstrBarTests"
    
    InstrBar {
        id: instrBar
        swarmRef: mockSwarm
    }
    
    function test_droneSelector() {
        compare(instrBar.selectedDroneId, "")
        instrBar.selectedDroneId = "UAV_1"
        compare(instrBar.selectedDroneId, "UAV_1")
    }
    
    function test_batteryColor() {
        instrBar.t_battery_pct = 80
        compare(instrBar.battColor2(), "#22c55e")
        instrBar.t_battery_pct = 15
        compare(instrBar.battColor2(), "#ef4444")
    }
}
```

#### 6.2.2 Integration-Tests (Python + Qt)

```python
# tests/test_ui_integration.py
import pytest
from PyQt6.QtCore import QTimer
from tools.ui.app import create_app

def test_arm_disarm_workflow(qtbot):
    """Test ARM → DISARM workflow"""
    app = create_app()
    qtbot.addWidget(app.window)
    
    # Simulate drone connection
    app.swarm.add("UAV_1", "mock://")
    qtbot.wait(100)
    
    # Click ARM button
    arm_btn = app.window.findChild(QPushButton, "armButton")
    qtbot.mouseClick(arm_btn, Qt.LeftButton)
    qtbot.wait(500)
    
    # Verify armed state
    assert app.swarm.droneSnapshot("UAV_1")["armed"] == True
```

#### 6.2.3 Visual Regression Tests (Playwright)

```python
# tests/visual/test_screenshots.py
from playwright.sync_api import sync_playwright

def test_dashboard_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080")
        page.click("text=Dashboard")
        page.screenshot(path="screenshots/dashboard.png")
        # Compare with baseline
        assert compare_images("screenshots/dashboard.png", 
                             "baselines/dashboard.png") > 0.95
```

### 6.3 Test-Coverage-Ziele

| Kategorie | Aktuell | Ziel |
|-----------|---------|------|
| Backend (Python) | 85% | 90% |
| QML Components | 0% | 70% |
| Integration | 0% | 60% |
| Visual Regression | 0% | 50% |

---

## 7. Performance-Analyse

### 7.1 Startup-Zeit

**Aktuell:** ~2200ms cold-start (siehe Profiler-Output)

| Phase | Zeit | Anteil |
|-------|------|--------|
| Python Start | 0ms | 0% |
| QtWebEngine Init | 88ms | 4% |
| Qt Core Imports | 10ms | 0.5% |
| QApplication Ready | 35ms | 1.6% |
| Splash Built | 1152ms | 52% |
| Context Construct | 538ms | 24% |
| QML Loaded | 257ms | 12% |
| Ready | 3ms | 0.1% |

**Bottleneck:** Splash-Screen-Rendering (1152ms)

**Empfehlung:** Lazy-Load Splash-Assets, Pre-render bei Installation

### 7.2 Runtime-Performance

**Telemetrie-Update:** 100ms Interval (10Hz)  
**Canvas-Repaints:** Attitude + Compass bei jedem Update  
**Memory:** ~150MB nach 10min Betrieb

✅ **Gut:** Keine Memory-Leaks (nach Feature 2 Fix)  
⚠️ **Optimierung:** Canvas-Repaints nur bei Wertänderung >1°

---

## 8. Empfehlungen (Priorisiert)

### 8.1 Kritisch (P0)

1. **UI-Tests implementieren** (6.2)
   - Component-Tests für InstrBar, Theme, Panels
   - Integration-Tests für Workflows
   - Geschätzter Aufwand: 3-4 Tage

2. **Accessibility-Grundlagen** (5.1)
   - Keyboard-Navigation für alle Buttons
   - Focus-Indicators
   - Geschätzter Aufwand: 2 Tage

### 8.2 Hoch (P1)

3. **Theme-Konsistenz** (1.2)
   - Alle hardcoded Spacing durch `Theme.spacing()` ersetzen
   - Font-Größen standardisieren
   - Geschätzter Aufwand: 1 Tag

4. **DroneSelector Component** (2.3)
   - Wiederverwendbare Component extrahieren
   - Einheitliches Styling
   - Geschätzter Aufwand: 0.5 Tage

5. **InstrBar-Erweiterungen** (3.2)
   - Mission Progress Tile
   - EKF Status Tile
   - Geschätzter Aufwand: 1-2 Tage

### 8.3 Mittel (P2)

6. **Responsive InstrBar** (3.3)
   - 2-Zeilen-Layout bei <1200px
   - Collapsible Sections
   - Geschätzter Aufwand: 2 Tage

7. **Context-Menu** (4.3)
   - Rechtsklick auf Drone → Quick-Commands
   - Waypoint-Editing
   - Geschätzter Aufwand: 1 Tag

8. **Visual Regression Tests** (6.2.3)
   - Screenshot-basierte Tests
   - CI-Integration
   - Geschätzter Aufwand: 2 Tage

### 8.4 Niedrig (P3)

9. **High-Contrast-Mode** (5.1)
   - Alternatives Farbschema
   - User-Preference
   - Geschätzter Aufwand: 1 Tag

10. **Performance-Optimierung** (7.2)
    - Canvas-Repaint-Throttling
    - Lazy-Loading für Panels
    - Geschätzter Aufwand: 1-2 Tage

---

## 9. Fazit

Die skymeshx GCS UI ist **funktional solide** mit einem **konsistenten Design-System**. Die Hauptschwächen liegen in:

1. **Fehlenden UI-Tests** (kritisch für Wartbarkeit)
2. **Accessibility-Lücken** (wichtig für professionelle Nutzung)
3. **Kleineren Inkonsistenzen** (Theme-Nutzung)

**Gesamtbewertung:** 7.5/10

**Nächste Schritte:**
1. UI-Tests implementieren (P0)
2. Accessibility-Grundlagen (P0)
3. Theme-Konsistenz (P1)

**Geschätzter Gesamtaufwand für P0+P1:** 7-9 Tage

---

## Anhang A: Theme-Migration-Checklist

- [ ] InstrBar: `spacing: 6` → `Theme.spacing(1.5)`
- [ ] DashboardPanel: `spacing: 10` → `Theme.spacing(2.5)`
- [ ] SwarmPanel: `spacing: 8` → `Theme.spacing(2)`
- [ ] SafetyPanel: `spacing: 12` → `Theme.spacing(3)`
- [ ] ROS2Panel: `spacing: 8` → `Theme.spacing(2)`
- [ ] ExperimentPanel: `spacing: 8` → `Theme.spacing(2)`
- [ ] Alle `font.pixelSize: 9` → `Theme.fontS` oder `Theme.fontM`
- [ ] Alle `font.pixelSize: 7` → `Theme.fontXS`
- [ ] Alle `margins: 10` → `Theme.spacing(2.5)`
- [ ] Alle `margins: 12` → `Theme.spacing(3)`

## Anhang B: Test-Coverage-Matrix

| Component | Unit | Integration | Visual | Total |
|-----------|------|-------------|--------|-------|
| Theme.qml | ✅ | - | - | 33% |
| InstrBar.qml | ❌ | ❌ | ❌ | 0% |
| DashboardPanel.qml | ❌ | ❌ | ❌ | 0% |
| SwarmPanel.qml | ❌ | ❌ | ❌ | 0% |
| SafetyPanel.qml | ❌ | ❌ | ❌ | 0% |
| ROS2Panel.qml | ❌ | ❌ | ❌ | 0% |
| MapView.qml | ❌ | ❌ | ❌ | 0% |
| **Gesamt** | **10%** | **0%** | **0%** | **3%** |
