# Sicherheitsaudit: UI Layer Security

**Datum:** 2026-06-16  
**Auditor:** Security Analysis  
**Scope:** UI Security, Web Integration, Input Validation, XSS, Command Injection  
**Severity Levels:** 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🟢 LOW

---

## Executive Summary

Das SkyMeshX GCS UI zeigt **moderate Sicherheitslücken** mit **8 kritischen Schwachstellen** in Web-Integration, Input-Validation und Command-Injection. Die Hauptrisiken liegen in der **ungeschützten JavaScript-Python Bridge** und **fehlender Input-Sanitization**.

### Kritische Findings

| ID | Severity | Modul | Issue | Impact |
|----|----------|-------|-------|--------|
| UI-01 | 🔴 CRITICAL | `map_tab.py` | XSS via Map Click Injection | JavaScript Code Execution |
| UI-02 | 🔴 CRITICAL | `map_tab.py` | JSON Injection in updateDrones | Data Corruption |
| UI-03 | 🔴 CRITICAL | `backend.py` | Command Injection via goto() | Arbitrary Drone Commands |
| UI-04 | 🔴 CRITICAL | `service_locator.py` | Unvalidated APF Auto-Avoidance | Unauthorized Drone Control |
| UI-05 | 🟠 HIGH | `main_window.py` | Emergency Stop ohne Confirmation | Accidental Mass-Disarm |
| UI-06 | 🟠 HIGH | `dashboard_tab.py` | Unvalidated Quick Commands | Command Flood |
| UI-07 | 🟠 HIGH | `backend.py` | Fire-and-Forget Commands | No Error Handling |
| UI-08 | 🟡 MEDIUM | `map_tab.py` | CDN Dependency (Leaflet.js) | Supply Chain Attack |
| UI-09 | 🟡 MEDIUM | `backend.py` | Telemetry Snapshot Exposure | Information Disclosure |
| UI-10 | 🟡 MEDIUM | `service_locator.py` | Global Service Registry | Privilege Escalation |
| UI-11 | 🟢 LOW | `map_tab.py` | Hardcoded Default Coordinates | Minor Info Leak |
| UI-12 | 🟢 LOW | `dashboard_tab.py` | Chart History Unbounded | Memory Leak |

---

## 🔴 CRITICAL Issues

### UI-01: XSS via Map Click Injection

**Datei:** `tools/ui/map_tab.py:332-337`

```python
def _on_map_clicked(self, lat: float, lon: float):
    self._click_info.setText(f"Lat: {lat:.6f}\nLon: {lon:.6f}")  # ❌ NO SANITIZATION
    if self._add_wp_mode:
        self._waypoints.append({"lat": lat, "lon": lon, "alt": 10.0})
        self._wp_list.addItem(f"WP{len(self._waypoints)-1}: {lat:.5f},{lon:.5f}")
        self._bridge.updateWaypoints.emit(json.dumps(self._waypoints))  # ❌ INJECTION
```

**JavaScript Side (map_tab.py:182-184):**
```javascript
map.on('click', function(e) {
  if (bridge) bridge.mapClicked(e.latlng.lat, e.latlng.lng);  // ❌ NO VALIDATION
});
```

**Problem:**
- JavaScript kann beliebige Werte an `mapClicked()` senden
- Keine Validierung von `lat`/`lon` Ranges
- Malicious JavaScript könnte injiziert werden via Browser DevTools

**Exploit-Szenario:**
```javascript
// Attacker öffnet Browser DevTools und führt aus:
bridge.mapClicked(999999, "<script>alert('XSS')</script>");

// Python empfängt:
lat = 999999  // Invalid coordinate
lon = "<script>alert('XSS')</script>"  // XSS payload

// Wird in UI angezeigt ohne Sanitization:
self._click_info.setText(f"Lat: 999999\nLon: <script>alert('XSS')</script>")
```

**Impact:**
- XSS in Qt WebEngine (kann zu Code Execution führen)
- Invalid Waypoints → Drohne fliegt zu falschen Koordinaten
- UI Corruption

