# Comprehensive Implementation Plan: Camera, Video Streaming & Advanced Mission Modes

**Date:** 2026-06-20  
**Version:** 2.0 (Merged Plan)  
**Status:** Ready for Implementation

## Executive Summary

This plan defines a complete implementation strategy for making **Seeding** and **Solar Inspection** modes intuitive, technically coherent, and production-ready. The core principle is that operators must always understand:

- ✅ **Which mode is currently active**
- ✅ **What the drone will do** after upload or execution
- ✅ **Which hardware capabilities** are required
- ✅ **Which camera, gimbal, or payload actions** will happen during the mission
- ✅ **How to cancel or leave** the current mode safely

This plan merges camera/video streaming features with a comprehensive product model for advanced mission modes, incorporating research-backed best practices for agricultural and solar inspection drone operations.

## Literature References

The following research papers informed this implementation plan:

- `1-s2.0-S2772375525007506-main.pdf` - Agricultural drone applications
- `Modern Agriculture - 2025 - Yumnam - Utilising Drones in Agriculture.pdf`
- `Application_of_drone_in_agriculture_A_review.pdf`
- `Drone-based_solar_panel_inspection_using_machine_l.pdf`
- `epjconf_riact2026_02005.pdf` - Solar panel inspection techniques
- `s10846-025-02265-w.pdf` - Drone control systems
- `SolarPanel-PV-Inspection-Radiometry.pdf` - Radiometric inspection methods

## Product Model: Universal Operator Contract

Every advanced mission mode (Solar, Seeding, Coverage, etc.) follows the same 8-step workflow:

### 1. Select Mode
Clear indication of what this mode does and what hardware is required.

### 2. Define Area
Draw boundaries, rows, or waypoints on map with visual feedback.

### 3. Configure Payload
Camera, gimbal, dispenser, or sensor settings with validation.

### 4. Preview Mission
Path, actions, duration, warnings - **MUST** be shown before upload.

### 5. Validate Safety
Hardware capabilities, battery, weather, airspace checks.

### 6. Upload Mission
Transfer to drone (does **NOT** auto-execute).

### 7. Execute
Explicit confirmation required to start mission.

### 8. Review Results
Logs, reports, captured data, analysis.

### Mission Summary Requirements

Before upload, every mode **MUST** show:

```
✅ Flight path visualization on map
✅ Altitude and speed parameters
✅ Expected waypoint count
✅ Estimated duration (minutes)
✅ Camera/gimbal actions with trigger points
✅ Payload actions (dispenser, sensors)
✅ Required hardware capabilities
✅ Known warnings or limitations
✅ Battery usage estimate
```

## Current State Analysis

### ✅ What Exists (Building Blocks)

**Backend Components:**
- [`skymeshx/control/seeding_planner.py`](../../skymeshx/control/seeding_planner.py) - Seeding mission generation with servo commands, spacing validation, PWM control
- [`skymeshx/control/solar_inspection.py`](../../skymeshx/control/solar_inspection.py) - Solar waypoints with gimbal mount and camera trigger commands
- [`skymeshx/sensors/thermal_camera.py`](../../skymeshx/sensors/thermal_camera.py) - ROS2 thermal subscription, calibration hooks, hotspot detection
- [`skymeshx/models/observation_uav.py`](../../skymeshx/models/observation_uav.py) - Camera, gimbal, stream, recording action models

**UI Components:**
- [`tools/ui/qml/panels/GimbalPanel.qml`](../../tools/ui/qml/panels/GimbalPanel.qml) - Basic gimbal control (needs expansion)
- [`tools/ui/qml/panels/MissionPanel.qml`](../../tools/ui/qml/panels/MissionPanel.qml) - Mission mode selection
- Map mode mutex system (✅ implemented 2026-06-20)
- ESC key global handler (✅ implemented 2026-06-20)

### ❌ Critical Gaps

**User Experience Issues:**

1. **Solar Inspection** - No clear explanation of what happens when selected
   - Operators don't know: Will it take photos? Thermal images? How many? Where?
   - No preview of camera trigger points or footprints
   - No indication of required hardware (thermal camera, gimbal)

2. **Seeding** - No end-to-end workflow
   - No field boundary drawing with exclusion zones
   - No dispenser calibration or bench test
   - No preview of drop points or seed density
   - No seed count estimation or tank capacity tracking

3. **Camera Settings** - No complete camera configuration UI
   - No resolution, FPS, FOV settings
   - No trigger mode selection (distance, time, waypoint)
   - No storage folder configuration

4. **Video Streaming** - No integrated live stream preview
   - No stream quality controls
   - No recording indicator
   - No telemetry overlay on video

5. **Workflow Coherence** - Camera, gimbal, and mission planning are disconnected
   - Solar mode doesn't show camera settings
   - Seeding mode doesn't show dispenser settings
   - No unified payload control center

6. **Mode Exclusivity** - Partially implemented
   - Map mutex exists for drawing modes
   - Needs extension to camera automation, gimbal automation, mission generation

