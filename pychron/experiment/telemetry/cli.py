"""CLI tools for analysing pychron telemetry logs.

Entry point: pychron-telemetry

Subcommands
-----------
inspect  -- Pretty-print events from a JSONL telemetry file.
timeline -- Render an ASCII span timeline for a JSONL file.
stats    -- Print aggregate metrics (counts, durations, failure rates).
replay   -- Reconstruct and display the incident report for a JSONL file.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from pychron.experiment.telemetry.event import TelemetryEvent
from pychron.experiment.telemetry.replay import (
    load_telemetry_log,
    replay_queue_telemetry,
)

app = typer.Typer(
    name="pychron-telemetry",
    help="Analyse pychron structured telemetry logs.",
    no_args_is_help=True,
    add_completion=False,
)

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

_LEVEL_COLORS = {
    "debug": typer.colors.BRIGHT_BLACK,
    "info": typer.colors.GREEN,
    "warning": typer.colors.YELLOW,
    "error": typer.colors.RED,
    "critical": typer.colors.BRIGHT_RED,
}

_TYPE_COLORS = {
    "span_start": typer.colors.CYAN,
    "span_end": typer.colors.BLUE,
    "state_transition": typer.colors.MAGENTA,
    "device_io": typer.colors.YELLOW,
    "monitor_check": typer.colors.BRIGHT_YELLOW,
    "interlock_check": typer.colors.BRIGHT_YELLOW,
    "telemetry_session_start": typer.colors.BRIGHT_GREEN,
    "telemetry_session_end": typer.colors.BRIGHT_GREEN,
    "device_health_state_change": typer.colors.BRIGHT_MAGENTA,
    "device_health_failure": typer.colors.RED,
    "device_health_recovery_attempt": typer.colors.YELLOW,
    "device_health_recovery_success": typer.colors.GREEN,
    "device_quorum_check": typer.colors.BRIGHT_BLUE,
}


def _fmt_ts(ts: float) -> str:
    """Format unix timestamp as HH:MM:SS.mmm."""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%H:%M:%S.") + f"{dt.microsecond // 1000:03d}"


def _color(text: str, color: Optional[str], bold: bool = False) -> str:
    """Return ANSI-coloured text if a terminal supports it."""
    if color is None:
        return text
    return typer.style(text, fg=color, bold=bold)


def _render_success(success: Optional[bool]) -> str:
    """Render success status as: ✓/✗/?.

    Args:
        success: True for passed, False for failed, None for unknown

    Returns:
        Colored status string (✓, ✗, or ?)
    """
    if success is True:
        return _color(" ✓", typer.colors.GREEN)
    elif success is False:
        return _color(" ✗", typer.colors.RED)
    else:
        return _color(" ?", typer.colors.YELLOW)


def _fmt_event_line(event: TelemetryEvent, index: int) -> str:
    """Format a single event as a one-line summary."""
    ts_str = _fmt_ts(event.ts)
    etype = event.event_type or "unknown"
    color = _TYPE_COLORS.get(etype)
    etype_col = _color(f"{etype:<30}", color)

    component = event.component or ""
    action = event.action or ""
    run_id = f"run={event.run_id}" if event.run_id else ""

    parts = [p for p in [component, action, run_id] if p]
    detail = "  ".join(parts)

    success_marker = ""
    if event.success is not None:
        if event.success is True:
            success_marker = _color(" OK", typer.colors.GREEN)
        elif event.success is False:
            success_marker = _color(" FAIL", typer.colors.RED)
        else:
            success_marker = _color(" UNKNOWN", typer.colors.YELLOW)

    duration = f"  {event.duration_ms:.1f}ms" if event.duration_ms is not None else ""

    return f"{index:>5}  {ts_str}  {etype_col}  {detail}{duration}{success_marker}"


# ---------------------------------------------------------------------------
# inspect
# ---------------------------------------------------------------------------


@app.command()
def inspect(
    log_file: Path = typer.Argument(..., help="Path to JSONL telemetry log file."),
    event_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by event type (e.g. span_start, state_transition)."
    ),
    component: Optional[str] = typer.Option(
        None, "--component", "-c", help="Filter by component name."
    ),
    run_id: Optional[str] = typer.Option(None, "--run", "-r", help="Filter by run ID."),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Maximum events to show."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full JSON payload."),
) -> None:
    """Pretty-print events from a JSONL telemetry file.

    Examples::

        pychron-telemetry inspect queue_exp001_20260101_120000.jsonl
        pychron-telemetry inspect run.jsonl --type span_start --verbose
        pychron-telemetry inspect run.jsonl --run sample-001-00-00 -n 20
    """
    try:
        events = list(load_telemetry_log(log_file))
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    # Apply filters
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    if component:
        events = [e for e in events if (e.component or "") == component]
    if run_id:
        events = [e for e in events if e.run_id == run_id]
    if limit is not None:
        events = events[:limit]

    if not events:
        typer.echo("No events match the given filters.")
        raise typer.Exit(0)

    typer.echo(f"{'#':>5}  {'time':12}  {'event_type':<30}  detail")
    typer.echo("-" * 90)

    for i, event in enumerate(events):
        typer.echo(_fmt_event_line(event, i + 1))
        if verbose and event.payload:
            payload_str = json.dumps(event.payload, indent=4, default=str)
            for line in payload_str.splitlines():
                typer.echo(f"         {line}")

    typer.echo(f"\n{len(events)} event(s) shown.")


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------


def _build_span_tree(
    events: list[TelemetryEvent],
) -> tuple[dict[str, dict], list[str]]:
    """Build a span tree from events.

    Returns:
        spans: dict span_id -> {start, end, action, component, parent, depth}
        roots: ordered list of root span IDs
    """
    starts: dict[str, TelemetryEvent] = {}
    ends: dict[str, TelemetryEvent] = {}

    for e in events:
        if e.event_type == "span_start" and e.span_id:
            starts[e.span_id] = e
        elif e.event_type == "span_end" and e.span_id:
            ends[e.span_id] = e

    spans: dict[str, dict] = {}
    for sid, start in starts.items():
        end = ends.get(sid)
        spans[sid] = {
            "start": start.ts,
            "end": end.ts if end else None,
            "duration_ms": end.duration_ms if end else None,
            "action": start.action or sid,
            "component": start.component or "",
            "parent": start.parent_span_id,
            "success": end.success if end else None,
            "depth": 0,
        }

    # Compute depths
    def _depth(sid: str, visited: set) -> int:
        if sid in visited:
            return 0
        visited.add(sid)
        parent = spans[sid]["parent"]
        if parent and parent in spans:
            return 1 + _depth(parent, visited)
        return 0

    for sid in spans:
        spans[sid]["depth"] = _depth(sid, set())

    # Order by start time
    roots = sorted(spans, key=lambda s: spans[s]["start"])
    return spans, roots


@app.command()
def timeline(
    log_file: Path = typer.Argument(..., help="Path to JSONL telemetry log file."),
    width: int = typer.Option(80, "--width", "-w", help="Width of the timeline bar in characters."),
    run_id: Optional[str] = typer.Option(None, "--run", "-r", help="Filter to a specific run ID."),
) -> None:
    """Render an ASCII span timeline showing operation durations.

    Each span is drawn as a bar proportional to its duration relative to
    the total session window.  Nested spans are indented.

    Examples::

        pychron-telemetry timeline queue_exp001_20260101_120000.jsonl
        pychron-telemetry timeline run.jsonl --width 100
    """
    try:
        events = list(load_telemetry_log(log_file))
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    if run_id:
        events = [e for e in events if e.run_id == run_id]

    spans, ordered = _build_span_tree(events)

    if not spans:
        typer.echo("No span events found in log.")
        raise typer.Exit(0)

    all_starts = [s["start"] for s in spans.values()]
    all_ends = [s["end"] for s in spans.values() if s["end"] is not None]

    t_min = min(all_starts)
    t_max = max(all_ends) if all_ends else t_min + 1.0
    total = t_max - t_min or 1.0

    # Header
    typer.echo(f"\nTimeline  ({_fmt_ts(t_min)} — {_fmt_ts(t_max)})  total={total * 1000:.0f}ms\n")
    label_width = 28

    for sid in ordered:
        s = spans[sid]
        indent = "  " * s["depth"]
        label = f"{indent}{s['action']}"
        label = label[:label_width]

        bar_start = int((s["start"] - t_min) / total * width)
        if s["end"] is not None:
            bar_end = max(bar_start + 1, int((s["end"] - t_min) / total * width))
        else:
            bar_end = bar_start + 1

        bar = " " * bar_start + "█" * max(1, bar_end - bar_start)
        bar = bar.ljust(width)

        dur = f"{s['duration_ms']:.0f}ms" if s["duration_ms"] is not None else "open"
        ok = _render_success(s["success"])

        typer.echo(f"{label:<{label_width}} |{bar}| {dur}{ok}")

    typer.echo(f"\n{len(spans)} span(s) rendered.")


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


def _print_device_health_stats(events: list[TelemetryEvent]) -> None:
    """Print device health statistics from events.

    Analyzes device health events and prints summary stats including:
    - Per-device failure and recovery counts
    - Success rates
    - Phase quorum check results
    """
    # Collect device health events
    device_events_by_name: dict[str, dict] = {}

    for e in events:
        if e.event_type in (
            "device_health_state_change",
            "device_health_failure",
            "device_health_recovery_attempt",
            "device_health_recovery_success",
        ):
            payload = e.payload or {}
            device_name = payload.get("device", "unknown")

            if device_name not in device_events_by_name:
                device_events_by_name[device_name] = {
                    "state_changes": [],
                    "failures": 0,
                    "recovery_attempts": 0,
                    "recovery_successes": 0,
                    "last_state": None,
                }

            if e.event_type == "device_health_state_change":
                device_events_by_name[device_name]["state_changes"].append(
                    {
                        "from": payload.get("from_state"),
                        "to": payload.get("to_state"),
                        "ts": e.ts,
                    }
                )
                device_events_by_name[device_name]["last_state"] = payload.get("to_state")
            elif e.event_type == "device_health_failure":
                device_events_by_name[device_name]["failures"] += 1
            elif e.event_type == "device_health_recovery_attempt":
                device_events_by_name[device_name]["recovery_attempts"] += 1
            elif e.event_type == "device_health_recovery_success":
                device_events_by_name[device_name]["recovery_successes"] += 1

    if device_events_by_name:
        typer.echo("\n--- Device Health Statistics ---")
        typer.echo(
            f"  {'device':<20} {'state':<15} {'failures':>8} {'recovery_ok':>8} {'state_changes':>8}"
        )
        typer.echo(f"  {'-' * 20} {'-' * 15} {'-' * 8} {'-' * 8} {'-' * 8}")
        for device_name, stats in sorted(device_events_by_name.items()):
            state = stats["last_state"] or "unknown"
            state_col = _color(state, typer.colors.RED if state != "HEALTHY" else None)
            typer.echo(
                f"  {device_name:<20} {state_col:<15} {stats['failures']:>8} {stats['recovery_successes']:>8} {len(stats['state_changes']):>8}"
            )

    # Collect phase quorum check results
    phase_quorum_checks: dict[str, dict] = {}
    for e in events:
        if e.event_type == "device_quorum_check":
            payload = e.payload or {}
            phase_name = payload.get("phase", "unknown")
            passed = payload.get("passed", False)

            if phase_name not in phase_quorum_checks:
                phase_quorum_checks[phase_name] = {"passed": 0, "failed": 0}

            if passed:
                phase_quorum_checks[phase_name]["passed"] += 1
            else:
                phase_quorum_checks[phase_name]["failed"] += 1

    if phase_quorum_checks:
        typer.echo("\n--- Phase Quorum Checks ---")
        typer.echo(f"  {'phase':<20} {'passed':>8} {'failed':>8} {'total':>8}")
        typer.echo(f"  {'-' * 20} {'-' * 8} {'-' * 8} {'-' * 8}")
        for phase_name in sorted(phase_quorum_checks.keys()):
            stats = phase_quorum_checks[phase_name]
            total = stats["passed"] + stats["failed"]
            fail_col = (
                _color(str(stats["failed"]), typer.colors.RED)
                if stats["failed"] > 0
                else str(stats["failed"])
            )
            typer.echo(f"  {phase_name:<20} {stats['passed']:>8} {fail_col:>8} {total:>8}")


def stats(
    log_file: Path = typer.Argument(..., help="Path to JSONL telemetry log file."),
) -> None:
    """Print aggregate metrics: event counts, span durations, failure rates.

    Examples::

        pychron-telemetry stats queue_exp001_20260101_120000.jsonl
    """
    try:
        events = list(load_telemetry_log(log_file))
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    if not events:
        typer.echo("No events in log.")
        raise typer.Exit(0)

    # Count by type
    type_counts: dict[str, int] = {}
    for e in events:
        type_counts[e.event_type] = type_counts.get(e.event_type, 0) + 1

    # Span durations
    durations_by_action: dict[str, list[float]] = {}
    failures_by_action: dict[str, int] = {}
    for e in events:
        if e.event_type == "span_end" and e.duration_ms is not None:
            key = e.action or "unknown"
            durations_by_action.setdefault(key, []).append(e.duration_ms)
            if e.success is False:
                failures_by_action[key] = failures_by_action.get(key, 0) + 1

    # Session window
    t_min = min(e.ts for e in events)
    t_max = max(e.ts for e in events)
    session_ms = (t_max - t_min) * 1000

    # Unique runs
    run_ids = {e.run_id for e in events if e.run_id}
    queue_ids = {e.queue_id for e in events if e.queue_id}

    typer.echo("\n=== Telemetry Stats ===\n")
    typer.echo(f"  File          : {log_file}")
    typer.echo(f"  Session span  : {session_ms:.0f}ms  ({_fmt_ts(t_min)} — {_fmt_ts(t_max)})")
    typer.echo(f"  Total events  : {len(events)}")
    typer.echo(f"  Queues        : {', '.join(sorted(queue_ids)) or 'none'}")
    typer.echo(f"  Runs          : {len(run_ids)}")

    typer.echo("\n--- Event type counts ---")
    for etype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        color = _TYPE_COLORS.get(etype)
        typer.echo(f"  {_color(f'{etype:<35}', color)} {count:>6}")

    # Device health statistics
    _print_device_health_stats(events)

    if durations_by_action:
        typer.echo("\n--- Span durations (ms) by action ---")
        typer.echo(f"  {'action':<30} {'count':>6} {'min':>8} {'mean':>8} {'max':>8} {'fail':>6}")
        typer.echo(f"  {'-' * 30} {'-' * 6} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 6}")
        for action, durs in sorted(durations_by_action.items()):
            n = len(durs)
            mn = min(durs)
            mx = max(durs)
            mean = sum(durs) / n
            fail = failures_by_action.get(action, 0)
            fail_col = _color(f"{fail:>6}", typer.colors.RED if fail else None)
            typer.echo(f"  {action:<30} {n:>6} {mn:>8.1f} {mean:>8.1f} {mx:>8.1f} {fail_col}")

    typer.echo("")


# ---------------------------------------------------------------------------
# replay
# ---------------------------------------------------------------------------


@app.command()
def replay(
    log_file: Path = typer.Argument(..., help="Path to JSONL telemetry log file."),
    show_timeline: bool = typer.Option(
        True, "--timeline/--no-timeline", help="Show event timeline."
    ),
    show_devices: bool = typer.Option(True, "--devices/--no-devices", help="Show device commands."),
    show_monitors: bool = typer.Option(
        True, "--monitors/--no-monitors", help="Show monitor/interlock events."
    ),
    show_state_machines: bool = typer.Option(
        True, "--state-machines/--no-state-machines", help="Show state machine history."
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Write incident report to file instead of stdout."
    ),
) -> None:
    """Reconstruct and display the incident report for a telemetry log.

    Parses the JSONL file and produces a structured incident report showing
    the execution timeline, state machine history, device commands, and
    monitor/interlock decisions.

    Examples::

        pychron-telemetry replay queue_exp001_20260101_120000.jsonl
        pychron-telemetry replay run.jsonl --no-devices -o report.txt
    """
    try:
        report = replay_queue_telemetry(log_file)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("PYCHRON TELEMETRY INCIDENT REPORT")
    lines.append("=" * 60)
    lines.append(report.summary)
    lines.append("")

    if show_timeline and report.timeline:
        lines.append("--- Execution Timeline ---")
        for ev in report.timeline:
            ts = _fmt_ts(ev.ts)
            dur = f"  {ev.duration_ms:.1f}ms" if ev.duration_ms is not None else ""
            ok = ""
            if ev.success is True:
                ok = "  OK"
            elif ev.success is False:
                ok = "  FAIL"
            lines.append(
                f"  {ts}  {ev.event_type:<22}  {ev.component:<20}  {ev.action or ''}{dur}{ok}"
            )
        lines.append("")

    if show_state_machines and report.state_machine_history:
        lines.append("--- State Machine History ---")
        for machine, transitions in sorted(report.state_machine_history.items()):
            lines.append(f"  {machine}:")
            for t in transitions:
                accepted = "accepted" if t.accepted else "rejected"
                reason = f"  ({t.reason})" if t.reason else ""
                lines.append(
                    f"    {_fmt_ts(t.ts)}  {t.state_from} -> {t.state_to}  [{accepted}]{reason}"
                )
        lines.append("")

    if show_devices and report.device_commands:
        lines.append("--- Device Commands ---")
        for cmd in report.device_commands:
            ts = _fmt_ts(cmd["ts"])
            dur = f"  {cmd['duration_ms']:.1f}ms" if cmd.get("duration_ms") else ""
            ok = "OK" if cmd.get("success") else "FAIL"
            lines.append(f"  {ts}  {cmd['component']:<20}  {cmd['action']:<20}  {ok}{dur}")
        lines.append("")

    if show_monitors and report.monitor_history:
        lines.append("--- Monitor / Interlock Events ---")
        for m in report.monitor_history:
            ts = _fmt_ts(m["ts"])
            reason = f"  {m['reason']}" if m.get("reason") else ""
            lines.append(f"  {ts}  {m['event_type']:<22}{reason}")
        lines.append("")

    if report.watchdog_events:
        lines.append("--- Watchdog / Health Events ---")
        for w in report.watchdog_events:
            ts = _fmt_ts(w["ts"])
            phase = f" phase={w.get('phase')}" if w.get("phase") else ""
            success = "✓" if w.get("success") else "✗"
            msg = f"  {w.get('message')}" if w.get("message") else ""
            lines.append(f"  {ts}  {w['event_type']:<25} {success}{phase}{msg}")
        lines.append("")

    text = "\n".join(lines)

    if output:
        output.write_text(text)
        typer.echo(f"Report written to {output}")
    else:
        typer.echo(text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the pychron-telemetry console script."""
    app()


if __name__ == "__main__":
    main()
