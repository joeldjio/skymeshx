import QtQuick
import QtQuick.Controls
import "." as Cmp

// ── Modern Button Component with smooth animations ──────────────────────────
// Usage:
//   ModernButton {
//       text: "Connect"
//       variant: "primary"  // primary, danger, success, warning, default
//       icon: "connect"
//       onClicked: { ... }
//   }
Button {
    id: control
    
    // ── Properties ────────────────────────────────────────────────────────
    property string variant: "default"  // primary, danger, success, warning, default
    property string icon: ""
    property bool loading: false
    
    // ── Styling based on variant ──────────────────────────────────────────
    readonly property color bgColor: {
        switch(variant) {
            case "primary": return Cmp.Theme.accent
            case "danger": return Cmp.Theme.danger
            case "success": return Cmp.Theme.success
            case "warning": return Cmp.Theme.warning
            default: return Cmp.Theme.bgInput
        }
    }
    
    readonly property color bgHoverColor: {
        switch(variant) {
            case "primary": return Cmp.Theme.accentLight
            case "danger": return Cmp.Theme.dangerDark
            case "success": return Cmp.Theme.successDark
            case "warning": return Cmp.Theme.warningDark
            default: return Cmp.Theme.bgHover
        }
    }
    
    readonly property color textColor: {
        return (variant === "default") ? Cmp.Theme.textPrimary : "white"
    }
    
    // ── Layout ────────────────────────────────────────────────────────────
    implicitWidth: Math.max(120, contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: 40
    leftPadding: 20
    rightPadding: 20
    topPadding: 10
    bottomPadding: 10
    
    // ── Background with smooth transitions ────────────────────────────────
    background: Rectangle {
        id: bg
        radius: Cmp.Theme.radiusM
        color: control.enabled ? bgColor : Cmp.Theme.bgPanel
        border.width: variant === "default" ? 1 : 0
        border.color: Cmp.Theme.border
        
        // Smooth color transition
        Behavior on color {
            ColorAnimation {
                duration: Cmp.Theme.transitionFast
                easing.type: Cmp.Theme.easingStandard
            }
        }
        
        // Hover state
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            color: bgHoverColor
            opacity: control.hovered ? 0.15 : 0
            
            Behavior on opacity {
                NumberAnimation {
                    duration: Cmp.Theme.transitionFast
                    easing.type: Cmp.Theme.easingStandard
                }
            }
        }
        
        // Press effect
        scale: control.pressed ? 0.97 : 1.0
        Behavior on scale {
            NumberAnimation {
                duration: 100
                easing.type: Easing.OutQuad
            }
        }
        
        // Subtle shadow for elevated variants
        layer.enabled: variant !== "default"
        layer.effect: DropShadow {
            horizontalOffset: 0
            verticalOffset: 2
            radius: 8
            samples: 16
            color: Qt.rgba(0, 0, 0, 0.3)
            opacity: control.pressed ? 0.1 : 0.3
            
            Behavior on opacity {
                NumberAnimation { duration: 100 }
            }
        }
    }
    
    // ── Content (icon + text) ─────────────────────────────────────────────
    contentItem: Row {
        spacing: Cmp.Theme.spaceS
        
        // Icon (if provided)
        Cmp.Icon {
            visible: icon !== ""
            svg: icon
            size: 18
            color: textColor
            anchors.verticalCenter: parent.verticalCenter
        }
        
        // Loading spinner
        BusyIndicator {
            visible: loading
            running: loading
            width: 18
            height: 18
            anchors.verticalCenter: parent.verticalCenter
        }
        
        // Text
        Text {
            text: control.text
            font.family: Cmp.Theme.fontSans
            font.pixelSize: Cmp.Theme.fontM
            font.weight: variant === "default" ? Cmp.Theme.fontWeightMedium : Cmp.Theme.fontWeightSemiBold
            color: control.enabled ? textColor : Cmp.Theme.textDisabled
            verticalAlignment: Text.AlignVCenter
            anchors.verticalCenter: parent.verticalCenter
            
            Behavior on color {
                ColorAnimation {
                    duration: Cmp.Theme.transitionFast
                }
            }
        }
    }
    
    // ── Ripple effect on click ────────────────────────────────────────────
    Rectangle {
        id: ripple
        anchors.centerIn: parent
        width: 0
        height: width
        radius: width / 2
        color: "white"
        opacity: 0
        
        ParallelAnimation {
            id: rippleAnimation
            NumberAnimation {
                target: ripple
                property: "width"
                from: 0
                to: control.width * 1.5
                duration: 400
                easing.type: Easing.OutQuad
            }
            NumberAnimation {
                target: ripple
                property: "opacity"
                from: 0.3
                to: 0
                duration: 400
                easing.type: Easing.OutQuad
            }
        }
    }
    
    onClicked: {
        if (variant !== "default") {
            rippleAnimation.restart()
        }
    }
    
    // ── Accessibility ─────────────────────────────────────────────────────
    Accessible.role: Accessible.Button
    Accessible.name: text
    Accessible.description: {
        if (loading) return "Loading..."
        if (!enabled) return "Disabled"
        return text
    }
}