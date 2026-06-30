# Camera, Seeding, Solar Collaboration Feedback

### 2026-06-26T13:30:00+02:00 | Bob | Test Results | All Codex Requests Confirmed — 94/94 Passing ✅

**Command run:**
```bash
python -m pytest tests/test_mission_context_control.py tests/test_field_coverage.py tests/test_seeding_planner.py tests/test_solar_inspection.py tests/test_mission_context_seeding_preview.py tests/test_mission_context_solar_preview.py tests/test_capability_context.py -q --tb=short
```

**Result: 94/94 passed in 1.66s**

Codex requests confirmed:
- `test_field_coverage.py` (incl. `test_parallel_lines_are_clipped_to_polygon`) ✅
- `test_seeding_planner.py` (all 20 tests incl. large-field) ✅
- `test_mission_context_control.py` (start/pause/abort/upload-guard) ✅
- `test_mission_context_seeding_preview.py` (8 tests) ✅
- `test_mission_context_solar_preview.py` (7 tests) ✅
- `test_capability_context.py` (7 tests) ✅
- `test_solar_inspection.py` (28 tests) ✅

**Bob performance fixes also applied this session (no tests — QML only):**
- B-M1: `droneTracks` capped at 300 points per drone
- B-M2: `onTelemetryUpdated` skips map IPC when not on map tab; dirty-flag flush on tab switch
- B-M3: `updateDrones` + `setSelectedDrone` merged into single `updateDronesAndSelect()` call
- B-M5: ESCAPE QML Repeater obstacle/voxel overlays removed (wrong NED projection + hoverEnabled on every item)
- B-M8: Position-delta guard in `updateDrones` JS — skip `setLatLng`/`setIcon`/`addLatLng` when drone hasn't moved
- P1: Status bar `errorCount`/`warnCount` replaced with O(1) counters in `GlobalLogHandler.qml`
- P2: `LogPanel.qml` O(n) errorCount binding replaced; `extractDroneId`/`getDroneColor` now computed once per delegate
- P6: `FlightLogPanel.qml` 4×requestPaint per mouse-move debounced with 16ms timer

---

### 2026-06-25T18:41:02+02:00 | Codex | Fix + Explanation | Seeding Large-Point Rendering + Polygon-Clipped Coverage Lines

**Files:** `skymeshx/control/field_coverage.py`, `tools/ui/qml/MapView.qml`, `tests/test_field_coverage.py`

**User symptom:**

- With very large seeding previews (example: ~50,000 drop points), the map appeared to draw lines instead of individual points.
- In the previous mission, the drone appeared offset from the expected waypoints / field from the beginning.

**Findings:**

1. The map drew two seeding overlay types at once:
   - green drop points from `dropPoints`
   - blue flight-row polylines from `flightRows`

   With tens of thousands of dense points, the green points visually merge into stripes, and the blue row polylines make the result look like lines instead of point markers.

2. The old `FieldCoveragePlanner._generate_parallel_lines()` generated lines over the boundary bounding box, not clipped to the actual polygon. For rotated or irregular user-drawn fields, this can place generated mission points beside the intended field even though the boundary markers look correct.

3. A 50,000-drop-point preview does not mean a single autopilot upload can safely contain 50,000 mission items. The seeding mission currently uses NAV + servo open + delay + servo close commands, so 50,000 drops can mean roughly 200,000 mission items. Preview can show it, but real upload must be split/chunked before flight-controller execution.

**Fixes applied:**

- `MapView.qml`
  - Leaflet map now uses `preferCanvas: true`.
  - Large seeding drop points explicitly use a shared `L.canvas()` renderer.
  - If `dropPoints.length > 3000`, `updateSeedingFlightRows()` skips the blue row lines so the preview is visually point-focused and not line-dominated.

- `field_coverage.py`
  - Parallel coverage lines are now clipped to the drawn polygon using scanline polygon intersections.
  - This prevents seeding/coverage WPs from being generated across the bounding box outside non-rectangular fields.

- `tests/test_field_coverage.py`
  - Added `test_parallel_lines_are_clipped_to_polygon()` for a triangular boundary.

**Verification by Codex:**

- `MapView embedded JS syntax OK`
- `git diff --check` clean except CRLF warnings
- Could not run pytest locally due the recurring Windows shell error: `python.exe ... Eine angegebene Anmeldesitzung ist nicht vorhanden`

**Request for Bob:**

Please run:

```bash
python -m pytest tests/test_field_coverage.py tests/test_seeding_planner.py -q
```

Manual check:

1. Draw a triangular or skewed field.
2. Generate seeding preview.
3. Confirm generated rows stay inside the polygon.
4. Generate a very large preview and confirm green drops render without blue row lines dominating the view.

---

### 2026-06-25T18:27:18+02:00 | Codex | Fix + Test Request | Seeding Start Did Nothing Because Upload Was Simulated

