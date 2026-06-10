pragma Singleton
import QtQuick

// ── Centralised design tokens ─────────────────────────────────────────
// Single source of truth for colours, typography and spacing.
// Use:   Theme.bg, Theme.accent, Theme.fontMono, Theme.spacing(2), …
//
// Registered as a QML Singleton via qmldir. Once we have the module set
// up, `import "components" as Cmp` makes `Cmp.Theme.bg` available.
QtObject {
    // ── Surface colours (improved contrast) ───────────────────────────
    readonly property color bg:           "#0a0e1a"  // Darker for better contrast
    readonly property color bgElevated:   "#141b2d"  // More distinct elevation
    readonly property color bgInput:      "#1a2332"  // Better input visibility
    readonly property color bgPanel:      "#0f1420"  // Subtle panel distinction
    readonly property color bgHover:      "#1e2a3f"  // Clear hover state

    // ── Borders / outlines (improved visibility) ──────────────────────
    readonly property color border:       "#2d3748"
    readonly property color borderMuted:  "#1e293b"
    readonly property color borderStrong: "#3d4d65"  // More visible
    readonly property color borderFocus:  "#3b82f6"  // Clear focus indicator

    // ── Text (improved hierarchy) ─────────────────────────────────────
    readonly property color textPrimary:   "#f1f5f9"  // Brighter primary
    readonly property color textSecondary: "#a0aec0"  // Better secondary
    readonly property color textMuted:     "#6b7280"  // Clearer muted
    readonly property color textFaded:     "#4b5563"  // Subtle faded
    readonly property color textDisabled:  "#374151"  // Clear disabled state

    // ── Brand / accents (vibrant and accessible) ──────────────────────
    readonly property color accent:       "#3b82f6"   // Brighter blue
    readonly property color accentLight:  "#60a5fa"   // Lighter variant
    readonly property color accentDark:   "#2563eb"   // Darker variant
    readonly property color success:      "#10b981"   // More vibrant green
    readonly property color successDark:  "#059669"
    readonly property color warning:      "#f59e0b"
    readonly property color warningDark:  "#d97706"
    readonly property color danger:       "#ef4444"
    readonly property color dangerDark:   "#dc2626"
    readonly property color info:         "#06b6d4"
    readonly property color infoDark:     "#0891b2"
    readonly property color violet:       "#8b5cf6"
    readonly property color violetDark:   "#7c3aed"

    // ── Semantic colors for states ────────────────────────────────────
    readonly property color stateIdle:      "#64748b"
    readonly property color stateArming:    "#f59e0b"
    readonly property color stateArmed:     "#f97316"
    readonly property color stateTakeoff:   "#3b82f6"
    readonly property color stateFlying:    "#10b981"
    readonly property color stateMission:   "#8b5cf6"
    readonly property color stateLanding:   "#f59e0b"
    readonly property color stateRTL:       "#f97316"
    readonly property color stateEmergency: "#ef4444"

    // ── Drone type colours (consistent across UI) ─────────────────────
    readonly property color droneGeneric:     "#3b82f6"
    readonly property color droneObservation: "#8b5cf6"
    readonly property color droneCoordinator: "#10b981"

    function droneColor(type) {
        if (type === "observation") return droneObservation
        if (type === "coordinator") return droneCoordinator
        return droneGeneric
    }

    // ── Typography (improved readability) ──────────────────────────────
    // Platform-specific primary font (best-looking choice per OS).
    readonly property string fontSans: Qt.platform.os === "windows" ? "Segoe UI"
                                     : Qt.platform.os === "osx"     ? "SF Pro Text"
                                     : "Ubuntu"       // Linux / other

    readonly property string fontMono: Qt.platform.os === "windows" ? "Cascadia Code"
                                     : Qt.platform.os === "osx"     ? "SF Mono"
                                     : "JetBrains Mono"  // Better Linux default

    // Prioritised family lists for font.families (Qt ≥ 5.13).
    readonly property var fontFamiliesSans: [
        "Segoe UI",      // Windows 10/11
        "SF Pro Text",   // macOS
        "Inter",         // Modern web font
        "Ubuntu",        // Ubuntu Linux
        "Noto Sans",     // Android / cross-platform
        "Helvetica Neue",
        "Arial",         // universal fallback
    ]

    readonly property var fontFamiliesMono: [
        "Cascadia Code", // Windows Terminal / Win 11
        "JetBrains Mono",// Modern coding font
        "Fira Code",     // Popular coding font
        "SF Mono",       // macOS
        "Consolas",      // Windows Vista+
        "Menlo",         // macOS (older)
        "DejaVu Sans Mono", // Linux
        "Liberation Mono",  // Linux
        "Courier New",      // universal fallback
    ]

    // Font sizes (improved scale)
    readonly property int   fontXS:  9
    readonly property int   fontS:   11
    readonly property int   fontM:   13
    readonly property int   fontL:   15
    readonly property int   fontXL:  18
    readonly property int   fontXXL: 24
    
    // Aliases for convenience
    readonly property int   fontXs:  fontXS
    readonly property int   fontSm:  fontS
    readonly property int   fontMd:  fontM
    readonly property int   fontLg:  fontL
    readonly property int   fontXl:  fontXL
    readonly property int   fontXxl: fontXXL

    // Font weights
    readonly property int   fontWeightNormal:   400
    readonly property int   fontWeightMedium:   500
    readonly property int   fontWeightSemiBold: 600
    readonly property int   fontWeightBold:     700

    // ── Spacing scale (improved 8px grid) ─────────────────────────────
    function spacing(n) { return n * 8 }
    
    // Common spacing values
    readonly property int spaceXS:  4
    readonly property int spaceS:   8
    readonly property int spaceM:   16
    readonly property int spaceL:   24
    readonly property int spaceXL:  32
    readonly property int spaceXXL: 48

    // ── Border radius (improved scale) ────────────────────────────────
    readonly property int radiusXS: 4
    readonly property int radiusS:  6
    readonly property int radiusM:  8
    readonly property int radiusL:  12
    readonly property int radiusXL: 16
    // Aliases for convenience
    readonly property int radiusXs: radiusXS
    readonly property int radiusSm: radiusS
    readonly property int radiusMd: radiusM
    readonly property int radiusLg: radiusL
    readonly property int radiusXl: radiusXL

    // ── Shadows (for depth) ───────────────────────────────────────────
    readonly property string shadowSm:  "0 1px 2px 0 rgba(0, 0, 0, 0.3)"
    readonly property string shadowMd:  "0 4px 6px -1px rgba(0, 0, 0, 0.4)"
    readonly property string shadowLg:  "0 10px 15px -3px rgba(0, 0, 0, 0.5)"
    readonly property string shadowXl:  "0 20px 25px -5px rgba(0, 0, 0, 0.6)"

    // ── Transitions (smooth animations) ───────────────────────────────
    readonly property int   transitionFast:   150
    readonly property int   transitionNormal: 250
    readonly property int   transitionSlow:   350
    // Aliases for convenience
    readonly property int durationFast:   transitionFast
    readonly property int durationNormal: transitionNormal
    readonly property int durationSlow:   transitionSlow
    
    // Easing curves
    readonly property int   easingStandard: Easing.OutCubic
    readonly property int   easingEmphasized: Easing.OutQuart
    readonly property int   easingDecelerate: Easing.OutQuad

    // ── Z-index layers ────────────────────────────────────────────────
    readonly property int   zBase:      0
    readonly property int   zDropdown:  1000
    readonly property int   zSticky:    1100
    readonly property int   zFixed:     1200
    readonly property int   zModal:     1300
    readonly property int   zPopover:   1400
    readonly property int   zTooltip:   1500
}
