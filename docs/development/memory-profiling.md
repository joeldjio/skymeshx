# Memory Profiling (Developer Tool)

## Overview

`tools/profile_memory.py` is a standalone developer tool for detecting memory leaks in the uavresearch GCS UI. It uses Python's `tracemalloc` module to track memory allocations.

## Usage

### Basic Workflow

1. **Start the UI** in one terminal:
   ```bash
   python -m tools.ui
   ```

2. **Start the profiler** in another terminal:
   ```bash
   python tools/profile_memory.py
   ```

3. **Begin tracking**:
   ```
   profiler> start
   ```

4. **Take baseline snapshot**:
   ```
   profiler> snap baseline
   ```

5. **Perform UI actions** (open/close panels, switch tabs, etc.)

6. **Take another snapshot**:
   ```
   profiler> snap after_action
   ```

7. **Compare snapshots**:
   ```
   profiler> compare baseline after_action
   ```

## Commands

- `start` - Start memory tracking
- `stop` - Stop memory tracking
- `snap <name>` - Take a snapshot with the given name
- `compare <name1> <name2>` - Compare two snapshots
- `list` - List all snapshots
- `qt` - Show Qt object counts
- `status` - Show current memory usage
- `help` - Show help
- `quit` - Exit profiler

## Example Session

```
$ python tools/profile_memory.py

Memory Profiler for uavresearch GCS
This is a developer tool for detecting memory leaks.

profiler> start
[Profiler] Memory tracking started

profiler> snap baseline
[Profiler] Snapshot 'baseline' taken: 45.23 MB current, 47.12 MB peak

# (Perform UI actions: open Swarm panel, close it, wait 30 seconds)

profiler> snap after_swarm
[Profiler] Snapshot 'after_swarm' taken: 46.78 MB current, 48.91 MB peak

profiler> compare baseline after_swarm

[Profiler] Comparison: baseline → after_swarm
Top 10 memory allocations:
--------------------------------------------------------------------------------
 1. tools/ui/context/swarm_context.py:145
    Size: +234.5 KB (456.2 KB total)
    Count: +12 (24 total)
 2. PyQt6/QtCore.py:892
    Size: +89.3 KB (178.6 KB total)
    Count: +45 (90 total)
...

profiler> qt

[Profiler] Qt Object Counts:
----------------------------------------
  QQuickItem                      1234
  QQmlContext                      456
  QObject                          234
  ...

profiler> quit
```

## Interpreting Results

### Memory Growth

- **Normal**: Small increases (< 5 MB) that stabilize
- **Potential Leak**: Continuous growth without stabilization
- **Definite Leak**: Large increases (> 20 MB) after simple actions

### Qt Object Counts

- **Normal**: Counts fluctuate but return to baseline
- **Leak**: Specific object types continuously increase
- **Common Culprits**: QQuickItem, QQmlContext, Signal connections

### Top Allocations

Look for:
- Repeated allocations in the same file/line
- Large allocations in UI code
- Allocations that don't decrease after actions complete

## Testing Scenarios

### Panel Open/Close
```
snap baseline
# Open panel
snap panel_open
# Close panel
# Wait 30 seconds
snap panel_closed
compare baseline panel_closed
# Should be similar if no leak
```

### Tab Switching
```
snap baseline
# Switch between tabs 10 times
snap after_switching
compare baseline after_switching
# Should show minimal growth
```

### Long-Running Operation
```
snap baseline
# Start mission, let it run for 5 minutes
snap during_mission
# Mission complete, wait 1 minute
snap after_mission
compare baseline after_mission
```

## Limitations

- Only tracks Python memory allocations
- Qt C++ objects are tracked indirectly via garbage collector
- Snapshot comparison shows net changes, not individual allocations
- ~10-20% memory overhead when profiling is active

## See Also

- Python `tracemalloc` documentation: https://docs.python.org/3/library/tracemalloc.html
- [UI Documentation](../ui/ui-documentation.md)
- [Development Guidelines](../project/overview.md)