# License Audit: Commercial Use Compliance

**Datum:** 2026-06-16  
**Auditor:** License Compliance Analysis  
**Scope:** Dependency Licenses, Research Paper Usage, Commercial Viability  
**Project License:** MIT  

---

## Executive Summary

Das UAVResearch-Projekt verwendet **MIT License** für eigenen Code, hat aber **kritische GPL-Abhängigkeiten** die kommerzielle Nutzung **einschränken**. 

### 🔴 CRITICAL: Kommerzielle Nutzung NICHT möglich ohne Änderungen

**Hauptproblem:** PyQt6 ist **GPL v3** → Zwingt gesamte Anwendung unter GPL v3

**Lösung:** Kommerzielle PyQt6-Lizenz kaufen ODER UI-Framework wechseln

---

## Lizenz-Status nach Komponente

| Komponente | Lizenz | Kommerziell? | Status | Aktion |
|------------|--------|--------------|--------|--------|
| **Core Package** | MIT | ✅ Ja | 🟢 OK | Keine |
| **pymavlink** | LGPL v3+ | ✅ Ja | 🟢 OK | Attribution |
| **pyserial** | BSD-3-Clause | ✅ Ja | 🟢 OK | Attribution |
| **PyQt6** | GPL v3 | ❌ Nein | 🔴 BLOCKER | Lizenz kaufen |
| **PyQt6-WebEngine** | GPL v3 | ❌ Nein | 🔴 BLOCKER | Lizenz kaufen |
| **pytest** | MIT | ✅ Ja | 🟢 OK | Nur Dev |
| **psutil** | BSD-3-Clause | ✅ Ja | 🟢 OK | Attribution |
| **ROS2 (rclpy)** | Apache 2.0 | ✅ Ja | 🟢 OK | Attribution |
| **px4_msgs** | BSD-3-Clause | ✅ Ja | 🟢 OK | Attribution |

---

## 🔴 CRITICAL: PyQt6 GPL v3 Problem

### Problem

**PyQt6 ist GPL v3-only:**
- GPL v3 ist "viral" → Zwingt gesamte Anwendung unter GPL v3
- Kommerzielle Closed-Source-Software ist **NICHT erlaubt**
- Verkauf von Binaries ohne Source Code ist **NICHT erlaubt**

### Betroffene Module

```
tools/ui/
├── main_window.py          # PyQt6.QtWidgets
├── dashboard_tab.py        # PyQt6.QtWidgets
├── map_tab.py              # PyQt6.QtWebEngineWidgets ← GPL!
├── swarm_tab.py            # PyQt6.QtWidgets
├── experiment_tab.py       # PyQt6.QtWidgets
├── safety_tab.py           # PyQt6.QtWidgets
├── log_tab.py              # PyQt6.QtWidgets
├── backend.py              # PyQt6.QtCore (Signals)
├── service_locator.py      # Indirekt betroffen
└── qml/                    # PyQt6.QtQml
    └── **/*.qml            # QML UI (GPL-kontaminiert)
```

**Impact:** Gesamte UI ist GPL v3 → Gesamte Anwendung muss GPL v3 sein

### Lösungen

#### Option 1: Kommerzielle PyQt6-Lizenz kaufen (€€€)

**Kosten:** ~€500-5000 pro Entwickler/Jahr (abhängig von Unternehmensgröße)

**Vorteile:**
- ✅ Keine Code-Änderungen nötig
- ✅ Professioneller Support
- ✅ Closed-Source erlaubt

**Nachteile:**
- ❌ Hohe Kosten
- ❌ Jährliche Verlängerung
- ❌ Pro-Developer-Lizenz

**Kontakt:** Riverbank Computing Limited  
**Website:** https://www.riverbankcomputing.com/commercial/buy

---

#### Option 2: UI-Framework wechseln (Empfohlen für Kommerzialisierung)

##### 2a) PySide6 (Qt for Python) - LGPL/Commercial

**Lizenz:** LGPL v3 / Commercial  
**Kosten:** Kostenlos (LGPL) oder Commercial License

**Vorteile:**
- ✅ LGPL erlaubt kommerzielle Nutzung (mit Dynamic Linking)
- ✅ Offizielle Qt-Implementierung
- ✅ API fast identisch zu PyQt6
- ✅ Kostenlos für die meisten kommerziellen Use Cases

**Nachteile:**
- ⚠️ Muss Dynamic Linking verwenden (Standard bei Python)
- ⚠️ Muss LGPL-Compliance sicherstellen

**Migration Effort:** ~2-3 Tage (API ist 95% kompatibel)