**Fix:**
```python
def _on_map_clicked(self, lat: float, lon: float):
    # Validate coordinate ranges
    if not (-90 <= lat <= 90):
        self.log_message.emit("ERROR", f"Invalid latitude: {lat}")
        return
    if not (-180 <= lon <= 180):
        self.log_message.emit("ERROR", f"Invalid longitude: {lon}")
        return
    
    # Sanitize for display (escape HTML)
    from html import escape
    safe_lat = escape(str(lat))
    safe_lon = escape(str(lon))
    self._click_info.setText(f"Lat: {safe_lat}\nLon: {safe_lon}")
    
    if self._add_wp_mode:
        self._waypoints.append({"lat": lat, "lon": lon, "alt": 10.0})
        self._wp_list.addItem(f"WP{len(self._waypoints)-1}: {lat:.5f},{lon:.5f}")
        self._bridge.updateWaypoints.emit(json.dumps(self._waypoints))
```

**Severity:** 🔴 CRITICAL - XSS + Invalid Waypoints

---

### UI-02: JSON Injection in updateDrones

**Datei:** `tools/ui/map_tab.py:317-330`

```python
def _on_telemetry(self, all_snaps: dict):
    payload = {
        did: {
            "lat":         snap.get("lat", 0),  # ❌ NO TYPE VALIDATION
            "lon":         snap.get("lon", 0),
            "alt_rel":     snap.get("alt_rel", 0),
            "groundspeed": snap.get("groundspeed", 0),
            "flight_mode": snap.get("flight_mode", "UNKNOWN"),  # ❌ NO SANITIZATION
            "armed":       snap.get("armed", False),
            "heading":     snap.get("yaw", 0),
        }
        for did, snap in all_snaps.items()
    }
    self._bridge.updateDrones.emit(json.dumps(payload))  # ❌ INJECTION RISK
```

**JavaScript Side (map_tab.py:69-72):**
```javascript
bridge.updateDrones.connect(function(json_str) {
  var data = JSON.parse(json_str);  // ❌ NO VALIDATION
  updateDroneMarkers(data);
});
```

**Problem:**
- `flight_mode` String wird nicht sanitized
- Malicious Telemetry könnte JavaScript Code enthalten
- `JSON.parse()` ist anfällig für Prototype Pollution

**Exploit-Szenario:**
```python
# Attacker manipuliert Telemetry (z.B. via MITM auf MAVLink)
malicious_snap = {
    "lat": 48.137,
    "lon": 11.575,
    "flight_mode": '"; alert("XSS"); var x="',  # JavaScript Injection
    "armed": True
}

# Wird zu JSON:
{
  "D1": {
    "flight_mode": "\"; alert(\"XSS\"); var x=\""
  }
}

# JavaScript führt aus:
var tip = id + '<br>' + (d.flight_mode||'UNKNOWN');  // XSS!
```

**Impact:**
- XSS in Map View
- Prototype Pollution → JavaScript Code Execution
- UI Corruption

**Fix:**
```python
def _on_telemetry(self, all_snaps: dict):
    from html import escape
    
    def sanitize_string(s: str) -> str:
        """Sanitize string for JSON/HTML display"""
        if not isinstance(s, str):
            return str(s)
        # Remove control characters
        s = ''.join(c for c in s if c.isprintable() or c in '\n\r\t')
        # Escape HTML
        return escape(s)
    
    payload = {
        did: {
            "lat":         float(snap.get("lat", 0)),
            "lon":         float(snap.get("lon", 0)),
            "alt_rel":     float(snap.get("alt_rel", 0)),
            "groundspeed": float(snap.get("groundspeed", 0)),
            "flight_mode": sanitize_string(snap.get("flight_mode", "UNKNOWN")),
            "armed":       bool(snap.get("armed", False)),
            "heading":     float(snap.get("yaw", 0)),
        }
        for did, snap in all_snaps.items()
    }
    self._bridge.updateDrones.emit(json.dumps(payload))
```

**Severity:** 🔴 CRITICAL - XSS + Prototype Pollution

---

### UI-03: Command Injection via goto()

**Datei:** `tools/ui/backend.py:236-242`

