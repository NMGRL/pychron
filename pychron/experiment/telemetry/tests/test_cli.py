"""Tests for the pychron-telemetry CLI (Phase 6)."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from typer.testing import CliRunner

from pychron.experiment.telemetry.cli import app
from pychron.experiment.telemetry.event import TelemetryEvent

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_log(path: Path, events: list[TelemetryEvent]) -> None:
    """Write a list of TelemetryEvents to a JSONL file."""
    with open(path, "w") as f:
        for e in events:
            f.write(json.dumps(e.to_dict(), default=str) + "\n")


def _make_session_events(
    queue_id: str = "test_queue",
    trace_id: str = "trace_abc",
    run_id: str = "sample-001-00-00",
) -> list[TelemetryEvent]:
    """Build a minimal realistic set of telemetry events for a session."""
    now = time.time()
    return [
        TelemetryEvent(
            event_type="telemetry_session_start",
            ts=now,
            level="info",
            queue_id=queue_id,
            trace_id=trace_id,
            component="executor",
            action="session_start",
            payload={"session_id": "session_001"},
        ),
        TelemetryEvent(
            event_type="state_transition",
            ts=now + 0.01,
            level="info",
            queue_id=queue_id,
            trace_id=trace_id,
            run_id=run_id,
            component="executor_machine",
            action="transition",
            state_from="idle",
            state_to="running_queue",
            accepted=True,
        ),
        TelemetryEvent(
            event_type="span_start",
            ts=now + 0.05,
            level="info",
            queue_id=queue_id,
            trace_id=trace_id,
            run_id=run_id,
            component="run_executor",
            action="extraction",
            span_id="span_extraction",
            parent_span_id=None,
        ),
        TelemetryEvent(
            event_type="span_end",
            ts=now + 0.35,
            level="info",
            queue_id=queue_id,
            trace_id=trace_id,
            run_id=run_id,
            component="run_executor",
            action="extraction",
            span_id="span_extraction",
            parent_span_id=None,
            duration_ms=300.0,
            success=True,
        ),
        TelemetryEvent(
            event_type="device_command",
            ts=now + 0.10,
            level="info",
            queue_id=queue_id,
            trace_id=trace_id,
            run_id=run_id,
            component="extraction_line",
            action="open_valve",
            success=True,
            duration_ms=50.0,
        ),
        TelemetryEvent(
            event_type="monitor_check",
            ts=now + 0.20,
            level="info",
            queue_id=queue_id,
            trace_id=trace_id,
            run_id=run_id,
            component="monitor",
            action="check",
            payload={"temperature": 300},
        ),
        TelemetryEvent(
            event_type="telemetry_session_end",
            ts=now + 1.0,
            level="info",
            queue_id=queue_id,
            trace_id=trace_id,
            component="executor",
            action="session_end",
            payload={"session_id": "session_001", "total_queues": 1},
        ),
    ]


# ---------------------------------------------------------------------------
# inspect
# ---------------------------------------------------------------------------


class TestInspectCommand(unittest.TestCase):
    """Tests for the inspect subcommand."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test.jsonl"
        _write_log(self.log_file, _make_session_events())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_inspect_shows_all_events(self) -> None:
        result = runner.invoke(app, ["inspect", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("7 event(s) shown", result.output)

    def test_inspect_filter_by_type(self) -> None:
        result = runner.invoke(app, ["inspect", str(self.log_file), "--type", "span_start"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("1 event(s) shown", result.output)
        self.assertIn("span_start", result.output)

    def test_inspect_filter_by_component(self) -> None:
        result = runner.invoke(app, ["inspect", str(self.log_file), "--component", "monitor"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("1 event(s) shown", result.output)

    def test_inspect_filter_by_run_id(self) -> None:
        result = runner.invoke(app, ["inspect", str(self.log_file), "--run", "sample-001-00-00"])
        self.assertEqual(result.exit_code, 0, result.output)
        # session_start and session_end have no run_id; 5 events do
        self.assertIn("5 event(s) shown", result.output)

    def test_inspect_limit(self) -> None:
        result = runner.invoke(app, ["inspect", str(self.log_file), "--limit", "3"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("3 event(s) shown", result.output)

    def test_inspect_verbose_shows_payload(self) -> None:
        result = runner.invoke(app, ["inspect", str(self.log_file), "--verbose", "--limit", "1"])
        self.assertEqual(result.exit_code, 0, result.output)
        # First event is session_start which has a payload
        self.assertIn("session_001", result.output)

    def test_inspect_missing_file(self) -> None:
        result = runner.invoke(app, ["inspect", "/nonexistent/path.jsonl"])
        self.assertNotEqual(result.exit_code, 0)

    def test_inspect_no_matches_exits_cleanly(self) -> None:
        result = runner.invoke(app, ["inspect", str(self.log_file), "--type", "no_such_type"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("No events", result.output)


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------


class TestTimelineCommand(unittest.TestCase):
    """Tests for the timeline subcommand."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test.jsonl"
        _write_log(self.log_file, _make_session_events())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_timeline_renders(self) -> None:
        result = runner.invoke(app, ["timeline", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("span(s) rendered", result.output)
        self.assertIn("extraction", result.output)

    def test_timeline_custom_width(self) -> None:
        result = runner.invoke(app, ["timeline", str(self.log_file), "--width", "40"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("span(s) rendered", result.output)

    def test_timeline_missing_file(self) -> None:
        result = runner.invoke(app, ["timeline", "/nonexistent/path.jsonl"])
        self.assertNotEqual(result.exit_code, 0)

    def test_timeline_no_spans_exits_cleanly(self) -> None:
        # Write a log with no span events
        log_no_spans = Path(self.temp_dir.name) / "no_spans.jsonl"
        events = [
            TelemetryEvent(
                event_type="state_transition",
                ts=time.time(),
                level="info",
                component="executor_machine",
                action="transition",
                state_from="idle",
                state_to="running",
            )
        ]
        _write_log(log_no_spans, events)
        result = runner.invoke(app, ["timeline", str(log_no_spans)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("No span events", result.output)

    def test_timeline_filter_by_run(self) -> None:
        result = runner.invoke(app, ["timeline", str(self.log_file), "--run", "sample-001-00-00"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("span(s) rendered", result.output)


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


class TestStatsCommand(unittest.TestCase):
    """Tests for the stats subcommand."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test.jsonl"
        _write_log(self.log_file, _make_session_events())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_stats_shows_total_events(self) -> None:
        result = runner.invoke(app, ["stats", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Total events", result.output)
        self.assertIn("7", result.output)

    def test_stats_shows_event_type_counts(self) -> None:
        result = runner.invoke(app, ["stats", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("state_transition", result.output)
        self.assertIn("span_start", result.output)

    def test_stats_shows_span_duration_table(self) -> None:
        result = runner.invoke(app, ["stats", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("extraction", result.output)
        self.assertIn("300", result.output)  # 300ms duration

    def test_stats_shows_queue_id(self) -> None:
        result = runner.invoke(app, ["stats", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("test_queue", result.output)

    def test_stats_missing_file(self) -> None:
        result = runner.invoke(app, ["stats", "/nonexistent/path.jsonl"])
        self.assertNotEqual(result.exit_code, 0)

    def test_stats_empty_file_exits_cleanly(self) -> None:
        empty_log = Path(self.temp_dir.name) / "empty.jsonl"
        empty_log.write_text("")
        result = runner.invoke(app, ["stats", str(empty_log)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("No events", result.output)


# ---------------------------------------------------------------------------
# replay
# ---------------------------------------------------------------------------


class TestReplayCommand(unittest.TestCase):
    """Tests for the replay subcommand."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "test.jsonl"
        _write_log(self.log_file, _make_session_events())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_replay_shows_report_header(self) -> None:
        result = runner.invoke(app, ["replay", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("INCIDENT REPORT", result.output)

    def test_replay_shows_queue_id(self) -> None:
        result = runner.invoke(app, ["replay", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("test_queue", result.output)

    def test_replay_shows_state_machine_history(self) -> None:
        result = runner.invoke(app, ["replay", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("executor_machine", result.output)
        self.assertIn("running_queue", result.output)

    def test_replay_shows_device_commands(self) -> None:
        result = runner.invoke(app, ["replay", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("open_valve", result.output)

    def test_replay_shows_monitor_events(self) -> None:
        result = runner.invoke(app, ["replay", str(self.log_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("monitor_check", result.output)

    def test_replay_no_devices_flag(self) -> None:
        result = runner.invoke(app, ["replay", str(self.log_file), "--no-devices"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("open_valve", result.output)

    def test_replay_no_monitors_flag(self) -> None:
        result = runner.invoke(app, ["replay", str(self.log_file), "--no-monitors"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("monitor_check", result.output)

    def test_replay_output_to_file(self) -> None:
        out_file = Path(self.temp_dir.name) / "report.txt"
        result = runner.invoke(app, ["replay", str(self.log_file), "--output", str(out_file)])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(out_file.exists())
        content = out_file.read_text()
        self.assertIn("INCIDENT REPORT", content)
        self.assertIn("test_queue", content)

    def test_replay_missing_file(self) -> None:
        result = runner.invoke(app, ["replay", "/nonexistent/path.jsonl"])
        self.assertNotEqual(result.exit_code, 0)


# ---------------------------------------------------------------------------
# Entry point smoke test
# ---------------------------------------------------------------------------


class TestCliHelp(unittest.TestCase):
    """Basic smoke tests for the CLI root and subcommand help."""

    def test_root_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("inspect", result.output)
        self.assertIn("timeline", result.output)
        self.assertIn("stats", result.output)
        self.assertIn("replay", result.output)

    def test_inspect_help(self) -> None:
        result = runner.invoke(app, ["inspect", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("JSONL", result.output)

    def test_timeline_help(self) -> None:
        result = runner.invoke(app, ["timeline", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)

    def test_stats_help(self) -> None:
        result = runner.invoke(app, ["stats", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)

    def test_replay_help(self) -> None:
        result = runner.invoke(app, ["replay", "--help"])
        self.assertEqual(result.exit_code, 0, result.output)


if __name__ == "__main__":
    unittest.main()
