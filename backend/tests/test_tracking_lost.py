"""Tracking Lost: what counting does when the camera stops seeing the arm.

A phone loses a Landmark for a Frame or two constantly -- a hand crosses the
elbow, the exposure shifts. The rule that matters is the difference between
that and genuinely losing the user: a short gap must cost nothing, a long one
must freeze the Phase machine and say so rather than invent a Rep.
"""

from pushform.analysis import geometry, synthetic
from pushform.analysis.config import DEFAULT_CONFIG
from pushform.analysis.events import Phase, RepCompleted, TrackingLost, TrackingRegained

ARM = ("SHOULDER", "ELBOW", "WRIST")

# One push-up as a square profile: five Frames of lockout, twenty-five at the
# bottom, then back up. At 30 fps the DOWN Phase lasts about a second, well
# past the Bounce window, so the only thing that can lose the Rep is the gap.
DESCENT = [170.0] * 5 + [70.0] * 25 + [170.0] * 16
SECOND_REP = [70.0] * 25 + [170.0] * 16


def unseen(indices: range):
    """Visibility overrides that hide both arms for a run of Frames."""
    hidden = {
        getattr(geometry, part)[side]: 0.1 for part in ARM for side in geometry.SIDES
    }

    def overrides(index: int) -> dict[int, float] | None:
        return hidden if index in indices else None

    return overrides


def of_type(events, kind):
    return [event for event in events if isinstance(event, kind)]


def test_a_short_gap_at_the_bottom_of_a_rep_still_counts_one_rep(walk_set):
    """Three unseen Frames hold the last good angle; the Rep survives untouched."""
    frames = synthetic.frames_from_angles(DESCENT, visibility=unseen(range(15, 18)))

    states, events = walk_set(frames)

    assert states[-1].reps == 1
    assert of_type(events, TrackingLost) == [], "three Frames is a blink, not a loss"
    assert all(state.tracking for state in states[15:18])


def test_a_gap_of_exactly_the_grace_window_is_still_not_a_loss(walk_set):
    """Five unseen Frames is the edge: Tracking is Lost after *more* than five."""
    grace = DEFAULT_CONFIG.tracking_grace_frames
    frames = synthetic.frames_from_angles(
        DESCENT, visibility=unseen(range(15, 15 + grace))
    )

    states, events = walk_set(frames)

    assert of_type(events, TrackingLost) == []
    assert states[-1].reps == 1


def test_a_long_gap_freezes_the_phase_and_says_tracking_was_lost(walk_set):
    """Twenty unseen Frames mid-Rep: the Phase machine stops rather than guesses."""
    frames = synthetic.frames_from_angles(
        DESCENT + SECOND_REP, visibility=unseen(range(10, 30))
    )

    states, events = walk_set(frames)

    assert len(of_type(events, TrackingLost)) == 1, "one event for one loss, not one a Frame"
    assert len(of_type(events, TrackingRegained)) == 1
    frozen = states[16:30]
    assert all(state.tracking is False for state in frozen)
    assert {state.phase for state in frozen} == {Phase.DOWN}, "the Phase froze where it was"


def test_the_rep_completes_after_tracking_returns_and_the_count_stays_right(walk_set):
    """The rep continues when tracking returns: two push-ups, two Reps."""
    frames = synthetic.frames_from_angles(
        DESCENT + SECOND_REP, visibility=unseen(range(10, 30))
    )

    states, events = walk_set(frames)

    assert [rep.index for rep in of_type(events, RepCompleted)] == [1, 2]
    assert states[-1].reps == 2
    assert states[-1].tracking is True


def test_the_same_sequence_seen_all_the_way_through_counts_the_same_two_reps(walk_set):
    """The control: the gap must not be what makes the count come out right."""
    states, _ = walk_set(synthetic.frames_from_angles(DESCENT + SECOND_REP))

    assert states[-1].reps == 2


def test_no_rep_is_invented_while_the_camera_cannot_see_the_user(walk_set):
    """Landmarks keep arriving during a loss; none of them may move the count."""
    frames = synthetic.frames_from_angles(
        [170.0] * 5 + [70.0] * 25 + [170.0] * 10, visibility=unseen(range(5, 40))
    )

    states, events = walk_set(frames)

    assert of_type(events, RepCompleted) == []
    assert states[-1].reps == 0
    assert states[-1].tracking is False