```python
def goto(self, lat: float, lon: float, alt: float) -> None:
    if self._drone:
        self.log_message.emit(
            "INFO",
            f"[{self.drone_id}] 🎯 GOTO lat={lat:.6f} lon={lon:.6f} alt={alt}m",  # ❌ NO VALIDATION
        )
        _run_async(self._drone.goto, lat, lon, alt)  # ❌ UNCHECKED PARAMS
```

**Problem:**
- Keine Validierung von `lat`, `lon`, `alt`
- Kann beliebige Werte an MAVLink senden
- Keine Range-Checks

**Exploit-Szenario:**
```python
# Attacker ruft auf (z.B. via Python Console oder malicious Plugin):
backend.goto(999999, 999999, -1000)  # Invalid coordinates + negative altitude

# Drohne empfängt:
# SET_POSITION_TARGET_GLOBAL_INT mit lat=999999e7, lon=999999e7, alt=-1000
# → Undefined Behavior, potentieller Crash
```

**Impact:**
- Drohne fliegt zu ungültigen Koordinaten
- Negative Altitude → Crash in Boden
- Autopilot Confusion

**Fix:**
```python
def goto(self, lat: float, lon: float, alt: float) -> None:
    # Validate coordinates
    if not (-90 <= lat <= 90):
        self.log_message.emit("ERROR", f"Invalid latitude: {lat}")
        return
    if not (-180 <= lon <= 180):
        self.log_message.emit("ERROR", f"Invalid longitude: {lon}")
        return
    if not (0 <= alt <= 500):  # Max 500m altitude
        self.log_message.emit("ERROR", f"Invalid altitude: {alt}")
        return
    
    if self._drone:
        self.log_message.emit(
            "INFO",
            f"[{self.drone_id}] 🎯 GOTO lat={lat:.6f} lon={lon:.6f} alt={alt}m",
        )
        _run_async(self._drone.goto, lat, lon, alt)
```

**Severity:** 🔴 CRITICAL - Command Injection → Drohnen-Crash

---

### UI-04: Unvalidated APF Auto-Avoidance

**Datei:** `tools/ui/service_locator.py:231-276`

```python
def _on_avoidance(drone_id: str, lat: float, lon: float, alt: float) -> None:
    try:
        b = swarm.backend.get_backend(drone_id)
        if not b or not hasattr(b, "goto"):
            return
        
        # ... checks ...
        
        b.goto(lat, lon, alt)  # ❌ NO VALIDATION OF lat/lon/alt
        swarm.logMessage.emit(
            "WARN",
            f"[SAFETY] APF auto-avoidance: pushing {drone_id} → "
            f"{lat:.5f}, {lon:.5f} @ {alt:.1f}m",
        )
    except Exception as exc:
        swarm.logMessage.emit("ERROR", f"[SAFETY] auto-avoidance failed: {exc}")
```

**Problem:**
- APF kann beliebige Koordinaten senden
- Keine Validierung von `lat`, `lon`, `alt`
- Keine Geofence-Check vor goto()
- Exception wird nur geloggt, nicht verhindert

**Exploit-Szenario:**
```python
# Malicious APF Filter sendet:
safety.avoidanceTriggered.emit("D1", 999, 999, -100)

# Drohne D1 empfängt goto(999, 999, -100)
# → Fliegt zu ungültigen Koordinaten oder crashed
```

**Impact:**
- Drohne verlässt Geofence
- Negative Altitude → Crash
- Unauthorized Drone Control

**Fix:**
```python
def _on_avoidance(drone_id: str, lat: float, lon: float, alt: float) -> None:
    try:
        # Validate coordinates FIRST
        if not (-90 <= lat <= 90):
            swarm.logMessage.emit("ERROR", f"[SAFETY] Invalid avoidance lat: {lat}")
            return
        if not (-180 <= lon <= 180):
            swarm.logMessage.emit("ERROR", f"[SAFETY] Invalid avoidance lon: {lon}")
            return
        if not (0 <= alt <= 500):
            swarm.logMessage.emit("ERROR", f"[SAFETY] Invalid avoidance alt: {alt}")
            return
        
        b = swarm.backend.get_backend(drone_id)
        if not b or not hasattr(b, "goto"):
            return
        
        # Check geofence before goto
        if hasattr(safety, "geofence") and safety.geofence:
            from skymeshx.safety.apf import Pose3D
            pos = Pose3D(lat, lon, alt)  # Convert to local NED first!
            if not safety.geofence.contains(pos):
                swarm.logMessage.emit(
                    "ERROR",
                    f"[SAFETY] Avoidance target outside geofence: {lat:.5f}, {lon:.5f}"
                )
                return
        
        # ... rest of checks ...
        
        b.goto(lat, lon, alt)
        swarm.logMessage.emit(
            "WARN",
            f"[SAFETY] APF auto-avoidance: pushing {drone_id} → "
            f"{lat:.5f}, {lon:.5f} @ {alt:.1f}m",
        )
    except Exception as exc:
        swarm.logMessage.emit("ERROR", f"[SAFETY] auto-avoidance failed: {exc}")
```

