# Camera, Seeding, Solar Implementation Plan
# Parallel Work Division: Bob & Codex

**Created:** 2026-06-23  
**Source:** `comprehensive-camera-seeding-solar-implementation.md`  
**Collaboration File:** `camera-seeding-solar-collab-feedback.md`

## 🎯 Collaboration Rules

1. **No Direct Communication** - All coordination via feedback file
2. **No Simultaneous Edits** - Check file ownership before editing
3. **Document First** - Write feedback entry before touching shared files
4. **Test Everything** - All code must have hardware-free tests
5. **API Contracts** - Document interfaces before implementation

---

## 📋 Codex Tasks (Backend & Foundation)

### Phase 1: Camera Context Foundation ⏱️ Week 1-2

- [x] **1.1** Create `tools/ui/context/camera_context.py`
  - [x] Implement `CameraContext` class inheriting from `QObject`
  - [x] Add QML-facing slots: `cameraStartStream()`, `cameraStopStream()`, `cameraSnapshot()`
  - [x] Add QML-facing slots: `cameraStartRecording()`, `cameraStopRecording()`
  - [x] Add QML-facing slots: `setCameraProfile()`, `getCameraStatus()`
  - [x] Add QML-facing slots: `setTempRange()`, `setColorPalette()`, `setHotspotDetection()`
  - [x] Implement Qt properties: `currentSource`, `streamActive`, `recordingActive`
  - [x] Implement Qt properties: `recordingDuration`, `frameAge`, `droppedFrames`
  - [x] Implement Qt properties: `currentProfile`, `lastError`
  - [x] Implement Qt signals: `streamStarted`, `streamStopped`, `recordingStarted`, `recordingStopped`
  - [x] Implement Qt signals: `snapshotCaptured`, `errorOccurred`, `statusChanged`
  - [x] Add hardware-free fallback behavior (mock mode when no camera available)
  - [x] Document API contract in feedback file

- [x] **1.2** Extend `tools/ui/backend.py` for camera delegation
  - [x] Add `get_camera_context()` method to return `CameraContext` instance
  - [x] Add camera stream routing to selected observation drone
  - [x] Add recording control delegation
  - [x] Add snapshot capture delegation
  - [x] Add camera/gimbal health status aggregation
  - [x] Ensure hardware-free operation when no camera backend available

- [x] **1.3** Extend `skymeshx/models/observation_uav.py`
  - [x] Add `start_camera_stream(source: str) -> bool` method
  - [x] Add `stop_camera_stream() -> bool` method
  - [x] Add `capture_snapshot() -> bool` method
  - [x] Add `start_recording(path: str) -> bool` method
  - [x] Add `stop_recording() -> bool` method
  - [x] Add `get_camera_status() -> dict` method
  - [x] Add `get_gimbal_status() -> dict` method
  - [x] Add MAVLink command mapping for camera control
  - [x] Add hardware-free mock responses

- [x] **1.4** Register camera context in `tools/ui/service_locator.py`
  - [x] Document change in feedback file BEFORE editing
  - [x] Add `camera` context registration
  - [x] Ensure proper initialization order
  - [x] Add cleanup on shutdown

- [x] **1.5** Create `tests/test_camera_context.py`
  - [x] Test stream start/stop with fake connection
  - [x] Test recording start/stop with fake connection
  - [x] Test snapshot capture with fake connection
  - [x] Test camera profile switching
  - [x] Test thermal settings (temp range, palette, hotspot detection)
  - [x] Test status property updates
  - [x] Test signal emissions
  - [x] Test error handling and fallback behavior
  - [x] Ensure all tests are hardware-free (no real MAVLink, no ROS2, no SITL)

### Phase 2: Capability Registry ⏱️ Week 3