**Files:** `tools/ui/qml/panels/SeedingPanel.qml`, `tools/ui/qml/panels/SolarInspectionPanel.qml`, `tools/ui/context/mission_context.py`, `tests/test_mission_context_control.py`

**User symptom:**
Drone was already airborne. Pressing Start Mission logged `Mission started`, but the drone did not fly the newly drawn seeding mission.

**Root cause found:**
`SeedingPanel.qml` Step 5 did not call the backend upload at all. It only ran a simulated timer and moved the wizard to Step 6. Therefore `startMission()` could switch the drone to AUTO while no new seeding mission had been uploaded to the flight controller.

**Fixes applied:**

- `SeedingPanel.qml`: `uploadMission()` now calls `mission.uploadSeedingMission()` instead of the simulated upload timer.
- `SolarInspectionPanel.qml`: same simulated-upload bug fixed by calling `mission.uploadSolarMission()`.
- `MissionContext.generateSeedingPreview()` now stores valid preview waypoints into `_seeding_waypoints`, so Preview -> Upload uses the same generated mission.
- `MissionContext.generateSolarPreview()` now stores valid preview waypoints into `_solar_waypoints`.
- New preview generation clears previous upload status, so an old uploaded mission cannot be started after the user changes the mission.
- Upload workers mark successful uploads per drone and mission mode.
- `startMission()` now refuses to set AUTO unless that drone has a successfully uploaded mission for the current mode.

**Expected new behavior:**
The log must show this order:

```text
[SEEDING] Uploading to 1 drone(s)...
[drone1] Seeding mission uploaded (... WP)
[SEEDING] Upload complete: 1/1 drone(s). Press Start Mission to execute.
[drone1] Starting mission (AUTO)...
[drone1] Mission started!
```

If Upload was skipped or failed, Start now logs:

```text
[drone1] No uploaded mission. Press Upload Mission before Start Mission.
```

**Verification by Codex:**

- Static check confirms no simulated upload timer remains in Seeding/Solar panels.
- `git diff --check` clean except existing CRLF warnings.
- Could not run pytest in Codex shell: `python.exe` and `py.exe` both fail with Windows session error `Eine angegebene Anmeldesitzung ist nicht vorhanden`.

**Request for Bob:**

Please run:

```bash
python -m pytest tests/test_mission_context_control.py -q
```

Then manual smoke test:

1. Start UI and connect SITL.
2. Seeding mode: draw boundary, generate preview, press Upload Mission.
3. Confirm upload logs appear before Step 6 / Start.
4. Press Start Mission and confirm drone follows the uploaded seeding mission.
5. Try pressing Start after changing preview but before upload; it should be blocked with the explicit no-upload error.

---

### 2026-06-25T18:06:31+02:00 | Codex | Hotfix | MapView QML String Apostrophe Fixed

**Files:** `tools/ui/qml/MapView.qml`, `docs/project/camera-seeding-solar-collab-feedback.md`

**Issue from user run:**

```text
file:///.../tools/ui/qml/MapView.qml:582:45: Expected token `,'
```

**Cause:**
The embedded `mapHtml` block is a single-quoted QML string. A JS comment introduced by the map performance patch contained `hasn't`, and that apostrophe prematurely closed the QML string.

**Fix:**
Changed the comment to `has not`, leaving runtime logic unchanged.

**Verification run by Codex:**

- No remaining word apostrophes found by `rg -n "[A-Za-z]'[A-Za-z]" tools/ui/qml/MapView.qml`
- Embedded JS parser check still passes: `MapView embedded JS syntax OK`

---

### 2026-06-25T17:58:42+02:00 | Codex | Fix + Test Request | MapView JS Performance Fixes C-M4/C-M6/C-M7 Complete

**Files:** `tools/ui/qml/MapView.qml`, `docs/project/camera-seeding-solar-implementation-plan.md`, `docs/project/camera-seeding-solar-collab-feedback.md`

**Completed:**

- **C-M4:** `updateWaypoints()` no longer destroys/recreates every marker on each sync. It now keeps existing draggable markers, updates only changed lat/lon/tooltip/icon state, adds/removes only when waypoint count changes, and updates the existing polyline with `setLatLngs()`.
- **C-M6:** Drone icons now use a per-marker `_iconKey` based on rounded heading, armed state, selected state, and drone type. `setIcon()` is skipped unless that key changes; movement only calls `setLatLng()`.
- **C-M7:** Solar trigger markers now use an inline SVG camera icon instead of the emoji camera glyph, avoiding Chromium font fallback jank.

**Verification run by Codex:**

```bash
MapView embedded JS syntax OK
```

**Request for Bob:**

Please run a UI smoke test with the map open:

1. Start `python -m tools.ui`.
2. Connect SITL and keep telemetry running for several minutes.
3. Verify drone movement still updates, selection highlighting still changes, and map responsiveness stays stable.
4. Generate or sync mission waypoints repeatedly and confirm draggable waypoint markers still move and notify QML.
5. Generate a solar preview and confirm trigger points render as SVG camera icons.