```python
# Änderungen:
# from PyQt6.QtWidgets import QWidget
# →
from PySide6.QtWidgets import QWidget

# from PyQt6.QtCore import pyqtSignal
# →
from PySide6.QtCore import Signal as pyqtSignal
```

---

##### 2b) Electron + Web UI - MIT/Apache

**Lizenz:** MIT (Electron), Apache 2.0 (Chromium)  
**Kosten:** Kostenlos

**Vorteile:**
- ✅ Vollständig kommerziell nutzbar
- ✅ Moderne Web-Technologien (React, Vue, etc.)
- ✅ Cross-Platform
- ✅ Große Community

**Nachteile:**
- ❌ Komplette UI-Rewrite nötig
- ❌ Größere Binaries (~100MB)
- ❌ Höherer RAM-Verbrauch

**Migration Effort:** ~4-6 Wochen

---

##### 2c) Tauri + Web UI - MIT/Apache

**Lizenz:** MIT (Tauri), Apache 2.0 (WebView)  
**Kosten:** Kostenlos

**Vorteile:**
- ✅ Vollständig kommerziell nutzbar
- ✅ Kleinere Binaries als Electron (~10MB)
- ✅ Bessere Performance
- ✅ Rust-Backend (sicher)

**Nachteile:**
- ❌ Komplette UI-Rewrite nötig
- ❌ Rust-Kenntnisse erforderlich
- ❌ Kleinere Community als Electron

**Migration Effort:** ~6-8 Wochen

---

##### 2d) Dear ImGui (Python Bindings) - MIT

**Lizenz:** MIT  
**Kosten:** Kostenlos

**Vorteile:**
- ✅ Vollständig kommerziell nutzbar
- ✅ Sehr performant
- ✅ Ideal für Echtzeit-Telemetrie
- ✅ Kleine Binaries

**Nachteile:**
- ❌ Weniger "polished" als Qt
- ❌ Immediate-Mode GUI (anderes Paradigma)
- ❌ Komplette UI-Rewrite nötig

**Migration Effort:** ~3-4 Wochen

---

#### Option 3: Dual-Licensing (Open Source + Commercial)

**Strategie:**
1. Open-Source Version mit PyQt6 (GPL v3) → Kostenlos
2. Commercial Version mit PySide6/Electron → Verkauf

**Vorteile:**
- ✅ Community kann Open-Source nutzen
- ✅ Kommerzielle Kunden zahlen für Closed-Source
- ✅ Beide Versionen pflegen

**Nachteile:**
- ❌ Doppelter Maintenance-Aufwand
- ❌ Komplexe Lizenz-Verwaltung

---

## 🟢 OK: Core Package (MIT License)

### Eigener Code

**Lizenz:** MIT  
**Copyright:** Joel Djio / Aerospace Research

**Erlaubt:**
- ✅ Kommerzielle Nutzung
- ✅ Modifikation
- ✅ Distribution
- ✅ Private Nutzung
- ✅ Sublizenzierung

**Bedingungen:**
- ⚠️ Copyright Notice beibehalten
- ⚠️ License Text beibehalten

**Keine Garantie:**
- ❌ Keine Haftung
- ❌ Keine Gewährleistung

---

## 🟢 OK: pymavlink (LGPL v3+)

### Lizenz-Details

**Lizenz:** GNU Lesser General Public License v3 or later  
**Copyright:** ArduPilot Dev Team  
**Repository:** https://github.com/ArduPilot/pymavlink

### Kommerzielle Nutzung

**Erlaubt:**
- ✅ Kommerzielle Nutzung als Library
- ✅ Dynamic Linking (Standard bei Python)
- ✅ Closed-Source Anwendung möglich

**Bedingungen:**
- ⚠️ LGPL License Text beibehalten
- ⚠️ Copyright Notice beibehalten
- ⚠️ Änderungen an pymavlink selbst müssen veröffentlicht werden
- ⚠️ User muss pymavlink ersetzen können (Dynamic Linking)

**Wichtig:**
- ✅ Generierter Code (mavgen.py) ist **MIT License** → Keine Einschränkungen!

### Compliance-Checkliste

```markdown
- [ ] LGPL v3 License Text in Distribution einbinden
- [ ] Copyright Notice für pymavlink einbinden
- [ ] Dokumentieren, dass pymavlink als Library verwendet wird
- [ ] Sicherstellen, dass User pymavlink ersetzen kann (pip install)
- [ ] Keine Modifikationen an pymavlink selbst (oder veröffentlichen)
```

---

## 🟢 OK: pyserial (BSD-3-Clause)

**Lizenz:** BSD 3-Clause License  
**Kommerzielle Nutzung:** ✅ Vollständig erlaubt

