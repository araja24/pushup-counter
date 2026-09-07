"""Choosing the Tracked Side by visibility, and reporting when neither side is there."""

from pushform.analysis import geometry, synthetic

ARM = ("SHOULDER", "ELBOW", "WRIST")


def dim(side: str, value: float) -> dict[int, float]:
    """Visibility overrides that make one arm hard to see."""
    return {getattr(geometry, part)[side]: value for part in ARM}


def test_the_tracked_side_is_the_left_when_both_sides_are_equally_visible(run_set):
    orchestrator, _ = run_set(synthetic.generate_frames(cycles=1))

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
