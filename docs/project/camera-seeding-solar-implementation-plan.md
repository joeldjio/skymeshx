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

- [ ] **1.1** Create `tools/ui/context/camera_context.py`
  - [ ] Implement `CameraContext` class inheriting from `QObject`
  - [ ] Add QML-facing slots: `cameraStartStream()`, `cameraStopStream()`, `cameraSnapshot()`
  - [ ] Add QML-facing slots: `cameraStartRecording()`, `cameraStopRecording()`
  - [ ] Add QML-facing slots: `setCameraProfile()`, `getCameraStatus()`
  - [ ] Add QML-facing slots: `setTempRange()`, `setColorPalette()`, `setHotspotDetection()`
  - [ ] Implement Qt properties: `currentSource`, `streamActive`, `recordingActive`
  - [ ] Implement Qt properties: `recordingDuration`, `frameAge`, `droppedFrames`
  - [ ] Implement Qt properties: `currentProfile`, `lastError`
  - [ ] Implement Qt signals: `streamStarted`, `streamStopped`, `recordingStarted`, `recordingStopped`
  - [ ] Implement Qt signals: `snapshotCaptured`, `errorOccurred`, `statusChanged`
  - [ ] Add hardware-free fallback behavior (mock mode when no camera available)
  - [ ] Document API contract in feedback file

- [ ] **1.2** Extend `tools/ui/backend.py` for camera delegation
  - [ ] Add `get_camera_context()` method to return `CameraContext` instance
  - [ ] Add camera stream routing to selected observation drone
  - [ ] Add recording control delegation
  - [ ] Add snapshot capture delegation
  - [ ] Add camera/gimbal health status aggregation
  - [ ] Ensure hardware-free operation when no camera backend available

- [ ] **1.3** Extend `skymeshx/models/observation_uav.py`
  - [ ] Add `start_camera_stream(source: str) -> bool` method
  - [ ] Add `stop_camera_stream() -> bool` method
  - [ ] Add `capture_snapshot() -> bool` method
  - [ ] Add `start_recording(path: str) -> bool` method
  - [ ] Add `stop_recording() -> bool` method
  - [ ] Add `get_camera_status() -> dict` method
  - [ ] Add `get_gimbal_status() -> dict` method
  - [ ] Add MAVLink command mapping for camera control
  - [ ] Add hardware-free mock responses

- [ ] **1.4** Register camera context in `tools/ui/service_locator.py`
  - [ ] Document change in feedback file BEFORE editing
  - [ ] Add `camera` context registration
  - [ ] Ensure proper initialization order
  - [ ] Add cleanup on shutdown

- [ ] **1.5** Create `tests/test_camera_context.py`
  - [ ] Test stream start/stop with fake connection
  - [ ] Test recording start/stop with fake connection
  - [ ] Test snapshot capture with fake connection
  - [ ] Test camera profile switching
  - [ ] Test thermal settings (temp range, palette, hotspot detection)
  - [ ] Test status property updates
  - [ ] Test signal emissions
  - [ ] Test error handling and fallback behavior
  - [ ] Ensure all tests are hardware-free (no real MAVLink, no ROS2, no SITL)

### Phase 2: Capability Registry ⏱️ Week 3

- [ ] **2.1** Create `skymeshx/models/capabilities.py`
  - [ ] Define `DroneCapabilities` dataclass with fields:
    - [ ] `has_camera: bool`
    - [ ] `has_thermal_camera: bool`
    - [ ] `has_gimbal: bool`
    - [ ] `has_dispenser: bool`
    - [ ] `camera_resolution: Optional[tuple]`
    - [ ] `camera_fov: Optional[tuple]`
    - [ ] `gimbal_axes: List[str]`
    - [ ] `dispenser_type: Optional[str]`
  - [ ] Implement `check_mode_requirements(mode: str, capabilities: DroneCapabilities) -> dict`
    - [ ] Return dict with `{"satisfied": bool, "missing": List[str], "warnings": List[str]}`
  - [ ] Define mode requirements:
    - [ ] Solar inspection: camera + gimbal (thermal optional but recommended)
    - [ ] Seeding: dispenser + GPS (camera optional)
    - [ ] Mapping: camera (gimbal optional)
  - [ ] Add capability detection from MAVLink autopilot capabilities
  - [ ] Add manual capability override for testing

- [ ] **2.2** Create `tests/test_capability_registry.py`
  - [ ] Test capability detection from fake autopilot
  - [ ] Test mode requirement checking for solar inspection
  - [ ] Test mode requirement checking for seeding
  - [ ] Test mode requirement checking for mapping
  - [ ] Test warning generation for missing optional capabilities
  - [ ] Test error generation for missing required capabilities
  - [ ] Ensure all tests are hardware-free