**Bedingungen:**
- ⚠️ Copyright Notice beibehalten
- ⚠️ License Text beibehalten
- ⚠️ Keine Werbung mit Namen ohne Erlaubnis

---

## 🟢 OK: psutil (BSD-3-Clause)

**Lizenz:** BSD 3-Clause License  
**Kommerzielle Nutzung:** ✅ Vollständig erlaubt

**Bedingungen:** Gleich wie pyserial

---

## 🟢 OK: pytest (MIT)

**Lizenz:** MIT License  
**Kommerzielle Nutzung:** ✅ Vollständig erlaubt  
**Hinweis:** Nur Development Dependency → Nicht in Distribution

---

## 🟢 OK: ROS2 (Apache 2.0)

**Lizenz:** Apache License 2.0  
**Kommerzielle Nutzung:** ✅ Vollständig erlaubt

**Bedingungen:**
- ⚠️ Apache License Text beibehalten
- ⚠️ NOTICE File beibehalten (falls vorhanden)
- ⚠️ Änderungen dokumentieren

**Optional Dependencies:**
- `rclpy` - Apache 2.0
- `px4_msgs` - BSD-3-Clause

---

## 📚 Research Papers & Referenced Code

### 1. SkySim (APF Implementation)

**Paper:** "SkySim: A ROS2-based Simulation Environment for Natural Language Control of Drone Swarms using Large Language Models"  
**Authors:** Shibu et al., 2025  
**arXiv:** 2602.01226  
**Code:** Nicht öffentlich verfügbar (nur Paper)

**Verwendung in Projekt:**
- `droneresearch/safety/apf.py` - APF Safety Filter basiert auf Paper

**Lizenz-Status:**
- ✅ **Algorithmus-Implementierung ist erlaubt** (Papers sind nicht urheberrechtlich geschützt)
- ✅ **Eigene Implementierung** (kein Code kopiert)
- ⚠️ **Citation erforderlich** in Dokumentation/Paper

**Compliance:**
```python
# droneresearch/safety/apf.py
"""
APF Safety Filter — Artificial Potential Field collision avoidance.

Based on: SkySim (Shibu et al., 2025)
    "SkySim: A ROS2-based Simulation Environment for Natural Language
     Control of Drone Swarms using Large Language Models"
    arXiv:2602.01226
"""
```

**Kommerzielle Nutzung:** ✅ Erlaubt (eigene Implementierung)

---

### 2. vswarm (Vision-based Flocking)

**Paper:** "Vision-based Drone Flocking in Outdoor Environments"  
**Authors:** Schilling et al., IEEE RA-L 2021  
**Repository:** https://github.com/lis-epfl/vswarm  
**Lizenz:** **BSD-3-Clause**

**Verwendung in Projekt:**
- `droneresearch/exploration/vswarm_bridge.py` - ROS2 Bridge zu vswarm

**Lizenz-Status:**
- ✅ **BSD-3-Clause erlaubt kommerzielle Nutzung**
- ✅ **Bridge-Code ist eigene Implementierung**
- ⚠️ **vswarm selbst muss separat installiert werden** (nicht gebundled)

**Compliance:**
```markdown
- [ ] BSD-3-Clause License von vswarm in Dokumentation erwähnen
- [ ] Copyright Notice für vswarm einbinden
- [ ] Klarstellen, dass vswarm separat installiert werden muss
```

**Kommerzielle Nutzung:** ✅ Erlaubt (BSD-3-Clause)

---

### 3. uav_frontier_exploration_3d (Frontier Exploration)

**Paper:** Batinovic et al., IEEE RA-L 2021  
**Repository:** https://github.com/larics/uav_frontier_exploration_3d  
**Lizenz:** **BSD-3-Clause**

**Verwendung in Projekt:**
- `droneresearch/exploration/frontier_bridge.py` - ROS2 Bridge zu Frontier Explorer

**Lizenz-Status:**
- ✅ **BSD-3-Clause erlaubt kommerzielle Nutzung**
- ✅ **Bridge-Code ist eigene Implementierung**
- ⚠️ **Frontier Explorer muss separat installiert werden**

**Compliance:** Gleich wie vswarm

**Kommerzielle Nutzung:** ✅ Erlaubt (BSD-3-Clause)

---

## 📋 Compliance-Checkliste für kommerzielle Distribution

### Sofort (vor Verkauf)

- [ ] **PyQt6-Problem lösen:**
  - [ ] Option A: Kommerzielle PyQt6-Lizenz kaufen
  - [ ] Option B: Zu PySide6 migrieren (Empfohlen)
  - [ ] Option C: Zu Electron/Tauri migrieren
  - [ ] Option D: Dual-Licensing (Open Source + Commercial)

