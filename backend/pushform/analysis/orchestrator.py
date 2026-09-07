"""The one door into the analysis: Frames in, events out.

The WebSocket handler, the replay CLI, the segmentation script and the tests
all drive a Set through this class and nothing else, so there is a single
definition of what a Rep is (ADR-0002).

    orchestrator = Orchestrator()
    orchestrator.start("set-1")
    for frame in frames:
        events = orchestrator.process(frame)
    summary = orchestrator.stop()
"""

from dataclasses import dataclass

from pushform.analysis import geometry
from pushform.analysis.config import DEFAULT_CONFIG, AnalysisConfig
from pushform.analysis.events import (
    Event,
    Phase,
    PhaseChanged,
    RepCompleted,
    State,
    Summary,
    TrackingLost,
    TrackingRegained,
)
from pushform.analysis.filters import MedianFilter, TrackedSideSelector
from pushform.analysis.geometry import Frame, Landmarks, Side
from pushform.analysis.phase import PhaseMachine
from pushform.analysis.stall import StallDetector
from pushform.analysis.tracking import Reading, TrackingMonitor

__all__ = ["Orchestrator"]

WIRE_SHAPE = '{"t": milliseconds, "lm": [[x, y, z, visibility]] * 33}'


def _read(frame: Frame) -> tuple[int, Landmarks]:
    """Pull the timestamp and Landmarks out of a wire-shape Frame.

    Frames come off a network, so this is where a malformed one is turned into
    a single named failure rather than a KeyError or an IndexError from deep
    inside the geometry.
    """
    try:
        t_ms = int(frame["t"])
        landmarks = frame["lm"]
        count = len(landmarks)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Frame must be {WIRE_SHAPE}: {error}") from error
    if count != geometry.LANDMARK_COUNT:
        raise ValueError(f"Frame must be {WIRE_SHAPE}: got {count} landmarks")
    return t_ms, landmarks


@dataclass
class _DownPhase:
    """The DOWN Phase currently underway, which may or may not become a Rep."""

    entered_ms: int
    counts: bool
    """False for the DOWN a Set is already in when it starts: there was no real
    UP-to-DOWN transition, so the ascent out of it is nobody's Rep."""

    min_elbow: float
    min_elbow_ms: int
    max_elbow: float

    def observe(self, elbow_angle: float, t_ms: int) -> None:
        if elbow_angle < self.min_elbow:
            self.min_elbow = elbow_angle
            self.min_elbow_ms = t_ms
        self.max_elbow = max(self.max_elbow, elbow_angle)


