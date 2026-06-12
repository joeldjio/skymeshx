# Drag-and-Drop Waypoint Editing

## Overview

The UAV Research GCS now supports intuitive drag-and-drop editing of mission waypoints directly on the map. This feature allows operators to quickly adjust flight paths by simply dragging waypoint markers to new positions.

## Features

### Interactive Waypoint Markers

- **Draggable Markers**: All waypoint markers on the map are draggable
- **Visual Feedback**: Markers become semi-transparent (60% opacity) during drag
- **Real-time Updates**: Connection lines between waypoints update dynamically as you drag
- **Altitude Preservation**: Waypoint altitude is automatically preserved when repositioning

### User Experience

1. **Start Dragging**: Click and hold on any waypoint marker
2. **Move**: Drag the marker to the desired location
3. **Release**: Drop the marker at the new position
4. **Automatic Update**: The waypoint list is automatically updated with the new coordinates

### Visual Indicators

- **Normal State**: Waypoint markers display with full opacity (100%)
- **Dragging State**: 
  - Marker opacity reduces to 60%
  - Connection lines become semi-transparent (30% opacity)
- **After Drop**: 
  - Marker returns to full opacity
  - Connection lines return to normal opacity (70%)

## Technical Implementation

### Architecture

The drag-and-drop functionality is implemented using:

1. **Leaflet.js Draggable Markers**: Waypoint markers are created with `draggable: true`
2. **Event Handlers**: Three event handlers manage the drag lifecycle:
   - `dragstart`: Reduces opacity for visual feedback
   - `drag`: Updates connection lines in real-time
   - `dragend`: Notifies QML and restores opacity

3. **QML Signal**: `waypointMoved(int index, real lat, real lon)` signal communicates position changes
4. **Model Update**: `handleWaypointMoved()` function updates the waypoint model

### Code Flow

```
User drags marker
    ↓
JavaScript: marker.on("dragstart")
    ↓
Visual feedback (opacity change)
    ↓
JavaScript: marker.on("drag")
    ↓
Update connection lines
    ↓
JavaScript: marker.on("dragend")
    ↓
Emit QML signal via window.location
    ↓
QML: onNavigationRequested
    ↓
QML: handleWaypointMoved()
    ↓
Update globalMissionWaypoints model
```

### Files Modified

- `tools/ui/qml/MapView.qml`: Added draggable marker creation and event handlers
- `tools/ui/qml/main.qml`: Added `handleWaypointMoved()` function and signal connection
- `tests/test_ui_waypoint_drag.py`: Comprehensive test suite

## Usage Examples

### Basic Waypoint Repositioning

1. Open the Map tab
2. Add waypoints using "ADD WAYPOINT" mode or by clicking on the map
3. Click and drag any waypoint marker to reposition it
4. The waypoint list automatically updates with new coordinates

### Mission Planning Workflow

1. **Initial Planning**: Add waypoints in approximate positions
2. **Fine-tuning**: Drag waypoints to precise locations
3. **Verification**: Check connection lines to ensure proper flight path
4. **Execution**: Upload mission to drone(s)

### Multi-Waypoint Adjustment

- Drag multiple waypoints sequentially
- Connection lines update after each drag
- All waypoints maintain their sequence order
- Altitude values are preserved for each waypoint

## Limitations and Considerations

### Current Limitations

1. **Altitude Editing**: Altitude must still be edited via the waypoint list or input field
2. **Batch Operations**: Waypoints must be moved individually (no multi-select)
3. **Undo/Redo**: No undo functionality for drag operations (use manual coordinate entry to revert)

### Best Practices

- **Zoom Level**: Zoom in for precise positioning
- **Connection Lines**: Use connection lines to verify flight path geometry
- **Altitude Awareness**: Remember that dragging only changes lat/lon, not altitude
- **Mission Validation**: Always verify the complete mission before upload

## Performance

- **Real-time Updates**: Connection lines update smoothly during drag (no lag)
- **Memory Efficient**: No additional memory overhead for drag functionality
- **Responsive**: Works smoothly with up to 50+ waypoints

## Testing

The feature includes comprehensive unit tests covering:

- Marker draggability
- Signal emission
- Model updates
- Altitude preservation
- Visual feedback
- Line updates
- Error handling (invalid indices)

Run tests with:
```bash
pytest tests/test_ui_waypoint_drag.py -v
```

## Future Enhancements

Potential improvements for future versions:

1. **Multi-select Drag**: Select and drag multiple waypoints simultaneously
2. **Altitude Editing**: Drag vertically to adjust altitude
3. **Snap-to-Grid**: Optional grid snapping for precise alignment
4. **Undo/Redo**: Full undo/redo support for drag operations
5. **Keyboard Modifiers**: Hold Shift for constrained movement (horizontal/vertical only)
6. **Distance Display**: Show distance from original position during drag

## Troubleshooting

### Waypoint Won't Drag

- **Check Map Mode**: Ensure you're not in "ADD WAYPOINT" mode
- **Verify Waypoint**: Confirm the waypoint is visible on the map
- **Browser Compatibility**: Ensure WebEngine is properly initialized

### Position Not Updating

- **Check Console**: Look for "Waypoint X moved to..." log messages
- **Model Sync**: Verify `globalMissionWaypoints` model is accessible
- **Signal Connection**: Ensure `waypointMoved` signal is connected in main.qml

### Visual Glitches

- **Refresh Map**: Switch tabs and return to Map tab
- **Clear and Re-add**: Remove and re-add waypoints if lines don't update
- **Zoom Reset**: Reset zoom level if markers appear misaligned

## Related Documentation

- [Mission Planning Guide](../setup/px4-mission-upload.md)
- [UI Documentation](ui-documentation.md)
- [Map View Features](../api/overview.md)

## Changelog

### Version 0.4.0 (2026-06-11)

- **Added**: Drag-and-drop waypoint editing
- **Added**: Real-time connection line updates
- **Added**: Visual feedback during drag operations
- **Added**: Comprehensive test suite (11 tests)
- **Fixed**: JavaScript string escaping in MapView.qml
- **Fixed**: Waypoint index resolution bug when adding/removing waypoints
- **Improved**: Waypoint toolbar translated to English
- **Improved**: Dynamic index lookup instead of stored index (prevents stale references)