### Phase 3: Solar Inspection Backend ⏱️ Week 4-5

- [ ] **3.1** Extend `skymeshx/control/solar_inspection.py`
  - [ ] Add `generate_solar_mission_with_preview()` method
  - [ ] Return preview data structure with:
    - [ ] Waypoint list with coordinates
    - [ ] Camera trigger points
    - [ ] Gimbal angle at each trigger point
    - [ ] Camera footprint polygons
    - [ ] Estimated duration
    - [ ] Battery usage estimate
  - [ ] Add `validate_solar_mission()` method
    - [ ] Check row spacing vs camera FOV
    - [ ] Check altitude vs ground sample distance (GSD)
    - [ ] Check battery capacity vs mission duration
    - [ ] Return validation result with warnings
  - [ ] Add thermal camera integration hooks
  - [ ] Ensure hardware-free operation with mock data

- [ ] **3.2** Update `tests/test_solar_inspection.py`
  - [ ] Test mission generation with preview data
  - [ ] Test validation logic for various configurations
  - [ ] Test camera trigger point calculation
  - [ ] Test footprint polygon generation
  - [ ] Test thermal camera integration
  - [ ] Ensure all tests are hardware-free

### Phase 4: Seeding Backend ⏱️ Week 6-7

- [ ] **4.1** Extend `skymeshx/control/seeding_planner.py`
  - [ ] Add `generate_seeding_mission_with_preview()` method
  - [ ] Return preview data structure with:
    - [ ] Flight path with rows
    - [ ] Drop points with seed count
    - [ ] Exclusion zones
    - [ ] Estimated seed usage
    - [ ] Estimated duration
    - [ ] Battery usage estimate
  - [ ] Add `validate_seeding_mission()` method
    - [ ] Check seed density vs dispenser capacity
    - [ ] Check field area vs tank capacity
    - [ ] Check flight speed vs dispenser rate
    - [ ] Return validation result with warnings
  - [ ] Add dispenser calibration data structure
  - [ ] Ensure hardware-free operation with mock data

- [ ] **4.2** Update `tests/test_seeding_planner.py`
  - [ ] Test mission generation with preview data
  - [ ] Test validation logic for various configurations
  - [ ] Test drop point calculation
  - [ ] Test seed usage estimation
  - [ ] Test dispenser calibration integration
  - [ ] Ensure all tests are hardware-free

### Phase 5: Mission Context Safety Review ⏱️ Week 8

- [ ] **5.1** Review `tools/ui/context/mission_context.py`
  - [ ] Document current upload/execute behavior in feedback file
  - [ ] Identify auto-execute paths (if any)
  - [ ] Propose separation of upload and execute
  - [ ] Wait for Bob's feedback before making changes
  - [ ] Implement agreed changes to ensure upload does NOT auto-execute
  - [ ] Add explicit `execute_mission()` method if needed
  - [ ] Update tests to verify new behavior

### Phase 6: Integration & Polish ⏱️ Week 9

- [ ] **6.1** Integration testing
  - [ ] Test camera context with backend integration
  - [ ] Test capability registry with mission contexts
  - [ ] Test solar inspection end-to-end (hardware-free)
  - [ ] Test seeding end-to-end (hardware-free)
  - [ ] Fix any integration issues

- [ ] **6.2** Documentation
  - [ ] Document camera context API in `docs/api/`
  - [ ] Document capability registry in `docs/api/`
  - [ ] Update `AGENTS.md` with new patterns
  - [ ] Write usage examples

---

## 🎨 Bob Tasks (QML UI & Wizards)

### Phase 1: Camera & Gimbal Control UI ⏱️ Week 1-2