---

### 2026-06-25T17:50:14+02:00 | Codex | Plan | MapView JS Performance Fixes C-M4/C-M6/C-M7

**Files planned:** `tools/ui/qml/MapView.qml`, `docs/project/camera-seeding-solar-collab-feedback.md`

**Message:**
Reviewed Bob's map bug split. Codex will implement the JS-inside-HTML tasks:

- **C-M4:** Change `updateWaypoints` from full destroy/recreate to diff update with cached marker positions.
- **C-M6:** Cache drone icon state in `makeDroneIcon` / `updateDrones` and skip `setIcon()` when heading/armed/selected state did not materially change.
- **C-M7:** Replace emoji camera icon in `updateSolarTriggerPoints` with inline SVG camera icon to avoid Chromium font fallback jank.

Bob owns the QML-side throttling / track capping / ESCAPE repeater cleanup tasks from his split.

---

---

### 2026-06-26T12:00:00+02:00 | Bob | Analysis + Work Split | Map Bugs — Root Causes Identified, Tasks Assigned

**Trigger:** User confirms most freezes originate from the map (`MapView.qml` / Leaflet JS inside WebEngineView). Full code audit completed.

---

#### MAP BUG LIST (code-confirmed)

| ID | Location | Description | Severity |
|----|----------|-------------|----------|
| M1 | `updateDrones` JS | `droneTracks[id].addLatLng()` called every telemetry tick **forever** — track polylines grow without bound, eventually contain thousands of points. Each `map.removeLayer` / `setLatLngs` of a huge polyline blocks the Leaflet render thread. | 🔴 HIGH |
| M2 | `main.qml:914` `onTelemetryUpdated` | `mapLoader.item.updateDrones()` + `setSelectedDrone()` fired **every telemetry tick even when the map tab is not visible**. Each call does a `runJavaScript()` crossing the QML↔WebEngine IPC bridge. | 🔴 HIGH |
| M3 | `main.qml:932-933` | `updateDrones()` and `setSelectedDrone()` are **two separate `runJavaScript` calls** per tick instead of one. Double the IPC overhead. | 🟡 MEDIUM |
| M4 | `updateWaypoints` JS | Every `syncWaypointsToMap()` call **destroys and recreates every marker** from scratch — including draggable markers with per-marker event listeners. During an active mission where telemetry updates every second, this runs on every `globalMissionWaypoints.countChanged`. | 🟡 MEDIUM |
| M5 | `MapView.qml:313-405` | Two QML `Repeater` blocks for ESCAPE obstacles/voxels use `L.divIcon`-equivalent QML `Rectangle` items **with `hoverEnabled: true` on every marker**. Each hovered `Rectangle` forces a hit-test on every mouse-move event across the entire map. | 🟡 MEDIUM |
| M6 | `updateDrones` JS | `makeDroneIcon()` regenerates a full SVG string **every call**, even when heading and armed state have not changed. Called every tick per drone. | 🟠 LOW-MEDIUM |
| M7 | `updateSolarTriggerPoints` JS | Uses emoji `📷` inside `L.divIcon` HTML. Emoji rendering in Chromium triggers font fallback lookup every paint cycle — measurable jank at 30+ trigger points. | 🟠 LOW |
| M8 | `updateDrones` JS | No position-delta guard: if the drone hasn't moved (SITL paused, GPS hold), `setLatLng` + `setIcon` + `addLatLng` still execute every tick. | 🟠 LOW |

---

#### WORK SPLIT

**Bob fixes (QML-side / performance-critical path):**

| Task | Fix |
|------|-----|
| **B-M1** | Cap `droneTracks` to last **300 points** — slice oldest when count exceeds limit |
| **B-M2** | Guard `onTelemetryUpdated` in `main.qml`: skip `updateDrones` + `setSelectedDrone` when `root.currentTab !== 0` (map tab). Add a "dirty" flag so the first switch back to Map tab triggers one immediate refresh. |
| **B-M3** | Merge `updateDrones(json)` + `setSelectedDrone(id)` into **one** `runJavaScript` call using a single combined JS call: `updateDronesAndSelect(json, id)` |
| **B-M5** | Remove the two ESCAPE QML `Repeater` blocks entirely from `MapView.qml` — they are placeholder 2D projections that are wrong anyway (NED coordinates used directly as pixel offsets). Replace with a comment marking where proper lat/lon projection should go. |
| **B-M8** | Add position-delta guard inside `updateDrones` JS: skip `setLatLng`/`setIcon`/`addLatLng` if `Math.abs(newLat - prevLat) + Math.abs(newLon - prevLon) < 0.000001` |

**Codex fixes (JS-inside-HTML / logic):**

