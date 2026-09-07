"""One Connection: a socket's worth of Sets, turned into wire messages.

The Connection is the only place that knows the shape of what travels over the
socket. It owns one :class:`~pushform.analysis.orchestrator.Orchestrator` and at
most one active Set, and it decides nothing about push-ups -- every verdict comes
back out of the analysis (ADR-0002).

Frames stream from the moment the socket opens, before any Set, so the phone can
show a live Elbow Angle while the user gets into position. The Orchestrator is
therefore always running: it runs a throwaway *preview* Set whenever the user has
no Set of their own, and the Connection reports IDLE and a zero count for it.

    connection = Connection(now=time.monotonic)
    for outgoing in connection.handle(incoming):
        await websocket.send_json(outgoing)
"""

from collections.abc import Callable

from pushform.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from pushform.analysis.events import Event, Phase, RepCompleted, State, Summary
from pushform.analysis.orchestrator import Orchestrator

__all__ = ["Connection", "STATE_INTERVAL_S"]

STATE_INTERVAL_S = 1.0 / 15.0
"""One State message per this many seconds. The phone renders at the camera's
frame rate; it does not need a message per Frame to do it."""

_PREVIEW_SET_ID = "preview"
"""The Set the Orchestrator runs between the user's Sets, so the readout stays
live. Nothing it counts is ever reported."""

COMMANDS = ("start", "stop", "reset")


class Connection:
    """One phone's socket: Frames in, State, Rep and Summary messages out."""

    def __init__(
        self,
        now: Callable[[], float],
        config: AnalysisConfig = DEFAULT_CONFIG,
        state_interval_s: float = STATE_INTERVAL_S,
    ) -> None:
        self._now = now
        self._state_interval_s = state_interval_s
        self._orchestrator = Orchestrator(config)
        self._set_id: str | None = None
        self._last_state_s: float | None = None
        self._begin_preview()

    @property
    def set_id(self) -> str | None:
        """The Set the user has running, or None between Sets."""
        return self._set_id

    def handle(self, message: object) -> list[dict]:
        """Answer one incoming message with the messages to send back.

        A dict carrying ``lm`` is a Frame; a dict carrying ``cmd`` is a command;
        anything else is refused. Nothing raises: a bad message becomes an
        ``error`` message and the Connection stays open.
        """
        if isinstance(message, dict) and "lm" in message:
            return self._on_frame(message)
        if isinstance(message, dict) and "cmd" in message:
            return self._on_command(message)
        return [error("malformed", "Send a Frame with 'lm' or a command with 'cmd'.")]

    def _on_frame(self, frame: dict) -> list[dict]:
        try:
            events = self._orchestrator.process(frame)
        except ValueError as bad_frame:
            return [error("malformed", str(bad_frame))]

        counting = self._set_id is not None
        messages = [rep_message(rep) for rep in reps(events)] if counting else []
        if self._state_due():
            messages.append(self._state_message())
        return messages

    def _on_command(self, message: dict) -> list[dict]:
        command = message["cmd"]
        if command not in COMMANDS:
            return [error("unknown_command", f"Unknown command {command!r}.")]
        if command == "start":
            return self._start(message.get("set_id"))
        if command == "stop":
            return self._stop()
        return self._reset()

    def _start(self, set_id: object) -> list[dict]:
        if not isinstance(set_id, str) or not set_id:
            return [error("malformed", "start needs a 'set_id'.")]
        self._orchestrator.start(set_id)
        self._set_id = set_id
        return [self._forced_state()]

    def _stop(self) -> list[dict]:
        if self._set_id is None:
            return [error("no_active_set", "No Set is running.")]
        summaries = [event for event in self._orchestrator.stop() if isinstance(event, Summary)]
        self._set_id = None
        self._begin_preview()
        return [summary_message(summary) for summary in summaries]

    def _reset(self) -> list[dict]:
        """Discard the Set in progress. No Summary: a reset Set never happened."""
        if self._set_id is None:
            return [error("no_active_set", "No Set is running.")]
        self._set_id = None
        self._begin_preview()
        return [self._forced_state()]

    def _begin_preview(self) -> None:
        """Keep the Orchestrator running so the readout survives between Sets."""
        self._orchestrator.reset()
        self._orchestrator.start(_PREVIEW_SET_ID)

    def _state_due(self) -> bool:
        """True at most once per state interval, by the injected wall clock."""
        now_s = self._now()
        if self._last_state_s is not None and now_s - self._last_state_s < self._state_interval_s:
            return False
        self._last_state_s = now_s
        return True

    def _forced_state(self) -> dict:
        """A State message the phone gets straight away, throttle or not."""
        self._last_state_s = None
        return self._state_message()

    def _state_message(self) -> dict:
        return state_message(self._orchestrator.state, counting=self._set_id is not None)


def reps(events: list[Event]) -> list[RepCompleted]:
    return [event for event in events if isinstance(event, RepCompleted)]


def state_message(state: State, *, counting: bool) -> dict:
    """The per-Frame readout. Outside a Set the Phase is IDLE and nothing is counted."""
    return {
        "type": "state",
        "reps": state.reps if counting else 0,
        "rejected": state.rejected if counting else 0,
        "phase": phase_name(state.phase if counting else Phase.IDLE),
        "elbow_angle": state.elbow_angle,
        "hip_angle": state.hip_angle,
        "aligned": state.aligned,
        "tracking": state.tracking,
        "stalled": state.stalled,
        "side": state.side,
    }


def rep_message(rep: RepCompleted) -> dict:
    """One finished Rep. ``down_ms`` and ``up_ms`` stay off the wire: the phone
    shows a count and a tone, not a breakdown."""
    return {
        "type": "rep",
        "index": rep.index,
        "counted": rep.counted,
        "label": rep.label,
        "reason": rep.reason,
        "source": rep.source,
        "min_elbow": rep.min_elbow,
        "max_elbow": rep.max_elbow,
        "duration_ms": rep.duration_ms,
        "confidence": rep.confidence,
    }


def summary_message(summary: Summary) -> dict:
    return {
        "type": "summary",
        "reps": summary.reps,
        "rejected": summary.rejected,
        "faults": dict(summary.faults),
        "duration_ms": summary.duration_ms,
        "avg_rep_ms": summary.avg_rep_ms,
    }


def error(code: str, message: str) -> dict:
    return {"type": "error", "code": code, "message": message}


def phase_name(phase: Phase) -> str:
    """IDLE, UP or DOWN: the Phase as the wire spells it."""
    return phase.name