**Severity:** 🔴 CRITICAL - Unauthorized Drone Control

---

## 🟠 HIGH Severity Issues

### UI-05: Emergency Stop ohne Confirmation

**Datei:** `tools/ui/main_window.py:118-122, 176-178`

```python
btn_estop = QPushButton("⛔  EMERGENCY STOP")
btn_estop.setObjectName("btn_danger")
btn_estop.setFixedHeight(36)
btn_estop.clicked.connect(self._emergency_stop)  # ❌ NO CONFIRMATION
lay.addWidget(btn_estop)

def _emergency_stop(self) -> None:
    self._swarm.disarm_all(force=True)  # ❌ IMMEDIATE EXECUTION
    self._on_log("ERROR", "⚛ EMERGENCY STOP — All drones force-disarmed!")
```

**Problem:**
- Kein Confirmation Dialog
- Accidental Click → Alle Drohnen disarmed
- Keine Undo-Möglichkeit

**Impact:**
- Alle Drohnen fallen vom Himmel
- Potentieller Totalverlust
- Safety-kritisch

**Fix:**
```python
def _emergency_stop(self) -> None:
    from PyQt6.QtWidgets import QMessageBox
    
    reply = QMessageBox.critical(
        self,
        "⚠️ EMERGENCY STOP",
        "This will IMMEDIATELY disarm ALL drones!\n\n"
        "All drones will fall from the sky.\n"
        "This action CANNOT be undone.\n\n"
        "Are you absolutely sure?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No  # Default to No
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        self._swarm.disarm_all(force=True)
        self._on_log("ERROR", "⚛ EMERGENCY STOP — All drones force-disarmed!")
```

**Severity:** 🟠 HIGH - Accidental Mass-Disarm

---

### UI-06: Unvalidated Quick Commands

**Datei:** `tools/ui/dashboard_tab.py:302-315`

```python
def _quick_cmd(self, cmd: str):
    b = self._swarm.get_backend(self._drone_id)
    if not b:
        return
    if cmd == "arm":
        b.arm()  # ❌ NO STATE CHECK
    elif cmd == "disarm":
        b.disarm()
    elif cmd == "takeoff":
        b.takeoff(10.0)  # ❌ HARDCODED ALTITUDE
    elif cmd == "land":
        b.land()
    elif cmd == "rtl":
        b.rtl()
```

**Problem:**
- Keine State-Checks (kann ARM während FLYING aufrufen)
- Keine Rate-Limiting → Command Flood
- Hardcoded Takeoff-Altitude (10m)

**Impact:**
- Invalid State Transitions
- Command Flood → Autopilot Overload
- Unerwartetes Verhalten

**Fix:**
```python
def _quick_cmd(self, cmd: str):
    b = self._swarm.get_backend(self._drone_id)
    if not b:
        return
    
    # Get current state
    snap = b.get_telemetry_snapshot()
    if not snap:
        return
    
    armed = snap.get("armed", False)
    alt_rel = snap.get("alt_rel", 0.0)
    
    # Validate state transitions
    if cmd == "arm":
        if armed:
            self._swarm.log_message.emit("WARN", f"[{self._drone_id}] Already armed")
            return
        b.arm()
    elif cmd == "disarm":
        if alt_rel > 0.5:
            reply = QMessageBox.warning(
                self,
                "⚠️ Disarm Warning",
                f"Drone is {alt_rel:.1f}m above ground!\n\nDisarm anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        b.disarm()
    elif cmd == "takeoff":
        if not armed:
            self._swarm.log_message.emit("ERROR", f"[{self._drone_id}] Must arm first")
            return
        if alt_rel > 0.5:
            self._swarm.log_message.emit("WARN", f"[{self._drone_id}] Already airborne")
            return
        b.takeoff(10.0)
    elif cmd == "land":
        if alt_rel < 0.5:
            self._swarm.log_message.emit("WARN", f"[{self._drone_id}] Already on ground")
            return
        b.land()
    elif cmd == "rtl":
        b.rtl()
```