## Phase 1: Camera & Gimbal Foundation (Weeks 1-2)

### Goal

Transform [`GimbalPanel.qml`](../../tools/ui/qml/panels/GimbalPanel.qml) into a **Camera & Gimbal Control Center** that serves all mission modes (Solar, Seeding, Mapping, Observation).

### 1.1 Camera Source Selection

Add support for multiple camera types:

- **None** - No camera (manual waypoint missions only)
- **RGB Camera** - Standard visible light camera
- **Thermal Camera** - FLIR or similar thermal imaging
- **Multispectral** - Agriculture-specific multispectral sensors
- **RTSP Stream** - Network camera stream
- **ROS2 Topic** - ROS2 image topic subscription
- **Test Source** - Synthetic test pattern for development

### 1.2 Stream Controls

Essential controls for video streaming:

- **Start/Stop Stream** - Toggle video feed
- **Snapshot** - Capture single frame (enabled only when streaming)
- **Start/Stop Recording** - Record video to file with timestamp
- **Recording Indicator** - Blinking red "REC" badge with duration

### 1.3 Camera Settings

Complete camera configuration:

```yaml
Resolution: [640x480, 1280x720, 1920x1080, 3840x2160]
FPS: [1-60]
Horizontal FOV: [10-180°]
Vertical FOV: [10-180°]
Trigger Mode: [Manual, Distance, Time, Waypoint]
Storage Folder: [configurable path]
```

### 1.4 Thermal Settings (when thermal camera selected)

Radiometric inspection requires:

```yaml
Calibration Profile: [Default, Solar Panel, Agriculture]
Temperature Unit: [Celsius, Fahrenheit, Kelvin]
Hotspot Threshold: [0-200°C]
Emissivity: [0.1-1.0]
Reflected Temperature: [-40 to 100°C]
Solar Irradiance: [W/m²] (for accurate temperature measurement)
```

**Important:** Radiometric inspection is more than taking a thermal picture. The UI should capture or remind the operator about:

- Time of day (solar angle affects readings)
- Irradiance or weather conditions
- Wind (affects panel temperature)
- Camera calibration status
- Emissivity of panel surface
- Reflected temperature from surroundings
- Focus and image blur
- Altitude and FOV (affects resolution)

### 1.5 Status Display

Real-time camera health monitoring:

```
Stream: Connected/Disconnected (green/red)
Recording: Active with duration (blinking red)
Frame Age: <50ms (good), >100ms (warning)
Dropped Frames: <10 (good), >10 (warning)
Camera Profile: Current profile name
```

### 1.6 Backend: CameraContext

**Create:** [`tools/ui/context/camera_context.py`](../../tools/ui/context/camera_context.py)

**Responsibilities:**
- Own camera settings exposed to QML
- Validate stream URLs and topic names
- Start/stop stream through backend/model layer
- Start/stop recording with automatic file naming
- Capture snapshot with timestamp
- Expose camera health metrics
- Expose FOV and trigger settings to mission planners

**Required API Methods:**
```python
cameraStartStream(source: str) -> bool
cameraStopStream() -> bool
cameraSnapshot() -> bool
cameraStartRecording(path: str) -> bool
cameraStopRecording() -> bool
setCameraProfile(profile: dict) -> bool
getCameraStatus() -> dict
setTempRange(min_c: float, max_c: float) -> bool
setColorPalette(palette: str) -> bool
setHotspotDetection(enabled: bool) -> bool
```

**Extend:** [`tools/ui/backend.py`](../../tools/ui/backend.py) and [`skymeshx/models/observation_uav.py`](../../skymeshx/models/observation_uav.py)

### 1.7 Safety Rules

- ❌ **NO** auto-start cloud upload
- ❌ **NO** auto-record without explicit operator action or mission setting
- ✅ **MUST** validate RTSP URLs and file paths before use
- ✅ Camera failure **MUST NOT** crash mission planner
- ✅ Mission upload blocked **ONLY** when mission requires camera and no valid camera available
- ✅ Bench test disabled while armed unless explicitly allowed
- ✅ Recording stops automatically on low storage (<1GB)

## Phase 2: Video Streaming Display (Weeks 3-4)

### 2.1 Video Feed Widget

Add live video preview to Gimbal Panel:

**Features:**
- Full-screen toggle button
- Telemetry overlay (altitude, speed, battery)
- Recording indicator (blinking red badge)
- Frame rate and dropped frame counter
- Crosshair or grid overlay (optional)

**Telemetry Overlay:**
```
ALT: 45.2 m
SPD: 5.3 m/s
BAT: 78% (green if >20%, red if <20%)
GPS: 12 sats
HDG: 045°
```

### 2.2 Stream Quality Controls

Adaptive streaming quality:

```yaml
Quality Preset: [Low (480p), Medium (720p), High (1080p), Ultra (4K)]
Bitrate: [1-20 Mbps]
Hardware Acceleration: [enabled/disabled]
Codec: [H.264, H.265, MJPEG]
```