| Task | Fix |
|------|-----|
| **C-M4** | `updateWaypoints` JS: replace full destroy+recreate with **diff update** — only move markers whose lat/lon changed; only add/remove markers when count changes. Cache marker positions. |
| **C-M6** | `makeDroneIcon` JS: cache last `{heading, armed, selected}` per drone ID; skip `setIcon` call if nothing changed (heading tolerance ±1°). |
| **C-M7** | `updateSolarTriggerPoints` JS: replace emoji `📷` with inline SVG camera icon (no font fallback). |

---

**Codex — please implement C-M4, C-M6, C-M7 directly in the `mapHtml` property string in `tools/ui/qml/MapView.qml` and mark them done here. Bob will implement B-M1 through B-M8 on the QML side.**

---

### 2026-06-26T00:00:00+02:00 | Bob | Analysis + Plan | UI Freeze Investigation — Performance & Crash-Safety Hardening

**Trigger:** User reports UI freeze when clicking FlightLog tab while a mission is in flight. General sluggishness when multiple tabs are open.

**Root causes identified (code-confirmed):**

#### 1. Status bar O(n) log counting on EVERY frame — most critical

In [`main.qml:1036-1049`](tools/ui/qml/main.qml), the status bar `Row` has two bound `property int`:

```qml
property int errorCount: {
    var count = 0
    for (var i = 0; i < globalLogModel.count; i++) {
        if (globalLogModel.get(i).level === "ERROR") count++
    }
    return count
}
property int warnCount: { /* same loop */ }
```

These are **eager bindings**. They re-execute every time `globalLogModel.count` changes — i.e., **every incoming log message**. During an active mission, the swarm fires log messages at ~1–5 Hz, which causes two full O(n) walks of the entire log model (up to 3000 entries = 6000 `ListModel.get()` calls per message). Every call to `ListModel.get()` is expensive in PySide6 QML.

**Same bug** exists in `LogPanel.qml:55-62` (another O(n) errorCount binding).

#### 2. LogPanel delegate calls extractDroneId() and getDroneColor() 3× per cell per repaint

In `LogPanel.qml:233-249`, each delegate row calls `extractDroneId(model.text)` and `getDroneColor(...)` **three times** on every repaint (for `width`, `border.color`, and `text`/`color` separately). With 3000 entries, this is 9000 regex calls on every layout pass.

#### 3. FlightLog Canvas repaints 4× every time hoverIdx changes

In `FlightLogPanel.qml:23`, `onHoverIdxChanged: repaintAll()` calls 4 canvas `requestPaint()` every mouse-move pixel. Each canvas iterates the full `rows[]` array. While the drone is flying this is less of a concern, but clicking the FlightLog tab forces:
- Panel load (Loader becomes active for the first time)
- All 4 Canvas `onPaint` fire immediately (even with empty data)
- The 4 `MouseArea` with `hoverEnabled: true` start generating position events

This load spike hitting an already-busy UI thread causes the freeze the user observed.

#### 4. panelLoader: `everVisited = true` keeps all loaded panels in memory forever

In `main.qml:980-990`, panels stay loaded once visited (`active: everVisited`). This means every panel opened during a session accumulates its connections, Timers, and signal handlers in memory simultaneously.

The **DashboardPanel** (`onTelemetryUpdated`) increments `telemetryTick` and calls `JSON.stringify()` every telemetry tick even when invisible. After visiting Dashboard + FlightLog + Mission tabs, 3 panels are doing work in the background.

#### 5. Telemetry bridge calls mapLoader.item.updateDrones() + setSelectedDrone() every telemetry tick

In `main.qml:912-934`, the `onTelemetryUpdated` Connections block runs unconditionally for every telemetry update even when the map tab is not visible. Each call crosses the QML↔Python boundary and calls into the WebEngineView JS engine.

---

**Proposed fixes — prioritised:**

| # | Fix | Impact | Complexity |
|---|-----|--------|------------|
| P1 | Replace O(n) `errorCount`/`warnCount` bindings in statusbar with maintained counters in GlobalLogHandler | High | Low |
| P2 | Replace O(n) `errorCount` binding in LogPanel with same counter | High | Low |
| P3 | Throttle `mapLoader.item.updateDrones()` — only call when map tab is visible | Medium | Low |
| P4 | LogPanel: compute `extractDroneId` once per delegate item, store as local property | Medium | Low |
| P5 | DashboardPanel: guard `onTelemetryUpdated` with `visible` check | Medium | Low |
| P6 | FlightLog: debounce `repaintAll()` with a 16ms timer instead of calling 4×requestPaint per pixel | Low | Low |
| P7 | Add `maxEntries` trim to 500 by default (was 3000) + document trade-off | Low | Low |

---

**Assignment:**

- **Bob:** Implements P1 (GlobalLogHandler counter), P2 (LogPanel), P3 (map throttle), P4 (LogPanel delegate), P5 (Dashboard guard), P6 (FlightLog debounce).
- **Codex:** Review. If Codex spots any Python-side (backend.py / swarm context) sources of excessive signal emission (e.g. telemetry firing faster than necessary or logging synchronous file I/O on the Qt thread), please document here.

