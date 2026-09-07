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

    Visibility is averaged over the three Landmarks that make the Elbow Angle
    -- shoulder, elbow, wrist -- because an arm is only useful if all three are
    there. A tie keeps the side already tracked, so a symmetric figure (a
    perfectly side-on view, or a synthetic one) does not flap between sides.
    """

    def __init__(self, window: int, visibility_floor: float) -> None:
        self._visibility_floor = visibility_floor
        self._history: dict[Side, deque[float]] = {
            side: deque(maxlen=window) for side in geometry.SIDES
        }
        self._side: Side = geometry.SIDES[0]

    @property
    def side(self) -> Side:
        return self._side

    def update(self, landmarks: Landmarks) -> Side:
        """Record this Frame's visibility and return the Tracked Side."""
        for side in geometry.SIDES:
            self._history[side].append(self._arm_visibility(landmarks, side))
        best = max(geometry.SIDES, key=self.mean_visibility)
        if self.mean_visibility(best) > self.mean_visibility(self._side):
            self._side = best
        return self._side

    def mean_visibility(self, side: Side) -> float:
        """Mean visibility of that arm over the window, 0.0 before any Frame."""
        values = self._history[side]
        return sum(values) / len(values) if values else 0.0

    def is_tracked(self, side: Side) -> bool:
        """Whether that arm has been visible enough to trust its angle."""
        return self.mean_visibility(side) >= self._visibility_floor

    def reset(self) -> None:
        for values in self._history.values():
            values.clear()
        self._side = geometry.SIDES[0]

    @staticmethod
    def _arm_visibility(landmarks: Landmarks, side: Side) -> float:
        parts = (geometry.SHOULDER[side], geometry.ELBOW[side], geometry.WRIST[side])
        return sum(geometry.visibility(landmarks, index) for index in parts) / len(parts)