### License Files

- [ ] **Eigene MIT License** beibehalten in Distribution
- [ ] **THIRD_PARTY_LICENSES.txt** erstellen mit:
  - [ ] pymavlink LGPL v3 License Text
  - [ ] pyserial BSD-3-Clause License Text
  - [ ] psutil BSD-3-Clause License Text
  - [ ] ROS2 Apache 2.0 License Text (falls gebundled)
  - [ ] vswarm BSD-3-Clause License Text (falls gebundled)
  - [ ] frontier_exploration BSD-3-Clause License Text (falls gebundled)

### Copyright Notices

- [ ] **NOTICE.txt** erstellen mit:
  - [ ] Copyright für pymavlink
  - [ ] Copyright für pyserial
  - [ ] Copyright für psutil
  - [ ] Copyright für ROS2 (falls gebundled)
  - [ ] Citations für Papers (SkySim, vswarm, frontier)

### Dokumentation

- [ ] **README.md** aktualisieren:
  - [ ] Lizenz-Informationen
  - [ ] Third-Party-Lizenzen
  - [ ] Citations für Papers

- [ ] **User Manual** erstellen:
  - [ ] Lizenz-Hinweise
  - [ ] Open-Source-Komponenten

### Code

- [ ] **Keine GPL-Kontamination:**
  - [ ] PyQt6 entfernen ODER Lizenz kaufen
  - [ ] Alle GPL-Dependencies prüfen

- [ ] **LGPL-Compliance (pymavlink):**
  - [ ] Dynamic Linking sicherstellen (Standard bei Python)
  - [ ] User kann pymavlink ersetzen (pip install)
  - [ ] Keine Modifikationen an pymavlink

---

## 💰 Kosten-Schätzung für kommerzielle Nutzung

### Option 1: PyQt6 Commercial License

| Item | Kosten | Frequenz |
|------|--------|----------|
| PyQt6 Commercial License | €500-5000 | Pro Developer/Jahr |
| **Total (1 Developer)** | **€500-5000/Jahr** | Jährlich |
| **Total (5 Developers)** | **€2500-25000/Jahr** | Jährlich |

**Hinweis:** Genaue Preise auf Anfrage bei Riverbank Computing

---

### Option 2: PySide6 (LGPL) - Kostenlos

| Item | Kosten | Frequenz |
|------|--------|----------|
| PySide6 (LGPL) | €0 | Einmalig |
| Migration Effort | ~2-3 Tage | Einmalig |
| **Total** | **€0** | - |

**Bedingung:** LGPL-Compliance (Dynamic Linking, License Text)

---

### Option 3: Electron/Tauri - Kostenlos

| Item | Kosten | Frequenz |
|------|--------|----------|
| Electron/Tauri | €0 | Einmalig |
| UI Rewrite | ~4-8 Wochen | Einmalig |
| **Total** | **€0** | - |

**Vorteil:** Vollständig MIT/Apache → Keine Einschränkungen

---

## 🎯 Empfehlung

### Für Kommerzialisierung: **PySide6 Migration**

**Gründe:**
1. ✅ **Kostenlos** (LGPL erlaubt kommerzielle Nutzung)
2. ✅ **Minimaler Aufwand** (2-3 Tage Migration)
3. ✅ **API-kompatibel** (95% gleich wie PyQt6)
4. ✅ **Offizielle Qt-Implementierung**
5. ✅ **Keine jährlichen Lizenzkosten**

**Migration-Plan:**

```bash
# 1. Dependencies ändern
pip uninstall PyQt6 PyQt6-WebEngine
pip install PySide6 PySide6-WebEngine

# 2. Imports ändern (automatisierbar)
find tools/ui -name "*.py" -exec sed -i 's/PyQt6/PySide6/g' {} \;
find tools/ui -name "*.py" -exec sed -i 's/pyqtSignal/Signal/g' {} \;
find tools/ui -name "*.py" -exec sed -i 's/pyqtSlot/Slot/g' {} \;

# 3. Tests ausführen
pytest tests/test_ui_*.py -v

# 4. Manuelle Anpassungen (falls nötig)
# - Signal/Slot Syntax
# - QML Imports
```

**Geschätzte Zeit:** 2-3 Tage  
**Kosten:** €0  
**Risiko:** Niedrig (API sehr ähnlich)

---

### Alternative: **Dual-Licensing**

**Für Open-Source Community:**
- GPL v3 Version mit PyQt6 (kostenlos)
- Auf GitHub veröffentlichen