class Orchestrator:
    """Runs one Set at a time over a stream of Frames."""

    def __init__(self, config: AnalysisConfig = DEFAULT_CONFIG) -> None:
        self._config = config
        self._elbow_filter = MedianFilter(config.median_window)
        self._sides = TrackedSideSelector(config.side_window)
        self._tracker = TrackingMonitor(config)
        self._stalls = StallDetector(config)
        self._phase = PhaseMachine(config)
        self.reset()

    @property
    def set_id(self) -> str | None:
        """The Set currently running, or the last one started; None after a reset."""
        return self._set_id

    @property
    def state(self) -> State:
        """The per-Frame snapshot as of the last processed Frame."""
        return State(
            reps=self._reps,
            rejected=self._rejected,
            phase=self._phase.phase if self._running else Phase.IDLE,
            elbow_angle=self._elbow_angle,
            hip_angle=self._hip_angle,
            aligned=True,  # Placeholder until the hip rules land (#8).
            tracking=self._tracking,
            stalled=self._stalls.stalled,
            side=self._side,
        )

    def start(self, set_id: str) -> None:
        """Begin a Set. Counting starts from zero, in UP, at the next Frame."""
        self.reset()
        self._set_id = set_id
        self._running = True

    def process(self, frame: Frame) -> list[Event]:
        """Take one wire-shape Frame and return the events it caused.

        Frames arriving outside a Set are ignored without being read: no
        events, and the State keeps reporting IDLE. A Frame whose Tracked Side
        is unseen holds the last good Elbow Angle rather than measuring this
        one; once Tracking is Lost the Phase machine is not fed at all, so it
        freezes where it was and the Rep resumes when the user reappears.

        Raises:
            ValueError: The Frame is not in wire shape. One error for every
                malformed Frame, so a caller reading from the network has a
                single thing to catch and report.
        """
        if not self._running:
            return []

        t_ms, landmarks = _read(frame)
        if self._first_frame_ms is None:
            self._first_frame_ms = t_ms
        self._last_frame_ms = t_ms

        self._choose_side(landmarks)
        reading = self._tracker.update(geometry.arm_visibility(landmarks, self._side))
        events = self._report_tracking(reading, t_ms)
        if reading is Reading.TRACKED:
            self._measure(landmarks)
        elbow_angle = self._elbow_angle
        if reading is Reading.LOST or elbow_angle is None:
            return events

        stall = self._stalls.update(elbow_angle, t_ms)
        if stall is not None:
            events.append(stall)
        events.extend(self._advance(elbow_angle, t_ms))
        if elbow_angle > self._config.up_threshold_deg:
            self._locked_out = True
        return events

    def stop(self) -> list[Event]:
        """End the Set and return its Summary. Nothing to summarise, nothing returned."""
        if not self._running:
            return []
        self._running = False
        self._down_phase = None
        return [
            Summary(
                reps=self._reps,
                rejected=self._rejected,
                duration_ms=self._elapsed_ms(),
                avg_rep_ms=(
                    sum(self._rep_durations) / len(self._rep_durations)
                    if self._rep_durations
                    else 0.0
                ),
            )
        ]

    def reset(self) -> None:
        """Discard the Set in progress without summarising it."""
        self._set_id: str | None = None
        self._running = False
        self._reps = 0
        self._rejected = 0
        self._rep_durations: list[int] = []
        self._down_phase: _DownPhase | None = None
        self._locked_out = False
        self._first_frame_ms: int | None = None
        self._last_frame_ms: int | None = None
        self._elbow_angle: float | None = None
        self._hip_angle: float | None = None
        self._side: Side | None = None
        self._tracking = False
        self._tracking_lost = False
        self._elbow_filter.reset()
        self._sides.reset()
        self._tracker.reset()
        self._stalls.reset()
        self._phase.reset()

    def _choose_side(self, landmarks: Landmarks) -> None:
        """Pick the Tracked Side, and start the smoothing over if it changed.

        Only re-evaluated outside DOWN: mid-Rep the two arms are at different
        points of the same movement, so swapping would rewrite the Rep's depth.
        The one exception is a Phase already frozen by Tracking Lost -- there is
        no live Rep to protect, and the other arm being visible is the only way
        back, so refusing to switch would strand counting in DOWN for good.

        A switch starts the smoothing over. The median window is the abandoned
        arm's history, and keeping it would report that arm for two more Frames
        -- a stale lockout followed by the new arm's real angle is exactly the
        fake descent that invents a Rep.
        """
        previous = self._side
        may_switch = self._phase.phase is not Phase.DOWN or self._tracker.lost
        self._side = self._sides.update(landmarks, may_switch=may_switch)
        if previous is not None and self._side != previous:
            self._elbow_filter.reset()

    def _measure(self, landmarks: Landmarks) -> None:
        """Read this Frame's angles off the Tracked Side."""
        self._hip_angle = geometry.hip_angle(landmarks, self._side)
        self._elbow_angle = self._elbow_filter.push(
            geometry.elbow_angle(landmarks, self._side)
        )

    def _report_tracking(self, reading: Reading, t_ms: int) -> list[Event]:
        """Announce a change in whether the user can be seen, once per change.

        A held Frame still counts as tracked: the last good angle stands in for
        it and nothing downstream can tell the difference, which is the point.
        """
        lost = reading is Reading.LOST
        self._tracking = not lost
        if lost == self._tracking_lost:
            return []
        self._tracking_lost = lost
        if not lost:
            return [TrackingRegained(t_ms=t_ms)]
        # A frozen machine cannot be stalled, and the dwell clock must not run
        # through a gap nobody could see.
        self._stalls.reset()
        return [TrackingLost(t_ms=t_ms)]

    def _advance(self, elbow_angle: float, t_ms: int) -> list[Event]:
        """Apply one smoothed Elbow Angle to the Phase machine and the Rep in progress."""
        previous = self._phase.phase
        changed = self._phase.update(elbow_angle)
        if changed is None:
            if self._down_phase is not None:
                self._down_phase.observe(elbow_angle, t_ms)
            return []

        events: list[Event] = [PhaseChanged(t_ms, changed, previous, elbow_angle)]
        if changed is Phase.DOWN:
            self._down_phase = _DownPhase(
                entered_ms=t_ms,
                counts=self._locked_out,
                min_elbow=elbow_angle,
                min_elbow_ms=t_ms,
                max_elbow=elbow_angle,
            )
            return events

        down_phase, self._down_phase = self._down_phase, None
        if down_phase is None:
            return events
        down_phase.observe(elbow_angle, t_ms)
        rep = self._complete(down_phase, t_ms)
        if rep is not None:
            events.append(rep)
        return events

    def _complete(self, down_phase: _DownPhase, t_ms: int) -> RepCompleted | None:
        """Turn a finished DOWN Phase into a Rep, unless it was a Bounce."""
        duration_ms = t_ms - down_phase.entered_ms
        if not down_phase.counts or duration_ms < self._config.bounce_ms:
            return None
        self._reps += 1
        self._rep_durations.append(duration_ms)
        return RepCompleted(
            index=self._reps,
            min_elbow=down_phase.min_elbow,
            max_elbow=down_phase.max_elbow,
            duration_ms=duration_ms,
            down_ms=down_phase.min_elbow_ms - down_phase.entered_ms,
            up_ms=t_ms - down_phase.min_elbow_ms,
        )

    def _elapsed_ms(self) -> int:
        if self._first_frame_ms is None or self._last_frame_ms is None:
            return 0
        return self._last_frame_ms - self._first_frame_ms