### 2.3 Fullscreen Mode

- Toggle with button or F11 key
- Overlay controls fade after 3 seconds
- Mouse movement shows controls again
- ESC exits fullscreen

## Phase 3: Thermal Camera Integration (Weeks 5-6)

### 3.1 Temperature Range Configuration

Dynamic temperature range adjustment:

```yaml
Min Temperature: [-40 to 200°C]
Max Temperature: [-40 to 200°C]
Auto Range: Automatically adjust to scene
```

### 3.2 Color Palette Selection

Multiple thermal palettes for different use cases:

- **Ironbow** - Industry standard (blue-red-yellow)
- **Rainbow** - Full spectrum visualization
- **Grayscale** - Black and white thermal
- **Hot** - Red-yellow-white (hot objects)
- **Cold** - Blue-cyan-white (cold objects)
- **Medical** - Medical imaging palette

**Palette Preview:** Show gradient bar below selection

### 3.3 Hotspot Detection

Automatic anomaly detection:

```yaml
Enable Hotspot Detection: [checkbox]
Threshold: [50-150°C]
Show Hotspots on Map: [checkbox]
Alert on Detection: [checkbox]
```

**Hotspot Markers:**
- Red circle on map at GPS location
- Temperature value label
- Thumbnail of thermal image
- Click to view full image

### 3.4 Thermal Calibration

**Calibration Profiles:**
- Default (generic)
- Solar Panel (emissivity 0.95, reflected temp 20°C)
- Agriculture (emissivity 0.98, reflected temp ambient)
- Custom (user-defined)

**Calibration Parameters:**
```yaml
Emissivity: [0.1-1.0]
Reflected Temperature: [-40 to 100°C]
Atmospheric Temperature: [-40 to 100°C]
Distance to Object: [1-1000m]
Relative Humidity: [0-100%]
```

## Phase 4: Solar Inspection Workflow (Weeks 7-8)

### 4.1 What Solar Mode Should Do

**Clear Definition:**

> Solar inspection mode means: The drone flies structured passes along selected solar panel rows, points the gimbal/camera at the panel surface, captures RGB and/or thermal images at configured intervals, geotags the captures, detects possible hotspots or damaged modules, and exports an inspection report.

**The UI must show this before upload.**

### 4.2 Solar Inspection Wizard (4 Steps)

#### Step 1: Setup

```yaml
Inspection Name: [text field] (e.g., "Solar Farm A - June 2026")
Select Drone: [dropdown] (from available drones)
Camera Profile: [RGB Only | Thermal Only | RGB + Thermal]
Enable Thermal: [checkbox]
```

**Next:** Define Site →

#### Step 2: Site Definition

**Actions:**
1. Draw solar farm boundary (polygon on map)
2. Add solar rows (lines on map, one by one)
3. Import rows from CSV/GeoJSON/KML (future)

**Row List Display:**
```
Row 1: 45.2 m [Delete]
Row 2: 43.8 m [Delete]
Row 3: 44.5 m [Delete]
Total: 3 rows, 133.5 m
```

**Map Overlays:**
- Solar farm boundary (blue polygon)
- Solar rows (yellow lines)
- Row numbers (labels)

**Next:** Flight Parameters →

#### Step 3: Flight & Camera Settings

**Flight Parameters:**
```yaml
Altitude: [5-100m] (default: 20m)
Speed: [1-15 m/s] (default: 5 m/s)
Row Overlap: [0-50%] (default: 20%)
Row Direction: [Auto | North-South | East-West]
Safe Turn Distance: [5-50m] (default: 10m)
RTL Behavior: [After mission | On battery low | Manual]
```

**Camera Settings:**
```yaml
Gimbal Pitch: [-90 to 0°] (default: -90° nadir)
Trigger Distance: [1-50m] (default: 5m)
Expected Image Footprint: [calculated from altitude + FOV]
```

**Thermal Settings (if enabled):**
```yaml
Calibration Profile: [Solar Panel]
Hotspot Threshold: [80°C]
Temperature Range: [Auto | Manual]
```

**Next:** Preview →

#### Step 4: Preview & Upload

**Mission Summary:**
```
Total Rows: 3
Total Waypoints: 24
Expected Images: 48 (RGB) + 48 (Thermal)
Estimated Duration: 8 min 32 sec
Flight Distance: 156.8 m
Camera Triggers: 48 points
Battery Required: ~35%
```

**Warnings (if any):**
```
⚠ Mission requires >80% battery - consider splitting
⚠ Low altitude - risk of collision with panels
⚠ Thermal camera not available
```

**Map Preview Toggles:**
- ☑ Show Flight Path (blue line)
- ☑ Show Camera Trigger Points (green dots)
- ☑ Show Camera Footprints (green rectangles)
- ☐ Show Skipped Rows

**Actions:**
- ← Back to Edit
- **Upload Mission** (highlighted button)