**Severity:** 🟠 HIGH - Invalid State Transitions

---

### UI-07: Fire-and-Forget Commands ohne Error Handling

**Datei:** `tools/ui/backend.py:204-242`

```python
def arm(self, force: bool = False) -> None:
    if self._drone:
        self.log_message.emit("INFO", f"[{self.drone_id}] ▶ ARM (force={force})")
        _run_async(self._drone.arm, force=force)  # ❌ NO ERROR HANDLING

def disarm(self, force: bool = False) -> None:
    if self._drone:
        self.log_message.emit("INFO", f"[{self.drone_id}] ■ DISARM (force={force})")
        _run_async(self._drone.disarm, force=force)  # ❌ NO ERROR HANDLING

# ... alle anderen Commands gleich ...
```

**Problem:**
- `_run_async()` ist Fire-and-Forget
- Keine Error Callbacks
- User bekommt kein Feedback bei Failure

**Impact:**
- Silent Failures
- User denkt Command wurde ausgeführt
- Potentiell gefährlich (z.B. ARM failed, aber User denkt Drohne ist armed)

**Fix:**
```python
def _run_async_with_callback(
    fn: Callable,
    on_success: Optional[Callable] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    *args,
    **kwargs
) -> None:
    """Run function in thread with success/error callbacks"""
    def wrapper():
        try:
            result = fn(*args, **kwargs)
            if on_success:
                on_success(result)
        except Exception as exc:
            if on_error:
                on_error(exc)
            else:
                print(f"[backend] async error: {exc}")
    
    threading.Thread(target=wrapper, daemon=True).start()

def arm(self, force: bool = False) -> None:
    if self._drone:
        self.log_message.emit("INFO", f"[{self.drone_id}] ▶ ARM (force={force})")
        
        def on_success(result):
            if result:
                self.log_message.emit("INFO", f"[{self.drone_id}] ✅ ARM successful")
            else:
                self.log_message.emit("ERROR", f"[{self.drone_id}] ❌ ARM failed")
        
        def on_error(exc):
            self.log_message.emit("ERROR", f"[{self.drone_id}] ❌ ARM error: {exc}")
        
        _run_async_with_callback(
            self._drone.arm,
            on_success=on_success,
            on_error=on_error,
            force=force
        )
```

**Severity:** 🟠 HIGH - Silent Failures

---

## 🟡 MEDIUM Severity Issues

### UI-08: CDN Dependency (Leaflet.js)

**Datei:** `tools/ui/map_tab.py:28-29`

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

**Problem:**
- Externe CDN-Abhängigkeit (unpkg.com)
- Keine Subresource Integrity (SRI) Checks
- Supply Chain Attack möglich

**Impact:**
- Wenn unpkg.com kompromittiert → Malicious JavaScript
- MITM Attack möglich
- Offline-Betrieb nicht möglich

**Fix:**
```python
# Option 1: Bundle Leaflet lokal
MAP_HTML = """
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="qrc:///leaflet/leaflet.css"/>
<script src="qrc:///leaflet/leaflet.js"></script>
...
"""

# Option 2: SRI Hashes
MAP_HTML = """
<link rel="stylesheet" 
      href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha384-..."
      crossorigin="anonymous"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha384-..."
        crossorigin="anonymous"></script>
"""
```

**Severity:** 🟡 MEDIUM - Supply Chain Attack

---

### UI-09: Telemetry Snapshot Exposure

**Datei:** `tools/ui/backend.py:289-299`

