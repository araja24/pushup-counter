"""A synthetic push-up: Frames of Landmarks with an Elbow Angle you dictate.

This generator is the fixture for every analysis test. Nothing here knows about
Phases or Reps; it only draws a side-on figure whose Elbow Angle follows a
requested profile, so a test can state the motion it means and assert on what
the analysis makes of it.

The figure lies along x with shoulder, hip, knee and ankle collinear (until
``hip_deviation_deg`` bends the body line at the hip), the wrist planted on the
floor directly below the shoulder, and the elbow flared back towards the feet.
The shoulder rides up and down as the elbow bends, exactly as a real push-up
does, so the requested Elbow Angle is reproduced to within a rounding error:
:func:`pushform.analysis.geometry.elbow_angle` on the output agrees with the
request to well under a degree.

Left and right Landmarks coincide, because a side-on figure projects both sides
onto the same points. The Tracked Side is therefore decided purely by the
``visibility`` override rather than by an invented near/far asymmetry.
"""

from collections.abc import Callable, Container, Sequence
from math import cos, pi, radians, sin
from random import Random
from typing import Literal, TypeAlias

from pushform.analysis import geometry
from pushform.analysis.geometry import Frame, Side

__all__ = ["Frame", "StartPhase", "VisibilityOverride", "frames_from_angles", "generate_frames"]

StartPhase = Literal["up", "down"]

VisibilityOverride: TypeAlias = Callable[[int], dict[int, float] | None]
"""Frame index -> ``{landmark index: visibility}`` to override, or ``None``."""

LANDMARK_COUNT = 33

_ARM_SEGMENT = 0.16
"""Upper arm and forearm, equal length, in normalised image units."""

_FLOOR_Y = 0.90
_SHOULDER_TO_HIP = 0.20
_HIP_TO_KNEE = 0.15
_KNEE_TO_ANKLE = 0.15
_NOSE_AHEAD = 0.10
_NOSE_RISE = 0.04
_DEFAULT_VISIBILITY = 0.95

_UNUSED_LANDMARK = (0.5, 0.5)
"""Face, hand and foot Landmarks the analysis never reads are parked here."""

_MIN_ANGLE_DEG = 1.0
_MAX_ANGLE_DEG = 179.0


def generate_frames(
    *,
    cycles: int = 1,
    elbow_min_deg: float = 70.0,
    elbow_max_deg: float = 170.0,
    cycle_ms: int = 1500,
    fps: int = 30,
    facing: Side = "right",
    noise_deg: float = 0.0,
    dropped_frames: Container[int] = (),
    start_phase: StartPhase = "up",
    visibility: VisibilityOverride | None = None,
    hip_deviation_deg: float = 0.0,
    seed: int = 0,
) -> list[Frame]:
    """Clean push-up cycles as wire-shape Frames.

    Args:
        cycles: How many full down-and-up cycles to draw.
        elbow_min_deg: Elbow Angle at the bottom of each cycle.
        elbow_max_deg: Elbow Angle at the top (lockout) of each cycle.
        cycle_ms: Wall-clock length of one cycle.
        fps: Frame rate; timestamps are ``round(index * 1000 / fps)``.
        facing: Which way the head points in image space, ``"left"`` or
            ``"right"``. Mirroring changes no angle, only the coordinates.
        noise_deg: Standard deviation of Gaussian noise added to the Elbow
            Angle before the Landmarks are drawn. The result is clamped to a
            drawable range, so heavy noise never produces a degenerate figure.
        dropped_frames: Frame indices to omit entirely, as a dropped Frame
            would be. Surviving Frames keep their original timestamps, so the
            gap stays visible in time.
        start_phase: ``"up"`` starts at lockout; ``"down"`` starts at the
            bottom of a rep, the case where the first ascent must not count.
        visibility: Callable from frame index to a ``{landmark index:
            visibility}`` mapping to override for that Frame, or ``None``.
            This is how a test steers or starves the Tracked Side.
        hip_deviation_deg: Constant bend of the body line at the hip, in
            degrees; the resulting Hip Angle is ``180 - abs(deviation)``.
            Positive sags the hips, negative pikes them.
        seed: Seed for the noise, so a noisy sequence is reproducible.

    Returns:
        One Frame per sampled instant, from ``t = 0`` to ``t = cycles *
        cycle_ms`` inclusive, minus any dropped Frames.
    """
    rng = Random(seed)
    frame_count = round(cycles * cycle_ms * fps / 1000) + 1
    middle = (elbow_max_deg + elbow_min_deg) / 2.0
    amplitude = (elbow_max_deg - elbow_min_deg) / 2.0
    sign = 1.0 if start_phase == "up" else -1.0

    angles = []
    for index in range(frame_count):
        phase = 2.0 * pi * (index * 1000.0 / fps) / cycle_ms
        angle = middle + sign * amplitude * cos(phase)
        if noise_deg:
            angle += rng.gauss(0.0, noise_deg)
        angles.append(min(max(angle, _MIN_ANGLE_DEG), _MAX_ANGLE_DEG))

    frames = frames_from_angles(
        angles,
        fps=fps,
        facing=facing,
        visibility=visibility,
        hip_deviation_deg=hip_deviation_deg,
    )
    return [frame for index, frame in enumerate(frames) if index not in dropped_frames]