**After Upload:**
- Mission uploaded successfully ✓
- Ready to execute (requires explicit confirmation)
- **Start Mission** button (separate confirmation)

### 4.3 Solar Inspection Backend Extensions

**Extend:** [`skymeshx/control/solar_inspection.py`](../../skymeshx/control/solar_inspection.py)

**New Data Classes:**

```python
@dataclass
class SolarRow:
    """Represents a solar panel row."""
    id: int
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    length_m: float
    azimuth_deg: float

@dataclass
class CameraTriggerPoint:
    """Camera trigger point with footprint."""
    lat: float
    lon: float
    alt: float
    gimbal_pitch: float
    footprint_width_m: float
    footprint_height_m: float
    expected_image_id: str

@dataclass
class SolarInspectionMission:
    """Complete solar inspection mission with preview data."""
    name: str
    rows: List[SolarRow]
    waypoints: List[Dict]  # MAVLink waypoints
    trigger_points: List[CameraTriggerPoint]
    flight_path_coords: List[Tuple[float, float]]
    
    # Mission statistics
    total_distance_m: float
    estimated_duration_s: float
    expected_image_count: int
    battery_required_percent: float
    
    # Camera settings
    camera_profile: str
    thermal_enabled: bool
    gimbal_pitch: float
    trigger_distance_m: float
    
    # Warnings
    warnings: List[str]
```

**New Methods:**

```python
def generate_mission_preview(
    rows: List[SolarRow],
    altitude_m: float,
    speed_mps: float,
    overlap_percent: float,
    camera_hfov: float,
    camera_vfov: float,
    gimbal_pitch: float,
    trigger_distance_m: float,
    thermal_enabled: bool = False
) -> SolarInspectionMission:
    """Generate complete mission preview with all metadata."""
    # Implementation...
```

### 4.4 Solar Inspection Report

**Report Output Formats:**
- **JSON** - Machine-readable for analysis tools
- **CSV** - Anomaly list for spreadsheet import
- **HTML** - Human-readable report with images
- **PDF** - Printable report (future)

**Report Contents:**

```yaml
Inspection Metadata:
  - Name, Date, Time
  - Drone ID, Operator
  - Weather conditions
  - Camera settings

Flight Statistics:
  - Total distance, duration
  - Images captured (RGB + Thermal)
  - Battery used

Findings:
  - Hotspot count
  - Damaged module count
  - Severity distribution

Anomaly List:
  - Image ID, GPS, Temperature
  - Panel row ID
  - Severity (Critical/High/Medium/Low)
  - Confidence score
  - Thumbnail path
```

## Phase 5: Seeding Mode Improvements (Weeks 9-10)

### 5.1 What Seeding Mode Should Do

**Clear Definition:**

> Seeding mode means: The drone flies over a defined field and triggers a seed dispenser at calculated points or along calculated rows. The operator configures crop/seed type, spacing, dispenser behavior, altitude, speed, and exclusion zones before upload.

**The UI must show exactly where drops happen and which servo/channel commands will be sent.**

### 5.2 Seeding Wizard (6 Steps)

#### Step 1: Field Definition

**Actions:**
1. Draw field boundary (polygon on map)
2. Draw exclusion zones (no-drop areas)
3. Choose row direction (auto/manual)

**Field Statistics:**
```
Field Area: 2.5 ha
Exclusion Zones: 1 (0.2 ha)
Effective Area: 2.3 ha
```

**Next:** Crop Settings →

#### Step 2: Crop & Seed Configuration

```yaml
Crop Type: [Wheat | Corn | Rice | Soybean | Custom]
Seed Spacing: [5-100 cm] (default: 20 cm)
Row Spacing: [10-200 cm] (default: 50 cm)
Seed Rate: [10-500 seeds/m²] (calculated)
Prescription Map: [None | Upload CSV] (variable-rate seeding)
```

**Seed Count Estimate:**
```
Expected Seeds: ~45,000
Seeds per Row: ~1,500
Total Rows: 30
```

**Next:** Dispenser Settings →

#### Step 3: Dispenser Configuration

```yaml
Servo Channel: [1-16] (default: 9)
Open PWM: [1000-2000] (default: 1900)
Close PWM: [1000-2000] (default: 1100)
Drop Duration: [100-5000 ms] (default: 500 ms)
Seeds per Pulse: [1-100] (default: 1)
Tank Capacity: [1-10000 seeds] (default: 5000)
```

**PWM Validation:**
- ✅ Open and close values are different
- ✅ Values are within safe range (1000-2000)
- ✅ Drop duration is reasonable (<5s)

**Bench Test:**
```
[Test Dispenser] button
- Disabled while armed (safety)
- Sends single pulse to verify operation
- Shows "Pulse sent ✓" confirmation
```

**Next:** Flight Parameters →

#### Step 4: Flight Parameters

```yaml
Altitude: [5-50m] (default: 10m)
Speed: [1-10 m/s] (default: 3 m/s)
Turn Behavior: [Sharp | Smooth | Wide]
RTL Behavior: [After mission | On empty tank | Manual]
```

