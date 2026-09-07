"""The synthetic Landmark generator is the fixture every analysis test leans on.

If it does not produce the Elbow Angle it was asked for, every counting test
below it is measuring the fixture rather than the analysis.
"""

import math

import pytest

from pushform.analysis import geometry, synthetic

TOLERANCE_DEG = 1.0


def elbow_angles(frames, side="left"):
    return [geometry.elbow_angle(frame["lm"], side) for frame in frames]


def test_frames_are_in_wire_shape():
    frames = synthetic.generate_frames(cycles=1, fps=30)

    for frame in frames:
        assert set(frame) == {"t", "lm"}
        assert isinstance(frame["t"], int)
        assert len(frame["lm"]) == 33
        assert all(len(landmark) == 4 for landmark in frame["lm"])


def test_timestamps_advance_at_the_requested_frame_rate():
    frames = synthetic.generate_frames(cycles=1, cycle_ms=1000, fps=10)

    assert [frame["t"] for frame in frames] == [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]


@pytest.mark.parametrize("facing", ["left", "right"])
@pytest.mark.parametrize("side", ["left", "right"])
def test_generated_landmarks_reproduce_the_requested_elbow_angle(facing, side):
    requested = [30.0, 60.0, 95.0, 120.0, 155.0, 179.0]

    frames = synthetic.frames_from_angles(requested, facing=facing)

    for wanted, produced in zip(requested, elbow_angles(frames, side), strict=True):
        assert produced == pytest.approx(wanted, abs=TOLERANCE_DEG)


def test_a_cycle_sweeps_between_the_requested_elbow_extremes():
    frames = synthetic.generate_frames(cycles=1, elbow_min_deg=70.0, elbow_max_deg=170.0)
    angles = elbow_angles(frames)

    assert min(angles) == pytest.approx(70.0, abs=TOLERANCE_DEG)
    assert max(angles) == pytest.approx(170.0, abs=TOLERANCE_DEG)


def test_a_cycle_starts_locked_out_and_a_down_start_starts_at_the_bottom():
    up_first = synthetic.generate_frames(cycles=1, elbow_min_deg=70.0, elbow_max_deg=170.0)
    down_first = synthetic.generate_frames(
        cycles=1, elbow_min_deg=70.0, elbow_max_deg=170.0, start_phase="down"
    )

    assert elbow_angles(up_first)[0] == pytest.approx(170.0, abs=TOLERANCE_DEG)
    assert elbow_angles(down_first)[0] == pytest.approx(70.0, abs=TOLERANCE_DEG)


def test_mirroring_the_figure_leaves_the_elbow_angles_alone():
    facing_left = elbow_angles(synthetic.generate_frames(cycles=2, facing="left"))
    facing_right = elbow_angles(synthetic.generate_frames(cycles=2, facing="right"))

    for left, right in zip(facing_left, facing_right, strict=True):
        assert left == pytest.approx(right, abs=1e-9)


def test_the_figure_faces_the_requested_direction():
    facing_right = synthetic.generate_frames(cycles=1, facing="right")[0]["lm"]
    facing_left = synthetic.generate_frames(cycles=1, facing="left")[0]["lm"]

    assert facing_right[geometry.NOSE][0] > facing_right[geometry.ANKLE["left"]][0]
    assert facing_left[geometry.NOSE][0] < facing_left[geometry.ANKLE["left"]][0]


@pytest.mark.parametrize("deviation", [0.0, 12.0, -12.0])
def test_hip_deviation_bends_the_body_line_by_that_many_degrees(deviation):
    frames = synthetic.generate_frames(cycles=1, hip_deviation_deg=deviation)

    for frame in frames:
        assert geometry.hip_angle(frame["lm"], "left") == pytest.approx(
            180.0 - abs(deviation), abs=TOLERANCE_DEG
        )


def test_dropped_frames_are_missing_from_the_sequence_without_shifting_time():
    complete = synthetic.generate_frames(cycles=1, cycle_ms=1000, fps=10)

    gappy = synthetic.generate_frames(cycles=1, cycle_ms=1000, fps=10, dropped_frames={2, 3})

    assert [frame["t"] for frame in gappy] == [0, 100, 400, 500, 600, 700, 800, 900, 1000]
    assert len(gappy) == len(complete) - 2


