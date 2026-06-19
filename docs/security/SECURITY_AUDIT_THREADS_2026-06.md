# Sicherheitsaudit: Thread-Safety & Race Conditions

**Datum:** 2026-06-16  
**Auditor:** Security Analysis  
**Scope:** Thread-Safety, Race Conditions, Deadlocks, Resource Management  
**Severity Levels:** 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM | 🟢 LOW

---

## Executive Summary

Das SkyMeshX-Projekt zeigt **gute Thread-Safety-Grundlagen** mit konsequenter Lock-Verwendung in Kernmodulen. Es wurden jedoch **12 kritische Schwachstellen** identifiziert, die zu Race Conditions, Deadlocks oder Datenverlust führen können.

### Kritische Findings

| ID | Severity | Modul | Issue | Impact |
|----|----------|-------|-------|--------|
| TS-01 | 🔴 CRITICAL | `connection.py` | Ungeschützter Callback-Dispatch | Race Condition bei Listener-Modifikation |
| TS-02 | 🔴 CRITICAL | `apf.py` | Shared Mutable State ohne Lock | Race Condition bei `_prev_positions` |
| TS-03 | 🟠 HIGH | `mission.py` | Mission Build nicht Thread-Safe | Concurrent Add führt zu korrupten Waypoints |
| TS-04 | 🟠 HIGH | `connection.py` | `_pending_cmds` Race Condition | Verlorene Command ACKs |
| TS-05 | 🟠 HIGH | `fsm.py` | Callback während Lock | Deadlock-Risiko bei Re-Entry |
| TS-06 | 🟡 MEDIUM | `telemetry.py` | Direct Field Access | Dokumentation vs. Realität |
| TS-07 | 🟡 MEDIUM | `apf.py` | `APFFilterLoop` Stop Race | Thread läuft nach `stop()` |
| TS-08 | 🟡 MEDIUM | `connection.py` | Reconnect Backoff Race | `_stop` Check ohne Lock |
| TS-09 | 🟡 MEDIUM | `mission.py` | Upload Abort Race | `_abort_event` nicht atomar |
| TS-10 | 🟢 LOW | `connection.py` | `last_nack` ohne Lock | Kosmetisches Problem |
| TS-11 | 🟢 LOW | `apf.py` | `_obstacles` nicht Thread-Safe | Selten verwendet |
| TS-12 | 🟢 LOW | `fsm.py` | History Truncation Race | Minimaler Impact |

---

## 🔴 CRITICAL Issues

### TS-01: Ungeschützter Callback-Dispatch in MAVLinkConnection

**Datei:** `skymeshx/core/connection.py:420-425`

```python
def _emit(self, event: str, *args):
    for cb in self._listeners.get(event, []):  # ❌ RACE CONDITION
        try:
            cb(*args)
        except Exception as e:
            print(f"[core] listener error ({event}): {e}")
```

**Problem:**
- `_listeners` wird ohne Lock gelesen
- Concurrent `on()` oder `off()` während `_emit()` → Iterator-Invalidierung
- Kann zu `RuntimeError: dictionary changed size during iteration` führen

**Exploit-Szenario:**
```python
# Thread 1: Receive loop
conn._emit("telemetry", telemetry)  # Iteriert über _listeners["telemetry"]

# Thread 2: UI Thread
conn.off("telemetry", old_callback)  # Modifiziert _listeners während Iteration
```

**Impact:**
- Crash der Receive-Loop → Verbindungsverlust
- Verlorene Telemetrie-Updates
- Potentieller Datenverlust bei kritischen Events (armed, mode)

**Fix:**
```python
def _emit(self, event: str, *args):
    with self._lock:
        callbacks = list(self._listeners.get(event, []))  # Snapshot
    for cb in callbacks:
        try:
            cb(*args)
        except Exception as e:
            print(f"[core] listener error ({event}): {e}")
```

**Severity:** 🔴 CRITICAL - Kann zu Verbindungsabbruch führen

---

### TS-02: Shared Mutable State in APFSafetyFilter

**Datei:** `skymeshx/safety/apf.py:180-181, 317-318`

```python
class APFSafetyFilter:
    def __init__(self, ...):
        self._prev_positions: Dict[str, Pose3D] = {}  # ❌ NO LOCK
        self._prev_velocities: Dict[str, Pose3D] = {}  # ❌ NO LOCK
    
    def filter(self, positions, desired):
        # Line 317-318: Concurrent modification
        self._prev_positions[drone_id] = pos  # ❌ RACE CONDITION
        self._prev_velocities[drone_id] = new_velocity
```

