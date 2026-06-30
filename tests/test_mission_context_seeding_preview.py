"""Tests for MissionContext seeding preview generation."""

from tools.ui.context.mission_context import MissionContext


def _boundary():
    return [
        {"lat": 48.137, "lon": 11.575},
        {"lat": 48.1375, "lon": 11.575},
        {"lat": 48.1375, "lon": 11.5755},
        {"lat": 48.137, "lon": 11.5755},
    ]


def test_generate_seeding_preview_from_qml_params(qapp):
    ctx = MissionContext()

    preview = ctx.generateSeedingPreview(
        {
            "boundary": _boundary(),
            "seedSpacing": 8.0,
            "rowSpacing": 10.0,
            "altitude": 10.0,
            "speed": 3.0,
            "seedCapacity": 1000,
            "seedWeightG": 0.08,
            "tankCapacityG": 1500.0,
            "seedsPerDrop": 2,
            "dispenseRate": 2.5,
            "addRtl": False,
            "exclusionZones": [{"name": "tree", "points": []}],
        }
    )

    assert preview["valid"] is True
    assert preview["errors"] == []
    assert preview["estimatedSeedUsage"] > 0
    assert preview["estimatedSeedWeightKg"] > 0
    assert len(preview["dropPoints"]) > 0
    assert len(preview["flightRows"]) > 0
    assert preview["exclusionZones"][0]["name"] == "tree"
    assert all(wp["cmd"] != 20 for wp in preview["waypoints"])


def test_seeding_preview_changed_signal_and_getter(qapp):
    ctx = MissionContext()
    emissions = []
    ctx.seedingPreviewChanged.connect(lambda: emissions.append(True))

    preview = ctx.generateSeedingPreview(
        {
            "boundary": _boundary(),
            "seedSpacing": 8.0,
            "rowSpacing": 10.0,
            "altitude": 10.0,
            "speed": 3.0,
            "addRtl": False,
        }
    )

    assert emissions == [True]
    assert preview["valid"] is True
    assert ctx.getSeedingPreview() == preview


def test_generate_seeding_preview_uses_stored_boundary_when_params_omit_boundary(qapp):
    ctx = MissionContext()
    ctx.addBoundaryPoint(48.137, 11.575)
    ctx.addBoundaryPoint(48.1375, 11.575)
    ctx.addBoundaryPoint(48.1375, 11.5755)
    ctx.addBoundaryPoint(48.137, 11.5755)

    preview = ctx.generateSeedingPreview({"seed_spacing": 8.0, "row_spacing": 10.0})

    assert preview["valid"] is True
    assert preview["estimatedSeedUsage"] > 0
    assert preview["fieldArea"] > 0


def test_generate_seeding_preview_reports_invalid_boundary(qapp):
    ctx = MissionContext()

    preview = ctx.generateSeedingPreview({"boundary": [], "altitude": 10.0})

    assert preview["valid"] is False
    assert preview["errors"]
    assert preview["dropPoints"] == []


def test_qml_drawing_aliases_exist_and_store_exclusion_zones(qapp):
    ctx = MissionContext()

    ctx.startDrawingExclusionZone()
    ctx.addBoundaryPoint(48.1371, 11.5751)
    ctx.addBoundaryPoint(48.1372, 11.5751)
    ctx.addBoundaryPoint(48.1372, 11.5752)
    ctx.finishDrawingBoundary()

    assert len(ctx._boundary_points) == 0
    assert len(ctx._exclusion_zones) == 1

    ctx.startDrawingSolarRows()
    assert ctx.addingSolarRow is True
    ctx.clearSolarRows()
    assert ctx.solarPanelRowCount == 0


def test_start_drawing_boundary_resets_exclusion_zone_mode(qapp):
    ctx = MissionContext()

    ctx.startDrawingExclusionZone()
    ctx.addBoundaryPoint(48.1371, 11.5751)
    ctx.addBoundaryPoint(48.1372, 11.5751)
    assert len(ctx.getExclusionZones()) == 1

    ctx.startDrawingBoundary()
    ctx.addBoundaryPoint(48.137, 11.575)
    ctx.addBoundaryPoint(48.1375, 11.575)
    ctx.addBoundaryPoint(48.1375, 11.5755)

    assert ctx.fieldBoundaryPoints == 3
    assert ctx.getBoundaryPoints() == [
        {"lat": 48.137, "lon": 11.575},
        {"lat": 48.1375, "lon": 11.575},
        {"lat": 48.1375, "lon": 11.5755},
    ]
    assert ctx.getExclusionZones() == []

    preview = ctx.generateSeedingPreview({"seed_spacing": 8.0, "row_spacing": 10.0})

    assert preview["valid"] is True
    assert preview["errors"] == []


def test_restarting_exclusion_zone_commits_previous_zone(qapp):
    ctx = MissionContext()

    ctx.startDrawingExclusionZone()
    ctx.addBoundaryPoint(48.1371, 11.5751)
    ctx.addBoundaryPoint(48.1372, 11.5751)
    ctx.addBoundaryPoint(48.1372, 11.5752)

    ctx.startDrawingExclusionZone()

    assert len(ctx._exclusion_zones) == 1
    assert ctx.getExclusionZones() == [
        [
            {"lat": 48.1371, "lon": 11.5751},
            {"lat": 48.1372, "lon": 11.5751},
            {"lat": 48.1372, "lon": 11.5752},
        ]
    ]


def test_seeding_preview_includes_active_exclusion_zone(qapp):
    ctx = MissionContext()
    ctx.addBoundaryPoint(48.137, 11.575)
    ctx.addBoundaryPoint(48.1375, 11.575)
    ctx.addBoundaryPoint(48.1375, 11.5755)
    ctx.addBoundaryPoint(48.137, 11.5755)

    ctx.startDrawingExclusionZone()
    ctx.addBoundaryPoint(48.1371, 11.5751)
    ctx.addBoundaryPoint(48.1372, 11.5751)
    ctx.addBoundaryPoint(48.1372, 11.5752)

    preview = ctx.generateSeedingPreview({"seed_spacing": 8.0, "row_spacing": 10.0})

    assert preview["valid"] is True
    assert preview["exclusionZones"] == [
        {
            "name": "exclusion-1",
            "points": [
                {"lat": 48.1371, "lon": 11.5751},
                {"lat": 48.1372, "lon": 11.5751},
                {"lat": 48.1372, "lon": 11.5752},
            ],
        }
    ]