- [x] **2.1** Create `skymeshx/models/capabilities.py`
  - [x] Define `DroneCapabilities` dataclass with fields:
    - [x] `has_camera: bool`
    - [x] `has_thermal_camera: bool`
    - [x] `has_gimbal: bool`
    - [x] `has_dispenser: bool`
    - [x] `camera_resolution: Optional[tuple]`
    - [x] `camera_fov: Optional[tuple]`
    - [x] `gimbal_axes: List[str]`
    - [x] `dispenser_type: Optional[str]`
  - [x] Implement `check_mode_requirements(mode: str, capabilities: DroneCapabilities) -> dict`
    - [x] Return dict with `{"satisfied": bool, "missing": List[str], "warnings": List[str]}`
  - [x] Define mode requirements:
    - [x] Solar inspection: camera + gimbal (thermal optional but recommended)
    - [x] Seeding: dispenser + GPS (camera optional)
    - [x] Mapping: camera (gimbal optional)
  - [x] Add capability detection from MAVLink autopilot capabilities
  - [x] Add manual capability override for testing

- [x] **2.2** Create `tests/test_capability_registry.py`
  - [x] Test capability detection from fake autopilot
  - [x] Test mode requirement checking for solar inspection
  - [x] Test mode requirement checking for seeding
  - [x] Test mode requirement checking for mapping
  - [x] Test warning generation for missing optional capabilities
  - [x] Test error generation for missing required capabilities
  - [x] Ensure all tests are hardware-free

### Phase 3: Solar Inspection Backend ⏱️ Week 4-5

- [x] **3.1** Extend `skymeshx/control/solar_inspection.py`
  - [x] Add `generate_solar_mission_with_preview()` method
  - [x] Return preview data structure with:
    - [x] Waypoint list with coordinates
    - [x] Camera trigger points
    - [x] Gimbal angle at each trigger point
    - [x] Camera footprint polygons
    - [x] Estimated duration
    - [x] Battery usage estimate
  - [x] Add `validate_solar_mission()` method
    - [x] Check row spacing vs camera FOV
    - [x] Check altitude vs ground sample distance (GSD)
    - [x] Check battery capacity vs mission duration
    - [x] Return validation result with warnings
  - [x] Add thermal camera integration hooks
  - [x] Ensure hardware-free operation with mock data

- [x] **3.2** Update `tests/test_solar_inspection.py`
  - [x] Test mission generation with preview data
  - [x] Test validation logic for various configurations
  - [x] Test camera trigger point calculation
  - [x] Test footprint polygon generation
  - [x] Test thermal camera integration
  - [x] Ensure all tests are hardware-free

### Phase 4: Seeding Backend ⏱️ Week 6-7

- [x] **4.1** Extend `skymeshx/control/seeding_planner.py`
  - [x] Add `generate_seeding_mission_with_preview()` method
  - [x] Return preview data structure with:
    - [x] Flight path with rows
    - [x] Drop points with seed count
    - [x] Exclusion zones
    - [x] Estimated seed usage
    - [x] Estimated duration
    - [x] Battery usage estimate
  - [x] Add `validate_seeding_mission()` method
    - [x] Check seed density vs dispenser capacity
    - [x] Check field area vs tank capacity
    - [x] Check flight speed vs dispenser rate
    - [x] Return validation result with warnings
  - [x] Add dispenser calibration data structure
  - [x] Ensure hardware-free operation with mock data

- [x] **4.2** Update `tests/test_seeding_planner.py`
  - [x] Test mission generation with preview data
  - [x] Test validation logic for various configurations
  - [x] Test drop point calculation
  - [x] Test seed usage estimation
  - [x] Test dispenser calibration integration
  - [x] Ensure all tests are hardware-free

### Phase 5: Mission Context Safety Review ⏱️ Week 8

- [x] **5.1** Review `tools/ui/context/mission_context.py`
  - [x] Document current upload/execute behavior in feedback file
  - [x] Identify auto-execute paths (if any)
  - [x] Propose separation of upload and execute
  - [x] Wait for Bob's feedback before making changes
  - [x] Implement agreed changes to ensure upload does NOT auto-execute
  - [x] `execute_mission()` not needed — `startMission()` already exists
  - [x] Tests verified (70/70 passing after changes)

### Phase 6: Integration & Polish ⏱️ Week 9