**Problem:**
- `filter()` ist als "stateless and thread-safe" dokumentiert (Zeile 148-150)
- Aber modifiziert `_prev_positions` und `_prev_velocities` ohne Lock
- Concurrent `filter()` Aufrufe → Race Condition

**Exploit-Szenario:**
```python
# Thread 1: APF Filter Loop (20 Hz)
safe1 = apf.filter(positions, desired)  # Schreibt _prev_positions

# Thread 2: Mission Coordinator
safe2 = apf.filter(positions, desired)  # Liest/Schreibt _prev_positions gleichzeitig
```

**Impact:**
- Inkonsistente Velocity-Berechnungen
- Falsche Kollisionsvermeidung
- Potentieller Drohnen-Crash bei falschen Repulsion Forces

**Fix:**
```python
class APFSafetyFilter:
    def __init__(self, ...):
        self._prev_positions: Dict[str, Pose3D] = {}
        self._prev_velocities: Dict[str, Pose3D] = {}
        self._state_lock = threading.Lock()  # NEW
    
    def filter(self, positions, desired):
        with self._state_lock:
            # ... existing logic ...
            self._prev_positions[drone_id] = pos
            self._prev_velocities[drone_id] = new_velocity
```

**Severity:** 🔴 CRITICAL - Sicherheitskritisch, kann zu Kollisionen führen

---

## 🟠 HIGH Severity Issues

### TS-03: Mission Build nicht Thread-Safe

**Datei:** `skymeshx/control/mission.py:52-56, 92-96`

```python
class MissionEngine:
    """
    Thread Safety
    -------------
    Mission building (add/clear) is NOT thread-safe - build from one thread only.
    upload() spawns a background thread and is safe to call from any thread.
    """
    
    def clear(self):
        self._waypoints.clear()  # ❌ NO LOCK
    
    def add(self, wp: Waypoint):
        self._waypoints.append(wp)  # ❌ NO LOCK
```

**Problem:**
- Dokumentiert als "NOT thread-safe"
- Aber keine Enforcement (kein Lock, keine Assertion)
- Entwickler können versehentlich concurrent `add()` aufrufen

**Exploit-Szenario:**
```python
# Thread 1: UI Thread
mission.add(Waypoint(lat=48.1, lon=11.5, alt=10))

# Thread 2: LLM Commander
mission.add(Waypoint(lat=48.2, lon=11.6, alt=10))  # Concurrent append
```

**Impact:**
- Korrupte Waypoint-Liste (verlorene Waypoints)
- Falsche Mission-Reihenfolge
- Potentieller Crash bei `list.append()` Race

**Fix Option 1 (Defensive):**
```python
def __init__(self, ...):
    self._waypoints: List[Waypoint] = []
    self._build_lock = threading.Lock()
    self._build_thread_id: Optional[int] = None

def add(self, wp: Waypoint):
    current_thread = threading.get_ident()
    if self._build_thread_id is None:
        self._build_thread_id = current_thread
    elif self._build_thread_id != current_thread:
        raise RuntimeError("Mission building must be done from a single thread")
    self._waypoints.append(wp)
```

**Fix Option 2 (Lock-based):**
```python
def __init__(self, ...):
    self._waypoints: List[Waypoint] = []
    self._build_lock = threading.Lock()

def add(self, wp: Waypoint):
    with self._build_lock:
        self._waypoints.append(wp)
```

**Severity:** 🟠 HIGH - Kann zu falschen Missionen führen

---

### TS-04: `_pending_cmds` Race Condition

**Datei:** `skymeshx/core/connection.py:197-198, 447-453, 678-679`

```python
class MAVLinkConnection:
    def __init__(self, ...):
        self._pending_cmds: Dict[int, float] = {}  # ❌ Shared between threads
        self._cmd_lock = threading.Lock()
    
    def _command_long(self, cmd, ...):
        # ... send command ...
        with self._cmd_lock:
            self._pending_cmds[int(cmd)] = time.time()
            cutoff = time.time() - 10.0
            stale = [k for k, t in self._pending_cmds.items() if t < cutoff]  # ❌ RACE
            for k in stale:
                self._pending_cmds.pop(k, None)
    
    def _parse(self, msg):
        # ...
        elif t == "COMMAND_ACK":
            # ...
            with self._cmd_lock:
                self._pending_cmds.pop(cmd_id, None)  # ✅ Protected
```

