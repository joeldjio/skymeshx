"""Tests for JSONL crash-safe event logging in TelemetryLogger."""

import json
import os
import tempfile

import pytest


class TestJSONLLogging:
    def test_events_written_immediately_as_jsonl(self, tmp_path):
        from skymeshx.data.logger import TelemetryLogger

        logger = TelemetryLogger(str(tmp_path))
        logger.start(drone_id="test")
        logger.log_event("armed", {"force": False})
        logger.log_event("takeoff", {"altitude": 10.0})
        # JSONL must be written before stop (crash-safe)
        jsonl_files = list(tmp_path.glob("*_events.jsonl"))
        assert len(jsonl_files) == 1, "Expected one JSONL file"
        lines = jsonl_files[0].read_text().strip().splitlines()
        assert len(lines) == 2
        e1 = json.loads(lines[0])
        assert e1["event"] == "armed"
        assert e1["data"] == {"force": False}
        logger.stop()

    def test_each_line_is_valid_json(self, tmp_path):
        from skymeshx.data.logger import TelemetryLogger

        logger = TelemetryLogger(str(tmp_path))
        logger.start(drone_id="test2")
        for i in range(5):
            logger.log_event(f"event_{i}", {"i": i})
        logger.stop()
        jsonl_files = list(tmp_path.glob("*_events.jsonl"))
        lines = jsonl_files[0].read_text().strip().splitlines()
        assert len(lines) == 5
        for line in lines:
            obj = json.loads(line)  # must not raise
            assert "event" in obj and "timestamp" in obj