- [ ] **6.1** Integration testing
  - [x] Add mission control worker tests for explicit Start/Pause/Abort
  - [x] Add MapView JS performance fixes for waypoint diffing, drone icon caching, and solar SVG trigger icons
  - [x] Fix Seeding/Solar wizard upload flow so Upload calls backend and Start is blocked without a successful upload
  - [x] Clip coverage/seeding parallel lines to the drawn polygon and improve large seeding-point map rendering
  - [ ] Test camera context with backend integration
  - [ ] Test capability registry with mission contexts
  - [ ] Test solar inspection end-to-end (hardware-free)
  - [ ] Test seeding end-to-end (hardware-free)
  - [ ] Fix any integration issues

- [ ] **6.2** Documentation
  - [x] Document camera context API in `docs/api/`
  - [ ] Document capability registry in `docs/api/`
  - [ ] Update `AGENTS.md` with new patterns
  - [ ] Write usage examples

---

## 🎨 Bob Tasks (QML UI & Wizards)

### Phase 1: Camera & Gimbal Control UI ⏱️ Week 1-2

- [x] **1.1** Extend `tools/ui/qml/panels/GimbalPanel.qml`
  - [x] Add camera source selection dropdown
    - [x] List available camera sources from `camera.availableSources`
    - [x] Show current source with indicator
  - [x] Add stream controls section
    - [x] "Start Stream" button → calls `camera.cameraStartStream(source)`
    - [x] "Stop Stream" button → calls `camera.cameraStopStream()`
    - [x] Stream status indicator (active/inactive)
  - [x] Add snapshot controls
    - [x] "Capture Snapshot" button → calls `camera.cameraSnapshot()`
    - [x] Show last snapshot timestamp
  - [x] Add recording controls
    - [x] "Start Recording" button → calls `camera.cameraStartRecording(path)`
    - [x] "Stop Recording" button → calls `camera.cameraStopRecording()`
    - [x] Recording indicator (red dot when active)
    - [x] Recording duration display
  - [x] Add camera settings section
    - [x] Resolution dropdown
    - [x] FPS slider
    - [x] Camera profile selection
  - [x] Add thermal settings section (conditional on thermal camera)
    - [x] Temperature range sliders (min/max °C)
    - [x] Color palette dropdown (Iron, Rainbow, Grayscale, etc.)
    - [x] Hotspot detection toggle
    - [x] Hotspot threshold slider
  - [x] Add camera status display
    - [x] Frame age indicator
    - [x] Dropped frames counter
    - [x] Stream health indicator
    - [x] Last error message display
  - [x] Connect all controls to `camera` QML context
  - [x] Add tooltips and help text
  - [x] Test with mock camera context

- [x] **1.2** Document API needs in feedback file
  - [x] List any missing properties from camera context
  - [x] List any missing slots/methods
  - [x] List any data format issues
  - [x] Request any additional signals needed

### Phase 2: Solar Inspection Wizard ⏱️ Week 3-4

- [x] **2.1** Create `tools/ui/qml/panels/SolarInspectionPanel.qml`
  - [x] Implement wizard step navigation (4 steps)
  - [x] Add circular step progress indicator with ✓ for completed steps

- [x] **2.2** Step 1: Setup
  - [x] Add mode description text
  - [x] Add required hardware checklist (Camera/Gimbal/Thermal each with live status indicator)
  - [x] Add capability check using `capabilities.checkModeRequirements("solar")`
  - [x] Show warnings for missing optional hardware (capability warnings list)
  - [x] Show errors for missing required hardware (missing capabilities list)
  - [x] "Next" button disabled when `!capabilitiesSatisfied`

- [x] **2.3** Step 2: Site Definition
  - [x] Add "Draw on Map" button → `mission.startDrawingSolarRows()` + switches to map tab
  - [x] Add "Clear" button → `mission.clearSolarRows()`
  - [x] Display row count ("Rows drawn: N")
  - [x] Add row spacing input (meters) — in Step 3
  - [x] Add panel orientation dropdown — in Step 3
  - [x] "Back" and "Next" buttons

