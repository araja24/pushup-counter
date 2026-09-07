"""Reading a `config` command into an :class:`AnalysisConfig`.

The phone may retune the two Phase thresholds for its own Connection -- a user
whose shoulders will not take a full descent still wants a counter that works.
What it may not do is send a pair that cannot describe a push-up, so every
value is checked here before it can reach the analysis.
"""

from dataclasses import replace

from pushform.analysis.config import AnalysisConfig

__all__ = ["ConfigRejected", "config_from"]

_STRAIGHT_ARM_DEG = 180.0
"""An Elbow Angle is an angle between two segments: 0 and 180 are the ends of
the scale, and a threshold at either is one nothing can ever cross."""


class ConfigRejected(ValueError):
    """The requested thresholds could not judge a push-up. Names why."""


def config_from(message: dict, current: AnalysisConfig) -> AnalysisConfig:
    """The tuning a `config` command asks for, built on the one in force.

    Only the two thresholds are settable. Window sizes and the Bounce window
    are the analysis's own business and are carried over untouched.

    Raises:
        ConfigRejected: The command does not carry a usable pair of thresholds.
    """
    down = _degrees(message, "down_threshold")
    up = _degrees(message, "up_threshold")
    if down >= up:
        raise ConfigRejected(
            f"down_threshold {down:g} must be below up_threshold {up:g};"
            " the gap between them is the hysteresis."
        )
    return replace(current, down_threshold_deg=down, up_threshold_deg=up)


def _degrees(message: dict, key: str) -> float:
    """One threshold off the wire, or a ConfigRejected saying what was wrong."""
    value = message.get(key)
    # bool is an int in Python, and True is not 1 degree.
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConfigRejected(f"{key} must be a number of degrees.")
    if not 0.0 < value < _STRAIGHT_ARM_DEG:
        raise ConfigRejected(
            f"{key} must be between 0 and {_STRAIGHT_ARM_DEG:g} degrees, not {value:g}."
        )
    return float(value)
