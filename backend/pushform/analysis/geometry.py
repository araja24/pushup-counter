"""The wire shape of a Frame, and 2D angles between its Landmarks.

Angles are computed from x and y only: MediaPipe's z is far noisier than the
two projected axes and a side-on push-up lives almost entirely in the image
plane. Every angle here is therefore invariant to the preview mirroring.
"""

from math import atan2, degrees
from collections.abc import Sequence
from typing import Literal, TypeAlias

__all__ = [
    "Side",
    "Frame",
    "Landmarks",
    "Point",
    "NOSE",
    "SHOULDER",
    "ELBOW",
    "WRIST",
    "HIP",
    "KNEE",
    "ANKLE",
    "SIDES",
    "angle_deg",
    "point",
    "visibility",
    "elbow_angle",
    "hip_angle",
]

Side = Literal["left", "right"]
"""Which side of the body a measurement is taken from."""

Point = tuple[float, float]
Landmarks = Sequence[Sequence[float]]
"""The 33 Landmarks of one Frame, each ``[x, y, z, visibility]``."""

Frame: TypeAlias = dict[str, object]
"""One Frame as it arrives from the phone: ``{"t": milliseconds, "lm": Landmarks}``."""

SIDES: tuple[Side, Side] = ("left", "right")

# MediaPipe Pose indices. Odd indices are the left side of the body.
NOSE = 0
SHOULDER: dict[Side, int] = {"left": 11, "right": 12}
ELBOW: dict[Side, int] = {"left": 13, "right": 14}
WRIST: dict[Side, int] = {"left": 15, "right": 16}
HIP: dict[Side, int] = {"left": 23, "right": 24}
KNEE: dict[Side, int] = {"left": 25, "right": 26}
ANKLE: dict[Side, int] = {"left": 27, "right": 28}


def angle_deg(a: Point, b: Point, c: Point) -> float:
    """The angle at vertex ``b`` between ``b->a`` and ``b->c``, in degrees.

    Returns a value in [0, 180]; a straight line through ``b`` gives 180. Uses
    atan2 of the cross and dot products rather than acos of a normalised dot,
    which loses precision exactly where push-ups spend their time -- near the
    straight arm. Two coincident points give 0.0.
    """
    ax, ay = a[0] - b[0], a[1] - b[1]
    cx, cy = c[0] - b[0], c[1] - b[1]
    cross = ax * cy - ay * cx
    dot = ax * cx + ay * cy
    return degrees(atan2(abs(cross), dot))


def point(landmarks: Landmarks, index: int) -> Point:
    """The image-space position of one Landmark."""
    landmark = landmarks[index]
    return (landmark[0], landmark[1])


def visibility(landmarks: Landmarks, index: int) -> float:
    """How confident the detector is that one Landmark is really there."""
    return landmarks[index][3]


def elbow_angle(landmarks: Landmarks, side: Side) -> float:
    """The Elbow Angle on one side: 180 is a straight arm, small is deep."""
    return angle_deg(
        point(landmarks, SHOULDER[side]),
        point(landmarks, ELBOW[side]),
        point(landmarks, WRIST[side]),
    )


def hip_angle(landmarks: Landmarks, side: Side) -> float:
    """The Hip Angle on one side: 180 is a straight body line."""
    return angle_deg(
        point(landmarks, SHOULDER[side]),
        point(landmarks, HIP[side]),
        point(landmarks, ANKLE[side]),
    )