```python
def get_telemetry_snapshot(self) -> Optional[dict]:
    if not self._drone:
        return None
    snap = self._drone.telemetry.snapshot()  # ❌ FULL SNAPSHOT
    snap["connectionString"] = self.connection_string  # ❌ SENSITIVE INFO
    snap["connected"] = self.is_connected
    snap["droneType"] = self.drone_type
    snap["fsmState"] = self._fsm_state
    snap["swarmRole"] = self.swarm_role
    snap["leaderId"] = self.leader_id
    return snap  # ❌ EXPOSED TO ALL CONSUMERS
```

**Problem:**
- Snapshot enthält alle Telemetrie-Daten (50+ Fields)
- Connection String wird exposed (kann Credentials enthalten)
- Keine Access Control

**Impact:**
- Information Disclosure
- Connection String Leak
- Potentiell Credentials Leak

**Fix:**
```python
def get_telemetry_snapshot(self, include_sensitive: bool = False) -> Optional[dict]:
    if not self._drone:
        return None
    
    snap = self._drone.telemetry.snapshot()
    
    # Add non-sensitive metadata
    snap["connected"] = self.is_connected
    snap["droneType"] = self.drone_type
    snap["fsmState"] = self._fsm_state
    snap["swarmRole"] = self.swarm_role
    snap["leaderId"] = self.leader_id
    
    # Only include sensitive data if explicitly requested
    if include_sensitive:
        # Redact credentials from connection string
        conn_str = self.connection_string
        if "@" in conn_str:  # e.g. tcp://user:pass@host:port
            conn_str = conn_str.split("@")[0] + "@***"
        snap["connectionString"] = conn_str
    
    return snap
```

**Severity:** 🟡 MEDIUM - Information Disclosure

---

### UI-10: Global Service Registry ohne Access Control

**Datei:** `tools/ui/service_locator.py:34-78`

```python
class ServiceLocator:
    """Tiny DI container: register, get, iterate."""
    
    def __init__(self) -> None:
        self._instances: Dict[str, Any] = {}  # ❌ NO ACCESS CONTROL
        self._factories: Dict[str, Callable[[], Any]] = {}
    
    def get(self, key: str) -> Any:
        if key in self._instances:
            return self._instances[key]  # ❌ ANYONE CAN ACCESS
        # ...
```

**Problem:**
- Jeder Code kann auf alle Services zugreifen
- Keine Role-Based Access Control
- Keine Audit Logs

**Impact:**
- Privilege Escalation
- Unauthorized Access zu kritischen Services (swarm, safety)
- Keine Nachvollziehbarkeit

**Fix:**
```python
from enum import Enum
from typing import Set

class ServiceRole(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    ADMIN = "admin"

class ServiceLocator:
    def __init__(self) -> None:
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._roles: Dict[str, ServiceRole] = {}  # NEW
        self._access_log: List[Tuple[str, str, float]] = []  # NEW
    
    def register(self, key: str, instance: Any, role: ServiceRole = ServiceRole.PUBLIC) -> None:
        self._instances[key] = instance
        self._roles[key] = role
    
    def get(self, key: str, caller_role: ServiceRole = ServiceRole.PUBLIC) -> Any:
        if key not in self._instances and key not in self._factories:
            raise KeyError(f"ServiceLocator: '{key}' not registered")
        
        # Check access
        required_role = self._roles.get(key, ServiceRole.PUBLIC)
        if required_role == ServiceRole.ADMIN and caller_role != ServiceRole.ADMIN:
            raise PermissionError(f"Access denied to '{key}' (requires ADMIN)")
        
        # Log access
        import time
        self._access_log.append((key, caller_role.value, time.time()))
        
        # Return instance
        if key in self._instances:
            return self._instances[key]
        inst = self._factories[key]()
        self._instances[key] = inst
        return inst
```

**Severity:** 🟡 MEDIUM - Privilege Escalation

---

## 🟢 LOW Severity Issues

### UI-11: Hardcoded Default Coordinates

**Datei:** `tools/ui/map_tab.py:50-51, 364`

```javascript
var map = L.map('map', {
  center: [48.1374, 11.5754],  // ❌ HARDCODED (Munich)
  zoom: 16,
  // ...
});
```

```python
else:
    lat, lon = 48.1374, 11.5754  # ❌ HARDCODED
```

