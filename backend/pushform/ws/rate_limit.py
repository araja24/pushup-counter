"""How many Frames a second one Connection will look at.

A phone sends Frames as fast as its camera runs and a script can send them as
fast as a socket will take them. The analysis costs the same either way, so the
Connection puts a ceiling on it. Dropping rather than queueing: a Frame skipped
now is replaced 25 ms later by a fresher one, and a queue would only turn extra
work into a stale readout.
"""

from collections import deque

__all__ = ["MAX_FRAMES_PER_SECOND", "FrameRateLimiter"]

MAX_FRAMES_PER_SECOND = 40
"""Comfortably above the 30 a second the phone aims for, so an honest client
never notices this exists."""

WINDOW_S = 1.0


class FrameRateLimiter:
    """A sliding one-second window over the Frames already admitted.

    Sliding rather than a counter reset every second: a fixed window lets a
    client send its whole allowance at the end of one second and again at the
    start of the next, which is the burst the limit exists to flatten.
    """

    def __init__(
        self,
        max_per_second: int = MAX_FRAMES_PER_SECOND,
        window_s: float = WINDOW_S,
    ) -> None:
        self._max_per_second = max_per_second
        self._window_s = window_s
        self._admitted: deque[float] = deque()

    def allow(self, now_s: float) -> bool:
        """Whether the Frame arriving at ``now_s`` may be processed.

        The clock is passed in rather than read here so that one Frame is one
        reading of it, whatever the Connection does with the Frame afterwards.
        """
        while self._admitted and self._admitted[0] <= now_s - self._window_s:
            self._admitted.popleft()
        if len(self._admitted) >= self._max_per_second:
            return False
        self._admitted.append(now_s)
        return True