- [ ] **1.1** Extend `tools/ui/qml/panels/GimbalPanel.qml`
  - [ ] Add camera source selection dropdown
    - [ ] List available camera sources from `camera.availableSources`
    - [ ] Show current source with indicator
  - [ ] Add stream controls section
    - [ ] "Start Stream" button → calls `camera.cameraStartStream(source)`
    - [ ] "Stop Stream" button → calls `camera.cameraStopStream()`
    - [ ] Stream status indicator (active/inactive)
  - [ ] Add snapshot controls
    - [ ] "Capture Snapshot" button → calls `camera.cameraSnapshot()`
    - [ ] Show last snapshot timestamp
  - [ ] Add recording controls
    - [ ] "Start Recording" button → calls `camera.cameraStartRecording(path)`
    - [ ] "Stop Recording" button → calls `camera.cameraStopRecording()`
    - [ ] Recording indicator (red dot when active)
    - [ ] Recording duration display
  - [ ] Add camera settings section
    - [ ] Resolution dropdown
    - [ ] FPS slider
    - [ ] Camera profile selection
  - [ ] Add thermal settings section (conditional on thermal camera)
    - [ ] Temperature range sliders (min/max °C)
    - [ ] Color palette dropdown (Iron, Rainbow, Grayscale, etc.)
    - [ ] Hotspot detection toggle
    - [ ] Hotspot threshold slider
  - [ ] Add camera status display
    - [ ] Frame age indicator
    - [ ] Dropped frames counter
    - [ ] Stream health indicator
    - [ ] Last error message display
  - [ ] Connect all controls to `camera` QML context
  - [ ] Add tooltips and help text
  - [ ] Test with mock camera context

- [ ] **1.2** Document API needs in feedback file
  - [ ] List any missing properties from camera context
  - [ ] List any missing slots/methods
  - [ ] List any data format issues
  - [ ] Request any additional signals needed

### Phase 2: Solar Inspection Wizard ⏱️ Week 3-4

- [ ] **2.1** Create `tools/ui/qml/panels/SolarInspectionPanel.qml`
  - [ ] Implement wizard step navigation (4 steps)
  - [ ] Add progress indicator showing current step

- [ ] **2.2** Step 1: Setup
  - [ ] Add mode description text
  - [ ] Add required hardware checklist
    - [ ] Camera (required)
    - [ ] Gimbal (required)
    - [ ] Thermal camera (optional, show warning if missing)
  - [ ] Add capability check using `capabilities.checkModeRequirements("solar")`
  - [ ] Show warnings for missing optional hardware
  - [ ] Show errors for missing required hardware
  - [ ] "Next" button (disabled if required hardware missing)

- [ ] **2.3** Step 2: Site Definition
  - [ ] Add "Draw Solar Rows" button
    - [ ] Activates map drawing mode
    - [ ] Shows instructions overlay
  - [ ] Display drawn rows on map as list
  - [ ] Add row spacing input (meters)
  - [ ] Add panel orientation dropdown (portrait/landscape)
  - [ ] Add "Clear Rows" button
  - [ ] "Back" and "Next" buttons

- [ ] **2.4** Step 3: Flight & Camera Settings
  - [ ] Add altitude slider (meters AGL)
  - [ ] Add speed slider (m/s)
  - [ ] Add camera angle slider (degrees from nadir)
  - [ ] Add trigger mode dropdown (distance/time/waypoint)
  - [ ] Add trigger interval input (meters or seconds)
  - [ ] Add overlap percentage slider (forward/side)
  - [ ] Show calculated GSD (ground sample distance)
  - [ ] Show calculated coverage area per image
  - [ ] "Back" and "Next" buttons

- [ ] **2.5** Step 4: Preview & Upload
  - [ ] Request preview data from backend
  - [ ] Display mission summary:
    - [ ] Total waypoints
    - [ ] Total images to capture
    - [ ] Estimated duration
    - [ ] Estimated battery usage
    - [ ] Required storage space
  - [ ] Show validation warnings (if any)
  - [ ] Display flight path on map with camera footprints
  - [ ] Display camera trigger points as markers
  - [ ] Add "Upload Mission" button
  - [ ] Add "Cancel" button
  - [ ] Show upload progress
  - [ ] Show success/error message after upload
  - [ ] Clarify that upload does NOT start mission automatically

- [ ] **2.6** Integrate with `tools/ui/qml/panels/MissionPanel.qml`
  - [ ] Add "Solar Inspection" mode button
  - [ ] Open `SolarInspectionPanel` when selected
  - [ ] Handle mode switching and cleanup

### Phase 3: Seeding Wizard ⏱️ Week 5-6

- [ ] **3.1** Create `tools/ui/qml/panels/SeedingPanel.qml`
  - [ ] Implement wizard step navigation (6 steps)
  - [ ] Add progress indicator showing current step

- [ ] **3.2** Step 1: Field Definition
  - [ ] Add "Draw Field Boundary" button
    - [ ] Activates map drawing mode
    - [ ] Shows instructions overlay
  - [ ] Display drawn boundary on map
  - [ ] Add "Draw Exclusion Zones" button
  - [ ] Display exclusion zones on map
  - [ ] Show calculated field area
  - [ ] "Next" button