**Problem:**
- `_command_long()` iteriert über `_pending_cmds.items()` während Lock gehalten wird
- Aber `pop()` während Iteration kann zu `RuntimeError` führen
- Cleanup-Logik ist ineffizient (O(n) bei jedem Command)

**Impact:**
- Potentieller Crash bei Command-Flood
- Verlorene Command ACKs
- Memory Leak bei vielen Commands

**Fix:**
```python
def _command_long(self, cmd, ...):
    # ... send command ...
    with self._cmd_lock:
        self._pending_cmds[int(cmd)] = time.time()
        # Cleanup: Remove stale entries (more efficient)
        if len(self._pending_cmds) > 100:  # Only cleanup when needed
            cutoff = time.time() - 10.0
            self._pending_cmds = {
                k: t for k, t in self._pending_cmds.items() if t >= cutoff
            }
```

**Severity:** 🟠 HIGH - Kann zu Command-Verlust führen

---

### TS-05: Callback während Lock in StateMachine

**Datei:** `skymeshx/core/fsm.py:135-166`

```python
def transition(self, new_state: DroneState, force: bool = False) -> bool:
    with self._lock:
        # ... state transition logic ...
        old = self._state
        self._prev  = old
        self._state = new_state
        self._history.append((time.time(), old, new_state))
    # Outside lock
    for cb in self._callbacks:  # ❌ Callbacks außerhalb Lock
        try:
            cb(old, new_state)
        except Exception as e:
            print(f"[fsm:{self.drone_id}] callback error: {e}")
    return True
```

**Problem:**
- Callbacks werden **außerhalb** des Locks aufgerufen
- Aber `_callbacks` Liste wird ohne Lock gelesen
- Concurrent `on_transition()` während Callback-Dispatch → Race

**Zusätzliches Deadlock-Risiko:**
```python
# Callback ruft transition() erneut auf
def on_state_change(old, new):
    if new == DroneState.FLYING:
        fsm.transition(DroneState.MISSION)  # Re-entry OK (Lock außerhalb)
```

**Impact:**
- Iterator-Invalidierung bei Callback-Modifikation
- Potentieller Crash der FSM
- Verlorene State-Transitions

**Fix:**
```python
def transition(self, new_state: DroneState, force: bool = False) -> bool:
    with self._lock:
        # ... state transition logic ...
        callbacks = list(self._callbacks)  # Snapshot
    # Outside lock
    for cb in callbacks:
        try:
            cb(old, new_state)
        except Exception as e:
            print(f"[fsm:{self.drone_id}] callback error: {e}")
    return True
```

**Severity:** 🟠 HIGH - Kann FSM korrumpieren

---

## 🟡 MEDIUM Severity Issues

### TS-06: Direct Field Access in TelemetryState

**Datei:** `skymeshx/core/telemetry.py:7-9, 28-79`

```python
"""
Thread Safety
-------------
TelemetryState is thread-safe. The update() and snapshot() methods
use an internal lock to protect concurrent access to telemetry fields.
Direct field access is NOT thread-safe - always use update()/snapshot().
"""

@dataclass
class TelemetryState:
    lat:           float = 0.0  # ❌ Public field, direct access möglich
    lon:           float = 0.0
    # ... 50+ weitere public fields
```

**Problem:**
- Dokumentation sagt "Direct field access is NOT thread-safe"
- Aber alle Fields sind public → Entwickler können direkt zugreifen
- Keine Enforcement durch Properties oder Private Fields

**Exploit-Szenario:**
```python
# Thread 1: Connection receive loop
telemetry.update(lat=48.137, lon=11.575)

# Thread 2: UI Thread
lat = telemetry.lat  # ❌ Direct access, keine Garantie für Konsistenz
lon = telemetry.lon  # Könnte von altem Update sein
```

**Impact:**
- Inkonsistente Telemetrie-Reads
- UI zeigt falsche Koordinaten
- Potentiell gefährlich bei Safety-Checks

**Fix Option 1 (Properties):**
```python
@dataclass
class TelemetryState:
    _lat: float = field(default=0.0, repr=False)
    _lon: float = field(default=0.0, repr=False)
    
    @property
    def lat(self) -> float:
        with self._lock:
            return self._lat
    
    @property
    def lon(self) -> float:
        with self._lock:
            return self._lon
```

**Fix Option 2 (Dokumentation + Linting):**
```python
# Add to .pylintrc or ruff.toml
# Warn on direct field access to TelemetryState
```

