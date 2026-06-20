# Open Source und Commercial Feature Split

Datum: 2026-06-20

Ziel dieses Dokuments: SkyMeshX soll als Open-Core-Produkt aufgebaut werden. Die Open-Source-Version soll stark genug sein, um Vertrauen, Forschung, Community-Beitraege und technische Adoption zu erzeugen. Die Commercial-Version soll produktive Nutzung, Support, Sicherheit, Deployment und fortgeschrittene Workflows monetarisieren.

## Leitprinzip

Open Source beantwortet:

> Wie baue, teste, verstehe und erweitere ich SkyMeshX?

Commercial beantwortet:

> Wie betreibe ich SkyMeshX sicher, komfortabel und professionell mit echten Flotten?

Die Grenze sollte nicht entlang "gute Features vs. schlechte Features" laufen, sondern entlang "Entwicklung/Forschung" vs. "produktiver Betrieb/Organisation".

## Empfohlenes Modell

Empfehlung: Open Core.

- Core SDK, CLI, Simulation, Safety-Basis und Tests bleiben offen.
- Pro-GCS, Enterprise-Security, Installer, Updater, Support-Integrationen und produktive Flottenfeatures werden commercial.
- Die offene Version bleibt nutzbar und ernstzunehmend, damit sie Entwickler und Forschungseinrichtungen wirklich anzieht.

## Feature Matrix

| Bereich | Open Source | Commercial |
|---|---|---|
| Core SDK | `Drone`, `Swarm`, Telemetry, FSM, MAVLink-Basis | stabile Enterprise-APIs, erweiterte Adapter, Integrationsgarantien |
| CLI | connect/status/arm/takeoff/land/goto/run | Batch-Operationen, Profile, signierte Skripte, Flottenbefehle |
| Simulation | Mock backend, SITL-Hilfen, Beispiele | One-click multi-vehicle SITL, Szenario-Manager, Demo-Pakete |
| Safety | APF-Basis, Battery Monitor, Collision Predictor | Safety Supervisor, Policy Engine, Safety Reports, erweiterte Geofences |
| Missionen | Basic Waypoint Mission, Mission Upload, Validierung | Mission Planner UI, Templates, Approval Workflow, Async Queue |
| UI/GCS | Community Dashboard, Map, Logs, Basis-Steuerung | Full Pro GCS, Fleet Dashboard, Advanced Panels, produktive Workflows |
| ROS2/PX4 | Beispiele, Basis-Bridge | Production Bridge UI, Reconnect Diagnostics, Formation Controller |
| Daten/Logs | JSONL Logs, einfache Exporte | Audit Logs, signierte Logs, Replay, Analytics, Kompression |
| LLM | Mock/local Beispiele | Cloud-LLM Integration, Guardrails, Approval Workflow |
| Installer | Source Install, Dev Build Scripts | signierte Installer, Auto-Updater, Lizenzsystem |
| Security | Security Baseline, Bugfixes, sichere Defaults | RBAC, Auth, verschluesselte Config, Enterprise Deployment |
| Support | Community Issues, Docs | Priority Support, SLA, Training, Custom Integration |

## Open Source Version

Die Open-Source-Version sollte enthalten:

- `skymeshx/core`
- `skymeshx/sdk`
- `skymeshx/cli`
- `skymeshx/control` Basisfunktionen
- `skymeshx/safety` Basisfunktionen
- `skymeshx/simulation` Basisfunktionen
- `skymeshx/data` einfache Logs und Speicherung
- `examples`
- hardwarefreie Tests
- Security Baseline und Audit-Dokumentation
- einfache Community-GCS oder minimale UI, falls wartbar

Zielgruppe:

- Forschung
- Hochschulen
- Maker
- Entwickler
- Integratoren, die SkyMeshX evaluieren

Nicht ideal fuer Open Source:

- kommerzielle Installer
- Lizenzsystem
- Auto-Updater
- Enterprise Auth/RBAC
- produktive Flotten-Dashboards
- Support- und Compliance-Dokumente

## Commercial Version

Die Commercial-Version sollte enthalten:

- Pro-GCS mit voller UI
- Multi-Drone Fleet Operations
- Mission Planner mit Templates
- ROS2/PX4 Production Tools
- Bag Recording/Playback UI
- Advanced Safety Supervisor
- Audit Logging und signierte Logs
- RBAC und Auth
- verschluesselte Konfiguration
- signierte Installer und Auto-Updater
- Lizenzmanagement
- kommerzielle Deployment-Guides
- Training, Support und Custom Integrations

