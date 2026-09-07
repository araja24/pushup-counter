"""What the analysis says: Phase changes, Reps, the Set Summary, and State.

These dataclasses are the contract between the analysis core and everything
downstream -- the WebSocket handler, the replay CLI and the tests. They are
frozen so an event cannot be edited after it has been reported.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

from pushform.analysis.geometry import Side

__all__ = [
    "Phase",
    "FAULTS",
    "PhaseChanged",
    "RepCompleted",
    "Summary",
    "State",
    "Event",
]


class Phase(str, Enum):
    """Which half of the movement the body is in.

    IDLE is the absence of a Set rather than a half of the movement: it is what
    the analysis reports before a Set starts and after one stops.
    """

    IDLE = "idle"
    UP = "up"
    DOWN = "down"


FAULTS: tuple[str, ...] = ("partial_rom", "hip_sag", "hip_pike")
"""The reasons a Rep can be rejected. Nothing raises one yet."""


def _no_faults() -> dict[str, int]:
    return dict.fromkeys(FAULTS, 0)


@dataclass(frozen=True, slots=True)
class PhaseChanged:
    """The Phase crossed a threshold on this Frame."""

    t_ms: int
    phase: Phase
    previous: Phase
    elbow_angle: float


@dataclass(frozen=True, slots=True)
class RepCompleted:
    """A Rep finished: the body entered DOWN and has now left it.

    Emitted only for Reps, never for Bounces. ``label``, ``reason``, ``source``
    and ``confidence`` are the classifier's fields; with no classifier loaded a
    Rep is ``unlabelled`` and counted.
    """

    index: int
    min_elbow: float
    max_elbow: float
    duration_ms: int
    down_ms: int
    """From entering DOWN to the deepest Elbow Angle."""

    up_ms: int
    """From the deepest Elbow Angle to leaving DOWN."""

    counted: bool = True
    label: str = "unlabelled"
    reason: str | None = None
    source: str = "none"
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class Summary:
    """The record a Set leaves behind when it stops."""

    reps: int
    duration_ms: int
    avg_rep_ms: float
    rejected: int = 0
    faults: dict[str, int] = field(default_factory=_no_faults)


@dataclass(frozen=True, slots=True)
class State:
    """Everything the phone needs to draw one Frame of feedback.

    ``aligned`` is always ``True`` and ``stalled`` always ``False`` until the
    form rules land: the phone draws a green skeleton and no stall prompt, and
    the wire shape does not change when the rules arrive.
    """

    reps: int
    rejected: int
    phase: Phase
    elbow_angle: float | None
    hip_angle: float | None
    aligned: bool | None
    tracking: bool
    stalled: bool
    side: Side | None


Event: TypeAlias = PhaseChanged | RepCompleted | Summary
"""Anything the Orchestrator hands back to its caller."""
