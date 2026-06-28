import QtQuick
import QtQuick.Controls

Item {
    id: root
    anchors.fill: parent

    property var rows: []
    property string logName: ""
    property string summaryText: qsTr("No flight log loaded.")

    function localFilePath(urlValue) {
        var path = String(urlValue || "")
        if (path.indexOf("file:///") === 0)
            path = path.substring(8)
        else if (path.indexOf("file://") === 0)
            path = path.substring(7)
        return decodeURIComponent(path)
    }

    function showError(message) {
        errorText.text = message
        loadErrorFlash.visible = true
        errorTimer.restart()
    }

    function openCsvDialog() {
        if (typeof swarm === "undefined" || !swarm.openFileDialog) {
            root.showError(qsTr("File dialog is not available"))
            return
        }
        var pathStr = root.localFilePath(
            swarm.openFileDialog(qsTr("Open CSV Flight Log"), qsTr("CSV Logs (*.csv);;All Files (*)"))
        )
        if (pathStr.length > 0)
            root.loadCsvPath(pathStr)
    }

    function openBagDialog() {
        if (typeof swarm === "undefined" || !swarm.openFileDialog) {
            root.showError(qsTr("File dialog is not available"))
            return
        }
        var pathStr = root.localFilePath(
            swarm.openFileDialog(qsTr("Open ROS2 Bag"), qsTr("ROS2 Bags (*.mcap *.db3);;All Files (*)"))
        )
        if (pathStr.length > 0)
            root.loadBagPath(pathStr)
    }

    function loadCsvPath(pathStr) {
        try {
            root.logName = pathStr.split("/").pop().split("\\").pop()
            if (typeof swarm === "undefined" || !swarm.readFile) {
                root.showError(qsTr("File reader is not available"))
                return
            }
            var content = swarm.readFile(pathStr)
            if (!content || content.length <= 0) {
                root.showError(qsTr("File could not be read"))
                return
            }
            root.loadCsv(content)
        } catch (e) {
            console.error("FlightLogPanel: Error loading CSV:", e)
            root.showError(qsTr("CSV load failed"))
        }
    }

    function loadBagPath(pathStr) {
        try {
            root.logName = pathStr.split("/").pop().split("\\").pop()
            if (typeof bagPlayback !== "undefined" && bagPlayback.loadBag)
                bagPlayback.loadBag(pathStr)
            else
                root.showError(qsTr("Bag playback is not available"))
        } catch (e) {
            console.error("FlightLogPanel: Error loading bag:", e)
            root.showError(qsTr("Bag load failed"))
        }
    }

    function formatTime(seconds) {
        if (!isFinite(seconds) || seconds < 0)
            seconds = 0
        var mins = Math.floor(seconds / 60)
        var secs = Math.floor(seconds % 60)
        return mins.toString() + ":" + (secs < 10 ? "0" : "") + secs.toString()
    }

    function colIndex(headers, name) {
        for (var i = 0; i < headers.length; i++) {
            if (headers[i] === name)
                return i
        }
        return -1
    }

    function numberAt(cols, headers, name) {
        var idx = root.colIndex(headers, name)
        if (idx < 0 || idx >= cols.length)
            return 0
        var value = parseFloat(cols[idx])
        return isFinite(value) ? value : 0
    }

    function loadCsv(text) {
        var lines = text.split("\n")
        if (lines.length < 2) {
            root.showError(qsTr("CSV has no data rows"))
            return
        }

        var headers = lines[0].split(",").map(function(h) { return h.trim() })
        var parsed = []
        var t0 = -1
        var maxAlt = 0
        var maxSpd = 0
        var firstBat = 0
        var lastBat = 0

        for (var i = 1; i < lines.length; i++) {
            var line = lines[i].trim()
            if (!line)
                continue
            var cols = line.split(",")
            var t = root.numberAt(cols, headers, "timestamp")
            if (t0 < 0)
                t0 = t
            var row = {
                t: t - t0,
                alt: root.numberAt(cols, headers, "alt_rel"),
                spd: root.numberAt(cols, headers, "groundspeed"),
                bat: root.numberAt(cols, headers, "battery_pct"),
                vz: root.numberAt(cols, headers, "vz")
            }
            if (parsed.length === 0)
                firstBat = row.bat
            lastBat = row.bat
            if (row.alt > maxAlt)
                maxAlt = row.alt
            if (row.spd > maxSpd)
                maxSpd = row.spd
            parsed.push(row)
        }

        rows = parsed
        if (parsed.length <= 0) {
            root.summaryText = qsTr("CSV loaded, but no usable rows were found.")
            return
        }

        var duration = parsed[parsed.length - 1].t
        root.summaryText =
            qsTr("Rows: ") + parsed.length +
            qsTr("   Duration: ") + root.formatTime(duration) +
            qsTr("   Max alt: ") + maxAlt.toFixed(1) + " m" +
            qsTr("   Max speed: ") + maxSpd.toFixed(1) + " m/s" +
            qsTr("   Battery delta: ") + (firstBat - lastBat).toFixed(0) + "%"
    }

    function bagStateText() {
        if (typeof bagPlayback === "undefined")
            return "N/A"
        return String(bagPlayback.state || "stopped").toUpperCase()
    }

    function bagProgressText() {
        if (typeof bagPlayback === "undefined")
            return "0:00 / 0:00"
        return root.formatTime(bagPlayback.progress * bagPlayback.duration) +
               " / " + root.formatTime(bagPlayback.duration)
    }

    Rectangle {
        id: loadErrorFlash
        visible: false
        anchors { top: parent.top; horizontalCenter: parent.horizontalCenter; topMargin: 8 }
        width: Math.min(parent.width - 24, errorText.implicitWidth + 24)
        height: 32
        radius: 6
        z: 10
        color: "#7f1d1d"
        border.color: "#ef4444"
        border.width: 1
        Text {
            id: errorText
            anchors.centerIn: parent
            color: "#fca5a5"
            font.pixelSize: 11
            elide: Text.ElideRight
            width: parent.width - 16
            horizontalAlignment: Text.AlignHCenter
        }
        Timer {
            id: errorTimer
            interval: 3000
            repeat: false
            onTriggered: loadErrorFlash.visible = false
        }
    }

    Column {
        anchors { fill: parent; margins: 12 }
        spacing: 10

        Row {
            width: parent.width
            height: 32
            spacing: 8

            Rectangle {
                width: 120
                height: 32
                radius: 6
                color: csvBtnMa.containsMouse ? "#2563eb" : "#1e2535"
                border.color: "#2563eb"
                border.width: 1
                Text {
                    anchors.centerIn: parent
                    text: qsTr("OPEN CSV")
                    color: "#e2e8f0"
                    font.pixelSize: 10
                    font.weight: Font.Bold
                }
                MouseArea {
                    id: csvBtnMa
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: root.openCsvDialog()
                }
            }

            Rectangle {
                width: 120
                height: 32
                radius: 6
                color: bagBtnMa.containsMouse ? "#059669" : "#1e2535"
                border.color: "#059669"
                border.width: 1
                Text {
                    anchors.centerIn: parent
                    text: qsTr("OPEN BAG")
                    color: "#e2e8f0"
                    font.pixelSize: 10
                    font.weight: Font.Bold
                }
                MouseArea {
                    id: bagBtnMa
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: root.openBagDialog()
                }
            }

            Text {
                width: Math.max(0, parent.width - 256)
                height: parent.height
                verticalAlignment: Text.AlignVCenter
                text: root.logName !== "" ? root.logName : qsTr("-- no log loaded --")
                color: root.logName !== "" ? "#94a3b8" : "#475569"
                font.pixelSize: 11
                font.family: "Consolas"
                elide: Text.ElideLeft
            }
        }

        Rectangle {
            width: parent.width
            height: 92
            radius: 8
            color: "#1a2035"
            border.color: "#2d3748"
            border.width: 1

            Column {
                anchors { fill: parent; margins: 12 }
                spacing: 8
                Text {
                    text: qsTr("Flight Log Summary")
                    color: "#94a3b8"
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }
                Text {
                    width: parent.width
                    text: root.summaryText
                    color: "#e2e8f0"
                    font.pixelSize: 12
                    font.family: "Consolas"
                    wrapMode: Text.Wrap
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 110
            radius: 8
            color: "#1a2035"
            border.color: "#2d3748"
            border.width: 1

            Column {
                anchors { fill: parent; margins: 12 }
                spacing: 10

                Text {
                    text: qsTr("ROS2 Bag Playback")
                    color: "#94a3b8"
                    font.pixelSize: 12
                    font.weight: Font.Bold
                }

                Row {
                    spacing: 8
                    height: 28

                    Text {
                        width: 170
                        height: parent.height
                        verticalAlignment: Text.AlignVCenter
                        text: root.bagStateText() + "  " + root.bagProgressText()
                        color: "#cbd5e1"
                        font.pixelSize: 10
                        font.family: "Consolas"
                    }

                    Rectangle {
                        width: 74
                        height: 28
                        radius: 6
                        color: playBtnMa.containsMouse ? "#059669" : "#1e2535"
                        border.color: "#059669"
                        border.width: 1
                        Text { anchors.centerIn: parent; text: qsTr("PLAY"); color: "#e2e8f0"; font.pixelSize: 10; font.weight: Font.Bold }
                        MouseArea {
                            id: playBtnMa
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                if (typeof bagPlayback !== "undefined" && bagPlayback.play)
                                    bagPlayback.play()
                            }
                        }
                    }

                    Rectangle {
                        width: 74
                        height: 28
                        radius: 6
                        color: stopBtnMa.containsMouse ? "#dc2626" : "#1e2535"
                        border.color: "#dc2626"
                        border.width: 1
                        Text { anchors.centerIn: parent; text: qsTr("STOP"); color: "#e2e8f0"; font.pixelSize: 10; font.weight: Font.Bold }
                        MouseArea {
                            id: stopBtnMa
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                if (typeof bagPlayback !== "undefined" && bagPlayback.stop)
                                    bagPlayback.stop()
                            }
                        }
                    }

                    Rectangle {
                        width: 32
                        height: 28
                        radius: 6
                        color: speedDownMa.containsMouse ? "#374151" : "#1e2535"
                        border.color: "#475569"
                        border.width: 1
                        Text { anchors.centerIn: parent; text: "-"; color: "#e2e8f0"; font.pixelSize: 13; font.weight: Font.Bold }
                        MouseArea {
                            id: speedDownMa
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                if (typeof bagPlayback !== "undefined")
                                    bagPlayback.playbackRate = Math.max(0.1, bagPlayback.playbackRate - 0.5)
                            }
                        }
                    }

                    Rectangle {
                        width: 32
                        height: 28
                        radius: 6
                        color: speedUpMa.containsMouse ? "#374151" : "#1e2535"
                        border.color: "#475569"
                        border.width: 1
                        Text { anchors.centerIn: parent; text: "+"; color: "#e2e8f0"; font.pixelSize: 13; font.weight: Font.Bold }
                        MouseArea {
                            id: speedUpMa
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                if (typeof bagPlayback !== "undefined")
                                    bagPlayback.playbackRate = Math.min(10.0, bagPlayback.playbackRate + 0.5)
                            }
                        }
                    }

                    Text {
                        height: parent.height
                        verticalAlignment: Text.AlignVCenter
                        text: (typeof bagPlayback !== "undefined") ? qsTr("Speed: ") + bagPlayback.playbackRate.toFixed(1) + "x" : qsTr("Speed: 1.0x")
                        color: "#64748b"
                        font.pixelSize: 10
                        font.family: "Consolas"
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: Math.max(120, parent.height - 258)
            radius: 8
            color: "#0a0e1a"
            border.color: "#1e293b"
            border.width: 1

            Text {
                anchors.centerIn: parent
                width: parent.width - 32
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("Charts are disabled in the safe FlightLog view until the tab-load freeze is isolated.")
                color: "#64748b"
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }
        }
    }
}
