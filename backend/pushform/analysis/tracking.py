"""Whether this Frame's Elbow Angle can be believed.

A detector loses a Landmark constantly and briefly -- a hand sweeps across the
elbow, the exposure shifts, the arm leaves the frame for two Frames of a
descent. Reacting to every one of those would strand the Phase machine
mid-rep; ignoring all of them would let it count push-ups for a user who has
walked away. The monitor is the line between the two: a short run of unseen
Frames is a blink and the last good angle is held over it, a long one is
Tracking Lost and the machine freezes.
"""

from enum import Enum

from pushform.analysis.config import AnalysisConfig

__all__ = ["Reading", "TrackingMonitor"]


class Reading(str, Enum):
    """What the analysis should do with the Frame just measured."""

    TRACKED = "tracked"
    """The arm was seen: use this Frame's Elbow Angle."""

    HELD = "held"
    """Unseen, but not for long: reuse the last good Elbow Angle."""

    LOST = "lost"
    """Unseen for longer than the grace window: Tracking is Lost, freeze."""


class TrackingMonitor:
    """Counts consecutive unseen Frames on the Tracked Side.

    Deliberately per-Frame rather than averaged over a window: a window would
    smear the moment the arm disappeared across the Frames either side of it,
    and the whole point is to know exactly how many Frames in a row were bad.
    """

    def __init__(self, config: AnalysisConfig) -> None:
        self._floor = config.visibility_floor
        self._grace_frames = config.tracking_grace_frames
        self.reset()

    @property
    def lost(self) -> bool:
        """Whether Tracking is currently Lost."""
        return self._lost

    def update(self, arm_visibility: float) -> Reading:
        """Judge one Frame's visibility on the Tracked Side."""
        if arm_visibility >= self._floor:
            self._unseen_frames = 0
            self._lost = False
            return Reading.TRACKED
        self._unseen_frames += 1
        self._lost = self._unseen_frames > self._grace_frames
        return Reading.LOST if self._lost else Reading.HELD

    def reset(self) -> None:
        self._unseen_frames = 0
        self._lost = False
