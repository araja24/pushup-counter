"""The Stall: an Elbow Angle parked between the two Phase thresholds.

Hysteresis (ADR-0004) makes the band between the DOWN and UP thresholds
deliberately inert -- an angle wobbling inside it changes no Phase and counts
no Rep. That is right for a shaking arm and wrong for a user holding half a
push-up: to them the counter has simply stopped working. This watches the
band and says so once, so the phone can ask for a lockout.
"""

from pushform.analysis.config import AnalysisConfig
from pushform.analysis.events import Stall, StallCleared

__all__ = ["StallDetector"]


class StallDetector:
    """Times how long the smoothed Elbow Angle stays inside the band.

    Timed by Frame timestamps rather than a wall clock, so a Recording replayed
    off disk stalls in exactly the same places it did live.
    """

    def __init__(self, config: AnalysisConfig) -> None:
        self._low = config.down_threshold_deg
        self._high = config.up_threshold_deg
        self._stall_ms = config.stall_ms
        self.reset()

    @property
    def stalled(self) -> bool:
        return self._stalled

    def update(self, elbow_angle: float, t_ms: int) -> Stall | StallCleared | None:
        """Feed one smoothed Elbow Angle; return the event it caused, if any."""
        if not self._in_band(elbow_angle):
            return self._leave(elbow_angle, t_ms)
        if self._entered_ms is None:
            self._entered_ms = t_ms
            return None
        held_ms = t_ms - self._entered_ms
        if self._stalled or held_ms <= self._stall_ms:
            return None
        self._stalled = True
        return Stall(t_ms=t_ms, elbow_angle=elbow_angle, held_ms=held_ms)

    def reset(self) -> None:
        """Forget the dwell in progress. No StallCleared: nothing is watching."""
        self._entered_ms: int | None = None
        self._stalled = False

    def _in_band(self, elbow_angle: float) -> bool:
        """Inclusive of both thresholds: the band is exactly the angles the
        Phase machine ignores, and it ignores the thresholds themselves."""
        return self._low <= elbow_angle <= self._high

    def _leave(self, elbow_angle: float, t_ms: int) -> StallCleared | None:
        was_stalled = self._stalled
        self.reset()
        return StallCleared(t_ms=t_ms, elbow_angle=elbow_angle) if was_stalled else None