---

### 2026-06-25T18:15:00+02:00 | Bob | Test Results | Codex Mission Control Tests — All Passing ✅

**Files:** `tests/test_mission_context_control.py`

**Command run:**

```bash
python -m pytest tests/test_mission_context_control.py tests/test_mission_context_seeding_preview.py tests/test_mission_context_solar_preview.py tests/test_capability_context.py -v
```

**Result: 28/28 passed**

- `test_start_mission_worker_arms_takeoffs_sets_auto_and_marks_active` ✅
- `test_start_mission_worker_uses_seeding_takeoff_altitude` ✅
- `test_start_mission_worker_uses_solar_takeoff_altitude` ✅
- `test_pause_mission_worker_sets_loiter` ✅
- `test_abort_mission_worker_sends_rtl_and_clears_active` ✅
- `test_boundary_timeout_keeps_drawn_points` ✅
- All 8 seeding preview tests ✅
- All 7 solar preview tests ✅
- All 7 capability context tests ✅

Codex fix confirmed: `_mission_control_worker("start")` now uses mission-specific takeoff altitude (seeding → `_seed_altitude`, solar → `_solar_altitude`, coverage → `_coverage_altitude`).

**Additional fixes Bob applied in this session (map rendering):**

1. `updateFieldBoundary([])` and `updateExclusionZones([])` in `MapView.qml` now always clear existing markers even when the new list is empty. Previously, pressing "Clear Boundary" after generating a preview left the old markers on the map.

2. `updateSeedingDropPoints` in `MapView.qml` — two fixes:
   - Guard changed from `if (!point.lat || !point.lon)` to explicit `=== null / === undefined` check — the falsy JS guard silently dropped any point at lat=0 or lon=0.
   - For datasets > 300 points: switched from `L.divIcon` markers to `L.circleMarker` (canvas-rendered, no DOM node per point, `interactive: false`). All points added at once via `L.layerGroup`. This fixes the "too many points not drawn / UI freeze" issue with large seeding missions.

---

### 2026-06-25T17:19:56+02:00 | Codex | Plan | Mission Start Worker Review + Tests

**Files planned:** `tools/ui/context/mission_context.py`, `tests/test_mission_context_control.py`, `docs/project/camera-seeding-solar-collab-feedback.md`

**Message:**
Reviewed Bob's manual-test update and request for Codex review.

Plan:
- Keep Bob's explicit Start Mission behavior: ARM -> TAKEOFF -> AUTO belongs in `startMission()`, not upload workers.
- Confirm `_mission_active` should be marked only after successful AUTO start.
- Confirm abort should clear `_mission_active`.
- Keep timeout behavior: drawing timeout stops drawing mode but keeps already drawn points; explicit cancel still clears points.
- Add hardware-free tests for:
  - start worker call order: arm -> takeoff -> AUTO
  - start worker marks `_mission_active`
  - pause sends LOITER
  - abort sends RTL and clears `_mission_active`
  - drawing timeout keeps boundary points
- Small fix found during review: start worker currently uses `_coverage_altitude` for all mission modes. Patch it to use mission-specific takeoff altitude:
  - coverage -> `_coverage_altitude`
  - seeding -> `_seed_altitude`
  - solar -> `_solar_altitude`

---

### 2026-06-25T17:21:09+02:00 | Codex | Fix + Test Request | Mission Control Worker Tests Added

**Files:** `tools/ui/context/mission_context.py`, `tests/test_mission_context_control.py`, `docs/project/camera-seeding-solar-collab-feedback.md`

**Message:**
Reviewed Bob's `_mission_control_worker` and `_on_drawing_timeout` changes.

Review result:
- ARM -> TAKEOFF -> AUTO belongs in explicit `startMission()`, not upload workers. This is consistent with **Upload != Execute**.
- Marking `_mission_active` after successful AUTO is the right place.
- `pause` sending LOITER is appropriate.
- `abort` sending RTL and clearing `_mission_active` is appropriate.
- Keeping already drawn boundary points on drawing timeout is the intended UI behavior. Explicit `cancelDrawingBoundary()` remains the destructive action that clears points.

Small fix added:
- `_mission_control_worker("start")` no longer always uses `_coverage_altitude` for takeoff.
- It now uses mission-specific altitude:
  - coverage -> `_coverage_altitude`
  - seeding -> `_seed_altitude`
  - solar -> `_solar_altitude`

Hardware-free tests added in `tests/test_mission_context_control.py`:
- `test_start_mission_worker_arms_takeoffs_sets_auto_and_marks_active`
- `test_start_mission_worker_uses_seeding_takeoff_altitude`
- `test_start_mission_worker_uses_solar_takeoff_altitude`
- `test_pause_mission_worker_sets_loiter`
- `test_abort_mission_worker_sends_rtl_and_clears_active`
- `test_boundary_timeout_keeps_drawn_points`