**Für kommerzielle Kunden:**
- PySide6/Electron Version (Closed-Source)
- Verkauf als Binary/SaaS

**Vorteil:** Beide Zielgruppen bedienen  
**Nachteil:** Doppelter Maintenance-Aufwand

---

## 📄 Template: THIRD_PARTY_LICENSES.txt

```text
UAVResearch Ground Control Station
Third-Party Software Licenses

This software includes the following third-party components:

================================================================================
pymavlink
================================================================================
License: GNU Lesser General Public License v3 or later (LGPL v3+)
Copyright: ArduPilot Dev Team
Repository: https://github.com/ArduPilot/pymavlink

[Full LGPL v3 License Text]
...

================================================================================
pyserial
================================================================================
License: BSD 3-Clause License
Copyright: Chris Liechti
Repository: https://github.com/pyserial/pyserial

[Full BSD-3-Clause License Text]
...

================================================================================
psutil
================================================================================
License: BSD 3-Clause License
Copyright: Giampaolo Rodola
Repository: https://github.com/giampaolo/psutil

[Full BSD-3-Clause License Text]
...

================================================================================
ROS2 (rclpy)
================================================================================
License: Apache License 2.0
Copyright: Open Source Robotics Foundation
Repository: https://github.com/ros2/rclpy

[Full Apache 2.0 License Text]
...

================================================================================
Research Papers & Algorithms
================================================================================

APF Safety Filter based on:
  Shibu et al., "SkySim: A ROS2-based Simulation Environment for Natural
  Language Control of Drone Swarms using Large Language Models"
  arXiv:2602.01226, 2025

vswarm Integration based on:
  Schilling et al., "Vision-based Drone Flocking in Outdoor Environments"
  IEEE RA-L 2021
  Repository: https://github.com/lis-epfl/vswarm (BSD-3-Clause)

Frontier Exploration Integration based on:
  Batinovic et al., IEEE RA-L 2021
  Repository: https://github.com/larics/uav_frontier_exploration_3d (BSD-3-Clause)
```

---

## 📄 Template: NOTICE.txt

```text
UAVResearch Ground Control Station
Copyright (c) 2025 Joel Djio / Aerospace Research

This product includes software developed by:
- ArduPilot Dev Team (pymavlink)
- Chris Liechti (pyserial)
- Giampaolo Rodola (psutil)
- Open Source Robotics Foundation (ROS2)

This product implements algorithms described in:
- Shibu et al., "SkySim" (arXiv:2602.01226, 2025)
- Schilling et al., "Vision-based Drone Flocking" (IEEE RA-L 2021)
- Batinovic et al., "Frontier Exploration" (IEEE RA-L 2021)

For full license information, see THIRD_PARTY_LICENSES.txt
```

---

## ⚖️ Legal Disclaimer

**Wichtig:** Dieses Audit ist keine Rechtsberatung. Für verbindliche Aussagen konsultiere einen Anwalt mit Expertise in Software-Lizenzen.

**Empfehlung:** Vor kommerzieller Distribution:
1. Anwalt konsultieren
2. Lizenz-Compliance prüfen lassen
3. Alle Third-Party-Lizenzen verifizieren

---

## 📞 Kontakte für Lizenz-Fragen

### PyQt6 Commercial License
- **Unternehmen:** Riverbank Computing Limited
- **Website:** https://www.riverbankcomputing.com/commercial/buy
- **Email:** sales@riverbankcomputing.com

### Rechtliche Beratung
- Software-Lizenz-Anwalt konsultieren
- Spezialisierung: Open-Source-Lizenzen, GPL, LGPL

---

## ✅ Zusammenfassung

### Kann ich mit diesem Projekt Geld verdienen?

**Aktuell:** ❌ **NEIN** (wegen PyQt6 GPL v3)

**Nach PySide6-Migration:** ✅ **JA** (alle Lizenzen kompatibel)

**Nach PyQt6-Lizenz-Kauf:** ✅ **JA** (aber teuer)

### Schnellste Lösung für Kommerzialisierung

1. **PySide6 Migration** (2-3 Tage, €0)
2. **THIRD_PARTY_LICENSES.txt** erstellen (1 Tag)
3. **NOTICE.txt** erstellen (1 Tag)
4. **Dokumentation aktualisieren** (1 Tag)

**Total:** ~1 Woche, €0 Kosten

### Papers & Algorithmen

✅ **Alle verwendeten Papers/Algorithmen sind kommerziell nutzbar**
- SkySim: Eigene Implementierung, Citation erforderlich
- vswarm: BSD-3-Clause (kommerziell OK)
- frontier_exploration: BSD-3-Clause (kommerziell OK)

---

**Ende des License Audits**