- [ ] **3.3** Step 2: Crop & Seed Configuration
  - [ ] Add crop type dropdown
  - [ ] Add seed type input
  - [ ] Add target seed density input (seeds/m²)
  - [ ] Add seed weight input (grams per seed)
  - [ ] Show calculated total seeds needed
  - [ ] Show calculated total weight needed
  - [ ] "Back" and "Next" buttons

- [ ] **3.4** Step 3: Dispenser Configuration
  - [ ] Add dispenser type dropdown
  - [ ] Add dispenser capacity input (grams or seeds)
  - [ ] Add dispenser rate input (seeds/second)
  - [ ] Add "Run Bench Test" button
    - [ ] Opens dispenser test dialog
    - [ ] Allows manual trigger testing
    - [ ] Records actual dispense rate
  - [ ] Add calibration data display
  - [ ] Show tank refill warnings if needed
  - [ ] "Back" and "Next" buttons

- [ ] **3.5** Step 4: Flight Parameters
  - [ ] Add altitude slider (meters AGL)
  - [ ] Add speed slider (m/s)
  - [ ] Add row spacing input (meters)
  - [ ] Add flight direction dropdown (N-S, E-W, auto)
  - [ ] Show calculated number of rows
  - [ ] Show calculated flight distance
  - [ ] "Back" and "Next" buttons

- [ ] **3.6** Step 5: Preview & Upload
  - [ ] Request preview data from backend
  - [ ] Display mission summary:
    - [ ] Total waypoints
    - [ ] Total drop points
    - [ ] Estimated duration
    - [ ] Estimated battery usage
    - [ ] Seed usage vs capacity
  - [ ] Show validation warnings (if any)
  - [ ] Display flight path on map with rows
  - [ ] Display drop points as markers
  - [ ] Display exclusion zones
  - [ ] Add "Upload Mission" button
  - [ ] Add "Cancel" button
  - [ ] Show upload progress
  - [ ] Show success/error message after upload
  - [ ] Clarify that upload does NOT start mission automatically

- [ ] **3.7** Step 6: Execution & Monitoring
  - [ ] Add "Start Mission" button (explicit execution)
  - [ ] Show mission progress bar
  - [ ] Show current waypoint / total waypoints
  - [ ] Show seeds dispensed counter
  - [ ] Show remaining seed capacity
  - [ ] Add "Pause Mission" button
  - [ ] Add "Abort Mission" button
  - [ ] Show real-time drop points on map

- [ ] **3.8** Integrate with `tools/ui/qml/panels/MissionPanel.qml`
  - [ ] Add "Seeding" mode button
  - [ ] Open `SeedingPanel` when selected
  - [ ] Handle mode switching and cleanup

### Phase 4: Map Overlays ⏱️ Week 7

- [ ] **4.1** Extend `tools/ui/qml/MapView.qml`
  - [ ] Add solar row overlay layer
    - [ ] Render rows as lines with labels
    - [ ] Show row spacing
  - [ ] Add solar trigger point overlay
    - [ ] Render trigger points as camera icons
    - [ ] Show camera footprint polygons
  - [ ] Add seeding row overlay
    - [ ] Render rows as lines with direction arrows
  - [ ] Add seeding drop point overlay
    - [ ] Render drop points as seed icons
    - [ ] Color code by status (planned/completed)
  - [ ] Add exclusion zone overlay
    - [ ] Render as red hatched polygons
  - [ ] Add mission preview path overlay
    - [ ] Render as dashed line with waypoint markers
  - [ ] Add overlay toggle controls
  - [ ] Ensure overlays update when mission data changes

### Phase 5: Main QML Integration ⏱️ Week 8

- [ ] **5.1** Update `tools/ui/qml/main.qml`
  - [ ] Verify camera context is properly exposed
  - [ ] Verify capability context is properly exposed
  - [ ] Test panel switching between modes
  - [ ] Test ESC key handling for wizard cancellation
  - [ ] Test map mode mutex with new wizards
  - [ ] Add any missing context connections

### Phase 6: Testing & Polish ⏱️ Week 9

- [ ] **6.1** UI testing
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

- [ ] **Codex:** Expose camera context to QML with documented properties/slots
- [ ] **Bob:** Test camera context integration and report issues
- [ ] **Codex:** Expose capability context to QML
- [ ] **Bob:** Test capability checks in wizards
- [ ] **Codex:** Provide preview data format for solar missions
- [ ] **Bob:** Implement preview display for solar missions
- [ ] **Codex:** Provide preview data format for seeding missions
- [ ] **Bob:** Implement preview display for seeding missions

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