- [x] **2.4** Step 3: Flight & Camera Settings
  - [x] Add altitude slider (10–120 m AGL)
  - [x] Add speed slider (1–15 m/s)
  - [x] Add camera angle slider (-90° to 0°)
  - [x] Add trigger mode dropdown (Distance/Time/Waypoint)
  - [x] Add trigger interval slider (adapts unit: m or s)
  - [x] Add forward overlap slider (50–90%)
  - [x] Add side overlap slider (40–80%)
  - [x] Show calculated GSD (cm/px)
  - [x] Show calculated coverage width/height/area per image
  - [x] "Back" and "Next" buttons

- [x] **2.5** Step 4: Preview & Upload
  - [x] Auto-generates preview on step entry (`Component.onCompleted`)
  - [x] "Generate Preview" button as manual fallback
  - [x] Loading indicator while generating
  - [x] Display mission summary (waypoints, images, duration, battery, storage, coverage area)
  - [x] Show validation warnings from preview data
  - [x] Show preview error message
  - [x] Map overlays updated via `solarPreviewChanged` signal in `main.qml`
  - [x] "Upload Mission" button (enabled only when `previewData.valid`)
  - [x] Upload progress indicator
  - [x] Clarify that upload does NOT start mission automatically (info box)
  - [ ] Per-layer map overlay toggle buttons (overlays work via signal, no toggle UI yet)

- [x] **2.6** Integrate with `tools/ui/qml/panels/MissionPanel.qml`
  - [x] "Solar" mode button present in mode selector
  - [x] `SolarInspectionPanel` loaded via `Loader` when solar mode selected
  - [x] Old solar UI hidden (visible: false, replaced)
  - [x] Handle mode switching and cleanup via `Component.onDestruction`

### Phase 3: Seeding Wizard ⏱️ Week 5-6

- [x] **3.1** Create `tools/ui/qml/panels/SeedingPanel.qml`
  - [x] Implement wizard step navigation (6 steps)
  - [x] Add progress indicator showing current step
  - [x] Define all configuration properties
  - [x] Implement navigation buttons (Back/Next/Upload/Start)
  - [x] All 6 step components implemented (not placeholders)

- [x] **3.2** Step 1: Field Definition
  - [x] Add "Draw Field Boundary" button → `mission.startDrawingBoundary()`
  - [x] Activates map drawing mode + switches to map tab
  - [x] Add "Clear Boundary" button → `mission.clearBoundary()`
  - [x] Add "Draw Exclusion Zones" button → `mission.startDrawingExclusionZone()`
  - [x] Display exclusion zones on map (via map overlay signal)
  - [x] Show calculated field area (live from `fieldArea` property)
  - [x] Show exclusion zone count
  - [x] "Next" button in footer navigation

- [x] **3.3** Step 2: Crop & Seed Configuration
  - [x] Add crop type dropdown (Wheat/Corn/Rice/Soybean/Barley/Oats/Custom)
  - [x] Add seed type text input
  - [x] Add seed spacing slider (1–600 m) — density auto-calculated
  - [x] Add seed weight slider (0.01–0.5 g/seed)
  - [x] Show calculated total seeds needed
  - [x] Show calculated total weight needed
  - [x] "Back" and "Next" buttons

- [x] **3.4** Step 3: Dispenser Configuration
  - [x] Add dispenser type dropdown (Pneumatic/Gravity/Centrifugal/Auger)
  - [x] Add tank capacity slider (1000–20000 g)
  - [x] Add dispenser rate slider (1–50 seeds/s)
  - [x] Add "Run Calibration Test" button (sets `dispenserCalibrated = true`)
  - [x] Show calibrated status indicator
  - [x] Show tank refill warning when totalWeightNeeded > dispenserCapacity
  - [x] "Back" and "Next" buttons

- [x] **3.5** Step 4: Flight Parameters
  - [x] Add altitude slider (2–20 m AGL)
  - [x] Add speed slider (1–10 m/s)
  - [x] Add row spacing slider (5–30 m)
  - [x] Add flight direction dropdown (Auto/North-South/East-West/Custom)
  - [x] Show calculated number of rows
  - [x] Show calculated flight distance
  - [x] "Back" and "Next" buttons