**Next:** Preview →

#### Step 5: Preview & Upload

**Mission Summary:**
```
Field Area: 2.3 ha
Total Rows: 30
Total Waypoints: 180
Expected Seed Drops: 45,000
Estimated Duration: 18 min 45 sec
Flight Distance: 3,240 m
Tank Refills Required: 9
Battery Required: ~65%
```

**Warnings (if any):**
```
⚠ Mission requires multiple tank refills
⚠ High seed count - verify tank capacity
⚠ Dispenser not configured
```

**Map Preview Toggles:**
- ☑ Show Flight Path (blue line)
- ☑ Show Drop Points (green dots)
- ☑ Show Density Heatmap (color gradient)
- ☑ Show Exclusion Zones (red polygons)

**Actions:**
- ← Back to Edit
- **Upload Mission** (highlighted button)

#### Step 6: Execution & Monitoring

**Real-time Statistics:**
```
Progress: 45% (Row 14 of 30)
Seeds Dispensed: 20,250 / 45,000
Area Covered: 1.0 ha / 2.3 ha
Time Elapsed: 8 min 32 sec
Time Remaining: ~10 min
Tank Level: 35% (refill soon)
```

**Visual Feedback on Map:**
- Completed rows (green)
- Current row (yellow)
- Remaining rows (gray)
- Drop points (green dots)
- Missed drops (red dots, if any)

### 5.3 Seeding Backend Extensions

**Extend:** [`skymeshx/control/seeding_planner.py`](../../skymeshx/control/seeding_planner.py)

**New Features:**
- Support exclusion zones (no-drop polygons)
- Support row direction (auto/manual)
- Support variable-rate prescription maps (CSV import)
- Estimate seed count and tank usage
- Split very large missions safely (battery/tank limits)
- Return preview data separately from MAVLink mission items

**New Data Classes:**

```python
@dataclass
class SeedPrescription:
    """Variable-rate seeding prescription."""
    zones: List[Dict]  # {polygon, seed_rate}
    
@dataclass
class SeedDispenserProfile:
    """Dispenser hardware configuration."""
    servo_channel: int
    open_pwm: int
    close_pwm: int
    drop_duration_ms: int
    seeds_per_pulse: int
    tank_capacity: int
    
@dataclass
class SeedingMissionPreview:
    """Complete seeding mission preview."""
    field_area_ha: float
    rows: List[Dict]
    drop_points: List[Tuple[float, float]]
    expected_seed_count: int
    tank_refills_required: int
    estimated_duration_s: float
    warnings: List[str]
```

### 5.4 Dispenser Safety Validation

**Pre-flight Checks:**
- ✅ Servo channel is configured (1-16)
- ✅ PWM values are within safe range (1000-2000)
- ✅ Open and close values are not equal
- ✅ Drop duration is within configured bounds (100-5000ms)
- ✅ Bench test is disabled while armed (unless explicitly allowed)
- ✅ No drop command outside field boundary
- ✅ No drop command inside exclusion zones
- ✅ Tank capacity is sufficient (or refill plan exists)

**Runtime Monitoring:**
- Track seeds dispensed vs. expected
- Alert on missed drops (servo failure)
- Alert on low tank level (20% remaining)
- Emergency stop button (stops dispenser, continues flight)

## Phase 6: Capability Registry & Mode Architecture (Week 11)

### 6.1 Capability Registry

**Central Capability Model:**

```python
@dataclass
class DroneCapabilities:
    """Hardware capabilities of a drone."""
    camera_available: bool
    thermal_camera_available: bool
    gimbal_available: bool
    seeding_dispenser_available: bool
    mission_upload_available: bool
    live_stream_available: bool
    recording_available: bool
    
    # Camera specs
    camera_hfov: float = 90.0
    camera_vfov: float = 60.0
    max_resolution: str = "1920x1080"
    
    # Gimbal specs
    gimbal_pitch_range: Tuple[float, float] = (-90, 0)
    gimbal_roll_range: Tuple[float, float] = (-45, 45)
    gimbal_yaw_range: Tuple[float, float] = (-180, 180)
```

**Mode Requirements:**

```python
SOLAR_INSPECTION_REQUIREMENTS = {
    "mission_upload": True,
    "gimbal": True,
    "camera": True,  # At least one camera
    "thermal": False  # Optional for radiometric inspection
}

SEEDING_REQUIREMENTS = {
    "mission_upload": True,
    "dispenser": True,
    "camera": False  # Optional for documentation
}

MAPPING_REQUIREMENTS = {
    "mission_upload": True,
    "camera": True,
    "gimbal": False  # Optional
}
```

**Capability Checking:**

```python
def check_mode_requirements(mode: str, capabilities: DroneCapabilities) -> Tuple[bool, List[str]]:
    """
    Check if drone meets mode requirements.
    
    Returns:
        (can_execute, missing_capabilities)
    """
    requirements = MODE_REQUIREMENTS[mode]
    missing = []
    
    for req, required in requirements.items():
        if required and not getattr(capabilities, f"{req}_available"):
            missing.append(req)
    
    return len(missing) == 0, missing
```