**Severity:** 🟡 MEDIUM - Dokumentation vs. Realität, aber Impact begrenzt

---

### TS-07: APFFilterLoop Stop Race

**Datei:** `skymeshx/safety/apf.py:381-399`

```python
class APFFilterLoop:
    def stop(self):
        self._running = False  # ❌ Keine Garantie, dass Thread stoppt
    
    def _loop(self):
        while self._running:  # ❌ Kein Lock, kein Event
            t0 = time.monotonic()
            try:
                # ... filter logic ...
            except Exception as e:
                print(f"[apf] filter error: {e}")
            elapsed = time.monotonic() - t0
            time.sleep(max(0, self._dt - elapsed))  # ❌ Kann lange dauern
```

**Problem:**
- `stop()` setzt nur Flag, wartet nicht auf Thread-Ende
- Thread kann noch bis zu `_dt` Sekunden (50ms) weiterlaufen
- Kein `join()` oder Timeout

**Impact:**
- Resource Leak (Thread läuft nach `stop()`)
- Callbacks werden nach `stop()` noch aufgerufen
- Potentieller Crash bei Cleanup

**Fix:**
```python
class APFFilterLoop:
    def __init__(self, ...):
        # ...
        self._stop_event = threading.Event()
    
    def stop(self, timeout: float = 1.0):
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
    
    def _loop(self):
        while self._running:
            t0 = time.monotonic()
            try:
                # ... filter logic ...
            except Exception as e:
                print(f"[apf] filter error: {e}")
            elapsed = time.monotonic() - t0
            # Interruptible sleep
            self._stop_event.wait(timeout=max(0, self._dt - elapsed))
            if self._stop_event.is_set():
                break
```

**Severity:** 🟡 MEDIUM - Resource Leak, aber kein Crash

---

### TS-08: Reconnect Backoff Race

**Datei:** `skymeshx/core/connection.py:537-571`

```python
def _reconnect_loop(self):
    backoff = 1.0
    attempt = 0
    while not self._stop.is_set():  # ❌ Kein Lock
        attempt += 1
        print(f"[mav] Reconnect attempt {attempt}, waiting {backoff:.0f}s...")
        self._stop.wait(backoff)
        if self._stop.is_set():  # ❌ TOCTOU Race
            return
        try:
            self._mav = mavutil.mavlink_connection(...)
            # ...
```

**Problem:**
- `_stop.is_set()` wird zweimal ohne Lock geprüft
- TOCTOU (Time-of-Check-Time-of-Use) Race
- Zwischen Check und `mavlink_connection()` kann `disconnect()` aufgerufen werden

**Impact:**
- Thread läuft nach `disconnect()` weiter
- Unnötige Reconnect-Versuche
- Resource Leak

**Fix:**
```python
def _reconnect_loop(self):
    backoff = 1.0
    attempt = 0
    while True:
        if self._stop.wait(timeout=backoff):  # Atomic check + wait
            return  # Stop event set
        attempt += 1
        print(f"[mav] Reconnect attempt {attempt}...")
        try:
            # ...
```

**Severity:** 🟡 MEDIUM - Resource Leak, aber kein Datenverlust

---

### TS-09: Mission Upload Abort Race

**Datei:** `skymeshx/control/mission.py:69-70, 180`

```python
class MissionEngine:
    def __init__(self, ...):
        self._abort_event = threading.Event()
    
    def upload(self, validate_first: bool = True) -> bool:
        # ...
        self._abort_event.clear()  # ❌ Nicht atomar mit Check
        # ...
        return self._do_upload(mav, n)
```

**Problem:**
- `abort()` kann zwischen `clear()` und `_do_upload()` aufgerufen werden
- Upload startet trotz Abort-Request
- Kein Lock um Abort-State

**Impact:**
- Upload läuft trotz Abort
- Verwirrende UI (Abort-Button funktioniert nicht)
- Potentiell gefährlich bei Emergency-Abort

**Fix:**
```python
class MissionEngine:
    def __init__(self, ...):
        self._abort_event = threading.Event()
        self._upload_lock = threading.Lock()
    
    def upload(self, validate_first: bool = True) -> bool:
        with self._upload_lock:
            if self._abort_event.is_set():
                return False
            self._abort_event.clear()
            # ...
            return self._do_upload(mav, n)
    
    def abort(self):
        with self._upload_lock:
            self._abort_event.set()
```

**Severity:** 🟡 MEDIUM - Kann zu unerwünschtem Upload führen