- [x] **3.6** Step 5: Preview & Upload
  - [x] "Generate Preview" button → `mission.generateSeedingPreview(params)`
  - [x] Display mission summary (waypoints, drop points, duration, battery)
  - [x] Show validation warnings from preview data
  - [x] Show preview error message
  - [x] Map overlays updated via `seedingPreviewChanged` signal in `main.qml`
  - [x] "Upload Mission" button (calls `uploadMission()`)
  - [x] Upload progress indicator
  - [x] Clarify that upload does NOT start mission automatically (info box)
  - [ ] Display flight path + drop points + exclusion zones as map overlay toggles (map overlay toggle buttons missing — overlays work via signal but no per-layer toggle UI)

- [x] **3.7** Step 6: Execution & Monitoring
  - [x] "Start Mission" button → `mission.startMission()` (in footer nav)
  - [x] Mission progress bar (UI present, wired to static 0% — live data needs backend signal)
  - [x] Show seeds dispensed counter (static placeholder — needs live backend signal)
  - [x] Show remaining seed capacity
  - [x] "Pause Mission" button → `mission.pauseMission()`
  - [x] Abort Mission button → `mission.abortMission()` + resets wizard
  - [ ] Show current waypoint / total waypoints (not yet wired to backend signal)
  - [ ] Show real-time drop points on map (not yet wired)

- [x] **3.8** Integrate with `tools/ui/qml/panels/MissionPanel.qml`
  - [x] "Seeding" mode button present in mode selector
  - [x] `SeedingPanel` loaded via `Loader` when seeding mode selected
  - [x] Old seeding UI hidden (`visible: false`)
  - [x] Handle mode switching and cleanup via `Component.onDestruction`

### Phase 4: Map Overlays ⏱️ Week 7

- [x] **4.1** Extend `tools/ui/qml/MapView.qml`
  - [x] Remove external CDN/tile dependency from startup map path
  - [x] Make local map engine the primary renderer
  - [x] Fix local engine JavaScript string syntax that caused `Unexpected identifier 'width'`
  - [x] Render local markers, polylines, and circles for offline overlays
  - [x] Add exclusion zone overlay (red dashed polygons with point markers)
  - [x] Add seeding drop points overlay → `drawSeedingMission()` / `clearSeedingMission()`
  - [x] Add seeding flight rows overlay (polylines from preview data)
  - [x] Add solar trigger points overlay → `drawSolarPreview()` / `clearSolarPreviewOverlays()`
  - [x] Add solar camera footprint overlay (polygons from preview data)
  - [x] Add solar mission rows overlay (polylines from preview data)
  - [x] Overlays update automatically via `seedingPreviewChanged` / `solarPreviewChanged` signals in `main.qml`
  - [ ] Per-layer overlay toggle controls (no toggle UI yet — all layers always visible)
  - [ ] Seeding row direction arrows (lines present, no arrow decoration)
  - [ ] Solar trigger point camera icons (plain markers used instead)

### Phase 5: Main QML Integration ⏱️ Week 8

- [x] **5.1** Update `tools/ui/qml/main.qml`
  - [x] Camera context properly exposed (`camera` QML context)
  - [x] Capability context properly exposed (`capabilities` QML context)
  - [x] `seedingPreviewChanged` → `syncSeedingPreviewToMap()` wired
  - [x] `solarPreviewChanged` → `syncSolarPreviewToMap()` wired
  - [ ] ESC key handling for wizard cancellation (not implemented)
  - [ ] Map mode mutex test (mode switching tested but not formally verified)

### Phase 6: Testing & Polish ⏱️ Week 9

- [ ] **6.1** UI testing
  - [x] Add backend signal/getter tests for seeding preview map flow
  - [x] Add backend signal/getter tests for solar preview map flow
  - [x] Add capability context nested QVariantMap shape test for Solar QML
  - [ ] Test camera controls with mock backend
  - [ ] Test solar wizard end-to-end
  - [ ] Test seeding wizard end-to-end
  - [ ] Test map overlays with sample data
  - [ ] Test error handling and user feedback
  - [ ] Test mode switching and cleanup