Zielgruppe:

- Unternehmen
- Forschungslabore mit Produktivbetrieb
- Drohnen-Dienstleister
- Industriepartner
- Teams mit Compliance-/Audit-Anforderungen

## Repo-Struktur

### Variante A: Zwei Repositories

Empfohlen fuer saubere Trennung.

```text
skymeshx
  skymeshx/
  examples/
  tests/
  docs/

skymeshx-pro
  pro_ui/
  installer/
  updater/
  enterprise_security/
  mission_templates/
  commercial_docs/
```

Vorteile:

- klare Lizenzgrenze
- einfacherer Kundenzugriff
- weniger Risiko, proprietaeren Code versehentlich zu veroeffentlichen

Nachteile:

- mehr Release-Koordination
- Schnittstellen zwischen Core und Pro muessen stabil sein

### Variante B: Ein Repository mit separatem Commercial-Verzeichnis

```text
skymeshx/
tools/ui/community/
commercial/
  ui_pro/
  updater/
  license/
  enterprise_security/
```

Vorteile:

- einfachere Entwicklung am Anfang
- Pro-Code kann direkt gegen lokale Core-Aenderungen laufen

Nachteile:

- hoehere Gefahr von Lizenz- und Release-Vermischung
- schwieriger, Community-Beitraege sauber zu verwalten

## Lizenzstrategie

Moegliche Modelle:

1. MIT oder Apache-2.0 fuer den Core, proprietaere Commercial-Version.
2. AGPL fuer Open Source plus Commercial License fuer Kunden, die Copyleft vermeiden wollen.
3. MIT Community Edition plus separate Pro-Lizenz.

Empfehlung:

- Core: Apache-2.0 oder MIT.
- Commercial: proprietaere Lizenz.
- Contributions: Contributor License Agreement oder Developer Certificate of Origin pruefen.

Hinweis: Fuer die finale Lizenzstrategie sollte juristische Beratung eingeholt werden.

## Packaging und Produktnamen

Moegliche Produktnamen:

- SkyMeshX Community
- SkyMeshX Pro
- SkyMeshX Enterprise

Vorschlag:

- `skymeshx` bleibt der offene Core.
- `SkyMeshX GCS Community` ist eine einfache UI.
- `SkyMeshX GCS Pro` ist die kommerzielle Vollversion.
- `SkyMeshX Enterprise` ergaenzt Auth, RBAC, Audit, Support und Deployment.

## Security-Aufteilung

Security-Bugfixes sollten nicht kuenstlich hinter Paywalls liegen. Unsichere Defaults in der Open-Source-Version schaden dem Ruf des gesamten Produkts.

Open Source:

- sichere Defaults
- Input Validation
- Security Baseline
- Tests fuer bekannte Schwachstellen
- einfache lokale Auth, falls ein Server exposed werden kann

Commercial:

- RBAC
- Multi-User Auth
- Audit Trails
- signierte Updates
- verschluesselte Konfiguration
- zentrale Policy-Verwaltung
- Compliance-Reports

## Release-Plan

### Phase 1: Stabiler Open Core

- Core API aufraeumen
- Security Baseline fertigstellen
- Test-Suite gruen bekommen
- Community-Dokumentation schreiben
- klare Modulgrenzen definieren

### Phase 2: Pro-Abgrenzung

- Pro-Features markieren
- Installer/Updater/Lizenzsystem aus Core herausziehen
- Feature Flags definieren
- Produktnamen und Versionierung festlegen

### Phase 3: Commercial Readiness

- signierte Installer
- verpflichtende Update-Signaturen
- Lizenz-Secret aus Build-Prozess statt Source
- Kundendokumentation
- Support-Prozess

## Empfohlene erste Umsetzung

1. `skymeshx` als Open-Source-Core behalten.
2. `tools/ui` aufteilen in Community-UI und Pro-UI.
3. Updater, Installer und Lizenzsystem als Commercial markieren.
4. Security-Fixes immer in Open Source zurueckfuehren.
5. Commercial-Wert ueber Produktivitaet, Sicherheit, Deployment und Support schaffen.

## Kurzfassung

Open Source:

- Core
- SDK
- CLI
- Tests
- Simulation
- Basis-Safety
- einfache UI

Commercial:

- Pro-GCS
- Installer/Updater
- Lizenzsystem
- Enterprise Security
- Advanced ROS2/PX4 Tools
- Fleet Operations
- Audit/Compliance
- Support

