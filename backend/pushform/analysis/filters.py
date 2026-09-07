"""Rolling-window smoothing over a stream of Frames.

Pose detection jitters, and a single bad Frame near a threshold would otherwise
fake a Phase change. Both helpers here answer from a short window of history
rather than from the latest Frame alone.
"""

from collections import deque
from statistics import median

from pushform.analysis import geometry
from pushform.analysis.geometry import Landmarks, Side

__all__ = ["MedianFilter", "TrackedSideSelector"]


class MedianFilter:
    """The median of the last N values, N growing until the window is full.

    A median rather than a mean because the failure being defended against is a
    lone wild reading: the mean drags towards it, the median ignores it. The
    cost is a lag of half a window, which falls out of a Rep's duration because
    it delays both the entry to DOWN and the exit from it equally.
    """

    def __init__(self, window: int) -> None:
        self._values: deque[float] = deque(maxlen=window)

    def push(self, value: float) -> float:
        """Add a reading and return the smoothed value."""
        self._values.append(value)
        return median(self._values)

    def reset(self) -> None:
        self._values.clear()


class TrackedSideSelector:
    """Picks the Tracked Side: the arm seen more clearly over the last N Frames.

    Averaged over a window rather than judged Frame by Frame because the
    question is which arm the camera sees better *overall*, and a single bad
    Frame is not an answer to it. A tie keeps the side already tracked, so a
    symmetric figure (a perfectly side-on view, or a synthetic one) does not
    flap between sides.
    """

    def __init__(self, window: int) -> None:
        self._history: dict[Side, deque[float]] = {
            side: deque(maxlen=window) for side in geometry.SIDES
        }
        self._side: Side = geometry.SIDES[0]

    @property
    def side(self) -> Side:
        return self._side

    def update(self, landmarks: Landmarks, *, may_switch: bool = True) -> Side:
        """Record this Frame's visibility and return the Tracked Side.

        Args:
            landmarks: This Frame's Landmarks. Their visibility joins the
                window whether or not the side is allowed to change, so the
                window is never a stale picture of what the camera can see.
            may_switch: False forbids a change of side this Frame. The caller
                passes False mid-Rep, where swapping arms would swap the Elbow
                Angle underneath a Rep already in progress.
        """
        for side in geometry.SIDES:
            self._history[side].append(geometry.arm_visibility(landmarks, side))
        if not may_switch:
            return self._side
        best = max(geometry.SIDES, key=self.mean_visibility)
        if self.mean_visibility(best) > self.mean_visibility(self._side):
            self._side = best
        return self._side

    def mean_visibility(self, side: Side) -> float:
        """Mean visibility of that arm over the window, 0.0 before any Frame."""
        values = self._history[side]
        return sum(values) / len(values) if values else 0.0

    def reset(self) -> None:
        for values in self._history.values():
            values.clear()
        self._side = geometry.SIDES[0]