**UI Behavior:**

- If requirements are met: Enable mode, show green checkmark
- If requirements are missing: Show mode with warning icon, explain what's missing
- **DO NOT** hide modes - always show what's possible and what's needed

### 6.2 Command Ownership Rules

**Mutex System Extension:**

```python
class CommandOwnership:
    """Tracks which mode owns which commands."""
    
    map_editing_owner: Optional[str] = None
    mission_generation_owner: Optional[str] = None
    camera_automation_owner: Optional[str] = None
    gimbal_automation_owner: Optional[str] = None
```

**Rules:**

1. **Only one mode** may own map editing at a time
2. **Only one mode** may own mission generation at a time
3. **Only one mode** may own camera automation at a time
4. **Only one mode** may own gimbal automation at a time
5. **Manual gimbal override** should pause mission camera automation or require confirmation

**Implementation:**

```python
def acquire_command_ownership(mode: str, command_type: str) -> bool:
    """
    Acquire ownership of a command type.
    
    Returns:
        True if acquired, False if already owned by another mode
    """
    current_owner = getattr(command_ownership, f"{command_type}_owner")
    
    if current_owner is None or current_owner == mode:
        setattr(command_ownership, f"{command_type}_owner", mode)
        return True
    else:
        # Another mode owns this command
        return False

def release_command_ownership(mode: str, command_type: str):
    """Release ownership of a command type."""
    current_owner = getattr(command_ownership, f"{command_type}_owner")
    
    if current_owner == mode:
        setattr(command_ownership, f"{command_type}_owner", None)
```

### 6.3 Mode State Machine

**Every complex mode should use:**

```python
class ModeState(Enum):
    IDLE = "idle"
    EDITING = "editing"
    CONFIGURED = "configured"
    PREVIEW_READY = "preview_ready"
    UPLOADED = "uploaded"
    EXECUTING = "executing"
    REVIEW = "review"
    CANCELLED = "cancelled"
    ERROR = "error"
```

**State Transitions:**

```
IDLE → EDITING (user starts drawing/configuring)
EDITING → CONFIGURED (user completes configuration)
CONFIGURED → PREVIEW_READY (preview generated)
PREVIEW_READY → UPLOADED (mission uploaded)
UPLOADED → EXECUTING (user confirms start)
EXECUTING → REVIEW (mission complete)
ANY → CANCELLED (user cancels)
ANY → ERROR (error occurs)
```

**ESC Key Behavior:**

```python
def handle_esc_key(current_state: ModeState):
    """Handle ESC key press based on current state."""
    if current_state == ModeState.EDITING:
        # Cancel active drawing/editing
        cancel_editing()
        return ModeState.IDLE
    
    elif current_state == ModeState.PREVIEW_READY:
        # Return to editing
        return ModeState.EDITING
    
    elif current_state == ModeState.EXECUTING:
        # DO NOT silently stop mission
        # Show safe action options dialog
        show_mission_pause_dialog()
        return current_state
    
    elif modal_dialog_open:
        # Close dialog first
        close_modal_dialog()
        return current_state
    
    else:
        # Default: cancel current mode
        cancel_mode()
        return ModeState.IDLE
```

## Phase 7: Testing Strategy (Week 12)

### 7.1 Unit Tests (Hardware-Free)

**Test Coverage:**

```python
# Solar Inspection
test_solar_config_validation()
test_solar_trigger_count_calculation()
test_solar_fov_footprint_calculation()
test_solar_battery_estimation()
test_solar_warning_generation()

# Seeding
test_seeding_exclusion_zones()
test_seeding_seed_count_estimate()
test_seeding_tank_refill_calculation()
test_dispenser_pwm_validation()
test_seeding_row_generation()

# Camera
test_camera_profile_validation()
test_stream_url_validation()
test_thermal_calibration()
test_hotspot_detection()

# Capability Registry
test_capability_requirement_checks()
test_mode_availability()
```

### 7.2 UI/Mode Tests

**Test Scenarios:**

```python
# Mode Switching
test_switching_from_seeding_to_solar_cancels_seeding()
test_switching_from_solar_to_waypoint_cancels_solar()
test_esc_cancels_active_edit_mode()

# Camera Integration
test_camera_settings_readable_by_solar_planner()
test_thermal_settings_applied_to_mission()

# Capability Checks
test_seeding_upload_disabled_without_dispenser()
test_solar_radiometric_disabled_without_thermal()
test_missing_capabilities_show_warning()

# Command Ownership
test_only_one_mode_owns_map_editing()
test_manual_gimbal_pauses_camera_automation()
```

### 7.3 Integration Tests (Mocked Hardware)

**Mock Components:**