---

## 🟢 LOW Severity Issues

### TS-10: `last_nack` ohne Lock

**Datei:** `skymeshx/core/connection.py:200, 681`

```python
class MAVLinkConnection:
    def __init__(self, ...):
        self.last_nack: Optional[Tuple[str, str]] = None  # ❌ NO LOCK
    
    def _parse(self, msg):
        # ...
        elif t == "COMMAND_ACK":
            # ...
            if not success:
                self.last_nack = (cmd_name, res_name)  # ❌ RACE
```

**Problem:**
- `last_nack` wird ohne Lock geschrieben/gelesen
- UI könnte inkonsistenten Wert lesen
- Aber nur kosmetisches Problem (kein Safety-Impact)

**Impact:**
- UI zeigt falschen NACK
- Keine Safety-Auswirkung

**Fix:**
```python
# Option 1: Use _lock
with self._lock:
    self.last_nack = (cmd_name, res_name)

# Option 2: Use atomic reference (Python GIL macht tuple-assignment atomar)
# Akzeptabel für Low-Severity Issue
```

**Severity:** 🟢 LOW - Kosmetisch

---

### TS-11: `_obstacles` nicht Thread-Safe

**Datei:** `skymeshx/safety/apf.py:179, 183-188, 246-255`

```python
class APFSafetyFilter:
    def __init__(self, ...):
        self._obstacles: List[Pose3D] = []  # ❌ NO LOCK
    
    def add_obstacle(self, x: float, y: float, z: float = 0.0):
        self._obstacles.append(Pose3D(x, y, z))  # ❌ RACE
    
    def clear_obstacles(self):
        self._obstacles.clear()  # ❌ RACE
    
    def filter(self, positions, desired):
        # ...
        for obs in self._obstacles:  # ❌ Iterator-Invalidierung möglich
            # ...
```

**Problem:**
- `_obstacles` wird ohne Lock modifiziert
- Concurrent `add_obstacle()` während `filter()` → Race
- Aber Feature wird selten verwendet (keine Beispiele im Code)

**Impact:**
- Potentieller Crash bei Obstacle-Modifikation
- Aber sehr selten in Praxis

**Fix:**
```python
class APFSafetyFilter:
    def __init__(self, ...):
        self._obstacles: List[Pose3D] = []
        self._obstacle_lock = threading.Lock()
    
    def add_obstacle(self, x: float, y: float, z: float = 0.0):
        with self._obstacle_lock:
            self._obstacles.append(Pose3D(x, y, z))
    
    def filter(self, positions, desired):
        with self._obstacle_lock:
            obstacles = list(self._obstacles)  # Snapshot
        # Use snapshot in filter logic
```

**Severity:** 🟢 LOW - Selten verwendet

---

### TS-12: FSM History Truncation Race

**Datei:** `skymeshx/core/fsm.py:147-148`

```python
def transition(self, new_state: DroneState, force: bool = False) -> bool:
    with self._lock:
        # ...
        self._history.append((time.time(), old, new_state))
        if len(self._history) > 500:
            self._history = self._history[-500:]  # ❌ Ineffizient, aber safe
```

**Problem:**
- Truncation ist ineffizient (O(n) copy)
- Aber innerhalb Lock, also thread-safe
- Nur Performance-Problem, kein Race

**Impact:**
- Minimaler Performance-Overhead
- Keine Correctness-Probleme

**Fix:**
```python
# Use deque with maxlen for O(1) append
from collections import deque

def __init__(self, ...):
    self._history = deque(maxlen=500)  # Auto-truncates
```

**Severity:** 🟢 LOW - Performance, kein Race

---

## Zusammenfassung der Schwachstellen

### Nach Severity

| Severity | Count | Modules |
|----------|-------|---------|
| 🔴 CRITICAL | 2 | `connection.py`, `apf.py` |
| 🟠 HIGH | 3 | `mission.py`, `connection.py`, `fsm.py` |
| 🟡 MEDIUM | 4 | `telemetry.py`, `apf.py`, `connection.py`, `mission.py` |
| 🟢 LOW | 3 | `connection.py`, `apf.py`, `fsm.py` |

### Nach Modul

| Modul | Critical | High | Medium | Low | Total |
|-------|----------|------|--------|-----|-------|
| `connection.py` | 1 | 1 | 1 | 2 | 5 |
| `apf.py` | 1 | 0 | 1 | 1 | 3 |
| `mission.py` | 0 | 1 | 1 | 0 | 2 |
| `fsm.py` | 0 | 1 | 0 | 1 | 2 |
| `telemetry.py` | 0 | 0 | 1 | 0 | 1 |

