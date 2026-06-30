# Mode Mutex Fix - June 2026

## Problem

Map interaction modes (waypoint adding, boundary drawing, solar row drawing) could overlap, causing confusion and unexpected behavior:

1. User in Solar mode clicks "Draw on Map"
2. User switches to Seeding mode
3. User clicks "Draw Boundary"
4. **Result**: Both solar row drawing AND boundary drawing active simultaneously

## Solution

Implemented a **minimal mode mutex system** that ensures only one map interaction mode is active at a time.

### Changes

#### 1. Added `cancelAllMapModes()` Function (main.qml)

```qml
function cancelAllMapModes() {
    // Cancel waypoint mode
    if (mapWaypointMode) {
        mapWaypointMode = false
        if (mapLoader.item) mapLoader.item.setPickMode(false)
    }
    
    // Cancel pick mode
    if (mapPickMode) {
        mapPickMode = false
        if (mapLoader.item) mapLoader.item.setPickMode(false)
        _mapPickTarget = null
    }
    
    // Cancel boundary drawing
    if (typeof mission !== "undefined" && mission && mission.drawingMode) {
        mission.cancelDrawingBoundary()
    }
    
    // Cancel solar row drawing
    if (typeof mission !== "undefined" && mission && mission.addingSolarRow) {
        mission.cancelSolarRowDrawing()
    }
}
```

#### 2. ESC Key Support (main.qml)

```qml
Shortcut {
    sequence: "Escape"
    context: Qt.ApplicationShortcut
    onActivated: {
        root.cancelAllMapModes()
        root._scFeedback("Map modes cancelled")
    }
}
```

#### 3. Cancel on Mission Mode Switch (MissionPanel.qml)

When switching between Coverage/Seeding/Solar modes:

```qml
onClicked: {
    if (mission && root.Window.window) {
        root.Window.window.cancelAllMapModes()
        mission.missionMode = 0  // or 1, or 2
    }
}
```

#### 4. Added Missing Methods (mission_context.py)

```python
@Slot()
def cancelSolarRowDrawing(self):
    """Cancel solar row drawing mode."""
    self._adding_solar_row = False
    self._solar_row_start_lat = 0.0
    self._solar_row_start_lon = 0.0
    self.solarRowDrawingModeChanged.emit(False)
    self.logMessage.emit("INFO", "[SOLAR] ❌ Solar row drawing cancelled")

@Property(bool, notify=solarRowDrawingModeChanged)
def addingSolarRow(self):
    """Return whether solar row drawing mode is active."""
    return self._adding_solar_row
```

## How It Works

### Before Fix
```
User Flow:
1. Solar mode → Click "Draw on Map" → Solar row drawing active
2. Switch to Seeding mode → Solar row drawing STILL active
3. Click "Draw Boundary" → BOTH modes active ❌
4. Click on map → Confusion! Which mode is active?
```

### After Fix
```
User Flow:
1. Solar mode → Click "Draw on Map" → Solar row drawing active
2. Switch to Seeding mode → cancelAllMapModes() called
   → Solar row drawing cancelled ✓
3. Click "Draw Boundary" → Only boundary drawing active ✓
4. Press ESC → All modes cancelled ✓
```

## Solar Mode UX

### Current Behavior
- Click "Add Row" button
- Click **two points** on map (start and end of solar panel row)
- Waypoints are generated **along the line** between the two points
- Each row is a **straight line** representing a row of solar panels

### Why Two Points?
Solar panels are typically arranged in **straight rows**. The two points define:
1. **Start point**: Beginning of the panel row
2. **End point**: End of the panel row

The system then generates inspection waypoints along this line with:
- Configured altitude
- Gimbal pitch (camera angle)
- Trigger distance (photo spacing)
- Overlap percentage

### Adding Multiple Rows
After adding a row:
- Drawing mode stays active
- Click two more points to add another row
- Press **ESC** to finish and exit drawing mode

### Future Improvements
Consider adding:
1. **Polygon support**: Define complex panel layouts
2. **Grid mode**: Automatically generate rows in a rectangular area
3. **Visual preview**: Show waypoints before confirming
4. **Row editing**: Modify existing rows

## Testing

### Test Scenarios

1. **Mode Switching**:
   - Start boundary drawing in Coverage mode
   - Switch to Solar mode
   - Verify boundary drawing is cancelled

2. **ESC Key**:
   - Start any drawing mode
   - Press ESC
   - Verify mode is cancelled and feedback shown

3. **Multiple Modes**:
   - Try to activate multiple modes
   - Verify only one is active at a time

4. **Solar Row Drawing**:
   - Add multiple rows
   - Press ESC to finish
   - Verify all rows are preserved

## Files Modified

- [`tools/ui/qml/main.qml`](../../tools/ui/qml/main.qml) - Added `cancelAllMapModes()` and ESC shortcut
- [`tools/ui/qml/panels/MissionPanel.qml`](../../tools/ui/qml/panels/MissionPanel.qml) - Call `cancelAllMapModes()` on mode switch
- [`tools/ui/context/mission_context.py`](../../tools/ui/context/mission_context.py) - Added `cancelSolarRowDrawing()` and `addingSolarRow` property

## Related Issues

- Fixes mode overlap bug
- Improves UX consistency
- Makes ESC key work globally
- Clarifies solar inspection workflow