```python
# Mock drone connection
FakeConnection(telemetry, commands)

# Mock camera stream
FakeCameraStream(resolution, fps, frames)

# Mock thermal camera
FakeThermalCamera(temp_range, hotspots)

# Mock mission upload
FakeMissionUpload(waypoints, result)

# Mock seeding dispenser
FakeDispenser(channel, pwm, pulses)
```

**Test Scenarios:**

```python
# Mission Preview
test_mission_preview_does_not_upload()
test_preview_shows_correct_statistics()

# Mission Upload
test_upload_does_not_auto_execute()
test_upload_validates_capabilities()

# Camera Failure
test_camera_failure_creates_warning()
test_mission_continues_without_camera_if_optional()

# Report Export
test_report_export_with_mocked_captures()
test_report_contains_all_metadata()
```

## Phase 8: Implementation Order (12 Weeks)

### Week 1-2: Camera & Gimbal Foundation
- ✅ Extend GimbalPanel.qml with camera controls
- ✅ Create CameraContext backend
- ✅ Add camera source selection
- ✅ Add stream controls
- ✅ Add camera settings UI
- ✅ Add thermal settings UI
- ✅ Add status display

### Week 3-4: Video Streaming Display
- ✅ Add video feed widget
- ✅ Add telemetry overlay
- ✅ Add recording indicator
- ✅ Add stream quality controls
- ✅ Add fullscreen mode
- ✅ Test with RTSP and ROS2 sources

### Week 5-6: Thermal Camera Integration
- ✅ Add temperature range configuration
- ✅ Add color palette selection
- ✅ Add hotspot detection
- ✅ Add thermal calibration profiles
- ✅ Add hotspot markers on map
- ✅ Test with thermal camera hardware

### Week 7-8: Solar Inspection Workflow
- ✅ Create solar inspection wizard (4 steps)
- ✅ Add solar row drawing on map
- ✅ Add flight parameter configuration
- ✅ Add camera/gimbal settings
- ✅ Generate mission preview with statistics
- ✅ Add map overlays (rows, triggers, footprints)
- ✅ Extend solar_inspection.py backend
- ✅ Add report export functionality

### Week 9-10: Seeding Mode Improvements
- ✅ Create seeding wizard (6 steps)
- ✅ Add field boundary and exclusion zones
- ✅ Add crop/seed configuration
- ✅ Add dispenser settings and bench test
- ✅ Add flight parameters
- ✅ Generate mission preview with seed count
- ✅ Add map overlays (rows, drops, density)
- ✅ Extend seeding_planner.py backend
- ✅ Add real-time execution monitoring

### Week 11: Capability Registry & Mode Architecture
- ✅ Implement capability registry
- ✅ Add mode requirement checks
- ✅ Extend command ownership system
- ✅ Implement mode state machine
- ✅ Add ESC key handling per state
- ✅ Test mode switching and ownership

### Week 12: Testing & Documentation
- ✅ Write unit tests (hardware-free)
- ✅ Write UI/mode tests
- ✅ Write integration tests (mocked)
- ✅ Update user documentation
- ✅ Create video tutorials
- ✅ Conduct user acceptance testing

## Minimum Viable Commercial Feature Set

For a strong first commercial version, prioritize:

### Must-Have Features:
1. ✅ Solar inspection wizard with clear workflow
2. ✅ Camera & Gimbal panel with live stream and recording
3. ✅ Thermal hotspot detection and reporting
4. ✅ Inspection report export (JSON, CSV, HTML)
5. ✅ Seeding wizard with dispenser calibration
6. ✅ Dispenser bench test and safety validation
7. ✅ Mission preview with warnings and statistics
8. ✅ Capability checks and clear error messages
9. ✅ Mode mutex and safe cancellation (ESC key)
10. ✅ Real-time execution monitoring

### Nice-to-Have Features (Future):
- Variable-rate seeding prescription maps
- Multi-drone solar inspection coordination
- AI-powered anomaly detection
- Cloud report storage and sharing
- Mobile app for field operations
- Offline map caching
- Weather integration
- Airspace integration

## Definition of Done

The feature set is **intuitive and complete** when:

### User Understanding:
- ✅ Selecting solar mode immediately explains the inspection mission
- ✅ Selecting seeding mode immediately explains the seeding mission
- ✅ The operator can see all drone actions before upload
- ✅ Camera and gimbal behavior is visible in preview
- ✅ Seeding drop points are visible before upload
- ✅ Solar image trigger points and footprints are visible before upload

### Hardware Integration:
- ✅ Missing hardware is shown as a clear warning (not hidden)
- ✅ Camera settings are integrated with mission planning
- ✅ Thermal calibration is accessible and documented
- ✅ Dispenser settings are validated and testable

### Safety & Workflow:
- ✅ Upload never implies automatic execution
- ✅ ESC reliably leaves the active edit mode
- ✅ Changing mode cancels the previous mode cleanly
- ✅ Manual overrides pause automation with confirmation
- ✅ All warnings are shown before mission upload

### Quality Assurance:
- ✅ All unit tests pass (hardware-free)
- ✅ All integration tests pass (mocked hardware)
- ✅ User acceptance testing completed
- ✅ Documentation is complete and accurate
- ✅ Video tutorials are available