- [ ] **6.2** User experience polish
  - [ ] Add loading indicators where needed
  - [ ] Add confirmation dialogs for destructive actions
  - [ ] Add tooltips for all controls
  - [ ] Add help text for wizard steps
  - [ ] Ensure consistent styling
  - [ ] Test with different screen sizes

- [ ] **6.3** Documentation
  - [ ] Document UI workflows in `docs/`
  - [ ] Create user guide for solar inspection
  - [ ] Create user guide for seeding
  - [ ] Add screenshots to documentation

---

## 🔄 Shared Coordination Tasks

### Feedback File Management

- [ ] **Codex:** Create initial feedback file with API contract
- [ ] **Bob:** Review API contract and request changes if needed
- [ ] **Codex:** Implement API changes based on feedback
- [ ] **Bob:** Confirm API changes work as expected
- [ ] **Both:** Document any blockers immediately
- [ ] **Both:** Review mission context upload/execute separation together
- [ ] **Both:** Agree on final behavior before implementation

### Integration Points

- [x] **Codex:** Expose camera context to QML with documented properties/slots
- [x] **Bob:** Camera/Gimbal UI implemented and wired to `camera` context
- [x] **Codex:** Expose capability context to QML
- [x] **Bob:** Capability checks in Solar wizard (Step 1 hardware checklist)
- [x] **Codex:** Provide preview data format for solar missions
- [x] **Bob:** Solar preview display implemented (Step 4 + map overlays)
- [x] **Codex:** Provide preview data format for seeding missions
- [x] **Bob:** Seeding preview display implemented (Step 5 + map overlays)

---

## 📊 Progress Tracking

### Week 1-2: Foundation
- **Codex:** Camera context + tests
- **Bob:** Camera UI controls

### Week 3-4: Capabilities & Solar UI
- **Codex:** Capability registry + tests
- **Bob:** Solar inspection wizard

### Week 5-6: Seeding
- **Codex:** Seeding backend extensions
- **Bob:** Seeding wizard

### Week 7-8: Integration
- **Codex:** Mission context review + solar backend
- **Bob:** Map overlays + main integration

### Week 9: Testing & Polish
- **Both:** Integration testing, bug fixes, documentation

---

## ✅ Definition of Done

### For Codex:
- [ ] All backend code has hardware-free unit tests
- [ ] All tests pass in CI
- [ ] API contracts documented in feedback file
- [ ] No auto-execute behavior after mission upload
- [ ] Camera context works with and without real hardware
- [ ] Capability registry correctly identifies missing hardware

### For Bob:
- [ ] All UI components render correctly
- [ ] All wizards complete end-to-end without errors
- [ ] Map overlays display correctly
- [ ] User can cancel any wizard at any step
- [ ] Clear indication of what will happen after upload
- [ ] Warnings shown for missing optional hardware
- [ ] Errors shown for missing required hardware

### For Both:
- [ ] No simultaneous edits to same files
- [ ] All coordination documented in feedback file
- [ ] Integration tests pass
- [ ] User documentation complete
- [ ] Code review completed

---

## 🚨 Critical Rules

1. **Upload ≠ Execute** - Mission upload must NEVER auto-start the mission
2. **Hardware-Free Tests** - All tests must work without MAVLink, ROS2, SITL, or real cameras
3. **Show Warnings, Don't Hide** - Missing hardware shows warnings, doesn't hide modes
4. **Document Before Edit** - Write feedback entry before touching shared files
5. **API First** - Define interfaces before implementation
6. **Test Everything** - No code without tests
7. **User Clarity** - User must always know what will happen next

---

## 📝 Next Steps

1. **Codex:** Create feedback file and document initial camera context API
2. **Bob:** Review API and request any changes needed
3. **Both:** Begin Phase 1 tasks in parallel
4. **Both:** Update feedback file daily with progress and blockers
