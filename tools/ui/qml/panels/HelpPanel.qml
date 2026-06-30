import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as Cmp

// HelpPanel - Complete Feature Reference for SkyMeshX GCS
// Modernized with theme integration and improved accessibility.

Item {
    id: root
    anchors.fill: parent

    component HelpSection: Rectangle {
        id: helpSection
        property string title: ""
        property string subtitle: ""
        property color accent: Cmp.Theme.accent
        property string body: ""
        width: parent ? parent.width : 600
        radius: Cmp.Theme.radiusMd
        color: Cmp.Theme.bgPanel
        border.color: Cmp.Theme.border
        border.width: 1
        height: secCol.implicitHeight + Cmp.Theme.spacing(3)

        Rectangle {
            width: 4
            height: parent.height - Cmp.Theme.spacing(2)
            anchors {
                left: parent.left
                leftMargin: Cmp.Theme.spacing(1)
                verticalCenter: parent.verticalCenter
            }
            radius: 2
            gradient: Gradient {
                GradientStop { position: 0.0; color: Qt.lighter(helpSection.accent, 1.2) }
                GradientStop { position: 1.0; color: helpSection.accent }
            }
        }

        Column {
            id: secCol
            anchors {
                left: parent.left
                leftMargin: Cmp.Theme.spacing(2.5)
                right: parent.right
                rightMargin: Cmp.Theme.spacing(2)
                top: parent.top
                topMargin: Cmp.Theme.spacing(1.5)
            }
            spacing: Cmp.Theme.spacing(1)

            Text {
                text: helpSection.title
                color: helpSection.accent
                font.pixelSize: Cmp.Theme.fontMd
                font.weight: Font.Bold
                font.letterSpacing: 0.5
            }
            Text {
                visible: helpSection.subtitle.length > 0
                text: helpSection.subtitle
                color: Cmp.Theme.textSecondary
                font.pixelSize: Cmp.Theme.fontXs
                font.italic: true
                wrapMode: Text.WordWrap
                width: parent.width
            }
            Text {
                text: helpSection.body
                color: Cmp.Theme.textPrimary
                font.pixelSize: Cmp.Theme.fontSm
                wrapMode: Text.WordWrap
                width: parent.width
                lineHeight: 1.5
                textFormat: Text.RichText
            }
        }

        Behavior on border.color {
            ColorAnimation { duration: Cmp.Theme.durationFast }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: parent.border.color = Qt.lighter(Cmp.Theme.border, 1.3)
            onExited: parent.border.color = Cmp.Theme.border
            propagateComposedEvents: true
        }
    }

    component GlossaryRow: Row {
        property string term: ""
        property string def: ""
        spacing: Cmp.Theme.spacing(1.5)
        width: parent ? parent.width : 0

        Text {
            text: parent.term
            color: Cmp.Theme.info
            font.pixelSize: Cmp.Theme.fontSm
            font.weight: Font.Bold
            font.family: "Consolas"
            width: 170
            wrapMode: Text.WordWrap
        }
        Text {
            text: parent.def
            color: Cmp.Theme.textPrimary
            font.pixelSize: Cmp.Theme.fontSm
            width: parent.width - 180
            wrapMode: Text.WordWrap
            textFormat: Text.RichText
            lineHeight: 1.4
        }
    }

    ScrollView {
        anchors {
            fill: parent
            margins: Cmp.Theme.spacing(2)
        }
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical.policy: ScrollBar.AsNeeded

        Column {
            width: parent.availableWidth
            spacing: Cmp.Theme.spacing(2)

            Rectangle {
                width: parent.width
                height: 100
                radius: Cmp.Theme.radiusLg
                gradient: Gradient {
                    GradientStop { position: 0.0; color: Qt.darker(Cmp.Theme.warning, 1.8) }
                    GradientStop { position: 1.0; color: Qt.darker(Cmp.Theme.warning, 2.2) }
                }
                border.color: Cmp.Theme.warning
                border.width: 2

                Column {
                    anchors {
                        left: parent.left
                        leftMargin: Cmp.Theme.spacing(3)
                        verticalCenter: parent.verticalCenter
                    }
                    spacing: Cmp.Theme.spacing(0.5)

                    Text {
                        text: qsTr("SkyMeshX Ground Control Station")
                        color: Cmp.Theme.warning
                        font.pixelSize: Cmp.Theme.fontXl
                        font.weight: Font.Bold
                    }
                    Text {
                        text: qsTr("Complete Feature Reference - Workflows - Conventions")
                        color: Cmp.Theme.textSecondary
                        font.pixelSize: Cmp.Theme.fontMd
                    }
                    Text {
                        text: qsTr("Read at least Quickstart and Global Concepts before arming a drone.")
                        color: Cmp.Theme.textMuted
                        font.pixelSize: Cmp.Theme.fontSm
                        font.italic: true
                    }
                }
            }

            Cmp.UpdateBanner {
                width: parent.width
            }
            Cmp.LicenseStatusBanner {
                width: parent.width
            }

            HelpSection {
                title: qsTr("1 - QUICKSTART (5 Steps to First Mission)")
                subtitle: qsTr("Assumption: SITL is already running, for example ArduCopter on tcp:127.0.0.1:5762.")
                accent: Cmp.Theme.success
                body:
                    qsTr("<b>1. Add Drone</b><br>") +
                    qsTr("&nbsp;&nbsp;Swarm Tab -> <b>+ DRONE</b> -> enter an ID such as <code>UAV_1</code> and a connection string such as <code>tcp:127.0.0.1:5762</code> -> <b>Connect</b>. ") +
                    qsTr("The status badge turns green and the FSM moves from <code>DISCONNECTED</code> to <code>IDLE</code>.<br><br>") +
                    qsTr("<b>2. Set Waypoints</b><br>") +
                    qsTr("&nbsp;&nbsp;Map Tab -> activate <b>ADD WAYPOINT</b> -> left-click the map. Set the AGL altitude in the top-right field. ESC cancels waypoint mode. ") +
                    qsTr("Alternative: Swarm Tab -> type Lat/Lon/Alt -> <b>Add WP</b>.<br><br>") +
                    qsTr("<b>3. Select Mission Targets</b><br>") +
                    qsTr("&nbsp;&nbsp;In the Swarm Tab, tick the drones that should receive the mission. If nothing is checked, commands fall back to the currently selected drone.<br><br>") +
                    qsTr("<b>4. Safety Check</b><br>") +
                    qsTr("&nbsp;&nbsp;Open the Safety Tab, enable APF, check the geofence radius, and verify altitude limits. For multi-drone missions, 50 m is often too small; use a larger radius such as 200 m when appropriate.<br><br>") +
                    qsTr("<b>5. Start Mission</b><br>") +
                    qsTr("&nbsp;&nbsp;Swarm Tab -> <b>START MISSION</b>. The UI arms, takes off, flies waypoints, and lands when the mission completes. The dispatched path remains visible on the map as green markers and a dashed line.")
            }

            HelpSection {
                title: qsTr("2 - GLOBAL CONCEPTS")
                subtitle: qsTr("Core concepts you must understand before operating real or simulated drones.")
                accent: Cmp.Theme.info
                body:
                    qsTr("<b>Selected Drone vs. Mission Targets</b><br>") +
                    qsTr("&nbsp;&nbsp;<b>Selected</b> is the one drone whose telemetry is displayed in the Telemetry Tab and InstrBar. <b>Mission Targets</b> are the checked drones in the Swarm Tab that receive actions such as ARM, TAKEOFF, GOTO, MISSION, and mode changes. An empty target set falls back to the selected drone.<br><br>") +
                    qsTr("<b>FSM per Drone</b><br>") +
                    qsTr("&nbsp;&nbsp;Each drone has a local state such as <code>DISCONNECTED</code>, <code>IDLE</code>, <code>ARMED</code>, <code>TAKEOFF</code>, <code>MISSION</code>, <code>RTL</code>, and <code>LANDING</code>. <code>EMERGENCY</code> and <code>ERROR</code> require reset or reconnect.<br><br>") +
                    qsTr("<b>APF Collision Protection</b><br>") +
                    qsTr("&nbsp;&nbsp;APF runs in the background and pushes drones apart when they get too close. APF can override formation and mission commands if the requested spacing is unsafe.<br><br>") +
                    qsTr("<b>Altitudes are AGL</b><br>") +
                    qsTr("&nbsp;&nbsp;A takeoff altitude of 10 m means 10 m above the launch point, not 10 m above mean sea level.<br><br>") +
                    qsTr("<b>Log Persistence</b><br>") +
                    qsTr("&nbsp;&nbsp;Everything shown in the Log Tab is also written to <code>tools/ui/syslogs/&lt;date&gt;_&lt;time&gt;.txt</code>. Include this file in bug reports.")
            }

            HelpSection {
                title: qsTr("TAB - MAP")
                subtitle: qsTr("Leaflet-based map with live drone markers, tracks, waypoints, dispatched missions, and geofence overlay.")
                accent: Cmp.Theme.info
                body:
                    qsTr("<b>What you see</b><br>") +
                    qsTr("&nbsp;&nbsp;Drone markers, track history, editable waypoint markers, dispatched mission paths, and geofence circles.<br><br>") +
                    qsTr("<b>How to use it</b><br>") +
                    qsTr("&nbsp;&nbsp;Use <b>ADD WAYPOINT</b> to enable waypoint mode, then click on the map. ESC cancels the mode. The altitude field defines the AGL altitude for the next waypoint. Use the sidebar or marker clicks to center/select drones.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Common Pitfalls</b></span><br>") +
                    qsTr("&nbsp;&nbsp;If the map looks empty, the drone may be outside the current viewport. Click the drone in the sidebar to center it. If waypoints are not placed, waypoint mode is probably off.")
            }

            HelpSection {
                title: qsTr("TAB - TELEMETRY (Dashboard)")
                subtitle: qsTr("Live cockpit for the currently selected drone.")
                accent: Cmp.Theme.accent
                body:
                    qsTr("<b>What you see</b><br>") +
                    qsTr("&nbsp;&nbsp;FSM state, drone type and role, flight hints, recent FSM transitions, altitude, speed, heading, climb rate, satellites, throttle, battery, voltage, and GPS fix.<br><br>") +
                    qsTr("<b>How to use it</b><br>") +
                    qsTr("&nbsp;&nbsp;Changing the combo box also changes the global selected drone across the UI. The first connected drone is auto-selected when the tab opens.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Common Pitfalls</b></span><br>") +
                    qsTr("&nbsp;&nbsp;All values at 0 or '-' usually mean the drone is not connected or telemetry has not started yet. In SITL, the first GPS fix can take up to 30 seconds.")
            }

            HelpSection {
                title: qsTr("TAB - SWARM CONTROL")
                subtitle: qsTr("Main workspace for multi-drone connection, missions, formations, and algorithms.")
                accent: Cmp.Theme.success
                body:
                    qsTr("<b>Drone Management</b><br>") +
                    qsTr("&nbsp;&nbsp;Add drones with an ID and connection string. Choose the drone type: generic or observation. Use the mission-target checkboxes to decide which drones receive commands.<br><br>") +
                    qsTr("<b>Missions</b><br>") +
                    qsTr("&nbsp;&nbsp;Enter waypoints manually or pick them from the map. <b>GOTO (N)</b> sends the position to all mission targets. <b>START MISSION</b> uploads a real MAVLink mission or falls back to sequential GOTO if upload is not supported.<br><br>") +
                    qsTr("<b>Swarm Algorithms</b><br>") +
                    qsTr("&nbsp;&nbsp;<b>Boids</b> provides Separation / Alignment / Cohesion. <b>Leader-Follower</b> assigns relative formation slots. <b>Consensus</b> supports distributed voting logic. <b>Behavior Trees</b> provide prepared mission templates.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Common Pitfalls</b></span><br>") +
                    qsTr("&nbsp;&nbsp;If formation does not start, check leader selection and formation size. If drones get too close, increase follow distance or lower APF min_distance carefully. The mission list is cleared after start by design; green map markers remain.")
            }

            HelpSection {
                title: qsTr("TAB - MISSION PLANNING")
                subtitle: qsTr("Advanced mission generation: Field Coverage, Seeding, and Solar Inspection.")
                accent: "#8b5cf6"
                body:
                    qsTr("<b>Coverage Mode</b><br>") +
                    qsTr("&nbsp;&nbsp;Draw a field boundary, choose a pattern (Parallel Lines, Spiral, Grid, Zigzag), set altitude, line spacing, overlap, and heading, then generate waypoints. Multi-drone coverage splits the field into sectors.<br><br>") +
                    qsTr("<b>Seeding Mode</b><br>") +
                    qsTr("&nbsp;&nbsp;Create seeding points or use generated coverage paths. Configure drop altitude, hover time, seed spacing, servo channel, and PWM values. Generated missions include DO_SET_SERVO commands.<br><br>") +
                    qsTr("<b>Solar Mode</b><br>") +
                    qsTr("&nbsp;&nbsp;Add panel rows, set altitude, gimbal pitch, trigger distance, and overlap. The generated inspection mission can include camera trigger and thermal inspection commands.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Best Practices</b></span><br>") +
                    qsTr("&nbsp;&nbsp;Use 15-20 m spacing with about 20% overlap for crop monitoring. Use -90 degree gimbal pitch for nadir solar inspection. Start multi-drone missions from separated positions.")
            }

            HelpSection {
                title: qsTr("TAB - SAFETY / APF")
                subtitle: qsTr("Active collision protection, geofence, obstacle, and battery safety layer.")
                accent: Cmp.Theme.danger
                body:
                    qsTr("<b>APF</b><br>") +
                    qsTr("&nbsp;&nbsp;APF pushes drones apart with a repulsive force. Configure min separation, max speed, and repulsion gain. <b>ENABLE APF</b> starts monitoring; <b>DISABLE</b> stops it.<br><br>") +
                    qsTr("<b>Geofence</b><br>") +
                    qsTr("&nbsp;&nbsp;Configure horizontal radius from spawn and min/max altitude in meters AGL. Breaches emit a signal, log an error, and can trigger auto-RTL depending on configuration.<br><br>") +
                    qsTr("<b>Obstacles</b><br>") +
                    qsTr("&nbsp;&nbsp;Static obstacle spheres can be added with Lat/Lon/Alt/Radius. APF treats them like drones.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Common Pitfalls</b></span><br>") +
                    qsTr("&nbsp;&nbsp;If APF fights a formation, follow distance is probably smaller than min separation. If all SITL drones spawn at the same Lat/Lon, stagger takeoff altitudes before enabling APF.")
            }

            HelpSection {
                title: qsTr("TAB - GIMBAL / CAMERA")
                subtitle: qsTr("Pan/Tilt control and preview for observation drones.")
                accent: "#8b5cf6"
                body:
                    qsTr("<b>Controls</b><br>") +
                    qsTr("&nbsp;&nbsp;Pan and tilt sliders send MAVLink mount commands immediately. Presets include Forward, Down/Nadir, and Tracking mode. Snapshot saves the current frame to <code>logs/snapshots/&lt;timestamp&gt;_&lt;drone&gt;.png</code>.<br><br>") +
                    qsTr("<b>Requirements</b><br>") +
                    qsTr("&nbsp;&nbsp;The drone must be added as type <i>observation</i>. The autopilot must support <code>MAV_CMD_DO_MOUNT_CONTROL</code>.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Common Pitfalls</b></span><br>") +
                    qsTr("&nbsp;&nbsp;If sliders move but nothing happens, the SITL build may not include a gimbal mount. If there is no live video in SITL, the panel normally shows a placeholder.")
            }

            HelpSection {
                title: qsTr("TAB - ROS2 / uXRCE-DDS (PX4 Bridge)")
                subtitle: qsTr("Direct ROS2 bridge access for PX4 drones through uXRCE-DDS without a MAVLink detour.")
                accent: Cmp.Theme.info
                body:
                    qsTr("<b>Left Column - Status and Configuration</b><br>") +
                    qsTr("&nbsp;&nbsp;Shows node status, installation hints, drone selector, namespace, bridge start/stop, and live uORB topics.<br><br>") +
                    qsTr("<b>Middle Column - uORB Snapshot and Offboard</b><br>") +
                    qsTr("&nbsp;&nbsp;Displays telemetry from uORB streams and can send position or velocity setpoints in the NED frame. <b>STOP</b> disables the continuous setpoint stream.<br><br>") +
                    qsTr("<b>Right Column - Vehicle Commands</b><br>") +
                    qsTr("&nbsp;&nbsp;ARM, DISARM, LAND, RTL, and TAKEOFF through VEHICLE_COMMAND.<br><br>") +
                    qsTr("<b>Requirements</b><br>") +
                    qsTr("&nbsp;&nbsp;ROS2 Humble/Jazzy, built and sourced <code>px4_msgs</code>, running <code>MicroXRCEAgent udp4 -p 8888</code>, and PX4 with DDS client enabled.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Common Pitfalls</b></span><br>") +
                    qsTr("&nbsp;&nbsp;Native Windows usually reports no_ros2; run the GCS in WSL2. If the bridge starts but snapshots stay empty, check MicroXRCEAgent and the namespace.")
            }

            HelpSection {
                title: qsTr("TAB - SCENARIO (Experiment Runner)")
                subtitle: qsTr("Run Python scripts or JSON scenarios through ExperimentContext.")
                accent: Cmp.Theme.warning
                body:
                    qsTr("<b>Python Script Mode</b><br>") +
                    qsTr("&nbsp;&nbsp;<b>OPEN</b> loads a .py file into the editor. <b>SAVE</b> writes the editor content to <code>experiments/uploads/&lt;name&gt;.py</code> and starts it. <b>RUN/STOP</b> executes or stops the current script. Script output is streamed into the global log with the <code>[SCRIPT]</code> prefix.<br><br>") +
                    qsTr("<b>JSON Scenario Mode</b><br>") +
                    qsTr("&nbsp;&nbsp;A predefined step list such as takeoff, hover, goto, and land is executed by ScenarioRunner. <i>Use SITL</i> can create SITL instances automatically. Results appear as pass/fail entries with duration.<br><br>") +
                    qsTr("<b>Watchdog</b><br>") +
                    qsTr("&nbsp;&nbsp;<code>experiment.setScriptTimeout(seconds)</code> sets a hard timeout that triggers force_stop after expiration.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Common Pitfalls</b></span><br>") +
                    qsTr("&nbsp;&nbsp;Scripts are code execution. Run only trusted scripts. If a script blocks inside a C library, force-stop may not interrupt it; restart the app if needed.")
            }

            HelpSection {
                title: qsTr("TAB - FLIGHT LOG")
                subtitle: qsTr("Offline replay and plots from telemetry CSVs written during previous connections.")
                accent: "#a78bfa"
                body:
                    qsTr("<b>Data Source</b><br>") +
                    qsTr("&nbsp;&nbsp;Each drone connection writes <code>logs/&lt;timestamp&gt;_&lt;drone&gt;_telemetry.csv</code> through <code>TelemetryLogger</code>. If the queue saturates, frames are dropped and the final dropped count is recorded.<br><br>") +
                    qsTr("<b>Functions</b><br>") +
                    qsTr("&nbsp;&nbsp;File selection, multi-select comparison overlays, plots for altitude, battery, speed, and heading over time, per-drone colors, and PNG export for reports.<br><br>") +
                    qsTr("<span style='color:#f59e0b'><b>Common Pitfalls</b></span><br>") +
                    qsTr("&nbsp;&nbsp;An empty plot usually means the CSV is empty or headers were not recognized. TelemetryLogger writes a header on the first frame.")
            }

            HelpSection {
                title: qsTr("TAB - SYSTEM LOG")
                subtitle: qsTr("Aggregated live stream of backend logs from swarm, experiment, safety, and ROS2.")
                accent: Cmp.Theme.textSecondary
                body:
                    qsTr("<b>What you see</b><br>") +
                    qsTr("&nbsp;&nbsp;Live entries with timestamp, level badge, drone tag, and message. Auto-scroll keeps the latest entry visible, and the header shows an error counter.<br><br>") +
                    qsTr("<b>Filters</b><br>") +
                    qsTr("&nbsp;&nbsp;Level dropdown (ALL / INFO / WARN / ERROR), case-insensitive search, and <b>CLEAR</b> for the in-memory log. The autosave file remains on disk.<br><br>") +
                    qsTr("<b>Persistence</b><br>") +
                    qsTr("&nbsp;&nbsp;Logs are also written to <code>tools/ui/syslogs/&lt;date&gt;_&lt;time&gt;.txt</code>. Always include this file in bug reports.")
            }

            HelpSection {
                title: qsTr("INSTRBAR (top strip, always visible)")
                subtitle: qsTr("Cockpit instruments and quick commands across all tabs.")
                accent: Cmp.Theme.accent
                body:
                    qsTr("<b>Tiles from left to right</b><br>") +
                    qsTr("&nbsp;&nbsp;1. <b>DRONE</b> - combo box and connection indicator.<br>") +
                    qsTr("&nbsp;&nbsp;2. <b>ARMED/MODE</b> - armed indicator, flight mode, and drone ID.<br>") +
                    qsTr("&nbsp;&nbsp;3. <b>Artificial Horizon</b> - live roll/pitch from the ATTITUDE stream.<br>") +
                    qsTr("&nbsp;&nbsp;4. <b>Compass</b> - heading with cardinal labels.<br>") +
                    qsTr("&nbsp;&nbsp;5. <b>ALT/SPEED/CLIMB</b> - numeric tiles with trend bars and unit conversion.<br>") +
                    qsTr("&nbsp;&nbsp;6. <b>BATTERY/GPS</b> - percentage, voltage, fix type, and satellite count.<br>") +
                    qsTr("&nbsp;&nbsp;7. <b>QUICK CMD</b> - ARM, DISARM, TAKEOFF, LAND, RTL, HOLD, plus set-altitude field.<br>") +
                    qsTr("&nbsp;&nbsp;8. <b>FLIGHT MODE</b> - Stab, Alt-H, Loiter, Guided, Auto, PosHld.<br><br>") +
                    qsTr("<b>Important:</b> quick commands and mode switches apply to all checked mission targets. If none are checked, they fall back to the selected drone.")
            }

            HelpSection {
                title: qsTr("CONVENTIONS, GOTCHAS AND TROUBLESHOOTING")
                accent: Cmp.Theme.danger
                body:
                    qsTr("<b>Connection Strings</b><br>") +
                    qsTr("&nbsp;&nbsp;<code>tcp:127.0.0.1:5762</code> - default ArduCopter SITL.<br>") +
                    qsTr("&nbsp;&nbsp;<code>tcp:127.0.0.1:5772</code> - SITL drone #2, typically +10 per vehicle.<br>") +
                    qsTr("&nbsp;&nbsp;<code>udp:127.0.0.1:14550</code> - common PX4 SITL endpoint.<br>") +
                    qsTr("&nbsp;&nbsp;<code>serial:/dev/ttyACM0:57600</code> or <code>serial:COM5:57600</code> - hardware.<br><br>") +
                    qsTr("<b>Altitudes</b><br>") +
                    qsTr("&nbsp;&nbsp;UI inputs are AGL. <code>alt_rel</code> is height above spawn. <code>alt</code> / <code>alt_amsl</code> are MSL.<br><br>") +
                    qsTr("<b>Mission Queue is One-Shot</b><br>") +
                    qsTr("&nbsp;&nbsp;After <b>START MISSION</b>, the editable list is cleared. Green map markers remain as a visual reference.<br><br>") +
                    qsTr("<b>SITL Spawn at Same Position</b><br>") +
                    qsTr("&nbsp;&nbsp;By default, SITL drones may spawn at the same Lat/Lon. APF can escalate during takeoff. Use staggered altitudes or spawn offsets.<br><br>") +
                    qsTr("<b>FSM Dead Ends</b><br>") +
                    qsTr("&nbsp;&nbsp;<code>EMERGENCY</code> requires reset/reconnect. <code>ERROR</code> indicates a hard fault. <code>DISCONNECTED</code> triggers reconnect attempts.<br><br>") +
                    qsTr("<b>Bug Report Checklist</b><br>") +
                    qsTr("&nbsp;&nbsp;1. Current <code>tools/ui/syslogs/&lt;date&gt;_&lt;time&gt;.txt</code><br>") +
                    qsTr("&nbsp;&nbsp;2. GCS console output (stdout + stderr)<br>") +
                    qsTr("&nbsp;&nbsp;3. Relevant <code>logs/&lt;timestamp&gt;_&lt;drone&gt;_telemetry.csv</code><br>") +
                    qsTr("&nbsp;&nbsp;4. SITL console output if simulation was used")
            }

            Rectangle {
                width: parent.width
                radius: Cmp.Theme.radiusMd
                color: Cmp.Theme.bgPanel
                border.color: Cmp.Theme.border
                border.width: 1
                height: glossCol.implicitHeight + Cmp.Theme.spacing(3)

                Rectangle {
                    width: 4
                    height: parent.height - Cmp.Theme.spacing(2)
                    anchors {
                        left: parent.left
                        leftMargin: Cmp.Theme.spacing(1)
                        verticalCenter: parent.verticalCenter
                    }
                    radius: 2
                    color: Cmp.Theme.info
                }

                Column {
                    id: glossCol
                    anchors {
                        left: parent.left
                        leftMargin: Cmp.Theme.spacing(2.5)
                        right: parent.right
                        rightMargin: Cmp.Theme.spacing(2)
                        top: parent.top
                        topMargin: Cmp.Theme.spacing(1.5)
                    }
                    spacing: Cmp.Theme.spacing(1)

                    Text {
                        text: qsTr("GLOSSARY")
                        color: Cmp.Theme.info
                        font.pixelSize: Cmp.Theme.fontMd
                        font.weight: Font.Bold
                        font.letterSpacing: 0.5
                    }

                    GlossaryRow { term: "AGL"; def: qsTr("Above Ground at Launch - altitude above takeoff point.") }
                    GlossaryRow { term: "AMSL / MSL"; def: qsTr("Above Mean Sea Level - absolute altitude.") }
                    GlossaryRow { term: "APF"; def: qsTr("Artificial Potential Field - repulsive collision protection.") }
                    GlossaryRow { term: "FSM"; def: qsTr("Finite State Machine - state automaton per drone.") }
                    GlossaryRow { term: "Selected Drone"; def: qsTr("The one drone whose telemetry is currently displayed.") }
                    GlossaryRow { term: "Mission Target"; def: qsTr("A checked drone that receives actions such as ARM, GOTO, and MISSION.") }
                    GlossaryRow { term: "WP"; def: qsTr("Waypoint - Lat/Lon/Alt point in a mission.") }
                    GlossaryRow { term: "RTL"; def: qsTr("Return To Launch - drone flies back to its launch point.") }
                    GlossaryRow { term: "SITL"; def: qsTr("Software In The Loop - drone simulation without hardware.") }
                    GlossaryRow { term: "uXRCE-DDS"; def: qsTr("Micro XRCE-DDS - PX4 bridge to ROS2.") }
                    GlossaryRow { term: "uORB"; def: qsTr("Micro Object Request Broker - PX4 internal message bus.") }
                    GlossaryRow { term: "NED"; def: qsTr("North-East-Down local coordinate system.") }
                    GlossaryRow { term: "Geofence"; def: qsTr("Virtual boundary with radius and altitude limits.") }
                    GlossaryRow { term: "Boids"; def: qsTr("Swarm algorithm with Separation, Alignment, and Cohesion.") }
                    GlossaryRow { term: "Leader-Follower"; def: qsTr("Formation model with one leader and followers using relative slot offsets.") }
                }
            }

            HelpSection {
                title: qsTr("KEYBOARD AND MOUSE SHORTCUTS")
                accent: Cmp.Theme.warning
                body:
                    qsTr("<b style='color:#fbbf24;letter-spacing:1px;'>FLIGHT COMMANDS</b><br>") +
                    qsTr("<table cellspacing='0' cellpadding='0' style='margin-top:4px;margin-bottom:10px;'>") +
                    qsTr("<tr><td style='width:180px'><b style='color:#93c5fd;font-family:Consolas'>Ctrl + A</b></td><td style='color:#cbd5e1'>ARM - arm all mission targets, or selected drone if none are checked</td></tr>") +
                    qsTr("<tr><td><b style='color:#93c5fd;font-family:Consolas'>Ctrl + D</b></td><td style='color:#cbd5e1'>DISARM - disarm all mission targets</td></tr>") +
                    qsTr("<tr><td><b style='color:#93c5fd;font-family:Consolas'>Ctrl + T</b></td><td style='color:#cbd5e1'>TAKEOFF to 10 m AGL</td></tr>") +
                    qsTr("<tr><td><b style='color:#93c5fd;font-family:Consolas'>Ctrl + L</b></td><td style='color:#cbd5e1'>LAND in place</td></tr>") +
                    qsTr("<tr><td><b style='color:#93c5fd;font-family:Consolas'>Ctrl + Home</b></td><td style='color:#cbd5e1'>RTL - Return to Launch</td></tr>") +
                    qsTr("<tr><td><b style='color:#ef4444;font-family:Consolas'>Ctrl + E</b></td><td style='color:#fca5a5'>EMERGENCY STOP - immediately disarm all drones</td></tr>") +
                    qsTr("</table>") +
                    qsTr("<b style='color:#fbbf24;letter-spacing:1px;'>NAVIGATION</b><br>") +
                    qsTr("<table cellspacing='0' cellpadding='0' style='margin-top:4px;margin-bottom:10px;'>") +
                    qsTr("<tr><td style='width:180px'><b style='color:#93c5fd;font-family:Consolas'>Ctrl + M</b></td><td style='color:#cbd5e1'>Jump to Map tab</td></tr>") +
                    qsTr("<tr><td><b style='color:#93c5fd;font-family:Consolas'>Ctrl + 1 ... 9</b></td><td style='color:#cbd5e1'>Select tabs 1-9 directly</td></tr>") +
                    qsTr("</table>") +
                    qsTr("<b style='color:#fbbf24;letter-spacing:1px;'>MAP AND MISSION</b><br>") +
                    qsTr("<table cellspacing='0' cellpadding='0' style='margin-top:4px;margin-bottom:10px;'>") +
                    qsTr("<tr><td style='width:180px'><b style='color:#93c5fd;font-family:Consolas'>Ctrl + W</b></td><td style='color:#cbd5e1'>Enable / disable waypoint mode</td></tr>") +
                    qsTr("<tr><td><b style='color:#93c5fd;font-family:Consolas'>ESC</b></td><td style='color:#cbd5e1'>Cancel waypoint mode or map-pick without setting a waypoint</td></tr>") +
                    qsTr("<tr><td><b style='color:#93c5fd;font-family:Consolas'>Left Click (WP mode)</b></td><td style='color:#cbd5e1'>Place waypoint on map</td></tr>") +
                    qsTr("</table>") +
                    qsTr("<b style='color:#fbbf24;letter-spacing:1px;'>SYSTEM</b><br>") +
                    qsTr("<table cellspacing='0' cellpadding='0' style='margin-top:4px;margin-bottom:10px;'>") +
                    qsTr("<tr><td style='width:180px'><b style='color:#93c5fd;font-family:Consolas'>F5</b></td><td style='color:#cbd5e1'>Refresh serial ports in the header</td></tr>") +
                    qsTr("<tr><td><b style='color:#93c5fd;font-family:Consolas'>Ctrl + S (Script Editor)</b></td><td style='color:#cbd5e1'>Save and Run in the Experiment tab</td></tr>") +
                    qsTr("</table>") +
                    qsTr("<b style='color:#fbbf24;letter-spacing:1px;'>MOUSE</b><br>") +
                    qsTr("<table cellspacing='0' cellpadding='0' style='margin-top:4px;'>") +
                    qsTr("<tr><td style='width:180px'><b style='color:#94a3b8'>Click drone in sidebar</b></td><td style='color:#cbd5e1'>Set selected drone and update telemetry display</td></tr>") +
                    qsTr("<tr><td><b style='color:#94a3b8'>Click mission checkbox</b></td><td style='color:#cbd5e1'>Toggle mission target selection</td></tr>") +
                    qsTr("<tr><td><b style='color:#94a3b8'>Mouse wheel on map</b></td><td style='color:#cbd5e1'>Zoom</td></tr>") +
                    qsTr("<tr><td><b style='color:#94a3b8'>Right-click + drag</b></td><td style='color:#cbd5e1'>Pan map</td></tr>") +
                    qsTr("<tr><td><b style='color:#94a3b8'>Click drone marker</b></td><td style='color:#cbd5e1'>Set selected drone and center map</td></tr>") +
                    qsTr("</table>") +
                    qsTr("<br><span style='color:#475569;font-style:italic;font-size:10px;'>All Ctrl shortcuts apply to active mission targets. Empty target set falls back to selected drone. Ctrl+A/D/T/L may be blocked while the Map tab is active because WebEngineView consumes those keys; switch to another tab first.</span>")
            }

            Rectangle {
                width: parent.width
                height: 64
                radius: Cmp.Theme.radiusMd
                color: Cmp.Theme.bgPanel
                border.color: Cmp.Theme.border
                border.width: 1

                Column {
                    anchors.centerIn: parent
                    spacing: Cmp.Theme.spacing(0.5)

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: qsTr("For issues: collect System Log + syslogs/*.txt + console output.")
                        color: Cmp.Theme.textSecondary
                        font.pixelSize: Cmp.Theme.fontSm
                        font.italic: true
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: qsTr("This Help Panel is read-only - no bindings, no side effects.")
                        color: Cmp.Theme.textMuted
                        font.pixelSize: Cmp.Theme.fontXs
                        font.italic: true
                    }
                }
            }

            Item { width: 1; height: Cmp.Theme.spacing(1) }
        }
    }
}
