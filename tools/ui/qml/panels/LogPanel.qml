import QtQuick
import QtQuick.Controls
import "../components" as Cmp

Item {
    id: root
    anchors.fill: parent

    // Injected by Loader.onLoaded in main.qml; fallback to local for standalone use
    property var activeLogModel: localLogModel

    ListModel { id: localLogModel }

    // Parse drone ID from log text like "[D1] ..." or "[SWARM] ..."
    function extractDroneId(text) {
        var match = text.match(/^\[([A-Z0-9_]+)\]/)
        return match ? match[1] : ""
    }

    function removeDroneId(text) {
        return text.replace(/^\[[A-Z0-9_]+\]\s*/, "")
    }

    function getDroneColor(droneId) {
        if (!droneId) return "#64748b"
        if (droneId === "SWARM") return "#8b5cf6"
        // Hash to color
        var colors = ["#22c55e", "#2563eb", "#f59e0b", "#ef4444", "#06b6d4", "#f97316", "#ec4899"]
        var hash = 0
        for (var i = 0; i < droneId.length; i++) {
            hash = ((hash << 5) - hash) + droneId.charCodeAt(i)
            hash = hash & hash
        }
        return colors[Math.abs(hash) % colors.length]
    }

    // ── Auto-save log to syslogs/ ─────────────────────────────────────
    // NOTE: Auto-save now lives in components/GlobalLogHandler.qml so it runs
    // even when the Log tab is never opened. This panel only provides manual
    // export via its own Save button.

    // ── Tab selector ──────────────────────────────────────────────────────
    property int _activeTab: 0  // 0=System Log, 1=Trace

    Row {
        id: tabRow
        anchors { top: parent.top; left: parent.left; right: parent.right; topMargin: 8; leftMargin: 12 }
        spacing: 4; height: 28

        Repeater {
            model: ["System Log", "Trace"]
            delegate: Rectangle {
                width: 100; height: 28; radius: 5
                color: root._activeTab === index ? "#2563eb" : "#1e2535"
                border.color: root._activeTab === index ? "#3b82f6" : "#2d3748"; border.width: 1
                Text { anchors.centerIn: parent; text: modelData; color: root._activeTab === index ? "white" : "#64748b"; font.pixelSize: 10; font.weight: Font.Bold }
                MouseArea { anchors.fill: parent; onClicked: root._activeTab = index }
            }
        }
    }

    // ── System Log tab ────────────────────────────────────────────────────
    Column {
        anchors { top: tabRow.bottom; left: parent.left; right: parent.right; bottom: parent.bottom; margins: 12; topMargin: 8 }
        spacing: 8
        visible: root._activeTab === 0

        // ── Header with stats ─────────────────────────────────────────────
        Rectangle {
            width: parent.width; height: 36; radius: 6
            color: "#1a2035"; border.color: "#2d3748"; border.width: 1

            Row {
                anchors { fill: parent; leftMargin: 10; rightMargin: 10 }
                spacing: 16

                // P2: use O(1) counter from GlobalLogHandler instead of O(n) scan
                property int errorCount: (typeof globalLog !== "undefined") ? globalLog.errorCount : 0

                Text {
                    text: qsTr("SYSTEM LOG")
                    color: "#e2e8f0"; font.pixelSize: 12; font.weight: Font.Bold
                    anchors.verticalCenter: parent.verticalCenter
                }

                // Error counter badge
                Rectangle {
                    width: errCountLbl.implicitWidth + 16; height: 20; radius: 10
                    color: parent.errorCount > 0 ? "#7f1d1d" : "#1e2535"
                    visible: parent.errorCount > 0
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        id: errCountLbl
                        anchors.centerIn: parent
                        text: parent.parent.errorCount + " ERR"
                        color: "#fca5a5"; font.pixelSize: 9; font.weight: Font.Bold
                    }
                }

                Item { width: 1; height: parent.height }

                Text {
                    text: root.activeLogModel.count + qsTr(" entries")
                    color: "#64748b"; font.pixelSize: 10
                    anchors.verticalCenter: parent.verticalCenter
                }

                // Export feedback toast
                Text {
                    id: exportFeedback
                    visible: false
                    color: "#4ade80"; font.pixelSize: 9
                    anchors.verticalCenter: parent.verticalCenter
                    Timer { id: exportHideTimer; interval: 4000; onTriggered: exportFeedback.visible = false }
                }

                Rectangle {
                    width: 90; height: 24; radius: 5
                    color: "#0f2d1a"
                    border.color: "#166534"; border.width: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Text { anchors.centerIn: parent; text: qsTr("AUTO-SAVE ACTIVE"); color: "#4ade80"; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
                }

                // Export current log to file
                Rectangle {
                    id: exportBtn
                    width: 70; height: 24; radius: 5
                    color: exportMa.containsMouse ? "#15803d" : "#1e2535"
                    border.color: "#22c55e"; border.width: 1
                    anchors.verticalCenter: parent.verticalCenter
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text { anchors.centerIn: parent; text: qsTr("EXPORT"); color: "#4ade80"; font.pixelSize: 9; font.weight: Font.Bold; font.letterSpacing: 1 }
                    MouseArea {
                        id: exportMa; anchors.fill: parent; hoverEnabled: true
                        onClicked: {
                            if (typeof swarm === "undefined" || !swarm) return
                            var d = new Date()
                            var stamp = d.getFullYear() + "-" +
                                        String(d.getMonth()+1).padStart(2,"0") + "-" +
                                        String(d.getDate()).padStart(2,"0") + "_" +
                                        String(d.getHours()).padStart(2,"0") +
                                        String(d.getMinutes()).padStart(2,"0") +
                                        String(d.getSeconds()).padStart(2,"0")
                            var lines = []
                            for (var i = 0; i < root.activeLogModel.count; i++) {
                                var e = root.activeLogModel.get(i)
                                lines.push(e.time + "  [" + e.level + "]  " + e.text)
                            }
                            var path = "logs/export_" + stamp + ".txt"
                            var ok = swarm.writeFile(path, lines.join("\n"))
                            exportFeedback.text = ok ? ("✓ " + path) : qsTr("✗ Export failed")
                            exportFeedback.color = ok ? "#4ade80" : "#fca5a5"
                            exportFeedback.visible = true
                            exportHideTimer.restart()
                        }
                    }
                }
            }
        }

        // ── Filter bar ────────────────────────────────────────────────────
        Row {
            width: parent.width; spacing: 6

            ComboBox {
                id: levelFilter; width: 80; height: 28
                model: ["ALL", "INFO", "WARN", "ERROR"]
                background: Rectangle { color: "#1e2535"; radius: 5; border.color: "#2d3748"; border.width: 1 }
                contentItem: Text { text: levelFilter.displayText; color: "#e2e8f0"; font.pixelSize: 11; verticalAlignment: Text.AlignVCenter; leftPadding: 6 }
                onCurrentTextChanged: logListView.filterLevel = currentText
            }

            TextField {
                id: searchField; width: parent.width - 150; height: 28
                placeholderText: qsTr("Search logs…")
                background: Rectangle { color: "#1e2535"; radius: 5; border.color: "#2d3748"; border.width: 1 }
                color: "#e2e8f0"; font.pixelSize: 11; leftPadding: 8
                onTextChanged: logListView.filterText = text.toLowerCase()
            }

            Rectangle {
                width: 60; height: 28; radius: 5
                color: clrM.containsMouse ? "#7f1d1d" : "#1e2535"
                border.color: "#2d3748"; border.width: 1
                Text { anchors.centerIn: parent; text: qsTr("CLEAR"); color: "#94a3b8"; font.pixelSize: 9; font.weight: Font.Bold }
                MouseArea { id: clrM; anchors.fill: parent; hoverEnabled: true; onClicked: root.activeLogModel.clear() }
            }
        }

        // ── Log view ──────────────────────────────────────────────────────
        Rectangle {
            width: parent.width
            height: parent.height - y
            radius: 8; color: "#0d1117"; border.color: "#2d3748"; border.width: 1

            ListView {
                id: logListView
                property string filterLevel: "ALL"
                property string filterText:  ""
                // Only auto-scroll when the view was already pinned to the
                // bottom. If the user scrolled up to inspect old entries,
                // we do not hijack their scroll position.
                property bool   _pinToBottom: true

                anchors { fill: parent; margins: 8 }
                clip: true
                spacing: 2

                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AlwaysOn }

                onContentYChanged: {
                    // Re-evaluate pin after each scroll movement
                    _pinToBottom = (contentY + height >= contentHeight - 4)
                }

                model: root.activeLogModel

                delegate: Rectangle {
                    // P2: compute once per delegate — avoid 3× regex + 3× color-hash per cell
                    readonly property string _did:   extractDroneId(model.text)
                    readonly property string _dcol:  getDroneColor(_did)

                    visible: {
                        var lvlOk = logListView.filterLevel === "ALL" || model.level === logListView.filterLevel
                        var txtOk = logListView.filterText === "" || (model.level + " " + model.text).toLowerCase().indexOf(logListView.filterText) >= 0
                        return lvlOk && txtOk
                    }
                    width: logListView.width
                    height: visible ? Math.max(row.implicitHeight + 8, 28) : 0
                    color: {
                        if (model.level === "ERROR") return "#227f1d1d"
                        if (model.level === "WARN") return "#2278350f"
                        return (index % 2 === 0) ? "#0d1117" : "#111827"
                    }
                    radius: 4
                    border.color: model.level === "ERROR" ? "#44ef4444" : "transparent"; border.width: 1

                    Row {
                        id: row
                        spacing: 8
                        anchors { fill: parent; leftMargin: 8; rightMargin: 8; verticalCenter: parent.verticalCenter }

                        // Time
                        Text {
                            text: model.time
                            color: "#4a5568"; font.pixelSize: 10
                            font.family: (typeof Cmp !== "undefined" && Cmp.Theme)
                                        ? Cmp.Theme.fontMono : "Consolas"
                            width: 60
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        // Drone ID Badge
                        Rectangle {
                            width: droneBadgeTxt.implicitWidth + 12; height: 18; radius: 9
                            color: _dcol + "33"
                            border.color: _dcol + "66"; border.width: 1
                            visible: _did !== ""
                            anchors.verticalCenter: parent.verticalCenter

                            Text {
                                id: droneBadgeTxt
                                anchors.centerIn: parent
                                text: _did
                                color: _dcol
                                font.pixelSize: 9; font.weight: Font.Bold
                                font.family: (typeof Cmp !== "undefined" && Cmp.Theme)
                                            ? Cmp.Theme.fontMono : "Consolas"
                            }
                        }

                        // Level Badge (only when no drone ID)
                        Rectangle {
                            width: 32; height: 16; radius: 8
                            color: model.level === "ERROR" ? "#7f1d1d"
                                 : model.level === "WARN"  ? "#78350f"
                                 : "#1e3a5f"
                            visible: extractDroneId(model.text) === ""
                            anchors.verticalCenter: parent.verticalCenter

                            Text {
                                anchors.centerIn: parent
                                text: model.level
                                color: model.level === "ERROR" ? "#fca5a5"
                                     : model.level === "WARN"  ? "#fcd34d"
                                     : "#93c5fd"
                                font.pixelSize: 8; font.weight: Font.Bold
                            }
                        }

                        // Message
                        Text {
                            text: removeDroneId(model.text)
                            color: model.level === "ERROR" ? "#fca5a5"
                                 : model.level === "WARN"  ? "#fcd34d"
                                 : "#8be9fd"
                            font.pixelSize: 11
                            font.family: (typeof Cmp !== "undefined" && Cmp.Theme)
                                        ? Cmp.Theme.fontMono : "Consolas"
                            width: parent.width - 140
                            wrapMode: Text.WordWrap
                            anchors.verticalCenter: parent.verticalCenter
                            elide: Text.ElideRight
                        }
                    }
                }

                // Auto-scroll only when pinned to bottom
                onCountChanged: if (_pinToBottom) positionViewAtEnd()
            }
        }
    }

    // ── Trace tab ──────────────────────────────────────────────────────────
    Column {
        anchors { top: tabRow.bottom; left: parent.left; right: parent.right; bottom: parent.bottom; margins: 12; topMargin: 8 }
        spacing: 8
        visible: root._activeTab === 1

        // ── Trace Session Controls ─────────────────────────────────────────
        Rectangle {
            width: parent.width; height: traceCtrlCol.implicitHeight + 20; radius: 6
            color: "#1a2035"; border.color: "#2d3748"; border.width: 1

            Column {
                id: traceCtrlCol
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                spacing: 8

                property bool _traceActive: (typeof trace !== "undefined" && trace) ? trace.sessionActive : false
                Timer { interval: 1000; running: root._activeTab === 1; repeat: true
                    onTriggered: traceCtrlCol._traceActive = (typeof trace !== "undefined" && trace) ? trace.sessionActive : false
                }

                // Status indicator
                Rectangle {
                    width: parent.width; height: 28; radius: 5
                    color: "#0d1117"
                    border.color: traceCtrlCol._traceActive ? "#22c55e" : "#374151"; border.width: 1
                    Row {
                        anchors { fill: parent; leftMargin: 8 }
                        spacing: 6
                        Rectangle {
                            width: 8; height: 8; radius: 4; anchors.verticalCenter: parent.verticalCenter
                            color: traceCtrlCol._traceActive ? "#22c55e" : "#475569"
                            SequentialAnimation on opacity {
                                running: traceCtrlCol._traceActive; loops: Animation.Infinite
                                NumberAnimation { to: 0.3; duration: 800 }
                                NumberAnimation { to: 1.0; duration: 800 }
                            }
                        }
                        Text {
                            text: traceCtrlCol._traceActive ? "Session active" : "No session"
                            color: traceCtrlCol._traceActive ? "#22c55e" : "#475569"
                            font.pixelSize: 10; font.weight: Font.Bold
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                // Scenario name input
                Row {
                    width: parent.width; spacing: 6
                    Text { text: "Scenario:"; color: "#64748b"; font.pixelSize: 10; anchors.verticalCenter: parent.verticalCenter; width: 60 }
                    TextField {
                        id: traceScenarioField; width: parent.width - 66; height: 26
                        placeholderText: "e.g. gz_x500_gimbal_seeding"
                        background: Rectangle { color: "#1e2535"; radius: 5; border.color: "#2d3748"; border.width: 1 }
                        color: "#e2e8f0"; font.pixelSize: 9; font.family: "Consolas"; leftPadding: 6
                        enabled: !traceCtrlCol._traceActive
                    }
                }

                // Start / Stop / Export
                Row {
                    width: parent.width; spacing: 4

                    Rectangle {
                        width: (parent.width - 8) / 3; height: 30; radius: 5
                        color: traceCtrlCol._traceActive ? "#1e293b" : (traceStartM.containsMouse ? "#166534" : "#14532d")
                        border.color: traceCtrlCol._traceActive ? "#374151" : "#22c55e"; border.width: 1
                        Text { anchors.centerIn: parent; text: "▶ Start"; color: traceCtrlCol._traceActive ? "#475569" : "#86efac"; font.pixelSize: 9; font.weight: Font.Bold }
                        MouseArea {
                            id: traceStartM; anchors.fill: parent; hoverEnabled: true
                            enabled: !traceCtrlCol._traceActive
                            onClicked: {
                                if (typeof trace === "undefined" || !trace) return
                                var scenario = traceScenarioField.text.trim() || "manual_trace_session"
                                trace.startSession(scenario)
                            }
                        }
                    }

                    Rectangle {
                        width: (parent.width - 8) / 3; height: 30; radius: 5
                        color: !traceCtrlCol._traceActive ? "#1e293b" : (traceStopM.containsMouse ? "#7f1d1d" : "#450a0a")
                        border.color: !traceCtrlCol._traceActive ? "#374151" : "#ef4444"; border.width: 1
                        Text { anchors.centerIn: parent; text: "■ Stop"; color: !traceCtrlCol._traceActive ? "#475569" : "#fca5a5"; font.pixelSize: 9; font.weight: Font.Bold }
                        MouseArea {
                            id: traceStopM; anchors.fill: parent; hoverEnabled: true
                            enabled: traceCtrlCol._traceActive
                            onClicked: {
                                if (typeof trace === "undefined" || !trace) return
                                trace.stopSession()
                            }
                        }
                    }

                    Rectangle {
                        width: (parent.width - 8) / 3; height: 30; radius: 5
                        color: traceExportM.containsMouse ? "#1e3a8a" : "#1e293b"
                        border.color: "#3b82f6"; border.width: 1
                        Text { anchors.centerIn: parent; text: "Export"; color: "#60a5fa"; font.pixelSize: 9; font.weight: Font.Bold }
                        MouseArea {
                            id: traceExportM; anchors.fill: parent; hoverEnabled: true
                            onClicked: {
                                if (typeof trace === "undefined" || !trace) return
                                var p = trace.exportSummary()
                                if (p) swarm.logMessage("INFO", "[TRACE] Exported: " + p)
                            }
                        }
                    }
                }

                // Session path
                Text {
                    width: parent.width
                    text: {
                        if (typeof trace === "undefined" || !trace) return "trace context unavailable"
                        var p = trace.sessionPath
                        return p ? "Path: " + p : "No active session"
                    }
                    color: "#475569"; font.pixelSize: 8; font.family: "Consolas"
                    wrapMode: Text.WordWrap
                }

                // Open folder button
                Rectangle {
                    width: parent.width; height: 26; radius: 5
                    color: openFolderM.containsMouse ? "#1e293b" : "transparent"
                    border.color: "#334155"; border.width: 1
                    visible: typeof trace !== "undefined" && trace && trace.sessionPath !== ""
                    Text { anchors.centerIn: parent; text: "Open Folder"; color: "#64748b"; font.pixelSize: 9 }
                    MouseArea {
                        id: openFolderM; anchors.fill: parent; hoverEnabled: true
                        onClicked: { if (typeof trace !== "undefined" && trace) trace.openFolder() }
                    }
                }
            }
        }

        // ── Trace path / info ──────────────────────────────────────────────
        Rectangle {
            width: parent.width; height: 40; radius: 6
            color: "#0d1117"; border.color: "#2d3748"; border.width: 1
            Text {
                anchors { fill: parent; margins: 8 }
                text: "Trace bundles saved to: trace_runs/<timestamp>_<scenario>/"
                color: "#374151"; font.pixelSize: 9; font.family: "Consolas"
                wrapMode: Text.WordWrap
            }
        }
    }
}
