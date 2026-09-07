"""Angles in image space: the primitive every phase decision rests on."""

import math

import pytest

from pushform.analysis import geometry


def mirrored(point: tuple[float, float]) -> tuple[float, float]:
    """The same point in a horizontally flipped image."""
    return (1.0 - point[0], point[1])


def test_perpendicular_arms_give_a_right_angle():
    assert geometry.angle_deg((1.0, 0.0), (0.0, 0.0), (0.0, 1.0)) == pytest.approx(90.0)


def test_collinear_points_give_a_straight_line():
    assert geometry.angle_deg((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)) == pytest.approx(180.0)


def test_equilateral_triangle_gives_sixty_degrees():
    apex = (0.5, math.sqrt(3.0) / 2.0)

    assert geometry.angle_deg((0.0, 0.0), apex, (1.0, 0.0)) == pytest.approx(60.0)


@pytest.mark.parametrize(
    ("a", "b", "c"),
    [
        ((1.0, 0.0), (0.0, 0.0), (0.0, 1.0)),
        ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)),
        ((0.0, 0.0), (0.5, math.sqrt(3.0) / 2.0), (1.0, 0.0)),
        ((0.2, 0.9), (0.4, 0.5), (0.9, 0.7)),
    ],
)
def test_mirroring_the_points_leaves_the_angle_unchanged(a, b, c):
    original = geometry.angle_deg(a, b, c)

    assert geometry.angle_deg(mirrored(a), mirrored(b), mirrored(c)) == pytest.approx(original)


def test_elbow_angle_reads_each_side_from_its_own_landmarks():
    landmarks = [[0.0, 0.0, 0.0, 0.9] for _ in range(33)]
    # Left elbow bent to a right angle: shoulder 11, elbow 13, wrist 15.
    landmarks[11] = [0.5, 0.4, 0.0, 0.9]
    landmarks[13] = [0.5, 0.6, 0.0, 0.9]
    landmarks[15] = [0.7, 0.6, 0.0, 0.9]
    # Right arm straight: shoulder 12, elbow 14, wrist 16.
    landmarks[12] = [0.5, 0.4, 0.0, 0.9]
    landmarks[14] = [0.5, 0.6, 0.0, 0.9]
    landmarks[16] = [0.5, 0.8, 0.0, 0.9]

    assert geometry.elbow_angle(landmarks, "left") == pytest.approx(90.0)
    assert geometry.elbow_angle(landmarks, "right") == pytest.approx(180.0)


def test_hip_angle_is_straight_for_a_flat_body_line():
    landmarks = [[0.0, 0.0, 0.0, 0.9] for _ in range(33)]
    landmarks[11] = [0.7, 0.5, 0.0, 0.9]  # left shoulder
    landmarks[23] = [0.5, 0.5, 0.0, 0.9]  # left hip
    landmarks[27] = [0.2, 0.5, 0.0, 0.9]  # left ankle

    assert geometry.hip_angle(landmarks, "left") == pytest.approx(180.0)


def test_landmark_visibility_is_read_from_the_fourth_component():
    landmarks = [[0.0, 0.0, 0.0, 0.1] for _ in range(33)]
    landmarks[13] = [0.0, 0.0, 0.0, 0.83]

    assert geometry.visibility(landmarks, 13) == pytest.approx(0.83)