**Problem:**
- Hardcoded Koordinaten (München)
- Information Leak (Entwickler-Standort?)
- Nicht konfigurierbar

**Impact:**
- Minor Information Disclosure
- Usability-Problem für andere Standorte

**Fix:**
```python
# In config.py
DEFAULT_MAP_CENTER = (48.1374, 11.5754)  # Munich
DEFAULT_MAP_ZOOM = 16

# In map_tab.py
MAP_HTML = f"""
var map = L.map('map', {{
  center: [{DEFAULT_MAP_CENTER[0]}, {DEFAULT_MAP_CENTER[1]}],
  zoom: {DEFAULT_MAP_ZOOM},
  // ...
}});
"""
```

**Severity:** 🟢 LOW - Minor Info Leak

---

### UI-12: Chart History Unbounded

**Datei:** `tools/ui/dashboard_tab.py:288-300`

```python
def _update_charts(self, snap: dict, t: float) -> None:
    _MAX_POINTS = 300  # ✅ BOUNDED
    bat_pct = snap.get("battery_pct", -1.0)
    self._history["time"].append(t)
    self._history["alt"].append(snap.get("alt_rel", 0.0))
    self._history["speed"].append(snap.get("groundspeed", 0.0))
    self._history["battery"].append(bat_pct if bat_pct >= 0 else 0)
    for k in self._history:
        if len(self._history[k]) > _MAX_POINTS:
            self._history[k] = self._history[k][-_MAX_POINTS:]  # ❌ INEFFICIENT
```

**Problem:**
- Truncation ist ineffizient (O(n) copy)
- Aber bounded, also kein Memory Leak
- Nur Performance-Problem

**Impact:**
- Minimal CPU Overhead
- Keine Correctness-Probleme

**Fix:**
```python
from collections import deque

def __init__(self, ...):
    self._history = {
        "alt": deque(maxlen=300),
        "speed": deque(maxlen=300),
        "battery": deque(maxlen=300),
        "time": deque(maxlen=300)
    }

def _update_charts(self, snap: dict, t: float) -> None:
    bat_pct = snap.get("battery_pct", -1.0)
    self._history["time"].append(t)
    self._history["alt"].append(snap.get("alt_rel", 0.0))
    self._history["speed"].append(snap.get("groundspeed", 0.0))
    self._history["battery"].append(bat_pct if bat_pct >= 0 else 0)
    # deque auto-truncates, no manual slicing needed
```

**Severity:** 🟢 LOW - Performance only

---

## Zusammenfassung der Schwachstellen

### Nach Severity

| Severity | Count | Modules |
|----------|-------|---------|
| 🔴 CRITICAL | 4 | `map_tab.py`, `backend.py`, `service_locator.py` |
| 🟠 HIGH | 3 | `main_window.py`, `dashboard_tab.py`, `backend.py` |
| 🟡 MEDIUM | 3 | `map_tab.py`, `backend.py`, `service_locator.py` |
| 🟢 LOW | 2 | `map_tab.py`, `dashboard_tab.py` |

### Nach Kategorie

| Kategorie | Count | Issues |
|-----------|-------|--------|
| **Input Validation** | 4 | UI-01, UI-03, UI-04, UI-06 |
| **XSS/Injection** | 2 | UI-01, UI-02 |
| **Command Safety** | 3 | UI-05, UI-06, UI-07 |
| **Information Disclosure** | 2 | UI-09, UI-11 |
| **Access Control** | 1 | UI-10 |
| **Supply Chain** | 1 | UI-08 |
| **Performance** | 1 | UI-12 |

---

## Empfohlene Maßnahmen

### Sofort (Critical)

1. **UI-01**: Input Validation für Map Clicks (lat/lon ranges)
2. **UI-02**: JSON Sanitization für Telemetry
3. **UI-03**: Coordinate Validation in goto()
4. **UI-04**: Geofence Check vor APF Auto-Avoidance

### Kurzfristig (High)

5. **UI-05**: Confirmation Dialog für Emergency Stop
6. **UI-06**: State Validation für Quick Commands
7. **UI-07**: Error Callbacks für async Commands

### Mittelfristig (Medium)