def test_visibility_overrides_apply_to_the_named_landmarks_of_that_frame():
    def hide_left_elbow(index: int):
        return {geometry.ELBOW["left"]: 0.1} if index == 1 else None

    frames = synthetic.generate_frames(cycles=1, fps=10, visibility=hide_left_elbow)

    assert geometry.visibility(frames[1]["lm"], geometry.ELBOW["left"]) == pytest.approx(0.1)
    assert geometry.visibility(frames[0]["lm"], geometry.ELBOW["left"]) > 0.6
    assert geometry.visibility(frames[1]["lm"], geometry.ELBOW["right"]) > 0.6


def test_noise_perturbs_the_angles_but_repeats_for_the_same_seed():
    clean = elbow_angles(synthetic.generate_frames(cycles=1, noise_deg=0.0))
    noisy = elbow_angles(synthetic.generate_frames(cycles=1, noise_deg=4.0, seed=7))
    again = elbow_angles(synthetic.generate_frames(cycles=1, noise_deg=4.0, seed=7))

    assert noisy == again
    assert noisy != clean
    assert max(abs(a - b) for a, b in zip(clean, noisy, strict=True)) < 20.0


def test_a_slower_frame_rate_yields_proportionally_fewer_frames():
    fast = synthetic.generate_frames(cycles=2, cycle_ms=1500, fps=30)
    slow = synthetic.generate_frames(cycles=2, cycle_ms=1500, fps=15)

    assert len(fast) == 91
    assert len(slow) == 46
    assert fast[-1]["t"] == slow[-1]["t"] == 3000


def test_angles_stay_inside_the_geometric_range_even_with_heavy_noise():
    angles = elbow_angles(
        synthetic.generate_frames(cycles=3, noise_deg=30.0, seed=1, elbow_max_deg=179.0)
    )

    assert all(0.0 < angle < 180.0 for angle in angles)
    assert not any(math.isnan(angle) for angle in angles)


@pytest.mark.parametrize("deviation", [0.0, 12.0, -12.0])
def test_facing_is_a_pure_horizontal_mirror(deviation):
    facing_right = synthetic.generate_frames(
        cycles=1, facing="right", hip_deviation_deg=deviation
    )[0]["lm"]
    facing_left = synthetic.generate_frames(
        cycles=1, facing="left", hip_deviation_deg=deviation
    )[0]["lm"]

    for right, left in zip(facing_right, facing_left, strict=True):
        assert left[0] == pytest.approx(1.0 - right[0])
        assert left[1] == pytest.approx(right[1])


@pytest.mark.parametrize("deviation", [12.0, -12.0])
def test_the_body_line_bends_the_same_way_whichever_way_the_body_faces(deviation):
    def leg_drop(frames):
        landmarks = frames[0]["lm"]
        return landmarks[geometry.ANKLE["left"]][1] - landmarks[geometry.HIP["left"]][1]

    facing_right = leg_drop(
        synthetic.generate_frames(cycles=1, facing="right", hip_deviation_deg=deviation)
    )
    facing_left = leg_drop(
        synthetic.generate_frames(cycles=1, facing="left", hip_deviation_deg=deviation)
    )

    assert math.copysign(1.0, facing_right) == math.copysign(1.0, facing_left)
    assert facing_right == pytest.approx(facing_left)


def test_a_positive_hip_deviation_sags_the_hips_below_the_body_line():
    sag = synthetic.generate_frames(cycles=1, hip_deviation_deg=12.0)[0]["lm"]
    pike = synthetic.generate_frames(cycles=1, hip_deviation_deg=-12.0)[0]["lm"]

    # y grows downwards, so sagging hips leave the ankle above the hip.
    assert sag[geometry.ANKLE["left"]][1] < sag[geometry.HIP["left"]][1]
    assert pike[geometry.ANKLE["left"]][1] > pike[geometry.HIP["left"]][1]
