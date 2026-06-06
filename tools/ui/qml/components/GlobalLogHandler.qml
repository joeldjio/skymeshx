import QtQuick

// ── Global log store + connections ────────────────────────────────────
// Aggregates log messages from swarm/experiment/safety into a single
// ListModel that survives panel open/close cycles.
//
// Exposes:
//   model            → ListModel of {time, level, text}
//   maxEntries       → ring buffer cap (default 3000)
//
// Syslog: each new entry is appended immediately via swarm.appendFile()
// into  logs/syslogs/<timestamp>.txt  (path resolved by Python so it
// works both in source-tree runs and PyInstaller bundles).
// No more per-second full-file rewrites.
Item {
    id: handler

    property alias  model:      logModel
    property int    maxEntries: 3000

    // External listeners (e.g. status bar) can hook this
    signal newEntry(string level, string text)

    ListModel { id: logModel }

    // ── Syslog path (resolved once on first entry) ────────────────────
    property string _syslogPath: ""

    function _ensureSyslogPath() {
        if (_syslogPath !== "") return
        if (typeof swarm === "undefined" || !swarm || !swarm.syslogsDir) return
        var dir = swarm.syslogsDir()               // "…/logs/syslogs" (abs path)
        var d   = new Date()
        var stamp = d.getFullYear() + "-" +
                    String(d.getMonth() + 1).padStart(2, "0") + "-" +
                    String(d.getDate()).padStart(2, "0") + "_" +
                    String(d.getHours()).padStart(2, "0") +
                    String(d.getMinutes()).padStart(2, "0") +
                    String(d.getSeconds()).padStart(2, "0")
        // Use forward-slash separator — Python handles both on Windows
        _syslogPath = dir + "/" + stamp + ".txt"
    }

    // ── Append one entry to syslog (crash-safe, incremental) ─────────
    function _appendToSyslog(time, level, text) {
        if (typeof swarm === "undefined" || !swarm || !swarm.appendFile) return
        _ensureSyslogPath()
        if (_syslogPath === "") return
        swarm.appendFile(_syslogPath, time + "  [" + level + "]  " + text)
    }

    // ── Add entry to in-memory model + syslog ────────────────────────
    function _append(level, text) {
        var d    = new Date()
        var time = Qt.formatTime(d, "hh:mm:ss")
        logModel.append({ time: time, level: level, text: text })
        if (logModel.count > handler.maxEntries)
            logModel.remove(0, 1)
        _appendToSyslog(time, level, text)
        handler.newEntry(level, text)
    }

    // ── Signal connections ────────────────────────────────────────────

    Connections {
        target: (typeof swarm !== "undefined") ? swarm : null
        function onLogMessage(level, text) { handler._append(level, text) }
        function onFsmStateChanged(droneId, fsmState) {
            var lvl = fsmState === "EMERGENCY" ? "ERROR"
                    : (fsmState === "RTL" || fsmState === "LANDING") ? "WARN" : "INFO"
            handler._append(lvl, "[FSM] " + droneId + ": " + fsmState)
        }
    }

    Connections {
        target: (typeof experiment !== "undefined") ? experiment : null
        function onLogMessage(text) {
            handler._append("INFO", "[EXP] " + text)
        }
        function onScriptLogMessage(text) {
            var lvl = text.startsWith("[ERROR]") ? "ERROR"
                    : text.startsWith("[WARN]")  ? "WARN" : "INFO"
            handler._append(lvl, "[SCRIPT] " + text)
        }
    }
}