## Success Metrics

### Quantitative:
- Mission preview accuracy: >95%
- Camera trigger success rate: >98%
- Dispenser pulse accuracy: >95%
- User task completion time: <50% of current
- Support ticket reduction: >60%

### Qualitative:
- Users understand what each mode does
- Users feel confident before mission upload
- Users can troubleshoot issues independently
- Users report improved workflow efficiency
- Users recommend the system to others

## Risk Mitigation

### Technical Risks:
1. **Camera stream latency** - Use hardware acceleration, adaptive bitrate
2. **Thermal calibration complexity** - Provide presets, clear documentation
3. **Mission preview accuracy** - Extensive testing, validation checks
4. **Dispenser timing precision** - Bench test, calibration wizard

### User Experience Risks:
1. **Wizard too complex** - User testing, iterative simplification
2. **Too many settings** - Sensible defaults, progressive disclosure
3. **Unclear warnings** - Plain language, actionable messages
4. **Mode confusion** - Clear labels, visual indicators

### Safety Risks:
1. **Accidental mission start** - Explicit confirmation required
2. **Dispenser malfunction** - Bench test, PWM validation
3. **Camera failure mid-mission** - Graceful degradation, warnings
4. **Battery estimation error** - Conservative estimates, safety margins

## Appendix A: MAVLink Commands

### Camera Commands:
```
MAV_CMD_DO_DIGICAM_CONTROL (203) - Trigger camera
MAV_CMD_VIDEO_START_CAPTURE (2500) - Start recording
MAV_CMD_VIDEO_STOP_CAPTURE (2501) - Stop recording
MAV_CMD_REQUEST_VIDEO_STREAM_INFORMATION (2504) - Get stream info
MAV_CMD_REQUEST_CAMERA_INFORMATION (521) - Get camera capabilities
```

### Gimbal Commands:
```
MAV_CMD_DO_MOUNT_CONTROL (205) - Control gimbal
MAV_CMD_DO_MOUNT_CONFIGURE (204) - Configure gimbal mode
```

### Servo Commands (Seeding):
```
MAV_CMD_DO_SET_SERVO (183) - Set servo PWM
MAV_CMD_DO_REPEAT_SERVO (184) - Repeat servo pulse
```

## Appendix B: File Structure

```
skymeshx/
├── control/
│   ├── seeding_planner.py (extended)
│   ├── solar_inspection.py (extended)
│   └── mission_validation.py (new)
├── sensors/
│   └── thermal_camera.py (extended)
└── models/
    ├── observation_uav.py (extended)
    └── capabilities.py (new)

tools/ui/
├── context/
│   ├── camera_context.py (new)
│   └── mission_context.py (extended)
├── qml/
│   └── panels/
│       ├── GimbalPanel.qml (extended)
│       ├── MissionPanel.qml (extended)
│       ├── SolarInspectionPanel.qml (new)
│       └── SeedingPanel.qml (new)
└── backend.py (extended)

tests/
├── test_solar_inspection.py (new)
├── test_seeding_planner.py (new)
├── test_camera_context.py (new)
├── test_capability_registry.py (new)
└── test_mode_state_machine.py (new)

docs/
├── user-guide/
│   ├── solar-inspection-tutorial.md (new)
│   └── seeding-tutorial.md (new)
└── api/
    ├── camera-api.md (new)
    └── mission-planning-api.md (updated)
```

## Appendix C: Configuration Examples

### Solar Inspection Config:
```yaml
solar_inspection:
  name: "Solar Farm A - June 2026"
  drone_id: "UAV_1"
  camera:
    profile: "RGB + Thermal"
    resolution: "1920x1080"
    hfov: 90
    vfov: 60
  thermal:
    enabled: true
    calibration: "Solar Panel"
    threshold: 80
    emissivity: 0.95
  flight:
    altitude: 20
    speed: 5
    overlap: 20
  rows:
    - {start: [47.123, 8.456], end: [47.124, 8.457]}
    - {start: [47.123, 8.458], end: [47.124, 8.459]}
```

### Seeding Config:
```yaml
seeding:
  field:
    boundary: [[47.1, 8.4], [47.1, 8.5], [47.2, 8.5], [47.2, 8.4]]
    exclusion_zones: [[[47.15, 8.45], [47.15, 8.46], [47.16, 8.46]]]
  crop:
    type: "Wheat"
    seed_spacing: 20
    row_spacing: 50
  dispenser:
    channel: 9
    open_pwm: 1900
    close_pwm: 1100
    drop_duration: 500
    seeds_per_pulse: 1
    tank_capacity: 5000
  flight:
    altitude: 10
    speed: 3
```

---

**End of Implementation Plan**

**Next Steps:**
1. Review plan with stakeholders
2. Prioritize phases based on user needs
3. Set up development environment
4. Begin Phase 1 implementation
5. Conduct weekly progress reviews