Local test blocker:
- Could not run pytest locally because `python.exe` still fails before startup with:

```text
Eine angegebene Anmeldesitzung ist nicht vorhanden.
```

Bob test request:

```bash
python -m pytest tests/test_mission_context_control.py tests/test_mission_context_seeding_preview.py tests/test_mission_context_solar_preview.py tests/test_capability_context.py -q
```

Manual test recommendation:
- Upload a mission first.
- Press Start Mission.
- Expected: drone arms if needed, takes off to the active mission mode altitude, then switches to AUTO.
- Press Pause: expected LOITER.
- Press Abort: expected RTL and mission lock cleared.

---

### 2026-06-25T17:45:00+02:00 | Bob | Manual Test Results + Fixes | UI Test Session Log Analysis

**Log file:** `logs/syslogs/2026-06-25_163649.txt`

**Manual test session summary:**

User tested the full coverage mission workflow. Two bugs were found and fixed by Bob. One remaining issue needs Codex review.

---

**What worked:**

- Connecting to SITL on `tcp:127.0.0.1:5762` ✅
- FSM state `IDLE` on connect ✅
- Home position set from first boundary point ✅
- Drawing boundary: 4 points added ✅
- Drawing exclusion zone: 3 points added ✅
- `abort` → RTL triggered correctly ✅

**What failed:**

1. `Mission: 1 WP` logged after `start command sent` — only 1 waypoint was on the drone despite drawing a 4-point boundary. Root cause: the boundary drawing timed out (`⏱ Boundary drawing timed out (5min)`), the old code called `_boundary_points.clear()`, then the user pressed Start Mission with no valid mission uploaded, so only a residual 1-WP mission was present on the vehicle.

2. `startMission()` → drone did nothing. Root cause: `_mission_control_worker` sent only `conn.set_mode("AUTO")` with no ARM or TAKEOFF. Drone was on the ground, disarmed.

**Fixes Bob implemented:**

Fix 1 — `_on_drawing_timeout` no longer clears `_boundary_points`:
```python
# Before (wrong):
self._boundary_points.clear()
# After (correct):
# Do NOT clear _boundary_points — keep what the user already drew
```

Fix 2 — `_mission_control_worker` "start" now runs full ARM → TAKEOFF → AUTO:
```python
# 1. drone.arm(timeout=10.0)       — skipped if already armed
# 2. drone.takeoff(altitude, 30.0) — skipped if altitude >= 2m
# 3. time.sleep(1.0)               — brief settle
# 4. drone.set_mode("AUTO", 5.0)   — start uploaded mission
# 5. mark _mission_active in SwarmContext
```

Uses `backend._drone` (SDK `Drone` object) — confirmed it has `.armed`, `.altitude`, `.arm()`, `.takeoff()`, `.set_mode()`.

`pause` updated: `drone.set_mode("LOITER", timeout=5.0)`.
`abort` updated: clears `_mission_active` from SwarmContext.

**Tests after fix: 22/22 green.**

---

**Additional UI fix (SolarInspectionPanel scroll):**

User reported two-finger scroll not working in SolarInspectionPanel. Root cause: inner `ScrollView` with fixed `height: 400` blocked the outer `MissionPanel` ScrollView. Fix: removed the inner `ScrollView` and wrapping `Rectangle` entirely — `Loader` now sits directly in `contentColumn`, same pattern as `SeedingPanel.qml` which works correctly.

---

**Request for Codex:**

1. **Review `_mission_control_worker` start sequence** — confirm the ARM→TAKEOFF→AUTO logic is correct for the project's FSM and that marking `_mission_active` here is the right place (was previously only set by upload workers).

2. **Review `_on_drawing_timeout` fix** — confirm keeping points on timeout is the intended behavior. The old behavior (clear on timeout) may have been intentional as a safety measure. If clearing was intentional, an alternative would be to extend the timeout instead of keeping points silently.

3. **Codex: Are there tests for `_mission_control_worker` / `startMission()`?** If not, please add hardware-free tests verifying arm→takeoff→AUTO sequence is called in the correct order, and that abort clears `_mission_active`.

---

### 2026-06-25T17:30:00+02:00 | Bob | Bug Fixes | startMission ARM+TAKEOFF+AUTO + Boundary Timeout Keeps Points

**Files:** `tools/ui/context/mission_context.py`

**Bugs found from log `2026-06-25_163649.txt`:**

1. `startMission()` sent only `set_mode("AUTO")` — drone was on ground, not armed → mission did nothing
2. `_on_drawing_timeout` called `_boundary_points.clear()` — drew 4 points but they were wiped on timeout

**Fixes:**

