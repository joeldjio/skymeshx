"""Tests for MissionContext solar preview generation."""

from tools.ui.context.mission_context import MissionContext


def test_generate_solar_preview_from_qml_params(qapp):
    ctx = MissionContext()

    preview = ctx.generateSolarPreview(
        {
            "rows": [
                {
                    "start": {"lat": 48.137, "lon": 11.575},
                    "end": {"lat": 48.138, "lon": 11.575},
                    "width": 2.5,
                }
            ],
            "altitude": 18.0,
            "speed": 4.0,
            "gimbalPitch": -85.0,
            "triggerDistance": 8.0,
            "overlap": 0.25,
            "thermalEnabled": True,
            "addRtl": False,
        }
    )

    assert preview["valid"] is True
    assert preview["errors"] == []
    assert preview["totalImages"] > 0
    assert len(preview["triggerPoints"]) == preview["totalImages"]
    assert len(preview["flightPath"]) > 0
    assert all(wp["cmd"] != 20 for wp in preview["waypoints"])


def test_solar_preview_changed_signal_and_getter(qapp):
    ctx = MissionContext()
    emissions = []
    ctx.solarPreviewChanged.connect(lambda: emissions.append(True))

    preview = ctx.generateSolarPreview(
        {
            "rows": [
                {
                    "start": {"lat": 48.137, "lon": 11.575},
                    "end": {"lat": 48.138, "lon": 11.575},
                    "width": 2.5,
                }
            ],
            "altitude": 18.0,
            "speed": 4.0,
            "gimbalAngle": -85.0,
            "triggerDistance": 8.0,
            "forwardOverlap": 25.0,
            "thermalEnabled": True,
            "addRTL": False,
        }
    )

    assert emissions == [True]
    assert preview["valid"] is True
    assert ctx.getSolarPreview() == preview


def test_generate_solar_preview_uses_stored_rows_when_params_omit_rows(qapp):
    ctx = MissionContext()
    ctx.addSolarRow(48.137, 11.575, 48.138, 11.575)

    preview = ctx.generateSolarPreview({"trigger_distance": 10.0})

    assert preview["valid"] is True
    assert preview["totalImages"] > 0
    assert preview["coverageArea"] > 0


def test_generate_solar_preview_reports_invalid_params(qapp):
    ctx = MissionContext()

    preview = ctx.generateSolarPreview({"rows": [], "altitude": 15.0})

    assert preview["valid"] is False
    assert preview["errors"]
    assert preview["waypoints"] == []


def test_generate_solar_preview_accepts_qml_wizard_aliases(qapp):
    ctx = MissionContext()
    ctx.addSolarRow(48.137, 11.575, 48.138, 11.575)

    preview = ctx.generateSolarPreview(
        {
            "altitude": 20.0,
            "speed": 4.0,
            "gimbalAngle": -70.0,
            "triggerDistance": 12.0,
            "forwardOverlap": 35.0,
            "cameraHFOV": 70.0,
            "cameraVFOV": 50.0,
            "addRTL": False,
            "thermalEnabled": True,
        }
    )

    assert preview["valid"] is True
    assert preview["errors"] == []
    assert preview["triggerPoints"]
    assert preview["triggerPoints"][0]["gimbalAngle"] == -70.0
    assert all(wp["cmd"] != 20 for wp in preview["waypoints"])
    assert preview["validation"]["footprintWidthM"] > 0


def test_generate_solar_preview_converts_trigger_time_to_distance(qapp):
    ctx = MissionContext()
    ctx.addSolarRow(48.137, 11.575, 48.138, 11.575)

    preview = ctx.generateSolarPreview(
        {
            "speed": 5.0,
            "triggerDistance": 0.0,
            "triggerTime": 3.0,
            "thermalEnabled": True,
        }
    )

    assert preview["valid"] is True
    assert preview["errors"] == []
    assert preview["totalImages"] > 0


def test_solar_row_drawing_stays_active_for_multiple_rows(qapp):
    ctx = MissionContext()

    ctx.startDrawingSolarRows()
    ctx.addSolarRowPoint(48.137, 11.575)
    ctx.addSolarRowPoint(48.138, 11.575)

    assert ctx.addingSolarRow is True
    assert ctx.solarPanelRowCount == 1

    ctx.addSolarRowPoint(48.137, 11.576)
    ctx.addSolarRowPoint(48.138, 11.576)

    assert ctx.addingSolarRow is True
    assert ctx.solarPanelRowCount == 2
