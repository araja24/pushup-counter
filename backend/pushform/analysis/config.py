"""The single home of every analysis threshold and window.

No other module defines a magic number that decides Phase, Rep or Tracked Side;
they all read one :class:`AnalysisConfig`. ``GET /api/config`` serves its
thresholds so the phone never hard-codes them either.
"""

from dataclasses import dataclass

__all__ = ["AnalysisConfig", "DEFAULT_CONFIG"]


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    """Thresholds and window sizes for one analysis run.

    Frozen so a running Set cannot be retuned underneath itself.
    """

    down_threshold_deg: float = 95.0
    """Elbow angle below which the Phase becomes DOWN."""

    up_threshold_deg: float = 155.0
    """Elbow angle above which the Phase becomes UP. Above the DOWN threshold,
    so angles between the two leave the Phase alone (hysteresis, ADR-0004)."""

    median_window: int = 5
    """Frames of median filtering applied to the tracked Elbow Angle."""

    side_window: int = 10
    """Frames of visibility history used to choose the Tracked Side."""

    visibility_floor: float = 0.6
    """Mean Landmark visibility at or above which the Tracked Side counts as tracked."""

    bounce_ms: int = 400
    """A DOWN Phase shorter than this is a Bounce: it changes Phase but is never a Rep."""


DEFAULT_CONFIG = AnalysisConfig()
"""The tuning every caller gets unless it deliberately passes its own."""