def frames_from_angles(
    elbow_angles: Sequence[float],
    *,
    fps: int = 30,
    facing: Side = "right",
    visibility: VisibilityOverride | None = None,
    hip_deviation_deg: float = 0.0,
) -> list[Frame]:
    """Wire-shape Frames drawn straight from a list of Elbow Angles.

    The low-level door into the generator, for tests that need an exact angle
    profile -- a single-Frame spike, or a square-edged DOWN Phase of a chosen
    length -- rather than a smooth cycle.
    """
    return [
        {
            "t": round(index * 1000.0 / fps),
            "lm": _landmarks(
                angle,
                facing=facing,
                hip_deviation_deg=hip_deviation_deg,
                overrides=visibility(index) if visibility else None,
            ),
        }
        for index, angle in enumerate(elbow_angles)
    ]


def _landmarks(
    elbow_deg: float,
    *,
    facing: Side,
    hip_deviation_deg: float,
    overrides: dict[int, float] | None,
) -> list[list[float]]:
    """The 33 Landmarks of a side-on figure holding one Elbow Angle."""
    forward = 1.0 if facing == "right" else -1.0
    half = radians(elbow_deg) / 2.0

    # Two equal arm segments meeting at elbow_deg span this much, so the
    # shoulder sits exactly that far above the planted wrist.
    reach = 2.0 * _ARM_SEGMENT * sin(half)
    wrist = (0.5, _FLOOR_Y)
    shoulder = (wrist[0], wrist[1] - reach)
    # Elbow on the perpendicular bisector of shoulder-wrist, flared towards the
    # feet: both segments are then exactly _ARM_SEGMENT long and meet at
    # elbow_deg.
    elbow = (
        (shoulder[0] + wrist[0]) / 2.0 - forward * _ARM_SEGMENT * cos(half),
        (shoulder[1] + wrist[1]) / 2.0,
    )

    hip = (shoulder[0] - forward * _SHOULDER_TO_HIP, shoulder[1])
    # Rotating the leg about the hip by d leaves a Hip Angle of 180 - |d|.
    # The y term carries no `forward` factor, so mirroring the facing does not
    # flip which way the body line bends.
    bend = radians(hip_deviation_deg) * forward
    leg = (-forward * cos(bend), -sin(bend))
    knee = (hip[0] + leg[0] * _HIP_TO_KNEE, hip[1] + leg[1] * _HIP_TO_KNEE)
    ankle = (knee[0] + leg[0] * _KNEE_TO_ANKLE, knee[1] + leg[1] * _KNEE_TO_ANKLE)
    nose = (shoulder[0] + forward * _NOSE_AHEAD, shoulder[1] - _NOSE_RISE)

    landmarks = [
        [_UNUSED_LANDMARK[0], _UNUSED_LANDMARK[1], 0.0, _DEFAULT_VISIBILITY]
        for _ in range(LANDMARK_COUNT)
    ]
    placements = (
        (geometry.NOSE, nose),
        *((geometry.SHOULDER[side], shoulder) for side in geometry.SIDES),
        *((geometry.ELBOW[side], elbow) for side in geometry.SIDES),
        *((geometry.WRIST[side], wrist) for side in geometry.SIDES),
        *((geometry.HIP[side], hip) for side in geometry.SIDES),
        *((geometry.KNEE[side], knee) for side in geometry.SIDES),
        *((geometry.ANKLE[side], ankle) for side in geometry.SIDES),
    )
    for index, (x, y) in placements:
        landmarks[index][0] = x
        landmarks[index][1] = y

    for index, value in (overrides or {}).items():
        landmarks[index][3] = value
    return landmarks
