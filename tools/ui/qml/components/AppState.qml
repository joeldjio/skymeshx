pragma Singleton
import QtQuick

// ── Global UI state ───────────────────────────────────────────────────
// Replaces ad-hoc properties scattered across main.qml.
// Anyone can read/write the active selection via:
//   Cmp.AppState.selectedDroneId = "drone-1"
//
// Listening for changes:
//   Connections {
//       target: Cmp.AppState
//       function onSelectedDroneIdChanged() { … }
//   }
QtObject {
    id: state

    // ── Drone selection ───────────────────────────────────────────────
    property string selectedDroneId: ""

    // ── Map interaction modes ─────────────────────────────────────────
    property bool   mapPickMode:    false

    // ── Cached UI counts (driven by Python contexts) ──────────────────
    property int    droneCount:     0
    property int    connectedCount: 0

    // ── Multi-drone Mission Target Selection ──────────────────────────
    // Set of drone IDs that should receive the next "Start Mission" call.
    // Stored as a JS object {id: true} so QML can do O(1) lookups.
    // When the set is empty, callers fall back to ``selectedDroneId``.
    property var missionTargetIds:   ({})
    property int missionTargetCount: 0   // mirrors size of missionTargetIds

    signal missionTargetsChanged()

    function isMissionTarget(did) { return state.missionTargetIds[did] === true }

    function toggleMissionTarget(did) {
        // Always create a new object so the property assignment triggers
        // QML bindings — assigning the same reference is a no-op for the
        // binding engine even if the content changed.
        var m = Object.assign({}, state.missionTargetIds)
        if (m[did]) delete m[did]; else m[did] = true
        state.missionTargetIds = m
        var c = 0; for (var k in m) c++
        state.missionTargetCount = c
        state.missionTargetsChanged()
    }

    function clearMissionTargets() {
        state.missionTargetIds = ({})
        state.missionTargetCount = 0
        state.missionTargetsChanged()
    }

    function effectiveMissionTargets() {
        var ids = []
        for (var k in state.missionTargetIds) ids.push(k)
        if (ids.length === 0 && state.selectedDroneId) ids.push(state.selectedDroneId)
        return ids
    }

    // ── Per-Drone Waypoint Storage ────────────────────────────────────
    // Structure: { droneId: [{lat, lon, alt}, ...], ... }
    property var droneWaypoints: ({})
    
    signal waypointsChanged(string droneId)
    
    function getWaypoints(droneId) {
        return state.droneWaypoints[droneId] || []
    }
    
    function setWaypoints(droneId, waypoints) {
        var w = Object.assign({}, state.droneWaypoints)
        w[droneId] = waypoints
        state.droneWaypoints = w
        state.waypointsChanged(droneId)
    }
    
    function addWaypoint(droneId, lat, lon, alt) {
        var wps = state.getWaypoints(droneId).slice() // copy
        wps.push({lat: lat, lon: lon, alt: alt})
        state.setWaypoints(droneId, wps)
    }
    
    function clearWaypoints(droneId) {
        state.setWaypoints(droneId, [])
    }
    
    function clearAllWaypoints() {
        state.droneWaypoints = ({})
    }
    
    // ── Multi-Drone Waypoint Operations ───────────────────────────────
    function setWaypointsForMultiple(droneIds, waypoints) {
        var w = Object.assign({}, state.droneWaypoints)
        for (var i = 0; i < droneIds.length; i++) {
            w[droneIds[i]] = waypoints
        }
        state.droneWaypoints = w
        // Emit for all affected drones
        for (var i = 0; i < droneIds.length; i++) {
            state.waypointsChanged(droneIds[i])
        }
    }
    
    function addWaypointForMultiple(droneIds, lat, lon, alt) {
        var w = Object.assign({}, state.droneWaypoints)
        for (var i = 0; i < droneIds.length; i++) {
            var wps = (w[droneIds[i]] || []).slice()
            wps.push({lat: lat, lon: lon, alt: alt})
            w[droneIds[i]] = wps
        }
        state.droneWaypoints = w
        for (var i = 0; i < droneIds.length; i++) {
            state.waypointsChanged(droneIds[i])
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────
    function selectDrone(id) { selectedDroneId = id }
    function clearSelection() { selectedDroneId = "" }
    function hasSelection()   { return selectedDroneId !== "" }
}