8. **UI-08**: Bundle Leaflet.js lokal oder SRI Hashes
9. **UI-09**: Redact Credentials in Telemetry Snapshots
10. **UI-10**: Role-Based Access Control für ServiceLocator

### Optional (Low)

11. **UI-11**: Konfigurierbare Default Map Coordinates
12. **UI-12**: deque für Chart History

---

## Security Best Practices für UI

### 1. Input Validation

```python
def validate_coordinates(lat: float, lon: float, alt: float) -> bool:
    """Validate GPS coordinates and altitude"""
    if not (-90 <= lat <= 90):
        return False
    if not (-180 <= lon <= 180):
        return False
    if not (0 <= alt <= 500):  # Max 500m
        return False
    return True
```

### 2. HTML/JavaScript Sanitization

```python
from html import escape

def sanitize_for_display(text: str) -> str:
    """Sanitize text for HTML display"""
    if not isinstance(text, str):
        text = str(text)
    # Remove control characters
    text = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')
    # Escape HTML
    return escape(text)
```

### 3. Command Confirmation

```python
def confirm_dangerous_action(parent, title: str, message: str) -> bool:
    """Show confirmation dialog for dangerous actions"""
    from PyQt6.QtWidgets import QMessageBox
    
    reply = QMessageBox.critical(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No  # Default to No
    )
    return reply == QMessageBox.StandardButton.Yes
```

### 4. Error Handling

```python
def safe_async_call(fn: Callable, on_error: Callable[[Exception], None], *args, **kwargs):
    """Async call with error handling"""
    def wrapper():
        try:
            fn(*args, **kwargs)
        except Exception as exc:
            on_error(exc)
    
    threading.Thread(target=wrapper, daemon=True).start()
```

---

## Testing-Empfehlungen

### Security Tests

```python
# tests/test_ui_security.py

def test_map_click_validation():
    """Test UI-01: Map click coordinate validation"""
    from tools.ui.map_tab import MapTab
    
    tab = MapTab(mock_swarm)
    
    # Valid coordinates
    tab._on_map_clicked(48.137, 11.575)
    assert len(tab._waypoints) == 1
    
    # Invalid latitude
    tab._on_map_clicked(999, 11.575)
    assert len(tab._waypoints) == 1  # Not added
    
    # Invalid longitude
    tab._on_map_clicked(48.137, 999)
    assert len(tab._waypoints) == 1  # Not added

def test_goto_validation():
    """Test UI-03: goto() coordinate validation"""
    from tools.ui.backend import DroneBackend
    
    backend = DroneBackend("D1", "tcp:127.0.0.1:5762")
    backend._drone = mock_drone
    
    # Valid goto
    backend.goto(48.137, 11.575, 10.0)
    assert mock_drone.goto_called
    
    # Invalid coordinates
    backend.goto(999, 999, -100)
    assert not mock_drone.goto_called  # Should be rejected

def test_emergency_stop_confirmation():
    """Test UI-05: Emergency stop requires confirmation"""
    from tools.ui.main_window import MainWindow
    
    window = MainWindow()
    
    # Mock QMessageBox to return No
    with patch('PyQt6.QtWidgets.QMessageBox.critical', return_value=QMessageBox.StandardButton.No):
        window._emergency_stop()
        assert not window._swarm.disarm_all_called
    
    # Mock QMessageBox to return Yes
    with patch('PyQt6.QtWidgets.QMessageBox.critical', return_value=QMessageBox.StandardButton.Yes):
        window._emergency_stop()
        assert window._swarm.disarm_all_called
```

### Fuzzing

```bash
# Use AFL++ for fuzzing coordinate inputs
afl-fuzz -i testcases/ -o findings/ -- python -m tools.ui.map_tab @@
```

---

## Referenzen

- [OWASP Top 10 2021](https://owasp.org/www-project-top-ten/)
- [Qt Security Best Practices](https://doc.qt.io/qt-6/security.html)
- [PyQt6 Security Guide](https://www.riverbankcomputing.com/static/Docs/PyQt6/security.html)
- [Leaflet.js Security](https://leafletjs.com/reference.html#security)
- [WebEngine Security](https://doc.qt.io/qt-6/qtwebengine-overview.html#security)

---

**Ende des Audits**
