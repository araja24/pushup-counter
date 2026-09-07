"""Choosing the Tracked Side by visibility, and reporting when neither side is there."""

import pytest

from pushform.analysis import geometry, synthetic
from pushform.analysis.events import Phase, RepCompleted

ARM = ("SHOULDER", "ELBOW", "WRIST")


def dim(side: str, value: float) -> dict[int, float]:
    """Visibility overrides that make one arm hard to see."""
    return {getattr(geometry, part)[side]: value for part in ARM}


def test_the_tracked_side_is_the_left_when_both_sides_are_equally_visible(run_set):
    orchestrator, _ = run_set(synthetic.generate_frames(cycles=1))

    assert orchestrator.state.side == "left"


def test_the_tracked_side_is_the_left_when_the_left_arm_is_the_clearer_one(run_set):
    frames = synthetic.generate_frames(cycles=1, visibility=lambda _index: dim("right", 0.7))

    orchestrator, _ = run_set(frames)

    assert orchestrator.state.side == "left"


def test_the_tracked_side_follows_the_more_visible_arm(run_set):
    frames = synthetic.generate_frames(cycles=2, visibility=lambda _index: dim("left", 0.2))

    orchestrator, _ = run_set(frames)

    assert orchestrator.state.side == "right"


def test_the_tracked_side_switches_when_the_other_arm_becomes_clearer(run_set):
    def fade_left_after_a_second(index: int) -> dict[int, float] | None:
        return dim("left", 0.1) if index >= 30 else None

    frames = synthetic.generate_frames(cycles=3, visibility=fade_left_after_a_second)

    orchestrator, _ = run_set(frames)

    assert orchestrator.state.side == "right"
    assert orchestrator.state.reps == 3


def test_tracking_is_false_while_the_tracked_arm_sits_below_the_visibility_floor(run_set):
    def hide_both_arms(_index: int) -> dict[int, float]:
        return {**dim("left", 0.2), **dim("right", 0.2)}

    orchestrator, _ = run_set(synthetic.generate_frames(cycles=1, visibility=hide_both_arms))

    assert orchestrator.state.tracking is False


def test_tracking_is_true_for_a_clearly_seen_arm(run_set):
    orchestrator, _ = run_set(synthetic.generate_frames(cycles=1))

    assert orchestrator.state.tracking is True


def clearer_right_arm_from(index_from: int):
    """Visibility that hands the clearer arm from left to right at one Frame.

    The left arm only fades to 0.7 -- still above the visibility floor, so this
    is a better view of the other arm rather than a Tracking Lost in disguise.
    """

    def overrides(index: int) -> dict[int, float] | None:
        return dim("left", 0.7) if index >= index_from else None

    return overrides


def test_the_tracked_side_never_switches_during_the_down_phase(walk_set):
    """A switch mid-Rep would swap the Elbow Angle underneath the Rep in progress.

    The right arm becomes the clearer one while the figure is at the bottom of
    a push-up. The Tracked Side has to wait for UP.
    """
    left = [170.0] * 5 + [70.0] * 25 + [170.0] * 16
    right = [170.0] * len(left)
    frames = synthetic.frames_from_side_angles(
        left, right, visibility=clearer_right_arm_from(12)
    )

    states, _ = walk_set(frames)

    down = [state.side for state in states if state.phase is Phase.DOWN]
    assert down, "the sequence must actually go DOWN for this to mean anything"
    assert set(down) == {"left"}, "the Tracked Side changed mid-Rep"
    assert states[-1].side == "right", "the switch happened once the arms were up"
    assert states[-1].reps == 1


def test_switching_the_tracked_side_resets_the_smoothing_and_emits_no_rep(walk_set):
    """The newly Tracked Side's Elbow Angle must be reported from its first Frame.

    The median window is still full of the arm just abandoned. Left over, it
    would report the wrong arm's angle for two more Frames -- and a stale 170
    followed by a real 100 is exactly the fake descent that manufactures Reps.
    """
    left = [170.0] * 40
    right = [100.0] * 40
    frames = synthetic.frames_from_side_angles(
        left, right, visibility=clearer_right_arm_from(10)
    )

    states, events = walk_set(frames)

    switched = next(index for index, state in enumerate(states) if state.side == "right")
    assert states[switched].elbow_angle == pytest.approx(100.0, abs=1.0)
    assert [event for event in events if isinstance(event, RepCompleted)] == []
    assert states[-1].reps == 0