`_mission_control_worker` "start" action now runs full sequence:
- ARM (skipped if already armed, `drone.arm(timeout=10.0)`)
- TAKEOFF if `altitude < 2m` using `drone.takeoff(altitude=coverage_altitude, timeout=30.0)`
- 1s settle after takeoff
- `drone.set_mode("AUTO", timeout=5.0)` to start uploaded mission
- Marks `_mission_active` in SwarmContext on success

Uses `backend._drone` (SDK Drone object) directly — has `.armed`, `.altitude`, `.arm()`, `.takeoff()`, `.set_mode()`.

`pause` also updated to use `drone.set_mode("LOITER", timeout=5.0)` via SDK.

`abort` now clears `_mission_active` flag in SwarmContext.

`_on_drawing_timeout` fixed: **no longer calls `_boundary_points.clear()`** — only stops drawing mode. User's drawn points survive the 5-minute timeout.

**Tests: 22/22 green** (`test_mission_context_seeding_preview`, `test_mission_context_solar_preview`, `test_capability_context`)

---

### 2026-06-25T16:24:35+02:00 | Codex | Review | Bob Phase 5 Safety Update Confirmed

**Files reviewed:** `docs/project/camera-seeding-solar-collab-feedback.md`, `docs/project/camera-seeding-solar-implementation-plan.md`, `tools/ui/context/mission_context.py`

**Message:**
Reviewed Bob's Phase 5 update. Spot-check confirms the three upload workers are upload-only:

- `_upload_mission_worker`
- `_upload_seeding_mission_worker`
- `_upload_solar_mission_worker`

They now upload mission items and log `Press Start Mission to execute.` No auto-arm, auto-takeoff, auto-start, or `_mission_active` marking was found in those workers.

`set_mode("AUTO")` remains only in the explicit `startMission()` path, which matches the project rule: **Upload != Execute**.

Feedback file was updated to mark Phase 5 safety and Bob's `70/70` reported test run as complete.

---

**Last condensed:** 2026-06-25T15:40:00+02:00
**Purpose:** Short coordination file for Codex + Bob. Old resolved requests were summarized and removed for readability.

---

### 2026-06-25T16:30:00+02:00 | Bob | Phase 5 Complete | Mission Context Safety Review — Upload Workers Cleaned ✅

**Files:** `tools/ui/context/mission_context.py`

**Implemented:**

Priority 1 (Mission Context Safety Review) is now complete. All three upload workers now do upload-only — no auto-arm, no auto-takeoff, no auto-start, no `_mission_active` marking.

Changes per worker:

- `_upload_mission_worker` (Coverage): Removed ARM → TAKEOFF → START MISSION sequence and `_mission_active` marking. Upload succeeds when `mission.upload()` returns True. Success message now says "Press Start Mission to execute."
- `_upload_seeding_mission_worker`: Removed FLYING/MISSION branch (auto `mission.start()`) and ground branch (ARM → TAKEOFF → START). Upload succeeds when `mission.upload()` returns True.
- `_upload_solar_mission_worker`: Removed auto-arm, auto-takeoff, `mission.start()`, and `_mission_active` marking. Upload succeeds when `mission.upload()` returns True.

Explicit execution path remains untouched in `startMission()` — user must press Start Mission after upload.

**Tests (70/70 green):**

- `test_mission_context_seeding_preview` (8 tests) ✅
- `test_mission_context_solar_preview` (7 tests) ✅
- `test_capability_context` (7 tests) ✅
- `test_seeding_planner` (20 tests incl. large-field tests) ✅
- `test_solar_inspection` (28 tests) ✅

**Priority 2 + 3 also confirmed passing** — all Codex-added Phase 6 signal/capability and large-field tests are green.

---

## Current Status

### Complete / Code-Side Ready

- Camera backend/context and Camera/Gimbal UI integration are complete.
- Capability registry/context is complete.
- Solar backend preview is complete:
  - `SolarParkInspectionPlanner.generate_solar_mission_with_preview()`
  - trigger points
  - camera footprint polygons
  - gimbal angles
  - duration, battery, storage, total image estimates
  - validation
- MissionContext solar wrapper is complete:
  - `generateSolarPreview(params)`
  - `getSolarPreview()`
  - `solarPreviewChanged`
  - accepts QML aliases from Bob's Solar Wizard:
    - `gimbalAngle`
    - `cameraHFOV`
    - `cameraVFOV`
    - `addRTL`
    - `forwardOverlap`
    - `sideOverlap`
    - `triggerTime`
- Seeding backend preview is complete:
  - `generate_seeding_mission_with_preview()`
  - drop points
  - flight rows/path
  - exclusion zones
  - seed usage, battery, duration estimates
  - dispenser sequence: `NAV -> SERVO_OPEN -> NAV_DELAY -> SERVO_CLOSE`
- MissionContext seeding wrapper is complete:
  - `generateSeedingPreview(params)`
  - `getSeedingPreview()`
  - `seedingPreviewChanged`
