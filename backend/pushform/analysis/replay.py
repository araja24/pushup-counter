"""Replay a Recording through the analysis and print what it made of it.

    python -m pushform.analysis.replay recording.json

The Recording is the JSON the record screen downloads: ``{"label": str | null,
"frames": [frame, ...]}``. Running it back through the same Orchestrator the
live app uses is how a developer checks a capture without a phone in hand.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from pushform.analysis.events import (
    Event,
    PhaseChanged,
    RepCompleted,
    Stall,
    StallCleared,
    Summary,
    TrackingLost,
    TrackingRegained,
)
from pushform.analysis.orchestrator import Orchestrator

__all__ = ["main"]


def main(argv: Sequence[str] | None = None) -> int:
    """Replay one Recording. Returns a process exit code."""
    parser = argparse.ArgumentParser(
        prog="python -m pushform.analysis.replay",
        description="Replay a recorded set of frames and print its events.",
    )
    parser.add_argument("recording", type=Path, help="Recording JSON to replay.")
    args = parser.parse_args(argv)

    try:
        recording = json.loads(args.recording.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"Could not read {args.recording}: {error}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(f"{args.recording} is not valid JSON: {error}", file=sys.stderr)
        return 1

    try:
        lines = replay(recording)
    except ValueError as error:
        print(f"malformed recording {args.recording}: {error}", file=sys.stderr)
        return 1

    for line in lines:
        print(line)
    return 0


def replay(recording: object) -> list[str]:
    """Run a Recording through a Set and describe every event it produced.

    Raises:
        ValueError: The Recording is not an envelope of wire-shape Frames.
    """
    frames, label = _unpack(recording)
    orchestrator = Orchestrator()
    orchestrator.start(label)

    lines = []
    for frame in frames:
        lines.extend(describe(event) for event in orchestrator.process(frame))
    (summary,) = orchestrator.stop()
    lines.append(describe(summary))
    lines.append(f"Counted reps: {summary.reps}")
    return lines


def _unpack(recording: object) -> tuple[list, str]:
    """The Frames and Set label of a Recording, or a ValueError naming the shape."""
    if not isinstance(recording, dict) or not isinstance(recording.get("frames"), list):
        raise ValueError('expected {"label": string or null, "frames": [frame, ...]}')
    label = recording.get("label")
    return recording["frames"], label if isinstance(label, str) and label else "replay"


def describe(event: Event) -> str:
    """One event as a line of log."""
    if isinstance(event, PhaseChanged):
        return (
            f"{event.t_ms:>7} ms  phase {event.previous.value} -> {event.phase.value}"
            f"  elbow {event.elbow_angle:.1f} deg"
        )
    if isinstance(event, RepCompleted):
        return (
            f"{'':>7}     rep {event.index}  {event.duration_ms} ms"
            f"  (down {event.down_ms} ms, up {event.up_ms} ms)"
            f"  elbow {event.min_elbow:.1f}-{event.max_elbow:.1f} deg"
            f"  {event.label}"
        )
    if isinstance(event, TrackingLost):
        return f"{event.t_ms:>7} ms  tracking lost"
    if isinstance(event, TrackingRegained):
        return f"{event.t_ms:>7} ms  tracking regained"
    if isinstance(event, Stall):
        return (
            f"{event.t_ms:>7} ms  stalled at {event.elbow_angle:.1f} deg"
            f" for {event.held_ms} ms"
        )
    if isinstance(event, StallCleared):
        return f"{event.t_ms:>7} ms  stall cleared at {event.elbow_angle:.1f} deg"
    if isinstance(event, Summary):
        return (
            f"{'':>7}     set of {event.reps} reps, {event.rejected} rejected,"
            f" {event.duration_ms} ms, average rep {event.avg_rep_ms:.0f} ms"
        )
    raise TypeError(f"Unknown event: {event!r}")


if __name__ == "__main__":  # pragma: no cover - exercised as a subprocess
    raise SystemExit(main())