---

## Empfohlene Maßnahmen

### Sofort (Critical)

1. **TS-01**: `_emit()` Callback-Dispatch mit Lock-Snapshot schützen
2. **TS-02**: `APFSafetyFilter` mit `_state_lock` ausstatten

### Kurzfristig (High)

3. **TS-03**: `MissionEngine` Build-Lock oder Thread-Assertion hinzufügen
4. **TS-04**: `_pending_cmds` Cleanup optimieren
5. **TS-05**: `StateMachine` Callback-Dispatch mit Snapshot

### Mittelfristig (Medium)

6. **TS-06**: `TelemetryState` Properties oder Linting-Rules
7. **TS-07**: `APFFilterLoop` mit `join()` und interruptible sleep
8. **TS-08**: `_reconnect_loop()` TOCTOU Race fixen
9. **TS-09**: `MissionEngine` Upload-Lock hinzufügen

### Optional (Low)

10. **TS-10**: `last_nack` mit Lock (oder akzeptieren)
11. **TS-11**: `_obstacles` Lock hinzufügen
12. **TS-12**: `_history` mit `deque(maxlen=500)` ersetzen

---

## Testing-Empfehlungen

### Thread-Safety Tests

```python
# tests/test_thread_safety.py

import threading
import pytest
from skymeshx.core.connection import MAVLinkConnection

def test_concurrent_listener_modification():
    """Test TS-01: Concurrent on()/off() during _emit()"""
    conn = MAVLinkConnection("tcp:127.0.0.1:5762")
    
    def add_remove_listeners():
        for _ in range(1000):
            cb = lambda *args: None
            conn.on("telemetry", cb)
            conn.off("telemetry", cb)
    
    def emit_events():
        for _ in range(1000):
            conn._emit("telemetry", conn.telemetry)
    
    threads = [
        threading.Thread(target=add_remove_listeners),
        threading.Thread(target=emit_events),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # Should not crash

def test_apf_concurrent_filter():
    """Test TS-02: Concurrent filter() calls"""
    from skymeshx.safety.apf import APFSafetyFilter, Pose3D
    
    apf = APFSafetyFilter()
    positions = {"D1": Pose3D(0, 0, 10), "D2": Pose3D(5, 0, 10)}
    desired = {"D1": Pose3D(10, 0, 10), "D2": Pose3D(15, 0, 10)}
    
    def run_filter():
        for _ in range(100):
            apf.filter(positions, desired)
    
    threads = [threading.Thread(target=run_filter) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # Should not crash or produce inconsistent results
```

### Race Condition Detection

```bash
# Use ThreadSanitizer (TSan) for C extensions
TSAN_OPTIONS="halt_on_error=1" python -m pytest tests/

# Use pytest-xdist for parallel test execution
pytest tests/ -n 8 --dist loadscope

# Use pytest-repeat for stress testing
pytest tests/test_thread_safety.py --count=1000
```

---

## Langfristige Architektur-Empfehlungen

### 1. Actor Model für Concurrency

Statt Shared State mit Locks → Message Passing:

```python
# Beispiel: APF Filter als Actor
class APFFilterActor:
    def __init__(self):
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
    
    def filter_async(self, positions, desired, callback):
        self._queue.put(("filter", positions, desired, callback))
    
    def _run(self):
        while True:
            msg = self._queue.get()
            if msg[0] == "filter":
                _, positions, desired, callback = msg
                safe = self._do_filter(positions, desired)
                callback(safe)
```

### 2. Immutable Data Structures

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)  # Immutable
class TelemetrySnapshot:
    lat: float
    lon: float
    alt: float
    # ...

# Update via copy
new_telemetry = replace(old_telemetry, lat=48.137)
```

### 3. Lock-Free Data Structures

```python
# Use atomic operations for simple cases
import threading

class AtomicCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
            return self._value
```

---

## Referenzen

- [Python Threading Best Practices](https://docs.python.org/3/library/threading.html)
- [ThreadSanitizer (TSan)](https://github.com/google/sanitizers/wiki/ThreadSanitizerCppManual)
- [Effective Python: Item 54 - Use Lock to Prevent Data Races](https://effectivepython.com/)
- [OWASP: Race Conditions](https://owasp.org/www-community/vulnerabilities/Race_Conditions)

---

**Ende des Audits**