- Drawing/backend wrappers are present:
  - `clearBoundary()`
  - `startDrawingExclusionZone()`
  - `startDrawingSolarRows()`
  - `clearSolarRows()`
  - `startMission()`
  - `pauseMission()`
  - `abortMission()`
- Seeding and Solar map preview signal flow is wired through `main.qml`.
- Bob reported Seeding/Solar map overlays complete.
- Bob reported a previous test batch passing: `59/59`.

---

## Current Open Items

### Priority 1 - Mission Context Safety Review

**Status:** Complete. Bob implemented the upload-worker cleanup and reported `70/70` tests passing.

**Rule:** Upload must not execute.

**Current behavior:**

- `uploadCoverageMission()`, `uploadSeedingMission()`, and `uploadSolarMission()` should only upload mission items.
- Upload workers do not:
  - arm
  - take off
  - switch to AUTO
  - mark drones as active mission-controlled
- Explicit execution remains in `startMission()`.
- User must press the Start Mission button after upload.

**Codex spot-check:** `set_mode("AUTO")` remains in explicit `startMission()`. Upload workers now log `Press Start Mission to execute.`

### Priority 2 - Test Status

**Status:** Complete per Bob.

Bob reported `70/70` passing:

- `test_mission_context_seeding_preview`
- `test_mission_context_solar_preview`
- `test_capability_context`
- `test_seeding_planner`
- `test_solar_inspection`

### Priority 3 - Large Seeding Fields

User request:

> "ich will diese limit nicht, ich will soviel field size definieren wie ich will"

Current code-side status:

- The hard 700-waypoint preview failure was removed from `skymeshx/control/seeding_planner.py`.
- Large seeding fields should now generate previews.
- Missions above the common 700-waypoint vehicle limit become warnings, not blocking errors.
- `estimatedWaypointCount` is included in preview data.

**Status:** Code-side complete; tests passed per Bob.

Manual UI test:

1. Draw the same field from `logs/syslogs/2026-06-25_105049.txt`.
2. Keep `seedSpacing` at `1.0m`.
3. Generate seeding preview.
4. Expected: preview succeeds.
5. Warning about high waypoint count is okay; `Preview generation failed` is not okay.

---

## Recent Changes Verified By Bob

### Phase 6 Signal + Capability Tests

Added and reported passing:

- `test_seeding_preview_changed_signal_and_getter()`
- `test_solar_preview_changed_signal_and_getter()`
- `test_capability_context_solar_qml_nested_capabilities_shape()`

These verify:

- `generateSeedingPreview()` emits `seedingPreviewChanged`.
- `getSeedingPreview()` returns the latest preview.
- `generateSolarPreview()` emits `solarPreviewChanged`.
- `getSolarPreview()` returns the latest preview.
- `capabilityCheck.capabilities.hasThermalCamera` is readable from QML-style nested data.

### Large Seeding Field Tests

Added and reported passing:

- `test_large_seeding_mission_above_vehicle_limit_remains_valid()`
- `test_large_seeding_preview_above_vehicle_limit_does_not_raise()`

These verify:

- >700 estimated waypoints is a warning, not an error.
- Preview generation does not raise for large fields.
- `estimatedWaypointCount` is present in QML preview data.

---

## Known Codex Local Blocker

Codex cannot run Python tests locally because `python.exe` / `py.exe` fails before startup with:

```text
Eine angegebene Anmeldesitzung ist nicht vorhanden.
```

Bob has been running pytest and reporting results.

---

## Resolved / Obsolete Requests Removed From File

The following old requests are considered resolved or obsolete and were removed from the long feedback history:

- "Leaflet white map" / `L is not defined` / `Unexpected identifier 'width'` issues.
- Local-map fallback vs online tile discussion.
- Missing seeding backend preview wrapper.
- Missing solar backend preview wrapper.
- Missing solar backend preview generation.
- Missing camera/capability context foundation.
- Seeding delay command missing between servo open/close.
- Exclusion zone state stuck after drawing.
- Preview map overlays not drawing because panels referenced `mapView` instead of `mapLoader.item`.
- Solar wizard parameter alias mismatch.
- Request claiming `startDrawingBoundary()` is missing for Solar rows. Correct Solar API is `startDrawingSolarRows()`.

---

## Quick Reference

Important files:

- `tools/ui/context/mission_context.py`
- `skymeshx/control/seeding_planner.py`
- `skymeshx/control/solar_inspection.py`
- `tools/ui/context/capability_context.py`
- `tools/ui/qml/main.qml`
- `tools/ui/qml/MapView.qml`
- `tools/ui/qml/panels/SeedingPanel.qml`
- `tools/ui/qml/panels/SolarInspectionPanel.qml`

Useful test commands:

```bash
python -m pytest tests/test_mission_context_seeding_preview.py tests/test_seeding_planner.py -q
python -m pytest tests/test_mission_context_solar_preview.py tests/test_solar_inspection.py -q
python -m pytest tests/test_capability_context.py -q
```
