"""The hysteresis Phase machine (ADR-0004).

Two thresholds, not one: the Elbow Angle must fall below the DOWN threshold to
enter DOWN and rise above the higher UP threshold to leave it. An angle wobbling
anywhere between the two changes nothing, which is what stops a shaking arm at
mid-depth from manufacturing Reps.
"""

from pushform.analysis.config import AnalysisConfig
from pushform.analysis.events import Phase

__all__ = ["PhaseMachine"]


class PhaseMachine:
    """Tracks UP and DOWN for one Set. Knows nothing about time or Reps."""

    def __init__(self, config: AnalysisConfig) -> None:
        self._config = config
        self._phase = Phase.UP

    @property
    def phase(self) -> Phase:
        return self._phase

    def update(self, elbow_angle: float) -> Phase | None:
        """Feed one smoothed Elbow Angle; return the new Phase, or None if unchanged."""
        if self._phase is Phase.UP and elbow_angle < self._config.down_threshold_deg:
            self._phase = Phase.DOWN
        elif self._phase is Phase.DOWN and elbow_angle > self._config.up_threshold_deg:
            self._phase = Phase.UP
        else:
            return None
        return self._phase

    def reset(self) -> None:
        """Back to UP, where every Set begins."""
        self._phase = Phase.UP
